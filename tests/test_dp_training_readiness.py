import os

import scripts.check_dp_training_start_readiness as readiness


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
    try:
        for name in TRACKED_ENVIRONMENT:
            os.environ.pop(name, None)
        os.environ.update(values)
        readiness._state_writable = lambda: True
        readiness.shutil.which = lambda name: "synthetic-codex.cmd"
        return readiness.check_readiness()
    finally:
        readiness._state_writable = original_state
        readiness.shutil.which = original_which
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
        "training_mode", "failure_category",
    }
    rendered = repr(result).lower()
    assert "synthetic-token" not in rendered
    assert "synthetic-sheet" not in rendered


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
