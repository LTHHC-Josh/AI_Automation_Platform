from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.classification_feedback_review_service import (
    ClassificationFeedbackReviewService,
)
from src.services.classification_feedback_storage_service import (
    ClassificationFeedbackStorageService,
)
from src.services.document_fingerprint_service import (
    DocumentFingerprintService,
)
from src.services.review_output_service import ReviewOutput


@dataclass(frozen=True)
class ClassificationFeedbackWorkflowResult:
    """
    PHI-safe result from one local feedback workflow.

    The result deliberately excludes the source path, filename,
    document content, OCR text, extracted fields, source_text, review
    evidence, and storage payload.
    """

    fingerprint: str | None
    byte_count: int
    success: bool
    status: str


class ClassificationFeedbackWorkflowService:
    """
    Fingerprints a local document, builds validated classification
    feedback, and stores it locally.

    The source path is used only by the local fingerprint service. It is
    never copied into feedback, storage, or the returned result.
    """

    def __init__(
        self,
        *,
        fingerprint_service: DocumentFingerprintService | None = None,
        review_service: ClassificationFeedbackReviewService | None = None,
        storage_service: ClassificationFeedbackStorageService | None = None,
    ) -> None:
        self.fingerprint_service = (
            fingerprint_service
            or DocumentFingerprintService()
        )

        self.review_service = (
            review_service
            or ClassificationFeedbackReviewService()
        )

        self.storage_service = (
            storage_service
            or ClassificationFeedbackStorageService()
        )

    def submit(
        self,
        *,
        source_path: str | Path,
        review_output: ReviewOutput,
        confirmed_category: Any,
        confirmed_subtype: Any,
        reviewer_confirmation_status: Any,
        created_at: Any = None,
    ) -> ClassificationFeedbackWorkflowResult:
        """
        Run one local PHI-safe classification-feedback submission.
        """

        fingerprint_result = (
            self.fingerprint_service.calculate(
                source_path
            )
        )

        if (
            not fingerprint_result.success
            or fingerprint_result.fingerprint is None
        ):
            return ClassificationFeedbackWorkflowResult(
                fingerprint=None,
                byte_count=0,
                success=False,
                status=fingerprint_result.status,
            )

        feedback_result = self.review_service.build(
            review_output=review_output,
            document_fingerprint=(
                fingerprint_result.fingerprint
            ),
            confirmed_category=confirmed_category,
            confirmed_subtype=confirmed_subtype,
            reviewer_confirmation_status=(
                reviewer_confirmation_status
            ),
            created_at=created_at,
        )

        if (
            not feedback_result.ready_for_storage
            or feedback_result.feedback is None
        ):
            return ClassificationFeedbackWorkflowResult(
                fingerprint=fingerprint_result.fingerprint,
                byte_count=fingerprint_result.byte_count,
                success=False,
                status="feedback_invalid",
            )

        storage_result = self.storage_service.store(
            feedback_result.feedback
        )

        workflow_succeeded = (
            storage_result.stored
            or storage_result.duplicate
        )

        return ClassificationFeedbackWorkflowResult(
            fingerprint=fingerprint_result.fingerprint,
            byte_count=fingerprint_result.byte_count,
            success=workflow_succeeded,
            status=storage_result.status,
        )
