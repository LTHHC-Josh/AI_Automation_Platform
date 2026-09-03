from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SmartsheetColumnPolicy:
    """
    Defines one explicitly approved logical Smartsheet column mapping.

    source_field:
        Structured review-output field name.

    column_name:
        Destination Smartsheet column title.

    required:
        Whether a populated source value is required.

    review_only:
        Whether the destination is intended only for human-review
        workflows.

    confidence_column_name:
        Optional explicitly approved destination column for the exact
        confidence associated with source_field.
    """

    source_field: str
    column_name: str
    required: bool = False
    review_only: bool = False
    confidence_column_name: str | None = None
    confidence_column_supports_text: bool = False


@dataclass
class SmartsheetRowMappingResult:
    """
    Deterministic logical Smartsheet row-mapping result.

    values may contain PHI and must never be printed or logged.
    """

    values: dict[str, Any] = field(
        default_factory=dict
    )
    missing_required_columns: list[str] = field(
        default_factory=list
    )
    review_only_columns: list[str] = field(
        default_factory=list
    )
    prohibited_fields: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )
    ready_for_write: bool = False
    omitted_columns: list[str] = field(
        default_factory=list
    )
    duplicate_destination_columns: list[str] = field(
        default_factory=list
    )
