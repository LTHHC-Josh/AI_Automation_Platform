from pathlib import Path
import tempfile

from src.services.document_attachment_naming_service import (
    DocumentAttachmentNamingService,
)
from src.services.filename_policy_service import FilenamePolicyResult


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


def test_complete_policy_name_is_used_only_for_temporary_copy():
    service = DocumentAttachmentNamingService()
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "synthetic-original.pdf"
        source.write_bytes(b"SYNTHETIC-DOCUMENT")
        policy = FilenamePolicyResult(
            complete=True,
            filename="EXAMPLE SYNTHETIC_PLAN_AUTH INIT_010126.pdf",
            review_required=False,
            status="resolved",
        )
        result = service.prepare(source_path=source, filename_policy_result=policy)
        assert result.success is True
        assert result.status == "prepared_reference_filename"
        assert result.temporary_path.name == policy.filename
        assert "EXAMPLE SYNTHETIC" not in repr(result)
        assert source.exists()
        assert service.cleanup(result.temporary_path) is True


def test_unresolved_policy_preserves_safe_fallback_and_flags_review():
    service = DocumentAttachmentNamingService()
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "synthetic-original.pdf"
        source.write_bytes(b"SYNTHETIC-DOCUMENT")
        policy = FilenamePolicyResult(
            complete=False,
            filename=None,
            review_required=True,
            status="workflow_token_unresolved",
        )
        result = service.prepare(source_path=source, filename_policy_result=policy)
        assert result.success is True
        assert result.status == "prepared_naming_fallback_review"
        assert result.temporary_path.name.startswith("LTHHC_AUTH_TEST_")
        assert service.cleanup(result.temporary_path) is True


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
run_test(
    "complete policy names only temporary copy",
    test_complete_policy_name_is_used_only_for_temporary_copy,
)
run_test(
    "unresolved policy preserves fallback and flags review",
    test_unresolved_policy_preserves_safe_fallback_and_flags_review,
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
