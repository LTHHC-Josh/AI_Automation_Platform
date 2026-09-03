from dataclasses import fields
from datetime import datetime, timezone
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.smartsheet_feedback_case_storage_service import (
    SmartsheetFeedbackCaseStorageResult,
    SmartsheetFeedbackCaseStorageService,
)
from src.services.smartsheet_feedback_ingestion_service import (
    SmartsheetFeedbackDiscussionResult,
    SmartsheetFeedbackIngestionResult,
    SmartsheetFeedbackIngestionService,
    SmartsheetFeedbackRowReference,
)


passed = 0
failed = 0


class RowReader:
    def __init__(self, rows=(), error=False):
        self.rows = rows
        self.error = error
        self.calls = []

    def read_rows(self, *, checkbox_title, source_scope):
        self.calls.append((checkbox_title, source_scope))
        if self.error:
            raise RuntimeError("protected row-reader detail")
        return self.rows


class DiscussionReader:
    def __init__(self, discussions=None, failures=()):
        self.discussions = discussions or {}
        self.failures = set(failures)
        self.calls = []

    def read_discussions(self, *, row_id):
        self.calls.append(row_id)
        if row_id in self.failures:
            raise RuntimeError("protected discussion detail")
        return self.discussions.get(
            row_id, SmartsheetFeedbackDiscussionResult(comments=())
        )


class RecordingStorage:
    def __init__(self, result=None, raises=False):
        self.result = result or SmartsheetFeedbackCaseStorageResult(
            stored=True, duplicate=False, status="stored"
        )
        self.raises = raises
        self.cases = []

    def store(self, feedback_case):
        self.cases.append(feedback_case)
        if self.raises:
            raise OSError("protected storage detail")
        return self.result


def build_service(
    *, rows=(), discussions=None, storage=None, row_error=False, discussion_failures=(),
    checkbox_title="Configured Flag", source_scope="protected-scope",
):
    row_reader = RowReader(rows=rows, error=row_error)
    discussion_reader = DiscussionReader(
        discussions=discussions, failures=discussion_failures
    )
    case_storage = storage or RecordingStorage()
    service = SmartsheetFeedbackIngestionService(
        row_reader=row_reader,
        discussion_reader=discussion_reader,
        case_storage=case_storage,
        checkbox_title=checkbox_title,
        source_scope=source_scope,
        utc_now=lambda: datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc),
    )
    return service, row_reader, discussion_reader, case_storage


def test_no_flagged_rows():
    service, _, discussions, _ = build_service(
        rows=(SmartsheetFeedbackRowReference(row_id=10, flagged=False),)
    )
    result = service.ingest()
    assert result == SmartsheetFeedbackIngestionResult(
        flagged_row_count=0,
        processed_feedback_case_count=0,
        skipped_count=0,
        success=True,
        status="no_flagged_rows",
        categories=(),
    )
    assert discussions.calls == []


def test_one_flagged_row_with_comments():
    service, _, _, storage = build_service(
        rows=(SmartsheetFeedbackRowReference(row_id=11, flagged=True),),
        discussions={
            11: SmartsheetFeedbackDiscussionResult(
                comments=(" protected feedback ", "   ")
            )
        },
    )
    result = service.ingest()
    assert result.flagged_row_count == 1
    assert result.processed_feedback_case_count == 1
    assert result.status == "completed"
    assert result.categories == ("comments_present",)
    assert storage.cases[0].comments == ("protected feedback",)


def test_multiple_flagged_rows_and_missing_comments():
    rows = tuple(
        SmartsheetFeedbackRowReference(row_id=row_id, flagged=True)
        for row_id in (12, 13)
    )
    service, _, _, _ = build_service(rows=rows)
    result = service.ingest()
    assert result.flagged_row_count == 2
    assert result.processed_feedback_case_count == 2
    assert result.categories == ("comments_missing",)


def test_only_literal_booleans_are_accepted():
    rows = (
        SmartsheetFeedbackRowReference(row_id=14, flagged=True),
        SmartsheetFeedbackRowReference(row_id=15, flagged=False),
        SmartsheetFeedbackRowReference(row_id=16, flagged=1),
        SmartsheetFeedbackRowReference(row_id=17, flagged=None),
    )
    service, _, discussions, _ = build_service(rows=rows)
    result = service.ingest()
    assert result.flagged_row_count == 1
    assert result.skipped_count == 2
    assert result.status == "completed_with_failures"
    assert discussions.calls == [14]


def test_invalid_true_row_is_flagged_and_skipped_without_discussion():
    service, _, discussions, _ = build_service(
        rows=(SmartsheetFeedbackRowReference(row_id=0, flagged=True),)
    )
    result = service.ingest()
    assert result.flagged_row_count == 1
    assert result.skipped_count == 1
    assert result.categories == ("invalid_row_reference",)
    assert discussions.calls == []


def test_invalid_configuration_stops_before_reader():
    service, rows, _, _ = build_service(checkbox_title=" ")
    result = service.ingest()
    assert result.status == "invalid_configuration"
    assert result.success is False
    assert rows.calls == []


def test_row_read_failure_is_sanitized():
    service, _, _, _ = build_service(row_error=True)
    result = service.ingest()
    assert result.status == "row_read_failed"
    assert repr(result).find("protected") == -1


def test_discussion_failure_is_sanitized():
    service, _, _, _ = build_service(
        rows=(SmartsheetFeedbackRowReference(row_id=18, flagged=True),),
        discussion_failures=(18,),
    )
    result = service.ingest()
    assert result.status == "completed_with_failures"
    assert result.categories == ("discussion_read_failed",)


def test_invalid_comments_fail_conservatively():
    service, _, _, storage = build_service(
        rows=(SmartsheetFeedbackRowReference(row_id=19, flagged=True),),
        discussions={19: SmartsheetFeedbackDiscussionResult(comments=(3,))},
    )
    result = service.ingest()
    assert result.categories == ("invalid_comments",)
    assert storage.cases == []


def test_storage_failure_is_sanitized():
    service, _, _, _ = build_service(
        rows=(SmartsheetFeedbackRowReference(row_id=20, flagged=True),),
        storage=RecordingStorage(raises=True),
    )
    result = service.ingest()
    assert result.categories == ("storage_failed",)
    assert result.success is False


def test_duplicate_is_a_successful_skip():
    duplicate = SmartsheetFeedbackCaseStorageResult(
        stored=False, duplicate=True, status="duplicate_feedback_case"
    )
    service, _, _, _ = build_service(
        rows=(SmartsheetFeedbackRowReference(row_id=21, flagged=True),),
        storage=RecordingStorage(result=duplicate),
    )
    result = service.ingest()
    assert result.status == "completed_with_skips"
    assert result.success is True
    assert result.skipped_count == 1


def test_repeat_and_changed_comment_snapshots_are_idempotent():
    with TemporaryDirectory() as directory:
        storage = SmartsheetFeedbackCaseStorageService(
            directory, protect=lambda value: value[::-1]
        )
        rows = (SmartsheetFeedbackRowReference(row_id=22, flagged=True),)
        first, _, _, _ = build_service(
            rows=rows,
            discussions={22: SmartsheetFeedbackDiscussionResult(comments=())},
            storage=storage,
        )
        repeat, _, _, _ = build_service(
            rows=rows,
            discussions={22: SmartsheetFeedbackDiscussionResult(comments=())},
            storage=storage,
        )
        changed, _, _, _ = build_service(
            rows=rows,
            discussions={
                22: SmartsheetFeedbackDiscussionResult(comments=("new feedback",))
            },
            storage=storage,
        )
        assert first.ingest().processed_feedback_case_count == 1
        assert repeat.ingest().categories == ("duplicate_feedback_case",)
        assert changed.ingest().processed_feedback_case_count == 1
        assert storage.count() == 2


def test_comment_order_does_not_change_snapshot():
    storage = RecordingStorage()
    rows = (SmartsheetFeedbackRowReference(row_id=23, flagged=True),)
    first, _, _, _ = build_service(
        rows=rows,
        discussions={
            23: SmartsheetFeedbackDiscussionResult(comments=("alpha", "beta"))
        },
        storage=storage,
    )
    second, _, _, _ = build_service(
        rows=rows,
        discussions={
            23: SmartsheetFeedbackDiscussionResult(comments=("beta", "alpha"))
        },
        storage=storage,
    )
    first.ingest()
    second.ingest()
    assert storage.cases[0].snapshot_digest == storage.cases[1].snapshot_digest


def test_storage_schema_and_filename_are_exact():
    with TemporaryDirectory() as directory:
        storage = SmartsheetFeedbackCaseStorageService(
            directory, protect=lambda value: value[::-1]
        )
        service, _, _, _ = build_service(
            rows=(SmartsheetFeedbackRowReference(row_id=24, flagged=True),),
            storage=storage,
        )
        service.ingest()
        paths = list(Path(directory).glob("*.feedback"))
        sealed = paths[0].read_bytes()
        payload = json.loads(sealed[::-1].decode("utf-8"))
        assert set(payload) == storage.ALLOWED_KEYS
        assert paths[0].name == f"{payload['snapshot_digest']}.feedback"
        assert b"protected-scope" not in sealed
        assert b'"row_id"' not in sealed


def test_protected_objects_have_safe_representations():
    row = SmartsheetFeedbackRowReference(row_id=25, flagged=True)
    discussion = SmartsheetFeedbackDiscussionResult(comments=("secret",))
    assert repr(row).startswith("<")
    assert repr(discussion).startswith("<")
    assert "25" not in repr(row)
    assert "secret" not in repr(discussion)


def test_public_result_has_exact_safe_fields():
    assert tuple(field.name for field in fields(SmartsheetFeedbackIngestionResult)) == (
        "flagged_row_count",
        "processed_feedback_case_count",
        "skipped_count",
        "success",
        "status",
        "categories",
    )


def test_api_has_no_document_or_write_inputs():
    signatures = (
        inspect.signature(SmartsheetFeedbackIngestionService.__init__),
        inspect.signature(SmartsheetFeedbackIngestionService.ingest),
    )
    prohibited = {
        "family", "subtype", "payload", "filename", "source_text",
        "model", "prompt", "mapping", "rule", "write_service", "ocr",
    }
    assert all(
        set(signature.parameters).isdisjoint(prohibited)
        for signature in signatures
    )


def test_source_has_no_production_dependencies():
    source = inspect.getsource(SmartsheetFeedbackIngestionService)
    prohibited = ("Ollama", "Graph", "OCR", "SmartsheetReviewedWrite", "prompt")
    assert all(term not in source for term in prohibited)


def run_test(name, test):
    global passed, failed
    try:
        test()
        passed += 1
        print(f"PASSED: {name}")
    except Exception as error:
        failed += 1
        print(f"FAILED: {name}: {type(error).__name__}")


tests = [
    (name.removeprefix("test_").replace("_", " "), value)
    for name, value in tuple(globals().items())
    if name.startswith("test_") and callable(value)
]

print("=" * 60)
print("Testing Smartsheet Feedback Ingestion")
print("=" * 60)
for test_name, test in tests:
    run_test(test_name, test)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic and mock")
print("External integration: Not called")
print("PHI handling: Protected values stayed in local in-memory or temporary storage")
if failed:
    raise SystemExit(1)
