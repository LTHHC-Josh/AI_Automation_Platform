from src.services.task_service import TaskService


class ProjectStatusService:

    def __init__(self):
        self.tasks = TaskService()

    def _find_task(self, task_name):

        task = self.tasks.find_task(task_name)

        if task is None:
            raise ValueError(f"Task not found: {task_name}")

        return task

    def complete_task(self, task_name, comment=""):

        task = self._find_task(task_name)

        self.tasks.update_status(task, "Completed")

        if comment:
            self.tasks.update_comment(task, comment)

        print(f"✓ Completed: {task_name}")

    def start_task(self, task_name, comment=""):

        task = self._find_task(task_name)

        self.tasks.update_status(task, "In Progress")

        if comment:
            self.tasks.update_comment(task, comment)

        print(f"✓ Started: {task_name}")

    def update_comment(self, task_name, comment):

        task = self._find_task(task_name)

        self.tasks.update_comment(task, comment)

        print(f"✓ Updated Comment: {task_name}")