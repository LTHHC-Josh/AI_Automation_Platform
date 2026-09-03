from dataclasses import dataclass, field
from typing import Any

from src.clients.smartsheet_client import (
    SmartsheetClient,
)


@dataclass(frozen=True)
class SmartsheetDestinationSchemaResult:
    column_count: int
    columns: dict[str, int]
    success: bool
    status: str
    column_types: dict[str, str] = field(default_factory=dict)
    system_column_types: dict[str, str] = field(default_factory=dict)


class SmartsheetDestinationSchemaService:
    """
    Reads only destination column titles, IDs, types, and system-column
    metadata from the approved AI-output Smartsheet.

    No row values, mapped values, OCR text, source_text, filenames,
    document paths, or patient data are returned or logged.
    """

    SYSTEM_COLUMN_TYPES = frozenset({
        "AUTO_NUMBER",
        "CREATED_BY",
        "CREATED_DATE",
        "MODIFIED_BY",
        "MODIFIED_DATE",
    })

    @classmethod
    def system_column_type_category(
        cls,
        value: Any,
    ) -> str:
        """Normalize SDK wrapper values without relying on wrapper truthiness."""
        normalized = str(value).strip().upper()
        if normalized in {"", "NONE", "NULL"}:
            return "none"
        if normalized in cls.SYSTEM_COLUMN_TYPES:
            return normalized
        return "unexpected"

    @classmethod
    def is_system_column_type(
        cls,
        value: Any,
    ) -> bool:
        """Return whether normalized metadata designates a system column."""
        return cls.system_column_type_category(value) != "none"

    def __init__(
        self,
        *,
        client: SmartsheetClient | None = None,
    ) -> None:
        self.client = (
            client
            or SmartsheetClient(
                sheet_id_env_var=(
                    "SMARTSHEET_AI_DESTINATION_SHEET_ID"
                )
            )
        )

    def read(
        self,
    ) -> SmartsheetDestinationSchemaResult:
        try:
            response = self.client.get_columns()
        except Exception:
            return self._failure(
                "schema_read_failed"
            )

        raw_columns = getattr(
            response,
            "data",
            response,
        )

        try:
            raw_columns = list(
                raw_columns
            )
        except TypeError:
            return self._failure(
                "invalid_schema"
            )

        columns = {}
        column_types = {}
        system_column_types = {}

        for column in raw_columns:
            title = getattr(
                column,
                "title",
                None,
            )

            column_id = getattr(
                column,
                "id",
                None,
            )

            column_type = str(
                getattr(column, "type", "") or ""
            ).strip().upper()

            if (
                not isinstance(
                    title,
                    str,
                )
                or not title.strip()
            ):
                return self._failure(
                    "invalid_column_title"
                )

            if (
                isinstance(
                    column_id,
                    bool,
                )
                or not isinstance(
                    column_id,
                    int,
                )
                or column_id <= 0
            ):
                return self._failure(
                    "invalid_column_id"
                )

            normalized_title = (
                title.strip()
            )

            if normalized_title in columns:
                return self._failure(
                    "duplicate_column_title"
                )

            columns[
                normalized_title
            ] = column_id
            column_types[normalized_title] = column_type
            system_column_types[normalized_title] = (
                self.system_column_type_category(
                    getattr(column, "system_column_type", None)
                )
            )

        if not columns:
            return self._failure(
                "empty_schema"
            )

        return SmartsheetDestinationSchemaResult(
            column_count=len(
                columns
            ),
            columns=columns,
            success=True,
            status="ready",
            column_types=column_types,
            system_column_types=system_column_types,
        )

    @staticmethod
    def _failure(
        status: str,
    ) -> SmartsheetDestinationSchemaResult:
        return SmartsheetDestinationSchemaResult(
            column_count=0,
            columns={},
            success=False,
            status=status,
            column_types={},
            system_column_types={},
        )
