import base64
import contextlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.local_document_source_recency_service import (
    LocalDocumentSourceRecencyService,
)


PROTECTED_MARKER = "PROTECTED_SYNTHETIC_REFRESH_MARKER"


def build_attachment_service(directory: Path, attachments):
    from src.graph.attachment_service import AttachmentService

    service = AttachmentService.__new__(AttachmentService)
    service.download_dir = directory
    service.get_attachments = lambda message_id: list(attachments)
    return service


def test_refresh_downloads_only_supported_non_inline_attachments():
    from src.services.local_document_inbox_refresh_service import (
        LocalDocumentInboxRefreshService,
    )

    class Email:
        def __init__(self):
            self.calls = []

        def get_recent_attachment_messages(self, *, top):
            self.calls.append(top)
            return [
                {
                    "id": PROTECTED_MARKER,
                    "subject": PROTECTED_MARKER,
                    "hasAttachments": True,
                }
            ]

        def mark_as_read(self, message_id):
            raise AssertionError("Refresh must not mutate mailbox state.")

    with TemporaryDirectory() as directory:
        incoming = Path(directory)
        protected_filename = f"{PROTECTED_MARKER}.pdf"
        attachments = [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "isInline": False,
                "name": protected_filename,
                "contentBytes": base64.b64encode(b"supported").decode(),
            },
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "isInline": False,
                "name": f"{PROTECTED_MARKER}.txt",
                "contentBytes": base64.b64encode(b"unsupported").decode(),
            },
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "isInline": True,
                "name": f"{PROTECTED_MARKER}.png",
                "contentBytes": base64.b64encode(b"inline").decode(),
            },
        ]
        email = Email()
        attachment = build_attachment_service(incoming, attachments)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = LocalDocumentInboxRefreshService(
                email_service_factory=lambda: email,
                attachment_service_factory=lambda: attachment,
            ).refresh(top=5, supported_extensions={".pdf", ".png"})

        assert result.success is True
        assert result.status == "completed"
        assert result.messages_checked == 1
        assert result.attachments_examined == 3
        assert result.attachments_downloaded == 1
        assert result.attachments_skipped == 2
        assert email.calls == [5]
        assert [path.suffix for path in incoming.iterdir()] == [".pdf"]
        assert PROTECTED_MARKER not in repr(result)
        assert PROTECTED_MARKER not in repr(result.to_safe_dict())
        assert PROTECTED_MARKER not in stdout.getvalue()
        assert PROTECTED_MARKER not in stderr.getvalue()


def test_refresh_skips_existing_filename_without_overwrite_or_rename():
    from src.services.local_document_inbox_refresh_service import (
        LocalDocumentInboxRefreshService,
    )

    class Email:
        def get_recent_attachment_messages(self, *, top):
            return [{"id": "synthetic", "hasAttachments": True}]

    with TemporaryDirectory() as directory:
        incoming = Path(directory)
        existing = incoming / "synthetic.pdf"
        existing.write_bytes(b"existing")
        attachment = build_attachment_service(
            incoming,
            [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "isInline": False,
                    "name": "synthetic.pdf",
                    "contentBytes": base64.b64encode(b"different").decode(),
                }
            ],
        )

        result = LocalDocumentInboxRefreshService(
            email_service_factory=Email,
            attachment_service_factory=lambda: attachment,
        ).refresh(top=1, supported_extensions={".pdf"})

        assert result.success is True
        assert result.attachments_downloaded == 0
        assert result.attachments_skipped == 1
        assert result.filename_collisions == 1
        assert existing.read_bytes() == b"existing"
        assert list(incoming.iterdir()) == [existing]


def test_refreshed_candidate_reaches_selector_without_processing():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )
    from src.services.local_document_inbox_refresh_service import (
        LocalDocumentInboxRefreshService,
    )

    class Email:
        def get_recent_attachment_messages(self, *, top):
            return [
                {
                    "id": "synthetic",
                    "receivedDateTime": "2026-01-03T00:00:00Z",
                    "hasAttachments": True,
                }
            ]

    class Selector:
        candidates = None

        def select(self, candidates):
            self.candidates = candidates
            return 1

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        older = incoming / "z_older.pdf"
        older.write_bytes(b"older")
        os.utime(older, ns=(1_000_000_000, 1_000_000_000))
        attachment = build_attachment_service(
            incoming,
            [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "isInline": False,
                    "name": f"{PROTECTED_MARKER}.pdf",
                    "contentBytes": base64.b64encode(b"new").decode(),
                }
            ],
        )
        refresh_service = LocalDocumentInboxRefreshService(
            email_service_factory=Email,
            attachment_service_factory=lambda: attachment,
            source_recency_service=LocalDocumentSourceRecencyService(
                root / "recency.json"
            ),
        )
        refreshed = refresh_service.refresh(
            top=1,
            supported_extensions={".pdf"},
        )
        repeated = refresh_service.refresh(
            top=1,
            supported_extensions={".pdf"},
        )
        processor_calls = []
        selector = Selector()
        selected = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=lambda: processor_calls.append(True),
            selection_snapshot_path=root / "selection.json",
            ocr_cache_directory=root / "cache",
            source_recency_service=refresh_service._source_recency_service,
        ).select_document(selector)

        assert refreshed.attachments_downloaded == 1
        assert repeated.attachments_downloaded == 0
        assert repeated.filename_collisions == 1
        assert selected.success is True
        assert selected.selected_index == 1
        assert len(selector.candidates) == 2
        assert selector.candidates[0][1].read_bytes() == b"new"
        assert selector.candidates[1][1] == older
        assert processor_calls == []
        assert PROTECTED_MARKER not in repr(selected)


def test_refresh_service_has_no_mailbox_mutation_or_processing_dependencies():
    import inspect

    from src.services import local_document_inbox_refresh_service

    source = inspect.getsource(local_document_inbox_refresh_service).lower()
    for forbidden in (
        "mark_as_read",
        "mark_handled",
        "mailboxprocessingstateservice",
        "documentprocessor",
        "ollama",
        "smartsheet",
    ):
        assert forbidden not in source


def test_cli_refreshes_before_selector_and_emits_safe_counts_only():
    from dataclasses import dataclass
    from unittest.mock import patch

    from scripts import evaluate_local_document

    events = []

    @dataclass
    class RefreshResult:
        success: bool = True
        status: str = "completed"

        def to_safe_dict(self):
            return {
                "success": True,
                "status": "completed",
                "messages_checked": 2,
                "messages_with_attachments": 1,
                "attachments_examined": 1,
                "attachments_downloaded": 1,
                "attachments_skipped": 0,
                "filename_collisions": 0,
            }

    class RefreshService:
        MAX_TOP = 25

        def refresh(self, **arguments):
            events.append(("refresh", arguments["top"]))
            return RefreshResult()

    class Selection:
        success = True
        selection_status = "selected"
        selected_index = 1

        @staticmethod
        def to_safe_dict():
            return {
                "success": True,
                "selection_status": "selected",
                "selected_index": 1,
            }

    class Evaluation:
        success = True

        @staticmethod
        def to_safe_dict():
            return {"success": True, "learning_report": {}}

    class EvaluationService:
        SUPPORTED_EXTENSIONS = {".pdf"}
        normalize_run_type = staticmethod(
            evaluate_local_document.LocalDocumentEvaluationService
            .normalize_run_type
        )

        def __init__(self, **arguments):
            pass

        def select_document(self, selector):
            events.append(("select", None))
            return Selection()

        def evaluate(self, **arguments):
            events.append(("evaluate", arguments["document_index"]))
            return Evaluation()

    arguments = [
        "evaluate_local_document.py",
        "--refresh-top",
        "2",
        "--select-document",
        "--run-type",
        "Synthetic Learning",
        "--authorize-cached-ocr-access",
        "--authorize-local-ollama",
        "--learning-report",
    ]
    stdout = io.StringIO()
    stderr = io.StringIO()

    with patch.object(
        evaluate_local_document,
        "LocalDocumentInboxRefreshService",
        RefreshService,
    ), patch.object(
        evaluate_local_document,
        "LocalDocumentEvaluationService",
        EvaluationService,
    ), patch.object(
        evaluate_local_document,
        "LocalProtectedDocumentSelector",
        return_value=object(),
    ), patch("sys.argv", arguments), contextlib.redirect_stdout(
        stdout
    ), contextlib.redirect_stderr(stderr):
        evaluate_local_document.main()

    assert events == [("refresh", 2), ("select", None), ("evaluate", 1)]
    rendered = stdout.getvalue() + stderr.getvalue()
    assert "Messages Checked: 2" in rendered
    assert "Attachments Downloaded: 1" in rendered
    assert PROTECTED_MARKER not in rendered
