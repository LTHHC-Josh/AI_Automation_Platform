from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.ai.ocr.providers.paddle_ocr_provider import (
    PaddleOCRProvider,
)
from src.services.document_fingerprint_service import (
    DocumentFingerprintResult,
)


class SuccessfulFingerprintService:
    def __init__(self, fingerprint):
        self.fingerprint = fingerprint

    def calculate(self, source_path):
        return DocumentFingerprintResult(
            fingerprint=self.fingerprint,
            byte_count=9,
            success=True,
            status="calculated",
        )


class RecordingOCR:
    def __init__(self):
        self.call_count = 0

    def predict(self, source_path):
        self.call_count += 1

        return [
            {
                "rec_texts": [
                    "synthetic OCR result",
                ]
            }
        ]


def build_provider(cache_directory, fingerprint, ocr):
    provider = PaddleOCRProvider.__new__(
        PaddleOCRProvider
    )
    provider.CACHE_DIRECTORY = Path(cache_directory)
    provider.fingerprint_service = (
        SuccessfulFingerprintService(
            fingerprint
        )
    )
    provider.ocr = ocr

    return provider


def test_cache_only_hit_returns_cached_text_without_ocr():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")

        fingerprint = "a" * 64
        cache_directory = root / "cache"
        cache_directory.mkdir()
        (cache_directory / f"{fingerprint}.txt").write_text(
            "synthetic cached text",
            encoding="utf-8",
        )

        ocr = RecordingOCR()
        provider = build_provider(
            cache_directory,
            fingerprint,
            ocr,
        )

        result = provider.extract_text(
            source_path,
            cache_only=True,
        )

        assert result == "synthetic cached text"
        assert ocr.call_count == 0


def test_provider_constructor_and_cache_only_hit_do_not_initialize_paddle():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")

        fingerprint = "d" * 64
        cache_directory = root / "cache"
        cache_directory.mkdir()
        (cache_directory / f"{fingerprint}.txt").write_text(
            "synthetic cached text",
            encoding="utf-8",
        )

        with patch(
            "src.ai.ocr.providers.paddle_ocr_provider.PaddleOCR",
            side_effect=AssertionError(
                "Paddle must not initialize for a cache-only hit."
            ),
        ) as paddle_constructor:
            provider = PaddleOCRProvider()
            provider.CACHE_DIRECTORY = cache_directory
            provider.fingerprint_service = SuccessfulFingerprintService(
                fingerprint
            )

            result = provider.extract_text(
                source_path,
                cache_only=True,
            )

        assert result == "synthetic cached text"
        assert paddle_constructor.call_count == 0


def test_cache_only_miss_never_falls_back_to_ocr():
    from src.ai.ocr.errors import (
        OCRCacheOnlyMissError,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")

        fingerprint = "b" * 64
        cache_directory = root / "cache"
        cache_directory.mkdir()
        ocr = RecordingOCR()
        provider = build_provider(
            cache_directory,
            fingerprint,
            ocr,
        )

        try:
            provider.extract_text(
                source_path,
                cache_only=True,
            )
        except OCRCacheOnlyMissError as error:
            assert str(error) == "OCR cache is unavailable."
            assert error.__cause__ is None
            assert error.__context__ is None
        else:
            raise AssertionError(
                "Expected cache-only miss to stop before OCR."
            )

        assert ocr.call_count == 0


def test_provider_constructor_and_cache_only_miss_do_not_initialize_paddle():
    from src.ai.ocr.errors import (
        OCRCacheOnlyMissError,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")

        fingerprint = "e" * 64
        cache_directory = root / "cache"
        cache_directory.mkdir()

        with patch(
            "src.ai.ocr.providers.paddle_ocr_provider.PaddleOCR",
            side_effect=AssertionError(
                "Paddle must not initialize for a cache-only miss."
            ),
        ) as paddle_constructor:
            provider = PaddleOCRProvider()
            provider.CACHE_DIRECTORY = cache_directory
            provider.fingerprint_service = SuccessfulFingerprintService(
                fingerprint
            )

            try:
                provider.extract_text(
                    source_path,
                    cache_only=True,
                )
            except OCRCacheOnlyMissError:
                pass
            else:
                raise AssertionError(
                    "Expected cache-only miss to stop before Paddle."
                )

        assert paddle_constructor.call_count == 0


def test_normal_mode_retains_existing_ocr_fallback():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")

        fingerprint = "c" * 64
        cache_directory = root / "cache"
        cache_directory.mkdir()
        ocr = RecordingOCR()
        provider = build_provider(
            cache_directory,
            fingerprint,
            ocr,
        )

        result = provider.extract_text(
            source_path
        )

        assert result == "synthetic OCR result"
        assert ocr.call_count == 1


def test_normal_cache_miss_initializes_paddle_for_prediction():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")

        fingerprint = "f" * 64
        cache_directory = root / "cache"
        cache_directory.mkdir()
        ocr = RecordingOCR()

        with patch(
            "src.ai.ocr.providers.paddle_ocr_provider.PaddleOCR",
            return_value=ocr,
        ) as paddle_constructor:
            provider = PaddleOCRProvider()
            provider.CACHE_DIRECTORY = cache_directory
            provider.fingerprint_service = SuccessfulFingerprintService(
                fingerprint
            )

            result = provider.extract_text(
                source_path
            )

        assert result == "synthetic OCR result"
        assert paddle_constructor.call_count == 1
        assert ocr.call_count == 1


def test_document_processor_cache_only_flag_is_opt_in():
    import inspect

    from src.document_processing.document_processor import (
        DocumentProcessor,
    )

    signature = inspect.signature(
        DocumentProcessor.process
    )

    assert "ocr_cache_only" in signature.parameters
    assert signature.parameters[
        "ocr_cache_only"
    ].default is False


def test_document_processor_forwards_explicit_cache_only_mode():
    from src.document_processing.document_processor import (
        DocumentProcessor,
    )

    class StopAfterOCR(Exception):
        pass

    class RecordingOCRService:
        def __init__(self):
            self.cache_only = None

        def extract_text(self, file_path, *, cache_only=False):
            self.cache_only = cache_only
            raise StopAfterOCR()

    with TemporaryDirectory() as directory:
        source_path = Path(directory) / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")
        processor = DocumentProcessor.__new__(
            DocumentProcessor
        )
        processor.ocr = RecordingOCRService()

        try:
            processor.process(
                source_path,
                ocr_cache_only=True,
            )
        except StopAfterOCR:
            pass
        else:
            raise AssertionError(
                "Expected synthetic stop after OCR call."
            )

        assert processor.ocr.cache_only is True


def test_document_processor_default_keeps_legacy_ocr_call_shape():
    from src.document_processing.document_processor import (
        DocumentProcessor,
    )

    class StopAfterOCR(Exception):
        pass

    class LegacyOCRService:
        def __init__(self):
            self.call_count = 0

        def extract_text(self, file_path):
            self.call_count += 1
            raise StopAfterOCR()

    with TemporaryDirectory() as directory:
        source_path = Path(directory) / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")
        processor = DocumentProcessor.__new__(
            DocumentProcessor
        )
        processor.ocr = LegacyOCRService()

        try:
            processor.process(
                source_path
            )
        except StopAfterOCR:
            pass
        else:
            raise AssertionError(
                "Expected synthetic stop after OCR call."
            )

        assert processor.ocr.call_count == 1
