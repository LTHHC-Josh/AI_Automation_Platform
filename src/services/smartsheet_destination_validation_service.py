from typing import Any

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
    - does not inspect or log mapped values;
    - validates column names and numeric column identifiers only.
    """

    def validate(
        self,
        mapping: SmartsheetRowMappingResult,
        available_columns: dict[str, int],
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

        result.mapping_ready = bool(
            mapping.ready_for_write
        )

        normalized_columns = self._normalize_columns(
            available_columns=available_columns,
            result=result,
        )

        mapped_column_names = self._get_mapped_column_names(
            mapping
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

        result.ready_for_write = (
            result.mapping_ready
            and result.destination_ready
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

        result.warnings = self._deduplicate_text(
            result.warnings
        )

        return result

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

        if isinstance(
            value,
            bool,
        ):
            return None

        try:
            column_id = int(
                value
            )
        except (TypeError, ValueError):
            return None

        if column_id < 1:
            return None

        return column_id

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
