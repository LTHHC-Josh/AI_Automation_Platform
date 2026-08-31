"""PHI-safe Prefect adapter for one manual bounded mailbox invocation."""

import re

from prefect import flow, get_run_logger, task
from prefect.context import get_run_context

from src.services.mailbox_full_review_orchestration_service import (
    MailboxClassificationReviewMode,
    MailboxFullReviewOrchestrationResult,
    MailboxFullReviewOrchestrationService,
)


PREFECT_MAILBOX_RUN_TYPE = "Prefect bounded mailbox orchestration"
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
    "smartsheet_row_write": "smartsheet-write",
    "attachment_upload": "smartsheet-attachment",
    "review_determination": "review-determination",
    "downstream_review": "review-state",
    "mailbox_completion": "mailbox-finalization",
    "completed": "workflow-completion",
}
_STAGE_STATUSES = {
    "started", "completed", "failed", "skipped", "cancelled", "passed",
    "review_required",
}
_SAFE_CATEGORY = re.compile(r"^[a-z][a-z0-9_]{0,79}$")


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


@task(
    name="bounded-mailbox-application-run",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def run_bounded_mailbox_application() -> MailboxFullReviewOrchestrationResult:
    """Call the complete application boundary exactly once."""
    logger = get_run_logger()

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
        _record_stage_visibility(visibility)
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
        result = MailboxFullReviewOrchestrationService().run_handoff_acceptance(
            review_mode=MailboxClassificationReviewMode.DOWNSTREAM,
            run_type=PREFECT_MAILBOX_RUN_TYPE,
            acceptance_max_messages=PREFECT_MANUAL_MAILBOX_MESSAGE_LIMIT,
            acceptance_max_documents=PREFECT_MANUAL_MAILBOX_DOCUMENT_LIMIT,
            stage_observer=observe_stage,
        )
    except Exception:
        raise SanitizedMailboxRunError(
            "stage=mailbox_processing status=failed "
            "failure_category=application_boundary_failed retryable=false"
        ) from None

    logger.info(
        "stage=%s status=%s failure_category=%s retryable=%s "
        "message_count=%s document_count=%s written_count=%s failed_count=%s "
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
        result.row_attempt_count,
        result.attachment_attempt_count,
        result.pending_document_count,
        result.completed_document_count,
    )

    if not result.success:
        raise SanitizedMailboxRunError(
            f"stage={result.stage} status={result.status} "
            f"failure_category={result.failure_category or 'operation_failed'} "
            f"retryable={str(result.retryable).lower()}"
        ) from None

    return result


@flow(
    name="lthhc-bounded-mailbox",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def bounded_mailbox_flow() -> MailboxFullReviewOrchestrationResult:
    """Run one bounded application invocation with no internal polling loop."""
    return run_bounded_mailbox_application()
