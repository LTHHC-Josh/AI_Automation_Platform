from dataclasses import dataclass
from typing import Any, Iterable

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.ui.classification_review_interaction import (
    ClassificationReviewInteraction,
)


@dataclass(frozen=True)
class MailboxReviewSessionResult:
    """
    PHI-safe summary of one local mailbox review session.

    The result excludes message identifiers, subjects, source paths,
    filenames, OCR text, extracted values, source evidence, review
    content, correction labels, fingerprints, and storage payloads.
    """

    message_count: int
    document_count: int
    submitted_count: int
    cancelled_count: int
    failed_count: int
    success: bool
    status: str


class MailboxReviewSessionService:
    """
    Coordinates explicit local review of already-processed documents.

    This service does not fetch mail, download attachments, process
    documents, run OCR, call Ollama, perform extraction, validate
    evidence, apply business rules, or mark messages as read.

    It only receives existing MessageProcessingResult objects and
    invokes the supplied ClassificationReviewInteraction once for each
    processed Document.
    """

    CANCELLED_STATUSES = {
        "cancelled",
    }

    def __init__(
        self,
        *,
        review_interaction: (
            ClassificationReviewInteraction
            | None
        ) = None,
    ) -> None:
        self.review_interaction = (
            review_interaction
            or ClassificationReviewInteraction()
        )

    def run(
        self,
        *,
        message_results: Iterable[
            MessageProcessingResult
        ],
        created_at: Any = None,
    ) -> MailboxReviewSessionResult:
        """
        Review processed documents one at a time.
        """

        try:
            results = list(
                message_results
            )
        except TypeError:
            return self._failure(
                status="invalid_message_results",
            )

        if any(
            not isinstance(
                result,
                MessageProcessingResult,
            )
            for result in results
        ):
            return self._failure(
                status="invalid_message_result",
            )

        message_count = len(
            results
        )
        document_count = 0
        submitted_count = 0
        cancelled_count = 0
        failed_count = 0

        for message_result in results:
            for document in (
                message_result.processed_documents
            ):
                document_count += 1

                interaction_result = (
                    self.review_interaction.run(
                        document=document,
                        created_at=created_at,
                    )
                )

                if interaction_result.success:
                    submitted_count += 1
                    continue

                if (
                    interaction_result.status
                    in self.CANCELLED_STATUSES
                ):
                    cancelled_count += 1
                    continue

                failed_count += 1

        if document_count == 0:
            return MailboxReviewSessionResult(
                message_count=message_count,
                document_count=0,
                submitted_count=0,
                cancelled_count=0,
                failed_count=0,
                success=True,
                status="no_documents",
            )

        if failed_count:
            session_status = (
                "completed_with_failures"
            )
            session_succeeded = False
        elif cancelled_count:
            session_status = (
                "completed_with_cancellations"
            )
            session_succeeded = True
        else:
            session_status = "completed"
            session_succeeded = True

        return MailboxReviewSessionResult(
            message_count=message_count,
            document_count=document_count,
            submitted_count=submitted_count,
            cancelled_count=cancelled_count,
            failed_count=failed_count,
            success=session_succeeded,
            status=session_status,
        )

    @staticmethod
    def _failure(
        *,
        status: str,
    ) -> MailboxReviewSessionResult:
        return MailboxReviewSessionResult(
            message_count=0,
            document_count=0,
            submitted_count=0,
            cancelled_count=0,
            failed_count=0,
            success=False,
            status=status,
        )
