from src.services.task_service import TaskService


task_service = TaskService()

new_row = task_service.create_task(
    "Test Task from TaskService"
)

print(f"Created row ID: {new_row.id}")