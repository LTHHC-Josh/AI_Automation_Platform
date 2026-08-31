"""PHI-safe Prefect adapter for one manual bounded mailbox invocation."""

from prefect import flow, get_run_logger, task

from src.services.mailbox_full_review_orchestration_service import (
    MailboxClassificationReviewMode,
    MailboxFullReviewOrchestrationResult,
    MailboxFullReviewOrchestrationService,
)


PREFECT_MAILBOX_RUN_TYPE = "Prefect bounded mailbox orchestration"
PREFECT_MANUAL_MAILBOX_MESSAGE_LIMIT = 1
PREFECT_MANUAL_MAILBOX_DOCUMENT_LIMIT = 1
PREFECT_MANUAL_MAILBOX_DISCOVERY_LIMIT = 10


class SanitizedMailboxRunError(RuntimeError):
    """A Prefect-visible failure containing allowlisted metadata only."""


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
                      failure_category=None):
        logger.info(
            "stage=%s status=%s duration_seconds=%s attempt_count=%s "
            "candidate_message_count=%s candidate_document_count=%s "
            "discovery_completed=%s eligible_candidate_count=%s "
            "popup_displayed=%s candidate_selected=%s "
            "candidate_available=%s unread_state_proven=%s "
            "inbox_membership_proven=%s exact_identity_match_proven=%s "
            "exactly_one_supported_document_proven=%s "
            "retryable=false failure_category=%s",
            stage, status, duration_seconds, attempt_count,
            candidate_message_count, candidate_document_count,
            discovery_completed, eligible_candidate_count,
            popup_displayed, candidate_selected,
            candidate_available, unread_state_proven,
            inbox_membership_proven, exact_identity_match_proven,
            exactly_one_supported_document_proven,
            failure_category or "none",
        )

    try:
        result = MailboxFullReviewOrchestrationService().run_selected_acceptance(
            discovery_top=PREFECT_MANUAL_MAILBOX_DISCOVERY_LIMIT,
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
