"""Local-only same-row correction state machine. No code execution or cloud model."""
from dataclasses import asdict
from src.services.document_processor_training_contracts import (
    AI_CORRECTION, AI_PROPOSED_CORRECTION, AI_CORRECTION_TYPE,
    AI_CORRECTION_STATUS, AI_RESOLUTION_RESULT, APPROVE_AI_CORRECTION,
    APPROVE_AI_RESOLUTION, REQUIRED_COLUMNS, TrainingCycleSummary,
    build_proposal, validate_analysis,
    TRAINING_MODES,
)
from src.services.smartsheet_feedback_case_storage_service import stable_digest
from src.services.local_correction_memory_service import LocalCorrectionStore, ApprovedDocumentLessons
from src.services.local_code_update_authorization import LocalCodeUpdateAuthorization

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
        counts = dict(flagged_case_count=0, new_case_count=0, updated_case_count=0,
                      analysis_ready_count=0, implementation_started_count=0,
                      implementation_completed_count=0, implementation_failed_count=0,
                      resolved_count=0, correction_applied_count=0,
                      awaiting_resolution_count=0, approved_lesson_count=0)
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
        failed = counts["implementation_failed_count"] > 0
        return TrainingCycleSummary(
            effective_mode=self.mode, **counts,
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
                   AI_CORRECTION_STATUS: state["status"]}
        if state.get("result"):
            updates[AI_RESOLUTION_RESULT] = state["result"]
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
        if not state or digest != state["input_digest"] or state["phase"] == "superseded":
            if state:
                self.store.save("audit", stable_digest(state), state)
            generation = (state or {}).get("generation", 0) + 1
            self._observe("local_analysis", "started")
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
                     "resolution_seen_false":False, "plan":None}
            self.store.save("case", key, state)
            if analysis.desired_behavior_sufficient and comments:
                try:
                    state["plan"] = self.executor.prepare(row_id, context, analysis)
                    state["status"] = "Analysis Ready"
                    state["phase"] = "proposed"
                    state["proposal"] = "Correct this existing record using verified document evidence. " + state["proposal"]
                except Exception:
                    state["phase"] = "blocked"
                    state["status"] = "Cannot Resolve Yet"
                    state["result"] = "No safe correction could be verified. Technical review or additional evidence is needed."
            else:
                state["phase"] = "blocked"
            self._observe("local_analysis", "completed")
            self.store.save("case", key, state)
            counts["updated_case_count" if generation > 1 else "new_case_count"] += 1
            self._publish(row_id, schema, state, row)
            return
        if state["phase"] == "preparing":
            # Interrupted inference is not silently repeated.
            counts["implementation_failed_count"] += 1
            return
        if not self._publish(row_id, schema, state, row) or state["phase"] != "proposed":
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
