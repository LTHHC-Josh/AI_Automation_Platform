from dataclasses import fields
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.document_fingerprint_service import (
    DocumentFingerprintResult,
    DocumentFingerprintService,
)


passed = 0
failed = 0


def run_test(name, test_function):
    global passed
    global failed

    try:
        test_function()
        passed += 1
        print(f"PASSED: {name}")
    except Exception as error:
        failed += 1
        print(f"FAILED: {name}: {type(error).__name__}")


def test_known_content():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.bin"
        content = b"synthetic-document-content"
        path.write_bytes(content)

        result = DocumentFingerprintService().calculate(path)

        assert result.success is True
        assert result.status == "calculated"
        assert result.byte_count == len(content)
        assert result.fingerprint == hashlib.sha256(content).hexdigest()


def test_empty_file():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "empty.bin"
        path.write_bytes(b"")

        result = DocumentFingerprintService().calculate(path)

        assert result.success is True
        assert result.byte_count == 0
        assert result.fingerprint == hashlib.sha256(b"").hexdigest()


def test_file_larger_than_one_chunk():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "large.bin"
        content = b"x" * (DocumentFingerprintService.CHUNK_SIZE + 37)
        path.write_bytes(content)

        result = DocumentFingerprintService().calculate(path)

        assert result.success is True
        assert result.byte_count == len(content)
        assert result.fingerprint == hashlib.sha256(content).hexdigest()


def test_same_content_is_deterministic():
    with TemporaryDirectory() as directory:
        first_path = Path(directory) / "first.bin"
        second_path = Path(directory) / "second.bin"
        content = b"same-content"

        first_path.write_bytes(content)
        second_path.write_bytes(content)

        service = DocumentFingerprintService()
        first = service.calculate(first_path)
        second = service.calculate(second_path)

        assert first.fingerprint == second.fingerprint
        assert first.byte_count == second.byte_count


def test_different_content_changes_fingerprint():
    with TemporaryDirectory() as directory:
        first_path = Path(directory) / "first.bin"
        second_path = Path(directory) / "second.bin"

        first_path.write_bytes(b"first")
        second_path.write_bytes(b"second")

        service = DocumentFingerprintService()
        first = service.calculate(first_path)
        second = service.calculate(second_path)

        assert first.fingerprint != second.fingerprint


def test_missing_file_is_phi_safe():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "sensitive-patient-name.pdf"

        result = DocumentFingerprintService().calculate(path)

        assert result.success is False
        assert result.status == "not_found"
        assert result.fingerprint is None
        assert result.byte_count == 0
        assert "sensitive-patient-name" not in repr(result)


def test_directory_is_rejected():
    with TemporaryDirectory() as directory:
        result = DocumentFingerprintService().calculate(directory)

        assert result.success is False
        assert result.status == "not_a_file"
        assert result.fingerprint is None
        assert result.byte_count == 0


def test_invalid_path_type_is_rejected():
    result = DocumentFingerprintService().calculate(None)

    assert result.success is False
    assert result.status == "invalid_path"
    assert result.fingerprint is None
    assert result.byte_count == 0


def test_result_contract_contains_only_allowed_fields():
    field_names = {field.name for field in fields(DocumentFingerprintResult)}

    assert field_names == {
        "fingerprint",
        "byte_count",
        "success",
        "status",
    }


def test_result_excludes_sensitive_terms():
    result = DocumentFingerprintResult(
        fingerprint="a" * 64,
        byte_count=10,
        success=True,
        status="calculated",
    )

    rendered = repr(result).lower()

    prohibited_terms = {
        "source_path",
        "filename",
        "document_content",
        "ocr_text",
        "source_text",
        "patient",
        "member_id",
        "authorization_number",
    }

    assert all(term not in rendered for term in prohibited_terms)


print("=" * 60)
print("Testing Document Fingerprint Service")
print("=" * 60)

run_test("known content has expected SHA-256", test_known_content)
run_test("empty file is supported", test_empty_file)
run_test("large file is read in chunks", test_file_larger_than_one_chunk)
run_test("same content is deterministic", test_same_content_is_deterministic)
run_test("different content changes fingerprint", test_different_content_changes_fingerprint)
run_test("missing file result is PHI-safe", test_missing_file_is_phi_safe)
run_test("directory is rejected", test_directory_is_rejected)
run_test("invalid path type is rejected", test_invalid_path_type_is_rejected)
run_test("result contains only allowed fields", test_result_contract_contains_only_allowed_fields)
run_test("result excludes sensitive terms", test_result_excludes_sensitive_terms)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic local-file test")
print("External integration: Not called")
print("PHI handling: Synthetic bytes remained local and were not printed")

if failed:
    raise SystemExit(1)
