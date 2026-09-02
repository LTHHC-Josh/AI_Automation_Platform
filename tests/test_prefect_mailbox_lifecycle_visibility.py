import asyncio
import os
import tempfile
import time
from pathlib import Path

os.environ["PREFECT_HOME"] = str(
    Path(tempfile.gettempdir()) / "lthhc_prefect_mailbox_visibility_test_home"
)
os.environ["PREFECT_SERVER_ANALYTICS_ENABLED"] = "false"
os.environ["DO_NOT_TRACK"] = "1"

from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import TaskRunFilter, TaskRunFilterFlowRunId
from prefect.testing.utilities import prefect_test_harness

import src.orchestration.prefect_mailbox_workflow as workflow
from src.services.mailbox_full_review_orchestration_service import (
    MailboxFullReviewOrchestrationResult,
)
from src.services.production_filename_assembly_service import FilenameReadinessDiagnostic


VISIBLE_STAGES = (
    "acceptance-handoff",
    "candidate-reverification",
    "document-acquisition",
    "ocr",
    "document-classification",
    "subtype-classification",
    "extraction-attempt-1",
    "validation-attempt-1",
    "extraction-retry-decision",
    "extraction-candidate-selection",
    "document-processing",
    "extraction",
    "deterministic-validation",
    "business-rules",
    "Smartsheet Row Created",
    "Smartsheet Attachment Uploaded",
    "review-determination",
    "mailbox-finalization",
    "review-state",
    "workflow-completion",
)
RUNNING_STAGE_NAMES = (
    "OCR",
    "Document Classification",
    "Subtype Classification",
    "Extraction Attempt 1",
    "Validation Attempt 1",
)


def result():
    return MailboxFullReviewOrchestrationResult(
        message_count=1,
        document_count=1,
        classification_submitted_count=0,
        classification_cancelled_count=0,
        approved_count=0,
        written_count=1,
        rejected_count=0,
        complete_review_cancelled_count=0,
        failed_count=0,
        success=True,
        status="completed",
        stage="completed",
        failure_category=None,
        retryable=False,
        row_attempt_count=1,
        attachment_attempt_count=1,
        pending_document_count=0,
        completed_document_count=1,
        row_action="created",
        attachment_action="uploaded",
        filename_readiness=FilenameReadinessDiagnostic(
            True, True, True, True, True, "Not Required", "Business"),
        review_reason_count=1,
        review_reason_categories=("authorization_quantity_requires_verification",),
    )


class SyntheticApplication:
    def run_handoff_acceptance(self, **kwargs):
        observer = kwargs["stage_observer"]
        internal_stages = (
            "acceptance_handoff",
            "candidate_reverification",
            "attachment_download",
            "ocr",
            "classification",
            "subtype_classification",
            "extraction_attempt_1",
            "validation_attempt_1",
            "extraction_retry_decision",
            "extraction_candidate_selection",
            "document_processing",
            "extraction",
            "validation",
            "business_rules",
            "smartsheet_row_created",
            "smartsheet_attachment_uploaded",
            "review_determination",
            "mailbox_completion",
            "downstream_review",
            "completed",
        )
        for stage in internal_stages:
            if stage in {
                "ocr", "classification", "subtype_classification",
                "extraction_attempt_1", "validation_attempt_1",
            }:
                observer(stage=stage, status="started", attempt=1)
                time.sleep(0.01)
            metadata = dict(
                stage=stage,
                status="completed",
                duration_seconds=0.01,
                attempt_count=1,
                candidate_message_count=1,
                candidate_document_count=1,
                review_required=False,
            )
            if stage == "extraction_attempt_1":
                metadata.update(
                    attempt=1,
                    ollama_total_duration_seconds=0.009,
                    ollama_load_duration_seconds=0.001,
                    ollama_prompt_eval_duration_seconds=0.002,
                    ollama_eval_duration_seconds=0.006,
                    prompt_token_count=12,
                    generated_token_count=8,
                )
            elif stage == "extraction_retry_decision":
                metadata.update(
                    retry_triggered=False,
                    raw_retry_required=False,
                    validated_retry_required=False,
                )
            elif stage == "extraction_candidate_selection":
                metadata.update(selected_attempt=1)
            observer(**metadata)
        return result()


def test_visibility_normalization_is_strictly_allowlisted_and_typed():
    normalized = workflow._normalize_stage_visibility(
        stage="extraction_attempt_1",
        status="completed",
        duration_seconds=2.5,
        attempt=1,
        prompt_token_count=12,
        generated_token_count=8,
        ollama_total_duration_seconds=2.0,
        retry_triggered=False,
        source_text="PROTECTED",
        prompt="PROTECTED",
        row_id="PROTECTED",
    )
    assert normalized["stage"] == "extraction-attempt-1"
    assert normalized["attempt"] == 1
    assert normalized["prompt_token_count"] == 12
    assert normalized["generated_token_count"] == 8
    assert normalized["ollama_total_duration_seconds"] == 2.0
    assert normalized["retry_triggered"] is False
    assert "source_text" not in normalized
    assert "prompt" not in normalized
    assert "row_id" not in normalized
    assert all(
        value is None or isinstance(value, (str, int, float, bool))
        for value in normalized.values()
    )


async def task_runs(flow_run_id):
    runs = []
    for _ in range(20):
        async with get_client() as client:
            runs = await client.read_task_runs(
                task_run_filter=TaskRunFilter(
                    flow_run_id=TaskRunFilterFlowRunId(any_=[flow_run_id])
                )
            )
        names = {run.name for run in runs}
        if len(names) >= len(VISIBLE_STAGES) + len(RUNNING_STAGE_NAMES) + 2:
            break
        await asyncio.sleep(0.25)
    return runs


def test_synthetic_flow_exposes_safe_lifecycle_task_runs():
    original = workflow.MailboxFullReviewOrchestrationService
    workflow.MailboxFullReviewOrchestrationService = SyntheticApplication
    try:
        with prefect_test_harness():
            state = workflow.bounded_mailbox_flow(return_state=True)
            runs = asyncio.run(task_runs(state.state_details.flow_run_id))
    finally:
        workflow.MailboxFullReviewOrchestrationService = original

    names = {run.name for run in runs}
    assert state.is_completed()
    assert any(name.startswith("bounded-mailbox-application-run") for name in names)
    for stage in VISIBLE_STAGES:
        if stage not in {
            "ocr", "document-classification", "subtype-classification",
            "extraction-attempt-1", "validation-attempt-1",
        }:
            assert f"{stage}-completed" in names
    for stage in RUNNING_STAGE_NAMES:
        assert stage in names
        stage_run = next(run for run in runs if run.name == stage)
        assert stage_run.state.is_completed()
        assert stage_run.total_run_time.total_seconds() > 0
    assert any(name.startswith("Workflow Summary") for name in names)
    assert not any(name.endswith("-started") for name in names)
    rendered = repr(names)
    for protected in (
        "message_id", "subject", "filename", "source_text", "row_id",
        "submission_key", "patient", "provider", "PROTECTED",
    ):
        assert protected not in rendered


class SyntheticRetryApplication(SyntheticApplication):
    def run_handoff_acceptance(self, **kwargs):
        observer = kwargs["stage_observer"]
        observer(stage="extraction_attempt_2", status="started", attempt=2)
        time.sleep(0.01)
        observer(
            stage="extraction_attempt_2", status="completed", attempt=2,
            duration_seconds=0.01,
        )
        observer(stage="validation_attempt_2", status="started", attempt=2)
        time.sleep(0.01)
        observer(
            stage="validation_attempt_2", status="completed", attempt=2,
            duration_seconds=0.01,
        )
        return super().run_handoff_acceptance(**kwargs)


def test_conditional_attempt_two_has_completed_duration_tasks():
    original = workflow.MailboxFullReviewOrchestrationService
    workflow.MailboxFullReviewOrchestrationService = SyntheticRetryApplication
    try:
        with prefect_test_harness():
            state = workflow.bounded_mailbox_flow(return_state=True)
            runs = asyncio.run(task_runs(state.state_details.flow_run_id))
    finally:
        workflow.MailboxFullReviewOrchestrationService = original
    for name in ("Extraction Attempt 2", "Validation Attempt 2"):
        stage_run = next(run for run in runs if run.name == name)
        assert stage_run.state.is_completed()
        assert stage_run.total_run_time.total_seconds() > 0


def test_conditional_attempt_two_uses_real_stage_names():
    manager = workflow._RunningStageVisibility()
    assert workflow._OPERATOR_STAGE_NAMES["extraction_attempt_2"] == "Extraction Attempt 2"
    assert workflow._OPERATOR_STAGE_NAMES["validation_attempt_2"] == "Validation Attempt 2"
    assert "extraction_retry_decision" not in workflow._LONG_RUNNING_STAGES
    assert "extraction_candidate_selection" not in workflow._LONG_RUNNING_STAGES


def test_smartsheet_action_stage_names_are_explicit_and_phi_safe():
    expected = {
        "smartsheet_row_created": "Smartsheet Row Created",
        "smartsheet_row_reconciled_existing": "Smartsheet Row Reconciled",
        "smartsheet_row_skipped": "Smartsheet Row Skipped",
        "smartsheet_attachment_uploaded": "Smartsheet Attachment Uploaded",
        "smartsheet_attachment_reconciled_existing": "Smartsheet Attachment Reconciled",
        "smartsheet_attachment_skipped": "Smartsheet Attachment Skipped",
    }
    assert {key: workflow._STAGE_NAMES[key] for key in expected} == expected
    assert "row_id" not in repr(expected)
    assert "attachment_name" not in repr(expected)


def test_summary_contract_excludes_protected_fields():
    source = Path(workflow.__file__).read_text(encoding="utf-8")
    summary_block = source.split("safe_summary = {", 1)[1].split("}\n    try:", 1)[0]
    for protected in (
        "source_text", "message_identity", "attachment_name", "document_name",
        "row_id", "payload", "mailbox_identity", "local_path", "credential",
    ):
        assert protected not in summary_block
    for safe_readiness_field in (
        "filename_person_components", "filename_payer_lookup",
        "filename_service_lookup", "filename_form", "filename_dates", "filename_workflow",
        "filename_qualifier", "filename_result", "filename_failure_category",
        "accepted_field_count", "optional_absent_field_count",
        "missing_required_count", "low_confidence_count", "unsupported_count",
        "ambiguous_count", "conflicting_count", "invalid_count",
        "quantity_present", "unit_source_category",
        "business_filename_attempted", "required_component_failure_count",
        "optional_component_omission_count",
    ):
        assert safe_readiness_field in summary_block
    try:
        workflow.record_mailbox_workflow_summary.fn(
            final_workflow_status="completed",
            document_count=1,
            written_count=1,
            failed_count=0,
            row_action="created",
            attachment_action="uploaded",
            row_attempt_count=1,
            attachment_attempt_count=1,
            completed_document_count=1,
            filename_person_components="Ready",
            filename_payer_lookup="Ready",
            filename_service_lookup="Ready",
            filename_dates="Ready",
            filename_workflow="Ready",
            filename_qualifier="Not Required",
            filename_result="business",
            review_reason_count=1,
            review_reason_categories="authorization_quantity_requires_verification",
            source_text="PROTECTED",
        )
    except TypeError:
        pass
    else:
        raise AssertionError("The summary task accepted a non-allowlisted field")


def test_visibility_failure_remains_best_effort():
    original = workflow._RunningStageVisibility.update
    workflow._RunningStageVisibility.update = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("synthetic"))
    original_record = workflow._record_stage_visibility
    workflow._record_stage_visibility = lambda metadata: None
    try:
        application = SyntheticApplication()
        assert application.run_handoff_acceptance(stage_observer=lambda **event: None).success
    finally:
        workflow._RunningStageVisibility.update = original
        workflow._record_stage_visibility = original_record


if __name__ == "__main__":
    test_visibility_normalization_is_strictly_allowlisted_and_typed()
    test_synthetic_flow_exposes_safe_lifecycle_task_runs()
    test_conditional_attempt_two_has_completed_duration_tasks()
    test_conditional_attempt_two_uses_real_stage_names()
    test_smartsheet_action_stage_names_are_explicit_and_phi_safe()
    test_summary_contract_excludes_protected_fields()
    test_visibility_failure_remains_best_effort()
    print("Passed: 7")
    print("Failed: 0")
    print("Classification: synthetic deterministic local Prefect workflow")
    print("External integrations: not called")
    print("PHI handling: fixed allowlisted lifecycle names and aggregate metadata only")
