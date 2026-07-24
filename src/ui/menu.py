import os

from clients.smartsheet_client import SmartsheetClient
from services.task_service import TaskService


def clear_screen():
    os.system("cls")


def pause():
    input("\nPress Enter to continue...")


def show_project_summary():
    client = SmartsheetClient()
    sheet = client.get_sheet()

    print("\nProject Summary")
    print("-" * 40)
    print(f"Project : {sheet.name}")
    print(f"Rows    : {len(sheet.rows)}")

    pause()


def find_task():
    service = TaskService()

    print("\nFind Task")
    print("-" * 40)

    task_name = input("Task Name: ")

    row = service.find_task(task_name)

    if row:
        print("\nTask Found!")
        print(f"Row ID: {row.id}")
    else:
        print("\nTask not found.")

    pause()


def run_menu():
    while True:
        clear_screen()

        print("=" * 50)
        print("      LTHHC AI AUTOMATION PLATFORM")
        print("=" * 50)

        print("\n1. Project Summary")
        print("2. Find Task")
        print("3. Update Task Status (Coming Soon)")
        print("4. Add Comment (Coming Soon)")
        print("5. Exit")

        choice = input("\nSelect an option: ")

        if choice == "1":
            show_project_summary()

        elif choice == "2":
            find_task()

        elif choice == "5":
            print("\nGoodbye!")
            break

        else:
            print("\nFeature not built yet.")
            pause()