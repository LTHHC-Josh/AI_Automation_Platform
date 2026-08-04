from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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
    """

    file_path: Path

    # Classification
    document_type: str = ""
    confidence: float = 0.0

    # OCR output
    raw_text: str = ""

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