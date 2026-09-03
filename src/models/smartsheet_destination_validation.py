from dataclasses import dataclass, field


SMARTSHEET_ROW_REQUEST_CONTRACT_VERSION = 2


@dataclass
class SmartsheetDestinationValidationResult:
    """
    PHI-safe result from validating a logical row mapping against an
    approved destination-column schema.

    This result contains only approved column metadata, fixed validation
    categories, and aggregate counts. It must not contain mapped cell values
    or Smartsheet payloads.
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
    column_types: dict[str, str] = field(
        default_factory=dict
    )
    mapped_field_count: int = 0
    included_cell_count: int = 0
    omitted_field_count: int = 0
    mapping_validation_passed: bool = False
    schema_validation_passed: bool = False
    type_validation_passed: bool = False
    rejected_field_categories: list[str] = field(
        default_factory=list
    )
    rejection_safe_category: str = "none"
    request_contract_version: int = SMARTSHEET_ROW_REQUEST_CONTRACT_VERSION
