from src.services.project_status_service import ProjectStatusService


service = ProjectStatusService()
tasks = service.tasks


updates = [
    (
        "Design Solution Architecture",
        "Completed",
        "Completed provider-based AI architecture with registry, factories, automatic provider discovery, and end-to-end validation.",
    ),
    (
        "Define Integration Architecture",
        "Completed",
        "Completed OCR → AI → Business Rules → Smartsheet architecture.",
    ),
    (
        "Design AI Pipeline",
        "Completed",
        "Implemented interchangeable OCR and LLM provider architecture.",
    ),
    (
        "Configure Branch Strategy",
        "Completed",
        "Git repository connected to GitHub and branch strategy validated.",
    ),
    (
        "Validate Development Environment",
        "Completed",
        "Python environment, virtual environment, GitHub integration, and AI platform validated.",
    ),
    (
        "Create OCR Service",
        "Completed",
        "OCR provider framework completed using mock provider.",
    ),
    (
        "Extract PDF Text",
        "In Progress",
        "Pipeline complete. Awaiting PaddleOCR implementation.",
    ),
    (
        "Unit Test OCR",
        "In Progress",
        "Mock OCR provider successfully validated.",
    ),
    (
        "Create Prompt Templates",
        "In Progress",
        "LLM provider framework complete. Prompt engineering started.",
    ),
    (
        "Implement Classification",
        "In Progress",
        "Mock document classification successfully implemented.",
    ),
    (
        "Implement Data Extraction",
        "In Progress",
        "Mock structured extraction successfully implemented.",
    ),
    (
        "Validate AI Output",
        "In Progress",
        "End-to-end AI platform successfully validated using mock providers.",
    ),
    (
        "Integration Testing",
        "Completed",
        "Smartsheet integration verified with successful read and update testing.",
    ),
]


print()
print("=" * 60)
print("Synchronizing Project Tracker")
print("=" * 60)
print()

updated = 0
unchanged = 0
not_found = 0
failed = 0

for task_name, status, comment in updates:
    try:
        task = tasks.find_task(task_name)

        if task is None:
            print(f"✗ Task not found: {task_name}")
            not_found += 1
            continue

        changed = tasks.sync_task(
            task=task,
            status=status,
            comment=comment,
        )

        if changed:
            updated += 1
            print(f"✓ Updated: {task_name}")
        else:
            unchanged += 1
            print(f"- No change: {task_name}")

    except Exception as ex:
        failed += 1
        print(f"✗ Failed: {task_name}")
        print(f"  {ex}")


print()
print("=" * 60)
print("Summary")
print("=" * 60)
print(f"Updated   : {updated}")
print(f"Unchanged : {unchanged}")
print(f"Not Found : {not_found}")
print(f"Failed    : {failed}")
print("=" * 60)