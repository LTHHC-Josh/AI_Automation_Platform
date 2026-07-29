"""
Service for working directly with Smartsheet rows.
"""

from src.clients.smartsheet_client import SmartsheetClient


class RowService:

    def __init__(self):

        self.client = SmartsheetClient()

    def create_row(self, cells):
        """
        Creates a new row.

        Parameters
        ----------
        cells : list
            List of Cell objects.

        Returns
        -------
        Row
        """

        return self.client.add_row(cells)