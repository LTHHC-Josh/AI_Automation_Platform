from dataclasses import dataclass
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


class SmartsheetDestinationSchemaService:
    """
    Reads only destination column titles and IDs from the approved
    AI-output Smartsheet.

    No row values, mapped values, OCR text, source_text, filenames,
    document paths, or patient data are returned or logged.
    """

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
            sheet = self.client.get_sheet()
        except Exception:
            return self._failure(
                "schema_read_failed"
            )

        raw_columns = getattr(
            sheet,
            "columns",
            None,
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
        )
