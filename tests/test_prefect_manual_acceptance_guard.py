from pathlib import Path
from types import SimpleNamespace

from src.graph.attachment_service import (
    AttachmentService,
    SupportedAttachmentCandidateOutcome,
    SupportedAttachmentCountResult,
    SupportedAttachmentDownloadResult,
)
from src.graph.mailbox_processor import (
    MailboxAcceptanceGuardError,
    MailboxProcessor,
)


class SyntheticEmail:
    def __init__(self, message_count):
        self.messages = [
            {"id": f"synthetic-{index}", "subject": "synthetic", "hasAttachments": True}
            for index in range(message_count)
        ]
        self.requested_top = None

    def get_unread_messages(self, top=10):
        self.requested_top = top
        return self.messages[:top]


class SyntheticAttachments:
    def __init__(self, count):
        self.count = count
        self.download_calls = 0

    def count_supported_file_attachments(self, message_id, *, supported_extensions):
        if self.count is None:
            return SupportedAttachmentCountResult(count=None, success=False)
        return SupportedAttachmentCountResult(count=self.count, success=True)

    def download_supported_file_attachments(self, message_id, *, supported_extensions):
        self.download_calls += 1
        outcomes = [
            SupportedAttachmentCandidateOutcome(
                local_path=Path(f"synthetic-{index}.pdf"),
                document_fingerprint=str(index) * 64,
                attachment_order_key=str(index + 1) * 64,
                status="downloaded",
            )
            for index in range(self.count or 0)
        ]
        return SupportedAttachmentDownloadResult(
            downloaded_files=[item.local_path for item in outcomes],
            candidate_outcomes=outcomes,
            examined_count=len(outcomes),
        )


class SyntheticDocuments:
    def __init__(self):
        self.calls = 0

    def process(self, file_path, *, stage_observer=None):
        self.calls += 1
        return object()


class SyntheticState:
    def check(self, message_id):
        return SimpleNamespace(success=True, handled=False)


class SyntheticJobs:
    def message_key(self, message_id):
        return "a" * 64

    def discover(self, **kwargs):
        return SimpleNamespace(success=True, state=SimpleNamespace(
            job_key="b" * 64, stage="discovered", lease_token=None))

    def acquire_processing_lease(self, job_key):
        return SimpleNamespace(success=True, state=SimpleNamespace(lease_token="safe"))

    def transition(self, job_key, **kwargs):
        return SimpleNamespace(success=True)


def build_processor(message_count, document_count):
    email = SyntheticEmail(message_count)
    attachments = SyntheticAttachments(document_count)
    documents = SyntheticDocuments()
    processor = MailboxProcessor(
        email_service=email,
        attachment_service=attachments,
        document_processor=documents,
        processing_state_service=SyntheticState(),
        job_state_service=SyntheticJobs(),
    )
    return processor, email, attachments, documents


def run_guarded(processor, observer=None):
    return processor.process_unread_messages(
        top=1,
        acceptance_max_messages=1,
        acceptance_max_documents=1,
        stage_observer=observer,
    )


def test_one_message_one_document_passes_and_processes_once():
    processor, email, attachments, documents = build_processor(1, 1)
    assert len(run_guarded(processor)) == 1
    assert email.requested_top == 2
    assert attachments.download_calls == 1
    assert documents.calls == 1


def test_guard_blocks_before_download_ocr_ollama_or_smartsheet():
    cases = [
        (1, 2, "acceptance_document_limit_exceeded"),
        (2, 1, "acceptance_message_limit_exceeded"),
        (1, None, "acceptance_count_unproven"),
    ]
    for message_count, document_count, category in cases:
        processor, email, attachments, documents = build_processor(
            message_count, document_count)
        try:
            run_guarded(processor)
        except MailboxAcceptanceGuardError as error:
            assert error.category == category
        else:
            raise AssertionError("Expected the acceptance guard to block.")
        assert email.requested_top == 2
        assert attachments.download_calls == 0
        assert documents.calls == 0


def test_stage_observability_is_allowlisted_and_contains_no_protected_content():
    processor, _, _, _ = build_processor(1, 1)
    events = []
    run_guarded(processor, lambda **event: events.append(event))
    rendered = repr(events)
    assert "mailbox_discovery" in rendered
    assert "acceptance_guard" in rendered
    assert "attachment_download" in rendered
    for protected in (
        "synthetic-0", "subject", "filename", "source_text", "row_id",
        "submission_key", "provider", "patient",
    ):
        assert protected not in rendered


def test_document_count_uses_metadata_only_and_fails_closed_on_invalid_shape():
    calls = []

    class MetadataClient:
        def get(self, endpoint, *, params, operation_category):
            calls.append((params, operation_category))
            return {"value": [
                {"@odata.type": "#microsoft.graph.fileAttachment",
                 "isInline": False, "name": "synthetic.pdf", "id": "safe"},
            ]}

    service = AttachmentService.__new__(AttachmentService)
    service.client = MetadataClient()
    service.config = SimpleNamespace(mailbox="configured-mailbox")
    result = service.count_supported_file_attachments(
        "synthetic-message", supported_extensions={".pdf"})
    assert result.success is True and result.count == 1
    assert calls == [(
        {"$select": "id,name,isInline,@odata.type"}, "attachment_enumeration")]
    assert "contentBytes" not in repr(calls)

    service.client.get = lambda *args, **kwargs: {"value": "unproven"}
    result = service.count_supported_file_attachments(
        "synthetic-message", supported_extensions={".pdf"})
    assert result.success is False and result.count is None


if __name__ == "__main__":
    tests = [value for name, value in globals().copy().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic and mock")
    print("External integrations: not called")
    print("PHI handling: aggregate counts and allowlisted stage metadata only")
