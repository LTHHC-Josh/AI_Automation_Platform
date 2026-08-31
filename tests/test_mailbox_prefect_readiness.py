import ast
import contextlib
from dataclasses import fields
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from prefect.logging import disable_run_logger

import src.orchestration.prefect_mailbox_workflow as prefect_adapter
from src.graph.mailbox_processor import MessageProcessingResult
from src.orchestration.prefect_mailbox_workflow import (
    PREFECT_MAILBOX_RUN_TYPE,
    SanitizedMailboxRunError,
    bounded_mailbox_flow,
    run_bounded_mailbox_application,
)
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetResult,
)
from src.services.mailbox_document_job_state_service import (
    MailboxDocumentJobStateService,
)
from src.services.mailbox_full_review_orchestration_service import (
    MailboxClassificationReviewMode,
    MailboxFullReviewOrchestrationResult,
    MailboxFullReviewOrchestrationService,
)
from src.services.mailbox_review_session_service import MailboxReviewSessionResult
from src.services.review_output_service import ReviewOutput
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)


ROOT = Path(__file__).resolve().parent.parent


def digest(character):
    return character * 64


def discover(service, suffix="a"):
    return service.discover(
        message_key=digest(suffix),
        attachment_key=digest("b"),
        document_key=digest("c"),
        attachment_required=True,
    ).state


def build_result(**overrides):
    values = {
        "message_count": 1,
        "document_count": 1,
        "classification_submitted_count": 0,
        "classification_cancelled_count": 0,
        "approved_count": 0,
        "written_count": 1,
        "rejected_count": 0,
        "complete_review_cancelled_count": 0,
        "failed_count": 0,
        "success": True,
        "status": "completed",
        "stage": "completed",
        "failure_category": None,
        "retryable": False,
        "row_attempt_count": 1,
        "attachment_attempt_count": 1,
        "pending_document_count": 0,
        "completed_document_count": 1,
    }
    values.update(overrides)
    return MailboxFullReviewOrchestrationResult(**values)


class RecordingMailbox:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def process_unread_messages(self, top=10):
        self.calls.append(top)
        return self.results


class RecordingComplete:
    def __init__(self, result):
        self.result = result

    def run(self, *, message_results, run_type=""):
        return self.result


class RecordingReview:
    def __init__(self):
        self.calls = []

    def run(self, *, message_results, created_at=None):
        self.calls.append(message_results)
        return MailboxReviewSessionResult(
            message_count=len(message_results),
            document_count=1,
            submitted_count=1,
            cancelled_count=0,
            failed_count=0,
            success=True,
            status="completed",
        )


def complete_result(*, documents=1, success=True, status="completed"):
    return MailboxCompleteReviewSmartsheetResult(
        message_count=1,
        document_count=documents,
        approved_count=0,
        written_count=documents if success else 0,
        rejected_count=0,
        cancelled_count=0,
        failed_count=0 if success else 1,
        success=success,
        status=status,
    )


def test_durable_batch_summary_is_fail_closed_and_aggregate_only():
    with TemporaryDirectory() as directory:
        service = MailboxDocumentJobStateService(directory)
        completed = discover(service, "a")
        lease = service.acquire_processing_lease(completed.job_key).state
        service.transition(
            completed.job_key,
            expected_stages={"processing"},
            stage="row_write_pending",
            lease_token=lease.lease_token,
        )
        service.transition(
            completed.job_key,
            expected_stages={"row_write_pending"},
            stage="row_written",
            smartsheet_row_id=1001,
            increment_row_attempt=True,
        )
        service.transition(
            completed.job_key,
            expected_stages={"row_written"},
            stage="attachment_written",
            increment_attachment_attempt=True,
        )
        pending = discover(service, "d")
        service.transition(
            pending.job_key,
            expected_stages={"discovered"},
            stage="row_written",
            smartsheet_row_id=1002,
        )

        summary = service.summarize([completed.job_key, pending.job_key])
        assert summary.completed_document_count == 1
        assert summary.pending_document_count == 1
        assert summary.row_attempt_count == 1
        assert summary.attachment_attempt_count == 1
        assert summary.failure_category == "work_pending"
        assert summary.retryable is True
        assert digest("a") not in repr(summary)


def test_uncertain_blocked_row_pending_and_corrupt_states_are_not_retryable():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        service = MailboxDocumentJobStateService(root)

        row_pending = discover(service, "a")
        lease = service.acquire_processing_lease(row_pending.job_key).state
        service.transition(
            row_pending.job_key,
            expected_stages={"processing"},
            stage="row_write_pending",
            lease_token=lease.lease_token,
        )
        assert service.summarize([row_pending.job_key]).retryable is False

        uncertain = discover(service, "d")
        lease = service.acquire_processing_lease(uncertain.job_key).state
        service.transition(
            uncertain.job_key,
            expected_stages={"processing"},
            stage="row_write_uncertain",
            lease_token=lease.lease_token,
            failure_category="row_write_outcome_unknown",
            retryable=False,
        )
        uncertain_summary = service.summarize([uncertain.job_key])
        assert uncertain_summary.retryable is False
        assert uncertain_summary.failure_category == "row_write_outcome_unknown"

        attachment_uncertain = discover(service, "1")
        service.transition(
            attachment_uncertain.job_key,
            expected_stages={"discovered"},
            stage="row_written",
            smartsheet_row_id=1003,
        )
        service.transition(
            attachment_uncertain.job_key,
            expected_stages={"row_written"},
            stage="attachment_write_uncertain",
            failure_category="attachment_write_outcome_unknown",
            retryable=False,
        )
        attachment_summary = service.summarize([attachment_uncertain.job_key])
        assert attachment_summary.retryable is False
        assert attachment_summary.failure_category == "attachment_write_outcome_unknown"

        blocked = discover(service, "e")
        service.transition(
            blocked.job_key,
            expected_stages={"discovered"},
            stage="blocked_permanent",
            failure_category="duplicate_row_conflict",
            retryable=False,
        )
        assert service.summarize([blocked.job_key]).retryable is False

        corrupt = discover(service, "f")
        (root / f"{corrupt.job_key}.json").write_text("{", encoding="utf-8")
        corrupt_summary = service.summarize([corrupt.job_key])
        assert corrupt_summary.retryable is False
        assert corrupt_summary.pending_document_count is None
        assert corrupt_summary.row_attempt_count is None
        assert corrupt_summary.failure_category == "state_corrupt"

        inconsistent = discover(service, "2")
        inconsistent_path = root / f"{inconsistent.job_key}.json"
        payload = json.loads(inconsistent_path.read_text(encoding="utf-8"))
        payload["stage"] = "not_a_stage"
        inconsistent_path.write_text(json.dumps(payload), encoding="utf-8")
        inconsistent_summary = service.summarize([inconsistent.job_key])
        assert inconsistent_summary.retryable is False
        assert inconsistent_summary.failure_category == "state_inconsistent"


def test_downstream_mode_is_explicit_and_interactive_mode_is_compatible():
    message = MessageProcessingResult("PRIVATE-SYNTHETIC-ID", "PRIVATE-SYNTHETIC")
    message.processed_documents = [object()]
    review = RecordingReview()
    service = MailboxFullReviewOrchestrationService(
        mailbox_processor=RecordingMailbox([message]),
        classification_review_session=review,
        complete_review_smartsheet_service=RecordingComplete(complete_result()),
    )
    downstream = service.run(
        review_mode=MailboxClassificationReviewMode.DOWNSTREAM,
        run_type="Synthetic downstream mode",
    )
    assert downstream.success is True
    assert review.calls == []

    interactive = service.run(
        review_mode=MailboxClassificationReviewMode.INTERACTIVE,
        run_type="Synthetic interactive mode",
    )
    assert interactive.success is True
    assert len(review.calls) == 1


def test_invalid_mode_and_mailbox_item_errors_fail_closed():
    mailbox = RecordingMailbox([])
    service = MailboxFullReviewOrchestrationService(
        mailbox_processor=mailbox,
        classification_review_session=RecordingReview(),
        complete_review_smartsheet_service=RecordingComplete(
            complete_result(documents=0, status="no_documents")
        ),
    )
    invalid = service.run(review_mode="downstream")
    assert invalid.status == "invalid_review_mode"
    assert invalid.retryable is False
    assert mailbox.calls == []

    failed_message = MessageProcessingResult("PRIVATE-ID", "PRIVATE-SUBJECT")
    failed_message.errors.append("Synthetic sanitized failure.")
    service.mailbox_processor = RecordingMailbox([failed_message])
    failed = service.run()
    assert failed.success is False
    assert failed.status == "mailbox_items_failed"
    assert failed.failure_category == "mailbox_item_failed"
    assert failed.retryable is False


def test_run_type_contract_accepts_and_preserves_adapter_purpose():
    mapping = SmartsheetReviewRowMappingService().map(
        review_output=ReviewOutput(document_type="synthetic"),
        policies=[],
        run_type=PREFECT_MAILBOX_RUN_TYPE,
    )
    assert mapping.values["Run Type"] == PREFECT_MAILBOX_RUN_TYPE


def test_adapter_is_parameterless_and_calls_only_full_boundary_once():
    calls = []

    class SyntheticService:
        def run_selected_acceptance(self, **kwargs):
            calls.append(kwargs)
            return build_result()

    original = prefect_adapter.MailboxFullReviewOrchestrationService
    prefect_adapter.MailboxFullReviewOrchestrationService = SyntheticService
    try:
        with disable_run_logger():
            result = run_bounded_mailbox_application.fn()
    finally:
        prefect_adapter.MailboxFullReviewOrchestrationService = original

    assert result.success is True
    assert calls == [{
        "discovery_top": 10,
        "review_mode": MailboxClassificationReviewMode.DOWNSTREAM,
        "run_type": PREFECT_MAILBOX_RUN_TYPE,
        "acceptance_max_messages": 1,
        "acceptance_max_documents": 1,
        "stage_observer": calls[0]["stage_observer"],
    }]
    assert callable(calls[0]["stage_observer"])
    assert not run_bounded_mailbox_application.fn.__code__.co_argcount

    source = (ROOT / "src/orchestration/prefect_mailbox_workflow.py").read_text(
        encoding="utf-8-sig"
    )
    tree = ast.parse(source)
    application_imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src.")
    }
    assert application_imports == {
        "src.services.mailbox_full_review_orchestration_service"
    }
    assert not any(
        isinstance(node, (ast.For, ast.AsyncFor, ast.While))
        for node in ast.walk(tree)
    )


def test_adapter_options_disable_prefect_retries_and_result_capture():
    assert bounded_mailbox_flow.retries == 0
    assert bounded_mailbox_flow.persist_result is False
    assert bounded_mailbox_flow.log_prints is False
    assert run_bounded_mailbox_application.retries == 0
    assert run_bounded_mailbox_application.persist_result is False
    assert run_bounded_mailbox_application.log_prints is False


def test_adapter_logs_only_allowlisted_aggregate_metadata():
    private_marker = "PRIVATE-SYNTHETIC-PATIENT"
    logged = []

    class SyntheticLogger:
        def info(self, template, *arguments):
            logged.append(template % arguments)

    class SyntheticService:
        def run_selected_acceptance(self, **kwargs):
            for stage in (
                "mailbox_discovery", "attachment_download", "ocr",
                "classification", "subtype_classification", "extraction",
                "validation", "business_rules", "smartsheet_row_write",
                "attachment_upload", "mailbox_completion",
                "downstream_review", "completed",
            ):
                kwargs["stage_observer"](
                    stage=stage,
                    status="completed",
                    duration_seconds=0.01,
                    attempt_count=1,
                )
            return build_result()

    original_service = prefect_adapter.MailboxFullReviewOrchestrationService
    original_logger = prefect_adapter.get_run_logger
    prefect_adapter.MailboxFullReviewOrchestrationService = SyntheticService
    prefect_adapter.get_run_logger = lambda: SyntheticLogger()
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = run_bounded_mailbox_application.fn()
    finally:
        prefect_adapter.MailboxFullReviewOrchestrationService = original_service
        prefect_adapter.get_run_logger = original_logger

    rendered = "\n".join(logged) + stdout.getvalue() + stderr.getvalue()
    assert result.success is True
    assert private_marker not in rendered
    assert "stage=completed" in rendered
    assert "message_count=1" in rendered
    assert "document_count=1" in rendered
    assert "written_count=1" in rendered
    assert "failed_count=0" in rendered
    assert "row_attempt_count=1" in rendered
    assert "attachment_attempt_count=1" in rendered
    assert "pending_document_count=0" in rendered
    assert "completed_document_count=1" in rendered
    for stage in (
        "mailbox_discovery", "attachment_download", "ocr", "classification",
        "subtype_classification", "extraction", "validation", "business_rules",
        "smartsheet_row_write", "attachment_upload", "mailbox_completion",
        "downstream_review", "completed",
    ):
        assert f"stage={stage}" in rendered
    assert private_marker not in rendered


def test_adapter_failure_is_sanitized_and_nonretrying():
    private_marker = "PRIVATE-SYNTHETIC-PATIENT"

    class FailingService:
        def run_selected_acceptance(self, **kwargs):
            raise RuntimeError(private_marker)

    original = prefect_adapter.MailboxFullReviewOrchestrationService
    prefect_adapter.MailboxFullReviewOrchestrationService = FailingService
    try:
        with disable_run_logger():
            try:
                run_bounded_mailbox_application.fn()
            except SanitizedMailboxRunError as error:
                rendered = str(error)
            else:
                raise AssertionError("Expected sanitized adapter failure.")
    finally:
        prefect_adapter.MailboxFullReviewOrchestrationService = original

    assert private_marker not in rendered
    assert "application_boundary_failed" in rendered
    assert "retryable=false" in rendered
    assert run_bounded_mailbox_application.retries == 0


def test_result_contract_contains_only_allowlisted_operational_fields():
    names = {field.name for field in fields(MailboxFullReviewOrchestrationResult)}
    assert {
        "stage",
        "status",
        "failure_category",
        "retryable",
        "row_attempt_count",
        "attachment_attempt_count",
        "pending_document_count",
        "completed_document_count",
    } <= names
    prohibited = {
        "message_id", "subject", "filename", "file_path", "source_text",
        "row_id", "submission_key", "payload", "patient", "provider",
    }
    assert names.isdisjoint(prohibited)


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic and mock")
    print("External integrations: not called")
    print("PHI handling: allowlisted statuses, booleans, and aggregate counts only")
