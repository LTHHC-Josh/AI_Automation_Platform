from concurrent.futures import ThreadPoolExecutor
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


def build_feedback():
    return ClassificationFeedback(
        document_fingerprint=FINGERPRINT_A,
        predicted_category="authorization",
        predicted_subtype="unknown",
        confirmed_category="authorization",
        confirmed_subtype="renewal",
        classification_confidence=0.88,
        correction_required=True,
        reviewer_confirmation_status="corrected",
        created_at="2026-08-06T16:00:00Z",
    )


def submit(
    storage_path,
):
    service = ClassificationFeedbackStorageService(
        storage_path
    )

    return service.store(
        build_feedback()
    )


def test_concurrent_duplicate_submission_stores_once():
    with TemporaryDirectory() as directory:
        storage_path = (
            Path(
                directory
            )
            / "feedback.jsonl"
        )

        with ThreadPoolExecutor(
            max_workers=8
        ) as executor:
            results = list(
                executor.map(
                    lambda _: submit(
                        storage_path
                    ),
                    range(
                        16
                    ),
                )
            )

        stored_results = [
            result
            for result in results
            if result.stored
        ]

        duplicate_results = [
            result
            for result in results
            if result.duplicate
        ]

        assert len(
            stored_results
        ) == 1

        assert len(
            duplicate_results
        ) == 15

        service = ClassificationFeedbackStorageService(
            storage_path
        )

        assert service.count() == 1


def test_concurrent_file_contains_one_valid_json_record():
    with TemporaryDirectory() as directory:
        storage_path = (
            Path(
                directory
            )
            / "feedback.jsonl"
        )

        with ThreadPoolExecutor(
            max_workers=8
        ) as executor:
            list(
                executor.map(
                    lambda _: submit(
                        storage_path
                    ),
                    range(
                        16
                    ),
                )
            )

        lines = [
            line
            for line in storage_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        assert len(
            lines
        ) == 1

        payload = json.loads(
            lines[0]
        )

        assert payload[
            "document_fingerprint"
        ] == FINGERPRINT_A


def test_lock_directory_is_removed_after_success():
    with TemporaryDirectory() as directory:
        storage_path = (
            Path(
                directory
            )
            / "feedback.jsonl"
        )

        service = ClassificationFeedbackStorageService(
            storage_path
        )

        result = service.store(
            build_feedback()
        )

        assert result.stored is True
        assert service.lock_path.exists() is False


def test_lock_directory_is_removed_after_duplicate():
    with TemporaryDirectory() as directory:
        storage_path = (
            Path(
                directory
            )
            / "feedback.jsonl"
        )

        service = ClassificationFeedbackStorageService(
            storage_path
        )

        service.store(
            build_feedback()
        )

        result = service.store(
            build_feedback()
        )

        assert result.duplicate is True
        assert service.lock_path.exists() is False


print("=" * 60)
print("Testing Classification Feedback Storage Locking")
print("=" * 60)

run_test(
    "concurrent duplicate submission stores once",
    test_concurrent_duplicate_submission_stores_once,
)
run_test(
    "concurrent file has one valid JSON record",
    test_concurrent_file_contains_one_valid_json_record,
)
run_test(
    "lock directory removed after success",
    test_lock_directory_is_removed_after_success,
)
run_test(
    "lock directory removed after duplicate",
    test_lock_directory_is_removed_after_duplicate,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(
    "Real or mock: Synthetic concurrent local storage test"
)
print("External integration: Not called")
print(
    "PHI handling: Only allowlisted feedback metadata was stored"
)

if failed:
    raise SystemExit(1)
