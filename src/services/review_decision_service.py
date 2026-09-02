from dataclasses import dataclass, field
from typing import Any

from src.models.document import Document
from src.models.document_taxonomy import DocumentTaxonomyRegistry
from src.services.field_validation_diagnostic_service import (
    FieldValidationDiagnosticService,
)


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

    Classification review, deterministic evidence validation, business
    rules, and field-confidence review remain separate concerns.

    Field-confidence review applies only to fields containing a
    meaningful extracted value. Optional fields that are empty, null,
    or were deterministically invalidated do not lower the minimum
    field confidence merely because their stored confidence is 0.0.

    Invalidated fields still require review through validation actions.
    """

    AUTO_APPROVE_CLASSIFICATION_THRESHOLD = 0.90
    HUMAN_REVIEW_CLASSIFICATION_THRESHOLD = 0.75
    FIELD_CONFIDENCE_THRESHOLD = 0.85

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

    SUCCESS_ACTIONS = {
        "Authorization validated successfully",
    }

    SUCCESS_VALIDATION_ACTIONS = {
        "Authorized units were reconciled from supported service-line evidence",
    }

    UNKNOWN_CATEGORY_REASON = (
        "Document category could not be determined."
    )

    UNSUPPORTED_CATEGORY_REASON = (
        "Document category is not supported by the classification "
        "contract."
    )

    UNKNOWN_AUTHORIZATION_SUBTYPE_REASON = (
        "Authorization subtype could not be determined."
    )

    UNKNOWN_TERMINATION_SUBTYPE_REASON = (
        "Authorization or service termination subtype could not be "
        "determined."
    )

    INCOMPATIBLE_SUBTYPE_REASON = (
        "Document category and subtype are incompatible."
    )

    OTHER_CATEGORY_REASON = (
        "Document category requires human confirmation."
    )

    MISSING_CLASSIFICATION_REASON = (
        "Document classification has no supporting reason."
    )

    def evaluate(
        self,
        document: Document,
    ) -> ReviewDecision:
        """
        Evaluate classification, extraction, validation, and business
        rule results and return the human-review decision.
        """

        reasons: list[str] = []
        required_review_reasons: list[str] = []

        classification_confidence = self._normalize_confidence(
            document.confidence
        )

        minimum_field_confidence = (
            self._get_minimum_field_confidence(
                document=document,
            )
        )

        category = self._normalize_label(
            getattr(
                document,
                "document_category",
                "",
            )
        )

        subtype = self._normalize_label(
            getattr(
                document,
                "document_subtype",
                "",
            )
        )

        classification_reason = str(
            getattr(
                document,
                "classification_reason",
                "",
            )
            or ""
        ).strip()

        self._append_classification_reasons(
            category=category,
            subtype=subtype,
            classification_reason=classification_reason,
            reasons=reasons,
            required_review_reasons=required_review_reasons,
        )

        if not document.document_type:
            reason = "Document type could not be determined."
            reasons.append(
                reason
            )
            required_review_reasons.append(
                reason
            )

        if (
            classification_confidence
            < self.HUMAN_REVIEW_CLASSIFICATION_THRESHOLD
        ):
            reason = (
                "Document classification confidence is below 75%."
            )
            reasons.append(
                reason
            )
            required_review_reasons.append(
                reason
            )

        elif (
            classification_confidence
            < self.AUTO_APPROVE_CLASSIFICATION_THRESHOLD
        ):
            reasons.append(
                "Document classification confidence is below 90%."
            )

        reasons.extend(self._field_confidence_reasons(document))

        if not self._has_structured_data(
            document.extracted_data
        ):
            reasons.append(
                "No structured data was extracted from the document."
            )

        for action in self._reviewable_validation_actions(document):
            if action not in self.SUCCESS_VALIDATION_ACTIONS:
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

        required_review_reasons = self._remove_duplicates(
            required_review_reasons
        )

        if not reasons:
            return ReviewDecision(
                needs_human_review=False,
                review_status="Verified by AI",
                reasons=[],
                classification_confidence=classification_confidence,
                minimum_field_confidence=minimum_field_confidence,
            )

        if required_review_reasons:
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

    def _append_classification_reasons(
        self,
        category: str,
        subtype: str,
        classification_reason: str,
        reasons: list[str],
        required_review_reasons: list[str],
    ) -> None:
        """
        Add deterministic classification review reasons.

        This method does not rerun classification or reinterpret OCR
        text. It evaluates only the preserved classification result.
        """

        if (
            not category
            or category == "unknown"
        ):
            reasons.append(
                self.UNKNOWN_CATEGORY_REASON
            )
            required_review_reasons.append(
                self.UNKNOWN_CATEGORY_REASON
            )

        elif category not in self.DOCUMENT_CATEGORIES:
            reasons.append(
                self.UNSUPPORTED_CATEGORY_REASON
            )
            required_review_reasons.append(
                self.UNSUPPORTED_CATEGORY_REASON
            )

        elif category == "authorization":
            if subtype not in self.AUTHORIZATION_SUBTYPES:
                reasons.append(
                    self.INCOMPATIBLE_SUBTYPE_REASON
                )
                required_review_reasons.append(
                    self.INCOMPATIBLE_SUBTYPE_REASON
                )
            elif subtype == "unknown":
                reasons.append(
                    self.UNKNOWN_AUTHORIZATION_SUBTYPE_REASON
                )

        elif category == "termination":
            if subtype not in self.TERMINATION_SUBTYPES:
                reasons.append(
                    self.INCOMPATIBLE_SUBTYPE_REASON
                )
                required_review_reasons.append(
                    self.INCOMPATIBLE_SUBTYPE_REASON
                )
            elif subtype == "unknown":
                reasons.append(
                    self.UNKNOWN_TERMINATION_SUBTYPE_REASON
                )
                required_review_reasons.append(
                    self.UNKNOWN_TERMINATION_SUBTYPE_REASON
                )

        elif category == "2067":
            if subtype not in self.FORM_2067_SUBTYPES:
                reasons.append(self.INCOMPATIBLE_SUBTYPE_REASON)
                required_review_reasons.append(self.INCOMPATIBLE_SUBTYPE_REASON)
            elif subtype == "unknown":
                reason = "2067 subtype could not be deterministically determined."
                reasons.append(reason)
                required_review_reasons.append(reason)

        elif category in self.CATEGORIES_WITHOUT_SUBTYPES:
            if subtype != "unknown":
                reasons.append(
                    self.INCOMPATIBLE_SUBTYPE_REASON
                )
                required_review_reasons.append(
                    self.INCOMPATIBLE_SUBTYPE_REASON
                )

        if category == "other":
            reasons.append(
                self.OTHER_CATEGORY_REASON
            )

        if not classification_reason:
            reasons.append(
                self.MISSING_CLASSIFICATION_REASON
            )

    def _get_minimum_field_confidence(
        self,
        document: Document,
    ) -> float | None:
        """
        Return the lowest confidence among populated extracted fields.
        """

        extracted_data = document.extracted_data
        field_confidences = document.field_confidences
        if not isinstance(extracted_data, dict):
            return None

        if not isinstance(
            field_confidences,
            dict,
        ):
            return None

        normalized_confidences: list[float] = []
        diagnostics = FieldValidationDiagnosticService(
            threshold=self.FIELD_CONFIDENCE_THRESHOLD
        )
        accepted_service_codes = not self._is_empty_value(
            extracted_data.get("service_codes")
        ) and field_confidences.get("service_codes") is not None

        for field_name, value in extracted_data.items():
            if field_name == "service_code" and accepted_service_codes:
                continue
            if self._is_empty_value(
                value
            ):
                continue
            if diagnostics.build(document, field_name).field_state != "accepted":
                continue

            confidence = field_confidences.get(
                field_name
            )

            if confidence is None:
                continue

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

    def _field_confidence_reasons(self, document: Document) -> list[str]:
        """Return field-specific reasons only for populated final fields."""
        reasons = []
        diagnostics = FieldValidationDiagnosticService(
            threshold=self.FIELD_CONFIDENCE_THRESHOLD
        )
        accepted_service_codes = not self._is_empty_value(
            document.extracted_data.get("service_codes")
        ) and document.field_confidences.get("service_codes") is not None
        for field_name, value in document.extracted_data.items():
            if field_name == "service_code" and accepted_service_codes:
                continue
            if self._is_empty_value(value):
                continue
            diagnostic = diagnostics.build(document, field_name)
            if diagnostic.field_state != "low_confidence":
                continue
            confidence = document.field_confidences.get(field_name)
            if confidence is None:
                evidence = document.field_evidence.get(field_name)
                provenance = (
                    str(evidence.get("provenance") or "")
                    if isinstance(evidence, dict) else ""
                )
                if provenance != "business_default_hours":
                    label = str(field_name).replace("_", " ").strip().capitalize()
                    reasons.append(f"{label} confidence is unavailable")
                continue
            if self._normalize_confidence(confidence) < self.FIELD_CONFIDENCE_THRESHOLD:
                label = str(field_name).replace("_", " ").strip().capitalize()
                reasons.append(f"{label} confidence is below the acceptance threshold")
        return reasons

    def _reviewable_validation_actions(self, document: Document) -> list[str]:
        """Filter informational and superseded validation events from review."""
        accepted_service_codes = not self._is_empty_value(
            document.extracted_data.get("service_codes")
        ) and document.field_confidences.get("service_codes") is not None
        actions = []
        for action in document.validation_actions:
            if action in self.SUCCESS_VALIDATION_ACTIONS:
                continue
            normalized = str(action or "").strip().lower()
            if normalized == "duplicate service-line evidence was removed":
                continue
            if accepted_service_codes and normalized.startswith(
                ("service_code ", "service code ")
            ):
                continue
            actions.append(action)
        return actions

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

    def _normalize_label(
        self,
        value: Any,
    ) -> str:
        """
        Normalize one classification label.
        """

        return str(
            value
            or ""
        ).strip().lower()

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
