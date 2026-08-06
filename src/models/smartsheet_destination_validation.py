from dataclasses import dataclass, field


@dataclass
class SmartsheetDestinationValidationResult:
    """
    PHI-safe result from validating a logical row mapping against an
    approved destination-column schema.

    This result contains column names and identifiers only. It must not
    contain mapped cell values or Smartsheet payloads.
    """

    column_ids: dict[str, int] = field(
        default_factory=dict
    )
    missing_columns: list[str] = field(
        default_factory=list
    )
    invalid_columns: list[str] = field(
        default_factory=list
    )
    duplicate_column_ids: list[int] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )
    mapping_ready: bool = False
    destination_ready: bool = False
    ready_for_write: bool = False
