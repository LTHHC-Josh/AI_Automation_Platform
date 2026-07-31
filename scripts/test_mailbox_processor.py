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

    processor = MailboxProcessor()

    results = processor.process_unread_messages(
        top=10
    )

    if not results:
        print("No unread messages found.")
        return

    total_downloaded = 0
    total_processed = 0
    total_skipped = 0
    total_marked_read = 0
    total_human_review = 0
    total_errors = 0

    for result in results:
        print()
        print("-" * 60)
        print(f"Subject: {result.subject}")
        print(f"Message ID: {result.message_id}")

        for file_path in result.downloaded_files:
            total_downloaded += 1
            print(f"Downloaded: {file_path}")

        for file_path in result.skipped_files:
            total_skipped += 1
            print(
                f"Skipped unsupported file: {file_path}"
            )

        for document in result.processed_documents:
            total_processed += 1

            if document.needs_human_review:
                total_human_review += 1

            print()
            print(f"Processed: {document.file_path}")

            print(
                f"Document type: {document.document_type}"
            )

            print(
                "Classification confidence: "
                f"{format_percentage(document.confidence)}"
            )

            print(
                f"Raw text: {document.raw_text}"
            )

            print(
                f"Extracted data: "
                f"{document.extracted_data}"
            )

            print(
                f"Field confidences: "
                f"{document.field_confidences}"
            )

            print(
                "Minimum field confidence: "
                f"{format_percentage(
                    document.minimum_field_confidence
                )}"
            )

            print(
                f"Business-rule actions: "
                f"{document.rule_actions}"
            )

            print(
                f"Review status: "
                f"{document.review_status}"
            )

            print(
                "Human verification required: "
                f"{document.needs_human_review}"
            )

            print(
                f"Review reasons: "
                f"{document.review_reasons}"
            )

        for error in result.errors:
            total_errors += 1
            print(f"Error: {error}")

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
    print("=" * 60)


if __name__ == "__main__":
    main()