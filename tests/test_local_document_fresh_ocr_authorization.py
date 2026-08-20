import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models.document import Document


PROTECTED_MARKER = "PROTECTED_SYNTHETIC_FRESH_OCR_MARKER"


class FingerprintService:
    def calculate(self, source_path):
        from src.services.document_fingerprint_service import (
            DocumentFingerprintResult,
        )

        import hashlib

        content = Path(source_path).read_bytes()
        return DocumentFingerprintResult(
            fingerprint=hashlib.sha256(content).hexdigest(),
            byte_count=len(content),
            success=True,
            status="calculated",
        )


class RecordingPaddle:
    def __init__(self):
        self.predicted_paths = []

    def predict(self, source_path):
        self.predicted_paths.append(Path(source_path))
        return [{"rec_texts": ["synthetic local OCR text"]}]


class Processor:
    def __init__(self, provider):
        self.provider = provider
        self.calls = []
        self.llm = type(
            "LLM",
            (),
            {"provider": type("Provider", (), {"FIELD_NAMES": ()})()},
        )()

    def process(self, path, *, ocr_cache_only=False):
        self.calls.append((path, ocr_cache_only))
        raw_text = self.provider.extract_text(
            path,
            cache_only=ocr_cache_only,
        )
        return Document(
            file_path=path,
            document_category="other",
            document_subtype="unknown",
            confidence=0.5,
            raw_text=raw_text,
        )


def safe_structural_analysis(*_):
    return {
        "document_structure": {},
        "date_fields": [],
        "authorization_service_structure": {},
        "business_concepts": [],
        "schema_gaps": [],
    }


def test_selected_cache_miss_requires_authorization_then_caches_local_ocr():
    from src.ai.ocr.providers.paddle_ocr_provider import PaddleOCRProvider
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
        unselected = incoming / f"a_{PROTECTED_MARKER}.pdf"
        selected = incoming / f"b_{PROTECTED_MARKER}.pdf"
        unselected.write_bytes(b"unselected synthetic document")
        selected.write_bytes(b"selected synthetic document")

        paddle = RecordingPaddle()
        paddle_initializations = []

        def processor_factory():
            provider = PaddleOCRProvider()
            provider.CACHE_DIRECTORY = cache
            provider.fingerprint_service = FingerprintService()

            def create_paddle():
                paddle_initializations.append(True)
                return paddle

            provider._create_ocr = create_paddle
            return Processor(provider)

        service = LocalDocumentEvaluationService(
            document_directory=incoming,
            processor_factory=processor_factory,
            selection_snapshot_path=root / "selection.json",
            ocr_cache_directory=cache,
            execution_classification=(
                LocalEvaluationExecutionClassification.SYNTHETIC_MOCK
            ),
            learning_analysis_factory=safe_structural_analysis,
        )
        selection = service.select_document(
            type("Selector", (), {"select": lambda self, candidates: 2})()
        )
        assert selection.success is True
        assert selection.selected_index == 2

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            blocked = service.evaluate(
                document_index=2,
                run_type="Synthetic Learning",
                authorize_cached_ocr_access=True,
                authorize_local_ollama=True,
                include_learning_report=True,
            )
            first = service.evaluate(
                document_index=2,
                run_type="Synthetic Learning",
                authorize_cached_ocr_access=True,
                authorize_local_ollama=True,
                authorize_local_ocr=True,
                include_learning_report=True,
            )
            cached = service.evaluate(
                document_index=2,
                run_type="Synthetic Learning",
                authorize_cached_ocr_access=True,
                authorize_local_ollama=True,
                authorize_local_ocr=True,
                include_learning_report=True,
            )

        assert blocked.success is False
        assert blocked.failure_category == "ocr_cache_unavailable"
        assert blocked.learning_report_requested is True
        assert blocked.learning_report_status == "blocked"
        assert blocked.cache_only_enforced is True
        assert first.success is True
        assert first.learning_report_status == "completed"
        assert first.cache_only_enforced is False
        assert cached.success is True
        assert cached.learning_report_status == "completed"
        assert paddle_initializations == [True]
        assert paddle.predicted_paths == [selected]
        assert len(list(cache.glob("*.txt"))) == 1

        rendered = repr(
            [
                blocked.to_safe_dict(),
                first.to_safe_dict(),
                cached.to_safe_dict(),
            ]
        ) + stdout.getvalue() + stderr.getvalue()
        assert PROTECTED_MARKER not in rendered
        assert unselected.name not in rendered
        assert selected.name not in rendered
        assert str(root) not in rendered
        assert "synthetic local OCR text" not in rendered


def test_cli_local_ocr_authorization_is_explicit_opt_in():
    from scripts.evaluate_local_document import build_argument_parser

    parser = build_argument_parser()
    arguments = [
        "--document-index",
        "1",
        "--run-type",
        "Synthetic Learning",
        "--authorize-cached-ocr-access",
        "--authorize-local-ollama",
    ]

    assert parser.parse_args(arguments).authorize_local_ocr is False
    assert parser.parse_args(
        [*arguments, "--authorize-local-ocr"]
    ).authorize_local_ocr is True
