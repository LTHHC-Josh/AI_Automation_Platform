from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from src.ai.ocr.providers.paddle_ocr_provider import PaddleOCRProvider
from src.models.ocr_diagnostics import OCRRunDiagnostics
from src.services.document_fingerprint_service import DocumentFingerprintResult


PROTECTED_MARKER = "PROTECTED_SYNTHETIC_DIAGNOSTIC_MARKER"


class FingerprintService:
    def calculate(self, _source_path):
        return DocumentFingerprintResult(
            fingerprint="a" * 64,
            byte_count=2048,
            success=True,
            status="calculated",
        )


class LazyResults:
    def __init__(self):
        self.iter_count = 0
        self.next_count = 0
        self._items = iter((
            {"rec_texts": ["synthetic first block"]},
            {"rec_texts": ["synthetic second block"]},
        ))

    def __iter__(self):
        self.iter_count += 1
        return self

    def __next__(self):
        self.next_count += 1
        return next(self._items)


class RecordingPaddle:
    def __init__(self, results):
        self.results = results
        self.predict_count = 0

    def predict(self, _source_path):
        self.predict_count += 1
        return self.results


def _provider(cache: Path, paddle=None):
    provider = PaddleOCRProvider.__new__(PaddleOCRProvider)
    provider.CACHE_DIRECTORY = cache
    provider.fingerprint_service = FingerprintService()
    provider.ocr = paddle
    provider.last_run_diagnostics = OCRRunDiagnostics()
    return provider


def test_normal_miss_instruments_one_init_predict_and_one_lazy_consumption():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        cache = root / "cache"
        cache.mkdir()
        source = root / f"{PROTECTED_MARKER}.pdf"
        source.write_bytes(b"synthetic")
        results = LazyResults()
        paddle = RecordingPaddle(results)
        provider = _provider(cache)
        init_count = []

        def create_ocr():
            init_count.append(True)
            return paddle

        provider._create_ocr = create_ocr
        document = provider.extract_document(source)
        safe = provider.last_run_diagnostics.to_safe_dict()

        assert document.page_count == 2
        assert document.raw_text == "synthetic first block\n\nsynthetic second block"
        assert init_count == [True]
        assert paddle.predict_count == 1
        assert results.iter_count == 1
        assert results.next_count == 3
        assert safe["engine_creation_count"] == 1
        assert safe["predict_call_count"] == 1
        assert safe["document_submission_count"] == 1
        assert safe["result_behavior"] == "lazy"
        assert safe["result_count"] == 2
        assert safe["result_conversion_count"] == 2
        assert [item["page_ordinal"] for item in safe["page_timings"]] == [1, 2]
        assert safe["extra_predict_calls_during_cache_writes"] == 0
        assert safe["application_source_rereads_during_cache_writes"] == 0
        assert safe["repeated_prediction_detected"] is False
        assert safe["repeated_conversion_detected"] is False
        assert len(list(cache.glob("*.txt"))) == 1
        assert len(list(cache.glob("*.ocr.json"))) == 1


def test_structured_miss_flat_hit_has_no_paddle_initialization_or_prediction():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        cache = root / "cache"
        cache.mkdir()
        source = root / "synthetic.pdf"
        source.write_bytes(b"synthetic")
        (cache / f"{'a' * 64}.txt").write_text("safe cached text", encoding="utf-8")
        provider = _provider(cache)

        def forbidden_create():
            raise AssertionError("Paddle must not initialize on a flat cache hit")

        provider._create_ocr = forbidden_create
        document = provider.extract_document(source, cache_only=True)
        safe = provider.last_run_diagnostics.to_safe_dict()

        assert document.raw_text == "safe cached text"
        assert safe["cache_category"] == "flat_hit"
        assert safe["engine_creation_count"] == 0
        assert safe["predict_call_count"] == 0


def test_structured_cache_hit_has_no_paddle_initialization_or_prediction():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        cache = root / "cache"
        cache.mkdir()
        source = root / "synthetic.pdf"
        source.write_bytes(b"synthetic")
        import json
        from src.models.ocr_document import OCRBlock, OCRDocument, OCRPage

        cached = OCRDocument(
            pages=(OCRPage(1, (OCRBlock("page_1_block_1", "safe", 1),)),),
            relationship_status="preserved",
        )
        (cache / f"{'a' * 64}.ocr.json").write_text(
            json.dumps(cached.to_protected_cache_dict()), encoding="utf-8"
        )
        provider = _provider(cache)
        document = provider.extract_document(source, cache_only=True)
        safe = provider.last_run_diagnostics.to_safe_dict()

        assert document.raw_text == "safe"
        assert safe["cache_category"] == "structured_hit"
        assert safe["engine_creation_count"] == 0
        assert safe["predict_call_count"] == 0


def test_diagnostics_contract_is_allowlisted_and_phi_safe():
    safe = OCRRunDiagnostics().to_safe_dict()
    rendered = repr(safe)
    expected = set(OCRRunDiagnostics.__dataclass_fields__)

    assert set(safe) == expected
    assert PROTECTED_MARKER not in rendered
    for forbidden in ("path", "filename", "hash", "ocr_text", "source_text", "exception"):
        assert forbidden not in rendered.lower()


def test_repeated_prediction_and_conversion_are_detected_deterministically():
    diagnostics = OCRRunDiagnostics(
        predict_call_count=2,
        document_submission_count=2,
        result_count=2,
        result_conversion_count=3,
    )

    PaddleOCRProvider._update_execution_invariants(diagnostics)

    assert diagnostics.repeated_prediction_detected is True
    assert diagnostics.repeated_conversion_detected is True
