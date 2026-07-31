from src.graph.email_service import EmailService


def main() -> None:
    print("Connecting to Microsoft Graph...")

    service = EmailService()
    messages = service.get_unread_messages(top=10)

    print(f"Connection successful. Found {len(messages)} unread message(s).")

    for message in messages:
        sender = (
            message.get("from", {})
            .get("emailAddress", {})
            .get("address", "Unknown sender")
        )

        print("-" * 60)
        print(f"Subject: {message.get('subject', '(No subject)')}")
        print(f"From: {sender}")
        print(f"Received: {message.get('receivedDateTime', 'Unknown')}")
        print(f"Has attachments: {message.get('hasAttachments', False)}")


if __name__ == "__main__":
    main()