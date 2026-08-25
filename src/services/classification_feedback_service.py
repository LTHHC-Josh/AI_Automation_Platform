from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any

from src.models.document_taxonomy import DocumentTaxonomyRegistry


@dataclass(frozen=True)
class ClassificationFeedback:
    """
    PHI-safe human-confirmed document-classification feedback.

    This contract intentionally excludes document content, OCR text,
    source evidence, identifying paths, filenames, email metadata,
    extracted values, and patient identifiers.
    """

    document_fingerprint: str
    predicted_category: str
    predicted_subtype: str
    confirmed_category: str
    confirmed_subtype: str
    classification_confidence: float
    correction_required: bool
    reviewer_confirmation_status: str
    created_at: str


@dataclass(frozen=True)
class ClassificationFeedbackResult:
    """
    Result of deterministic feedback validation.
    """

    feedback: ClassificationFeedback | None
    errors: tuple[str, ...]
    ready_for_storage: bool


class ClassificationFeedbackService:
    """
    Builds a PHI-safe classification-feedback record.

    The service accepts labels, confidence, confirmation status, and a
    precomputed local SHA-256 document fingerprint only. It does not
    accept or process a document path, document bytes, OCR text,
    source_text, extracted values, or email content.
    """

    DOCUMENT_CATEGORIES = set(DocumentTaxonomyRegistry.families())

    AUTHORIZATION_SUBTYPES = set(
        DocumentTaxonomyRegistry.definition("authorization").subtypes
    )
    TERMINATION_SUBTYPES = set(
        DocumentTaxonomyRegistry.definition("termination").subtypes
    )
    FORM_2067_SUBTYPES = set(
        DocumentTaxonomyRegistry.definition("2067").subtypes
    )
    CATEGORIES_WITHOUT_SUBTYPES = {
        family for family in DocumentTaxonomyRegistry.families()
        if DocumentTaxonomyRegistry.definition(family).subtypes == frozenset({"unknown"})
    }

    CONFIRMATION_STATUSES = {
        "confirmed",
        "corrected",
    }

    SHA256_PATTERN = re.compile(
        r"^[0-9a-f]{64}$"
    )

    def build(
        self,
        *,
        document_fingerprint: Any,
        predicted_category: Any,
        predicted_subtype: Any,
        confirmed_category: Any,
        confirmed_subtype: Any,
        classification_confidence: Any,
        reviewer_confirmation_status: Any,
        created_at: Any = None,
    ) -> ClassificationFeedbackResult:
        """
        Validate and build one feedback record.
        """

        errors: list[str] = []

        fingerprint = self._normalize_label(
            document_fingerprint
        )

        predicted_category_value = self._normalize_label(
            predicted_category
        )
        predicted_subtype_value = self._normalize_label(
            predicted_subtype
        )
        confirmed_category_value = self._normalize_label(
            confirmed_category
        )
        confirmed_subtype_value = self._normalize_label(
            confirmed_subtype
        )
        confirmation_status = self._normalize_label(
            reviewer_confirmation_status
        )
        confidence = self._normalize_confidence(
            classification_confidence
        )

        if not self.SHA256_PATTERN.fullmatch(
            fingerprint
        ):
            errors.append(
                "Document fingerprint must be a lowercase SHA-256 hash."
            )

        self._validate_classification(
            category=predicted_category_value,
            subtype=predicted_subtype_value,
            prefix="Predicted",
            errors=errors,
        )

        self._validate_classification(
            category=confirmed_category_value,
            subtype=confirmed_subtype_value,
            prefix="Confirmed",
            errors=errors,
        )

        if confirmation_status not in self.CONFIRMATION_STATUSES:
            errors.append(
                "Reviewer confirmation status must be confirmed or "
                "corrected."
            )

        correction_required = (
            predicted_category_value
            != confirmed_category_value
            or predicted_subtype_value
            != confirmed_subtype_value
        )

        expected_status = (
            "corrected"
            if correction_required
            else "confirmed"
        )

        if (
            confirmation_status in self.CONFIRMATION_STATUSES
            and confirmation_status != expected_status
        ):
            errors.append(
                "Reviewer confirmation status does not match whether "
                "the classification changed."
            )

        timestamp = self._normalize_timestamp(
            created_at
        )

        if timestamp is None:
            errors.append(
                "created_at must be an ISO-8601 UTC timestamp."
            )

        if errors:
            return ClassificationFeedbackResult(
                feedback=None,
                errors=tuple(
                    errors
                ),
                ready_for_storage=False,
            )

        feedback = ClassificationFeedback(
            document_fingerprint=fingerprint,
            predicted_category=predicted_category_value,
            predicted_subtype=predicted_subtype_value,
            confirmed_category=confirmed_category_value,
            confirmed_subtype=confirmed_subtype_value,
            classification_confidence=confidence,
            correction_required=correction_required,
            reviewer_confirmation_status=confirmation_status,
            created_at=timestamp,
        )

        return ClassificationFeedbackResult(
            feedback=feedback,
            errors=(),
            ready_for_storage=True,
        )

    def _validate_classification(
        self,
        *,
        category: str,
        subtype: str,
        prefix: str,
        errors: list[str],
    ) -> None:
        if category not in self.DOCUMENT_CATEGORIES:
            errors.append(
                f"{prefix} category is not supported."
            )
            return

        definition = DocumentTaxonomyRegistry.definition(category)
        if definition is None or subtype not in definition.subtypes:
            errors.append(
                f"{prefix} subtype is not supported for the selected category."
            )

    def _normalize_label(
        self,
        value: Any,
    ) -> str:
        return str(
            value
            or ""
        ).strip().lower()

    def _normalize_confidence(
        self,
        value: Any,
    ) -> float:
        try:
            confidence = float(
                value
            )
        except (TypeError, ValueError):
            return 0.0

        if confidence > 1:
            confidence = confidence / 100

        return max(
            0.0,
            min(
                confidence,
                1.0,
            ),
        )

    def _normalize_timestamp(
        self,
        value: Any,
    ) -> str | None:
        if value is None:
            timestamp = datetime.now(
                timezone.utc
            )
        else:
            try:
                timestamp = datetime.fromisoformat(
                    str(
                        value
                    ).replace(
                        "Z",
                        "+00:00",
                    )
                )
            except (TypeError, ValueError):
                return None

        if timestamp.tzinfo is None:
            return None

        timestamp = timestamp.astimezone(
            timezone.utc
        )

        return timestamp.isoformat().replace(
            "+00:00",
            "Z",
        )
