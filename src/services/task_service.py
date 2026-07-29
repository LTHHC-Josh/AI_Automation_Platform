from src.clients.smartsheet_client import SmartsheetClient
from src.services.column_service import ColumnService
from src.services.row_service import RowService
from src.models.task import Task
import smartsheet


class TaskService:

    def __init__(self):
        self.client = SmartsheetClient()
        self.columns = ColumnService()
        self.rows = RowService()

    def _get_sheet(self):
        return self.client.get_sheet()

    def get_tasks(self):

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
                        latest_comment=comment,
                    )
                )

        return tasks

    def get_task(self, number):

        tasks = self.get_tasks()

        if number < 1 or number > len(tasks):
            return None

        return tasks[number - 1]

    def find_task(self, task_name):

        task_name = task_name.strip().lower()

        for task in self.get_tasks():

            if task.name.strip().lower() == task_name:
                return task

        return None

    def create_task(self, task_name):

        task_column = self.columns.get("Task Name")

        cell = smartsheet.models.Cell()
        cell.column_id = task_column
        cell.value = task_name

        return self.rows.create_row([cell])

    def update_field(self, task, column_name, value):

        column_id = self.columns.get(column_name)

        self.client.update_cell(
            task.row_id,
            column_id,
            value,
        )

    def update_status(self, task, new_status):

        self.update_field(
            task,
            "Status",
            new_status,
        )

        task.status = new_status

    def update_comment(self, task, comment):

        self.update_field(
            task,
            "Latest Comment",
            comment,
        )

        task.latest_comment = comment

    def update_percent_complete(self, task, percent_complete):
        """
        Updates the percent-complete field.

        Do not use this method when the Smartsheet column is controlled
        by a column formula.
        """

        self.update_field(
            task,
            "% Complete",
            percent_complete,
        )

        task.percent_complete = percent_complete

    def sync_task(
        self,
        task,
        status=None,
        comment=None,
    ):
        """
        Synchronizes editable task fields with Smartsheet.

        Only changed values are sent, and all changes for the row
        are included in one Smartsheet API request.

        Returns:
            True when Smartsheet was updated.
            False when no changes were needed.
        """

        updates = {}

        status_changed = (
            status is not None
            and task.status != status
        )

        comment_changed = (
            comment is not None
            and task.latest_comment != comment
        )

        if status_changed:
            status_column = self.columns.get("Status")
            updates[status_column] = status

        if comment_changed:
            comment_column = self.columns.get("Latest Comment")
            updates[comment_column] = comment

        if not updates:
            return False

        self.client.update_row(
            task.row_id,
            updates,
        )

        if status_changed:
            task.status = status

        if comment_changed:
            task.latest_comment = comment

        return True

    def sync_task_by_name(
        self,
        task_name,
        status=None,
        comment=None,
    ):
        """
        Finds a task by name and synchronizes its editable fields.

        Returns:
            True when Smartsheet was updated.
            False when no changes were needed.

        Raises:
            ValueError when the task cannot be found.
        """

        task = self.find_task(task_name)

        if task is None:
            raise ValueError(f"Task not found: {task_name}")

        return self.sync_task(
            task=task,
            status=status,
            comment=comment,
        )

    def complete_task(self, task_name):

        task = self.find_task(task_name)

        if task is None:
            print(f"Task not found: {task_name}")
            return False

        changed = self.sync_task(
            task=task,
            status="Completed",
        )

        if changed:
            print(f"Completed: {task.name}")
        else:
            print(f"Already completed: {task.name}")

        return True