from dataclasses import dataclass, field

from src.models.document import Document


@dataclass
class ReviewDecision:
    """
    Represents the platform's decision about whether a processed
    document needs human verification.
    """

    needs_human_review: bool
    review_status: str
    reasons: list[str] = field(default_factory=list)
    classification_confidence: float = 0.0
    minimum_field_confidence: float | None = None


class ReviewDecisionService:
    """
    Determines whether a processed document can continue automatically
    or must be reviewed by a person.

    Confidence values must use decimal form:

        0.95 = 95%
        0.80 = 80%
    """

    AUTO_APPROVE_CLASSIFICATION_THRESHOLD = 0.90
    HUMAN_REVIEW_CLASSIFICATION_THRESHOLD = 0.75
    FIELD_CONFIDENCE_THRESHOLD = 0.85

    SUCCESS_ACTIONS = {
        "Authorization validated successfully",
    }

    def evaluate(
        self,
        document: Document,
    ) -> ReviewDecision:
        reasons: list[str] = []

        classification_confidence = self._normalize_confidence(
            document.confidence
        )

        minimum_field_confidence = self._get_minimum_field_confidence(
            document.field_confidences
        )

        if not document.document_type:
            reasons.append(
                "Document type could not be determined."
            )

        if (
            classification_confidence
            < self.HUMAN_REVIEW_CLASSIFICATION_THRESHOLD
        ):
            reasons.append(
                "Document classification confidence is below 75%."
            )

        elif (
            classification_confidence
            < self.AUTO_APPROVE_CLASSIFICATION_THRESHOLD
        ):
            reasons.append(
                "Document classification confidence is below 90%."
            )

        if minimum_field_confidence is not None:
            if (
                minimum_field_confidence
                < self.FIELD_CONFIDENCE_THRESHOLD
            ):
                reasons.append(
                    "One or more extracted fields have confidence below 85%."
                )

        if not document.extracted_data:
            reasons.append(
                "No structured data was extracted from the document."
            )

        for action in document.rule_actions:
            if action not in self.SUCCESS_ACTIONS:
                reasons.append(action)

        reasons = self._remove_duplicates(reasons)

        if not reasons:
            return ReviewDecision(
                needs_human_review=False,
                review_status="Verified by AI",
                reasons=[],
                classification_confidence=classification_confidence,
                minimum_field_confidence=minimum_field_confidence,
            )

        if (
            classification_confidence
            < self.HUMAN_REVIEW_CLASSIFICATION_THRESHOLD
        ):
            review_status = "Human Review Required"
        else:
            review_status = "Human Review Recommended"

        return ReviewDecision(
            needs_human_review=True,
            review_status=review_status,
            reasons=reasons,
            classification_confidence=classification_confidence,
            minimum_field_confidence=minimum_field_confidence,
        )

    def _get_minimum_field_confidence(
        self,
        field_confidences: dict[str, float],
    ) -> float | None:
        if not field_confidences:
            return None

        normalized_confidences = [
            self._normalize_confidence(value)
            for value in field_confidences.values()
        ]

        if not normalized_confidences:
            return None

        return min(normalized_confidences)

    def _normalize_confidence(
        self,
        value,
    ) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0

        if confidence > 1:
            confidence = confidence / 100

        return max(0.0, min(confidence, 1.0))

    def _remove_duplicates(
        self,
        values: list[str],
    ) -> list[str]:
        unique_values: list[str] = []

        for value in values:
            if value not in unique_values:
                unique_values.append(value)

        return unique_values