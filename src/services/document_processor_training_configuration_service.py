"""Fail-closed protected capability configuration for DP Training."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

from dotenv import dotenv_values

from src.services.document_processor_training_contracts import TRAINING_MODES


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_PATH = REPOSITORY_ROOT / ".env"
RUNTIME_FINGERPRINT_ENV = "DP_TRAINING_CAPABILITY_FINGERPRINT"


class DPTrainingConfigurationError(RuntimeError):
    """A PHI-safe DP Training capability configuration failure."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


@dataclass(frozen=True)
class DPTrainingCapabilityConfiguration:
    mode: str
    smartsheet_writes_enabled: bool
    codex_dispatch_enabled: bool
    fingerprint: str


def load_configured_dp_training_capabilities(
    *, env_path: Path = DEFAULT_ENV_PATH
) -> DPTrainingCapabilityConfiguration:
    """Read only the DP Training capability contract from the protected file."""
    try:
        values = dotenv_values(env_path)
    except Exception:
        raise DPTrainingConfigurationError("training_mode_unavailable") from None

    raw_mode = values.get("DP_TRAINING_MODE")
    if raw_mode is None or not str(raw_mode).strip():
        raise DPTrainingConfigurationError("training_mode_unavailable")
    mode = str(raw_mode).strip().lower()
    if mode not in TRAINING_MODES:
        raise DPTrainingConfigurationError("training_mode_invalid")

    write_enabled = _read_gate(
        values.get("DP_TRAINING_ALLOW_SMARTSHEET_WRITES")
    )
    dispatch_enabled = _read_gate(
        values.get("DP_TRAINING_ALLOW_CODEX_DISPATCH")
    )
    payload = {
        "codex_dispatch_enabled": dispatch_enabled,
        "mode": mode,
        "smartsheet_writes_enabled": write_enabled,
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    return DPTrainingCapabilityConfiguration(
        mode=mode,
        smartsheet_writes_enabled=write_enabled,
        codex_dispatch_enabled=dispatch_enabled,
        fingerprint=fingerprint,
    )


def load_runtime_dp_training_capabilities(
    *, env_path: Path = DEFAULT_ENV_PATH
) -> DPTrainingCapabilityConfiguration:
    """Require the protected configuration to match the startup-frozen runtime."""
    configured = load_configured_dp_training_capabilities(env_path=env_path)
    runtime_mode = str(os.getenv("DP_TRAINING_MODE") or "").strip().lower()
    runtime_fingerprint = str(os.getenv(RUNTIME_FINGERPRINT_ENV) or "").strip().lower()
    if not runtime_mode or not runtime_fingerprint:
        raise DPTrainingConfigurationError("training_mode_unavailable")
    if runtime_mode not in TRAINING_MODES:
        raise DPTrainingConfigurationError("training_mode_invalid")
    if (
        runtime_mode != configured.mode
        or runtime_fingerprint != configured.fingerprint
    ):
        raise DPTrainingConfigurationError("training_mode_mismatch")
    return configured


def _read_gate(value: object) -> bool:
    if value is None or value == "" or value == "false":
        return False
    if value == "true":
        return True
    raise DPTrainingConfigurationError("training_capability_gate_invalid")
