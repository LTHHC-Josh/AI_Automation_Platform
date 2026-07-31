from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """
    Represents a document as it moves through the AI pipeline.
    """

    file_path: Path

    # Classification
    document_type: str = ""
    confidence: float = 0.0

    # OCR output
    raw_text: str = ""

    # Extracted structured data
    extracted_data: dict = field(default_factory=dict)

    # Optional confidence score for each extracted field
    field_confidences: dict[str, float] = field(
        default_factory=dict
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