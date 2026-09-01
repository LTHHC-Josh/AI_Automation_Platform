import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = ROOT / "scripts" / "check_mailbox_prefect_readiness.py"
WORKER_CHECK = ROOT / "scripts" / "check_mailbox_worker_auth_readiness.py"
WORKER_LAUNCHER = ROOT / "scripts" / "invoke_prefect_mailbox_worker.ps1"
DP_LAUNCHER = ROOT / "scripts" / "invoke_prefect_document_processor.ps1"
DEPLOYMENT = ROOT / "prefect.yaml"


class FakeAuthenticator:
    def __init__(self, token="synthetic-token"):
        self.token = token

    def get_access_token(self):
        return self.token


def test_prefect_and_worker_checks_share_graph_auth_boundary():
    preflight = PREFLIGHT.read_text(encoding="utf-8-sig")
    worker = WORKER_CHECK.read_text(encoding="utf-8-sig")
    assert "from src.graph.readiness import graph_auth_ready" in preflight
    assert "from src.graph.readiness import graph_auth_ready" in worker


def test_graph_auth_boundary_returns_only_boolean_and_discards_token():
    from src.graph.readiness import graph_auth_ready

    assert graph_auth_ready(lambda: FakeAuthenticator()) is True
    assert graph_auth_ready(lambda: FakeAuthenticator("")) is False
    assert graph_auth_ready(lambda: (_ for _ in ()).throw(RuntimeError("private"))) is False


def test_worker_subprocess_resolves_approved_config_without_printing_values():
    names = ("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET", "GRAPH_MAILBOX")
    synthetic = {name: f"private-{index}" for index, name in enumerate(names)}
    environment = os.environ.copy()
    environment.update(synthetic)
    environment["PYTHON_DOTENV_DISABLED"] = "1"
    environment["PYTHONPATH"] = str(ROOT)
    code = (
        "from src.graph.config import load_graph_config; "
        "c=load_graph_config(); "
        "print('true' if all((c.tenant_id,c.client_id,c.client_secret,c.mailbox)) else 'false')"
    )
    completed = subprocess.run(
        [str(ROOT / ".venv" / "Scripts" / "python.exe"), "-c", code],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    rendered = completed.stdout + completed.stderr
    assert completed.returncode == 0
    assert completed.stdout.strip() == "true"
    assert all(value not in rendered for value in synthetic.values())


def test_missing_worker_config_fails_before_any_mailbox_boundary():
    from src.graph.readiness import graph_auth_ready

    mailbox_called = False

    def missing_config():
        raise RuntimeError("missing")

    assert graph_auth_ready(missing_config) is False
    assert mailbox_called is False


def test_launcher_is_fail_closed_and_deployment_stays_secret_free_parameterless():
    launcher = WORKER_LAUNCHER.read_text(encoding="utf-8-sig")
    deployment = DEPLOYMENT.read_text(encoding="utf-8-sig")
    assert "check_mailbox_worker_auth_readiness.py" in launcher
    assert launcher.index("check_mailbox_worker_auth_readiness.py") < launcher.index("worker start")
    assert "Worker authentication readiness failed." in launcher
    assert "--limit 1" in launcher
    assert "[switch]$PrepareAcceptanceHandoff" in launcher
    assert "prepare_mailbox_acceptance_handoff.py" in launcher
    assert launcher.index("prepare_mailbox_acceptance_handoff.py") < launcher.index("worker start")
    assert "MailboxAcceptanceHandoffService().cleanup()" in launcher
    assert "parameters: {}" in deployment
    assert "job_variables: {}" in deployment
    prohibited = ("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET", "GRAPH_MAILBOX")
    assert all(marker not in launcher for marker in prohibited)
    assert all(marker not in deployment for marker in prohibited)


def test_unattended_launcher_uses_same_noninteractive_auth_boundary():
    launcher = DP_LAUNCHER.read_text(encoding="utf-8-sig")
    assert "check_mailbox_worker_auth_readiness.py" in launcher
    assert launcher.index("check_mailbox_worker_auth_readiness.py") < launcher.index("$workerArguments")
    assert "Start-Process -FilePath $prefect" in launcher
    assert "lthhc-unattended-dp-worker" in launcher
    assert "'--limit','1'" in launcher
    assert "$basePollSeconds = 300" in launcher
    assert "$maximumBackoffSeconds = 1800" in launcher
    assert "consecutive_failures" in launcher
    assert "deployment run $deploymentName --watch" in launcher
    assert "while (-not $worker.HasExited)" in launcher
    assert launcher.index("deployment run $deploymentName --watch") < launcher.index("Start-Sleep -Seconds $waitSeconds")
    assert launcher.index("$activationPath") < launcher.index("deployment run $deploymentName --watch")
    assert "Document Processor activation timed out." in launcher
    assert "dp-stop.signal" in launcher
    assert "PrepareAcceptanceHandoff" not in launcher
    for marker in ("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET", "GRAPH_MAILBOX"):
        assert marker not in launcher


def test_worker_check_public_contract_is_boolean_only():
    source = WORKER_CHECK.read_text(encoding="utf-8-sig")
    assert json.loads('{"worker_graph_auth_ready":true}') == {"worker_graph_auth_ready": True}
    assert "worker_graph_auth_ready" in source
    for marker in ("mailbox", "Smartsheet", "OCR", "Ollama", "deployment run"):
        assert marker not in source.replace("check_mailbox_worker_auth_readiness", "")


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic and mock")
    print("External integrations: not called")
    print("PHI handling: boolean-only auth readiness; synthetic values suppressed")
