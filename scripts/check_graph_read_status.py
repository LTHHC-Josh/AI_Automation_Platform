from src.graph.email_service import EmailService


def main() -> None:
    print("=" * 60)
    print("Checking Microsoft Graph Read Status")
    print("=" * 60)

    service = EmailService()
    messages = service.get_recent_messages(top=10)

    if not messages:
        print("No inbox messages found.")
        return

    for index, message in enumerate(
        messages,
        start=1,
    ):
        print()
        print("-" * 60)
        print(f"Message number: {index}")
        print(
            "Subject: "
            f"{message.get('subject', '(No subject)')}"
        )
        print(
            "Received: "
            f"{message.get('receivedDateTime', '')}"
        )
        print(
            "Graph isRead: "
            f"{message.get('isRead')}"
        )
        print(
            "Message ID: "
            f"{message.get('id', '')}"
        )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()