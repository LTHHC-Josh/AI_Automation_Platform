from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib

from src.graph.attachment_service import (
    SupportedAttachmentCandidateOutcome,
    SupportedAttachmentDownloadResult,
)
from src.graph.mailbox_processor import (
    MailboxProcessor,
)
from src.services.mailbox_processing_state_service import (
    MailboxProcessingStateService,
)
from src.services.mailbox_document_job_state_service import (
    MailboxDocumentJobStateService,
)


passed = 0
failed = 0


class RecordingEmailService:
    def __init__(self):
        self.mark_calls = []

    def mark_as_read(
        self,
        message_id,
    ):
        self.mark_calls.append(
            message_id
        )
        return True


class RecordingAttachmentService:
    def __init__(self):
        self.calls = []

    def download_supported_file_attachments(
        self,
        message_id,
        *,
        supported_extensions,
    ):
        self.calls.append(
            message_id
        )

        file_path = Path("synthetic.pdf")
        return SupportedAttachmentDownloadResult(
            downloaded_files=[file_path],
            candidate_outcomes=[
                SupportedAttachmentCandidateOutcome(
                    local_path=file_path,
                    document_fingerprint=hashlib.sha256(
                        b"synthetic-document"
                    ).hexdigest(),
                    attachment_order_key=hashlib.sha256(
                        b"synthetic-attachment"
                    ).hexdigest(),
                    status="downloaded",
                )
            ],
            examined_count=1,
            skipped_count=0,
        )


class RecordingDocumentProcessor:
    def __init__(self):
        self.calls = []

    def process(
        self,
        file_path,
    ):
        self.calls.append(
            file_path
        )
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


def test_handled_state_survives_new_processor_instance():
    with TemporaryDirectory() as directory:
        state_root = Path(directory)
        message = {
            "id": "synthetic-persistent-message",
            "subject": "Synthetic subject",
            "hasAttachments": True,
        }

        first_email = RecordingEmailService()
        first_attachments = (
            RecordingAttachmentService()
        )
        first_documents = (
            RecordingDocumentProcessor()
        )

        first_processor = MailboxProcessor(
            email_service=first_email,
            attachment_service=first_attachments,
            document_processor=first_documents,
            processing_state_service=(
                MailboxProcessingStateService(
                    state_root / "messages"
                )
            ),
            job_state_service=MailboxDocumentJobStateService(
                state_root / "jobs"
            ),
        )

        first_result = (
            first_processor.process_message(
                message
            )
        )

        assert first_result.succeeded is True
        assert first_result.marked_as_read is False
        assert len(first_result.work_items) == 1
        assert first_email.mark_calls == []

        assert first_attachments.calls == [
            "synthetic-persistent-message"
        ]

        assert first_documents.calls == [
            Path("synthetic.pdf")
        ]

        job_key = first_result.work_items[0].job_key
        first_processor.job_state_service.transition(
            job_key,
            expected_stages={"row_write_pending"},
            stage="row_written",
            smartsheet_row_id=1001,
        )
        first_processor.job_state_service.transition(
            job_key,
            expected_stages={"row_written"},
            stage="attachment_written",
        )
        assert first_processor.complete_message(first_result) is True
        assert first_email.mark_calls == [
            "synthetic-persistent-message"
        ]

        second_email = RecordingEmailService()
        second_attachments = (
            RecordingAttachmentService()
        )
        second_documents = (
            RecordingDocumentProcessor()
        )

        second_processor = MailboxProcessor(
            email_service=second_email,
            attachment_service=second_attachments,
            document_processor=second_documents,
            processing_state_service=(
                MailboxProcessingStateService(
                    state_root / "messages"
                )
            ),
            job_state_service=MailboxDocumentJobStateService(
                state_root / "jobs"
            ),
        )

        second_result = (
            second_processor.process_message(
                message
            )
        )

        assert (
            second_result.processed_documents
            == []
        )

        assert second_result.errors == []
        assert second_result.marked_as_read is True

        assert second_attachments.calls == []
        assert second_documents.calls == []

        assert second_email.mark_calls == [
            "synthetic-persistent-message"
        ]


print("=" * 60)
print("Testing Mailbox Persistent Idempotency")
print("=" * 60)

run_test(
    (
        "handled state survives "
        "new processor instance"
    ),
    (
        test_handled_state_survives_new_processor_instance
    ),
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(
    "Real or mock: "
    "Synthetic deterministic local-state integration"
)
print("Microsoft Graph: Not called")
print("Attachment download: Mocked")
print("Document processing: Mocked")
print("OCR: Not called")
print("Ollama: Not called")
print("Smartsheet: Not called")
print("External integration: Not called")
print(
    "PHI handling: Synthetic identifiers only; "
    "raw message IDs were not persisted"
)

if failed:
    raise SystemExit(1)
