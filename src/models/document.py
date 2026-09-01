from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.models.ocr_document import OCRDocument
from src.models.document_concept import DeterministicDocumentConcept


@dataclass
class AuthorizationServiceLine:
    """
    Represents one service row extracted from an authorization.

    This model preserves the relationship between a service code,
    modifier, quantity, dates, status, confidence, and source evidence.

    It does not interpret the business meaning of those values.
    """

    service_code: str | None = None
    modifier: str | None = None
    quantity: Any = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    confidence: float = 0.0
    source_text: str = ""
    candidate_evidence: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class Document:
    """
    Represents a document as it moves through the AI pipeline.

    Extracted fields are retained in three forms:

    extracted_data:
        Flat field-name-to-value mapping used by business rules.

    field_confidences:
        Flat field-name-to-confidence mapping used by review logic.

    field_evidence:
        Complete field evidence containing value, confidence, and
        source_text for deterministic validation and auditing.

    service_lines:
        Optional row-level authorization service data. Existing flat
        fields remain available for backward compatibility.

    processing_metrics:
        PHI-safe processing durations and local model-generation
        statistics. OCR text, source evidence, extracted values, and
        identifiers must never be stored in this structure.
    """

    file_path: Path

    # Classification
    #
    # document_type remains the backward-compatible routing value used
    # by extraction and retry behavior.
    #
    # document_category and document_subtype preserve the richer
    # classification contract used by review and future Smartsheet
    # workflows.
    document_type: str = ""
    document_category: str = "unknown"
    document_subtype: str = "unknown"
    classification_reason: str = ""
    confidence: float = 0.0
    classification_support_status: str = "unknown"
    subtype_support_status: str = "unknown"
    family_evidence_confidence: float | None = None
    subtype_evidence_confidence: float | None = None

    # OCR output
    raw_text: str = ""
    ocr_document: OCRDocument | None = field(default=None, repr=False)
    deterministic_concepts: tuple[DeterministicDocumentConcept, ...] = field(
        default=(), repr=False
    )

    # Extracted structured values
    extracted_data: dict[str, Any] = field(
        default_factory=dict
    )

    # Confidence score for each extracted field
    field_confidences: dict[str, float] = field(
        default_factory=dict
    )

    # Full extraction evidence for each field
    field_evidence: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    # Optional row-level authorization service data
    service_lines: list[AuthorizationServiceLine] = field(
        default_factory=list
    )

    # PHI-safe processing and local-model metrics
    processing_metrics: dict[str, Any] = field(
        default_factory=dict
    )

    # Deterministic evidence-validation output
    validation_actions: list[str] = field(
        default_factory=list
    )

    # Business-rule output
    rule_actions: list[str] = field(
        default_factory=list
    )

    # Human-review decision
    needs_human_review: bool = False
    review_status: str = ""
    review_reasons: list[str] = field(
        default_factory=list
    )
    minimum_field_confidence: float | None = None

    # Structured local human-review handoff
    review_output: Any = None
