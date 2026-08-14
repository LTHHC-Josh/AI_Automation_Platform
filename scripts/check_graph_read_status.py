from src.graph.email_service import EmailService
from src.graph.errors import GraphBoundaryError


def main() -> None:
    print("Read-status diagnostic attempted: True")

    try:
        service = EmailService()
        messages = service.get_recent_messages(
            top=10
        )
    except GraphBoundaryError as error:
        print("Messages checked: 0")
        print("Read messages: 0")
        print("Unread messages: 0")
        print(
            f"Status: {error.category}"
        )
        return
    except Exception:
        print("Messages checked: 0")
        print("Read messages: 0")
        print("Unread messages: 0")
        print("Status: read_status_diagnostic_failed")
        return

    read_count = sum(
        1
        for message in messages
        if message.get(
            "isRead"
        ) is True
    )

    print(
        f"Messages checked: {len(messages)}"
    )
    print(
        f"Read messages: {read_count}"
    )
    print(
        "Unread messages: "
        f"{len(messages) - read_count}"
    )
    print("Status: completed")


if __name__ == "__main__":
    main()
