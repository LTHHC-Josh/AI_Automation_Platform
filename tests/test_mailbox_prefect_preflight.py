import contextlib
from dataclasses import fields
import importlib.util
import io
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_mailbox_prefect_readiness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mailbox_prefect_preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def probes(module, *, values=None):
    selected = {
        "graph": True,
        "smartsheet": (True, True),
        "ocr": True,
        "ollama": True,
        "storage": True,
        "prefect": True,
    }
    selected.update(values or {})
    return module.ReadinessProbes(
        graph=lambda: selected["graph"],
        smartsheet=lambda: selected["smartsheet"],
        ocr=lambda: selected["ocr"],
        ollama=lambda: selected["ollama"],
        storage=lambda: selected["storage"],
        prefect=lambda: selected["prefect"],
    )


def test_all_ready_contract_contains_only_boolean_fields():
    module = load_module()
    result = module.check_readiness(probes(module))
    assert result.all_ready is True
    assert all(isinstance(getattr(result, item.name), bool) for item in fields(result))
    assert tuple(item.name for item in fields(result)) == (
        "graph_auth_config_ready",
        "smartsheet_destination_config_ready",
        "submission_key_column_config_ready",
        "ocr_config_model_ready",
        "ollama_model_ready",
        "local_state_storage_ready",
        "postgresql_prefect_ready",
        "all_ready",
    )


def test_each_failed_probe_fails_closed_without_leaking_output():
    module = load_module()
    private_marker = "PRIVATE-SYNTHETIC-CREDENTIAL"

    def failure():
        print(private_marker)
        raise RuntimeError(private_marker)

    cases = (
        {"graph": failure},
        {"smartsheet": failure},
        {"ocr": failure},
        {"ollama": failure},
        {"storage": failure},
        {"prefect": failure},
        {"smartsheet": (True, False)},
        {"smartsheet": True},
    )
    for values in cases:
        selected = probes(module, values=values)
        for name, value in values.items():
            if callable(value):
                selected = module.ReadinessProbes(
                    **{
                        field: (value if field == name else getattr(selected, field))
                        for field in (
                            "graph", "smartsheet", "ocr", "ollama", "storage", "prefect"
                        )
                    }
                )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = module.check_readiness(selected)
        assert result.all_ready is False
        assert private_marker not in stdout.getvalue() + stderr.getvalue()


def test_main_outputs_only_compact_boolean_json_and_exit_code():
    module = load_module()
    original = module.check_readiness
    module.check_readiness = lambda: original(probes(module))
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exit_code = module.main()
    finally:
        module.check_readiness = original
    payload = json.loads(output.getvalue())
    assert exit_code == 0
    assert set(payload) == {item.name for item in fields(module.MailboxPrefectReadiness)}
    assert all(value is True for value in payload.values())


def test_source_has_no_mailbox_enumeration_or_business_processing_calls():
    source = SCRIPT.read_text(encoding="utf-8-sig")
    prohibited = (
        "process_unread_messages",
        "bounded_mailbox_flow(",
        "deployment run",
        "get_unread_messages",
        "DocumentProcessor",
        ".classify(",
        ".extract(",
        ".add_row(",
        ".attach_file_to_row(",
    )
    for marker in prohibited:
        assert marker not in source


def test_prefect_probe_uses_running_server_backend_and_preserves_manual_contract():
    module = load_module()
    deployment = {
        "id": "00000000-0000-0000-0000-000000000001",
        "work_pool_name": module.POOL_NAME,
        "schedules": [],
        "parameter_openapi_schema": {"properties": {}},
        "global_concurrency_limit": {"limit": 1},
        "concurrency_options": {"collision_strategy": "CANCEL_NEW"},
    }
    pool = {
        "type": "process",
        "status": "READY",
        "concurrency_limit": 1,
        "is_paused": False,
    }

    class Response:
        def __init__(self, payload=None):
            self.status_code = 200
            self.payload = payload

        def json(self):
            return self.payload

    class Requests:
        @staticmethod
        def get(url, **kwargs):
            if url.endswith("/admin/version"):
                return Response("3.8.4")
            if url.endswith("/admin/settings"):
                return Response(
                    {"server": {"database": {"driver": "postgresql+asyncpg"}}}
                )
            return Response()

        @staticmethod
        def post(url, **kwargs):
            if url.endswith("/flow_runs/filter"):
                return Response([])
            return Response([{"status": "ONLINE"}])

    original_requests = module.requests
    original_run = module._run_prefect
    prefect_calls = []
    saved = {
        name: os.environ.pop(name, None)
        for name in (
            "PREFECT_SERVER_DATABASE_CONNECTION_URL",
            "PREFECT_API_DATABASE_CONNECTION_URL",
        )
    }
    module.requests = Requests
    def run_prefect(*arguments):
        prefect_calls.append(arguments)
        if arguments == ("version",):
            return "3.8.4 sqlite"
        if arguments[:2] == ("work-pool", "inspect"):
            return json.dumps(pool)
        return json.dumps(deployment)

    module._run_prefect = run_prefect
    try:
        assert module._prefect_ready() is True
        assert ("version",) not in prefect_calls
        original_post = Requests.post
        Requests.post = staticmethod(
            lambda url, **kwargs: (
                Response([{"state": "PENDING"}])
                if url.endswith("/flow_runs/filter")
                else original_post(url, **kwargs)
            )
        )
        assert module._prefect_ready() is False
    finally:
        module.requests = original_requests
        module._run_prefect = original_run
        for name, value in saved.items():
            if value is not None:
                os.environ[name] = value


def test_prefect_probe_rejects_sqlite_or_unproven_running_server_backend():
    module = load_module()

    class Response:
        status_code = 200

        def __init__(self, payload=None):
            self.payload = payload

        def json(self):
            return self.payload

    class Requests:
        driver = "sqlite+aiosqlite"

        @classmethod
        def get(cls, url, **kwargs):
            if url.endswith("/admin/version"):
                return Response("3.8.4")
            if url.endswith("/admin/settings"):
                payload = (
                    {"server": {"database": {"driver": cls.driver}}}
                    if cls.driver is not None
                    else {"server": {"database": {}}}
                )
                return Response(payload)
            return Response()

    original_requests = module.requests
    module.requests = Requests
    try:
        assert module._prefect_ready() is False
        Requests.driver = None
        assert module._prefect_ready() is False
    finally:
        module.requests = original_requests


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic and mock")
    print("External integrations: not called")
    print("PHI handling: allowlisted readiness booleans only")
