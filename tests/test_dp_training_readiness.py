import os
from types import SimpleNamespace

import scripts.check_dp_training_start_readiness as readiness
from src.services.document_processor_training_configuration_service import (
    DPTrainingConfigurationError,
)


TRACKED_ENVIRONMENT = (
    "SMARTSHEET_API_TOKEN",
    "SMARTSHEET_AI_DESTINATION_SHEET_ID",
    "DP_TRAINING_MODE",
    "DP_TRAINING_ALLOW_SMARTSHEET_WRITES",
    "DP_TRAINING_ALLOW_CODEX_DISPATCH",
)


def run_with(values):
    previous = {name: os.environ.get(name) for name in TRACKED_ENVIRONMENT}
    original_state = readiness._state_writable
    original_which = readiness.shutil.which
    original_configured = readiness.load_configured_dp_training_capabilities
    original_runtime = readiness.load_runtime_dp_training_capabilities
    try:
        for name in TRACKED_ENVIRONMENT:
            os.environ.pop(name, None)
        os.environ.update(values)
        readiness._state_writable = lambda: True
        readiness.shutil.which = lambda name: "synthetic-codex.cmd"
        capabilities = SimpleNamespace(
            mode=values["DP_TRAINING_MODE"],
            smartsheet_writes_enabled=(
                values.get("DP_TRAINING_ALLOW_SMARTSHEET_WRITES") == "true"
            ),
            codex_dispatch_enabled=(
                values.get("DP_TRAINING_ALLOW_CODEX_DISPATCH") == "true"
            ),
            fingerprint="a" * 64,
        )
        readiness.load_configured_dp_training_capabilities = lambda: capabilities
        readiness.load_runtime_dp_training_capabilities = lambda: capabilities
        return readiness.check_readiness()
    finally:
        readiness._state_writable = original_state
        readiness.shutil.which = original_which
        readiness.load_configured_dp_training_capabilities = original_configured
        readiness.load_runtime_dp_training_capabilities = original_runtime
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def configured(mode, **extra):
    return {
        "SMARTSHEET_API_TOKEN": "synthetic-token",
        "SMARTSHEET_AI_DESTINATION_SHEET_ID": "synthetic-sheet",
        "DP_TRAINING_MODE": mode,
        **extra,
    }


def test_schema_and_read_only_modes_need_no_mutation_gate():
    for mode in ("schema_only", "read_only"):
        result = run_with(configured(mode))
        assert result["all_ready"]
        assert result["smartsheet_write_gate_ready"]
        assert result["codex_dispatch_gate_ready"]


def test_write_and_dispatch_modes_fail_closed_until_exact_gates():
    write_blocked = run_with(configured("proposal_write"))
    assert not write_blocked["all_ready"]
    assert write_blocked["failure_category"] == "smartsheet_write_gate_disabled"
    dispatch_blocked = run_with(configured(
        "approval_dispatch", DP_TRAINING_ALLOW_SMARTSHEET_WRITES="true"
    ))
    assert not dispatch_blocked["all_ready"]
    assert dispatch_blocked["failure_category"] == "codex_dispatch_gate_disabled"
    ready = run_with(configured(
        "approval_dispatch",
        DP_TRAINING_ALLOW_SMARTSHEET_WRITES="true",
        DP_TRAINING_ALLOW_CODEX_DISPATCH="true",
    ))
    assert ready["all_ready"]


def test_public_readiness_contract_contains_only_safe_fixed_fields():
    result = run_with(configured("schema_only"))
    assert set(result) == {
        "all_ready", "configuration_ready", "mode_ready",
        "protected_state_ready", "smartsheet_write_gate_ready",
        "codex_dispatch_gate_ready", "codex_runtime_ready",
        "training_mode", "configured_mode", "runtime_effective_mode",
        "mode_match", "capability_fingerprint", "failure_category",
    }
    rendered = repr(result).lower()
    assert "synthetic-token" not in rendered
    assert "synthetic-sheet" not in rendered


def test_runtime_readiness_reports_the_effective_mode_match():
    previous = {name: os.environ.get(name) for name in TRACKED_ENVIRONMENT}
    original_state = readiness._state_writable
    original_runtime = readiness.load_runtime_dp_training_capabilities
    try:
        os.environ.update(configured("read_only"))
        readiness._state_writable = lambda: True
        readiness.load_runtime_dp_training_capabilities = lambda: SimpleNamespace(
            mode="read_only",
            smartsheet_writes_enabled=False,
            codex_dispatch_enabled=False,
            fingerprint="b" * 64,
        )
        result = readiness.check_readiness(require_runtime_match=True)
        assert result["all_ready"]
        assert result["configured_mode"] == "read_only"
        assert result["runtime_effective_mode"] == "read_only"
        assert result["mode_match"] is True
    finally:
        readiness._state_writable = original_state
        readiness.load_runtime_dp_training_capabilities = original_runtime
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def test_missing_or_invalid_mode_is_a_fail_closed_readiness_result():
    previous = {name: os.environ.get(name) for name in TRACKED_ENVIRONMENT}
    original_state = readiness._state_writable
    original_configured = readiness.load_configured_dp_training_capabilities
    try:
        os.environ.update(configured("read_only"))
        readiness._state_writable = lambda: True

        def fail_configuration():
            raise DPTrainingConfigurationError("training_mode_unavailable")

        readiness.load_configured_dp_training_capabilities = fail_configuration
        result = readiness.check_readiness()
        assert result["all_ready"] is False
        assert result["mode_ready"] is False
        assert result["configured_mode"] == "unavailable"
        assert result["failure_category"] == "training_mode_unavailable"
    finally:
        readiness._state_writable = original_state
        readiness.load_configured_dp_training_capabilities = original_configured
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


if __name__ == "__main__":
    tests = [
        value for name, value in tuple(globals().items())
        if name.startswith("test_")
    ]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic readiness")
    print("External integrations: not called")
    print("PHI handling: fixed booleans, modes, and categories only")
