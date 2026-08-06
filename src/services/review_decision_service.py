from dataclasses import dataclass, field
from typing import Any

from src.models.document import Document


@dataclass
class ReviewDecision:
    """
    Represents the platform's human-review decision.
    """

    needs_human_review: bool
    review_status: str
    reasons: list[str] = field(
        default_factory=list
    )
    classification_confidence: float = 0.0
    minimum_field_confidence: float | None = None


class ReviewDecisionService:
    """
    Determines whether a document can continue automatically or must
    be reviewed by a person.

    Field-confidence review applies only to fields containing a
    meaningful extracted value. Optional fields that are empty, null,
    or were deterministically invalidated do not lower the minimum
    field confidence merely because their stored confidence is 0.0.

    Invalidated fields still require review through the validation
    actions produced by the deterministic evidence validator.
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
        """
        Evaluate classification, extraction, validation, and business
        rule results and return the human-review decision.
        """

        reasons: list[str] = []

        classification_confidence = self._normalize_confidence(
            document.confidence
        )

        minimum_field_confidence = (
            self._get_minimum_field_confidence(
                extracted_data=document.extracted_data,
                field_confidences=document.field_confidences,
            )
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

        if (
            minimum_field_confidence is not None
            and minimum_field_confidence
            < self.FIELD_CONFIDENCE_THRESHOLD
        ):
            reasons.append(
                "One or more extracted fields have confidence below 85%."
            )

        if not self._has_structured_data(
            document.extracted_data
        ):
            reasons.append(
                "No structured data was extracted from the document."
            )

        for action in document.validation_actions:
            reasons.append(
                action
            )

        for action in document.rule_actions:
            if action not in self.SUCCESS_ACTIONS:
                reasons.append(
                    action
                )

        reasons = self._remove_duplicates(
            reasons
        )

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
        extracted_data: dict[str, Any],
        field_confidences: dict[str, float],
    ) -> float | None:
        """
        Return the lowest confidence among populated extracted fields.

        Empty optional fields do not represent extracted claims and must
        not lower the document's minimum field confidence.

        Fields containing False or numeric zero are considered populated
        because those can be meaningful extracted values.
        """

        if not isinstance(
            extracted_data,
            dict,
        ):
            return None

        if not isinstance(
            field_confidences,
            dict,
        ):
            return None

        normalized_confidences: list[float] = []

        for field_name, value in extracted_data.items():
            if self._is_empty_value(
                value
            ):
                continue

            confidence = field_confidences.get(
                field_name
            )

            normalized_confidences.append(
                self._normalize_confidence(
                    confidence
                )
            )

        if not normalized_confidences:
            return None

        return min(
            normalized_confidences
        )

    def _has_structured_data(
        self,
        extracted_data: dict[str, Any],
    ) -> bool:
        """
        Determine whether at least one meaningful structured value exists.
        """

        if not isinstance(
            extracted_data,
            dict,
        ):
            return False

        return any(
            not self._is_empty_value(
                value
            )
            for value in extracted_data.values()
        )

    def _is_empty_value(
        self,
        value: Any,
    ) -> bool:
        """
        Determine whether a structured value contains no usable data.

        Boolean False and numeric zero are retained as meaningful values.
        """

        if value is None:
            return True

        if isinstance(
            value,
            str,
        ):
            return not value.strip()

        if isinstance(
            value,
            (list, tuple, set, dict),
        ):
            return len(
                value
            ) == 0

        return False

    def _normalize_confidence(
        self,
        value: Any,
    ) -> float:
        """
        Normalize a confidence value into the range 0.0 through 1.0.
        """

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

    def _remove_duplicates(
        self,
        values: list[str],
    ) -> list[str]:
        """
        Remove duplicate review reasons while preserving their order.
        """

        unique_values: list[str] = []

        for value in values:
            if value not in unique_values:
                unique_values.append(
                    value
                )

        return unique_values