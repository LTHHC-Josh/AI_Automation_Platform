import asyncio
import inspect
import time

from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import TaskRunFilter, TaskRunFilterFlowRunId
from prefect.testing.utilities import prefect_test_harness

import src.orchestration.prefect_document_processor_training as training
from src.services.document_processor_training_contracts import TrainingCycleSummary


class SyntheticTrainingApplication:
    def run_cycle(self, *, stage_observer):
        stage_observer(stage="training_poll", status="started")
        time.sleep(0.01)
        stage_observer(stage="training_poll", status="completed", case_count=1)
        stage_observer(stage="case_discovered", status="completed", case_count=1)
        stage_observer(stage="case_loaded", status="started")
        time.sleep(0.01)
        stage_observer(stage="case_loaded", status="completed", case_count=1)
        stage_observer(stage="comment_checkpoint", status="completed")
        stage_observer(stage="local_analysis", status="started")
        time.sleep(0.01)
        stage_observer(stage="local_analysis", status="completed")
        stage_observer(stage="proposal_validated", status="completed")
        stage_observer(stage="awaiting_approval", status="completed")
        return TrainingCycleSummary(
            flagged_case_count=1,
            new_case_count=1,
            analysis_ready_count=1,
            awaiting_approval_count=1,
        )


async def read_task_runs(flow_run_id):
    async with get_client() as client:
        return await client.read_task_runs(
            task_run_filter=TaskRunFilter(
                flow_run_id=TaskRunFilterFlowRunId(any_=[flow_run_id])
            )
        )


def test_flow_is_parameterless_zero_retry_and_result_persistence_disabled():
    assert list(inspect.signature(training.document_processor_training_flow.fn).parameters) == []
    assert training.document_processor_training_flow.name == "lthhc-dp-training"
    assert training.document_processor_training_flow.retries == 0
    assert training.document_processor_training_flow.persist_result is False
    assert training.run_document_processor_training_cycle.retries == 0
    assert training.run_document_processor_training_cycle.persist_result is False


def test_isolated_flow_exposes_real_running_stages_and_safe_summary():
    original_factory = training.DocumentProcessorTrainingApplicationService.from_environment
    original_write = training._write_safe_summary
    training.DocumentProcessorTrainingApplicationService.from_environment = classmethod(
        lambda cls: SyntheticTrainingApplication()
    )
    training._write_safe_summary = lambda summary: None
    try:
        with prefect_test_harness():
            state = training.document_processor_training_flow(return_state=True)
            runs = asyncio.run(read_task_runs(state.state_details.flow_run_id))
    finally:
        training.DocumentProcessorTrainingApplicationService.from_environment = original_factory
        training._write_safe_summary = original_write
    assert state.is_completed()
    names = {run.name for run in runs}
    assert "Training Poll" in names
    assert "Local Analysis" in names
    assert "Correction Case Discovered" in names
    assert "Training Cycle Complete" in names
    for name in ("Training Poll", "Correction Case Loaded", "Local Analysis"):
        run = next(item for item in runs if item.name == name)
        assert run.state.is_completed()
        assert run.total_run_time.total_seconds() > 0
    rendered = repr(names).lower()
    for prohibited in (
        "row_id", "comment_text", "patient", "member", "filename",
        "source_text", "proposal_text", "document_path",
    ):
        assert prohibited not in rendered


def test_stage_and_summary_inputs_are_allowlisted():
    event = training._normalize_event(
        stage="local_analysis",
        status="completed",
        case_count=2,
        duration_seconds=1.5,
        failure_category="none",
    )
    assert set(event) == {
        "stage", "status", "case_count", "duration_seconds", "failure_category"
    }
    assert training._STAGE_NAMES["implementation_dispatch"] == "Implementation Dispatch"
    assert "awaiting_approval" not in training._LONG_RUNNING


if __name__ == "__main__":
    tests = [value for name, value in tuple(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/mock/isolated local Prefect")
    print("External integrations: not called")
    print("PHI handling: fixed safe stage names and aggregate counts only")
