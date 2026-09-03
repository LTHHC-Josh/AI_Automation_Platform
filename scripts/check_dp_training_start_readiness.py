"""PHI-safe readiness check for the operator-owned DP Training runtime."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from uuid import uuid4

from dotenv import load_dotenv

from src.services.document_processor_training_contracts import TRAINING_MODES


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def check_readiness() -> dict[str, object]:
    load_dotenv()
    mode = str(os.getenv("DP_TRAINING_MODE", "schema_only") or "").strip().lower()
    configuration_ready = bool(
        os.getenv("SMARTSHEET_API_TOKEN")
        and os.getenv("SMARTSHEET_AI_DESTINATION_SHEET_ID")
    )
    mode_ready = mode in TRAINING_MODES
    state_ready = _state_writable()
    write_gate_ready = (
        mode not in {"proposal_write", "approval_dispatch"}
        or os.getenv("DP_TRAINING_ALLOW_SMARTSHEET_WRITES") == "true"
    )
    dispatch_gate_ready = (
        mode != "approval_dispatch"
        or os.getenv("DP_TRAINING_ALLOW_CODEX_DISPATCH") == "true"
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
    if not configuration_ready:
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
        "training_mode": mode if mode_ready else "invalid",
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
    result = check_readiness()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["all_ready"] else 1)
