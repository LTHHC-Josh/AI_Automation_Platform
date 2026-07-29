from src.clients.smartsheet_client import SmartsheetClient


class ColumnService:

    def __init__(self):
        client = SmartsheetClient()
        sheet = client.get_sheet()

        self.columns = {}

        for column in sheet.columns:
            self.columns[column.title] = column.id

    def get(self, column_name):
        return self.columns.get(column_name)