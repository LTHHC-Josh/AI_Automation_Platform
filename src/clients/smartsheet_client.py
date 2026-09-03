from pathlib import Path
from dotenv import load_dotenv
import os
import smartsheet


class _DefaultTimeoutSession:
    """Delegate to the SDK session while bounding otherwise-unbounded sends."""

    def __init__(self, session, timeout_seconds):
        self._session = session
        self._timeout_seconds = timeout_seconds

    def send(self, request, **kwargs):
        kwargs.setdefault("timeout", self._timeout_seconds)
        return self._session.send(request, **kwargs)

    def __getattr__(self, name):
        return getattr(self._session, name)


class SmartsheetClient:

    DEFAULT_SHEET_ID_ENV_VAR = "SMARTSHEET_SHEET_ID"
    DEFAULT_HTTP_TIMEOUT_SECONDS = 30.0

    def __init__(
        self,
        sheet_id_env_var=DEFAULT_SHEET_ID_ENV_VAR,
    ):
        load_dotenv()

        if (
            not isinstance(sheet_id_env_var, str)
            or not sheet_id_env_var.strip()
        ):
            raise ValueError(
                "Smartsheet sheet ID environment variable "
                "name is required."
            )

        self.api_token = os.getenv(
            "SMARTSHEET_API_TOKEN"
        )

        self.sheet_id_env_var = (
            sheet_id_env_var.strip()
        )

        self.sheet_id = os.getenv(
            self.sheet_id_env_var
        )

        if not self.api_token:
            raise ValueError(
                "SMARTSHEET_API_TOKEN not found in .env"
            )

        if not self.sheet_id:
            raise ValueError(
                f"{self.sheet_id_env_var} "
                "not found in .env"
            )

        self.client = smartsheet.Smartsheet(
            self.api_token
        )

        raw_timeout = os.getenv(
            "SMARTSHEET_HTTP_TIMEOUT_SECONDS",
            str(self.DEFAULT_HTTP_TIMEOUT_SECONDS),
        )
        try:
            timeout_seconds = float(raw_timeout)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "SMARTSHEET_HTTP_TIMEOUT_SECONDS must be a positive number."
            ) from error
        if timeout_seconds <= 0:
            raise ValueError(
                "SMARTSHEET_HTTP_TIMEOUT_SECONDS must be a positive number."
            )
        self.client._session = _DefaultTimeoutSession(
            self.client._session,
            timeout_seconds,
        )

        self.client.errors_as_exceptions(True)

    def get_sheet(self):
        return self.client.Sheets.get_sheet(
            self.sheet_id
        )

    def get_columns(self):
        """Return only destination column metadata, never sheet rows or cells."""
        return self.client.Sheets.get_columns(
            self.sheet_id,
            include_all=True,
        )

    def list_columns(self):

        sheet = self.get_sheet()

        print("\nColumns:\n")

        for column in sheet.columns:
            print(
                f"{column.title} --> {column.id}"
            )

    def update_cell(
        self,
        row_id,
        column_id,
        value,
    ):

        row = smartsheet.models.Row()
        row.id = row_id

        cell = smartsheet.models.Cell()
        cell.column_id = column_id
        cell.value = value

        row.cells.append(cell)

        self.client.Sheets.update_rows(
            self.sheet_id,
            [row],
        )

    def update_row(
        self,
        row_id,
        updates,
    ):
        """
        Updates multiple cells in a single Smartsheet API request.

        Parameters
        ----------
        row_id : int
            Smartsheet row ID

        updates : dict
            {
                column_id: value,
                column_id: value,
                ...
            }
        """

        row = smartsheet.models.Row()
        row.id = row_id

        for column_id, value in updates.items():

            cell = smartsheet.models.Cell()
            cell.column_id = column_id
            cell.value = value

            row.cells.append(cell)

        self.client.Sheets.update_rows(
            self.sheet_id,
            [row],
        )

    def add_row(self, cells):
        """
        Adds a new row to the configured Smartsheet.
        """

        row = smartsheet.models.Row()
        row.to_bottom = True
        row.cells = cells

        response = self.client.Sheets.add_rows(
            self.sheet_id,
            [row],
        )

        return response.result[0]

    def attach_file_to_row(
        self,
        row_id,
        file_path,
    ):
        """
        Attach one local file to an existing row.

        The Smartsheet SDK multipart boundary requires the actual file
        stream. Passing a local path string causes that string itself to
        be treated as the multipart file content.
        """

        path = Path(file_path)

        with path.open("rb") as file_stream:
            return self.client.Attachments.attach_file_to_row(
                self.sheet_id,
                row_id,
                file_stream,
            )

    def find_row_ids_by_exact_column_value(self, *, column_id, value):
        """Return protected row IDs matching one already-resolved technical column."""
        if isinstance(column_id, bool) or not isinstance(column_id, int) or column_id <= 0:
            raise ValueError("A valid technical column ID is required.")

        matches = []
        page = 1
        page_size = 100
        expected_version = None
        expected_total_row_count = None
        rows_seen = 0

        while True:
            sheet = self.client.Sheets.get_sheet(
                self.sheet_id,
                column_ids=[column_id],
                page_size=page_size,
                page=page,
            )
            version = getattr(sheet, "version", None)
            if page == 1:
                if isinstance(version, bool) or not isinstance(version, int) or version < 0:
                    raise RuntimeError("Paginated sheet response has an invalid version.")
                expected_version = version
            elif version != expected_version:
                raise RuntimeError("Sheet version changed during paginated read.")

            total_row_count = getattr(sheet, "total_row_count", None)
            if (
                isinstance(total_row_count, bool)
                or not isinstance(total_row_count, int)
                or total_row_count < 0
            ):
                raise RuntimeError("Paginated sheet response has an invalid row count.")
            if page == 1:
                expected_total_row_count = total_row_count
            elif total_row_count != expected_total_row_count:
                raise RuntimeError("Sheet row count changed during paginated read.")

            rows = list(getattr(sheet, "rows", []) or [])
            if rows_seen < total_row_count and not rows:
                raise RuntimeError("Paginated sheet response ended before all rows were read.")

            for row in rows:
                for cell in getattr(row, "cells", []) or []:
                    if (
                        getattr(cell, "column_id", None) == column_id
                        and getattr(cell, "value", None) == value
                    ):
                        row_id = getattr(row, "id", None)
                        if (
                            isinstance(row_id, int)
                            and not isinstance(row_id, bool)
                            and row_id > 0
                        ):
                            matches.append(row_id)
                        break

            rows_seen += len(rows)
            if rows_seen > total_row_count:
                raise RuntimeError("Paginated sheet response exceeded its row count.")
            if rows_seen >= total_row_count:
                break
            page += 1

        return matches

    def find_row_ids_by_exact_column_title_value(self, *, column_title, value):
        if not isinstance(column_title, str) or not column_title.strip():
            raise ValueError("A configured technical column is required.")
        response = self.client.Sheets.get_columns(self.sheet_id, include_all=True)
        columns = getattr(response, "data", response)
        matches = [column.id for column in (columns or [])
                   if getattr(column, "title", None) == column_title]
        if len(matches) != 1:
            raise ValueError("Configured technical column is unavailable or ambiguous.")
        return self.find_row_ids_by_exact_column_value(column_id=matches[0], value=value)

    def list_row_attachment_names(self, *, row_id):
        """Return attachment names for one protected known row."""
        if isinstance(row_id, bool) or not isinstance(row_id, int) or row_id <= 0:
            raise ValueError("A valid row reference is required.")
        response = self.client.Attachments.list_row_attachments(
            self.sheet_id, row_id, include_all=True,
        )
        data = getattr(response, "data", response)
        return [
            name for item in (data or [])
            if isinstance((name := getattr(item, "name", None)), str)
        ]
