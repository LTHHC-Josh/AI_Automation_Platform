from dotenv import load_dotenv
import os
import smartsheet


class SmartsheetClient:
    def __init__(self):
        # Load variables from the .env file
        load_dotenv()

        self.api_token = os.getenv("SMARTSHEET_API_TOKEN")
        self.sheet_id = os.getenv("SMARTSHEET_SHEET_ID")

        if not self.api_token:
            raise ValueError("SMARTSHEET_API_TOKEN not found in .env")

        if not self.sheet_id:
            raise ValueError("SMARTSHEET_SHEET_ID not found in .env")

        # Create the Smartsheet client
        self.client = smartsheet.Smartsheet(self.api_token)
        self.client.errors_as_exceptions(True)

    def get_sheet(self):
        """Returns the entire Smartsheet."""
        return self.client.Sheets.get_sheet(self.sheet_id)

    def list_columns(self):
        """Print all columns in the sheet."""
        sheet = self.get_sheet()

        print("\nColumns:\n")

        for column in sheet.columns:
            print(f"{column.title} --> {column.id}")