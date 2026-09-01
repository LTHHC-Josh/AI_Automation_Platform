"""Return only allowlisted booleans for an authorized mailbox-run preflight.

This command performs no mailbox enumeration, document retrieval, inference,
or business write. Some probes contact approved configuration/readiness
endpoints and therefore must be run only after separate operator authorization.
"""

from __future__ import annotations

import contextlib
from dataclasses import asdict, dataclass
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Callable
from urllib.parse import quote, urlparse

import requests


ROOT = Path(__file__).resolve().parent.parent
PREFECT = ROOT / ".venv" / "Scripts" / "prefect.exe"
API_URL = "http://127.0.0.1:4200/api"
POOL_NAME = "lthhc-local-process"
DEPLOYMENT_NAME = "lthhc-bounded-mailbox/document-processor-manual"
TERMINAL_FLOW_RUN_STATE_TYPES = frozenset(
    {"COMPLETED", "FAILED", "CANCELLED", "CRASHED"}
)
FLOW_RUN_PAGE_SIZE = 200


@dataclass(frozen=True)
class MailboxPrefectReadiness:
    graph_auth_config_ready: bool
    smartsheet_destination_config_ready: bool
    submission_key_column_config_ready: bool
    ocr_config_model_ready: bool
    ollama_model_ready: bool
    local_state_storage_ready: bool
    postgresql_prefect_ready: bool
    all_ready: bool


@dataclass(frozen=True)
class ReadinessProbes:
    graph: Callable[[], bool]
    smartsheet: Callable[[], tuple[bool, bool]]
    ocr: Callable[[], bool]
    ollama: Callable[[], bool]
    storage: Callable[[], bool]
    prefect: Callable[[], bool]


def _quiet_probe(probe, default):
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            return probe()
    except Exception:
        return default


def _graph_ready() -> bool:
    from src.graph.readiness import graph_auth_ready

    return graph_auth_ready()


def _smartsheet_ready() -> tuple[bool, bool]:
    from src.services.smartsheet_review_configuration_service import (
        APPROVED_DOCUMENT_FIELD_POLICIES,
    )
    from src.services.smartsheet_destination_schema_service import (
        SmartsheetDestinationSchemaService,
    )
    from src.services.smartsheet_review_row_mapping_service import (
        SmartsheetReviewRowMappingService,
    )
    from src.services.smartsheet_submission_key_configuration_service import (
        SmartsheetSubmissionKeyConfigurationService,
    )

    schema = SmartsheetDestinationSchemaService().read()
    if not schema.success:
        return False, False
    required = set(SmartsheetReviewRowMappingService.OPERATIONAL_METADATA_COLUMNS)
    for policy in APPROVED_DOCUMENT_FIELD_POLICIES:
        required.add(policy.column_name)
        if policy.confidence_column_name:
            required.add(policy.confidence_column_name)
    destination_ready = required.issubset(schema.columns)

    key = SmartsheetSubmissionKeyConfigurationService().resolve()
    key_ready = bool(
        key.success
        and key.column_title in schema.columns
        and schema.column_types.get(key.column_title) == "TEXT_NUMBER"
    )
    return destination_ready, key_ready


def _ocr_ready() -> bool:
    from src.ai import config
    from src.ai.ocr.providers.paddle_ocr_provider import PaddleOCRProvider

    if config.OCR_PROVIDER != "paddle":
        return False
    provider = PaddleOCRProvider()
    model = provider._create_ocr()
    return model is not None


def _ollama_ready() -> bool:
    from src.ai import config
    from src.ai.llm.llm_factory import LLMFactory

    if config.LLM_PROVIDER != "ollama":
        return False
    provider = LLMFactory.create()
    parsed = urlparse(provider.base_url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        return False
    result = provider.test_connection()
    return result.get("model_available") is True


def _storage_ready() -> bool:
    directories = (
        ROOT / "data" / "incoming",
        ROOT / "data" / "ocr_cache",
        ROOT / "data" / "mailbox_processing_state",
        ROOT / "data" / "mailbox_processing_state" / "jobs",
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        first = None
        second = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="ascii", newline="\n", dir=directory, delete=False
            ) as handle:
                first = Path(handle.name)
                handle.write("ready\n")
                handle.flush()
                os.fsync(handle.fileno())
            with tempfile.NamedTemporaryFile(
                "w", encoding="ascii", newline="\n", dir=directory, delete=False
            ) as handle:
                second = Path(handle.name)
                handle.write("replace\n")
            os.replace(second, first)
            second = None
            if first.read_text(encoding="ascii") != "replace\n":
                return False
        finally:
            if second is not None:
                second.unlink(missing_ok=True)
            if first is not None:
                first.unlink(missing_ok=True)
    return True


def _run_prefect(*arguments: str) -> str:
    completed = subprocess.run(
        [str(PREFECT), "--profile", "lthhc-local", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Prefect readiness command failed.")
    return completed.stdout


def _mailbox_run_history_is_terminal(deployment_id: object) -> bool:
    if not isinstance(deployment_id, str) or not deployment_id:
        return False
    offset = 0
    while True:
        runs = requests.post(
            f"{API_URL}/flow_runs/filter",
            json={
                "deployments": {"id": {"any_": [deployment_id]}},
                "limit": FLOW_RUN_PAGE_SIZE,
                "offset": offset,
            },
            timeout=10,
        )
        if runs.status_code != 200:
            return False
        run_items = runs.json()
        if not isinstance(run_items, list):
            return False
        for item in run_items:
            if not isinstance(item, dict) or item.get("state_type") not in (
                TERMINAL_FLOW_RUN_STATE_TYPES
            ):
                return False
        if len(run_items) < FLOW_RUN_PAGE_SIZE:
            return True
        offset += len(run_items)


def _prefect_ready() -> bool:
    if (
        os.getenv("PREFECT_SERVER_DATABASE_CONNECTION_URL")
        or os.getenv("PREFECT_API_DATABASE_CONNECTION_URL")
        or not PREFECT.is_file()
    ):
        return False
    health = requests.get(f"{API_URL}/health", timeout=10)
    database_ready = requests.get(f"{API_URL}/ready", timeout=10)
    server_version = requests.get(f"{API_URL}/admin/version", timeout=10)
    server_settings = requests.get(f"{API_URL}/admin/settings", timeout=10)
    if not all(
        response.status_code == 200
        for response in (health, database_ready, server_version, server_settings)
    ):
        return False
    settings = server_settings.json()
    if not isinstance(settings, dict):
        return False
    database = settings.get("server", {}).get("database", {})
    if not isinstance(database, dict) or (
        server_version.json() != "3.8.4"
        or database.get("driver") != "postgresql+asyncpg"
    ):
        return False

    pool = json.loads(_run_prefect("work-pool", "inspect", POOL_NAME, "--output", "json"))
    if not (
        pool.get("type") == "process"
        and pool.get("status") == "READY"
        and pool.get("concurrency_limit") == 1
        and pool.get("is_paused") is False
    ):
        return False

    deployment = json.loads(
        _run_prefect("deployment", "inspect", DEPLOYMENT_NAME, "--output", "json")
    )
    schema = deployment.get("parameter_openapi_schema") or {}
    global_concurrency = deployment.get("global_concurrency_limit") or {}
    concurrency = deployment.get("concurrency_limit") or global_concurrency.get("limit")
    options = deployment.get("concurrency_options") or {}
    if not (
        deployment.get("work_pool_name") == POOL_NAME
        and deployment.get("schedules") in (None, [])
        and schema.get("properties", {}) == {}
        and schema.get("required", []) == []
        and concurrency == 1
        and options.get("collision_strategy") == "CANCEL_NEW"
    ):
        return False

    if not _mailbox_run_history_is_terminal(deployment.get("id")):
        return False

    workers = requests.post(
        f"{API_URL}/work_pools/{quote(POOL_NAME, safe='')}/workers/filter",
        json={"limit": 10, "offset": 0},
        timeout=10,
    )
    if workers.status_code != 200:
        return False
    worker_items = workers.json()
    return (
        isinstance(worker_items, list)
        and len(worker_items) == 1
        and worker_items[0].get("status") == "ONLINE"
    )


def default_probes() -> ReadinessProbes:
    return ReadinessProbes(
        graph=_graph_ready,
        smartsheet=_smartsheet_ready,
        ocr=_ocr_ready,
        ollama=_ollama_ready,
        storage=_storage_ready,
        prefect=_prefect_ready,
    )


def check_readiness(probes: ReadinessProbes | None = None) -> MailboxPrefectReadiness:
    selected = probes or default_probes()
    graph = _quiet_probe(selected.graph, False) is True
    smartsheet_result = _quiet_probe(selected.smartsheet, (False, False))
    if not isinstance(smartsheet_result, tuple) or len(smartsheet_result) != 2:
        smartsheet_result = (False, False)
    smartsheet, submission_key = smartsheet_result
    ocr = _quiet_probe(selected.ocr, False) is True
    ollama = _quiet_probe(selected.ollama, False) is True
    storage = _quiet_probe(selected.storage, False) is True
    prefect = _quiet_probe(selected.prefect, False) is True
    values = (
        graph,
        smartsheet is True,
        submission_key is True,
        ocr,
        ollama,
        storage,
        prefect,
    )
    return MailboxPrefectReadiness(*values, all(values))


def main() -> int:
    result = check_readiness()
    print(json.dumps(asdict(result), separators=(",", ":")))
    return 0 if result.all_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
