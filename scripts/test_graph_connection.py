from src.graph.email_service import EmailService
from src.graph.errors import GraphBoundaryError


def main() -> None:
    print("Connection attempted: True")

    try:
        service = EmailService()
        messages = service.get_unread_messages(
            top=10
        )
    except GraphBoundaryError as error:
        print("Connection successful: False")
        print("Messages checked: 0")
        print("Unread messages: 0")
        print("Messages with attachments: 0")
        print(
            f"Status: {error.category}"
        )
        return
    except Exception:
        print("Connection successful: False")
        print("Messages checked: 0")
        print("Unread messages: 0")
        print("Messages with attachments: 0")
        print("Status: graph_diagnostic_failed")
        return

    attachment_count = sum(
        1
        for message in messages
        if message.get(
            "hasAttachments",
            False,
        ) is True
    )

    print("Connection successful: True")
    print(
        f"Messages checked: {len(messages)}"
    )
    print(
        f"Unread messages: {len(messages)}"
    )
    print(
        "Messages with attachments: "
        f"{attachment_count}"
    )
    print("Status: completed")


if __name__ == "__main__":
    main()
