import ast
import contextlib
import io
import os
from pathlib import Path
import tempfile
import time


os.environ["PREFECT_HOME"] = str(
    Path(tempfile.gettempdir()) / "lthhc_prefect_test_home"
)
os.environ["PREFECT_SERVER_ANALYTICS_ENABLED"] = "false"
os.environ["DO_NOT_TRACK"] = "1"

from prefect.logging import disable_run_logger
from prefect.testing.utilities import prefect_test_harness

from src.orchestration.prefect_control_room import (
    SyntheticControlRoomSummary,
    phi_safe_control_room_flow,
    phi_safe_wiring_check,
)


ROOT = Path(__file__).resolve().parent.parent
PROHIBITED_IMPORT_PREFIXES = (
    "src.graph",
    "src.ai",
    "src.clients",
    "src.smartsheet",
    "src.document_processing",
    "src.services",
)
CRITICAL_COMMANDS = (
    " config set ",
    "-Action 'Server'",
    " work-pool create ",
    " work-pool set-concurrency-limit ",
    " deploy --all",
    " worker start ",
    " deployment run ",
)


def assert_summary(summary):
    assert summary == SyntheticControlRoomSummary(
        stage="synthetic_control_room",
        status="completed",
        attempt_count=1,
        retryable=False,
    )


def test_task_contract_is_fixed_and_phi_safe():
    with disable_run_logger():
        summary = phi_safe_wiring_check.fn()
    assert_summary(summary)
    assert tuple(SyntheticControlRoomSummary.__dataclass_fields__) == (
        "stage",
        "status",
        "attempt_count",
        "retryable",
    )


def test_flow_runs_once_against_temporary_sqlite_backend():
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    with prefect_test_harness(), contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
        summary = phi_safe_control_room_flow()
    time.sleep(2)
    assert_summary(summary)
    captured = captured_stdout.getvalue() + captured_stderr.getvalue()
    assert "PRIVATE-SYNTHETIC-PATIENT" not in captured


def test_flow_and_task_options_are_conservative():
    assert phi_safe_control_room_flow.name == "lthhc-phi-safe-control-room"
    assert phi_safe_control_room_flow.retries == 0
    assert phi_safe_control_room_flow.persist_result is False
    assert phi_safe_wiring_check.name == "phi-safe-wiring-check"
    assert phi_safe_wiring_check.retries == 0
    assert phi_safe_wiring_check.persist_result is False


def test_synthetic_module_has_no_production_imports():
    source = (ROOT / "src/orchestration/prefect_control_room.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    for module_name in imported:
        assert not module_name.startswith(PROHIBITED_IMPORT_PREFIXES)


def test_documented_critical_commands_are_single_line_copy_safe():
    guide = (ROOT / "docs/prefect_local_control_room.md").read_text(encoding="utf-8-sig")
    lines = guide.splitlines()
    for marker in CRITICAL_COMMANDS:
        matches = [line for line in lines if marker in line]
        assert matches, marker
        for line in matches:
            assert line.startswith(("& ", "$", "1..5 "))
            assert not line.rstrip().endswith("`")
    for line in lines:
        if "`" in line and not line.lstrip().startswith("#"):
            assert not line.endswith("` ")


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic local Prefect validation")
    print("External integrations: not called")
    print("PHI handling: fixed synthetic statuses and timing metadata only")
