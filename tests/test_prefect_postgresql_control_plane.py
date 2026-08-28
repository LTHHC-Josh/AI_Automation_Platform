import ast
from pathlib import Path
import re
import yaml


ROOT = Path(__file__).resolve().parent.parent
CONFIGURE = ROOT / "scripts/configure_prefect_postgresql.ps1"
LAUNCHER = ROOT / "scripts/invoke_prefect_postgresql.ps1"
GUIDE = ROOT / "docs/prefect_local_control_room.md"


def read(path):
    return path.read_text(encoding="utf-8-sig")


def test_configuration_is_loopback_scram_least_privilege_and_fail_closed():
    source = read(CONFIGURE)
    assert "Assert-ElevatedSession" in source
    assert "Expected exactly one installed PostgreSQL service" in source
    assert "listen_addresses = 'localhost'" in source
    assert "port = '5432'" in source
    assert "password_encryption = 'scram-sha-256'" in source
    assert "pg_hba_file_rules" in source
    assert "127.0.0.1" in source and "::1" in source
    assert "NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION" in source
    assert "Refusing to overwrite" in source
    assert "ConvertFrom-SecureString" in source
    assert "RandomNumberGenerator" in source
    assert "Set-Service -Name $serviceName -StartupType Manual" in source


def test_launcher_uses_only_process_local_canonical_setting_and_cleans_up():
    source = read(LAUNCHER)
    assert "[ValidateSet('UpgradeDryRun', 'Upgrade', 'Server')]" in source
    assert "postgresql+asyncpg://prefect_server:$plainPassword" in source
    assert "$env:PREFECT_SERVER_DATABASE_CONNECTION_URL = $connectionUrl" in source
    assert "$env:PREFECT_SERVER_DATABASE_DRIVER = 'postgresql+asyncpg'" in source
    assert "$env:PREFECT_API_DATABASE_CONNECTION_URL =" not in source
    assert source.count("Remove-Item Env:PREFECT_SERVER_DATABASE_CONNECTION_URL") == 1
    assert source.count("Remove-Item Env:PREFECT_API_DATABASE_CONNECTION_URL") == 1
    assert source.count("Remove-Item Env:PREFECT_SERVER_DATABASE_DRIVER") == 1
    assert "finally" in source
    assert "Write-Host $connectionUrl" not in source
    assert "Write-Output $connectionUrl" not in source
    assert "--profile 'lthhc-postgres-server' version" in source


def test_repository_files_never_persist_a_complete_url_or_password():
    repository_sources = "\n".join(
        read(path)
        for path in (CONFIGURE, LAUNCHER, GUIDE, ROOT / "prefect.yaml")
    )
    assert "PREFECT_API_DATABASE_CONNECTION_URL=" not in repository_sources
    assert "PREFECT_SERVER_DATABASE_CONNECTION_URL=" not in repository_sources
    assert not re.search(r"postgresql\+asyncpg://prefect_server:[^$\s]", repository_sources)


def test_documented_operator_commands_are_one_physical_line():
    guide = read(GUIDE)
    required_markers = (
        "winget install --id PostgreSQL.PostgreSQL.17",
        "configure_prefect_postgresql.ps1",
        "-Action 'UpgradeDryRun'",
        "-Action 'Upgrade'",
        "-Action 'Server'",
        "work-pool create 'lthhc-local-process'",
        "work-pool set-concurrency-limit 'lthhc-local-process' 1",
        "deploy --all",
        "deploy 'src/orchestration/prefect_mailbox_workflow.py:bounded_mailbox_flow'",
        "deployment inspect 'lthhc-bounded-mailbox/manual-local'",
        "worker start --pool 'lthhc-local-process'",
        "Start-Process 'http://127.0.0.1:4200'",
        "1..5 | ForEach-Object",
        "Stop-Service -Name $pgServices[0].Name",
    )
    lines = guide.splitlines()
    for marker in required_markers:
        matches = [line for line in lines if marker in line]
        assert len(matches) == 1, marker
        assert not matches[0].rstrip().endswith("`")


def test_synthetic_and_manual_mailbox_deployments_are_conservative():
    deployment = read(ROOT / "prefect.yaml")
    assert deployment.count("entrypoint:") == 2
    assert "prefect_control_room.py:phi_safe_control_room_flow" in deployment
    assert "prefect_mailbox_workflow.py:bounded_mailbox_flow" in deployment
    assert deployment.count("schedule: null") == 2
    assert deployment.count("parameters: {}") == 2
    assert "name: manual-local" in deployment
    assert "limit: 1" in deployment
    assert "collision_strategy: CANCEL_NEW" in deployment
    assert "retries" not in deployment
    parsed = yaml.safe_load(deployment)
    mailbox = parsed["deployments"][1]
    assert mailbox == {
        "name": "manual-local",
        "description": (
            "Manual-only bounded mailbox orchestration with PHI-safe "
            "operational output."
        ),
        "tags": ["manual", "phi-safe"],
        "schedule": None,
        "concurrency_limit": {"limit": 1, "collision_strategy": "CANCEL_NEW"},
        "entrypoint": (
            "src/orchestration/prefect_mailbox_workflow.py:bounded_mailbox_flow"
        ),
        "parameters": {},
        "work_pool": {
            "name": "lthhc-local-process",
            "work_queue_name": None,
            "job_variables": {},
        },
    }


def test_operational_exception_is_version_bounded_and_evidence_gated():
    guide = read(GUIDE)
    continuity = read(ROOT / "PROJECT_MEMORY.md")
    tracker = read(ROOT / "update_project_tracker.py")
    for source in (guide, continuity, tracker):
        assert "Prefect 3.8.4" in source
        assert "9e9dadc36797" in source
        assert "14dc68cc5853" in source
        assert "version" in source.lower()
    assert "dry-run-only" in guide
    assert "must be rechecked on every Prefect version change" in guide
    assert "lthhc-bounded-mailbox/manual-local" in continuity
    assert "prefect_mailbox_workflow.py:bounded_mailbox_flow" in read(
        ROOT / "prefect.yaml"
    )


def test_tracker_and_memory_parse_without_embedded_runtime_secret():
    ast.parse(read(ROOT / "update_project_tracker.py"))
    continuity = read(ROOT / "PROJECT_MEMORY.md")
    assert "postgresql+asyncpg://prefect_server:" not in continuity
    assert "postgres-password.txt" not in continuity


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic PostgreSQL control-plane validation")
    print("External integrations: not called")
    print("PHI handling: configuration names, booleans, and fixed synthetic metadata only")
