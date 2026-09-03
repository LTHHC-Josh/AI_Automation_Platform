from typing import Any

from datetime import date
import math

from src.models.smartsheet_destination_validation import (
    SmartsheetDestinationValidationResult,
)
from src.models.smartsheet_mapping import (
    SmartsheetRowMappingResult,
)


class SmartsheetDestinationValidationService:
    """
    Validates a logical Smartsheet row mapping against an approved
    destination-column schema.

    This service:
    - does not connect to Smartsheet;
    - does not create Cell or Row objects;
    - does not retain or log mapped values;
    - validates column identifiers, destination types, writable state, and
      serialized scalar compatibility before any external request.
    """

    MAX_CELL_TEXT_LENGTH = 4000
    SUPPORTED_COLUMN_TYPES = frozenset({"CHECKBOX", "DATE", "TEXT_NUMBER"})

    def validate(
        self,
        mapping: SmartsheetRowMappingResult,
        available_columns: dict[str, int],
        available_column_types: dict[str, str] | None = None,
        available_system_column_types: dict[str, str] | None = None,
    ) -> SmartsheetDestinationValidationResult:
        """
        Resolve every logical destination column to a unique positive
        Smartsheet column identifier.

        Automatic write readiness requires both:
        - the upstream mapping to be ready;
        - every mapped destination column to exist and be valid.
        """

        result = SmartsheetDestinationValidationResult()

        if not isinstance(
            mapping,
            SmartsheetRowMappingResult,
        ):
            result.warnings.append(
                "Logical Smartsheet row mapping is unavailable or invalid."
            )
            return result

        result.mapping_ready = bool(mapping.ready_for_write)
        if not isinstance(mapping.values, dict):
            result.warnings.append(
                "Logical Smartsheet row values are unavailable or invalid."
            )
            result.rejection_safe_category = "row_mapping_values_invalid"
            return result

        result.mapped_field_count = len(mapping.values)
        result.included_cell_count = len(mapping.values)
        result.omitted_field_count = (
            len(mapping.omitted_columns)
            if isinstance(mapping.omitted_columns, list)
            else 0
        )

        mapped_column_names = self._get_mapped_column_names(mapping)
        mapping_keys_valid = (
            len(mapped_column_names) == len(mapping.values)
            and all(
                isinstance(name, str) and name.strip() == name and bool(name)
                for name in mapping.values
            )
        )
        duplicate_destinations = (
            list(mapping.duplicate_destination_columns)
            if isinstance(mapping.duplicate_destination_columns, list)
            else ["invalid"]
        )
        omitted_columns_valid = (
            isinstance(mapping.omitted_columns, list)
            and all(
                isinstance(name, str) and name.strip() == name and bool(name)
                for name in mapping.omitted_columns
            )
            and not set(mapping.omitted_columns).intersection(mapping.values)
        )
        result.mapping_validation_passed = (
            result.mapping_ready
            and mapping_keys_valid
            and not duplicate_destinations
            and omitted_columns_valid
            and bool(mapped_column_names)
        )
        if not mapping_keys_valid:
            result.rejected_field_categories.append(
                "row_mapping_destination_name_invalid"
            )
        if duplicate_destinations:
            result.rejected_field_categories.append(
                "row_mapping_duplicate_destination"
            )
        if not omitted_columns_valid:
            result.rejected_field_categories.append(
                "row_mapping_omission_contract_invalid"
            )
        if not result.mapping_validation_passed:
            result.rejection_safe_category = (
                result.rejected_field_categories[0]
                if result.rejected_field_categories
                else "mapping_not_ready"
            )

        normalized_columns = self._normalize_columns(
            available_columns=available_columns,
            result=result,
        )

        normalized_types = self._normalize_column_types(
            available_column_types
        )
        normalized_system_types = self._normalize_system_column_types(
            available_system_column_types
        )

        for column_name in mapped_column_names:
            column_id = normalized_columns.get(
                column_name
            )

            if column_id is None:
                result.missing_columns.append(
                    column_name
                )
                continue

            result.column_ids[
                column_name
            ] = column_id

            column_type = normalized_types.get(column_name)
            if column_type is None:
                result.invalid_columns.append(column_name)
                result.rejected_field_categories.append(
                    "row_mapping_column_type_unsupported"
                )
                if result.rejection_safe_category == "none":
                    result.rejection_safe_category = (
                        "row_mapping_column_type_unsupported"
                    )
                continue
            result.column_types[column_name] = column_type

            system_column_type = normalized_system_types.get(column_name)
            if system_column_type is None:
                result.invalid_columns.append(column_name)
                result.rejected_field_categories.append(
                    "row_mapping_writable_state_unavailable"
                )
                if result.rejection_safe_category == "none":
                    result.rejection_safe_category = (
                        "row_mapping_writable_state_unavailable"
                    )
                continue

            if system_column_type != "none":
                result.invalid_columns.append(column_name)
                result.rejected_field_categories.append(
                    "row_mapping_system_column_not_writable"
                )
                if result.rejection_safe_category == "none":
                    result.rejection_safe_category = (
                        "row_mapping_system_column_not_writable"
                    )
                continue

            category = self.value_rejection_category(
                value=mapping.values.get(column_name),
                column_type=column_type,
            )
            if category is not None:
                result.rejected_field_categories.append(category)
                if result.rejection_safe_category == "none":
                    result.rejection_safe_category = category

        result.missing_columns = self._deduplicate_text(
            result.missing_columns
        )
        result.invalid_columns = self._deduplicate_text(
            result.invalid_columns
        )
        result.duplicate_column_ids = self._deduplicate_integers(
            result.duplicate_column_ids
        )
        result.warnings = self._deduplicate_text(
            result.warnings
        )
        result.rejected_field_categories = self._deduplicate_text(
            result.rejected_field_categories
        )

        result.destination_ready = (
            bool(
                mapped_column_names
            )
            and not result.missing_columns
            and not result.invalid_columns
            and not result.duplicate_column_ids
            and len(
                result.column_ids
            ) == len(
                mapped_column_names
            )
        )
        result.schema_validation_passed = result.destination_ready
        result.type_validation_passed = (
            result.destination_ready
            and len(result.column_types) == len(mapped_column_names)
            and not result.rejected_field_categories
        )

        result.ready_for_write = (
            result.mapping_validation_passed
            and result.destination_ready
            and result.type_validation_passed
        )

        if not result.mapping_ready:
            result.warnings.append(
                "Upstream row mapping is not ready for automatic writing."
            )

        if result.missing_columns:
            result.warnings.append(
                "One or more mapped destination columns are missing."
            )

        if result.invalid_columns:
            result.warnings.append(
                "One or more destination columns have invalid identifiers."
            )

        if result.duplicate_column_ids:
            result.warnings.append(
                "Multiple destination columns resolve to the same identifier."
            )

        if result.rejected_field_categories:
            result.warnings.append(
                "One or more mapped values are incompatible with the destination contract."
            )

        result.warnings = self._deduplicate_text(
            result.warnings
        )

        return result

    def _normalize_column_types(self, values: Any) -> dict[str, str]:
        if not isinstance(values, dict):
            return {}
        normalized = {}
        for raw_name, raw_type in values.items():
            name = str(raw_name or "").strip()
            column_type = str(raw_type or "").strip().upper()
            if name and column_type in self.SUPPORTED_COLUMN_TYPES:
                normalized[name] = column_type
        return normalized

    @staticmethod
    def _normalize_system_column_types(values: Any) -> dict[str, str]:
        if not isinstance(values, dict):
            return {}
        return {
            str(name or "").strip(): str(value or "none").strip().lower()
            for name, value in values.items()
            if str(name or "").strip()
        }

    def value_rejection_category(
        self,
        *,
        value: Any,
        column_type: str,
    ) -> str | None:
        if value is None:
            return "row_mapping_value_missing"
        if column_type == "CHECKBOX":
            return (
                None
                if isinstance(value, bool)
                else "row_mapping_invalid_checkbox_value"
            )
        if column_type == "DATE":
            if not isinstance(value, str):
                return "row_mapping_invalid_date_value"
            try:
                parsed = date.fromisoformat(value)
            except ValueError:
                return "row_mapping_invalid_date_value"
            return (
                None
                if parsed.isoformat() == value
                else "row_mapping_invalid_date_value"
            )
        if column_type == "TEXT_NUMBER":
            if isinstance(value, bool):
                return "row_mapping_invalid_text_number_value"
            if isinstance(value, int):
                return None
            if isinstance(value, float):
                return (
                    None
                    if math.isfinite(value)
                    else "row_mapping_invalid_numeric_value"
                )
            if isinstance(value, str):
                return (
                    None
                    if len(value) <= self.MAX_CELL_TEXT_LENGTH
                    else "row_mapping_text_too_long"
                )
            return "row_mapping_unsupported_value_type"
        return "row_mapping_column_type_unsupported"

    def _normalize_columns(
        self,
        available_columns: Any,
        result: SmartsheetDestinationValidationResult,
    ) -> dict[str, int]:
        """
        Normalize a title-to-ID mapping without accepting invalid IDs.
        """

        if not isinstance(
            available_columns,
            dict,
        ):
            result.warnings.append(
                "Destination column schema is unavailable or invalid."
            )
            return {}

        normalized: dict[str, int] = {}
        ids_to_names: dict[int, str] = {}

        for raw_name, raw_id in available_columns.items():
            column_name = str(
                raw_name
            ).strip()

            if not column_name:
                result.invalid_columns.append(
                    "<blank column name>"
                )
                continue

            column_id = self._normalize_column_id(
                raw_id
            )

            if column_id is None:
                result.invalid_columns.append(
                    column_name
                )
                continue

            existing_name = ids_to_names.get(
                column_id
            )

            if (
                existing_name is not None
                and existing_name != column_name
            ):
                result.duplicate_column_ids.append(
                    column_id
                )
                continue

            normalized[
                column_name
            ] = column_id

            ids_to_names[
                column_id
            ] = column_name

        return normalized

    def _get_mapped_column_names(
        self,
        mapping: SmartsheetRowMappingResult,
    ) -> list[str]:
        """
        Read logical destination names without reading mapped values.
        """

        if not isinstance(
            mapping.values,
            dict,
        ):
            return []

        names: list[str] = []

        for raw_name in mapping.values:
            column_name = str(
                raw_name
            ).strip()

            if not column_name:
                continue

            if column_name in names:
                continue

            names.append(
                column_name
            )

        return names

    def _normalize_column_id(
        self,
        value: Any,
    ) -> int | None:
        """
        Accept positive integer identifiers only.

        Boolean values are rejected because bool is a subclass of int.
        """

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
        ):
            return None

        if value < 1:
            return None

        return value

    def _deduplicate_text(
        self,
        values: list[str],
    ) -> list[str]:
        """
        Deduplicate text while preserving first occurrence order.
        """

        seen: set[str] = set()
        deduplicated: list[str] = []

        for value in values:
            if value in seen:
                continue

            seen.add(
                value
            )
            deduplicated.append(
                value
            )

        return deduplicated

    def _deduplicate_integers(
        self,
        values: list[int],
    ) -> list[int]:
        """
        Deduplicate integers while preserving first occurrence order.
        """

        seen: set[int] = set()
        deduplicated: list[int] = []

        for value in values:
            if value in seen:
                continue

            seen.add(
                value
            )
            deduplicated.append(
                value
            )

        return deduplicated
