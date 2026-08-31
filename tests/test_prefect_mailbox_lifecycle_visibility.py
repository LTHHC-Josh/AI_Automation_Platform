import asyncio
import os
import tempfile
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
    "smartsheet-write",
    "smartsheet-attachment",
    "review-determination",
    "mailbox-finalization",
    "review-state",
    "workflow-completion",
)
VISIBLE_STARTED_STAGES = (
    "ocr",
    "document-classification",
    "extraction-attempt-1",
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
    )


class SyntheticApplication:
    def run_handoff_acceptance(self, **kwargs):
        observer = kwargs["stage_observer"]
        for stage in ("ocr", "classification", "extraction_attempt_1"):
            observer(stage=stage, status="started", attempt=1)
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
            "smartsheet_row_write",
            "attachment_upload",
            "review_determination",
            "mailbox_completion",
            "downstream_review",
            "completed",
        )
        for stage in internal_stages:
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


async def task_run_names(flow_run_id):
    names = set()
    for _ in range(20):
        async with get_client() as client:
            runs = await client.read_task_runs(
                task_run_filter=TaskRunFilter(
                    flow_run_id=TaskRunFilterFlowRunId(any_=[flow_run_id])
                )
            )
        names = {run.name for run in runs}
        if len(names) >= len(VISIBLE_STAGES) + len(VISIBLE_STARTED_STAGES) + 1:
            break
        await asyncio.sleep(0.25)
    return names


def test_synthetic_flow_exposes_safe_lifecycle_task_runs():
    original = workflow.MailboxFullReviewOrchestrationService
    workflow.MailboxFullReviewOrchestrationService = SyntheticApplication
    try:
        with prefect_test_harness():
            state = workflow.bounded_mailbox_flow(return_state=True)
            names = asyncio.run(task_run_names(state.state_details.flow_run_id))
    finally:
        workflow.MailboxFullReviewOrchestrationService = original

    assert state.is_completed()
    assert any(name.startswith("bounded-mailbox-application-run") for name in names)
    for stage in VISIBLE_STAGES:
        assert f"{stage}-completed" in names
    for stage in VISIBLE_STARTED_STAGES:
        assert f"{stage}-started" in names
    rendered = repr(names)
    for protected in (
        "message_id", "subject", "filename", "source_text", "row_id",
        "submission_key", "patient", "provider", "PROTECTED",
    ):
        assert protected not in rendered


if __name__ == "__main__":
    test_visibility_normalization_is_strictly_allowlisted_and_typed()
    test_synthetic_flow_exposes_safe_lifecycle_task_runs()
    print("Passed: 2")
    print("Failed: 0")
    print("Classification: synthetic deterministic local Prefect workflow")
    print("External integrations: not called")
    print("PHI handling: fixed allowlisted lifecycle names and aggregate metadata only")
