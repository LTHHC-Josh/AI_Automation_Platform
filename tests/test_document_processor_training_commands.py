from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "scripts/invoke_prefect_control_room.ps1"
LAUNCHER = ROOT / "scripts/invoke_prefect_document_processor_training.ps1"
INSTALLER = ROOT / "scripts/install_prefect_control_room_commands.ps1"


def read(path):
    return path.read_text(encoding="utf-8-sig")


def test_exact_training_commands_and_actions_are_installed():
    installer = read(INSTALLER)
    wrapper = read(WRAPPER)
    for command, action in (
        ("startdptraining", "StartDPTraining"),
        ("statusdptraining", "StatusDPTraining"),
        ("stopdptraining", "StopDPTraining"),
    ):
        assert f"{command} = '{action}'" in installer
        assert f"'{action}'" in wrapper
    for prohibited in ("startfeedback", "statusfeedback", "stopfeedback"):
        assert prohibited not in installer.lower()


def test_training_launcher_is_parameterless_bounded_and_dedicated():
    source = read(LAUNCHER)
    assert "param()" in source
    assert "lthhc-dp-training/document-processor-training" in source
    assert "lthhc-dp-training-process" in source
    assert "lthhc-dp-training-worker" in source
    assert "--limit','1'" in source
    assert "deployment run $deploymentName --watch" in source
    assert "$basePollSeconds = 300" in source
    assert "$maximumBackoffSeconds = 1800" in source
    assert "$env:PREFECT_WORKER_WEBSERVER_PORT = '8081'" in source
    assert "dp-training-stop.signal" in source
    for prohibited in ("startdp", "document-processor-live", "stop-service", "start-service"):
        assert prohibited not in source.lower()


def test_live_and_training_stop_boundaries_are_independent():
    source = read(WRAPPER)
    live = source.split("function Stop-DocumentProcessor {", 1)[1].split(
        "function Start-DocumentProcessorTraining", 1
    )[0]
    training = source.split("function Stop-DocumentProcessorTraining {", 1)[1].split(
        "function Stop-ControlRoomInfrastructure", 1
    )[0]
    assert "dp_training" not in live
    assert "Stop-OwnedComponent -Name 'dp'" in live
    assert "Stop-OwnedComponent -Name 'dp_training'" in training
    assert "Stop-OwnedComponent -Name 'dp'" not in training
    assert "Stop-Service" not in training
    assert source.count("Local\\LTHHC-Prefect-DocumentServices-Control") == 4


def test_training_start_does_not_conflict_with_live_pool_worker():
    source = read(WRAPPER)
    block = source.split("function Start-DocumentProcessorTraining {", 1)[1].split(
        "function Stop-DocumentProcessorTraining", 1
    )[0]
    assert "$control.training_fresh_online_worker_count -ne 0" in block
    assert "$control.fresh_online_worker_count -ne 0" not in block
    assert "$control.unattended_run_active" not in block
    assert "Start-OwnedComponent -Name 'dp_training'" in block


def test_control_room_shutdown_guards_both_runtime_families():
    source = read(WRAPPER)
    block = source.split("function Stop-ControlRoomInfrastructure {", 1)[1].split(
        "switch ($Action)", 1
    )[0]
    assert "$ownedDp" in block and "$ownedTraining" in block
    assert "$control.fresh_online_worker_count" in block
    assert "$control.training_fresh_online_worker_count" in block


def test_modified_powershell_parses_in_windows_powershell_51():
    paths = ",".join("'" + str(path).replace("'", "''") + "'" for path in (
        WRAPPER, LAUNCHER, INSTALLER,
    ))
    command = (
        "$all=@(" + paths + ");foreach($path in $all){$tokens=$null;$errors=$null;"
        "[System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)|Out-Null;"
        "if($errors.Count){exit 8}};Write-Output $PSVersionTable.PSVersion.Major"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


if __name__ == "__main__":
    tests = [value for name, value in tuple(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic Windows PowerShell 5.1")
    print("External integrations: not called")
    print("PHI handling: fixed command, pool, deployment, and ownership names only")
