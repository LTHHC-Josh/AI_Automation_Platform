"""
Updates completed setup tasks in the LTHHC AI Platform Smartsheet.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.services.task_service import TaskService


def main():

    service = TaskService()

    tasks = [
        "Install Python",
        "Install VS Code",
        "Install Git",
        "Install Ollama",
        "Create Repository",
        "Configure Virtual Environment",
    ]

    print("\nLTHHC Project Updater\n")

    for task in tasks:
        print(f"Updating: {task}")
        service.complete_task(task)

    print("\nDone.")


if __name__ == "__main__":
    main()