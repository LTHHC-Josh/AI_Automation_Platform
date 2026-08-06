from typing import Any

from src.services.classification_feedback_service import (
    ClassificationFeedbackResult,
    ClassificationFeedbackService,
)
from src.services.review_output_service import ReviewOutput


class ClassificationFeedbackReviewService:
    """
    Builds PHI-safe classification feedback from review metadata.

    ReviewOutput may contain PHI-bearing fields and source evidence.
    This adapter reads only the classification category, subtype, and
    confidence. It never copies fields, service lines, review reasons,
    source_text, extracted values, OCR text, or local paths.
    """

    def __init__(self) -> None:
        self.feedback_service = ClassificationFeedbackService()

    def build(
        self,
        *,
        review_output: ReviewOutput,
        document_fingerprint: Any,
        confirmed_category: Any,
        confirmed_subtype: Any,
        reviewer_confirmation_status: Any,
        created_at: Any = None,
    ) -> ClassificationFeedbackResult:
        """
        Build one validated feedback record from classification metadata.
        """

        if not isinstance(
            review_output,
            ReviewOutput,
        ):
            return ClassificationFeedbackResult(
                feedback=None,
                errors=(
                    "review_output must be a ReviewOutput instance.",
                ),
                ready_for_storage=False,
            )

        return self.feedback_service.build(
            document_fingerprint=document_fingerprint,
            predicted_category=review_output.document_category,
            predicted_subtype=review_output.document_subtype,
            confirmed_category=confirmed_category,
            confirmed_subtype=confirmed_subtype,
            classification_confidence=(
                review_output.classification_confidence
            ),
            reviewer_confirmation_status=(
                reviewer_confirmation_status
            ),
            created_at=created_at,
        )
