from dotenv import load_dotenv
import os
import smartsheet


class SmartsheetClient:

    def __init__(self):
        load_dotenv()

        self.api_token = os.getenv("SMARTSHEET_API_TOKEN")
        self.sheet_id = os.getenv("SMARTSHEET_SHEET_ID")

        if not self.api_token:
            raise ValueError("SMARTSHEET_API_TOKEN not found in .env")

        if not self.sheet_id:
            raise ValueError("SMARTSHEET_SHEET_ID not found in .env")

        self.client = smartsheet.Smartsheet(self.api_token)
        self.client.errors_as_exceptions(True)

    def get_sheet(self):
        return self.client.Sheets.get_sheet(self.sheet_id)

    def list_columns(self):

        sheet = self.get_sheet()

        print("\nColumns:\n")

        for column in sheet.columns:
            print(f"{column.title} --> {column.id}")

    def update_cell(self, row_id, column_id, value):

        row = smartsheet.models.Row()
        row.id = row_id

        cell = smartsheet.models.Cell()
        cell.column_id = column_id
        cell.value = value

        row.cells.append(cell)

        self.client.Sheets.update_rows(
            self.sheet_id,
            [row]
        )

    def update_row(self, row_id, updates):
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
            [row]
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
            [row]
        )

        return response.result[0]