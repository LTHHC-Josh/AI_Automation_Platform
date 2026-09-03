"""PHI-safe readiness check for the operator-owned DP Training runtime."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
from uuid import uuid4

from dotenv import load_dotenv

from src.services.document_processor_training_configuration_service import (
    DPTrainingConfigurationError,
    load_configured_dp_training_capabilities,
    load_runtime_dp_training_capabilities,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def check_readiness(*, require_runtime_match: bool = False) -> dict[str, object]:
    load_dotenv(REPOSITORY_ROOT / ".env")
    configuration_error = "none"
    capabilities = None
    try:
        capabilities = (
            load_runtime_dp_training_capabilities()
            if require_runtime_match
            else load_configured_dp_training_capabilities()
        )
    except DPTrainingConfigurationError as error:
        configuration_error = error.category
    mode = capabilities.mode if capabilities is not None else "unavailable"
    configuration_ready = bool(
        os.getenv("SMARTSHEET_API_TOKEN")
        and os.getenv("SMARTSHEET_AI_DESTINATION_SHEET_ID")
    )
    mode_ready = capabilities is not None
    state_ready = _state_writable()
    write_gate_ready = (
        mode not in {"proposal_write", "approval_dispatch"}
        or bool(capabilities and capabilities.smartsheet_writes_enabled)
    )
    dispatch_gate_ready = (
        mode != "approval_dispatch"
        or bool(capabilities and capabilities.codex_dispatch_enabled)
    )
    codex_ready = True
    if mode == "approval_dispatch":
        codex_ready = bool(
            (shutil.which("codex.cmd") or shutil.which("codex"))
            and (REPOSITORY_ROOT / "src/contracts/dp_training_codex_result.schema.json").is_file()
        )
    all_ready = (
        configuration_ready and mode_ready and state_ready and codex_ready
        and write_gate_ready and dispatch_gate_ready
    )
    if configuration_error != "none":
        category = configuration_error
    elif not configuration_ready:
        category = "smartsheet_configuration_unavailable"
    elif not mode_ready:
        category = "training_mode_invalid"
    elif not state_ready:
        category = "protected_state_unavailable"
    elif not write_gate_ready:
        category = "smartsheet_write_gate_disabled"
    elif not dispatch_gate_ready:
        category = "codex_dispatch_gate_disabled"
    elif not codex_ready:
        category = "codex_runtime_unavailable"
    else:
        category = "none"
    return {
        "all_ready": all_ready,
        "configuration_ready": configuration_ready,
        "mode_ready": mode_ready,
        "protected_state_ready": state_ready,
        "smartsheet_write_gate_ready": write_gate_ready,
        "codex_dispatch_gate_ready": dispatch_gate_ready,
        "codex_runtime_ready": codex_ready,
        "training_mode": mode,
        "configured_mode": mode,
        "runtime_effective_mode": mode if require_runtime_match and mode_ready else "not_running",
        "mode_match": bool(require_runtime_match and mode_ready),
        "capability_fingerprint": capabilities.fingerprint if capabilities else "unavailable",
        "failure_category": category,
    }


def _state_writable() -> bool:
    directory = REPOSITORY_ROOT / "data/smartsheet_feedback"
    path = directory / f".training-readiness-{uuid4().hex}.tmp"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(b"ready\n")
            stream.flush()
            os.fsync(stream.fileno())
        return True
    except OSError:
        return False
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    require_runtime_match = "--require-runtime-match" in sys.argv[1:]
    result = check_readiness(require_runtime_match=require_runtime_match)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["all_ready"] else 1)
