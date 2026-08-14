from src.graph.mailbox_processor import MailboxProcessor


def format_percentage(
    value: float | None,
) -> str:
    if value is None:
        return "Not available"

    return f"{value * 100:.1f}%"


def main() -> None:
    print("=" * 60)
    print("Testing Mailbox Document Processing")
    print("=" * 60)

    total_downloaded = 0
    total_processed = 0
    total_skipped = 0
    total_marked_read = 0
    total_human_review = 0
    total_errors = 0

    try:
        processor = MailboxProcessor()

        results = processor.process_unread_messages(
            top=10
        )
    except Exception:
        results = []
        total_errors = 1

    for message_number, result in enumerate(
        results,
        start=1,
    ):
        print()
        print("-" * 60)
        print(
            f"Message sequence: {message_number}"
        )

        total_downloaded += len(
            result.downloaded_files
        )

        total_skipped += len(
            result.skipped_files
        )

        for document in result.processed_documents:
            total_processed += 1

            if document.needs_human_review:
                total_human_review += 1

            print()
            print(
                f"Document type: {document.document_type}"
            )

            print(
                "Classification confidence: "
                f"{format_percentage(document.confidence)}"
            )

            print(
                "Minimum field confidence: "
                f"{format_percentage(
                    document.minimum_field_confidence
                )}"
            )

            print(
                "Field count: "
                f"{len(document.field_evidence)}"
            )

            print(
                "Service-line count: "
                f"{len(document.service_lines)}"
            )

            print(
                "Validation-action count: "
                f"{len(document.validation_actions)}"
            )

            print(
                "Business-rule-action count: "
                f"{len(document.rule_actions)}"
            )

            print(
                f"Review status: "
                f"{document.review_status}"
            )

            print(
                "Review required: "
                f"{document.needs_human_review}"
            )

            print(
                "Review-reason count: "
                f"{len(document.review_reasons)}"
            )

        total_errors += len(
            result.errors
        )

        if result.marked_as_read:
            total_marked_read += 1

        print(
            "Message processing succeeded: "
            f"{result.succeeded}"
        )

        print(
            "Message marked as read: "
            f"{result.marked_as_read}"
        )

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Messages checked : {len(results)}")
    print(f"Files downloaded : {total_downloaded}")
    print(f"Files processed  : {total_processed}")
    print(f"Files skipped    : {total_skipped}")
    print(f"Human review     : {total_human_review}")
    print(f"Marked as read   : {total_marked_read}")
    print(f"Errors           : {total_errors}")
    print(
        "Status            : "
        + (
            "completed"
            if total_errors == 0
            else "completed_with_errors"
        )
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
