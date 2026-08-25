from pathlib import Path

from src.graph.mailbox_processor import (
    MailboxProcessor,
)
from src.services.mailbox_processing_state_service import (
    MailboxProcessingStateResult,
)
import hashlib
from types import SimpleNamespace
from src.graph.attachment_service import (
    SupportedAttachmentCandidateOutcome,
    SupportedAttachmentDownloadResult,
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

    def download_supported_file_attachments(self, message_id, *, supported_extensions):
        files = self.download_file_attachments(message_id)
        supported = [path for path in files if path.suffix.lower() in supported_extensions]
        outcomes = [SupportedAttachmentCandidateOutcome(
            local_path=path,
            document_fingerprint=hashlib.sha256(str(path).encode()).hexdigest(),
            attachment_order_key=hashlib.sha256(("attachment:" + str(path)).encode()).hexdigest(),
            status="downloaded",
        ) for path in supported]
        return SupportedAttachmentDownloadResult(
            downloaded_files=supported,
            candidate_outcomes=outcomes,
            examined_count=len(files),
            skipped_count=len(files) - len(supported),
        )


class RecordingJobStateService:
    def __init__(self):
        self.states = {}

    def message_key(self, message_id):
        return hashlib.sha256(message_id.encode()).hexdigest()

    def discover(self, *, message_key, attachment_key, document_key, attachment_required):
        key = hashlib.sha256((message_key + attachment_key + document_key).encode()).hexdigest()
        state = self.states.setdefault(
            key, SimpleNamespace(job_key=key, stage="discovered", lease_token=None))
        return SimpleNamespace(success=True, state=state)

    def acquire_processing_lease(self, job_key):
        state = self.states[job_key]
        state.stage = "processing"
        state.lease_token = "synthetic-lease"
        return SimpleNamespace(success=True, state=state)

    def transition(self, job_key, **kwargs):
        state = self.states[job_key]
        state.stage = kwargs["stage"]
        state.lease_token = None
        return SimpleNamespace(success=True, state=state)


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


class RecordingProcessingStateService:
    def __init__(
        self,
        *,
        handled=False,
        check_success=True,
        store_success=True,
    ):
        self.handled = handled
        self.check_success = check_success
        self.store_success = store_success
        self.check_calls = []
        self.store_calls = []

    def check(
        self,
        message_id,
    ):
        self.check_calls.append(
            message_id
        )

        if not self.check_success:
            return MailboxProcessingStateResult(
                handled=False,
                stored=False,
                duplicate=False,
                success=False,
                status="state_check_failed",
            )

        return MailboxProcessingStateResult(
            handled=self.handled,
            stored=False,
            duplicate=self.handled,
            success=True,
            status=(
                "already_handled"
                if self.handled
                else "not_handled"
            ),
        )

    def mark_handled(
        self,
        message_id,
    ):
        self.store_calls.append(
            message_id
        )

        if not self.store_success:
            return MailboxProcessingStateResult(
                handled=False,
                stored=False,
                duplicate=False,
                success=False,
                status="state_storage_failed",
            )

        self.handled = True

        return MailboxProcessingStateResult(
            handled=True,
            stored=True,
            duplicate=False,
            success=True,
            status="handled_recorded",
        )


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
    state=None,
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
        processing_state_service=(
            state
            or RecordingProcessingStateService()
        ),
        job_state_service=RecordingJobStateService(),
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


def test_no_attachment_is_recorded_and_marked_read():
    email = RecordingEmailService()
    state = RecordingProcessingStateService()

    processor = build_processor(
        email=email,
        state=state,
    )

    result = processor.process_message(
        message(
            has_attachments=False
        )
    )

    assert result.processed_documents == []
    assert result.errors == []
    assert result.marked_as_read is True

    assert state.store_calls == [
        "synthetic-message-id"
    ]

    assert email.mark_calls == [
        "synthetic-message-id"
    ]


def test_unsupported_attachment_is_recorded_and_marked_read():
    email = RecordingEmailService()
    state = RecordingProcessingStateService()

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
        state=state,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.processed_documents == []

    assert result.skipped_files == []

    assert result.errors == []
    assert result.marked_as_read is True
    assert documents.calls == []

    assert state.store_calls == [
        "synthetic-message-id"
    ]


def test_empty_download_result_is_recorded_and_marked_read():
    email = RecordingEmailService()
    state = RecordingProcessingStateService()

    processor = build_processor(
        email=email,
        attachments=(
            RecordingAttachmentService(
                files=[]
            )
        ),
        state=state,
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

    assert state.store_calls == [
        "synthetic-message-id"
    ]


def test_supported_document_success_waits_for_business_completion():
    email = RecordingEmailService()
    state = RecordingProcessingStateService()

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
        state=state,
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
    assert result.marked_as_read is False

    assert documents.calls == [
        Path("synthetic.pdf")
    ]

    assert state.store_calls == []


def test_already_handled_skips_processing():
    email = RecordingEmailService()

    state = RecordingProcessingStateService(
        handled=True
    )

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
        state=state,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.errors == []
    assert result.processed_documents == []
    assert result.marked_as_read is True
    assert attachments.calls == []
    assert documents.calls == []
    assert state.store_calls == []

    assert email.mark_calls == [
        "synthetic-message-id"
    ]


def test_state_check_failure_blocks_processing():
    email = RecordingEmailService()

    state = RecordingProcessingStateService(
        check_success=False
    )

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
        state=state,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.marked_as_read is False
    assert attachments.calls == []
    assert documents.calls == []
    assert email.mark_calls == []

    assert result.errors == [
        "Mailbox processing state "
        "could not be checked."
    ]


def test_state_storage_failure_remains_unread():
    email = RecordingEmailService()

    state = RecordingProcessingStateService(
        store_success=False
    )

    processor = build_processor(
        email=email,
        state=state,
    )

    result = processor.process_message(
        message(
            has_attachments=False
        )
    )

    assert result.marked_as_read is False
    assert email.mark_calls == []

    assert state.store_calls == [
        "synthetic-message-id"
    ]

    assert result.errors == [
        "Mailbox processing state "
        "could not be stored."
    ]


def test_download_failure_remains_unread():
    email = RecordingEmailService()
    state = RecordingProcessingStateService()

    attachments = RecordingAttachmentService(
        error=RuntimeError(
            "Synthetic private download detail"
        )
    )

    processor = build_processor(
        email=email,
        attachments=attachments,
        state=state,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.marked_as_read is False
    assert email.mark_calls == []
    assert state.store_calls == []

    assert result.errors == [
        "Attachment download failed."
    ]

    assert (
        "Synthetic private download detail"
        not in repr(result)
    )


def test_document_failure_remains_unread():
    email = RecordingEmailService()
    state = RecordingProcessingStateService()

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
        state=state,
    )

    result = processor.process_message(
        message(
            has_attachments=True
        )
    )

    assert result.marked_as_read is False
    assert email.mark_calls == []
    assert state.store_calls == []

    assert result.errors == [
        "Document processing failed."
    ]

    assert (
        "Synthetic private processing detail"
        not in repr(result)
    )


def test_mixed_success_and_failure_remains_unread():
    email = RecordingEmailService()
    state = RecordingProcessingStateService()

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
        state=state,
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
    assert state.store_calls == []

    assert result.errors == [
        "Document processing failed."
    ]


def test_mark_read_failure_keeps_handled_state():
    email = RecordingEmailService(
        mark_error=RuntimeError(
            "Synthetic private Graph detail"
        )
    )

    state = RecordingProcessingStateService()

    processor = build_processor(
        email=email,
        state=state,
    )

    result = processor.process_message(
        message(
            has_attachments=False
        )
    )

    assert result.marked_as_read is False

    assert state.store_calls == [
        "synthetic-message-id"
    ]

    assert state.handled is True

    assert result.errors == [
        "Email could not be marked as read."
    ]

    assert (
        "Synthetic private Graph detail"
        not in repr(result)
    )


def test_missing_message_id_is_not_checked_or_marked():
    email = RecordingEmailService()
    state = RecordingProcessingStateService()

    processor = build_processor(
        email=email,
        state=state,
    )

    result = processor.process_message(
        {
            "subject": "Synthetic subject",
            "hasAttachments": False,
        }
    )

    assert result.marked_as_read is False
    assert email.mark_calls == []
    assert state.check_calls == []
    assert state.store_calls == []

    assert result.errors == [
        "Message does not contain an ID."
    ]


print("=" * 60)
print("Testing Mailbox Handling")
print("=" * 60)

run_test(
    "no attachment is recorded and marked read",
    test_no_attachment_is_recorded_and_marked_read,
)
run_test(
    "unsupported attachment is recorded and marked read",
    test_unsupported_attachment_is_recorded_and_marked_read,
)
run_test(
    "empty download result is recorded and marked read",
    test_empty_download_result_is_recorded_and_marked_read,
)
run_test(
    "supported document success waits for business completion",
    test_supported_document_success_waits_for_business_completion,
)
run_test(
    "already handled message skips processing",
    test_already_handled_skips_processing,
)
run_test(
    "state check failure blocks processing",
    test_state_check_failure_blocks_processing,
)
run_test(
    "state storage failure remains unread",
    test_state_storage_failure_remains_unread,
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
    "mark-read failure keeps handled state",
    test_mark_read_failure_keeps_handled_state,
)
run_test(
    "missing message ID is not checked or marked",
    test_missing_message_id_is_not_checked_or_marked,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Mock mailbox-boundary test")
print("Microsoft Graph: Mocked")
print("Processing state: Mocked")
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
