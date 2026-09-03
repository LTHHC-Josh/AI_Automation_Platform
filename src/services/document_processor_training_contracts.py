"""Deterministic contracts for Document Processor Training."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable


AI_CORRECTION = "AI Correction"
AI_PROPOSED_CORRECTION = "AI Proposed Correction"
AI_CORRECTION_TYPE = "AI Correction Type"
APPROVE_AI_CORRECTION = "Approve AI Correction"
AI_CORRECTION_STATUS = "AI Correction Status"
APPROVE_AI_RESOLUTION = "Approve AI Resolution"
AI_RESOLUTION_RESULT = "AI Resolution Result"

HUMAN_OWNED_COLUMNS = frozenset({
    AI_CORRECTION,
    APPROVE_AI_CORRECTION,
    APPROVE_AI_RESOLUTION,
})
WORKFLOW_OWNED_COLUMNS = frozenset({
    AI_PROPOSED_CORRECTION,
    AI_CORRECTION_TYPE,
    AI_CORRECTION_STATUS,
    AI_RESOLUTION_RESULT,
})
REQUIRED_COLUMNS = HUMAN_OWNED_COLUMNS | WORKFLOW_OWNED_COLUMNS

CORRECTION_TYPES = (
    "Classification",
    "Document Subtype",
    "Missing Field",
    "Incorrect Field Value",
    "Confidence",
    "Review Reason",
    "Filename",
    "Service Line",
    "Modifier",
    "Date",
    "Quantity / Unit",
    "Mapping",
    "Reference Data",
    "Recovery / Duplicate Handling",
    "External System Dependency",
    "Needs Investigation",
    "Other",
)

CORRECTION_STATUSES = (
    "New",
    "Analysis Ready",
    "Approved for Implementation",
    "Implementation In Progress",
    "Retest Required",
    "Resolved",
    "Rejected",
    "Needs More Information",
    "Cannot Resolve Yet",
    "Requires External System",
)

ALLOWED_STATUS_TRANSITIONS = {
    "New": frozenset({"Analysis Ready", "Needs More Information"}),
    "Analysis Ready": frozenset({
        "New", "Approved for Implementation", "Rejected", "Cannot Resolve Yet",
    }),
    "Approved for Implementation": frozenset({
        "New", "Implementation In Progress", "Rejected",
    }),
    "Implementation In Progress": frozenset({
        "Retest Required", "Needs More Information", "Cannot Resolve Yet",
        "Requires External System",
    }),
    "Retest Required": frozenset({"New", "Resolved", "Cannot Resolve Yet"}),
    "Resolved": frozenset({"New"}),
    "Rejected": frozenset({"New"}),
    "Needs More Information": frozenset({"New", "Rejected"}),
    "Cannot Resolve Yet": frozenset({"New"}),
    "Requires External System": frozenset({"New"}),
}

IMPLEMENTATION_LAYERS = (
    "Code",
    "Business Rule",
    "Extraction / Prompt",
    "Mapping",
    "Reference Data",
    "External System",
    "Multiple Layers",
    "Needs Investigation",
)

BEHAVIOR_CODES = {
    "remain_blank_when_absent": "Optional evidence should remain blank when absent and should not create review noise.",
    "require_review_when_unsupported": "Unsupported or unreliable evidence should remain unknown and require human review.",
    "preserve_supported_value": "Supported evidence should be preserved through validation and destination mapping.",
    "correct_classification": "The document classification should follow deterministically supported document meaning.",
    "correct_subtype": "The document subtype should follow deterministically supported purpose evidence.",
    "correct_confidence": "Confidence should reflect the validated evidence owner without a synthetic default.",
    "remove_false_review_reason": "The unsupported review reason should not be emitted.",
    "add_required_review_reason": "The applicable unsupported condition should produce a human review reason.",
    "correct_filename": "The business filename should use only validated naming components and approved placeholders.",
    "correct_mapping": "The validated field should map only to its approved destination contract.",
    "correct_reference_lookup": "Reference resolution should use the approved deterministic lookup boundary and fail closed.",
    "prevent_duplicate_action": "Recovery should reconcile exact durable identity before any repeated external action.",
    "needs_investigation": "The behavior requires repository investigation before a safe change can be proposed.",
    "external_dependency": "The correction depends on an approved external-system capability that is not currently available.",
}

AFFECTED_FIELDS = (
    "Document Category",
    "Document Subtype",
    "Classification Confidence",
    "Review Status",
    "Review Reason",
    "Filename",
    "Patient Name",
    "Member ID",
    "Payer",
    "Authorization Number",
    "Authorization Status",
    "Request Type",
    "Service Code",
    "Service Description",
    "Program",
    "Modifier",
    "Authorized Units",
    "Authorization Unit",
    "Approved Visits",
    "Start Date",
    "End Date",
    "Posted Date",
    "Member Date of Birth",
    "Provider",
    "Diagnosis",
    "Hours",
    "Days Per Week",
    "Service Line",
    "Mapping",
    "Reference Data",
    "Recovery",
    "External System",
)

TRAINING_MODES = (
    "schema_only",
    "read_only",
    "proposal_write",
    "approval_dispatch",
)

_SAFE_FIELD_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9 /_-]{0,79}$")
_SAFE_BEHAVIOR_TEXT = re.compile(r"^[A-Za-z][A-Za-z0-9 .,;:()/_'\-]{0,1499}$")


@dataclass(frozen=True, repr=False)
class CorrectionComment:
    discussion_id: int
    comment_id: int
    created_at: str
    modified_at: str
    author_display: str
    text: str


@dataclass(frozen=True, repr=False)
class CorrectionRow:
    row_id: int
    values: dict[str, Any]
    sheet_version: int


@dataclass(frozen=True, repr=False)
class CorrectionSchemaResult:
    success: bool
    status: str
    column_count: int
    column_ids: dict[str, int]
    column_types: dict[str, str]
    system_column_types: dict[str, str]
    context_column_ids: dict[str, int]


@dataclass(frozen=True, repr=False)
class CorrectionAnalysis:
    correction_type: str
    affected_fields: tuple[str, ...]
    behavior_code: str
    desired_behavior: str
    likely_layers: tuple[str, ...]
    information_sufficient: bool


@dataclass(frozen=True)
class TrainingCycleSummary:
    flagged_case_count: int = 0
    new_case_count: int = 0
    updated_case_count: int = 0
    analysis_ready_count: int = 0
    awaiting_approval_count: int = 0
    implementation_authorized_count: int = 0
    implementation_started_count: int = 0
    implementation_completed_count: int = 0
    implementation_failed_count: int = 0
    retest_required_count: int = 0
    resolved_count: int = 0
    needs_more_information_count: int = 0
    requires_external_system_count: int = 0
    polling_result: str = "completed"
    failure_category: str = "none"
    recoverable: bool = False
    retryable: bool = False


def normalize_checkbox(value: Any) -> bool | None:
    """Normalize official untouched/boolean values; reject every other shape."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise ValueError("checkbox_value_invalid")


def validate_analysis(value: Any) -> CorrectionAnalysis:
    if not isinstance(value, CorrectionAnalysis):
        raise ValueError("correction_analysis_invalid")
    correction_type = value.correction_type.strip() if isinstance(value.correction_type, str) else ""
    if correction_type not in CORRECTION_TYPES:
        raise ValueError("correction_type_invalid")
    if not isinstance(value.information_sufficient, bool):
        raise ValueError("correction_sufficiency_invalid")
    fields = _normalize_vocab(value.affected_fields, allowed=AFFECTED_FIELDS)
    layers = _normalize_vocab(value.likely_layers, allowed=IMPLEMENTATION_LAYERS)
    behavior_code = value.behavior_code.strip() if isinstance(value.behavior_code, str) else ""
    if behavior_code not in BEHAVIOR_CODES:
        raise ValueError("correction_behavior_code_invalid")
    behavior = value.desired_behavior.strip() if isinstance(value.desired_behavior, str) else ""
    if value.information_sufficient and not _SAFE_BEHAVIOR_TEXT.fullmatch(behavior):
        raise ValueError("correction_behavior_invalid")
    if not value.information_sufficient:
        behavior = "More reviewer information is required before a correction can be proposed."
        behavior_code = "needs_investigation"
        correction_type = "Needs Investigation"
    return CorrectionAnalysis(
        correction_type=correction_type,
        affected_fields=fields,
        behavior_code=behavior_code,
        desired_behavior=behavior,
        likely_layers=layers or ("Needs Investigation",),
        information_sufficient=value.information_sufficient,
    )


def build_proposal(analysis: CorrectionAnalysis) -> str:
    validated = validate_analysis(analysis)
    if not validated.information_sufficient:
        return validated.desired_behavior
    field_text = ", ".join(validated.affected_fields) or "the affected AI output"
    proposal = f"For {field_text}: {validated.desired_behavior}"
    if len(proposal) > 1500 or not _SAFE_BEHAVIOR_TEXT.fullmatch(proposal):
        raise ValueError("correction_proposal_invalid")
    return proposal


def safe_behavior_for_code(behavior_code: str) -> str:
    try:
        return BEHAVIOR_CODES[behavior_code]
    except (KeyError, TypeError):
        raise ValueError("correction_behavior_code_invalid") from None


def local_analysis_schema() -> dict[str, Any]:
    """Return the exact constrained schema accepted from the local model."""
    return {
        "type": "object",
        "properties": {
            "correction_type": {"type": "string", "enum": list(CORRECTION_TYPES)},
            "affected_fields": {
                "type": "array",
                "items": {"type": "string", "enum": list(AFFECTED_FIELDS)},
                "maxItems": 10,
            },
            "behavior_code": {
                "type": "string", "enum": list(BEHAVIOR_CODES)
            },
            "desired_behavior": {"type": "string", "maxLength": 1500},
            "likely_layers": {
                "type": "array",
                "items": {"type": "string", "enum": list(IMPLEMENTATION_LAYERS)},
                "maxItems": 4,
            },
            "information_sufficient": {"type": "boolean"},
        },
        "required": [
            "correction_type", "affected_fields", "behavior_code",
            "desired_behavior", "likely_layers", "information_sufficient",
        ],
        "additionalProperties": False,
    }


def _normalize_vocab(
    values: Iterable[str] | Any,
    *,
    allowed: Iterable[str] | None,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise ValueError("correction_vocabulary_invalid")
    allow = set(allowed) if allowed is not None else None
    normalized = []
    for value in values:
        item = value.strip() if isinstance(value, str) else ""
        if not item or not _SAFE_FIELD_NAME.fullmatch(item):
            raise ValueError("correction_vocabulary_invalid")
        if allow is not None and item not in allow:
            raise ValueError("correction_vocabulary_invalid")
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)
