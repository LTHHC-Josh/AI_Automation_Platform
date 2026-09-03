from dataclasses import dataclass
from enum import Enum
import inspect
from typing import Any

from src.graph.mailbox_processor import (
    MailboxAcceptanceGuardError,
    MailboxProcessor,
)
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetService,
)
from src.services.mailbox_review_session_service import (
    MailboxReviewSessionResult,
    MailboxReviewSessionService,
)
from src.services.mailbox_acceptance_handoff_service import (
    MailboxAcceptanceHandoffError,
    MailboxAcceptanceHandoffService,
)
from src.models.mailbox_acceptance import MailboxAcceptanceSelectionResult
from src.services.production_filename_assembly_service import FilenameReadinessDiagnostic
from src.services.field_validation_diagnostic_service import FinalValidationSummary


class FirstEligibleMailboxCandidateSelector:
    """Choose only candidate one from the existing newest-first safe list."""

    def select(self, candidates):
        if not candidates:
            return MailboxAcceptanceSelectionResult(
                candidate_number=None,
                popup_displayed=False,
                disposition="no_selection",
            )
        return MailboxAcceptanceSelectionResult(
            candidate_number=1,
            popup_displayed=False,
            disposition="selected",
        )


@dataclass(frozen=True)
class MailboxFullReviewOrchestrationResult:
    """
    PHI-safe summary of one full mailbox review workflow.

    The result excludes message IDs, subjects, filenames, paths,
    OCR text, source_text, extracted values, review payloads,
    Smartsheet payloads, row IDs, and patient data.

    Legacy complete-review counters remain for result compatibility;
    normal automatic production processing does not use them as gates.
    """

    message_count: int | None
    document_count: int | None
    classification_submitted_count: int
    classification_cancelled_count: int
    approved_count: int
    written_count: int
    rejected_count: int
    complete_review_cancelled_count: int
    failed_count: int
    success: bool
    status: str
    stage: str = "completed"
    failure_category: str | None = None
    retryable: bool = False
    row_attempt_count: int | None = None
    attachment_attempt_count: int | None = None
    pending_document_count: int | None = None
    completed_document_count: int = 0
    row_action: str = "skipped"
    attachment_action: str = "skipped"
    filename_readiness: FilenameReadinessDiagnostic | None = None
    review_reason_count: int = 0
    review_reason_categories: tuple[str, ...] = ()
    validation_summary: FinalValidationSummary = FinalValidationSummary()
    row_create_attempted: bool = False
    row_outcome_proven: bool = False
    reconciliation_attempted: bool = False
    reconciliation_match_cardinality: str = "not_attempted"
    row_recovery_state: str = "none"
    attachment_blocked_due_to_unresolved_row: bool = False
    recoverable: bool = False
    request_contract_version: int = 0
    request_contract_rearm_count: int = 0
    mapped_field_count: int = 0
    included_cell_count: int = 0
    omitted_field_count: int = 0
    mapping_validation_passed: bool = False
    schema_validation_passed: bool = False
    type_validation_passed: bool = False
    rejected_field_categories: tuple[str, ...] = ()
    rejection_safe_category: str = "none"
    api_status_class: str = "unavailable"
    api_error_code: int | None = None


class MailboxClassificationReviewMode(str, Enum):
    """Explicit application-owned disposition for local classification review."""

    INTERACTIVE = "interactive"
    DOWNSTREAM = "downstream"
    DEMO_SKIP = "demo_skip"


class MailboxFullReviewOrchestrationService:
    """
    Coordinates one explicit full mailbox workflow.

    Order:

    mailbox processing
    -> automatic Smartsheet submission
    -> conditional downstream classification review/feedback

    Classification confirmation is not a separate write credential.
    """

    def __init__(
        self,
        *,
        mailbox_processor: MailboxProcessor | None = None,
        classification_review_session: (
            MailboxReviewSessionService
            | None
        ) = None,
        complete_review_smartsheet_service: (
            MailboxCompleteReviewSmartsheetService
            | None
        ) = None,
        acceptance_handoff_service: MailboxAcceptanceHandoffService | None = None,
    ) -> None:
        self.mailbox_processor = (
            mailbox_processor
            or MailboxProcessor()
        )

        self.classification_review_session = (
            classification_review_session
            or MailboxReviewSessionService()
        )

        self.complete_review_smartsheet_service = (
            complete_review_smartsheet_service
            or MailboxCompleteReviewSmartsheetService()
        )
        self.acceptance_handoff_service = (
            acceptance_handoff_service or MailboxAcceptanceHandoffService()
        )

    def run(
        self,
        *,
        top: Any = 10,
        created_at: Any = None,
        review_mode: MailboxClassificationReviewMode = (
            MailboxClassificationReviewMode.INTERACTIVE
        ),
        run_type: str = "",
        acceptance_max_messages: int | None = None,
        acceptance_max_documents: int | None = None,
        acceptance_selector=None,
        acceptance_identity: str | None = None,
        acceptance_discovery_top: int = 10,
        acceptance_require_popup: bool = True,
        stage_observer=None,
    ) -> MailboxFullReviewOrchestrationResult:
        normalized_top = self._normalize_top(
            top
        )

        if normalized_top is None:
            return self._failure(
                "invalid_top",
                stage="input_validation",
            )

        if not isinstance(review_mode, MailboxClassificationReviewMode):
            return self._failure(
                "invalid_review_mode",
                stage="input_validation",
            )

        try:
            processing_options = {}
            if acceptance_max_messages is not None or acceptance_max_documents is not None:
                processing_options.update(
                    acceptance_max_messages=acceptance_max_messages,
                    acceptance_max_documents=acceptance_max_documents,
                )
            if stage_observer is not None:
                processing_options["stage_observer"] = stage_observer
            if acceptance_identity is not None:
                message_results = self.mailbox_processor.process_preselected_acceptance(
                    acceptance_identity,
                    **processing_options,
                )
            elif acceptance_selector is None:
                message_results = self.mailbox_processor.process_unread_messages(
                    top=normalized_top,
                    **processing_options,
                )
            else:
                message_results = (
                    self.mailbox_processor.process_selected_unread_message(
                        selector=acceptance_selector,
                        discovery_top=acceptance_discovery_top,
                        require_popup=acceptance_require_popup,
                        **processing_options,
                    )
                )
        except MailboxAcceptanceGuardError as error:
            return self._failure(
                error.category,
                stage="acceptance_guard",
                message_count=error.message_count,
                document_count=error.document_count,
            )
        except Exception:
            return self._failure(
                "mailbox_processing_failed",
                stage="mailbox_processing",
            )

        try:
            action_started_at = __import__("time").perf_counter()
            complete_run = self.complete_review_smartsheet_service.run
            complete_arguments = {
                "message_results": message_results,
                "run_type": run_type,
            }
            parameters = inspect.signature(complete_run).parameters
            if (
                "stage_observer" in parameters
                or any(
                    parameter.kind == inspect.Parameter.VAR_KEYWORD
                    for parameter in parameters.values()
                )
            ):
                complete_arguments["stage_observer"] = stage_observer
            complete_result = complete_run(**complete_arguments)
            row_stage = f"smartsheet_row_{complete_result.row_action}"
            if complete_result.row_action == "failed":
                row_stage = (
                    "smartsheet_row_outcome_unresolved"
                    if complete_result.row_recovery_state == "reconcile_only"
                    else "smartsheet_row_write_failed"
                )
            self._observe(
                stage_observer, row_stage,
                "failed" if complete_result.row_action == "failed" else "completed",
                action_started_at,
            )
            attachment_stage = (
                "smartsheet_attachment_blocked"
                if complete_result.attachment_blocked_due_to_unresolved_row
                else f"smartsheet_attachment_{complete_result.attachment_action}"
            )
            self._observe(
                stage_observer, attachment_stage,
                "failed" if (
                    complete_result.attachment_action == "failed"
                    or complete_result.attachment_blocked_due_to_unresolved_row
                ) else "completed",
                action_started_at,
            )
        except Exception:
            mailbox_summary = (
                self._build_noninteractive_classification_result(
                    message_results,
                    review_mode=MailboxClassificationReviewMode.DOWNSTREAM,
                )
            )
            return self._build_result(
                message_results=message_results,
                message_count=mailbox_summary.message_count,
                document_count=mailbox_summary.document_count,
                failed_count=1,
                success=False,
                status="smartsheet_submission_failed",
                stage="business_actions",
                failure_category="smartsheet_submission_failed",
            )

        message_error_count = sum(
            bool(getattr(result, "errors", None))
            for result in message_results
        )

        if complete_result.status == "no_documents" and message_error_count:
            return self._build_result(
                message_results=message_results,
                message_count=complete_result.message_count,
                document_count=0,
                failed_count=message_error_count,
                success=False,
                status="mailbox_items_failed",
                stage="mailbox_processing",
                failure_category="mailbox_item_failed",
            )

        if complete_result.status == "no_documents":
            return self._build_result(
                message_results=message_results,
                message_count=complete_result.message_count,
                document_count=0,
                failed_count=0,
                success=True,
                status="no_documents",
                stage="completed",
            )

        if not complete_result.success:
            return self._build_result(
                message_results=message_results,
                message_count=complete_result.message_count,
                document_count=complete_result.document_count,
                approved_count=complete_result.approved_count,
                written_count=complete_result.written_count,
                rejected_count=complete_result.rejected_count,
                complete_review_cancelled_count=(
                    complete_result.cancelled_count
                ),
                failed_count=complete_result.failed_count,
                success=False,
                status=complete_result.status,
                stage="business_actions",
                failure_category=(
                    complete_result.failure_category or complete_result.status
                ),
                row_action=complete_result.row_action,
                attachment_action=complete_result.attachment_action,
            )

        for message_result in message_results:
            if getattr(message_result, "work_items", None):
                if not getattr(message_result, "business_actions_completed", False):
                    return self._build_result(
                        message_results=message_results,
                        message_count=complete_result.message_count,
                        document_count=complete_result.document_count,
                        approved_count=complete_result.approved_count,
                        written_count=complete_result.written_count,
                        rejected_count=complete_result.rejected_count,
                        complete_review_cancelled_count=complete_result.cancelled_count,
                        failed_count=max(1, complete_result.failed_count),
                        success=False,
                        status="business_completion_incomplete",
                        stage="business_actions",
                        failure_category="business_completion_incomplete",
                        row_action=complete_result.row_action,
                        attachment_action=complete_result.attachment_action,
                    )
                if not self.mailbox_processor.complete_message(message_result):
                    return self._build_result(
                        message_results=message_results,
                        message_count=complete_result.message_count,
                        document_count=complete_result.document_count,
                        approved_count=complete_result.approved_count,
                        written_count=complete_result.written_count,
                        rejected_count=complete_result.rejected_count,
                        complete_review_cancelled_count=complete_result.cancelled_count,
                        failed_count=1,
                        success=False,
                        status="mailbox_completion_failed",
                        stage="mailbox_completion",
                        failure_category="mailbox_completion_failed",
                        row_action=complete_result.row_action,
                        attachment_action=complete_result.attachment_action,
                    )
        self._observe(stage_observer, "mailbox_completion", "completed", action_started_at)

        if review_mode in {
            MailboxClassificationReviewMode.DOWNSTREAM,
            MailboxClassificationReviewMode.DEMO_SKIP,
        }:
            classification_result = (
                self._build_noninteractive_classification_result(
                    message_results,
                    review_mode=review_mode,
                )
            )
            self._observe(stage_observer, "downstream_review", "completed", action_started_at)
        else:
            try:
                classification_result = (
                    self.classification_review_session.run(
                        message_results=message_results,
                        created_at=created_at,
                    )
                )
            except Exception:
                return self._build_result(
                    message_results=message_results,
                    message_count=complete_result.message_count,
                    document_count=complete_result.document_count,
                    approved_count=complete_result.approved_count,
                    written_count=complete_result.written_count,
                    rejected_count=complete_result.rejected_count,
                    complete_review_cancelled_count=(
                        complete_result.cancelled_count
                    ),
                    failed_count=(
                        complete_result.failed_count + 1
                    ),
                    success=False,
                    status="completed_with_review_failures",
                    stage="downstream_review",
                    failure_category="interactive_review_failed",
                    row_action=complete_result.row_action,
                    attachment_action=complete_result.attachment_action,
                )

        if not classification_result.success:
            return self._build_result(
                message_results=message_results,
                message_count=(
                    classification_result.message_count
                ),
                document_count=(
                    classification_result.document_count
                ),
                classification_submitted_count=(
                    classification_result.submitted_count
                ),
                classification_cancelled_count=(
                    classification_result.cancelled_count
                ),
                approved_count=complete_result.approved_count,
                written_count=complete_result.written_count,
                rejected_count=complete_result.rejected_count,
                complete_review_cancelled_count=(
                    complete_result.cancelled_count
                ),
                failed_count=(
                    complete_result.failed_count
                    + classification_result.failed_count
                ),
                success=False,
                status="completed_with_review_failures",
                stage="downstream_review",
                failure_category="interactive_review_failed",
                row_action=complete_result.row_action,
                attachment_action=complete_result.attachment_action,
            )

        failed_count = (
            classification_result.failed_count
            + complete_result.failed_count
        )

        success = (
            classification_result.success
            and complete_result.success
        )

        if not success:
            status = "completed_with_failures"

        else:
            status = "completed"

        result = self._build_result(
            message_results=message_results,
            message_count=(
                classification_result.message_count
            ),
            document_count=(
                classification_result.document_count
            ),
            classification_submitted_count=(
                classification_result.submitted_count
            ),
            classification_cancelled_count=(
                classification_result.cancelled_count
            ),
            approved_count=(
                complete_result.approved_count
            ),
            written_count=(
                complete_result.written_count
            ),
            rejected_count=(
                complete_result.rejected_count
            ),
            complete_review_cancelled_count=(
                complete_result.cancelled_count
            ),
            failed_count=failed_count,
            success=success,
            status=status,
            stage="completed" if success else "downstream_review",
            failure_category=None if success else "workflow_failed",
            row_action=complete_result.row_action,
            attachment_action=complete_result.attachment_action,
            filename_readiness=complete_result.filename_readiness,
            review_reason_count=complete_result.review_reason_count,
            review_reason_categories=complete_result.review_reason_categories,
            validation_summary=complete_result.validation_summary,
        )
        if result.success:
            self._observe(stage_observer, "completed", "completed", action_started_at)
        return result

    def run_selected_acceptance(
        self,
        *,
        discovery_top: int = 10,
        created_at: Any = None,
        review_mode: MailboxClassificationReviewMode = (
            MailboxClassificationReviewMode.DOWNSTREAM
        ),
        run_type: str = "",
        acceptance_max_messages: int = 1,
        acceptance_max_documents: int = 1,
        stage_observer=None,
        selector=None,
    ) -> MailboxFullReviewOrchestrationResult:
        """Run one explicit popup-selected manual acceptance."""
        if selector is None:
            from src.ui.mailbox_acceptance_selection import (
                LocalMailboxAcceptanceSelector,
            )

            selector = LocalMailboxAcceptanceSelector()
        return self.run(
            top=1,
            created_at=created_at,
            review_mode=review_mode,
            run_type=run_type,
            acceptance_max_messages=acceptance_max_messages,
            acceptance_max_documents=acceptance_max_documents,
            acceptance_selector=selector,
            acceptance_discovery_top=discovery_top,
            stage_observer=stage_observer,
        )

    def run_handoff_acceptance(
        self,
        *,
        created_at: Any = None,
        review_mode: MailboxClassificationReviewMode = MailboxClassificationReviewMode.DOWNSTREAM,
        run_type: str = "",
        acceptance_max_messages: int = 1,
        acceptance_max_documents: int = 1,
        stage_observer=None,
    ) -> MailboxFullReviewOrchestrationResult:
        """Atomically claim a sealed identity and run only that exact candidate."""
        handoff_started_at = __import__("time").perf_counter()
        self._observe(stage_observer, "acceptance_handoff", "started", handoff_started_at)
        try:
            handoff = self.acceptance_handoff_service.claim()
        except MailboxAcceptanceHandoffError as error:
            self._observe(
                stage_observer, "acceptance_handoff", "failed", handoff_started_at,
                failure_category=error.category,
            )
            return self._failure(error.category, stage="acceptance_handoff")
        except Exception:
            self._observe(
                stage_observer, "acceptance_handoff", "failed", handoff_started_at,
                failure_category="handoff_claim_failed",
            )
            return self._failure("handoff_claim_failed", stage="acceptance_handoff")
        self._observe(stage_observer, "acceptance_handoff", "completed", handoff_started_at)
        return self.run(
            top=1,
            created_at=created_at,
            review_mode=review_mode,
            run_type=run_type,
            acceptance_max_messages=acceptance_max_messages,
            acceptance_max_documents=acceptance_max_documents,
            acceptance_identity=handoff.message_identity,
            stage_observer=stage_observer,
        )

    def run_unattended_once(
        self,
        *,
        review_mode: MailboxClassificationReviewMode = MailboxClassificationReviewMode.DOWNSTREAM,
        run_type: str = "",
        discovery_top: int = 10,
        stage_observer=None,
    ) -> MailboxFullReviewOrchestrationResult:
        """Process at most the newest eligible candidate without a popup."""
        result = self.run(
            top=1,
            review_mode=review_mode,
            run_type=run_type,
            acceptance_max_messages=1,
            acceptance_max_documents=1,
            acceptance_selector=FirstEligibleMailboxCandidateSelector(),
            acceptance_discovery_top=discovery_top,
            acceptance_require_popup=False,
            stage_observer=stage_observer,
        )
        if result.failure_category != "acceptance_no_eligible_candidate":
            return result
        return self._build_result(
            message_results=[],
            message_count=0,
            document_count=0,
            failed_count=0,
            success=True,
            status="no_eligible_candidate",
            stage="completed",
        )

    @staticmethod
    def _observe(observer, stage, status, started_at, **metadata):
        if callable(observer):
            duration = max(0.0, __import__("time").perf_counter() - started_at)
            observer(stage=stage, status=status, duration_seconds=duration, **metadata)

    @staticmethod
    def _build_noninteractive_classification_result(
        message_results,
        *,
        review_mode: MailboxClassificationReviewMode,
    ) -> MailboxReviewSessionResult:
        """
        Build a PHI-safe demo-only classification-review summary.

        This does not alter AI classification, extraction, validation,
        business rules, review output, or Smartsheet write readiness.
        """
        try:
            results = list(
                message_results
            )
        except TypeError:
            return MailboxReviewSessionResult(
                message_count=0,
                document_count=0,
                submitted_count=0,
                cancelled_count=0,
                failed_count=1,
                success=False,
                status="invalid_message_results",
            )

        document_count = 0

        for result in results:
            documents = getattr(
                result,
                "processed_documents",
                None,
            )

            if not isinstance(
                documents,
                list,
            ):
                return MailboxReviewSessionResult(
                    message_count=len(
                        results
                    ),
                    document_count=document_count,
                    submitted_count=0,
                    cancelled_count=0,
                    failed_count=1,
                    success=False,
                    status="invalid_processed_documents",
                )

            document_count += len(
                documents
            )

        return MailboxReviewSessionResult(
            message_count=len(
                results
            ),
            document_count=document_count,
            submitted_count=0,
            cancelled_count=0,
            failed_count=0,
            success=True,
            status=(
                "no_documents"
                if document_count == 0
                else (
                    "classification_review_deferred_downstream"
                    if review_mode == MailboxClassificationReviewMode.DOWNSTREAM
                    else "classification_review_skipped_demo"
                )
            ),
        )

    def _build_result(
        self,
        *,
        message_results,
        message_count: int,
        document_count: int,
        failed_count: int,
        success: bool,
        status: str,
        stage: str,
        failure_category: str | None = None,
        classification_submitted_count: int = 0,
        classification_cancelled_count: int = 0,
        approved_count: int = 0,
        written_count: int = 0,
        rejected_count: int = 0,
        complete_review_cancelled_count: int = 0,
        row_action: str = "skipped",
        attachment_action: str = "skipped",
        filename_readiness: FilenameReadinessDiagnostic | None = None,
        review_reason_count: int = 0,
        review_reason_categories: tuple[str, ...] = (),
        validation_summary: FinalValidationSummary = FinalValidationSummary(),
    ) -> MailboxFullReviewOrchestrationResult:
        results = list(message_results)
        job_keys = [
            item.job_key
            for result in results
            for item in getattr(result, "work_items", [])
        ]
        state_service = getattr(self.mailbox_processor, "job_state_service", None)
        summary_method = getattr(state_service, "summarize", None)

        if job_keys and callable(summary_method):
            summary = summary_method(job_keys)
            row_attempt_count = summary.row_attempt_count
            attachment_attempt_count = summary.attachment_attempt_count
            pending_document_count = summary.pending_document_count
            completed_document_count = summary.completed_document_count
            row_create_attempted = summary.row_create_attempted
            row_outcome_proven = summary.row_outcome_proven
            reconciliation_attempted = summary.row_reconciliation_attempted
            reconciliation_match_cardinality = (
                summary.row_reconciliation_match_cardinality
            )
            row_recovery_state = summary.row_recovery_state
            attachment_blocked_due_to_unresolved_row = (
                summary.attachment_blocked_due_to_unresolved_row
            )
            recoverable = summary.recoverable
            request_contract_version = summary.row_request_contract_version
            request_contract_rearm_count = (
                summary.row_request_contract_rearm_count
            )
            mapped_field_count = summary.row_mapped_field_count
            included_cell_count = summary.row_included_cell_count
            omitted_field_count = summary.row_omitted_field_count
            mapping_validation_passed = (
                summary.row_mapping_validation_passed
            )
            schema_validation_passed = summary.row_schema_validation_passed
            type_validation_passed = summary.row_type_validation_passed
            rejected_field_categories = (
                summary.row_rejected_field_categories
            )
            rejection_safe_category = summary.row_rejection_safe_category
            api_status_class = summary.row_api_status_class
            api_error_code = summary.row_api_error_code
            if not summary.success or summary.pending_document_count:
                failure_category = summary.failure_category or failure_category
            retryable = bool(not success and summary.success and summary.retryable)
        elif not job_keys and document_count == 0 and not failed_count:
            row_attempt_count = 0
            attachment_attempt_count = 0
            pending_document_count = 0
            completed_document_count = 0
            retryable = False
            row_create_attempted = False
            row_outcome_proven = False
            reconciliation_attempted = False
            reconciliation_match_cardinality = "not_attempted"
            row_recovery_state = "none"
            attachment_blocked_due_to_unresolved_row = False
            recoverable = False
            request_contract_version = 0
            request_contract_rearm_count = 0
            mapped_field_count = 0
            included_cell_count = 0
            omitted_field_count = 0
            mapping_validation_passed = False
            schema_validation_passed = False
            type_validation_passed = False
            rejected_field_categories = ()
            rejection_safe_category = "none"
            api_status_class = "unavailable"
            api_error_code = None
        else:
            row_attempt_count = None
            attachment_attempt_count = None
            pending_document_count = None
            completed_document_count = 0
            retryable = False
            row_create_attempted = False
            row_outcome_proven = False
            reconciliation_attempted = False
            reconciliation_match_cardinality = "unavailable"
            row_recovery_state = "blocked"
            attachment_blocked_due_to_unresolved_row = False
            recoverable = False
            request_contract_version = 0
            request_contract_rearm_count = 0
            mapped_field_count = 0
            included_cell_count = 0
            omitted_field_count = 0
            mapping_validation_passed = False
            schema_validation_passed = False
            type_validation_passed = False
            rejected_field_categories = ()
            rejection_safe_category = "none"
            api_status_class = "unavailable"
            api_error_code = None

        return MailboxFullReviewOrchestrationResult(
            message_count=message_count,
            document_count=document_count,
            classification_submitted_count=classification_submitted_count,
            classification_cancelled_count=classification_cancelled_count,
            approved_count=approved_count,
            written_count=written_count,
            rejected_count=rejected_count,
            complete_review_cancelled_count=complete_review_cancelled_count,
            failed_count=failed_count,
            success=success,
            status=status,
            stage=stage,
            failure_category=None if success else failure_category,
            retryable=retryable,
            row_attempt_count=row_attempt_count,
            attachment_attempt_count=attachment_attempt_count,
            pending_document_count=pending_document_count,
            completed_document_count=completed_document_count,
            row_action=row_action,
            attachment_action=attachment_action,
            filename_readiness=filename_readiness,
            review_reason_count=review_reason_count,
            review_reason_categories=review_reason_categories,
            validation_summary=validation_summary,
            row_create_attempted=row_create_attempted,
            row_outcome_proven=row_outcome_proven,
            reconciliation_attempted=reconciliation_attempted,
            reconciliation_match_cardinality=reconciliation_match_cardinality,
            row_recovery_state=row_recovery_state,
            attachment_blocked_due_to_unresolved_row=(
                attachment_blocked_due_to_unresolved_row
            ),
            recoverable=recoverable,
            request_contract_version=request_contract_version,
            request_contract_rearm_count=request_contract_rearm_count,
            mapped_field_count=mapped_field_count,
            included_cell_count=included_cell_count,
            omitted_field_count=omitted_field_count,
            mapping_validation_passed=mapping_validation_passed,
            schema_validation_passed=schema_validation_passed,
            type_validation_passed=type_validation_passed,
            rejected_field_categories=rejected_field_categories,
            rejection_safe_category=rejection_safe_category,
            api_status_class=api_status_class,
            api_error_code=api_error_code,
        )

    @staticmethod
    def _normalize_top(
        value: Any,
    ) -> int | None:
        if isinstance(
            value,
            bool,
        ):
            return None

        try:
            normalized = int(
                value
            )
        except (TypeError, ValueError):
            return None

        if normalized < 1:
            return None

        return normalized

    @staticmethod
    def _failure(
        status: str,
        *,
        stage: str = "completed",
        message_count: int | None = 0,
        document_count: int | None = 0,
    ) -> MailboxFullReviewOrchestrationResult:
        return MailboxFullReviewOrchestrationResult(
            message_count=message_count,
            document_count=document_count,
            classification_submitted_count=0,
            classification_cancelled_count=0,
            approved_count=0,
            written_count=0,
            rejected_count=0,
            complete_review_cancelled_count=0,
            failed_count=0,
            success=False,
            status=status,
            stage=stage,
            failure_category=status,
        )
