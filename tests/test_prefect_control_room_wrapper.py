from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "scripts" / "invoke_prefect_control_room.ps1"


def source():
    return WRAPPER.read_text(encoding="utf-8-sig")


def test_actions_and_safe_local_state_contract():
    text = source()
    assert "[ValidateSet('StartUI', 'Status', 'PrepareRun', 'RunOnce', 'StopWorker', 'StopControlRoom', 'RestartControlRoom')]" in text
    assert "LTHHC\\Prefect\\control-room" in text
    for prohibited in ("message_id", "subject", "sender", "filename", "row_id", "token", "payload"):
        assert prohibited not in text.lower()


def test_start_ui_neither_starts_worker_nor_runs_deployment_and_opens_ui():
    text = source()
    helper = text.split("function Start-ControlRoom {", 1)[1].split("function Stop-ControlRoomWorker", 1)[0]
    block = text.split("'StartUI' {", 1)[1].split("'PrepareRun' {", 1)[0]
    assert "$postgresLauncher" in helper
    assert "Start-Process 'http://127.0.0.1:4200'" in helper
    assert "Start-ControlRoom" in block
    assert "worker" not in block.lower()
    assert "deployment run" not in block


def test_prepare_delegates_handoff_and_never_invokes_deployment():
    block = source().split("'PrepareRun' {", 1)[1].split("'RunOnce' {", 1)[0]
    assert "fresh_online_worker_count -ne 0" in block
    assert "-PrepareAcceptanceHandoff" in block
    assert "deployment run" not in block


def test_run_once_contains_exactly_one_parameterless_watched_invocation():
    text = source()
    block = text.split("'RunOnce' {", 1)[1].split("'StopWorker' {", 1)[0]
    assert text.count("deployment run") == 1
    assert "deployment run $deploymentName --watch" in block
    for prohibited in ("--param", "--run-name", "--tag", "--start-in", "--start-at"):
        assert prohibited not in block


def test_stop_worker_requires_ownership_and_does_not_stop_infrastructure():
    text = source()
    helper = text.split("function Stop-ControlRoomWorker {", 1)[1].split("function Stop-ControlRoomInfrastructure", 1)[0]
    block = text.split("'StopWorker' {", 1)[1].split("'StopControlRoom' {", 1)[0]
    assert "Test-OwnedProcess $record $Marker" in text
    assert "Get-CimInstance Win32_Process" in text
    assert ".IndexOf($RequiredMarker, [StringComparison]::OrdinalIgnoreCase) -lt 0" in text
    assert ".Contains($RequiredMarker, [StringComparison]" not in text
    assert "Invoke-TaskKill -ProcessId ([int]$Identity.pid)" in text
    assert "Invoke-TaskKill -ProcessId ([int]$Identity.pid) -Force" in text
    assert "Sort-Object depth -Descending" in text
    assert "process_created_utc" in text
    assert "/T" not in text
    assert "Stop-OwnedComponent -Name 'worker'" in helper
    assert "Stop-Service" not in helper and "Stop-OwnedComponent -Name 'server'" not in helper
    assert "Stop-ControlRoomWorker" in block
    assert "Get-Process |" not in text
    assert "Stop-Process -Name" not in text


def test_control_room_stop_and_restart_are_worker_guarded_and_never_run_deployment():
    text = source()
    helper = text.split("function Stop-ControlRoomInfrastructure {", 1)[1].split("switch ($Action)", 1)[0]
    stop = text.split("'StopControlRoom' {", 1)[1].split("'RestartControlRoom' {", 1)[0]
    restart = text.split("'RestartControlRoom' {", 1)[1]
    assert "Stop the worker before control-room maintenance." in helper
    assert "Stop-OwnedComponent -Name 'server'" in helper and "Stop-Service" in helper
    assert "Stop-ControlRoomInfrastructure" in stop
    assert "Stop-ControlRoomInfrastructure" in restart and "Start-ControlRoom" in restart
    assert "worker start" not in restart and "deployment run" not in restart


def test_status_is_allowlisted_and_read_only():
    block = source().split("'Status' {", 1)[1].split("'StartUI' {", 1)[0]
    assert "Get-ControlPlaneStatus" in block
    assert "Start-" not in block and "Stop-" not in block and "deployment run" not in block


def test_wrapper_avoids_known_powershell_7_only_constructs():
    text = source()
    for unsupported in (
        "ConvertFrom-Json -AsHashtable",
        "-Encoding utf8NoBOM",
        "ForEach-Object -Parallel",
        "?.",
        "??",
    ):
        assert unsupported not in text


def test_ownership_comparison_runs_in_windows_powershell_51():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null
$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile(
    '__WRAPPER_PATH__', [ref]$tokens, [ref]$errors
)
if($errors.Count -ne 0){exit 10}
$functionAst=$ast.Find({
    param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Test-OwnedProcess'
}, $true)
Invoke-Expression $functionAst.Extent.Text
function Get-ProcessIdentity([int]$ProcessId){return $global:SyntheticIdentity}
$record=@{pid=42;owned=$true;process_created_utc='2026-01-01T00:00:00.0000000+00:00'}
$global:SyntheticIdentity=@{pid=42;created_utc='2026-01-01T00:00:00.0000000+00:00';command_line='powershell -File INVOKE_PREFECT_POSTGRESQL.PS1'}
if(-not (Test-OwnedProcess $record 'invoke_prefect_postgresql.ps1')){exit 11}
$global:SyntheticIdentity.command_line='powershell -File unrelated.ps1'
if(Test-OwnedProcess $record 'invoke_prefect_postgresql.ps1'){exit 12}
if(Test-OwnedProcess @{} 'invoke_prefect_postgresql.ps1'){exit 13}
$global:SyntheticIdentity.command_line='powershell -File invoke_prefect_postgresql.ps1'
$global:SyntheticIdentity.created_utc='2026-01-02T00:00:00.0000000+00:00'
if(Test-OwnedProcess $record 'invoke_prefect_postgresql.ps1'){exit 14}
Write-Output $PSVersionTable.PSVersion.Major
"""
    command = command.replace("__WRAPPER_PATH__", wrapper_path)
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert completed.returncode == 0, (
        f"exit={completed.returncode} stdout={completed.stdout!r} "
        f"stderr={completed.stderr!r}"
    )
    assert completed.stdout.strip() == "5"


def test_owned_nested_process_tree_stops_without_touching_unrelated_process():
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        grandchild = temporary / "grandchild.ps1"
        child = temporary / "child.ps1"
        root = temporary / "invoke_prefect_postgresql.ps1"
        grandchild.write_text("Start-Sleep -Seconds 120\n", encoding="utf-8")
        child.write_text(
            "$p=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"
            f"'{grandchild}') -WindowStyle Hidden -PassThru\n"
            "Wait-Process -Id $p.Id\n",
            encoding="utf-8",
        )
        root.write_text(
            "$one=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"
            f"'{child}') -WindowStyle Hidden -PassThru\n"
            "$two=Start-Process powershell.exe -ArgumentList @('-NoProfile','-Command','Start-Sleep -Seconds 120') -WindowStyle Hidden -PassThru\n"
            "Start-Process powershell.exe -ArgumentList @('-NoProfile','-Command','exit 0') -WindowStyle Hidden | Out-Null\n"
            "Wait-Process -Id @($one.Id,$two.Id)\n",
            encoding="utf-8",
        )
        wrapper_path = str(WRAPPER).replace("'", "''")
        root_path = str(root).replace("'", "''")
        state_directory = str(temporary / "state").replace("'", "''")
        command = r"""
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
if($errors.Count){exit 20}
foreach($name in @('Read-ControlState','Write-ControlState','Get-ProcessIdentity','Test-ProcessIdentity','Test-OwnedProcess','Get-ProvenOwnedProcessTree','Invoke-TaskKill','Stop-ProvenProcess','Stop-OwnedComponent')){
  $node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq $name},$true)
  Invoke-Expression $node.Extent.Text
}
$stateDirectory='__STATE_DIRECTORY__';$statePath=Join-Path $stateDirectory 'owned-processes.json'
$root=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','__ROOT__') -WindowStyle Hidden -PassThru
$unrelated=Start-Process powershell.exe -ArgumentList @('-NoProfile','-Command','Start-Sleep -Seconds 120') -WindowStyle Hidden -PassThru
try {
  Start-Sleep -Seconds 2
  $identity=Get-ProcessIdentity $root.Id
  if($null -eq $identity){exit 21}
  $state=@{server=@{pid=$root.Id;owned=$true;process_created_utc=$identity.created_utc;started_utc=[DateTimeOffset]::UtcNow.ToString('o')}}
  Write-ControlState $state
  $tree=@(Get-ProvenOwnedProcessTree $state.server 'invoke_prefect_postgresql.ps1')
  if($tree.Count -lt 4){exit 22}
  Stop-OwnedComponent 'server' 'invoke_prefect_postgresql.ps1'
  if(Test-ProcessIdentity $identity){exit 23}
  if($null -eq (Get-Process -Id $unrelated.Id -ErrorAction SilentlyContinue)){exit 24}
  if((Read-ControlState).ContainsKey('server')){exit 25}
  Write-Output $PSVersionTable.PSVersion.Major
} finally {
  $ErrorActionPreference='Continue'
  taskkill.exe /PID $root.Id /T /F 2>$null | Out-Null
  taskkill.exe /PID $unrelated.Id /T /F 2>$null | Out-Null
}
"""
        command = (
            command.replace("__WRAPPER__", wrapper_path)
            .replace("__ROOT__", root_path)
            .replace("__STATE_DIRECTORY__", state_directory)
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=40,
        )
        assert completed.returncode == 0, (
            f"exit={completed.returncode} stdout={completed.stdout!r} stderr={completed.stderr!r}"
        )
        assert completed.stdout.strip() == "5"


def test_force_fallback_revalidates_identity_after_graceful_failure():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Stop-ProvenProcess'},$true)
Invoke-Expression $node.Extent.Text
$global:alive=$true;$global:calls=@()
function Test-ProcessIdentity([hashtable]$Identity){return $global:alive}
function Invoke-TaskKill([int]$ProcessId,[switch]$Force){$global:calls+=@($Force.IsPresent);if($Force){$global:alive=$false;return 0};return 128}
function Wait-Process { param([int]$Id,[int]$Timeout,[object]$ErrorAction) }
Stop-ProvenProcess @{pid=42;created_utc='synthetic'}
if($global:calls.Count -ne 2 -or $global:calls[0] -ne $false -or $global:calls[1] -ne $true){exit 31}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
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
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/static")
    print("External integrations: not called")
    print("PHI handling: source-level allowlist assertions only")
