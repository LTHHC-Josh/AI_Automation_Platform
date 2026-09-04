"""Deterministic contracts for Document Processor Training."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable

from src.models.document_processor_business_context import (
    DOCUMENT_PROCESSOR_BUSINESS_CONTEXT,
)


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

ANALYSIS_CONTRACT_VERSION = 2
CORRECTION_TYPES = DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.correction_types
TECHNICAL_DISPOSITIONS = (
    DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.technical_dispositions
)
FEEDBACK_RELATIONSHIPS = DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.feedback_relationships

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
    "New": frozenset({
        "Analysis Ready", "Needs More Information", "Requires External System",
    }),
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
    "correct_authorization_filename_subtype": (
        "A supported authorization intake subtype should use its canonical business filename token and only validated applicable naming components."
    ),
    "correct_mapping": "The validated field should map only to its approved destination contract.",
    "correct_reference_lookup": "Reference resolution should use the approved deterministic lookup boundary and fail closed.",
    "prevent_duplicate_action": "Recovery should reconcile exact durable identity before any repeated external action.",
    "needs_investigation": "The behavior requires repository investigation before a safe change can be proposed.",
    "external_dependency": "The correction depends on an approved external-system capability that is not currently available.",
}

OBSERVED_FAILURE_TYPES = (
    "Classification", "Document Subtype", "Missing Field",
    "Incorrect Field Value", "Confidence", "Review Reason",
    "Filename Token", "Filename Missing Component",
    "Filename Unrelated Component", "Service Line", "Modifier", "Date",
    "Quantity / Unit", "Mapping", "Reference Data",
    "Recovery / Duplicate Handling", "External System Dependency", "Other",
)

FILENAME_COMPONENTS = (
    "Canonical Document Type",
    "Validated Payer",
    "Applicable Validated Service",
    "Supported Date or Date Range",
)

EXCLUDED_FILENAME_COMPONENTS = ("Unrelated Extracted Fields",)

DOCUMENT_CATEGORY_CONCEPTS = tuple(
    item.family for item in DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.document_taxonomy
) + ("not_applicable",)

INTAKE_SUBTYPE_CONCEPTS = tuple(
    item.key for item in DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.intake_subtype_taxonomy
) + ("unknown", "not_applicable")

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

HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE = "historical_acceptance_blocked"
HISTORICAL_ACCEPTANCE_RESULT = (
    "Historical feedback acceptance only. Verify current behavior through a real "
    "retest before authorizing any implementation."
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
    primary_correction_type: str
    related_correction_types: tuple[str, ...]
    affected_fields: tuple[str, ...]
    behavior_code: str
    desired_behavior: str
    likely_layers: tuple[str, ...]
    desired_behavior_sufficient: bool
    technical_disposition: str
    feedback_relationship: str
    observed_failure_type: str
    affected_document_category: str
    desired_intake_subtype: str
    required_filename_components: tuple[str, ...]
    excluded_filename_components: tuple[str, ...]
    analysis_outcome_category: str = "validated"

    @property
    def correction_type(self) -> str:
        """Backward-readable alias for the one visible Smartsheet type."""
        return self.primary_correction_type


@dataclass(frozen=True)
class TrainingCycleSummary:
    effective_mode: str = "unavailable"
    business_context_version: int = (
        DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.business_context_version
    )
    analysis_contract_version: int = ANALYSIS_CONTRACT_VERSION
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
    correction_type = (
        value.primary_correction_type.strip()
        if isinstance(value.primary_correction_type, str) else ""
    )
    if correction_type not in CORRECTION_TYPES:
        raise ValueError("correction_type_invalid")
    if not isinstance(value.desired_behavior_sufficient, bool):
        raise ValueError("correction_sufficiency_invalid")
    if value.technical_disposition not in TECHNICAL_DISPOSITIONS:
        raise ValueError("correction_technical_disposition_invalid")
    if value.feedback_relationship not in FEEDBACK_RELATIONSHIPS:
        raise ValueError("correction_feedback_relationship_invalid")
    if value.observed_failure_type not in OBSERVED_FAILURE_TYPES:
        raise ValueError("correction_observed_failure_invalid")
    if value.affected_document_category not in DOCUMENT_CATEGORY_CONCEPTS:
        raise ValueError("correction_document_category_invalid")
    if value.desired_intake_subtype not in INTAKE_SUBTYPE_CONCEPTS:
        raise ValueError("correction_intake_subtype_invalid")
    fields = _normalize_vocab(value.affected_fields, allowed=AFFECTED_FIELDS)
    related = _normalize_vocab(
        value.related_correction_types, allowed=CORRECTION_TYPES
    )
    layers = _normalize_vocab(value.likely_layers, allowed=IMPLEMENTATION_LAYERS)
    required_components = _normalize_vocab(
        value.required_filename_components, allowed=FILENAME_COMPONENTS
    )
    excluded_components = _normalize_vocab(
        value.excluded_filename_components, allowed=EXCLUDED_FILENAME_COMPONENTS
    )
    behavior_code = value.behavior_code.strip() if isinstance(value.behavior_code, str) else ""
    if behavior_code not in BEHAVIOR_CODES:
        raise ValueError("correction_behavior_code_invalid")
    sufficient = value.desired_behavior_sufficient
    relationship = value.feedback_relationship
    if relationship in {"Conflicts", "Insufficient"}:
        sufficient = False
    filename_symptoms = {
        "Filename Token", "Filename Missing Component", "Filename Unrelated Component"
    }
    if (
        value.observed_failure_type in filename_symptoms
        or required_components
        or excluded_components
    ):
        correction_type = "Filename"
    if (
        correction_type == "Filename"
        and value.desired_intake_subtype not in {"unknown", "not_applicable"}
        and "Document Subtype" not in related
    ):
        related = (*related, "Document Subtype")
    related = tuple(item for item in related if item != correction_type)
    if not sufficient:
        behavior = "More reviewer information is required before a correction can be proposed."
        behavior_code = "needs_investigation"
        correction_type = "Needs Investigation"
        related = ()
        technical_disposition = "Needs Investigation"
        outcome = "model_business_intent_insufficient"
    else:
        technical_disposition = value.technical_disposition
        if value.desired_intake_subtype == "init":
            technical_disposition = "External Dependency"
            if "External System" not in layers:
                layers = (*layers, "External System")
        behavior = _render_desired_behavior(
            correction_type=correction_type,
            behavior_code=behavior_code,
            category=value.affected_document_category,
            subtype=value.desired_intake_subtype,
            required_components=required_components,
            excluded_components=excluded_components,
            technical_disposition=technical_disposition,
        )
        outcome = value.analysis_outcome_category
    if not _SAFE_BEHAVIOR_TEXT.fullmatch(behavior):
        raise ValueError("correction_behavior_invalid")
    return CorrectionAnalysis(
        primary_correction_type=correction_type,
        related_correction_types=related,
        affected_fields=fields,
        behavior_code=behavior_code,
        desired_behavior=behavior,
        likely_layers=layers or ("Needs Investigation",),
        desired_behavior_sufficient=sufficient,
        technical_disposition=technical_disposition,
        feedback_relationship=relationship,
        observed_failure_type=value.observed_failure_type,
        affected_document_category=value.affected_document_category,
        desired_intake_subtype=value.desired_intake_subtype,
        required_filename_components=required_components,
        excluded_filename_components=excluded_components,
        analysis_outcome_category=outcome,
    )


def build_proposal(analysis: CorrectionAnalysis) -> str:
    validated = validate_analysis(analysis)
    if not validated.desired_behavior_sufficient:
        return validated.desired_behavior
    proposal = validated.desired_behavior
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
            "primary_correction_type": {"type": "string", "enum": list(CORRECTION_TYPES)},
            "related_correction_types": {
                "type": "array", "items": {"type": "string", "enum": list(CORRECTION_TYPES)},
                "maxItems": 4,
            },
            "affected_fields": {
                "type": "array",
                "items": {"type": "string", "enum": list(AFFECTED_FIELDS)},
                "maxItems": 10,
            },
            "behavior_code": {
                "type": "string", "enum": list(BEHAVIOR_CODES)
            },
            "likely_layers": {
                "type": "array",
                "items": {"type": "string", "enum": list(IMPLEMENTATION_LAYERS)},
                "maxItems": 4,
            },
            "desired_behavior_sufficient": {"type": "boolean"},
            "technical_disposition": {
                "type": "string", "enum": list(TECHNICAL_DISPOSITIONS),
            },
            "feedback_relationship": {
                "type": "string", "enum": list(FEEDBACK_RELATIONSHIPS),
            },
            "observed_failure_type": {
                "type": "string", "enum": list(OBSERVED_FAILURE_TYPES),
            },
            "affected_document_category": {
                "type": "string", "enum": list(DOCUMENT_CATEGORY_CONCEPTS),
            },
            "desired_intake_subtype": {
                "type": "string", "enum": list(INTAKE_SUBTYPE_CONCEPTS),
            },
            "required_filename_components": {
                "type": "array", "items": {"type": "string", "enum": list(FILENAME_COMPONENTS)},
                "maxItems": 4,
            },
            "excluded_filename_components": {
                "type": "array", "items": {"type": "string", "enum": list(EXCLUDED_FILENAME_COMPONENTS)},
                "maxItems": 1,
            },
        },
        "required": [
            "primary_correction_type", "related_correction_types", "affected_fields",
            "behavior_code", "likely_layers", "desired_behavior_sufficient",
            "technical_disposition", "feedback_relationship", "observed_failure_type",
            "affected_document_category", "desired_intake_subtype",
            "required_filename_components", "excluded_filename_components",
        ],
        "additionalProperties": False,
    }


def _render_desired_behavior(
    *, correction_type: str, behavior_code: str, category: str, subtype: str,
    required_components: tuple[str, ...], excluded_components: tuple[str, ...],
    technical_disposition: str,
) -> str:
    if correction_type == "Filename" and subtype not in {"unknown", "not_applicable"}:
        definitions = {
            item.key: item
            for item in DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.intake_subtype_taxonomy
        }
        definition = definitions[subtype]
        evidence = (
            "authoritative external context"
            if definition.requires_external_context
            else "validated document evidence"
        )
        category_text = "authorization documents" if category == "authorization" else "supported documents"
        proposal = (
            f"For {category_text}, when the {definition.token} intake subtype is directly supported by "
            f"{evidence}, use the canonical AUTH {definition.token} document type token in the business filename."
        )
        if required_components:
            proposal += " Include " + ", ".join(
                component.lower() for component in required_components
            ) + " according to the established naming convention."
        if excluded_components:
            proposal += " Do not add unrelated extracted fields to the filename."
        if technical_disposition == "Needs Investigation":
            proposal += " The implementation layer requires repository investigation."
        return proposal
    return BEHAVIOR_CODES[behavior_code]


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
