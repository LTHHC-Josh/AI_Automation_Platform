"""PHI-safe readiness for beginning unattended mailbox polling.

This boundary intentionally does not enumerate the mailbox, initialize OCR,
contact Ollama, or inspect the Smartsheet destination. Those dependencies are
required only after an eligible document is acquired and remain fail-closed in
the existing production pipeline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Callable

from src.graph.readiness import graph_auth_ready


ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class UnattendedStartReadiness:
    graph_auth_ready: bool
    local_state_storage_ready: bool
    all_ready: bool
    failure_category: str


def _storage_ready() -> bool:
    directories = (
        ROOT / "data" / "incoming",
        ROOT / "data" / "ocr_cache",
        ROOT / "data" / "mailbox_processing_state",
        ROOT / "data" / "mailbox_processing_state" / "jobs",
    )
    try:
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    "w", encoding="ascii", newline="\n", dir=directory, delete=False
                ) as handle:
                    temporary = Path(handle.name)
                    handle.write("ready\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                if temporary.read_text(encoding="ascii") != "ready\n":
                    return False
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
    except Exception:
        return False
    return True


def check_start_readiness(
    graph_probe: Callable[[], bool] = graph_auth_ready,
    storage_probe: Callable[[], bool] = _storage_ready,
) -> UnattendedStartReadiness:
    try:
        graph = graph_probe() is True
    except Exception:
        graph = False
    try:
        storage = storage_probe() is True
    except Exception:
        storage = False
    if not graph:
        category = "graph_auth_unavailable"
    elif not storage:
        category = "local_state_storage_unavailable"
    else:
        category = "none"
    return UnattendedStartReadiness(graph, storage, graph and storage, category)


def main() -> int:
    result = check_start_readiness()
    print(json.dumps(asdict(result), separators=(",", ":")))
    return 0 if result.all_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
