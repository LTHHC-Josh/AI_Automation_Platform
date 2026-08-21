import contextlib
import io
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models.document import (
    AuthorizationServiceLine,
    Document,
)


PROTECTED_MARKER = "PROTECTED_SYNTHETIC_MARKER"
SAFE_RUN_TYPE = "Controlled Local Evaluation"


class RecordingProcessor:
    def __init__(self, document=None, error=None):
        self.document = document
        self.error = error
        self.calls = []

    def process(self, file_path, *, ocr_cache_only=False):
        self.calls.append(
            {
                "file_path": file_path,
                "ocr_cache_only": ocr_cache_only,
            }
        )

        print(PROTECTED_MARKER)
        print(PROTECTED_MARKER, file=sys.stderr)

        if self.error is not None:
            raise self.error

        return self.document


class RecordingProtectedReviewConsumer:
    def __init__(self):
        self.documents = []

    def review(self, document):
        self.documents.append(document)
        print(PROTECTED_MARKER)


def build_document(path: Path) -> Document:
    document = Document(
        file_path=path,
        document_type="authorization",
        document_category="authorization",
        document_subtype="initial",
        classification_reason=PROTECTED_MARKER,
        confidence=0.91,
        raw_text=PROTECTED_MARKER,
    )

    document.extracted_data = {
        "supported_high": PROTECTED_MARKER,
        "supported_low": PROTECTED_MARKER,
        "empty_field": None,
    }

    document.field_confidences = {
        "supported_high": 0.91,
        "supported_low": 0.50,
        "empty_field": 0.0,
    }

    document.field_evidence = {
        "supported_high": {
            "value": PROTECTED_MARKER,
            "confidence": 0.91,
            "source_text": PROTECTED_MARKER,
        }
    }

    document.service_lines = [
        AuthorizationServiceLine(
            service_code=PROTECTED_MARKER,
            confidence=0.91,
            source_text=PROTECTED_MARKER,
        ),
        AuthorizationServiceLine(
            quantity=7,
            confidence=0.50,
            source_text=PROTECTED_MARKER,
        ),
    ]

    document.validation_actions = [
        PROTECTED_MARKER,
        PROTECTED_MARKER,
    ]

    document.rule_actions = [
        PROTECTED_MARKER,
    ]

    document.needs_human_review = True
    document.review_status = "Human Review Required"
    document.review_reasons = [
        PROTECTED_MARKER,
        PROTECTED_MARKER,
        PROTECTED_MARKER,
    ]
    document.minimum_field_confidence = 0.50

    document.processing_metrics = {
        "ocr_wall_seconds": 0.10,
        "classification_wall_seconds": 0.20,
        "extraction_wall_seconds": 0.30,
        "validation_wall_seconds": 0.40,
        "business_rules_wall_seconds": 0.50,
        "human_review_wall_seconds": 0.60,
        "total_wall_seconds": 2.10,
        "extraction_attempt_count": 2,
        "extraction_retry_triggered": True,
        "extraction_selected_attempt": 2,
        "provider_detail": PROTECTED_MARKER,
    }

    document.review_output = {
        "protected": PROTECTED_MARKER,
    }

    return document


def evaluate_with_synthetic_document(
    *,
    protected_review_consumer=None,
):
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
        LocalEvaluationExecutionClassification,
    )

    temporary_directory = TemporaryDirectory()
    root = Path(temporary_directory.name)
    protected_path = root / f"{PROTECTED_MARKER}.pdf"
    protected_path.write_bytes(b"synthetic")

    document = build_document(protected_path)
    processor = RecordingProcessor(document=document)

    service = LocalDocumentEvaluationService(
        document_directory=root,
        processor_factory=lambda: processor,
        selection_snapshot_path=root / "selection.json",
        execution_classification=(
            LocalEvaluationExecutionClassification.SYNTHETIC_MOCK
        ),
        protected_review_consumer=protected_review_consumer,
    )

    stdout = io.StringIO()
    stderr = io.StringIO()

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        result = service.evaluate(
            document_index=1,
            run_type=SAFE_RUN_TYPE,
            authorize_cached_ocr_access=True,
            authorize_local_ollama=True,
        )

    return (
        temporary_directory,
        protected_path,
        processor,
        result,
        stdout.getvalue(),
        stderr.getvalue(),
    )


def test_numeric_selector_is_required_before_document_access():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    factory_calls = []
    service = LocalDocumentEvaluationService(
        document_directory=Path("unused"),
        processor_factory=lambda: factory_calls.append(True),
    )

    result = service.evaluate(
        document_index=None,
        run_type=SAFE_RUN_TYPE,
        authorize_cached_ocr_access=True,
        authorize_local_ollama=True,
    )

    assert result.success is False
    assert result.failure_category == "invalid_document_selector"
    assert factory_calls == []


def test_blank_run_type_is_rejected_before_document_access():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    factory_calls = []
    service = LocalDocumentEvaluationService(
        document_directory=Path("unused"),
        processor_factory=lambda: factory_calls.append(True),
    )

    result = service.evaluate(
        document_index=1,
        run_type="   ",
        authorize_cached_ocr_access=True,
        authorize_local_ollama=True,
    )

    assert result.success is False
    assert result.failure_category == "invalid_run_type"
    assert result.run_type == ""
    assert factory_calls == []


def test_cached_ocr_authorization_is_required():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    service = LocalDocumentEvaluationService(
        document_directory=Path("unused"),
    )

    result = service.evaluate(
        document_index=1,
        run_type=SAFE_RUN_TYPE,
        authorize_cached_ocr_access=False,
        authorize_local_ollama=True,
    )

    assert result.failure_category == "protected_document_access_not_authorized"


def test_local_ollama_authorization_is_required():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    service = LocalDocumentEvaluationService(
        document_directory=Path("unused"),
    )

    result = service.evaluate(
        document_index=1,
        run_type=SAFE_RUN_TYPE,
        authorize_cached_ocr_access=True,
        authorize_local_ollama=False,
    )

    assert result.failure_category == "local_ollama_not_authorized"


def test_processing_uses_cache_only_and_suppresses_nested_output():
    temporary, protected_path, processor, result, stdout, stderr = (
        evaluate_with_synthetic_document()
    )

    try:
        assert result.success is True
        assert processor.calls == [
            {
                "file_path": protected_path,
                "ocr_cache_only": True,
            }
        ]
        assert stdout == ""
        assert stderr == ""
    finally:
        temporary.cleanup()


def test_filename_path_and_protected_values_are_absent_from_result():
    temporary, protected_path, _, result, stdout, stderr = (
        evaluate_with_synthetic_document()
    )

    try:
        rendered = repr(result)
        safe_mapping = result.to_safe_dict()
        serialized = repr(safe_mapping)

        for forbidden in (
            PROTECTED_MARKER,
            str(protected_path),
            protected_path.name,
        ):
            assert forbidden not in rendered
            assert forbidden not in serialized
            assert forbidden not in stdout
            assert forbidden not in stderr

        assert not hasattr(result, "document")
        assert not hasattr(result, "review_output")
        assert not hasattr(result, "document_path")
        assert not hasattr(result, "filename")
        assert not hasattr(result, "fingerprint")
    finally:
        temporary.cleanup()


def test_aggregate_counts_and_review_metadata_are_preserved():
    temporary, _, _, result, _, _ = evaluate_with_synthetic_document()

    try:
        assert result.final_field_count == 2
        assert result.service_line_count == 2
        assert result.low_confidence_field_count == 1
        assert result.low_confidence_service_line_count == 1
        assert result.validation_action_count == 2
        assert result.business_rule_action_count == 1
        assert result.review_required is True
        assert result.review_status == "Human Review Required"
        assert result.review_reason_count == 3
        assert result.minimum_field_confidence == 0.50
        assert result.extraction_attempt_count == 2
        assert result.retry_triggered is True
        assert result.selected_attempt == 2
    finally:
        temporary.cleanup()


def test_only_allowlisted_stage_timings_are_returned():
    temporary, _, _, result, _, _ = evaluate_with_synthetic_document()

    try:
        assert set(result.stage_timings) == {
            "ocr",
            "classification",
            "extraction",
            "validation",
            "business_rules",
            "review",
        }
        assert result.total_timing == 2.10
        assert PROTECTED_MARKER not in repr(result.stage_timings)
    finally:
        temporary.cleanup()


def test_execution_classification_and_suppression_provenance_are_explicit():
    from src.services.local_document_evaluation_service import (
        LocalEvaluationExecutionClassification,
    )

    temporary, _, _, result, _, _ = evaluate_with_synthetic_document()

    try:
        assert result.execution_classification == (
            LocalEvaluationExecutionClassification.SYNTHETIC_MOCK.value
        )
        assert result.cache_only_enforced is True
        assert result.processing_stdout_suppressed is True
        assert result.processing_stderr_suppressed is True
        assert result.protected_values_suppressed is True
        assert result.external_integrations_invoked is False
    finally:
        temporary.cleanup()


def test_raw_provider_exception_is_sanitized_without_context():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
        LocalEvaluationExecutionClassification,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        protected_path = root / f"{PROTECTED_MARKER}.pdf"
        protected_path.write_bytes(b"synthetic")

        raw_error = RuntimeError(PROTECTED_MARKER)
        raw_error.__cause__ = ValueError(PROTECTED_MARKER)
        processor = RecordingProcessor(error=raw_error)

        service = LocalDocumentEvaluationService(
            document_directory=root,
            processor_factory=lambda: processor,
            selection_snapshot_path=root / "selection.json",
            execution_classification=(
                LocalEvaluationExecutionClassification.SYNTHETIC_MOCK
            ),
        )

        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = service.evaluate(
                document_index=1,
                run_type=SAFE_RUN_TYPE,
                authorize_cached_ocr_access=True,
                authorize_local_ollama=True,
            )

        assert result.success is False
        assert result.failure_category == "local_processing_failed"
        assert result.execution_status == "failed"
        assert PROTECTED_MARKER not in repr(result)
        assert PROTECTED_MARKER not in stdout.getvalue()
        assert PROTECTED_MARKER not in stderr.getvalue()


def test_protected_review_handoff_is_in_memory_and_not_in_result():
    consumer = RecordingProtectedReviewConsumer()
    temporary, _, _, result, stdout, stderr = evaluate_with_synthetic_document(
        protected_review_consumer=consumer,
    )

    try:
        assert len(consumer.documents) == 1
        assert consumer.documents[0].raw_text == PROTECTED_MARKER
        assert result.protected_review_handoff_completed is True
        assert result.protected_review_requested is True
        assert result.protected_review_status == "completed"
        assert PROTECTED_MARKER not in repr(result)
        assert stdout == ""
        assert stderr == ""
    finally:
        temporary.cleanup()


def test_no_protected_review_consumer_preserves_existing_operation():
    temporary, _, _, result, _, _ = evaluate_with_synthetic_document()

    try:
        assert result.success is True
        assert result.protected_review_requested is False
        assert result.protected_review_handoff_completed is False
        assert result.protected_review_status == "not_requested"
    finally:
        temporary.cleanup()


def test_protected_review_unavailable_is_sanitized():
    from src.ui.local_protected_review import (
        ProtectedReviewUnavailableError,
    )

    class UnavailableConsumer:
        def review(self, document):
            raise ProtectedReviewUnavailableError(PROTECTED_MARKER)

    temporary, protected_path, _, result, stdout, stderr = (
        evaluate_with_synthetic_document(
            protected_review_consumer=UnavailableConsumer(),
        )
    )

    try:
        assert result.success is False
        assert result.failure_category == "protected_review_unavailable"
        assert result.protected_review_requested is True
        assert result.protected_review_handoff_completed is False
        assert result.protected_review_status == "unavailable"
        assert PROTECTED_MARKER not in repr(result)
        assert str(protected_path) not in repr(result)
        assert stdout == ""
        assert stderr == ""
    finally:
        temporary.cleanup()


def test_protected_review_failure_is_sanitized():
    class FailingConsumer:
        def review(self, document):
            raise RuntimeError(PROTECTED_MARKER)

    temporary, protected_path, _, result, stdout, stderr = (
        evaluate_with_synthetic_document(
            protected_review_consumer=FailingConsumer(),
        )
    )

    try:
        assert result.success is False
        assert result.failure_category == "protected_review_failed"
        assert result.protected_review_requested is True
        assert result.protected_review_handoff_completed is False
        assert result.protected_review_status == "failed"
        assert PROTECTED_MARKER not in repr(result)
        assert str(protected_path) not in repr(result)
        assert stdout == ""
        assert stderr == ""
    finally:
        temporary.cleanup()


def test_service_has_no_external_integration_imports():
    import inspect

    from src.services import local_document_evaluation_service

    source = inspect.getsource(
        local_document_evaluation_service
    ).lower()

    for forbidden_import in (
        "src.graph",
        "smartsheet",
        "mailbox",
    ):
        assert forbidden_import not in source


def test_cli_requires_selector_run_type_and_authorizations():
    from scripts.evaluate_local_document import (
        build_argument_parser,
    )

    parser = build_argument_parser()

    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        try:
            parser.parse_args([])
        except SystemExit as error:
            assert error.code != 0
        else:
            raise AssertionError("Expected required CLI arguments.")


def test_cli_rejects_blank_run_type():
    from scripts.evaluate_local_document import (
        build_argument_parser,
    )

    parser = build_argument_parser()

    with contextlib.redirect_stderr(io.StringIO()):
        try:
            parser.parse_args(
                [
                    "--document-index",
                    "1",
                    "--run-type",
                    "   ",
                    "--authorize-cached-ocr-access",
                    "--authorize-local-ollama",
                ]
            )
        except SystemExit as error:
            assert error.code != 0
        else:
            raise AssertionError("Expected blank Run Type rejection.")


def test_cli_accepts_only_explicit_safe_preflight_values():
    from scripts.evaluate_local_document import (
        build_argument_parser,
    )

    parser = build_argument_parser()
    args = parser.parse_args(
        [
            "--document-index",
            "1",
            "--run-type",
            f"  {SAFE_RUN_TYPE}  ",
            "--authorize-cached-ocr-access",
            "--authorize-local-ollama",
        ]
    )

    assert args.document_index == 1
    assert args.run_type == SAFE_RUN_TYPE
    assert args.authorize_cached_ocr_access is True
    assert args.authorize_local_ollama is True
    assert args.authorize_local_ocr is False


def test_cli_learning_report_is_explicit_opt_in():
    from scripts.evaluate_local_document import build_argument_parser

    parser = build_argument_parser()
    base_arguments = [
        "--document-index",
        "1",
        "--run-type",
        SAFE_RUN_TYPE,
        "--authorize-cached-ocr-access",
        "--authorize-local-ollama",
    ]

    assert parser.parse_args(base_arguments).learning_report is False
    assert parser.parse_args([*base_arguments, "--learning-report"]).learning_report is True


def test_list_documents_is_phi_safe_and_matches_evaluation_selector_order():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
        LocalEvaluationExecutionClassification,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        cache = root / "cache"
        incoming.mkdir()
        cache.mkdir()
        later_name = incoming / f"z_{PROTECTED_MARKER}.png"
        earlier_name = incoming / f"a_{PROTECTED_MARKER}.pdf"
        earlier_name.write_bytes(b"first synthetic document")
        later_name.write_bytes(b"second synthetic document")
        os.utime(earlier_name, ns=(1_000_000_000, 1_000_000_000))
        os.utime(later_name, ns=(2_000_000_000, 2_000_000_000))

        processor = RecordingProcessor(document=build_document(later_name))
        service = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=lambda: processor,
            execution_classification=(
                LocalEvaluationExecutionClassification.SYNTHETIC_MOCK
            ),
            selection_snapshot_path=root / "selection.json",
            ocr_cache_directory=cache,
        )

        listed = service.list_documents()
        rendered = repr(listed.to_safe_dict())
        assert listed.success is True
        assert listed.candidate_count == 2
        assert [item.index for item in listed.documents] == [1, 2]
        expected = service._document_candidates()
        assert [item.file_type for item in listed.documents] == [
            path.suffix.lstrip(".") for path in expected
        ]
        assert [item.relative_order for item in listed.documents] == [
            "newest", "2nd newest"
        ]
        assert all(not item.cached_ocr_available for item in listed.documents)
        assert PROTECTED_MARKER not in rendered
        assert str(root) not in rendered
        assert earlier_name.name not in rendered
        assert later_name.name not in rendered
        assert "fingerprint" not in rendered

        evaluated = service.evaluate(
            document_index=1,
            run_type=SAFE_RUN_TYPE,
            authorize_cached_ocr_access=True,
            authorize_local_ollama=True,
        )
        assert evaluated.success is True
        assert processor.calls[0]["file_path"] == expected[0]


def test_legacy_candidate_order_uses_fingerprint_not_filesystem_metadata():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        oldest = incoming / "a_oldest.pdf"
        tied_second = incoming / "a_tied.pdf"
        tied_third = incoming / "z_tied.pdf"
        newest = incoming / "z_newest.pdf"
        for path in (oldest, tied_second, tied_third, newest):
            path.write_bytes(path.name.encode("utf-8"))
        os.utime(oldest, ns=(1_000_000_000, 1_000_000_000))
        os.utime(tied_second, ns=(2_000_000_000, 2_000_000_000))
        os.utime(tied_third, ns=(2_000_000_000, 2_000_000_000))
        os.utime(newest, ns=(3_000_000_000, 3_000_000_000))
        service = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=lambda: None,
            selection_snapshot_path=root / "selection.json",
            ocr_cache_directory=root / "cache",
        )

        first_order = service._document_candidates()
        os.utime(oldest, ns=(9_000_000_000, 9_000_000_000))
        os.utime(newest, ns=(1, 1))
        assert service._document_candidates() == first_order
        listed = service.list_documents()
        assert [item.relative_order for item in listed.documents] == [
            "newest", "2nd newest", "3rd newest", "4th newest"
        ]


def test_list_selector_evaluation_and_selected_snapshot_share_one_order():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
        LocalEvaluationExecutionClassification,
    )

    class Selector:
        candidates = None

        def select(self, candidates):
            self.candidates = candidates
            return 2

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        older = incoming / f"z_{PROTECTED_MARKER}.pdf"
        newer = incoming / f"a_{PROTECTED_MARKER}.pdf"
        older.write_bytes(b"older")
        newer.write_bytes(b"newer")
        os.utime(older, ns=(1_000_000_000, 1_000_000_000))
        os.utime(newer, ns=(2_000_000_000, 2_000_000_000))
        processor = RecordingProcessor(document=build_document(older))
        selector = Selector()
        snapshot = root / "selection.json"
        service = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=lambda: processor,
            execution_classification=(
                LocalEvaluationExecutionClassification.SYNTHETIC_MOCK
            ),
            selection_snapshot_path=snapshot,
            ocr_cache_directory=root / "cache",
        )

        listed = service.list_documents()
        selected = service.select_document(selector)
        evaluated = service.evaluate(
            document_index=2,
            run_type=SAFE_RUN_TYPE,
            authorize_cached_ocr_access=True,
            authorize_local_ollama=True,
        )

        assert listed.documents[0].relative_order == "newest"
        expected = tuple(enumerate(service._document_candidates(), start=1))
        assert selector.candidates == expected
        assert selected.selected_index == 2
        assert evaluated.success is True
        assert processor.calls[0]["file_path"] == expected[1][1]
        stored = json.loads(snapshot.read_text(encoding="utf-8"))
        assert stored["version"] == 4
        assert stored["selected_index"] == 2
        assert "selected_fingerprint" not in stored
        assert PROTECTED_MARKER not in repr(selected.to_safe_dict())

        mismatched = service.evaluate(
            document_index=1,
            run_type=SAFE_RUN_TYPE,
            authorize_cached_ocr_access=True,
            authorize_local_ollama=True,
        )
        assert mismatched.success is False
        assert mismatched.failure_category == "document_selection_changed"


def test_list_documents_reports_cache_metadata_without_processing():
    import hashlib

    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        cache = root / "cache"
        incoming.mkdir()
        cache.mkdir()
        protected_path = incoming / f"{PROTECTED_MARKER}.pdf"
        content = b"synthetic cache candidate"
        protected_path.write_bytes(content)
        fingerprint = hashlib.sha256(content).hexdigest()
        (cache / f"{fingerprint}.txt").write_text(
            "synthetic cached text",
            encoding="utf-8",
        )
        processor_calls = []
        service = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=lambda: processor_calls.append(True),
            selection_snapshot_path=root / "selection.json",
            ocr_cache_directory=cache,
        )

        result = service.list_documents()

        assert result.success is True
        assert result.documents[0].cached_ocr_available is True
        assert result.documents[0].relative_order == "newest"
        assert processor_calls == []


def test_changed_candidate_order_fails_before_evaluation():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        selected = incoming / "b.pdf"
        selected.write_bytes(b"selected")
        processor_calls = []
        service = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=lambda: processor_calls.append(True),
            selection_snapshot_path=root / "selection.json",
            ocr_cache_directory=root / "cache",
        )
        assert service.list_documents().success is True

        (incoming / "a.pdf").write_bytes(b"new candidate")
        result = service.evaluate(
            document_index=1,
            run_type=SAFE_RUN_TYPE,
            authorize_cached_ocr_access=True,
            authorize_local_ollama=True,
        )

        assert result.success is False
        assert result.failure_category == "document_selection_changed"
        assert processor_calls == []


def test_protected_selector_uses_stable_index_without_processing_or_safe_output():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    class Selector:
        def __init__(self):
            self.candidates = None

        def select(self, candidates):
            self.candidates = candidates
            return 2

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        first = incoming / f"a_{PROTECTED_MARKER}.pdf"
        second = incoming / f"b_{PROTECTED_MARKER}.pdf"
        first.write_bytes(b"first")
        second.write_bytes(b"second")
        os.utime(first, ns=(2_000_000_000, 2_000_000_000))
        os.utime(second, ns=(1_000_000_000, 1_000_000_000))
        processor_calls = []
        selector = Selector()
        service = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=lambda: processor_calls.append(True),
            selection_snapshot_path=root / "selection.json",
            ocr_cache_directory=root / "cache",
        )

        result = service.select_document(selector)

        assert result.success is True
        assert result.selection_status == "selected"
        assert result.selected_index == 2
        assert selector.candidates == tuple(
            enumerate(service._document_candidates(), start=1)
        )
        assert processor_calls == []
        assert PROTECTED_MARKER not in repr(result)
        assert PROTECTED_MARKER not in repr(result.to_safe_dict())
        assert str(first) not in repr(result)
        assert str(second) not in repr(result)


def test_protected_selector_cancellation_does_not_process():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        incoming = root / "incoming"
        incoming.mkdir()
        (incoming / "synthetic.pdf").write_bytes(b"synthetic")
        processor_calls = []
        service = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=lambda: processor_calls.append(True),
            selection_snapshot_path=root / "selection.json",
            ocr_cache_directory=root / "cache",
        )

        result = service.select_document(
            type("Selector", (), {"select": lambda self, candidates: None})()
        )

        assert result.success is False
        assert result.selection_status == "cancelled"
        assert result.selected_index is None
        assert processor_calls == []


def test_cli_list_mode_requires_no_evaluation_arguments_or_processor():
    from unittest.mock import patch

    from scripts import evaluate_local_document

    calls = []

    class SafeListResult:
        success = True

        @staticmethod
        def to_safe_dict():
            return {
                "success": True,
                "failure_category": None,
                "candidate_count": 1,
                "documents": [
                    {
                        "index": 1,
                        "relative_order": "newest",
                        "file_type": "pdf",
                        "cached_ocr_available": True,
                    }
                ],
            }

    class FakeService:
        normalize_run_type = staticmethod(
            evaluate_local_document.LocalDocumentEvaluationService
            .normalize_run_type
        )

        def __init__(self, **arguments):
            calls.append(("constructed", arguments))

        def list_documents(self):
            calls.append(("listed", None))
            return SafeListResult()

        def evaluate(self, **arguments):
            raise AssertionError("Evaluation must not run in list mode.")

    stdout = io.StringIO()
    with patch.object(
        evaluate_local_document,
        "LocalDocumentEvaluationService",
        FakeService,
    ), patch(
        "sys.argv",
        ["evaluate_local_document.py", "--list-documents"],
    ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(
        io.StringIO()
    ):
        evaluate_local_document.main()

    rendered = stdout.getvalue()
    assert calls == [("constructed", {}), ("listed", None)]
    assert PROTECTED_MARKER not in rendered
    assert "Available Documents" in rendered
    assert "Index" in rendered
    assert "Relative Order" in rendered
    assert "Cached OCR" in rendered
    assert "newest" in rendered
    assert "PDF" in rendered
    assert "Yes" in rendered
    assert not rendered.lstrip().startswith("{")


def test_cli_list_json_preserves_structured_safe_output():
    from unittest.mock import patch

    from scripts import evaluate_local_document

    class SafeListResult:
        success = True

        @staticmethod
        def to_safe_dict():
            return {
                "success": True,
                "failure_category": None,
                "candidate_count": 1,
                "documents": [
                    {
                        "index": 1,
                        "relative_order": "newest",
                        "file_type": "pdf",
                        "cached_ocr_available": True,
                    }
                ],
            }

    class FakeService:
        normalize_run_type = staticmethod(
            evaluate_local_document.LocalDocumentEvaluationService
            .normalize_run_type
        )

        def __init__(self, **arguments):
            pass

        def list_documents(self):
            return SafeListResult()

        def evaluate(self, **arguments):
            raise AssertionError("Evaluation must not run in list mode.")

    stdout = io.StringIO()
    with patch.object(
        evaluate_local_document,
        "LocalDocumentEvaluationService",
        FakeService,
    ), patch(
        "sys.argv",
        ["evaluate_local_document.py", "--list-documents", "--json"],
    ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(
        io.StringIO()
    ):
        evaluate_local_document.main()

    parsed = __import__("json").loads(stdout.getvalue())
    assert parsed == SafeListResult.to_safe_dict()
    assert PROTECTED_MARKER not in stdout.getvalue()


def test_cli_learning_report_defaults_to_safe_sectioned_text_and_json_is_exact():
    from unittest.mock import patch

    from scripts import evaluate_local_document

    safe_mapping = {
        "run_type": "Synthetic Learning",
        "success": True,
        "learning_report_status": "completed",
        "learning_report": {
            "document_structure": {
                "document_form_type": "communication_form",
                "page_count": 2,
            },
            "field_inventory": [
                {
                    "field_name": "posted_date",
                    "support_status": "supported",
                    "evidence_available": True,
                }
            ],
            "review_quality": {
                "review_required": True,
                "selected_attempt": 1,
            },
            "protected_values_suppressed": True,
        },
    }

    class SafeEvaluationResult:
        success = True

        @staticmethod
        def to_safe_dict():
            return safe_mapping

    class FakeService:
        normalize_run_type = staticmethod(
            evaluate_local_document.LocalDocumentEvaluationService
            .normalize_run_type
        )

        def __init__(self, **arguments):
            pass

        def evaluate(self, **arguments):
            return SafeEvaluationResult()

    base_arguments = [
        "evaluate_local_document.py",
        "--document-index",
        "1",
        "--run-type",
        "Synthetic Learning",
        "--authorize-cached-ocr-access",
        "--authorize-local-ollama",
        "--learning-report",
    ]

    def run(arguments):
        stdout = io.StringIO()
        with patch.object(
            evaluate_local_document,
            "LocalDocumentEvaluationService",
            FakeService,
        ), patch("sys.argv", arguments), contextlib.redirect_stdout(
            stdout
        ), contextlib.redirect_stderr(io.StringIO()):
            evaluate_local_document.main()
        return stdout.getvalue()

    text_output = run(base_arguments)
    assert "Document Learning Analysis" in text_output
    assert "Evaluation Summary" in text_output
    assert "Learning Report" in text_output
    assert "Document Structure" in text_output
    assert "Field Inventory" in text_output
    assert "Review Quality" in text_output
    assert "posted_date" in text_output
    assert "Support Status: supported" in text_output
    assert PROTECTED_MARKER not in text_output
    assert not text_output.lstrip().startswith("{")

    json_output = run([*base_arguments, "--json"])
    assert __import__("json").loads(json_output) == safe_mapping
    assert PROTECTED_MARKER not in json_output
