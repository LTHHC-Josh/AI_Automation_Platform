from pathlib import Path
from dotenv import load_dotenv
import os
import smartsheet


class SmartsheetClient:

    DEFAULT_SHEET_ID_ENV_VAR = "SMARTSHEET_SHEET_ID"

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

        self.client.errors_as_exceptions(True)

    def get_sheet(self):
        return self.client.Sheets.get_sheet(
            self.sheet_id
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
        sheet = self.client.Sheets.get_sheet(
            self.sheet_id,
            column_ids=[column_id],
            include_all=True,
        )
        matches = []
        for row in getattr(sheet, "rows", []) or []:
            for cell in getattr(row, "cells", []) or []:
                if getattr(cell, "column_id", None) == column_id and getattr(cell, "value", None) == value:
                    row_id = getattr(row, "id", None)
                    if isinstance(row_id, int) and not isinstance(row_id, bool) and row_id > 0:
                        matches.append(row_id)
                    break
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
