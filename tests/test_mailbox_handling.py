from pathlib import Path

from src.graph.mailbox_processor import (
    MailboxProcessor,
)


passed = 0
failed = 0


class RecordingEmailService:
    def __init__(
        self,
        *,
        mark_result=True,
        mark_error=None,
    ):
        self.mark_result = mark_result
        self.mark_error = mark_error
        self.mark_calls = []

    def mark_as_read(
        self,
        message_id,
    ):
        self.mark_calls.append(
            message_id
        )

        if self.mark_error is not None:
            raise self.mark_error

        return self.mark_result


class RecordingAttachmentService:
    def __init__(
        self,
        *,
        files=None,
        error=None,
    ):
        self.files = (
            list(files)
            if files is not None
            else []
        )
        self.error = error
        self.calls = []

    def download_file_attachments(
        self,
        message_id,
    ):
        self.calls.append(
            message_id
        )

        if self.error is not None:
            raise self.error

        return list(
            self.files
        )


class RecordingDocumentProcessor:
    def __init__(
        self,
        *,
        error=None,
    ):
        self.error = error
        self.calls = []

    def process(
        self,
        file_path,
    ):
        self.calls.append(
            file_path
        )

        if self.error is not None:
            raise self.error

        return object()


def run_test(
    name,
    test_function,
):
    global passed
    global failed

    try:
        test_function()
        passed += 1
        print(
            f"PASSED: {name}"
        )
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def build_processor(
    *,
    email=None,
    attachments=None,
    documents=None,
):
    return MailboxProcessor(
        email_service=(
            email
            or RecordingEmailService()
        ),
        attachment_service=(
            attachments
            or RecordingAttachmentService()
        ),
        document_processor=(
            documents
            or RecordingDocumentProcessor()
        ),
    )


def message(
    *,
    has_attachments,
):
    return {
        "id": "synthetic-message-id",
        "subject": "Synthetic subject",
        "hasAttachments": has_attachments,
    }


def test_no_attachment_is_marked_read():
    email = RecordingEmailService()

    processor = build_processor(
        email=email
    )

    result = processor.process_message(
        message(
            has_attachments=False
        )
    )

    assert result.processed_documents == []
    assert result.errors == []
    assert result.marked_as_read is True

    assert email.mark_calls == [
        "synthetic-message-id"
    ]


def test_unsupported_attachment_is_marked_read():
    email = RecordingEmailService()

    attachments = RecordingAttachmentService(
        files=[
            Path("synthetic.txt")
        ]
    )

    documents = RecordingDocumentProcessor()

    processor = build_processor(
        email=email,
        attachments=attachments,
        documents=documents,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.processed_documents == []

    assert result.skipped_files == [
        Path("synthetic.txt")
    ]

    assert result.errors == []
    assert result.marked_as_read is True
    assert documents.calls == []


def test_empty_download_result_is_marked_read():
    email = RecordingEmailService()

    processor = build_processor(
        email=email,
        attachments=(
            RecordingAttachmentService(
                files=[]
            )
        ),
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.downloaded_files == []
    assert result.processed_documents == []
    assert result.errors == []
    assert result.marked_as_read is True


def test_supported_document_success_is_marked_read():
    email = RecordingEmailService()

    attachments = RecordingAttachmentService(
        files=[
            Path("synthetic.pdf")
        ]
    )

    documents = RecordingDocumentProcessor()

    processor = build_processor(
        email=email,
        attachments=attachments,
        documents=documents,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert len(
        result.processed_documents
    ) == 1

    assert result.succeeded is True
    assert result.marked_as_read is True

    assert documents.calls == [
        Path("synthetic.pdf")
    ]


def test_download_failure_remains_unread():
    email = RecordingEmailService()

    attachments = RecordingAttachmentService(
        error=RuntimeError(
            "Synthetic private download detail"
        )
    )

    processor = build_processor(
        email=email,
        attachments=attachments,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.marked_as_read is False
    assert email.mark_calls == []

    assert result.errors == [
        "Attachment download failed."
    ]

    assert (
        "Synthetic private download detail"
        not in repr(result)
    )


def test_document_failure_remains_unread():
    email = RecordingEmailService()

    attachments = RecordingAttachmentService(
        files=[
            Path("synthetic.pdf")
        ]
    )

    documents = RecordingDocumentProcessor(
        error=RuntimeError(
            "Synthetic private processing detail"
        )
    )

    processor = build_processor(
        email=email,
        attachments=attachments,
        documents=documents,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.marked_as_read is False
    assert email.mark_calls == []

    assert result.errors == [
        "Document processing failed."
    ]

    assert (
        "Synthetic private processing detail"
        not in repr(result)
    )


def test_mixed_success_and_failure_remains_unread():
    email = RecordingEmailService()

    attachments = RecordingAttachmentService(
        files=[
            Path("synthetic.pdf"),
            Path("synthetic.png"),
        ]
    )

    class MixedDocumentProcessor:
        def __init__(self):
            self.call_count = 0

        def process(
            self,
            file_path,
        ):
            self.call_count += 1

            if self.call_count == 2:
                raise RuntimeError(
                    "Synthetic private failure"
                )

            return object()

    processor = build_processor(
        email=email,
        attachments=attachments,
        documents=MixedDocumentProcessor(),
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert len(
        result.processed_documents
    ) == 1

    assert result.succeeded is False
    assert result.marked_as_read is False
    assert email.mark_calls == []

    assert result.errors == [
        "Document processing failed."
    ]


def test_mark_read_failure_is_sanitized():
    email = RecordingEmailService(
        mark_error=RuntimeError(
            "Synthetic private Graph detail"
        )
    )

    processor = build_processor(
        email=email
    )

    result = processor.process_message(
        message(
            has_attachments=False
        )
    )

    assert result.marked_as_read is False

    assert result.errors == [
        "Email could not be marked as read."
    ]

    assert (
        "Synthetic private Graph detail"
        not in repr(result)
    )


def test_missing_message_id_is_not_marked_read():
    email = RecordingEmailService()

    processor = build_processor(
        email=email
    )

    result = processor.process_message(
        {
            "subject": "Synthetic subject",
            "hasAttachments": False,
        }
    )

    assert result.marked_as_read is False
    assert email.mark_calls == []

    assert result.errors == [
        "Message does not contain an ID."
    ]


print("=" * 60)
print("Testing Mailbox Handling")
print("=" * 60)

run_test(
    "no attachment is marked read",
    test_no_attachment_is_marked_read,
)
run_test(
    "unsupported attachment is marked read",
    test_unsupported_attachment_is_marked_read,
)
run_test(
    "empty download result is marked read",
    test_empty_download_result_is_marked_read,
)
run_test(
    "supported document success is marked read",
    test_supported_document_success_is_marked_read,
)
run_test(
    "download failure remains unread",
    test_download_failure_remains_unread,
)
run_test(
    "document failure remains unread",
    test_document_failure_remains_unread,
)
run_test(
    "mixed success and failure remains unread",
    test_mixed_success_and_failure_remains_unread,
)
run_test(
    "mark-read failure is sanitized",
    test_mark_read_failure_is_sanitized,
)
run_test(
    "missing message ID is not marked read",
    test_missing_message_id_is_not_marked_read,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Mock mailbox-boundary test")
print("Microsoft Graph: Mocked")
print("Attachment download: Mocked")
print("Document processing: Mocked")
print("OCR: Not called")
print("Ollama: Not called")
print("Smartsheet: Not called")
print("External integration: Not called")
print(
    "PHI handling: Only synthetic identifiers, "
    "counts, booleans, and sanitized statuses used"
)

if failed:
    raise SystemExit(1)
