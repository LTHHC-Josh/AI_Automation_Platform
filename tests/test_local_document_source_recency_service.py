import base64
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.graph.attachment_service import AttachmentService
from src.services.local_document_evaluation_service import LocalDocumentEvaluationService
from src.services.local_document_inbox_refresh_service import LocalDocumentInboxRefreshService
from src.services.local_document_source_recency_service import LocalDocumentSourceRecencyService


def fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def record(service, path, content, received, message, attachment):
    assert service.record(
        local_path=path,
        document_fingerprint=fingerprint(content),
        received_datetime=received,
        message_id=message,
        attachment_order_key=hashlib.sha256(attachment.encode()).hexdigest(),
        status="downloaded",
    )


def evaluator(root, recency):
    return LocalDocumentEvaluationService(
        document_directory=root / "incoming",
        processor_factory=lambda: None,
        selection_snapshot_path=root / "selection.json",
        ocr_cache_directory=root / "cache",
        source_recency_service=recency,
    )


def test_graph_recency_controls_shared_order_and_ignores_filesystem_metadata():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        paths = [incoming / "z.pdf", incoming / "a.pdf", incoming / "m.pdf"]
        contents = [b"legacy", b"newest", b"second"]
        for path, content in zip(paths, contents):
            path.write_bytes(content)
        os.utime(paths[1], ns=(1, 1))
        os.utime(paths[2], ns=(9_000_000_000, 9_000_000_000))
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        record(recency, paths[1], b"newest", "2026-01-03T00:00:00Z", "message-new", "a")
        record(recency, paths[2], b"second", "2026-01-02T00:00:00Z", "message-old", "b")
        service = evaluator(root, recency)
        ordered = service._document_candidates()
        assert ordered == [paths[1], paths[2], paths[0]]
        assert [item.index for item in service.list_documents().documents] == [1, 2, 3]


def test_equal_message_time_and_same_message_attachments_are_deterministic():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        contents = [b"one", b"two", b"three"]
        paths = [incoming / f"{index}.pdf" for index in range(3)]
        for path, content in zip(paths, contents):
            path.write_bytes(content)
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        for path, content, message, attachment in (
            (paths[0], b"one", "same", "z"),
            (paths[1], b"two", "same", "a"),
            (paths[2], b"three", "other", "q"),
        ):
            record(
                recency,
                path,
                content,
                "2026-01-03T00:00:00Z",
                message,
                attachment,
            )
        first = evaluator(root, recency)._document_candidates()
        second = evaluator(root, recency)._document_candidates()
        assert first == second


def test_identical_collision_promotes_but_different_collision_does_not_claim():
    class Email:
        received = "2026-01-03T00:00:00Z"
        def get_recent_attachment_messages(self, *, top):
            return [{"id": "message", "receivedDateTime": self.received, "hasAttachments": True}]

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        target = incoming / "candidate.pdf"
        target.write_bytes(b"same")
        attachment = AttachmentService.__new__(AttachmentService)
        attachment.download_dir = incoming
        attachment.get_attachments = lambda message_id: [{
            "id": "attachment", "@odata.type": "#microsoft.graph.fileAttachment",
            "isInline": False, "name": target.name,
            "contentBytes": base64.b64encode(b"same").decode(),
        }]
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        refresh = LocalDocumentInboxRefreshService(
            email_service_factory=Email,
            attachment_service_factory=lambda: attachment,
            source_recency_service=recency,
        )
        assert refresh.refresh(top=1, supported_extensions={".pdf"}).success
        assert recency.ordering_key(target, fingerprint(b"same")) is not None
        attachment.get_attachments = lambda message_id: [{
            "id": "other", "@odata.type": "#microsoft.graph.fileAttachment",
            "isInline": False, "name": target.name,
            "contentBytes": base64.b64encode(b"different").decode(),
        }]
        assert refresh.refresh(top=1, supported_extensions={".pdf"}).success
        assert recency.ordering_key(target, fingerprint(b"different")) is None
        assert target.read_bytes() == b"same"


def test_malformed_registry_is_ignored_and_failed_atomic_write_preserves_prior():
    with TemporaryDirectory() as directory:
        registry = Path(directory) / "state.json"
        registry.write_text('{"version":1,"records":{"bad":{}}}', encoding="utf-8")
        service = LocalDocumentSourceRecencyService(registry)
        assert service.ordering_key(Path(directory) / "candidate.pdf", "0" * 64) is None
        original = registry.read_bytes()
        with patch("src.services.local_document_source_recency_service.os.replace", side_effect=OSError):
            assert not service.record(
                local_path=Path(directory) / "candidate.pdf",
                document_fingerprint="0" * 64,
                received_datetime="2026-01-01T00:00:00Z",
                message_id="message",
                attachment_order_key="1" * 64,
                status="downloaded",
            )
        assert registry.read_bytes() == original


def test_recency_change_invalidates_snapshot_and_safe_results_do_not_leak_metadata():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        first = incoming / "first.pdf"
        second = incoming / "second.pdf"
        first.write_bytes(b"first")
        second.write_bytes(b"second")
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        record(recency, first, b"first", "2026-01-02T00:00:00Z", "secret-message", "a")
        service = evaluator(root, recency)
        listed = service.list_documents()
        record(recency, second, b"second", "2026-01-03T00:00:00Z", "other-secret", "b")
        selected, changed = service._select_document(1)
        assert selected is None and changed is True
        rendered = repr(listed.to_safe_dict())
        assert "2026-" not in rendered and "secret" not in rendered
        assert str(root) not in rendered and "fingerprint" not in rendered


def test_duplicate_bytes_remain_separate_and_resolve_exact_selected_path():
    class Selector:
        candidates = None

        def select(self, candidates):
            self.candidates = candidates
            return 2

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        first = incoming / "first.pdf"
        second = incoming / "second.pdf"
        first.write_bytes(b"identical")
        second.write_bytes(b"identical")
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        service = evaluator(root, recency)
        selector = Selector()

        selected = service.select_document(selector)
        resolved, changed = service._select_document(2)

        assert selected.success is True
        assert len(selector.candidates) == 2
        assert selector.candidates[0][1] != selector.candidates[1][1]
        assert resolved == selector.candidates[1][1]
        assert changed is False


def test_duplicate_bytes_have_independent_authoritative_recency():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        older = incoming / "older.pdf"
        newer = incoming / "newer.pdf"
        legacy = incoming / "legacy.pdf"
        for path in (older, newer, legacy):
            path.write_bytes(b"identical")
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        record(
            recency,
            older,
            b"identical",
            "2026-01-02T00:00:00Z",
            "older-message",
            "a",
        )
        record(
            recency,
            newer,
            b"identical",
            "2026-01-03T00:00:00Z",
            "newer-message",
            "b",
        )
        service = evaluator(root, recency)

        first = service._document_candidates()
        os.utime(legacy, ns=(9_000_000_000, 9_000_000_000))
        second = service._document_candidates()

        assert first == [newer, older, legacy]
        assert second == first


def test_same_candidate_keeps_newest_graph_occurrence_deterministically():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        candidate = root / "candidate.pdf"
        candidate.write_bytes(b"same")
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        record(
            recency,
            candidate,
            b"same",
            "2026-01-03T00:00:00Z",
            "newer-message",
            "a",
        )
        newest_key = recency.ordering_key(candidate, fingerprint(b"same"))
        record(
            recency,
            candidate,
            b"same",
            "2026-01-02T00:00:00Z",
            "older-message",
            "b",
        )

        assert recency.ordering_key(candidate, fingerprint(b"same")) == newest_key


def test_duplicate_byte_replacement_and_candidate_change_invalidate_snapshot():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        first = incoming / "first.pdf"
        second = incoming / "second.pdf"
        first.write_bytes(b"identical")
        second.write_bytes(b"identical")
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        service = evaluator(root, recency)
        assert service.list_documents().success is True

        second.write_bytes(b"replacement")
        resolved, changed = service._select_document(1)

        assert resolved is None
        assert changed is True


def test_snapshot_contains_only_protected_internal_candidate_identity():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        candidate = incoming / "protected-marker.pdf"
        candidate.write_bytes(b"synthetic")
        recency = LocalDocumentSourceRecencyService(root / "state.json")
        service = evaluator(root, recency)
        assert service.list_documents().success is True

        stored = json.loads((root / "selection.json").read_text(encoding="utf-8"))
        rendered = json.dumps(stored, sort_keys=True)

        assert stored["version"] == 4
        assert "candidate_identity" in stored["candidates"][0]
        assert candidate.name not in rendered
        assert str(root) not in rendered
