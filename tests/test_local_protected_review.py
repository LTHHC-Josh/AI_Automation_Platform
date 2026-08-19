import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models.document import (
    AuthorizationServiceLine,
    Document,
)
from src.services.review_output_service import (
    ReviewOutputService,
)


PROTECTED_MARKER = "PROTECTED_SYNTHETIC_REVIEW_MARKER"


class RecordingView:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def show(self, *, model, open_document):
        self.calls.append(
            {
                "model": model,
                "open_document": open_document,
            }
        )

        if self.error is not None:
            raise self.error


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
        "synthetic_field": PROTECTED_MARKER,
        "missing_field": None,
    }
    document.field_confidences = {
        "synthetic_field": 0.91,
        "missing_field": 0.0,
    }
    document.field_evidence = {
        "synthetic_field": {
            "value": PROTECTED_MARKER,
            "confidence": 0.91,
            "source_text": PROTECTED_MARKER,
        },
        "missing_field": {
            "value": None,
            "confidence": 0.0,
            "source_text": "",
        },
    }
    document.service_lines = [
        AuthorizationServiceLine(
            service_code=PROTECTED_MARKER,
            modifier=PROTECTED_MARKER,
            quantity=3,
            start_date=PROTECTED_MARKER,
            end_date=PROTECTED_MARKER,
            status=PROTECTED_MARKER,
            confidence=0.83,
            source_text=PROTECTED_MARKER,
        )
    ]
    document.validation_actions = [PROTECTED_MARKER]
    document.rule_actions = [PROTECTED_MARKER]
    document.needs_human_review = True
    document.review_status = "Human Review Required"
    document.review_reasons = [PROTECTED_MARKER]
    document.minimum_field_confidence = 0.83
    document.review_output = ReviewOutputService().build(document)
    return document


def test_review_model_keeps_protected_values_in_memory_only():
    from src.ui.local_protected_review import (
        LocalProtectedReviewConsumer,
    )

    with TemporaryDirectory() as directory:
        protected_path = Path(directory) / f"{PROTECTED_MARKER}.pdf"
        protected_path.write_bytes(b"synthetic")
        document = build_document(protected_path)
        view = RecordingView()
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            LocalProtectedReviewConsumer(
                view_factory=lambda: view,
            ).review(document)

        assert len(view.calls) == 1
        model = view.calls[0]["model"]
        assert model.source_path == protected_path
        assert model.review_output.fields[0].value == PROTECTED_MARKER
        assert model.review_output.fields[0].source_text == PROTECTED_MARKER
        assert model.review_output.service_lines[0].service_code == PROTECTED_MARKER
        assert model.review_output.validation_actions == [PROTECTED_MARKER]
        assert model.review_output.rule_actions == [PROTECTED_MARKER]
        assert model.review_output.review_reasons == [PROTECTED_MARKER]
        assert PROTECTED_MARKER not in repr(model)
        assert str(protected_path) not in repr(model)
        assert stdout.getvalue() == ""
        assert stderr.getvalue() == ""


def test_open_action_uses_existing_source_without_copy_or_path_output():
    from src.ui.local_protected_review import (
        LocalProtectedReviewConsumer,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        protected_path = root / f"{PROTECTED_MARKER}.pdf"
        protected_path.write_bytes(b"synthetic")
        before = sorted(path.name for path in root.iterdir())
        opened = []
        view = RecordingView()

        consumer = LocalProtectedReviewConsumer(
            view_factory=lambda: view,
            document_opener=lambda path: opened.append(path),
        )
        consumer.review(build_document(protected_path))
        view.calls[0]["open_document"]()

        assert opened == [protected_path]
        assert sorted(path.name for path in root.iterdir()) == before


def test_review_is_synchronous_and_has_open_and_done_actions():
    from src.ui.local_protected_review import (
        LocalProtectedReviewConsumer,
    )

    events = []

    class SynchronousView:
        def show(self, *, model, open_document):
            events.append("shown")

    with TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.pdf"
        path.write_bytes(b"synthetic")
        consumer = LocalProtectedReviewConsumer(
            view_factory=SynchronousView,
        )
        consumer.review(build_document(path))
        events.append("returned")

    assert events == ["shown", "returned"]

    import inspect

    from src.ui import local_protected_review

    source = inspect.getsource(local_protected_review)
    assert "Open selected document" in source
    assert "Done" in source


def test_consumer_has_no_output_persistence_or_clipboard_operations():
    import inspect

    from src.ui import local_protected_review

    source = inspect.getsource(local_protected_review).lower()

    for forbidden in (
        "print(",
        "logging",
        "clipboard",
        "write_text",
        "write_bytes",
        "namedtemporaryfile",
        "mkstemp",
        "smartsheet",
        "src.graph",
        "mailbox",
    ):
        assert forbidden not in source


def test_unavailable_view_raises_safe_category_without_raw_context():
    from src.ui.local_protected_review import (
        LocalProtectedReviewConsumer,
        ProtectedReviewUnavailableError,
    )

    raw_error = RuntimeError(PROTECTED_MARKER)

    def unavailable_factory():
        raise raw_error

    with TemporaryDirectory() as directory:
        path = Path(directory) / f"{PROTECTED_MARKER}.pdf"
        path.write_bytes(b"synthetic")

        try:
            LocalProtectedReviewConsumer(
                view_factory=unavailable_factory,
            ).review(build_document(path))
        except ProtectedReviewUnavailableError as error:
            assert str(error) == "protected_review_unavailable"
            assert error.__cause__ is None
            assert error.__context__ is None
            assert PROTECTED_MARKER not in repr(error)
        else:
            raise AssertionError("Expected protected review unavailable error.")


def test_view_failure_raises_safe_category_without_raw_context():
    from src.ui.local_protected_review import (
        LocalProtectedReviewConsumer,
        ProtectedReviewFailedError,
    )

    with TemporaryDirectory() as directory:
        path = Path(directory) / f"{PROTECTED_MARKER}.pdf"
        path.write_bytes(b"synthetic")

        try:
            LocalProtectedReviewConsumer(
                view_factory=lambda: RecordingView(
                    RuntimeError(PROTECTED_MARKER)
                ),
            ).review(build_document(path))
        except ProtectedReviewFailedError as error:
            assert str(error) == "protected_review_failed"
            assert error.__cause__ is None
            assert error.__context__ is None
            assert PROTECTED_MARKER not in repr(error)
        else:
            raise AssertionError("Expected protected review failed error.")


def test_cli_protected_review_is_explicit_opt_in():
    from scripts.evaluate_local_document import build_argument_parser

    parser = build_argument_parser()
    base_arguments = [
        "--document-index",
        "1",
        "--run-type",
        "Synthetic Review",
        "--authorize-cached-ocr-access",
        "--authorize-local-ollama",
    ]

    assert parser.parse_args(base_arguments).protected_review is False
    assert parser.parse_args(
        [*base_arguments, "--protected-review"]
    ).protected_review is True


def test_cli_opt_in_wires_consumer_without_exposing_protected_data():
    from unittest.mock import patch

    from scripts import evaluate_local_document

    consumer = object()
    captured = {}

    class FakeResult:
        success = True

        def to_safe_dict(self):
            return {
                "success": True,
                "protected_review_requested": True,
                "protected_review_status": "completed",
            }

    class FakeService:
        normalize_run_type = staticmethod(
            evaluate_local_document.LocalDocumentEvaluationService
            .normalize_run_type
        )

        def __init__(self, *, protected_review_consumer=None):
            captured["consumer"] = protected_review_consumer

        def evaluate(self, **arguments):
            captured["arguments"] = arguments
            return FakeResult()

    arguments = [
        "evaluate_local_document.py",
        "--document-index",
        "1",
        "--run-type",
        "Synthetic Review",
        "--authorize-cached-ocr-access",
        "--authorize-local-ollama",
        "--protected-review",
    ]
    stdout = io.StringIO()
    stderr = io.StringIO()

    with patch.object(
        evaluate_local_document,
        "LocalProtectedReviewConsumer",
        return_value=consumer,
    ), patch.object(
        evaluate_local_document,
        "LocalDocumentEvaluationService",
        FakeService,
    ), patch("sys.argv", arguments), contextlib.redirect_stdout(
        stdout
    ), contextlib.redirect_stderr(stderr):
        evaluate_local_document.main()

    assert captured["consumer"] is consumer
    assert captured["arguments"]["document_index"] == 1
    assert "protected_review" not in captured["arguments"]
    assert PROTECTED_MARKER not in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_tkinter_dependency_is_standard_library_and_lazy():
    import inspect

    from src.ui import local_protected_review

    source = inspect.getsource(local_protected_review)
    assert "import tkinter" in source
    assert "def _load_tkinter" in source
