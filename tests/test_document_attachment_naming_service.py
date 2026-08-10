from pathlib import Path
import tempfile

from src.services.document_attachment_naming_service import (
    DocumentAttachmentNamingService,
)


passed = 0
failed = 0


def run_test(name, test):
    global passed
    global failed

    try:
        test()
        passed += 1
        print(f"PASSED: {name}")
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def test_temporary_copy_uses_test_convention():
    service = DocumentAttachmentNamingService()

    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "private-source.pdf"
        source.write_bytes(b"SYNTHETIC-DOCUMENT")

        result = service.prepare(
            source_path=source
        )

        assert result.success is True
        assert result.prepared is True
        assert result.temporary_path is not None
        assert result.temporary_path.exists()

        assert (
            result.temporary_path.name.startswith(
                "LTHHC_AUTH_TEST_"
            )
        )

        assert (
            result.temporary_path.suffix
            == ".pdf"
        )

        assert source.exists()

        assert service.cleanup(
            result.temporary_path
        ) is True


def test_missing_source_is_blocked():
    service = DocumentAttachmentNamingService()

    result = service.prepare(
        source_path="missing-synthetic.pdf"
    )

    assert result.success is False
    assert result.prepared is False
    assert result.temporary_path is None


print("=" * 60)
print("Testing Document Attachment Naming")
print("=" * 60)

run_test(
    "temporary copy uses test convention",
    test_temporary_copy_uses_test_convention,
)

run_test(
    "missing source is blocked",
    test_missing_source_is_blocked,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic local-file test")
print("Smartsheet external API: Not called")
print("Microsoft Graph: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("PHI handling: Synthetic file bytes only; paths not printed")

if failed:
    raise SystemExit(1)
