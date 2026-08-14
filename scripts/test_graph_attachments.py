from src.graph.attachment_service import AttachmentService
from src.graph.email_service import EmailService
from src.graph.errors import GraphBoundaryError


def main() -> None:
    print("Attachment diagnostic attempted: True")

    total_downloaded = 0
    messages_with_attachments = 0
    skipped_or_errors = 0
    status = "completed"

    try:
        email_service = EmailService()
        attachment_service = AttachmentService()
        messages = email_service.get_unread_messages(
            top=10
        )
    except GraphBoundaryError as error:
        messages = []
        skipped_or_errors = 1
        status = error.category
    except Exception:
        messages = []
        skipped_or_errors = 1
        status = "attachment_diagnostic_failed"

    for message in messages:
        has_attachments = message.get(
            "hasAttachments",
            False,
        ) is True

        if not has_attachments:
            continue

        message_id = message.get("id")
        messages_with_attachments += 1

        if not message_id:
            skipped_or_errors += 1
            status = "completed_with_errors"
            continue

        try:
            downloaded_files = (
                attachment_service
                .download_file_attachments(
                    message_id
                )
            )
            total_downloaded += len(
                downloaded_files
            )
        except GraphBoundaryError as error:
            skipped_or_errors += 1
            status = error.category
        except Exception:
            skipped_or_errors += 1
            status = "attachment_diagnostic_failed"

    print(
        f"Messages checked: {len(messages)}"
    )
    print(
        "Messages with attachments: "
        f"{messages_with_attachments}"
    )
    print(
        "Attachments downloaded: "
        f"{total_downloaded}"
    )
    print(
        f"Skipped/errors: {skipped_or_errors}"
    )
    print(
        f"Status: {status}"
    )


if __name__ == "__main__":
    main()
