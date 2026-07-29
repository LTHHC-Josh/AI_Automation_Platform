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