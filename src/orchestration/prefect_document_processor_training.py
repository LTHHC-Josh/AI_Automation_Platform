"""PHI-safe Prefect adapter for one bounded DP Training cycle."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import re
from uuid import uuid4

from prefect import flow, get_run_logger, task
from prefect.client.orchestration import get_client
from prefect.context import get_run_context
from prefect.states import Completed, Failed, Running

from src.services.document_processor_training_application_service import (
    DocumentProcessorTrainingApplicationService,
)
from src.services.document_processor_training_configuration_service import (
    DPTrainingConfigurationError,
)
from src.services.document_processor_training_contracts import TrainingCycleSummary


_STAGE_NAMES = {
    "training_poll": "Training Poll",
    "case_discovered": "Correction Case Discovered",
    "case_loaded": "Correction Case Loaded",
    "comment_checkpoint": "Comment Checkpoint Updated",
    "local_analysis": "Local Analysis",
    "proposal_validated": "Proposal Validated",
    "proposal_write": "Proposal Written",
    "awaiting_approval": "Awaiting Correction Approval",
    "implementation_authorized": "Implementation Authorized",
    "implementation_dispatch": "Implementation Dispatch",
    "implementation_result": "Implementation Result",
    "retest_required": "Retest Required",
    "resolution_approved": "Resolution Approved",
    "case_resolved": "Case Resolved",
}
_LONG_RUNNING = {
    "training_poll", "case_loaded", "local_analysis", "proposal_write",
    "implementation_dispatch",
}
_SAFE_CATEGORY = re.compile(r"^[a-z][a-z0-9_]{0,79}$")


class SanitizedTrainingRunError(RuntimeError):
    """A Prefect-visible failure containing allowlisted metadata only."""


@task(
    name="dp-training-lifecycle-stage",
    task_run_name="{stage}",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def record_training_lifecycle_stage(
    *,
    stage: str,
    status: str,
    case_count: int | None = None,
    duration_seconds: float | None = None,
    failure_category: str = "none",
) -> None:
    """Record one normalized lifecycle event."""


@task(
    name="DP Training Workflow Summary",
    task_run_name="Training Cycle Complete",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def record_training_summary(**safe_summary) -> None:
    get_run_logger().info(
        " ".join(
            f"{key}={str(value).lower() if isinstance(value, bool) else value}"
            for key, value in safe_summary.items()
        )
    )


class _RunningTrainingStages:
    def __init__(self) -> None:
        self._runs: dict[str, object] = {}

    def update(self, *, stage: str, status: str) -> bool:
        if stage not in _LONG_RUNNING:
            return False
        context = get_run_context()
        flow_run_id = getattr(getattr(context, "task_run", None), "flow_run_id", None)
        if flow_run_id is None:
            return False
        client = get_client(sync_client=True)
        if status == "started":
            task_run = client.create_task_run(
                task=record_training_lifecycle_stage,
                flow_run_id=flow_run_id,
                dynamic_key=f"dp-training-{stage}-{uuid4().hex}",
                name=_STAGE_NAMES[stage],
                state=Running(),
                task_inputs={},
            )
            self._runs[stage] = task_run.id
            return True
        task_run_id = self._runs.pop(stage, None)
        if task_run_id is None:
            return False
        terminal = Failed(message="Training stage failed") if status == "failed" else Completed()
        client.set_task_run_state(task_run_id, terminal, force=True)
        return True

    def fail_open(self) -> None:
        client = get_client(sync_client=True)
        for task_run_id in tuple(self._runs.values()):
            client.set_task_run_state(
                task_run_id, Failed(message="Training boundary failed"), force=True
            )
        self._runs.clear()


def _normalize_event(*, stage, status, case_count=None, duration_seconds=None,
                     failure_category=None):
    safe_stage = _STAGE_NAMES.get(stage, "DP Training Status")
    safe_status = status if status in {"started", "completed", "failed", "skipped"} else "failed"
    safe_count = (
        case_count
        if isinstance(case_count, int) and not isinstance(case_count, bool) and case_count >= 0
        else None
    )
    safe_duration = (
        float(duration_seconds)
        if isinstance(duration_seconds, (int, float))
        and not isinstance(duration_seconds, bool)
        and 0 <= float(duration_seconds) <= 86400
        else None
    )
    category = (
        failure_category
        if isinstance(failure_category, str) and _SAFE_CATEGORY.fullmatch(failure_category)
        else "none" if not failure_category else "sanitized_failure"
    )
    return {
        "stage": safe_stage,
        "status": safe_status,
        "case_count": safe_count,
        "duration_seconds": safe_duration,
        "failure_category": category,
    }


def _safe_failure_category(value: object) -> str:
    return value if isinstance(value, str) and _SAFE_CATEGORY.fullmatch(value) else "sanitized_failure"


def _write_safe_summary(summary: TrainingCycleSummary) -> None:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        return
    directory = Path(base) / "LTHHC" / "Prefect" / "control-room"
    path = directory / "dp-training-summary.json"
    temporary = directory / f".dp-training-summary-{uuid4().hex}.tmp"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        temporary.write_text(
            json.dumps(asdict(summary), sort_keys=True, separators=(",", ":")) + "\n",
            encoding="ascii",
        )
        os.replace(temporary, path)
    except OSError:
        return
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


@task(
    name="DP Training Cycle",
    task_run_name="DP Training Cycle",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def run_document_processor_training_cycle() -> TrainingCycleSummary:
    stages = _RunningTrainingStages()

    def observe(**event) -> None:
        normalized = _normalize_event(**event)
        represented = False
        try:
            represented = stages.update(stage=event.get("stage"), status=normalized["status"])
        except Exception:
            represented = False
        if not represented:
            try:
                record_training_lifecycle_stage(**normalized)
            except Exception:
                pass

    try:
        result = DocumentProcessorTrainingApplicationService.from_environment().run_cycle(
            stage_observer=observe
        )
    except DPTrainingConfigurationError as error:
        try:
            stages.fail_open()
        except Exception:
            pass
        result = TrainingCycleSummary(
            polling_result="failed",
            failure_category=_safe_failure_category(error.category),
            recoverable=False,
            retryable=False,
        )
    except Exception:
        try:
            stages.fail_open()
        except Exception:
            pass
        raise SanitizedTrainingRunError(
            "stage=dp_training status=failed failure_category=application_boundary_failed retryable=false"
        ) from None
    _write_safe_summary(result)
    try:
        record_training_summary(**asdict(result))
    except Exception:
        pass
    if result.polling_result == "failed":
        category = _safe_failure_category(result.failure_category)
        raise SanitizedTrainingRunError(
            f"stage=dp_training status=failed failure_category={category} "
            f"retryable={str(result.retryable).lower()}"
        ) from None
    return result


@flow(
    name="lthhc-dp-training",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def document_processor_training_flow() -> TrainingCycleSummary:
    """Run one parameterless bounded DP Training cycle."""
    return run_document_processor_training_cycle()
