from clients.smartsheet_client import SmartsheetClient
from services.column_service import ColumnService
from models.task import Task


class TaskService:

    def __init__(self):
        self.client = SmartsheetClient()
        self.columns = ColumnService()

    def _get_sheet(self):
        return self.client.get_sheet()

    def get_tasks(self):
        """
        Returns a list of Task objects.
        """

        sheet = self._get_sheet()

        task_col = self.columns.get("Task Name")
        status_col = self.columns.get("Status")
        assigned_col = self.columns.get("Assigned To")
        percent_col = self.columns.get("% Complete")
        comment_col = self.columns.get("Latest Comment")

        tasks = []

        for row in sheet.rows:

            name = ""
            status = ""
            assigned = ""
            percent = ""
            comment = ""

            for cell in row.cells:

                if cell.column_id == task_col:
                    name = cell.value or ""

                elif cell.column_id == status_col:
                    status = cell.value or ""

                elif cell.column_id == assigned_col:
                    assigned = cell.value or ""

                elif cell.column_id == percent_col:
                    percent = cell.value or ""

                elif cell.column_id == comment_col:
                    comment = cell.value or ""

            if name:

                tasks.append(
                    Task(
                        row_id=row.id,
                        name=name,
                        status=status,
                        assigned_to=assigned,
                        percent_complete=percent,
                        latest_comment=comment
                    )
                )

        return tasks

    def get_task(self, number):

        tasks = self.get_tasks()

        if number < 1 or number > len(tasks):
            return None

        return tasks[number - 1]

    def update_status(self, task, new_status):

        status_column = self.columns.get("Status")

        self.client.update_cell(
            task.row_id,
            status_column,
            new_status
        )

        task.status = new_status