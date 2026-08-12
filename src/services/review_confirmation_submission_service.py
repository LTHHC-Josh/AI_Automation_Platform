from dataclasses import dataclass
from typing import Any

from src.models.document import Document
from src.services.classification_feedback_workflow_service import (
    ClassificationFeedbackWorkflowService,
)
from src.services.review_output_service import ReviewOutput


@dataclass(frozen=True)
class ReviewConfirmationSubmissionResult:
    """
    PHI-safe result from one explicit reviewer submission.

    The result excludes the source path, filename, OCR text, extracted
    values, source evidence, review fields, service lines, and storage
    payload.
    """

    fingerprint: str | None
    byte_count: int
    success: bool
    status: str


class ReviewConfirmationSubmissionService:
    """
    Submits classification feedback only after explicit human review.

    This service uses the completed Document and its attached
    ReviewOutput. It does not rerun OCR, classification, extraction,
    deterministic validation, business rules, review decisions, or
    review-output construction.
    """

    EXPLICIT_CONFIRMATION_STATUSES = {
        "confirmed",
        "corrected",
    }

    def __init__(
        self,
        *,
        feedback_workflow: (
            ClassificationFeedbackWorkflowService
            | None
        ) = None,
    ) -> None:
        self.feedback_workflow = (
            feedback_workflow
            or ClassificationFeedbackWorkflowService()
        )

    def submit(
        self,
        *,
        document: Document,
        confirmed_category: Any,
        confirmed_subtype: Any,
        reviewer_confirmation_status: Any,
        created_at: Any = None,
    ) -> ReviewConfirmationSubmissionResult:
        """
        Submit one explicit reviewer classification decision.
        """

        if not isinstance(
            document,
            Document,
        ):
            return self._failure(
                "invalid_document"
            )

        if not isinstance(
            document.review_output,
            ReviewOutput,
        ):
            return self._failure(
                "review_output_missing"
            )

        confirmation_status = str(
            reviewer_confirmation_status
            or ""
        ).strip().lower()

        if (
            confirmation_status
            not in self.EXPLICIT_CONFIRMATION_STATUSES
        ):
            return self._failure(
                "confirmation_not_explicit"
            )

        workflow_result = (
            self.feedback_workflow.submit(
                source_path=document.file_path,
                review_output=document.review_output,
                confirmed_category=confirmed_category,
                confirmed_subtype=confirmed_subtype,
                reviewer_confirmation_status=(
                    confirmation_status
                ),
                created_at=created_at,
            )
        )

        if workflow_result.success:
            normalized_category = str(
                confirmed_category
                or ""
            ).strip().lower()

            normalized_subtype = str(
                confirmed_subtype
                or ""
            ).strip().lower()

            document.document_category = (
                normalized_category
            )
            document.document_subtype = (
                normalized_subtype
            )
            document.review_output.document_category = (
                normalized_category
            )
            document.review_output.document_subtype = (
                normalized_subtype
            )

        return ReviewConfirmationSubmissionResult(
            fingerprint=workflow_result.fingerprint,
            byte_count=workflow_result.byte_count,
            success=workflow_result.success,
            status=workflow_result.status,
        )

    @staticmethod
    def _failure(
        status: str,
    ) -> ReviewConfirmationSubmissionResult:
        return ReviewConfirmationSubmissionResult(
            fingerprint=None,
            byte_count=0,
            success=False,
            status=status,
        )
