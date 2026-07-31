from src.graph.attachment_service import AttachmentService
from src.graph.email_service import EmailService


def main() -> None:
    print("Checking unread messages for attachments...")

    email_service = EmailService()
    attachment_service = AttachmentService()

    messages = email_service.get_unread_messages(top=10)

    if not messages:
        print("No unread messages found.")
        return

    total_downloaded = 0

    for message in messages:
        subject = message.get("subject", "(No subject)")
        message_id = message.get("id")
        has_attachments = message.get("hasAttachments", False)

        print("-" * 60)
        print(f"Subject: {subject}")
        print(f"Has attachments: {has_attachments}")

        if not message_id or not has_attachments:
            continue

        downloaded_files = (
            attachment_service.download_file_attachments(
                message_id
            )
        )

        for file_path in downloaded_files:
            total_downloaded += 1
            print(f"Downloaded: {file_path}")

    print("-" * 60)
    print(f"Total attachments downloaded: {total_downloaded}")


if __name__ == "__main__":
    main()