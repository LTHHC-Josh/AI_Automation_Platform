"""PHI-safe Prefect adapter for one manual bounded mailbox invocation."""

import re
from uuid import uuid4

from prefect import flow, get_run_logger, task
from prefect.client.orchestration import get_client
from prefect.context import get_run_context
from prefect.states import Completed, Failed, Running

from src.services.mailbox_full_review_orchestration_service import (
    MailboxClassificationReviewMode,
    MailboxFullReviewOrchestrationResult,
    MailboxFullReviewOrchestrationService,
)


PREFECT_MAILBOX_RUN_TYPE = "Prefect bounded mailbox orchestration"
PREFECT_UNATTENDED_MAILBOX_RUN_TYPE = "Prefect unattended mailbox orchestration"
PREFECT_MANUAL_MAILBOX_MESSAGE_LIMIT = 1
PREFECT_MANUAL_MAILBOX_DOCUMENT_LIMIT = 1
PREFECT_MANUAL_MAILBOX_DISCOVERY_LIMIT = 10

_STAGE_NAMES = {
    "acceptance_handoff": "acceptance-handoff",
    "acceptance_guard": "candidate-readiness",
    "mailbox_discovery": "candidate-readiness",
    "candidate_selection": "candidate-readiness",
    "candidate_reverification": "candidate-reverification",
    "attachment_download": "document-acquisition",
    "ocr": "ocr",
    "classification": "document-classification",
    "extraction_attempt_1": "extraction-attempt-1",
    "validation_attempt_1": "validation-attempt-1",
    "extraction_retry_decision": "extraction-retry-decision",
    "extraction_attempt_2": "extraction-attempt-2",
    "validation_attempt_2": "validation-attempt-2",
    "extraction_candidate_selection": "extraction-candidate-selection",
    "document_processing": "document-processing",
    "subtype_classification": "subtype-classification",
    "extraction": "extraction",
    "validation": "deterministic-validation",
    "business_rules": "business-rules",
    "smartsheet_row_created": "Smartsheet Row Created",
    "smartsheet_row_reconciled_existing": "Smartsheet Row Reconciled",
    "smartsheet_row_skipped": "Smartsheet Row Skipped",
    "smartsheet_row_failed": "Smartsheet Row Failed",
    "smartsheet_row_mixed": "Smartsheet Row Mixed Actions",
    "smartsheet_attachment_uploaded": "Smartsheet Attachment Uploaded",
    "smartsheet_attachment_reconciled_existing": "Smartsheet Attachment Reconciled",
    "smartsheet_attachment_skipped": "Smartsheet Attachment Skipped",
    "smartsheet_attachment_failed": "Smartsheet Attachment Failed",
    "smartsheet_attachment_mixed": "Smartsheet Attachment Mixed Actions",
    "review_determination": "review-determination",
    "downstream_review": "review-state",
    "mailbox_completion": "mailbox-finalization",
    "completed": "workflow-completion",
}
_LONG_RUNNING_STAGES = {
    "ocr",
    "classification",
    "subtype_classification",
    "extraction_attempt_1",
    "validation_attempt_1",
    "extraction_attempt_2",
    "validation_attempt_2",
}
_OPERATOR_STAGE_NAMES = {
    "ocr": "OCR",
    "classification": "Document Classification",
    "subtype_classification": "Subtype Classification",
    "extraction_attempt_1": "Extraction Attempt 1",
    "validation_attempt_1": "Validation Attempt 1",
    "extraction_attempt_2": "Extraction Attempt 2",
    "validation_attempt_2": "Validation Attempt 2",
}
_STAGE_STATUSES = {
    "started", "completed", "failed", "skipped", "cancelled", "passed",
    "review_required",
}
_SAFE_CATEGORY = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
_SAFE_ROW_ACTIONS = {"created", "reconciled_existing", "skipped", "failed", "mixed"}
_SAFE_ATTACHMENT_ACTIONS = {
    "uploaded", "reconciled_existing", "skipped", "failed", "mixed",
}


class SanitizedMailboxRunError(RuntimeError):
    """A Prefect-visible failure containing allowlisted metadata only."""


@task(
    name="mailbox-lifecycle-stage",
    task_run_name="{stage}-{status}",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def record_mailbox_lifecycle_stage(
    *,
    stage: str,
    status: str,
    duration_seconds: float | None = None,
    attempt_count: int | None = None,
    message_count: int | None = None,
    document_count: int | None = None,
    review_required: bool | None = None,
    attempt: int | None = None,
    selected_attempt: int | None = None,
    retry_triggered: bool | None = None,
    raw_retry_required: bool | None = None,
    validated_retry_required: bool | None = None,
    extraction_wall_seconds: float | None = None,
    validation_wall_seconds: float | None = None,
    ollama_total_duration_seconds: float | None = None,
    ollama_load_duration_seconds: float | None = None,
    ollama_prompt_eval_duration_seconds: float | None = None,
    ollama_eval_duration_seconds: float | None = None,
    prompt_token_count: int | None = None,
    generated_token_count: int | None = None,
    ocr_fingerprint_seconds: float | None = None,
    ocr_engine_init_seconds: float | None = None,
    ocr_predict_return_seconds: float | None = None,
    ocr_result_consumption_seconds: float | None = None,
    ocr_result_conversion_seconds: float | None = None,
    ocr_text_traversal_seconds: float | None = None,
    ocr_page_block_construction_seconds: float | None = None,
    ocr_predict_call_count: int | None = None,
    ocr_document_submission_count: int | None = None,
    ocr_result_count: int | None = None,
    ocr_recognized_block_count: int | None = None,
    failure_category: str = "none",
) -> None:
    """Create one PHI-safe Prefect task run for an application lifecycle event."""


@task(
    name="Workflow Summary",
    task_run_name="Workflow Summary",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def record_mailbox_workflow_summary(
    *,
    final_workflow_status: str,
    document_count: int,
    written_count: int,
    failed_count: int,
    row_action: str = "skipped",
    attachment_action: str = "skipped",
    row_attempt_count: int = 0,
    attachment_attempt_count: int = 0,
    completed_document_count: int = 0,
    filename_person_components: str = "Unresolved",
    filename_payer_lookup: str = "Unresolved",
    filename_service_lookup: str = "Unresolved",
    filename_form: str = "Omitted",
    filename_dates: str = "Unresolved",
    filename_extension: str = "Unresolved",
    filename_workflow: str = "Unresolved",
    filename_qualifier: str = "Unresolved",
    filename_result: str = "technical_fallback",
    filename_failure_category: str = "not_evaluated",
    business_filename_attempted: bool = False,
    required_component_failure_count: int = 0,
    optional_component_omission_count: int = 0,
    accepted_field_count: int = 0,
    optional_absent_field_count: int = 0,
    missing_required_count: int = 0,
    low_confidence_count: int = 0,
    unsupported_count: int = 0,
    ambiguous_count: int = 0,
    conflicting_count: int = 0,
    invalid_count: int = 0,
    quantity_present: bool = False,
    unit_source_category: str = "unresolved",
    review_reason_count: int = 0,
    review_reason_categories: str = "none",
    review_required: bool | None = None,
    attempt_count: int | None = None,
    selected_attempt: int | None = None,
    retry_triggered: bool | None = None,
    ocr_duration_seconds: float | None = None,
    classification_duration_seconds: float | None = None,
    extraction_duration_seconds: float | None = None,
    validation_duration_seconds: float | None = None,
    document_processing_duration_seconds: float | None = None,
    ollama_total_duration_seconds: float | None = None,
    prompt_token_count: int | None = None,
    generated_token_count: int | None = None,
) -> None:
    """Expose only the already-normalized operational summary in Prefect."""
    safe_summary = locals()
    get_run_logger().info(
        " ".join(
            f"{key}={str(value).lower() if isinstance(value, bool) else value}"
            for key, value in safe_summary.items()
            if value is not None
        )
    )


class _RunningStageVisibility:
    """Manage PHI-free Prefect child task states around application stages."""

    def __init__(self):
        self._runs = {}

    def update(self, *, application_stage, status):
        if application_stage not in _LONG_RUNNING_STAGES:
            return False
        context = get_run_context()
        flow_run_id = getattr(getattr(context, "task_run", None), "flow_run_id", None)
        if flow_run_id is None:
            return False
        client = get_client(sync_client=True)
        if status == "started":
            task_run = client.create_task_run(
                task=record_mailbox_lifecycle_stage,
                flow_run_id=flow_run_id,
                dynamic_key=f"stage-{application_stage}-{uuid4().hex}",
                name=_OPERATOR_STAGE_NAMES[application_stage],
                state=Running(),
                task_inputs={},
            )
            self._runs[application_stage] = task_run.id
            return True
        task_run_id = self._runs.pop(application_stage, None)
        if task_run_id is None:
            return False
        terminal_state = Failed(message="Application stage failed") if status == "failed" else Completed()
        client.set_task_run_state(task_run_id, terminal_state, force=True)
        return True

    def fail_open_stages(self):
        client = get_client(sync_client=True)
        for task_run_id in tuple(self._runs.values()):
            client.set_task_run_state(
                task_run_id,
                Failed(message="Application boundary failed"),
                force=True,
            )
        self._runs.clear()


def _normalize_stage_visibility(
    *, stage, status, duration_seconds=None, attempt_count=None,
    candidate_message_count=None, candidate_document_count=None,
    review_required=None, failure_category=None, **operational_metadata,
):
    safe_stage = _STAGE_NAMES.get(stage, "workflow-status")
    safe_status = status if status in _STAGE_STATUSES else "failed"
    safe_category = failure_category if (
        isinstance(failure_category, str) and _SAFE_CATEGORY.fullmatch(failure_category)
    ) else "none" if failure_category is None or failure_category == "" else "sanitized_failure"

    def safe_count(value):
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None

    safe_duration = (
        float(duration_seconds)
        if isinstance(duration_seconds, (int, float))
        and not isinstance(duration_seconds, bool)
        and 0 <= float(duration_seconds) <= 86400
        else None
    )
    normalized = {
        "stage": safe_stage,
        "status": safe_status,
        "duration_seconds": safe_duration,
        "attempt_count": safe_count(attempt_count),
        "message_count": safe_count(candidate_message_count),
        "document_count": safe_count(candidate_document_count),
        "review_required": review_required if isinstance(review_required, bool) else None,
        "failure_category": safe_category,
    }
    duration_fields = {
        "extraction_wall_seconds", "validation_wall_seconds",
        "ollama_total_duration_seconds", "ollama_load_duration_seconds",
        "ollama_prompt_eval_duration_seconds", "ollama_eval_duration_seconds",
        "ocr_fingerprint_seconds", "ocr_engine_init_seconds",
        "ocr_predict_return_seconds", "ocr_result_consumption_seconds",
        "ocr_result_conversion_seconds", "ocr_text_traversal_seconds",
        "ocr_page_block_construction_seconds",
    }
    count_fields = {
        "attempt", "selected_attempt", "prompt_token_count",
        "generated_token_count", "ocr_predict_call_count",
        "ocr_document_submission_count", "ocr_result_count",
        "ocr_recognized_block_count",
    }
    bool_fields = {
        "retry_triggered", "raw_retry_required", "validated_retry_required",
    }
    for field_name in duration_fields:
        value = operational_metadata.get(field_name)
        normalized[field_name] = (
            float(value)
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            and 0 <= float(value) <= 86400
            else None
        )
    for field_name in count_fields:
        normalized[field_name] = safe_count(operational_metadata.get(field_name))
    for field_name in bool_fields:
        value = operational_metadata.get(field_name)
        normalized[field_name] = value if isinstance(value, bool) else None
    return normalized


def _record_stage_visibility(metadata) -> None:
    try:
        try:
            context = get_run_context()
        except Exception:
            context = None
        if context is not None and getattr(context, "task_run", None) is not None:
            record_mailbox_lifecycle_stage(**metadata)
        else:
            record_mailbox_lifecycle_stage.fn(**metadata)
    except Exception:
        # Visibility must never replace the authoritative application failure path.
        return


def _run_mailbox_application(*, unattended: bool) -> MailboxFullReviewOrchestrationResult:
    """Call the complete application boundary exactly once."""
    logger = get_run_logger()
    running_stages = _RunningStageVisibility()
    summary_events = {}

    def observe_stage(*, stage, status, duration_seconds=None, attempt_count=None,
                      candidate_message_count=None, candidate_document_count=None,
                      discovery_completed=None, eligible_candidate_count=None,
                      popup_displayed=None, candidate_selected=None,
                      candidate_available=None, unread_state_proven=None,
                      inbox_membership_proven=None,
                      exact_identity_match_proven=None,
                      exactly_one_supported_document_proven=None,
                      not_unread_count=None, no_supported_document_count=None,
                      multiple_supported_documents_count=None,
                      unsupported_document_type_count=None,
                      document_count_unprovable_count=None,
                      review_required=None,
                      failure_category=None,
                      **operational_metadata):
        visibility = _normalize_stage_visibility(
            stage=stage,
            status=status,
            duration_seconds=duration_seconds,
            attempt_count=attempt_count,
            candidate_message_count=candidate_message_count,
            candidate_document_count=candidate_document_count,
            review_required=review_required,
            failure_category=failure_category,
            **operational_metadata,
        )
        try:
            represented_by_running_task = running_stages.update(
                application_stage=stage,
                status=status,
            )
        except Exception:
            represented_by_running_task = False
        if not represented_by_running_task:
            _record_stage_visibility(visibility)
        if status in {"completed", "review_required"}:
            summary_events[stage] = dict(visibility)
        log_metadata = {
            **visibility,
            "discovery_completed": discovery_completed,
            "eligible_candidate_count": eligible_candidate_count,
            "popup_displayed": popup_displayed,
            "candidate_selected": candidate_selected,
            "candidate_available": candidate_available,
            "unread_state_proven": unread_state_proven,
            "inbox_membership_proven": inbox_membership_proven,
            "exact_identity_match_proven": exact_identity_match_proven,
            "exactly_one_supported_document_proven": (
                exactly_one_supported_document_proven
            ),
            "retryable": False,
        }
        populated = {
            key: value for key, value in log_metadata.items()
            if value is not None and not (key == "failure_category" and value == "none")
        }
        logger.info(
            " ".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}"
                     for key, value in populated.items())
        )

    try:
        service = MailboxFullReviewOrchestrationService()
        if unattended:
            result = service.run_unattended_once(
                review_mode=MailboxClassificationReviewMode.DOWNSTREAM,
                run_type=PREFECT_UNATTENDED_MAILBOX_RUN_TYPE,
                discovery_top=PREFECT_MANUAL_MAILBOX_DISCOVERY_LIMIT,
                stage_observer=observe_stage,
            )
        else:
            result = service.run_handoff_acceptance(
                review_mode=MailboxClassificationReviewMode.DOWNSTREAM,
                run_type=PREFECT_MAILBOX_RUN_TYPE,
                acceptance_max_messages=PREFECT_MANUAL_MAILBOX_MESSAGE_LIMIT,
                acceptance_max_documents=PREFECT_MANUAL_MAILBOX_DOCUMENT_LIMIT,
                stage_observer=observe_stage,
            )
    except Exception:
        try:
            running_stages.fail_open_stages()
        except Exception:
            pass
        raise SanitizedMailboxRunError(
            "stage=mailbox_processing status=failed "
            "failure_category=application_boundary_failed retryable=false"
        ) from None

    logger.info(
        "stage=%s status=%s failure_category=%s retryable=%s "
        "message_count=%s document_count=%s written_count=%s failed_count=%s "
        "row_action=%s attachment_action=%s "
        "row_attempt_count=%s attachment_attempt_count=%s "
        "pending_document_count=%s completed_document_count=%s",
        result.stage,
        result.status,
        result.failure_category or "none",
        str(result.retryable).lower(),
        result.message_count,
        result.document_count,
        result.written_count,
        result.failed_count,
        result.row_action,
        result.attachment_action,
        result.row_attempt_count,
        result.attachment_attempt_count,
        result.pending_document_count,
        result.completed_document_count,
    )

    document_event = summary_events.get("document_processing", {})
    extraction_event = summary_events.get("extraction", {})
    validation_event = summary_events.get("validation", {})
    ocr_event = summary_events.get("ocr", {})
    classification_event = summary_events.get("classification", {})
    candidate_event = summary_events.get("extraction_candidate_selection", {})
    retry_event = summary_events.get("extraction_retry_decision", {})
    review_event = summary_events.get("review_determination", {})
    filename = result.filename_readiness
    safe_summary = {
        "final_workflow_status": result.status,
        "document_count": result.document_count,
        "written_count": result.written_count,
        "failed_count": result.failed_count,
        "row_action": (
            result.row_action if result.row_action in _SAFE_ROW_ACTIONS else "failed"
        ),
        "attachment_action": (
            result.attachment_action
            if result.attachment_action in _SAFE_ATTACHMENT_ACTIONS else "failed"
        ),
        "row_attempt_count": result.row_attempt_count,
        "attachment_attempt_count": result.attachment_attempt_count,
        "completed_document_count": result.completed_document_count,
        "filename_person_components": (
            "Ready" if filename and filename.person_components_ready else "Unresolved"
        ),
        "filename_payer_lookup": (
            "Ready" if filename and filename.payer_lookup_ready else "Unresolved"
        ),
        "filename_service_lookup": (
            filename.service_component_status if filename else "Not Evaluated"
        ),
        "filename_form": (
            filename.form_component_status if filename else "Not Evaluated"
        ),
        "filename_dates": (
            "Ready" if filename and filename.dates_ready else "Unresolved"
        ),
        "filename_extension": (
            filename.extension_component_status
            if filename else "Not Evaluated"
        ),
        "filename_workflow": (
            filename.workflow_component_status if filename else "Not Evaluated"
        ),
        "filename_qualifier": (
            filename.qualifier_status if filename else "Not Evaluated"
        ),
        "filename_result": (
            filename.filename_result if filename else "Not Evaluated"
        ),
        "filename_failure_category": (
            filename.filename_failure_category if filename else "not_evaluated"
        ),
        "business_filename_attempted": (
            filename.business_filename_attempted if filename else False
        ),
        "required_component_failure_count": (
            filename.required_component_failure_count if filename else 0
        ),
        "optional_component_omission_count": (
            filename.optional_component_omission_count if filename else 0
        ),
        "accepted_field_count": result.validation_summary.accepted_field_count,
        "optional_absent_field_count": result.validation_summary.optional_absent_field_count,
        "missing_required_count": result.validation_summary.missing_required_count,
        "low_confidence_count": result.validation_summary.low_confidence_count,
        "unsupported_count": result.validation_summary.unsupported_count,
        "ambiguous_count": result.validation_summary.ambiguous_count,
        "conflicting_count": result.validation_summary.conflicting_count,
        "invalid_count": result.validation_summary.invalid_count,
        "quantity_present": result.validation_summary.quantity_present,
        "unit_source_category": result.validation_summary.unit_source_category,
        "review_reason_count": result.review_reason_count,
        "review_reason_categories": (
            "; ".join(result.review_reason_categories)
            if result.review_reason_categories else "none"
        ),
        "review_required": review_event.get("review_required"),
        "attempt_count": extraction_event.get("attempt_count"),
        "selected_attempt": candidate_event.get("selected_attempt"),
        "retry_triggered": retry_event.get("retry_triggered"),
        "ocr_duration_seconds": ocr_event.get("duration_seconds"),
        "classification_duration_seconds": classification_event.get("duration_seconds"),
        "extraction_duration_seconds": extraction_event.get("duration_seconds"),
        "validation_duration_seconds": validation_event.get("duration_seconds"),
        "document_processing_duration_seconds": document_event.get("duration_seconds"),
        "ollama_total_duration_seconds": summary_events.get(
            f"extraction_attempt_{candidate_event.get('selected_attempt')}", {}
        ).get("ollama_total_duration_seconds"),
        "prompt_token_count": summary_events.get(
            f"extraction_attempt_{candidate_event.get('selected_attempt')}", {}
        ).get("prompt_token_count"),
        "generated_token_count": summary_events.get(
            f"extraction_attempt_{candidate_event.get('selected_attempt')}", {}
        ).get("generated_token_count"),
    }
    try:
        record_mailbox_workflow_summary(**safe_summary)
    except Exception:
        pass

    if not result.success:
        raise SanitizedMailboxRunError(
            f"stage={result.stage} status={result.status} "
            f"failure_category={result.failure_category or 'operation_failed'} "
            f"retryable={str(result.retryable).lower()}"
        ) from None

    return result


@task(
    name="bounded-mailbox-application-run",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def run_bounded_mailbox_application() -> MailboxFullReviewOrchestrationResult:
    """Call the sealed-handoff manual application boundary exactly once."""
    return _run_mailbox_application(unattended=False)


@task(
    name="unattended-mailbox-application-run",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def run_unattended_mailbox_application() -> MailboxFullReviewOrchestrationResult:
    """Discover, re-verify, and process at most one eligible candidate."""
    return _run_mailbox_application(unattended=True)


@flow(
    name="lthhc-bounded-mailbox",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def bounded_mailbox_flow() -> MailboxFullReviewOrchestrationResult:
    """Run one bounded application invocation with no internal polling loop."""
    return run_bounded_mailbox_application()


@flow(
    name="lthhc-unattended-mailbox",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def unattended_mailbox_flow() -> MailboxFullReviewOrchestrationResult:
    """Run one scheduled, bounded, no-popup mailbox check."""
    return run_unattended_mailbox_application()
