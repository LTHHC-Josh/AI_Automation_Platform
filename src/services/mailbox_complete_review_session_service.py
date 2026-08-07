from dataclasses import dataclass
from typing import Iterable

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.services.complete_review_approval_service import (
    CompleteReviewApprovalResult,
)
from src.ui.complete_review_approval_interaction import (
    CompleteReviewApprovalInteraction,
)


@dataclass(frozen=True)
class MailboxCompleteReviewSessionResult:
    """
    PHI-safe summary of one complete-review mailbox session.

    The result excludes message identifiers, subjects, filenames,
    file paths, OCR text, extracted values, source_text, review
    payloads, and patient data.
    """

    message_count: int
    document_count: int
    approved_count: int
    rejected_count: int
    cancelled_count: int
    failed_count: int
    success: bool
    status: str


class MailboxCompleteReviewSessionService:
    """
    Coordinates explicit complete-review approval for already
    processed mailbox documents.

    This service does not fetch mail, download attachments, process
    documents, run OCR, call Ollama, rerun validation, apply business
    rules, perform classification feedback, or call Smartsheet.

    It invokes the supplied CompleteReviewApprovalInteraction once
    for each processed document that has structured review output.
    """

    CANCELLED_STATUSES = {
        "cancelled",
    }

    REJECTED_STATUSES = {
        "rejected",
    }

    def __init__(
        self,
        *,
        review_interaction: (
            CompleteReviewApprovalInteraction
            | None
        ) = None,
    ) -> None:
        self.review_interaction = (
            review_interaction
            or CompleteReviewApprovalInteraction()
        )

    def run(
        self,
        *,
        message_results: Iterable[
            MessageProcessingResult
        ],
    ) -> MailboxCompleteReviewSessionResult:
        """
        Run complete-review approval once for every processed
        document.
        """

        try:
            results = list(
                message_results
            )
        except TypeError:
            return self._failure(
                "invalid_message_results"
            )

        if any(
            not isinstance(
                result,
                MessageProcessingResult,
            )
            for result in results
        ):
            return self._failure(
                "invalid_message_result"
            )

        message_count = len(
            results
        )

        document_count = 0
        approved_count = 0
        rejected_count = 0
        cancelled_count = 0
        failed_count = 0

        for message_result in results:
            for document in (
                message_result.processed_documents
            ):
                document_count += 1

                review_output = getattr(
                    document,
                    "review_output",
                    None,
                )

                if review_output is None:
                    failed_count += 1
                    continue

                approval_result = (
                    self.review_interaction.run(
                        review_output=review_output
                    )
                )

                if (
                    approval_result.success
                    and approval_result.approved
                    and approval_result.status
                    == "approved"
                ):
                    approved_count += 1
                    continue

                if (
                    approval_result.status
                    in self.REJECTED_STATUSES
                ):
                    rejected_count += 1
                    continue

                if (
                    approval_result.status
                    in self.CANCELLED_STATUSES
                ):
                    cancelled_count += 1
                    continue

                failed_count += 1

        if document_count == 0:
            return MailboxCompleteReviewSessionResult(
                message_count=message_count,
                document_count=0,
                approved_count=0,
                rejected_count=0,
                cancelled_count=0,
                failed_count=0,
                success=True,
                status="no_documents",
            )

        if failed_count:
            session_status = (
                "completed_with_failures"
            )
            session_success = False

        elif cancelled_count:
            session_status = (
                "completed_with_cancellations"
            )
            session_success = True

        elif rejected_count:
            session_status = (
                "completed_with_rejections"
            )
            session_success = True

        else:
            session_status = "completed"
            session_success = True

        return MailboxCompleteReviewSessionResult(
            message_count=message_count,
            document_count=document_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            cancelled_count=cancelled_count,
            failed_count=failed_count,
            success=session_success,
            status=session_status,
        )

    @staticmethod
    def _failure(
        status: str,
    ) -> MailboxCompleteReviewSessionResult:
        return MailboxCompleteReviewSessionResult(
            message_count=0,
            document_count=0,
            approved_count=0,
            rejected_count=0,
            cancelled_count=0,
            failed_count=0,
            success=False,
            status=status,
        )
