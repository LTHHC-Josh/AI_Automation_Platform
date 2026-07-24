from clients.smartsheet_client import SmartsheetClient


class TaskService:

    def __init__(self):
        self.client = SmartsheetClient()
        self.sheet = self.client.get_sheet()

    def find_task(self, task_name):
        """
        Find a task by its Task Name column.
        """

        for row in self.sheet.rows:

            if not row.cells:
                continue

            task = row.cells[0].value

            if task is None:
                continue

            if str(task).lower() == task_name.lower():
                return row

        return None