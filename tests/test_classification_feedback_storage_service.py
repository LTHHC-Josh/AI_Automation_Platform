import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.classification_feedback_service import (
    ClassificationFeedback,
)
from src.services.classification_feedback_storage_service import (
    ClassificationFeedbackStorageService,
)


passed = 0
failed = 0

FINGERPRINT_A = "a" * 64
FINGERPRINT_B = "b" * 64


def run_test(
    name,
    test,
):
    global passed
    global failed

    try:
        test()
        passed += 1
        print(
            f"PASSED: {name}"
        )
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def build_feedback(
    fingerprint=FINGERPRINT_A,
):
    return ClassificationFeedback(
        document_fingerprint=fingerprint,
        predicted_category="authorization",
        predicted_subtype="unknown",
        confirmed_category="authorization",
        confirmed_subtype="renewal",
        classification_confidence=0.88,
        correction_required=True,
        reviewer_confirmation_status="corrected",
        created_at="2026-08-06T16:00:00Z",
    )


def build_store(
    directory,
):
    return ClassificationFeedbackStorageService(
        Path(
            directory
        )
        / "feedback.jsonl"
    )


def test_first_record_is_stored():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        result = store.store(
            build_feedback()
        )

        assert result.stored is True
        assert result.duplicate is False
        assert result.record_count == 1
        assert result.status == "stored"
        assert store.count() == 1


def test_duplicate_fingerprint_is_rejected():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        first = store.store(
            build_feedback()
        )
        second = store.store(
            build_feedback()
        )

        assert first.stored is True
        assert second.stored is False
        assert second.duplicate is True
        assert second.record_count == 1
        assert second.status == "duplicate_fingerprint"


def test_different_fingerprint_is_stored():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        store.store(
            build_feedback(
                FINGERPRINT_A
            )
        )

        result = store.store(
            build_feedback(
                FINGERPRINT_B
            )
        )

        assert result.stored is True
        assert result.record_count == 2


def test_contains_fingerprint():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        store.store(
            build_feedback()
        )

        assert store.contains_fingerprint(
            FINGERPRINT_A
        ) is True

        assert store.contains_fingerprint(
            FINGERPRINT_B
        ) is False


def test_invalid_type_is_rejected():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        result = store.store(
            {}
        )

        assert result.stored is False
        assert result.duplicate is False
        assert result.status == "invalid_feedback_type"
        assert result.record_count == 0


def test_jsonl_contains_only_allowed_keys():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        store.store(
            build_feedback()
        )

        payload = json.loads(
            store.storage_path.read_text(
                encoding="utf-8"
            ).strip()
        )

        assert set(
            payload
        ) == store.ALLOWED_KEYS


def test_jsonl_excludes_phi_fields():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        store.store(
            build_feedback()
        )

        serialized = store.storage_path.read_text(
            encoding="utf-8"
        )

        prohibited_terms = {
            "raw_text",
            "source_text",
            "file_path",
            "file_name",
            "patient_name",
            "member_id",
            "authorization_number",
            "email_subject",
            "email_sender",
            "document_bytes",
            "extracted_data",
            "service_lines",
        }

        assert all(
            term not in serialized
            for term in prohibited_terms
        )


def test_service_api_excludes_document_inputs():
    signature = inspect.signature(
        ClassificationFeedbackStorageService.store
    )

    parameter_names = set(
        signature.parameters
    )

    prohibited_parameters = {
        "file_path",
        "document_path",
        "document_bytes",
        "raw_text",
        "source_text",
        "extracted_data",
        "review_output",
    }

    assert parameter_names.isdisjoint(
        prohibited_parameters
    )


def test_missing_file_has_zero_records():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        assert store.count() == 0


def test_blank_lines_are_ignored():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        store.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        store.storage_path.write_text(
            "\n\n",
            encoding="utf-8",
        )

        assert store.count() == 0


def test_invalid_json_lines_are_ignored():
    with TemporaryDirectory() as directory:
        store = build_store(
            directory
        )

        store.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        store.storage_path.write_text(
            "invalid-json\n",
            encoding="utf-8",
        )

        assert store.count() == 0


print("=" * 60)
print("Testing Classification Feedback Storage")
print("=" * 60)

run_test(
    "first record is stored",
    test_first_record_is_stored,
)
run_test(
    "duplicate fingerprint is rejected",
    test_duplicate_fingerprint_is_rejected,
)
run_test(
    "different fingerprint is stored",
    test_different_fingerprint_is_stored,
)
run_test(
    "contains fingerprint",
    test_contains_fingerprint,
)
run_test(
    "invalid type is rejected",
    test_invalid_type_is_rejected,
)
run_test(
    "JSONL contains only allowed keys",
    test_jsonl_contains_only_allowed_keys,
)
run_test(
    "JSONL excludes PHI fields",
    test_jsonl_excludes_phi_fields,
)
run_test(
    "service API excludes document inputs",
    test_service_api_excludes_document_inputs,
)
run_test(
    "missing file has zero records",
    test_missing_file_has_zero_records,
)
run_test(
    "blank lines are ignored",
    test_blank_lines_are_ignored,
)
run_test(
    "invalid JSON lines are ignored",
    test_invalid_json_lines_are_ignored,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic local storage test")
print("External integration: Not called")
print("PHI handling: Only allowlisted feedback metadata was stored")

if failed:
    raise SystemExit(1)
