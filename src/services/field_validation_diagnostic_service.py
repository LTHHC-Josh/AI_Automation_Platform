from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.models.document import Document
from src.services.review_decision_service import ReviewDecisionService
from src.services.review_reason_summary_service import ReviewReasonSummaryService


class FieldValidationState(str, Enum):
    NOT_PRESENT = "not_present"
    MISSING_REQUIRED = "missing_required"
    ACCEPTED = "accepted"
    LOW_CONFIDENCE = "low_confidence"
    UNSUPPORTED = "unsupported"
    CONFLICTING = "conflicting"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


class DocumentFieldRequirementService:
    """Expose only requiredness already enforced by committed business rules."""

    AUTHORIZATION_REQUIRED_FIELDS = frozenset({
        "patient_name", "authorization_number", "payer", "member_id",
        "authorization_status", "start_date", "end_date",
    })

    def is_required(self, document: Any, field_name: str) -> bool:
        category = str(getattr(document, "document_category", "") or "").lower()
        return category == "authorization" and field_name in self.AUTHORIZATION_REQUIRED_FIELDS


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
    field_state: str = FieldValidationState.NOT_PRESENT.value
    required: bool = False


@dataclass(frozen=True)
class FinalValidationSummary:
    accepted_field_count: int = 0
    optional_absent_field_count: int = 0
    missing_required_count: int = 0
    low_confidence_count: int = 0
    unsupported_count: int = 0
    ambiguous_count: int = 0
    conflicting_count: int = 0
    invalid_count: int = 0
    quantity_present: bool = False
    unit_source_category: str = "unresolved"


class FieldValidationDiagnosticService:
    """Build PHI-safe field-state diagnostics without returning field values."""

    def __init__(self, *, threshold: float = ReviewDecisionService.FIELD_CONFIDENCE_THRESHOLD,
                 requirement_service=None):
        self.threshold = float(threshold)
        self.reason_summary = ReviewReasonSummaryService()
        self.requirement_service = requirement_service or DocumentFieldRequirementService()

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
        reason_code = self.reason_summary.summarize_codes(matching_actions) or None
        threshold_passed = (
            candidate_confidence is not None
            and candidate_confidence >= self.threshold
        )
        validation_passed = value_present and not matching_actions
        required = self.requirement_service.is_required(document, field_name)
        state = self._state(
            value_present=value_present, required=required,
            threshold_passed=threshold_passed, actions=matching_actions,
        )
        return FieldValidationDiagnostic(
            field_category=field_name,
            candidate_confidence=candidate_confidence,
            threshold_passed=threshold_passed,
            source_support_proven=validation_passed,
            validated_value_present=value_present,
            validation_passed=validation_passed,
            review_triggered=state not in {
                FieldValidationState.ACCEPTED, FieldValidationState.NOT_PRESENT,
            },
            reason_code=reason_code,
            field_state=state.value,
            required=required,
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
        reason_code = self.reason_summary.summarize_codes(matching) or None
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
            field_state=self._state(
                value_present=value_present, required=False,
                threshold_passed=threshold_passed, actions=matching,
            ).value,
            required=False,
        )

    def summarize(self, document: Any) -> FinalValidationSummary:
        if not isinstance(document, Document):
            return FinalValidationSummary()
        states = []
        for field_name in document.field_evidence:
            states.append(self.build(document, str(field_name)).field_state)
        for index, line in enumerate(document.service_lines or []):
            candidate = getattr(line, "candidate_evidence", {})
            for component in ("service_code", "modifier", "quantity", "start_date", "end_date", "status"):
                if isinstance(candidate, dict) and component in candidate:
                    states.append(self.build_service_line(document, index, component).field_state)
        counts = {state.value: states.count(state.value) for state in FieldValidationState}
        unit = document.field_evidence.get("authorization_unit")
        unit_source = (
            str(unit.get("provenance") or "unresolved")
            if isinstance(unit, dict) and unit.get("value") is not None
            else "unresolved"
        )
        if unit_source not in {"explicit_document_evidence", "business_default_hours"}:
            unit_source = "unresolved"
        return FinalValidationSummary(
            accepted_field_count=counts[FieldValidationState.ACCEPTED.value],
            optional_absent_field_count=counts[FieldValidationState.NOT_PRESENT.value],
            missing_required_count=counts[FieldValidationState.MISSING_REQUIRED.value],
            low_confidence_count=counts[FieldValidationState.LOW_CONFIDENCE.value],
            unsupported_count=counts[FieldValidationState.UNSUPPORTED.value],
            ambiguous_count=counts[FieldValidationState.AMBIGUOUS.value],
            conflicting_count=counts[FieldValidationState.CONFLICTING.value],
            invalid_count=counts[FieldValidationState.INVALID.value],
            quantity_present=not self._empty(document.extracted_data.get("authorized_units")),
            unit_source_category=unit_source,
        )

    @staticmethod
    def _state(*, value_present, required, threshold_passed, actions):
        text = " ".join(str(action).lower() for action in actions)
        if actions:
            if "conflict" in text or "multiple" in text:
                return FieldValidationState.CONFLICTING
            if "ambiguous" in text or "requires verification" in text:
                return FieldValidationState.AMBIGUOUS
            if "invalid" in text or "could not be normalized" in text:
                return FieldValidationState.INVALID
            return FieldValidationState.UNSUPPORTED
        if not value_present:
            return (
                FieldValidationState.MISSING_REQUIRED
                if required else FieldValidationState.NOT_PRESENT
            )
        if not threshold_passed:
            return FieldValidationState.LOW_CONFIDENCE
        return FieldValidationState.ACCEPTED

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
