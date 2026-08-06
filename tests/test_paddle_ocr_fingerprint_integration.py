from pathlib import Path
from tempfile import TemporaryDirectory

from src.ai.ocr.providers.paddle_ocr_provider import (
    PaddleOCRProvider,
)
from src.services.document_fingerprint_service import (
    DocumentFingerprintResult,
)


passed = 0
failed = 0


class SuccessfulFingerprintService:
    def __init__(self, fingerprint):
        self.fingerprint = fingerprint
        self.call_count = 0

    def calculate(self, source_path):
        self.call_count += 1

        return DocumentFingerprintResult(
            fingerprint=self.fingerprint,
            byte_count=9,
            success=True,
            status="calculated",
        )


class FailedFingerprintService:
    def calculate(self, source_path):
        return DocumentFingerprintResult(
            fingerprint=None,
            byte_count=0,
            success=False,
            status="read_failed",
        )


class UnexpectedOCR:
    def predict(self, source_path):
        raise AssertionError(
            "OCR prediction should not run on a cache hit."
        )


def run_test(name, test_function):
    global passed
    global failed

    try:
        test_function()
        passed += 1
        print(f"PASSED: {name}")
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def build_provider(cache_directory, fingerprint_service):
    provider = PaddleOCRProvider.__new__(
        PaddleOCRProvider
    )

    provider.CACHE_DIRECTORY = Path(
        cache_directory
    )

    provider.fingerprint_service = (
        fingerprint_service
    )

    provider.ocr = UnexpectedOCR()

    return provider


def test_shared_fingerprint_service_drives_cache_lookup():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.pdf"
        source_path.write_bytes(b"synthetic")

        fingerprint = "a" * 64
        cache_directory = root / "cache"
        cache_directory.mkdir()

        cache_path = (
            cache_directory
            / f"{fingerprint}.txt"
        )

        cache_path.write_text(
            "synthetic cached text",
            encoding="utf-8",
        )

        fingerprint_service = (
            SuccessfulFingerprintService(
                fingerprint
            )
        )

        provider = build_provider(
            cache_directory,
            fingerprint_service,
        )

        result = provider.extract_text(
            source_path
        )

        assert result == "synthetic cached text"
        assert fingerprint_service.call_count == 1


def test_fingerprint_failure_is_sanitized():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = (
            root
            / "sensitive-patient-name.pdf"
        )

        source_path.write_bytes(
            b"synthetic"
        )

        cache_directory = root / "cache"
        cache_directory.mkdir()

        provider = build_provider(
            cache_directory,
            FailedFingerprintService(),
        )

        try:
            provider.extract_text(
                source_path
            )
        except RuntimeError as error:
            rendered = str(error)

            assert (
                "sensitive-patient-name"
                not in rendered
            )

            assert (
                str(source_path)
                not in rendered
            )

            assert rendered == (
                "The local document could not be read "
                "for OCR processing."
            )
        else:
            raise AssertionError(
                "Expected sanitized RuntimeError."
            )


def test_provider_no_longer_defines_private_hash_method():
    assert not hasattr(
        PaddleOCRProvider,
        "_calculate_file_hash",
    )


print("=" * 60)
print("Testing PaddleOCR Fingerprint Integration")
print("=" * 60)

run_test(
    "shared service drives cache lookup",
    test_shared_fingerprint_service_drives_cache_lookup,
)
run_test(
    "fingerprint failure is sanitized",
    test_fingerprint_failure_is_sanitized,
)
run_test(
    "private hash method was removed",
    test_provider_no_longer_defines_private_hash_method,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic integration test")
print("OCR prediction: Not called")
print("External integration: Not called")
print("PHI handling: Synthetic content only; paths were not printed")

if failed:
    raise SystemExit(1)
