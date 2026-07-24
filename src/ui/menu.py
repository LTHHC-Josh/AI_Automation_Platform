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

    clear_screen()

    print("=" * 60)
    print("PROJECT SUMMARY")
    print("=" * 60)

    print(f"\nProject : {sheet.name}")
    print(f"Rows    : {len(sheet.rows)}")

    pause()


def task_details(service, task):

    while True:

        clear_screen()

        print("=" * 60)
        print("TASK DETAILS")
        print("=" * 60)

        print(f"\nTask              : {task.name}")
        print(f"Status            : {task.status}")
        print(f"Assigned To       : {task.assigned_to}")
        print(f"% Complete        : {task.percent_complete}")
        print(f"Latest Comment    : {task.latest_comment}")

        print("\n" + "-" * 60)
        print("1. Update Status")
        print("2. Back")

        choice = input("\nSelection: ")

        if choice == "1":

            print(f"\nCurrent Status: {task.status}")

            new_status = input("New Status: ")

            service.update_status(task, new_status)

            print("\n✅ Status updated successfully!")

            pause()

        elif choice == "2":
            return


def browse_tasks():

    service = TaskService()

    while True:

        clear_screen()

        tasks = service.get_tasks()

        print("=" * 80)
        print("PROJECT TASKS")
        print("=" * 80)

        print(f"{'#':<5}{'STATUS':<18}TASK")
        print("-" * 80)

        for i, task in enumerate(tasks, start=1):
            print(f"{i:<5}{task.status:<18}{task.name}")

        print("\n0. Back")

        choice = input("\nSelect Task Number: ")

        if choice == "0":
            return

        if not choice.isdigit():
            continue

        task = service.get_task(int(choice))

        if task is not None:
            task_details(service, task)
        else:
            print("\nInvalid task number.")
            pause()


def run_menu():

    while True:

        clear_screen()

        print("=" * 55)
        print("        LTHHC AI AUTOMATION PLATFORM")
        print("=" * 55)

        print("\n1. Project Summary")
        print("2. Browse Tasks")
        print("3. Exit")

        choice = input("\nSelect an option: ")

        if choice == "1":
            show_project_summary()

        elif choice == "2":
            browse_tasks()

        elif choice == "3":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid selection.")
            pause()