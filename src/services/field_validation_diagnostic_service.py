from dataclasses import dataclass
from typing import Any

from src.models.document import Document
from src.services.review_decision_service import ReviewDecisionService
from src.services.review_reason_summary_service import ReviewReasonSummaryService


@dataclass(frozen=True)
class FieldValidationDiagnostic:
    field_category: str
    candidate_confidence: float | None
    threshold_passed: bool
    source_support_proven: bool
    validated_value_present: bool
    validation_passed: bool
    review_triggered: bool
    reason_code: str | None


class FieldValidationDiagnosticService:
    """Build PHI-safe field-state diagnostics without returning field values."""

    def __init__(self, *, threshold: float = ReviewDecisionService.FIELD_CONFIDENCE_THRESHOLD):
        self.threshold = float(threshold)
        self.reason_summary = ReviewReasonSummaryService()

    def build(self, document: Any, field_name: str) -> FieldValidationDiagnostic:
        evidence = (
            document.field_evidence.get(field_name, {})
            if isinstance(document, Document) and isinstance(document.field_evidence, dict)
            else {}
        )
        candidate_confidence = self._confidence(
            evidence.get("candidate_confidence", evidence.get("confidence"))
        )
        value_present = not self._empty(evidence.get("value"))
        matching_actions = [
            str(action)
            for action in getattr(document, "validation_actions", [])
            if str(action).lower().startswith(field_name.replace("_", " ").lower())
            or str(action).lower().startswith(field_name.lower())
        ]
        reason_code = self.reason_summary.summarize(matching_actions) or None
        threshold_passed = (
            candidate_confidence is not None
            and candidate_confidence >= self.threshold
        )
        validation_passed = value_present and not matching_actions
        return FieldValidationDiagnostic(
            field_category=field_name,
            candidate_confidence=candidate_confidence,
            threshold_passed=threshold_passed,
            source_support_proven=validation_passed,
            validated_value_present=value_present,
            validation_passed=validation_passed,
            review_triggered=bool(matching_actions) or (value_present and not threshold_passed),
            reason_code=reason_code,
        )

    def build_service_line(
        self, document: Any, line_index: int, component: str
    ) -> FieldValidationDiagnostic:
        lines = getattr(document, "service_lines", [])
        if (
            not isinstance(line_index, int)
            or line_index < 0
            or not isinstance(lines, list)
            or line_index >= len(lines)
        ):
            return FieldValidationDiagnostic(
                f"service_line_{component}", None, False, False, False, False, True, "service_line_unavailable"
            )
        line = lines[line_index]
        candidate = getattr(line, "candidate_evidence", {})
        candidate_confidence = self._confidence(
            candidate.get("confidence", getattr(line, "confidence", None))
            if isinstance(candidate, dict)
            else getattr(line, "confidence", None)
        )
        value_present = not self._empty(getattr(line, component, None))
        prefix = f"service line {line_index + 1} {component.replace('_', ' ')}"
        matching = [
            str(action)
            for action in getattr(document, "validation_actions", [])
            if str(action).lower().startswith(prefix)
        ]
        reason_code = self.reason_summary.summarize(matching) or None
        threshold_passed = candidate_confidence is not None and candidate_confidence >= self.threshold
        validation_passed = value_present and not matching
        return FieldValidationDiagnostic(
            field_category=f"service_line_{component}",
            candidate_confidence=candidate_confidence,
            threshold_passed=threshold_passed,
            source_support_proven=validation_passed,
            validated_value_present=value_present,
            validation_passed=validation_passed,
            review_triggered=bool(matching) or (value_present and not threshold_passed),
            reason_code=reason_code,
        )

    @staticmethod
    def _confidence(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return None
        if normalized > 1:
            normalized /= 100
        return max(0.0, min(normalized, 1.0))

    @staticmethod
    def _empty(value: Any) -> bool:
        return value is None or value == "" or value == [] or value == {}
