from dataclasses import dataclass
from typing import Any

from src.graph.mailbox_processor import MailboxProcessor
from src.services.mailbox_review_session_service import (
    MailboxReviewSessionService,
)


@dataclass(frozen=True)
class MailboxReviewOrchestrationResult:
    """
    PHI-safe result from mailbox processing followed by local review.

    The result excludes message identifiers, subjects, attachment
    paths, filenames, OCR text, extracted values, review evidence,
    fingerprints, correction labels, and storage payloads.
    """

    message_count: int
    document_count: int
    submitted_count: int
    cancelled_count: int
    failed_count: int
    success: bool
    status: str


class MailboxReviewOrchestrationService:
    """
    Connects mailbox processing to the explicit local review session.

    MailboxProcessor remains responsible for mailbox ingestion,
    attachment download, and document processing.

    MailboxReviewSessionService remains responsible for explicit
    reviewer interaction.

    This service does not inspect, log, print, copy, or return message
    identifiers, subjects, paths, OCR text, extracted values, review
    evidence, correction labels, fingerprints, or storage payloads.
    """

    def __init__(
        self,
        *,
        mailbox_processor: MailboxProcessor | None = None,
        review_session: MailboxReviewSessionService | None = None,
    ) -> None:
        self.mailbox_processor = (
            mailbox_processor
            or MailboxProcessor()
        )

        self.review_session = (
            review_session
            or MailboxReviewSessionService()
        )

    def run(
        self,
        *,
        top: int = 10,
        created_at: Any = None,
    ) -> MailboxReviewOrchestrationResult:
        """
        Process unread messages and review returned documents.
        """

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
            review_result = self.review_session.run(
                message_results=message_results,
                created_at=created_at,
            )
        except Exception:
            return self._failure(
                "review_session_failed"
            )

        if not review_result.success:
            orchestration_status = (
                review_result.status
            )
        elif review_result.status == "no_documents":
            orchestration_status = "no_documents"
        elif (
            review_result.status
            == "completed_with_cancellations"
        ):
            orchestration_status = (
                "completed_with_cancellations"
            )
        else:
            orchestration_status = "completed"

        return MailboxReviewOrchestrationResult(
            message_count=review_result.message_count,
            document_count=review_result.document_count,
            submitted_count=review_result.submitted_count,
            cancelled_count=review_result.cancelled_count,
            failed_count=review_result.failed_count,
            success=review_result.success,
            status=orchestration_status,
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
    ) -> MailboxReviewOrchestrationResult:
        return MailboxReviewOrchestrationResult(
            message_count=0,
            document_count=0,
            submitted_count=0,
            cancelled_count=0,
            failed_count=0,
            success=False,
            status=status,
        )
