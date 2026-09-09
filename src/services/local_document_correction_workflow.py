"""Local-only same-row correction state machine. No code execution or cloud model."""
from dataclasses import asdict
from src.services.document_processor_training_contracts import (
    AI_CORRECTION, AI_PROPOSED_CORRECTION, AI_CORRECTION_TYPE,
    AI_CORRECTION_STATUS, AI_RESOLUTION_RESULT, APPROVE_AI_CORRECTION,
    APPROVE_AI_RESOLUTION, REQUIRED_COLUMNS, TrainingCycleSummary,
    build_proposal, validate_analysis, CorrectionAnalysis,
    TRAINING_MODES,
)
from src.services.smartsheet_feedback_case_storage_service import stable_digest
from src.services.local_correction_memory_service import LocalCorrectionStore, ApprovedDocumentLessons
from src.services.local_code_update_authorization import LocalCodeUpdateAuthorization

# Fixed categories only: exception messages may contain protected SDK/model data.
PREPARATION_CONTRACT_VERSION = 4
PREPARATION_FAILURE_CATEGORIES = frozenset({
    "correction_field_not_mapped", "correction_source_outside_scope",
    "correction_source_identity_unproven", "correction_row_identity_unproven",
    "correction_source_binding_conflict", "correction_source_changed",
    "correction_legacy_state_unprovable", "correction_legacy_identity_unproven",
    "correction_legacy_source_unproven", "correction_schema_unavailable",
    "correction_mapping_unavailable", "correction_unrelated_field_change",
    "correction_filename_unavailable", "correction_attachment_identity_unproven",
    "correction_no_verified_change", "correction_write_scope_invalid",
    "correction_clear_type_invalid", "correction_type_validation_failed",
    "correction_attachment_response_invalid", "correction_preparation_unavailable",
    "correction_intent_insufficient", "correction_preparation_interrupted",
    "correction_proposal_refresh_requires_unchecked_approval",
    "correction_requested_filename_unresolved",
})

def preparation_failure_category(error):
    value = error.args[0] if isinstance(error, ValueError) and len(error.args) == 1 else None
    return value if isinstance(value, str) and value in PREPARATION_FAILURE_CATEGORIES else "correction_preparation_unavailable"

def verified_proposal(plan, affected_fields, required_filename_components=()):
    """Describe verified actions, not an unfulfilled model-requested outcome."""
    updates = plan.get("updates", {})
    if not isinstance(updates, dict):
        raise ValueError("correction_preparation_unavailable")
    parts = []
    review_columns = {"AI Review Reasons", "AI Review Status", "AI Review Required", "AI Minimum Field Confidence"}
    if updates:
        parts.append("Update review information from verified document evidence."
                     if set(updates) <= review_columns
                     else f"Update {len(updates)} row fields from verified document evidence.")
    if plan.get("attachment"):
        name = str(plan["attachment"].get("name", ""))
        placeholders = {
            "Payer When Applicable": "[PAYER]",
            "Service When Applicable": "[SERVICE]",
        }
        if any(placeholders.get(component, "\0") in name
               for component in required_filename_components):
            raise ValueError("correction_requested_filename_unresolved")
        parts.append("Correct the document filename.")
    elif "Filename" in affected_fields:
        raise ValueError("correction_requested_filename_unresolved")
    if not updates and not plan.get("attachment"):
        raise ValueError("correction_no_verified_change")
    return " ".join(parts)

class LocalDocumentCorrectionWorkflow:
    MAX_CASES = 5
    def __init__(self, *, schema_service, reader, writer, repository, analyzer,
                 executor, mode, store=None, lessons=None, code_updates=None):
        self.schema_service, self.reader, self.writer = schema_service, reader, writer
        self.repository, self.analyzer, self.executor = repository, analyzer, executor
        if mode not in TRAINING_MODES:
            raise ValueError("training_mode_invalid")
        self.mode = mode
        self.store = store or LocalCorrectionStore()
        self.lessons = lessons or ApprovedDocumentLessons(self.store)
        self.code_updates = code_updates

    def run_cycle(self, *, stage_observer=None):
        self.observer = stage_observer
        self._preparation_failures = set()
        counts = dict(flagged_case_count=0, new_case_count=0, updated_case_count=0,
                      analysis_ready_count=0, implementation_started_count=0,
                      implementation_completed_count=0, implementation_failed_count=0,
                      resolved_count=0, correction_applied_count=0,
                      awaiting_resolution_count=0, approved_lesson_count=0,
                      blocked_case_count=0)
        try:
            with self.repository.exclusive_operation():
                self._observe("training_poll", "started")
                schema = self.schema_service.read()
                if not schema.success:
                    raise ValueError("schema_unavailable")
                if self.mode == "schema_only":
                    self._observe("training_poll", "completed")
                    return TrainingCycleSummary(effective_mode=self.mode, polling_result="schema_ready")
                rows = [r for r in self.reader.read_rows(schema=schema)
                        if r.values.get(AI_CORRECTION) is True]
                self._observe("training_poll", "completed")
                counts["flagged_case_count"] = len(rows)
                # Human-owned flags may remain checked on resolved cases. Rotate
                # the bounded window so those cases cannot starve later feedback.
                cursor=self.store.load("audit","local-poll-cursor") or {"offset":0}
                offset=cursor.get("offset",0)
                if type(offset) is not int or offset<0: offset=0
                start=offset % len(rows) if rows else 0
                selected=(rows[start:]+rows[:start])[:self.MAX_CASES]
                if rows and self.mode!="read_only":
                    self.store.save("audit","local-poll-cursor",{"offset":(start+len(selected)) % len(rows)})
                for row in selected:
                    try:
                        self._advance(row.row_id, schema, counts)
                    except Exception:
                        # Never emit model text, exception text, values, or identifiers.
                        counts["implementation_failed_count"] += 1
                        self._observe("local_correction", "failed")
        except Exception:
            self._observe("training_poll", "failed")
            return TrainingCycleSummary(effective_mode=self.mode, polling_result="failed",
                                        failure_category="local_correction_unavailable")
        failed = counts["implementation_failed_count"] > 0 or counts["blocked_case_count"] > 0
        return TrainingCycleSummary(
            effective_mode=self.mode, **counts,
            preparation_failure_categories=",".join(sorted(self._preparation_failures)) or "none",
            polling_result="completed_with_failures" if failed else "completed",
            failure_category="local_correction_unresolved" if failed else "none",
        )

    def _observe(self, stage, status):
        try:
            if callable(self.observer):
                self.observer(stage=stage, status=status)
        except Exception:
            pass

    def _read(self, row_id, schema):
        row = self.reader.read_context_row(row_id=row_id, schema=schema)
        comments = [asdict(x) for x in self.reader.read_comments(row_id=row_id)]
        context = {k:v for k,v in row.values.items() if k not in REQUIRED_COLUMNS}
        return row, comments, context, stable_digest({"row": context, "comments": comments})

    def _publish(self, row_id, schema, state, row):
        updates = {AI_PROPOSED_CORRECTION: state["proposal"],
                   AI_CORRECTION_TYPE: state["type"],
                   AI_CORRECTION_STATUS: state["status"],
                   AI_RESOLUTION_RESULT: state.get("result", "")}
        if all(row.values.get(k) == v for k,v in updates.items()):
            return True
        result = self.writer.write(
            row_id=row_id, schema=schema, updates=updates,
            expected_proposal_hash_values={k:row.values.get(k) for k in REQUIRED_COLUMNS},
        )
        return result.success and result.outcome_proven

    def _advance(self, row_id, schema, counts):
        row, comments, context, digest = self._read(row_id, schema)
        if row.values.get(AI_CORRECTION) is not True or self.mode == "read_only":
            return
        # Preserve legacy identity/history; old approvals never authorize this contract.
        legacy = self.repository.load_or_create(source_scope="ai-destination", row_id=row_id)
        key = legacy.case_id
        state = self.store.load("case", key)
        if state and state["phase"] == "resolved" and digest == state["input_digest"]:
            self._continue_code_update(key, state, row_id, schema, counts)
            fresh, _, _, _ = self._read(row_id, schema)
            self._publish(row_id, schema, state, fresh)
            return
        if state and state["phase"] == "applying":
            # Before interpreting changed feedback, reconcile the reserved old intent.
            if not self._publish(row_id, schema, state, row):
                return
            if (row.values.get(APPROVE_AI_CORRECTION) is True
                    and stable_digest(comments) == state["comment_digest"]
                    and callable(getattr(self.executor, "resume", None))):
                self.executor.resume(row_id, state["plan"])
            if not self.executor.verify(row_id, state["plan"]):
                counts["implementation_failed_count"] += 1
                return
            self._applied(key, state, row_id, schema, counts)
            return
        if state and state["phase"] == "awaiting_resolution":
            if digest != state["input_digest"]:
                # A changed production field/comment invalidates this resolution.
                state["phase"] = "superseded"
                self.store.save("case", key, state)
            else:
                self._resolve(key, state, row, comments, schema, counts)
                if state["phase"] == "awaiting_resolution":
                    counts["awaiting_resolution_count"] += 1
                return
        # One reanalysis after a tested contract upgrade, on the SAME identity.
        # Only unapplied blocked plans with unchecked human approvals are eligible.
        # Reservation precedes inference, so interruption cannot cause a hot retry.
        upgrade_blocked = bool(
            state and state["phase"] == "blocked"
            and (state.get("plan") is None or (
                state.get("preparation_failure_category") == "correction_requested_filename_unresolved"
                and isinstance(state.get("plan"), dict)
            ))
            and state.get("preparation_contract_version", 1) < PREPARATION_CONTRACT_VERSION
            and row.values.get(APPROVE_AI_CORRECTION) is not True
            and row.values.get(APPROVE_AI_RESOLUTION) is not True
        )
        if not state or digest != state["input_digest"] or state["phase"] == "superseded" or upgrade_blocked:
            prior_analysis = (state.get("analysis") if upgrade_blocked
                              and digest == state["input_digest"] else None)
            if state:
                self.store.save("audit", stable_digest(state), state)
            generation = (state or {}).get("generation", 0) + 1
            self.store.save("case", key, {
                "phase":"preparing", "generation":generation, "input_digest":digest,
                "preparation_contract_version":PREPARATION_CONTRACT_VERSION,
            })
            self._observe("local_analysis", "started")
            if isinstance(prior_analysis, dict):
                # Feedback/context are unchanged: reuse validated intent, not
                # old document values. Original-source replay still validates
                # the new plan, and human approvals never carry over.
                analysis = validate_analysis(CorrectionAnalysis(**prior_analysis))
            else:
                analysis = validate_analysis(self.analyzer.analyze(protected_context={
                    "row": context, "prior_reviewer_feedback": comments[:-1],
                    "current_reviewer_feedback": comments[-1] if comments else {},
                }))
            # Local model provides intent, never field evidence. Replay validates original source.
            state = {"phase":"preparing", "generation":generation, "input_digest":digest,
                     "feedback":comments, "row_before":context, "analysis":asdict(analysis),
                     "comment_digest":stable_digest(comments), "proposal":build_proposal(analysis),
                     "type":analysis.correction_type, "status":"Needs More Information",
                     "code":analysis.behavior_code, "family":analysis.affected_document_category,
                     "approval_seen_false":row.values.get(APPROVE_AI_CORRECTION) is not True,
                     "resolution_seen_false":False, "plan":None,
                     "preparation_contract_version":PREPARATION_CONTRACT_VERSION,
                     "preparation_failure_category":"none"}
            self.store.save("case", key, state)
            if analysis.desired_behavior_sufficient and comments:
                try:
                    state["plan"] = self.executor.prepare(row_id, context, analysis)
                    state["status"] = "Analysis Ready"
                    state["phase"] = "proposed"
                    state["proposal"] = verified_proposal(state["plan"], analysis.affected_fields, analysis.required_filename_components)
                except Exception as error:
                    state["preparation_failure_category"] = preparation_failure_category(error)
                    state["phase"] = "blocked"
                    state["status"] = "Cannot Resolve Yet"
                    state["result"] = "No safe correction could be verified. Technical verification is needed; your feedback has been retained."
            else:
                state["phase"] = "blocked"
                state["preparation_failure_category"] = "correction_intent_insufficient"
            self._observe("local_analysis", "failed" if state["phase"] == "blocked" else "completed")
            if state["phase"] == "blocked":
                self._record_blocked(state, counts)
            self.store.save("case", key, state)
            counts["updated_case_count" if generation > 1 else "new_case_count"] += 1
            if not self._publish(row_id, schema, state, row):
                counts["implementation_failed_count"] += 1
            elif state["phase"] == "proposed":
                counts["analysis_ready_count"] += 1
            return
        if state["phase"] == "preparing":
            # Interrupted inference is not silently repeated.
            counts["implementation_failed_count"] += 1
            self._preparation_failures.add("correction_preparation_interrupted")
            return
        if state["phase"] == "blocked":
            self._record_blocked(state, counts)
        if state["phase"] == "proposed":
            try:
                presentation = verified_proposal(state["plan"], state["analysis"]["affected_fields"], state["analysis"].get("required_filename_components", ()))
            except ValueError as error:
                self.store.save("audit", stable_digest(state), state)
                state["phase"] = "blocked"
                state["status"] = "Cannot Resolve Yet"
                state["preparation_failure_category"] = preparation_failure_category(error)
                state["proposal"] = "The requested correction could not be verified. No correction will be applied."
                state["result"] = "The requested filename correction remains incomplete. No correction will be applied; verified work and feedback are retained."
                self.store.save("case", key, state)
                self._record_blocked(state, counts)
                self._publish(row_id, schema, state, row)
                return
            if presentation != state["proposal"]:
                # Never turn approval of old wording into approval of a new scope.
                if row.values.get(APPROVE_AI_CORRECTION) is True:
                    counts["blocked_case_count"] += 1
                    self._preparation_failures.add("correction_proposal_refresh_requires_unchecked_approval")
                    return
                self.store.save("audit", stable_digest(state), state)
                state["proposal"] = presentation
                state["approval_seen_false"] = True
                self.store.save("case", key, state)
        if not self._publish(row_id, schema, state, row):
            counts["implementation_failed_count"] += 1
            return
        if state["phase"] != "proposed":
            return
        counts["analysis_ready_count"] += 1
        if self.mode not in {"local_correction", "approval_dispatch"}:
            return
        if row.values.get(APPROVE_AI_CORRECTION) is not True:
            state["approval_seen_false"] = True
            self.store.save("case", key, state)
            return
        if not state["approval_seen_false"]:
            return
        current, current_comments, _, current_digest = self._read(row_id, schema)
        if (current_digest != digest or current.values.get(AI_CORRECTION) is not True
                or current.values.get(APPROVE_AI_CORRECTION) is not True
                or current.values.get(AI_PROPOSED_CORRECTION) != state["proposal"]
                or current.values.get(AI_CORRECTION_TYPE) != state["type"]
                or current.values.get(AI_CORRECTION_STATUS) != "Analysis Ready"):
            return
        # Durable reservation precedes every possible external correction action.
        state["phase"] = "applying"
        state["status"] = "Correction In Progress"
        state["result"] = "Applying the approved correction to this existing row/document."
        self.store.save("case", key, state)
        if not self._publish(row_id, schema, state, current):
            return
        counts["implementation_started_count"] += 1
        self._observe("local_correction", "started")
        try:
            self.executor.apply(row_id, state["plan"])
        except Exception:
            state["status"] = "Cannot Resolve Yet"
            state["result"] = "Correction needs safe recovery. Unresolved requests will not be repeated."
            self.store.save("case", key, state)
            fresh, _, _, _ = self._read(row_id, schema)
            self._publish(row_id, schema, state, fresh)
            raise RuntimeError("local_correction_unresolved") from None
        if not self.executor.verify(row_id, state["plan"]):
            raise ValueError("correction_outcome_unresolved")
        self._applied(key, state, row_id, schema, counts)

    def _record_blocked(self, state, counts):
        counts["blocked_case_count"] += 1
        category = state.get("preparation_failure_category")
        self._preparation_failures.add(category if category in PREPARATION_FAILURE_CATEGORIES
                                       else "correction_preparation_unavailable")

    def _applied(self, key, state, row_id, schema, counts):
        row, comments, _, digest = self._read(row_id, schema)
        # Binding the corrected row must NOT treat it as new reviewer feedback.
        state["phase"] = "awaiting_resolution"
        state["status"] = "Awaiting Resolution Approval"
        changed_fields = ", ".join(sorted(state["plan"]["updates"]))
        actions = ("Updated row fields: " + changed_fields + ". ") if changed_fields else ""
        if state["plan"].get("attachment"):
            actions += "Updated the document filename as a new attachment version. "
        state["result"] = actions + (
            "Original document evidence was revalidated and changes were read back. "
            "Review the result, then check Approve AI Resolution."
        )
        state["input_digest"] = digest
        state["resolution_seen_false"] = row.values.get(APPROVE_AI_RESOLUTION) is not True
        state["resolution_feedback_changed"] = stable_digest(comments) != state["comment_digest"]
        self.store.save("case", key, state)
        self._publish(row_id, schema, state, row)
        counts["implementation_completed_count"] += 1
        counts["correction_applied_count"] += 1
        counts["awaiting_resolution_count"] += 1
        self._observe("local_correction", "completed")
        self._observe("awaiting_resolution", "completed")

    def _resolve(self, key, state, row, comments, schema, counts):
        row_id = row.row_id
        if not self._publish(row_id, schema, state, row):
            return
        if self.mode not in {"local_correction", "approval_dispatch"}:
            return
        if state.get("resolution_feedback_changed"):
            state["phase"] = "superseded"
            self.store.save("case", key, state)
            return
        if row.values.get(APPROVE_AI_RESOLUTION) is not True:
            state["resolution_seen_false"] = True
            self.store.save("case", key, state)
            return
        if not state["resolution_seen_false"] or not self.executor.verify(row_id, state["plan"]):
            return
        fresh, fresh_comments, _, digest = self._read(row_id, schema)
        if (digest != state["input_digest"] or fresh.values.get(AI_CORRECTION) is not True
                or fresh.values.get(APPROVE_AI_RESOLUTION) is not True
                or fresh.values.get(AI_RESOLUTION_RESULT) != state["result"]
                or fresh.values.get(AI_CORRECTION_STATUS) != state["status"]):
            return
        receipt = stable_digest({"case":key, "generation":state["generation"], "plan":state["plan"]})
        # Approval binds this exact verified resolution once, not arbitrary future edits.
        # Code execution is deliberately blocked until isolation/promotion is proven.
        state["local_code_update_status"] = LocalCodeUpdateAuthorization(self.store).record(
            family=state["family"], code=state["code"], receipt=receipt,
            resolution_verified=True,
        )
        self.lessons.approve(family=state["family"], code=state["code"],
                             receipt=receipt, resolution_verified=True)
        state["phase"] = "resolved"
        state["status"] = "Resolved"
        state["result"] = (
            "Resolution approved. Document-type guidance retained. Any necessary local code update "
            "is authorized but pending verified isolation; application code has not changed."
        )
        self.store.save("case", key, state)
        self._publish(row_id, schema, state, fresh)
        counts["resolved_count"] += 1
        counts["approved_lesson_count"] += 1
        self._observe("resolution_approved", "completed")
        self._observe("case_resolved", "completed")
        self._continue_code_update(key, state, row_id, schema, counts)

    def _continue_code_update(self, key, state, row_id, schema, counts):
        if self.code_updates is None or self.mode not in {"local_correction", "approval_dispatch"}:
            return
        fresh, _, _, current_digest = self._read(row_id, schema)
        if (current_digest != state["input_digest"]
                or fresh.values.get(APPROVE_AI_RESOLUTION) is not True
                or fresh.values.get(AI_CORRECTION) is not True):
            return
        if not self.executor.verify(row_id, state["plan"]):
            return
        receipt = stable_digest({"case":key, "generation":state["generation"], "plan":state["plan"]})
        self._observe("local_code_update", "started")
        status = self.code_updates.process(receipt=receipt, family=state["family"], code=state["code"])
        messages = {
            "promoted": "Tested local code update installed; previous version retained for recovery.",
            "guidance_only": "Local code review found no change necessary.",
            "rolled_back": "Code update failed verification; the previous version was restored.",
            "waiting_for_clean_source": "Code update waiting; existing source changes were preserved.",
            "scope_unavailable": "Code update is outside the supported automatic edit scope; current code retained.",
        }
        state["local_code_update_status"] = status
        state["result"] = "Resolution approved. Document-type guidance retained. " + messages.get(
            status, "Code update could not be verified; no successful installation is claimed.")
        self.store.save("case", key, state)
        if status not in {"promoted", "guidance_only", "waiting_for_clean_source"}:
            counts["implementation_failed_count"] += 1
        self._observe("local_code_update", "completed" if status in {"promoted", "guidance_only"} else "failed")
        current, _, _, _ = self._read(row_id, schema)
        self._publish(row_id, schema, state, current)
