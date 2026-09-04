"""Bounded Document Processor Training application workflow."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Callable

from src.clients.smartsheet_client import SmartsheetClient
from src.models.document_processor_business_context import BUSINESS_CONTEXT_VERSION
from src.services.document_processor_training_analysis_service import (
    LocalCorrectionAnalysisService,
    PhiSafeImplementationTaskService,
)
from src.services.smartsheet_feedback_case_storage_service import (
    CorrectionCase,
    ProtectedCorrectionCaseRepository,
    stable_digest,
)
from src.services.document_processor_training_codex_service import (
    BoundedCodexDispatcher,
)
from src.services.document_processor_training_configuration_service import (
    load_runtime_dp_training_capabilities,
)
from src.services.document_processor_training_contracts import (
    ANALYSIS_CONTRACT_VERSION,
    AI_CORRECTION,
    AI_CORRECTION_STATUS,
    AI_CORRECTION_TYPE,
    AI_PROPOSED_CORRECTION,
    AI_RESOLUTION_RESULT,
    APPROVE_AI_CORRECTION,
    APPROVE_AI_RESOLUTION,
    ALLOWED_STATUS_TRANSITIONS,
    HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE,
    HISTORICAL_ACCEPTANCE_RESULT,
    REQUIRED_COLUMNS,
    TRAINING_MODES,
    CorrectionAnalysis,
    TrainingCycleSummary,
    build_proposal,
    validate_analysis,
)
from src.services.smartsheet_document_processor_training_service import (
    SmartsheetCorrectionReader,
    SmartsheetCorrectionSchemaService,
    SmartsheetCorrectionWriter,
)


StageObserver = Callable[..., None]


class DocumentProcessorTrainingApplicationService:
    """Advance a bounded set of durable correction cases once."""

    MAX_CASE_REVISIONS_PER_CYCLE = 5

    def __init__(
        self,
        *,
        schema_service,
        reader,
        repository,
        analyzer,
        writer,
        task_service,
        dispatcher,
        mode: str,
    ) -> None:
        self.schema_service = schema_service
        self.reader = reader
        self.repository = repository
        self.analyzer = analyzer
        self.writer = writer
        self.task_service = task_service
        self.dispatcher = dispatcher
        if mode not in TRAINING_MODES:
            raise ValueError("training_mode_invalid")
        self.mode = mode

    @classmethod
    def from_environment(cls) -> "DocumentProcessorTrainingApplicationService":
        capabilities = load_runtime_dp_training_capabilities()
        mode = capabilities.mode
        write_enabled = capabilities.smartsheet_writes_enabled
        dispatch_enabled = capabilities.codex_dispatch_enabled
        if mode in {"proposal_write", "approval_dispatch"} and not write_enabled:
            raise RuntimeError("training_smartsheet_write_gate_disabled")
        if mode == "approval_dispatch" and not dispatch_enabled:
            raise RuntimeError("training_codex_dispatch_gate_disabled")
        client = SmartsheetClient(
            sheet_id_env_var="SMARTSHEET_AI_DESTINATION_SHEET_ID"
        )
        reader = SmartsheetCorrectionReader(client=client)
        return cls(
            schema_service=SmartsheetCorrectionSchemaService(client=client),
            reader=reader,
            repository=ProtectedCorrectionCaseRepository(),
            analyzer=LocalCorrectionAnalysisService(),
            writer=SmartsheetCorrectionWriter(client=client, reader=reader),
            task_service=PhiSafeImplementationTaskService(),
            dispatcher=BoundedCodexDispatcher(
                enabled=(
                    mode == "approval_dispatch"
                    and write_enabled
                    and dispatch_enabled
                )
            ),
            mode=mode,
        )

    def run_cycle(self, *, stage_observer: StageObserver | None = None) -> TrainingCycleSummary:
        self._cycle = {
            "new": 0, "updated": 0, "authorized": 0,
            "started": 0, "completed": 0, "failed": 0, "resolved": 0,
        }
        self._implementation_dispatched = False
        self._observe(stage_observer, "training_poll", "started")
        schema = self.schema_service.read()
        if not schema.success:
            self._observe(
                stage_observer, "training_poll", "failed",
                failure_category=schema.status,
            )
            return TrainingCycleSummary(
                effective_mode=self.mode,
                polling_result="failed",
                failure_category=schema.status,
                recoverable=True,
                retryable=True,
            )
        if self.mode == "schema_only":
            self._observe(stage_observer, "training_poll", "completed")
            return TrainingCycleSummary(
                effective_mode=self.mode, polling_result="schema_ready"
            )
        try:
            rows = self.reader.read_rows(schema=schema)
        except Exception:
            self._observe(
                stage_observer, "training_poll", "failed",
                failure_category="flagged_row_read_failed",
            )
            return TrainingCycleSummary(
                effective_mode=self.mode,
                polling_result="failed",
                failure_category="flagged_row_read_failed",
                recoverable=True,
                retryable=True,
            )
        self._observe(stage_observer, "training_poll", "completed")
        row_by_id = {row.row_id: row for row in rows}
        flagged = [row for row in rows if row.values.get(AI_CORRECTION) is True]
        for row in flagged[:self.MAX_CASE_REVISIONS_PER_CYCLE]:
            self._advance_flagged_case(
                row=row, schema=schema, stage_observer=stage_observer
            )
        self._reject_withdrawn_cases(
            row_by_id=row_by_id, schema=schema, stage_observer=stage_observer
        )
        return self._summary(flagged_count=len(flagged))

    def _advance_flagged_case(self, *, row, schema, stage_observer) -> int:
        self._observe(stage_observer, "case_discovered", "completed", case_count=1)
        self._observe(stage_observer, "case_loaded", "started")
        try:
            row = self.reader.read_context_row(row_id=row.row_id, schema=schema)
            if row.values.get(AI_CORRECTION) is not True:
                self._observe(stage_observer, "case_loaded", "completed", case_count=0)
                return 0
            comments = self.reader.read_comments(row_id=row.row_id)
            correction_case = self.repository.load_or_create(
                source_scope="ai-destination", row_id=row.row_id
            )
        except Exception:
            self._observe(
                stage_observer, "case_loaded", "failed",
                failure_category="case_load_failed",
            )
            return 0
        self._observe(stage_observer, "case_loaded", "completed", case_count=1)
        if not self._reconcile_write_intent(
            correction_case=correction_case, schema=schema
        ):
            return 0
        comment_payload = [asdict(comment) for comment in comments]
        protected_row = {
            title: value
            for title, value in row.values.items()
            if title not in REQUIRED_COLUMNS
        }
        input_digest = stable_digest({
            "row": protected_row,
            "comments": comment_payload,
        })
        changed = input_digest != correction_case.input_digest
        if changed:
            if correction_case.proposal_generation == 0:
                self._cycle["new"] += 1
            else:
                self._cycle["updated"] += 1
            if correction_case.implementation_state == "running":
                correction_case.pending_feedback = True
                correction_case.comments = comment_payload
                correction_case.comment_checkpoint_digest = stable_digest(comment_payload)
                self.repository.save(correction_case)
                return 1
            correction_case.input_digest = input_digest
            correction_case.comment_checkpoint_digest = stable_digest(comment_payload)
            correction_case.comments = comment_payload
            correction_case.row_snapshot = protected_row
            correction_case.correction_approval_baseline_seen = False
            correction_case.correction_approval_previous = None
            correction_case.resolution_approval_baseline_seen = False
            correction_case.resolution_approval_previous = None
            correction_case.pending_feedback = False
            self._transition(correction_case, "New")
            self._observe(stage_observer, "comment_checkpoint", "completed")
            self._analyze_case(
                correction_case=correction_case,
                schema=schema,
                source_row=row,
                stage_observer=stage_observer,
            )
        elif self._analysis_upgrade_eligible(correction_case):
            self._cycle["updated"] += 1
            correction_case.correction_approval_baseline_seen = False
            correction_case.correction_approval_previous = None
            correction_case.resolution_approval_baseline_seen = False
            correction_case.resolution_approval_previous = None
            self._transition(correction_case, "New")
            self._analyze_case(
                correction_case=correction_case,
                schema=schema,
                source_row=row,
                stage_observer=stage_observer,
            )
        elif self.mode in {"proposal_write", "approval_dispatch"}:
            self._sync_existing_proposal(
                correction_case=correction_case,
                schema=schema,
                source_row=row,
                stage_observer=stage_observer,
            )
        self._advance_approval(
            correction_case=correction_case,
            row=row,
            schema=schema,
            stage_observer=stage_observer,
        )
        self._advance_resolution(
            correction_case=correction_case,
            row=row,
            schema=schema,
            stage_observer=stage_observer,
        )
        self.repository.save(correction_case)
        return 1 if changed else 0

    @staticmethod
    def _analysis_upgrade_eligible(correction_case: CorrectionCase) -> bool:
        return (
            correction_case.implementation_state
            != HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE
            and correction_case.implementation_state != "running"
            and correction_case.status in {
                "New", "Analysis Ready", "Needs More Information",
                "Cannot Resolve Yet", "Requires External System",
            }
            and (
                correction_case.analysis_contract_version < ANALYSIS_CONTRACT_VERSION
                or correction_case.business_context_version < BUSINESS_CONTEXT_VERSION
            )
            and correction_case.analysis_attempt_state != "started"
        )

    def _analyze_case(
        self, *, correction_case, schema, source_row, stage_observer
    ) -> None:
        analysis_attempt_key = stable_digest({
            "case": correction_case.case_id,
            "input": correction_case.input_digest,
            "analysis_contract_version": ANALYSIS_CONTRACT_VERSION,
            "business_context_version": BUSINESS_CONTEXT_VERSION,
        })
        if (
            correction_case.analysis_attempt_key == analysis_attempt_key
            and correction_case.analysis_attempt_state == "started"
        ):
            return
        correction_case.analysis_attempt_key = analysis_attempt_key
        correction_case.analysis_attempt_state = "started"
        self.repository.save(correction_case)
        if not correction_case.comments:
            analysis = CorrectionAnalysis(
                primary_correction_type="Needs Investigation",
                related_correction_types=(),
                affected_fields=(),
                behavior_code="needs_investigation",
                desired_behavior="",
                likely_layers=("Needs Investigation",),
                desired_behavior_sufficient=False,
                technical_disposition="Needs Investigation",
                feedback_relationship="Insufficient",
                observed_failure_type="Other",
                affected_document_category="not_applicable",
                desired_intake_subtype="not_applicable",
                required_filename_components=(),
                excluded_filename_components=(),
                analysis_outcome_category="comment_unavailable",
            )
        else:
            self._observe(stage_observer, "local_analysis", "started")
            protected_context = {
                "row": correction_case.row_snapshot,
                "prior_reviewer_feedback": correction_case.comments[:-1],
                "current_reviewer_feedback": correction_case.comments[-1],
            }
            analysis = self.analyzer.analyze(protected_context=protected_context)
            self._observe(stage_observer, "local_analysis", "completed")
        analysis = validate_analysis(analysis)
        proposal = build_proposal(analysis)
        correction_case.proposal_generation += 1
        correction_case.proposal_text = proposal
        correction_case.correction_type = analysis.correction_type
        correction_case.related_correction_types = list(
            analysis.related_correction_types
        )
        correction_case.behavior_code = analysis.behavior_code
        correction_case.affected_fields = list(analysis.affected_fields)
        correction_case.likely_layers = list(analysis.likely_layers)
        correction_case.technical_disposition = analysis.technical_disposition
        correction_case.feedback_relationship = analysis.feedback_relationship
        correction_case.observed_failure_type = analysis.observed_failure_type
        correction_case.affected_document_category = (
            analysis.affected_document_category
        )
        correction_case.desired_intake_subtype = analysis.desired_intake_subtype
        correction_case.required_filename_components = list(
            analysis.required_filename_components
        )
        correction_case.excluded_filename_components = list(
            analysis.excluded_filename_components
        )
        correction_case.analysis_outcome_category = (
            analysis.analysis_outcome_category
        )
        correction_case.analysis_contract_version = ANALYSIS_CONTRACT_VERSION
        correction_case.business_context_version = BUSINESS_CONTEXT_VERSION
        correction_case.analysis_attempt_state = "completed"
        correction_case.proposal_hash = self._proposal_digest(correction_case)
        status = (
            "Needs More Information"
            if not analysis.desired_behavior_sufficient
            else (
                "Requires External System"
                if analysis.technical_disposition == "External Dependency"
                else "Analysis Ready"
            )
        )
        self._transition(correction_case, status)
        self._observe(stage_observer, "proposal_validated", "completed")
        self.repository.save(correction_case)
        if self.mode in {"proposal_write", "approval_dispatch"}:
            updates = {
                AI_PROPOSED_CORRECTION: proposal,
                AI_CORRECTION_TYPE: analysis.correction_type,
                AI_CORRECTION_STATUS: status,
            }
            if (
                correction_case.implementation_state
                == HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE
            ):
                correction_case.resolution_result = HISTORICAL_ACCEPTANCE_RESULT
                updates[AI_RESOLUTION_RESULT] = HISTORICAL_ACCEPTANCE_RESULT
            if source_row.values.get(AI_RESOLUTION_RESULT) not in {None, ""}:
                updates[AI_RESOLUTION_RESULT] = (
                    HISTORICAL_ACCEPTANCE_RESULT
                    if correction_case.implementation_state
                    == HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE
                    else (
                        "New reviewer feedback reopened this correction. Review the revised "
                        "proposal and use a new approval edge before implementation."
                    )
                )
            written = self._write_case_fields(
                correction_case=correction_case,
                schema=schema,
                updates=updates,
                expected_values={
                    title: source_row.values.get(title)
                    for title in updates
                },
                stage_observer=stage_observer,
            )
            if not written:
                self._transition(correction_case, "Cannot Resolve Yet")
                self.repository.save(correction_case)

    def _sync_existing_proposal(
        self, *, correction_case, schema, source_row, stage_observer
    ) -> bool:
        """Publish one already-validated durable generation after mode promotion."""
        if (
            correction_case.proposal_generation <= 0
            or correction_case.status not in {
                "Analysis Ready", "Needs More Information", "Requires External System"
            }
            or not self._proposal_digest_matches(correction_case)
        ):
            return False
        try:
            validate_analysis(CorrectionAnalysis(
                primary_correction_type=correction_case.correction_type,
                related_correction_types=tuple(
                    correction_case.related_correction_types
                ),
                affected_fields=tuple(correction_case.affected_fields),
                behavior_code=correction_case.behavior_code,
                desired_behavior=correction_case.proposal_text,
                likely_layers=tuple(correction_case.likely_layers),
                desired_behavior_sufficient=(
                    correction_case.status != "Needs More Information"
                ),
                technical_disposition=correction_case.technical_disposition,
                feedback_relationship=correction_case.feedback_relationship,
                observed_failure_type=correction_case.observed_failure_type,
                affected_document_category=(
                    correction_case.affected_document_category
                ),
                desired_intake_subtype=correction_case.desired_intake_subtype,
                required_filename_components=tuple(
                    correction_case.required_filename_components
                ),
                excluded_filename_components=tuple(
                    correction_case.excluded_filename_components
                ),
                analysis_outcome_category=correction_case.analysis_outcome_category,
            ))
        except (TypeError, ValueError):
            return False
        updates = {
            AI_PROPOSED_CORRECTION: correction_case.proposal_text,
            AI_CORRECTION_TYPE: correction_case.correction_type,
            AI_CORRECTION_STATUS: correction_case.status,
        }
        if (
            correction_case.implementation_state
            == HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE
        ):
            correction_case.resolution_result = HISTORICAL_ACCEPTANCE_RESULT
            updates[AI_RESOLUTION_RESULT] = HISTORICAL_ACCEPTANCE_RESULT
        return self._write_case_fields(
            correction_case=correction_case,
            schema=schema,
            updates=updates,
            expected_values={
                title: source_row.values.get(title)
                for title in updates
            },
            stage_observer=stage_observer,
        )

    def _advance_approval(self, *, correction_case, row, schema, stage_observer) -> None:
        current = row.values.get(APPROVE_AI_CORRECTION)
        if (
            correction_case.implementation_state
            == HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE
        ):
            return
        if self.mode != "approval_dispatch":
            correction_case.correction_approval_baseline_seen = current is not True
            correction_case.correction_approval_previous = (
                False if current is not True else None
            )
            return
        if current is not True:
            correction_case.correction_approval_baseline_seen = True
            correction_case.correction_approval_previous = False
            if correction_case.status == "Analysis Ready":
                self._observe(stage_observer, "awaiting_approval", "completed")
            return
        valid_edge = (
            correction_case.status == "Analysis Ready"
            and correction_case.correction_approval_baseline_seen
            and correction_case.correction_approval_previous is False
            and correction_case.correction_approval_consumed_generation
            < correction_case.proposal_generation
        )
        correction_case.correction_approval_previous = True
        if valid_edge:
            correction_case.implementation_job_id = stable_digest({
                "case": correction_case.case_id,
                "proposal": correction_case.proposal_hash,
            })
            correction_case.implementation_state = "authorized"
            self._transition(correction_case, "Approved for Implementation")
            self.repository.save(correction_case)
            self._cycle["authorized"] += 1
            self._observe(stage_observer, "implementation_authorized", "completed")
        if (
            correction_case.status != "Approved for Implementation"
            or correction_case.implementation_state not in {"authorized", "waiting"}
            or self._implementation_dispatched
        ):
            return
        if not self._proposal_is_current(correction_case=correction_case, schema=schema):
            return
        expected_status = row.values.get(AI_CORRECTION_STATUS)
        if expected_status not in {"Analysis Ready", "Approved for Implementation"}:
            return
        if not self._write_case_fields(
            correction_case=correction_case,
            schema=schema,
            updates={AI_CORRECTION_STATUS: "Approved for Implementation"},
            expected_values={
                AI_PROPOSED_CORRECTION: correction_case.proposal_text,
                AI_CORRECTION_TYPE: correction_case.correction_type,
                AI_CORRECTION_STATUS: expected_status,
            },
            stage_observer=stage_observer,
        ):
            correction_case.implementation_state = "waiting"
            self.repository.save(correction_case)
            return
        self._implementation_dispatched = True
        task = self.task_service.build(
            opaque_case_id=correction_case.case_id,
            proposal_generation=correction_case.proposal_generation,
            business_context_version=correction_case.business_context_version,
            analysis=CorrectionAnalysis(
                primary_correction_type=correction_case.correction_type,
                related_correction_types=tuple(
                    correction_case.related_correction_types
                ),
                affected_fields=tuple(correction_case.affected_fields),
                behavior_code=correction_case.behavior_code,
                desired_behavior=correction_case.proposal_text,
                likely_layers=tuple(correction_case.likely_layers),
                desired_behavior_sufficient=True,
                technical_disposition=correction_case.technical_disposition,
                feedback_relationship=correction_case.feedback_relationship,
                observed_failure_type=correction_case.observed_failure_type,
                affected_document_category=(
                    correction_case.affected_document_category
                ),
                desired_intake_subtype=correction_case.desired_intake_subtype,
                required_filename_components=tuple(
                    correction_case.required_filename_components
                ),
                excluded_filename_components=tuple(
                    correction_case.excluded_filename_components
                ),
                analysis_outcome_category=correction_case.analysis_outcome_category,
            ),
        )
        def mark_started() -> None:
            self._cycle["started"] += 1
            correction_case.implementation_attempt_count += 1
            correction_case.correction_approval_consumed_generation = correction_case.proposal_generation
            correction_case.implementation_state = "running"
            self._transition(correction_case, "Implementation In Progress")
            self.repository.save(correction_case)
            self._write_case_fields(
                correction_case=correction_case,
                schema=schema,
                updates={AI_CORRECTION_STATUS: "Implementation In Progress"},
                expected_values={
                    AI_PROPOSED_CORRECTION: correction_case.proposal_text,
                    AI_CORRECTION_TYPE: correction_case.correction_type,
                    AI_CORRECTION_STATUS: "Approved for Implementation",
                },
                stage_observer=stage_observer,
            )
            self._observe(stage_observer, "implementation_dispatch", "started")

        result = self.dispatcher.dispatch(task, on_started=mark_started)
        if not result.attempt_started:
            correction_case.implementation_state = "waiting"
            correction_case.resolution_result = (
                "Implementation is approved and waiting for a safe repository and "
                "local Codex execution window. No implementation attempt has started."
            )
            self._write_case_fields(
                correction_case=correction_case,
                schema=schema,
                updates={AI_RESOLUTION_RESULT: correction_case.resolution_result},
                expected_values={
                    AI_PROPOSED_CORRECTION: correction_case.proposal_text,
                    AI_CORRECTION_TYPE: correction_case.correction_type,
                    AI_CORRECTION_STATUS: "Approved for Implementation",
                },
                stage_observer=stage_observer,
            )
            self.repository.save(correction_case)
            return
        if result.success:
            self._cycle["completed"] += 1
            correction_case.implementation_state = "completed"
            correction_case.implementation_commit_sha = result.commit_sha
            correction_case.result_generation += 1
            correction_case.resolution_result = (
                f"The approved {correction_case.correction_type.lower()} behavior was "
                "implemented and safety checks passed. "
                "A real document retest is required. If the result is correct, check "
                "Approve AI Resolution. Reference: " + result.commit_sha[:12]
            )
            correction_case.resolution_hash = stable_digest({
                "generation": correction_case.result_generation,
                "result": correction_case.resolution_result,
            })
            correction_case.resolution_approval_baseline_seen = False
            correction_case.resolution_approval_previous = None
            self._transition(correction_case, "Retest Required")
            self._observe(stage_observer, "implementation_dispatch", "completed")
            self._observe(stage_observer, "implementation_result", "completed")
            self._observe(stage_observer, "retest_required", "completed")
            written = self._write_case_fields(
                correction_case=correction_case,
                schema=schema,
                updates={
                    AI_RESOLUTION_RESULT: correction_case.resolution_result,
                    AI_CORRECTION_STATUS: "Retest Required",
                },
                expected_values={
                    AI_PROPOSED_CORRECTION: correction_case.proposal_text,
                    AI_CORRECTION_TYPE: correction_case.correction_type,
                },
                stage_observer=stage_observer,
            )
            if not written:
                correction_case.implementation_state = "result_write_failed"
                self._transition(correction_case, "Cannot Resolve Yet")
                self.repository.save(correction_case)
        else:
            self._cycle["failed"] += 1
            correction_case.implementation_state = "failed"
            target = {
                "codex_needs_more_information": "Needs More Information",
                "codex_requires_external_system": "Requires External System",
            }.get(result.status, "Cannot Resolve Yet")
            correction_case.result_generation += 1
            correction_case.resolution_result = (
                "Implementation could not be completed safely. Technical review or "
                "additional business guidance is required before another approved attempt."
            )
            self._transition(correction_case, target)
            self._observe(
                stage_observer, "implementation_dispatch", "failed",
                failure_category=result.status,
            )
            self._write_case_fields(
                correction_case=correction_case,
                schema=schema,
                updates={
                    AI_RESOLUTION_RESULT: correction_case.resolution_result,
                    AI_CORRECTION_STATUS: target,
                },
                expected_values={
                    AI_PROPOSED_CORRECTION: correction_case.proposal_text,
                    AI_CORRECTION_TYPE: correction_case.correction_type,
                },
                stage_observer=stage_observer,
            )

    def _advance_resolution(self, *, correction_case, row, schema, stage_observer) -> None:
        if correction_case.status != "Retest Required":
            return
        current = row.values.get(APPROVE_AI_RESOLUTION)
        if current is not True:
            correction_case.resolution_approval_baseline_seen = True
            correction_case.resolution_approval_previous = False
            return
        valid_edge = (
            correction_case.resolution_approval_baseline_seen
            and correction_case.resolution_approval_previous is False
            and correction_case.resolution_approval_consumed_generation
            < correction_case.result_generation
            and not correction_case.pending_feedback
        )
        correction_case.resolution_approval_previous = True
        if not valid_edge or self.mode != "approval_dispatch":
            return
        if not self._resolution_is_current(
            correction_case=correction_case, schema=schema
        ):
            return
        if not self._write_case_fields(
            correction_case=correction_case,
            schema=schema,
            updates={AI_CORRECTION_STATUS: "Resolved"},
            expected_values={
                AI_CORRECTION_STATUS: "Retest Required",
                AI_RESOLUTION_RESULT: correction_case.resolution_result,
            },
            stage_observer=stage_observer,
        ):
            return
        correction_case.resolution_approval_consumed_generation = correction_case.result_generation
        self._transition(correction_case, "Resolved")
        self._cycle["resolved"] += 1
        self._observe(stage_observer, "resolution_approved", "completed")
        self._observe(stage_observer, "case_resolved", "completed")

    def _proposal_is_current(self, *, correction_case, schema) -> bool:
        try:
            current = self.reader.read_row(row_id=correction_case.row_id, schema=schema)
            comments = self.reader.read_comments(row_id=correction_case.row_id)
        except Exception:
            return False
        comment_payload = [asdict(comment) for comment in comments]
        return (
            correction_case.proposal_hash == self._proposal_digest(correction_case)
            and
            current.values.get(AI_PROPOSED_CORRECTION) == correction_case.proposal_text
            and current.values.get(AI_CORRECTION_TYPE) == correction_case.correction_type
            and current.values.get(AI_CORRECTION_STATUS)
            in {"Analysis Ready", "Approved for Implementation"}
            and current.values.get(AI_CORRECTION) is True
            and current.values.get(APPROVE_AI_CORRECTION) is True
            and stable_digest(comment_payload) == correction_case.comment_checkpoint_digest
        )

    @staticmethod
    def _proposal_digest(correction_case: CorrectionCase) -> str:
        return stable_digest({
            "input": correction_case.input_digest,
            "generation": correction_case.proposal_generation,
            "type": correction_case.correction_type,
            "related_types": tuple(correction_case.related_correction_types),
            "proposal": correction_case.proposal_text,
            "analysis_contract_version": correction_case.analysis_contract_version,
            "business_context_version": correction_case.business_context_version,
        })

    @staticmethod
    def _proposal_digest_matches(correction_case: CorrectionCase) -> bool:
        if (
            correction_case.proposal_hash
            == DocumentProcessorTrainingApplicationService._proposal_digest(
                correction_case
            )
        ):
            return True
        if correction_case.analysis_contract_version != 1:
            return False
        return correction_case.proposal_hash == stable_digest({
            "input": correction_case.input_digest,
            "generation": correction_case.proposal_generation,
            "type": correction_case.correction_type,
            "proposal": correction_case.proposal_text,
        })

    def _resolution_is_current(self, *, correction_case, schema) -> bool:
        try:
            current = self.reader.read_row(row_id=correction_case.row_id, schema=schema)
            comments = self.reader.read_comments(row_id=correction_case.row_id)
        except Exception:
            return False
        comment_payload = [asdict(comment) for comment in comments]
        return (
            correction_case.resolution_hash == stable_digest({
                "generation": correction_case.result_generation,
                "result": correction_case.resolution_result,
            })
            and current.values.get(AI_CORRECTION) is True
            and current.values.get(AI_CORRECTION_STATUS) == "Retest Required"
            and current.values.get(AI_RESOLUTION_RESULT)
            == correction_case.resolution_result
            and current.values.get(APPROVE_AI_RESOLUTION) is True
            and stable_digest(comment_payload)
            == correction_case.comment_checkpoint_digest
        )

    def _write_case_fields(
        self, *, correction_case, schema, updates, stage_observer,
        expected_values=None,
    ) -> bool:
        correction_case.write_intent = {
            "generation": correction_case.proposal_generation,
            "field_names": sorted(updates),
            "value_digest": stable_digest(updates),
            "values": dict(updates),
            "state": "pending",
        }
        self.repository.save(correction_case)
        self._observe(stage_observer, "proposal_write", "started")
        result = self.writer.write(
            row_id=correction_case.row_id,
            updates=updates,
            schema=schema,
            expected_proposal_hash_values=expected_values,
        )
        correction_case.write_intent["state"] = (
            "reconciled" if result.success else result.status
        )
        self.repository.save(correction_case)
        self._observe(
            stage_observer,
            "proposal_write",
            "completed" if result.success else "failed",
            failure_category="none" if result.success else result.status,
        )
        return result.success

    def _reconcile_write_intent(self, *, correction_case, schema) -> bool:
        intent = correction_case.write_intent
        if not isinstance(intent, dict) or intent.get("state") not in {
            "pending", "workflow_write_outcome_unresolved"
        }:
            return True
        values = intent.get("values")
        if (
            not isinstance(values, dict)
            or not values
            or set(values) - {
                AI_PROPOSED_CORRECTION,
                AI_CORRECTION_TYPE,
                AI_CORRECTION_STATUS,
                AI_RESOLUTION_RESULT,
            }
            or intent.get("field_names") != sorted(values)
            or intent.get("value_digest") != stable_digest(values)
            or intent.get("generation") != correction_case.proposal_generation
        ):
            intent["state"] = "workflow_write_intent_invalid"
            self.repository.save(correction_case)
            return False
        try:
            current = self.reader.read_row(
                row_id=correction_case.row_id, schema=schema
            )
        except Exception:
            return False
        if all(current.values.get(title) == value for title, value in values.items()):
            intent["state"] = "reconciled"
            self.repository.save(correction_case)
            return True
        intent["state"] = "workflow_write_outcome_unresolved"
        self.repository.save(correction_case)
        return False

    def _reject_withdrawn_cases(self, *, row_by_id, schema, stage_observer) -> None:
        try:
            cases = self.repository.list_cases()
        except Exception:
            return
        for correction_case in cases:
            row = row_by_id.get(correction_case.row_id)
            if row is None or row.values.get(AI_CORRECTION) is not False:
                continue
            if not self._reconcile_write_intent(
                correction_case=correction_case, schema=schema
            ):
                continue
            if correction_case.status in {
                "New", "Analysis Ready", "Needs More Information",
                "Approved for Implementation",
            } and correction_case.implementation_attempt_count == 0:
                self._transition(correction_case, "Rejected")
                if self.mode in {"proposal_write", "approval_dispatch"}:
                    self._write_case_fields(
                        correction_case=correction_case,
                        schema=schema,
                        updates={AI_CORRECTION_STATUS: "Rejected"},
                        expected_values={
                            AI_CORRECTION_STATUS: row.values.get(AI_CORRECTION_STATUS)
                        },
                        stage_observer=stage_observer,
                    )
                self.repository.save(correction_case)

    def _summary(self, *, flagged_count: int) -> TrainingCycleSummary:
        try:
            cases = self.repository.list_cases()
        except Exception:
            return TrainingCycleSummary(
                flagged_case_count=flagged_count,
                effective_mode=self.mode,
                polling_result="completed_with_failures",
                failure_category="case_summary_unavailable",
                recoverable=True,
                retryable=True,
            )
        statuses = [case.status for case in cases]
        return TrainingCycleSummary(
            flagged_case_count=flagged_count,
            effective_mode=self.mode,
            new_case_count=self._cycle["new"],
            updated_case_count=self._cycle["updated"],
            analysis_ready_count=statuses.count("Analysis Ready"),
            awaiting_approval_count=statuses.count("Analysis Ready"),
            implementation_authorized_count=self._cycle["authorized"],
            implementation_started_count=self._cycle["started"],
            implementation_completed_count=self._cycle["completed"],
            implementation_failed_count=self._cycle["failed"],
            retest_required_count=statuses.count("Retest Required"),
            resolved_count=statuses.count("Resolved"),
            needs_more_information_count=statuses.count("Needs More Information"),
            requires_external_system_count=statuses.count("Requires External System"),
        )

    @staticmethod
    def _transition(correction_case: CorrectionCase, status: str) -> None:
        if correction_case.status == status:
            return
        if status not in ALLOWED_STATUS_TRANSITIONS.get(correction_case.status, ()):
            raise ValueError("correction_status_transition_invalid")
        correction_case.status = status
        correction_case.transition_history.append({
            "status": status,
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        })

    @staticmethod
    def _observe(observer: StageObserver | None, stage: str, status: str, **values: Any) -> None:
        if observer is None:
            return
        safe = {
            key: value for key, value in values.items()
            if key in {"case_count", "duration_seconds", "failure_category"}
        }
        try:
            observer(stage=stage, status=status, **safe)
        except Exception:
            return
