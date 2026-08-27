"""Synthetic Prefect control-room acceptance flow.

This module deliberately has no connection to production processing. It proves
only that the local Prefect server, process worker, deployment, flow, and task
can communicate while exposing allowlisted operational metadata.
"""

from dataclasses import dataclass

from prefect import flow, get_run_logger, task


@dataclass(frozen=True)
class SyntheticControlRoomSummary:
    """Allowlisted result for the PHI-safe synthetic flow."""

    stage: str
    status: str
    attempt_count: int
    retryable: bool


@task(
    name="phi-safe-wiring-check",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def phi_safe_wiring_check() -> SyntheticControlRoomSummary:
    """Perform one bounded in-memory wiring check."""

    summary = SyntheticControlRoomSummary(
        stage="synthetic_control_room",
        status="completed",
        attempt_count=1,
        retryable=False,
    )
    get_run_logger().info(
        "stage=synthetic_control_room status=completed "
        "attempt_count=1 retryable=false"
    )
    return summary


@flow(
    name="lthhc-phi-safe-control-room",
    retries=0,
    log_prints=False,
    persist_result=False,
)
def phi_safe_control_room_flow() -> SyntheticControlRoomSummary:
    """Run exactly one synthetic task and return its allowlisted summary."""

    return phi_safe_wiring_check()
