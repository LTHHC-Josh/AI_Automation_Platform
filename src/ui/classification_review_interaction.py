from collections.abc import Callable
from typing import Any

from src.models.document import Document
from src.services.review_confirmation_submission_service import (
    ReviewConfirmationSubmissionResult,
    ReviewConfirmationSubmissionService,
)


class ClassificationReviewInteraction:
    """
    Runs one local classification-review interaction.

    The interaction displays only PHI-safe classification metadata. It
    does not display or return the source path, filename, OCR text,
    classification reason, extracted values, field evidence,
    source_text, service lines, or feedback-storage payload.
    """

    def __init__(
        self,
        *,
        submission_service: (
            ReviewConfirmationSubmissionService
            | None
        ) = None,
        input_reader: Callable[[str], str] = input,
        output_writer: Callable[[str], Any] = print,
    ) -> None:
        self.submission_service = (
            submission_service
            or ReviewConfirmationSubmissionService()
        )
        self.input_reader = input_reader
        self.output_writer = output_writer

    def run(
        self,
        *,
        document: Document,
        created_at: Any = None,
    ) -> ReviewConfirmationSubmissionResult:
        """
        Review and optionally submit one classification decision.
        """

        if not isinstance(
            document,
            Document,
        ):
            return self._failure(
                "invalid_document"
            )

        if document.review_output is None:
            return self._failure(
                "review_output_missing"
            )

        review_output = document.review_output

        predicted_category = self._normalize_label(
            getattr(
                review_output,
                "document_category",
                "unknown",
            )
        )

        predicted_subtype = self._normalize_label(
            getattr(
                review_output,
                "document_subtype",
                "unknown",
            )
        )

        confidence = self._normalize_confidence(
            getattr(
                review_output,
                "classification_confidence",
                0.0,
            )
        )

        self.output_writer(
            "=" * 60
        )
        self.output_writer(
            "CLASSIFICATION REVIEW"
        )
        self.output_writer(
            "=" * 60
        )
        self.output_writer(
            f"Predicted category : {predicted_category}"
        )
        self.output_writer(
            f"Predicted subtype  : {predicted_subtype}"
        )
        self.output_writer(
            f"Confidence         : {confidence:.2f}"
        )
        self.output_writer(
            ""
        )
        self.output_writer(
            "1. Confirm classification"
        )
        self.output_writer(
            "2. Correct classification"
        )
        self.output_writer(
            "0. Cancel"
        )

        choice = self._read_text(
            "Selection: "
        )

        if choice == "0":
            return self._failure(
                "cancelled"
            )

        if choice == "1":
            confirmed_category = (
                predicted_category
            )
            confirmed_subtype = (
                predicted_subtype
            )
            confirmation_status = "confirmed"

        elif choice == "2":
            confirmed_category = (
                self._read_text(
                    "Confirmed category: "
                )
            )

            confirmed_subtype = (
                self._read_text(
                    "Confirmed subtype: "
                )
            )

            if (
                not confirmed_category
                or not confirmed_subtype
            ):
                return self._failure(
                    "correction_labels_required"
                )

            confirmation_status = "corrected"

        else:
            return self._failure(
                "invalid_selection"
            )

        result = self.submission_service.submit(
            document=document,
            confirmed_category=confirmed_category,
            confirmed_subtype=confirmed_subtype,
            reviewer_confirmation_status=(
                confirmation_status
            ),
            created_at=created_at,
        )

        self.output_writer(
            f"Submission status: {result.status}"
        )

        return result

    def _read_text(
        self,
        prompt: str,
    ) -> str:
        value = self.input_reader(
            prompt
        )

        return str(
            value
            or ""
        ).strip()

    @staticmethod
    def _normalize_label(
        value: Any,
    ) -> str:
        normalized = str(
            value
            or ""
        ).strip().lower()

        return (
            normalized
            or "unknown"
        )

    @staticmethod
    def _normalize_confidence(
        value: Any,
    ) -> float:
        try:
            confidence = float(
                value
            )
        except (TypeError, ValueError):
            return 0.0

        if confidence > 1:
            confidence = (
                confidence / 100
            )

        return max(
            0.0,
            min(
                confidence,
                1.0,
            ),
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
