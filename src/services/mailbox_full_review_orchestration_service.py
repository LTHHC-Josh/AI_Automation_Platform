from dataclasses import dataclass
from typing import Any

from src.graph.mailbox_processor import (
    MailboxProcessor,
)
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetService,
)
from src.services.mailbox_review_session_service import (
    MailboxReviewSessionService,
)


@dataclass(frozen=True)
class MailboxFullReviewOrchestrationResult:
    """
    PHI-safe summary of one full mailbox review workflow.

    The result excludes message IDs, subjects, filenames, paths,
    OCR text, source_text, extracted values, review payloads,
    Smartsheet payloads, row IDs, and patient data.
    """

    message_count: int
    document_count: int
    classification_submitted_count: int
    classification_cancelled_count: int
    approved_count: int
    written_count: int
    rejected_count: int
    complete_review_cancelled_count: int
    failed_count: int
    success: bool
    status: str


class MailboxFullReviewOrchestrationService:
    """
    Coordinates one explicit full mailbox workflow.

    Order:

    mailbox processing
    -> classification review/feedback
    -> explicit complete review
    -> approved Smartsheet submission

    Classification confirmation never authorizes writing by itself.
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

    def run(
        self,
        *,
        top: Any = 10,
        created_at: Any = None,
    ) -> MailboxFullReviewOrchestrationResult:
        normalized_top = self._normalize_top(
            top
        )

        if normalized_top is None:
            return self._failure(
                "invalid_top"
            )

        try:
            message_results = (
                self.mailbox_processor
                .process_unread_messages(
                    top=normalized_top
                )
            )
        except Exception:
            return self._failure(
                "mailbox_processing_failed"
            )

        try:
            classification_result = (
                self.classification_review_session.run(
                    message_results=message_results,
                    created_at=created_at,
                )
            )
        except Exception:
            return self._failure(
                "classification_review_failed"
            )

        if not classification_result.success:
            return MailboxFullReviewOrchestrationResult(
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
                approved_count=0,
                written_count=0,
                rejected_count=0,
                complete_review_cancelled_count=0,
                failed_count=(
                    classification_result.failed_count
                ),
                success=False,
                status=(
                    classification_result.status
                ),
            )

        if classification_result.status == "no_documents":
            return MailboxFullReviewOrchestrationResult(
                message_count=(
                    classification_result.message_count
                ),
                document_count=0,
                classification_submitted_count=0,
                classification_cancelled_count=0,
                approved_count=0,
                written_count=0,
                rejected_count=0,
                complete_review_cancelled_count=0,
                failed_count=0,
                success=True,
                status="no_documents",
            )

        try:
            complete_result = (
                self.complete_review_smartsheet_service.run(
                    message_results=message_results
                )
            )
        except Exception:
            return MailboxFullReviewOrchestrationResult(
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
                approved_count=0,
                written_count=0,
                rejected_count=0,
                complete_review_cancelled_count=0,
                failed_count=1,
                success=False,
                status="complete_review_failed",
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

        elif complete_result.cancelled_count:
            status = "completed_with_cancellations"

        elif complete_result.rejected_count:
            status = "completed_with_rejections"

        else:
            status = "completed"

        return MailboxFullReviewOrchestrationResult(
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
    ) -> MailboxFullReviewOrchestrationResult:
        return MailboxFullReviewOrchestrationResult(
            message_count=0,
            document_count=0,
            classification_submitted_count=0,
            classification_cancelled_count=0,
            approved_count=0,
            written_count=0,
            rejected_count=0,
            complete_review_cancelled_count=0,
            failed_count=0,
            success=False,
            status=status,
        )
