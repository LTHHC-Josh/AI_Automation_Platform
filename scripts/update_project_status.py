from src.services.project_status_service import ProjectStatusService


project = ProjectStatusService()


project.complete_task(
    "Authenticate API",
    "Connected to Smartsheet API and verified authentication."
)

project.complete_task(
    "Read Sheet Metadata",
    "ColumnService implemented and metadata retrieval verified."
)

project.complete_task(
    "Create Row Mapper",
    "TaskService abstracts Smartsheet row creation."
)

project.complete_task(
    "Insert Rows",
    "TaskService.create_task() tested successfully end-to-end."
)

project.complete_task(
    "Update Rows",
    "Task status updates verified successfully."
)

project.start_task(
    "Integration Testing",
    "End-to-end testing of Smartsheet services in progress."
)

print("\nProject status update complete.")