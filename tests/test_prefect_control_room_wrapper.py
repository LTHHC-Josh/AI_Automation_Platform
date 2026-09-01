from pathlib import Path
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "scripts" / "invoke_prefect_control_room.ps1"


def source():
    return WRAPPER.read_text(encoding="utf-8-sig")


def test_actions_and_safe_local_state_contract():
    text = source()
    assert "'StartDP', 'StatusDP', 'StopDP'" in text
    assert "LTHHC\\Prefect\\control-room" in text
    for prohibited in ("message_id", "subject", "sender", "filename", "row_id", "token", "payload"):
        assert prohibited not in text.lower()


def test_unattended_commands_are_separate_owned_polling_controls():
    text = source()
    start = text.split("function Start-DocumentProcessor {", 1)[1].split("function Stop-DocumentProcessor", 1)[0]
    stop = text.split("function Stop-DocumentProcessor {", 1)[1].split("function Stop-ControlRoomInfrastructure", 1)[0]
    status = text.split("function Get-DocumentProcessorStatus {", 1)[1].split("function Start-OwnedComponent", 1)[0]
    assert "invoke_prefect_document_processor.ps1" in start
    assert "invoke_prefect_document_processor.ps1" in start
    assert "fresh_online_worker_count -ne 0" in start
    assert "mailbox_run_conflict" in start and "unattended_run_active" in start
    assert "System.Threading.Mutex" in start and "WaitOne(0)" in start
    assert "check_unattended_dp_start_readiness.py" in text
    assert start.index("$dpStartReadinessProbe") < start.index("Start-OwnedComponent -Name 'dp'")
    assert "Document Processor application readiness failed." not in start
    assert "Document Processor startup failed at $startupStage ($failureCategory)." in start
    assert "$startupCheckTimeoutSeconds = 30" in text
    assert "[Console]::Out.Flush()" in text
    assert text.index("'StartDP' {") < text.index("Start-DocumentProcessor", text.index("'StartDP' {"))
    assert "Write-Output (Start-DocumentProcessor)" not in text
    assert "dp_stop_requested_active_run" in stop
    assert "dp-stop.signal" in stop
    assert "Stop-OwnedComponent -Name 'dp'" in stop
    assert "Stop-Service" not in stop and "Stop-OwnedComponent -Name 'server'" not in stop
    assert "dp_process_ownership_proven" in status
    assert "current_bounded_run_active" in status
    assert "subject" not in status and "filename" not in status and "row_id" not in status


def test_manual_prepare_refuses_unattended_conflicts():
    block = source().split("'PrepareRun' {", 1)[1].split("'RunOnce' {", 1)[0]
    assert "$status.unattended_run_active" in block


def test_start_dp_duplicate_is_idempotent_in_windows_powershell_51():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Start-DocumentProcessor'},$true)
Invoke-Expression $node.Extent.Text
function Read-ControlState { return @{dp=@{pid=42;owned=$true;process_created_utc='synthetic'}} }
function Test-OwnedProcess { return $true }
function Write-StartupProgress { param([string]$Message) }
if(@(Start-DocumentProcessor)[-1] -ne 'dp_already_running'){exit 51}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


def test_start_dp_readiness_failure_precedes_worker_and_surfaces_safe_category():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Start-DocumentProcessor'},$true)
Invoke-Expression $node.Extent.Text
function Read-ControlState { return @{} }
function Get-ControlPlaneStatus { return @{postgresql_running=$true;prefect_server_reachable=$true;manual_deployment_ready=$true;unattended_deployment_ready=$true;mailbox_run_conflict=$false;unattended_run_active=$false;fresh_online_worker_count=0} }
function Test-PrefectServerReachable { return $true }
function Test-PrefectServerBackendSafe { return $true }
function Invoke-BoundedProcess { return @{exit_code=1;output=@('{"all_ready":false,"failure_category":"graph_auth_unavailable"}')} }
function Write-StartupProgress { param([string]$Message) $global:progress += @($Message) }
function Start-OwnedComponent { $global:workerCreated=$true }
$python='synthetic';$dpStartReadinessProbe='synthetic';$repositoryRoot='synthetic';$startupCheckTimeoutSeconds=30;$global:workerCreated=$false;$global:progress=@()
try { Start-DocumentProcessor; exit 56 } catch {
  if($_.Exception.Message -ne 'Document Processor startup failed at Graph authentication (graph_auth_unavailable).'){exit 57}
}
if($global:workerCreated){exit 58}
if(($global:progress -join '|') -notmatch '\[1/5\].*\[2/5\].*\[3/5\].*Stage: Graph authentication.*Reason: graph_auth_unavailable'){exit 59}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


def test_start_dp_progress_is_flushed_before_slow_work_in_windows_powershell_51():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Write-StartupProgress'},$true)
Invoke-Expression $node.Extent.Text
Write-StartupProgress 'visible-before-wait'
Start-Sleep -Seconds 2
Write-Output 'complete'
""".replace("__WRAPPER__", wrapper_path)
    started = time.monotonic()
    process = subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    assert process.stdout.readline().strip() == "visible-before-wait"
    assert time.monotonic() - started < 1.5
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 0, stderr
    assert stdout.strip() == "complete"


def test_start_dp_interruption_path_cleans_only_recorded_owned_runtime():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Start-DocumentProcessor'},$true)
Invoke-Expression $node.Extent.Text
function Write-StartupProgress { param([string]$Message) }
function Read-ControlState { return @{} }
function Test-OwnedProcess { return $false }
function Test-PrefectServerReachable { return $true }
function Test-PrefectServerBackendSafe { return $true }
function Get-ControlPlaneStatus { return @{postgresql_running=$true;prefect_server_reachable=$true;manual_deployment_ready=$true;unattended_deployment_ready=$true;mailbox_run_conflict=$false;unattended_run_active=$false;fresh_online_worker_count=0} }
function Invoke-BoundedProcess { return @{exit_code=0;output=@('{"all_ready":true,"failure_category":"none"}')} }
function Start-OwnedComponent { $global:started=$true }
function Get-FreshOnlineWorkerCount { throw [System.Management.Automation.PipelineStoppedException]::new() }
function Stop-OwnedComponent { param([string]$Name,[string]$Marker) if($Name -eq 'dp' -and $Marker -eq 'invoke_prefect_document_processor.ps1'){$global:stopped=$true} }
$python='synthetic';$dpStartReadinessProbe='synthetic';$repositoryRoot='synthetic';$startupCheckTimeoutSeconds=30;$global:started=$false;$global:stopped=$false
try { Start-DocumentProcessor; exit 71 } catch {}
if(-not $global:started -or -not $global:stopped){exit 72}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


def test_status_dp_reports_running_and_degraded_states_in_windows_powershell_51():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Get-DocumentProcessorStatus'},$true)
Invoke-Expression $node.Extent.Text
function Get-ControlPlaneStatus { return @{prefect_server_reachable=$true;work_pool_ready=$true;unattended_deployment_ready=$true;unattended_run_active=$false;fresh_online_worker_count=1} }
function Read-ControlState { return @{dp=@{pid=42;owned=$true;process_created_utc='synthetic'}} }
function Test-OwnedProcess { return $global:owned }
function Test-RecordedOwnedProcessExited { return $global:exited }
function Test-Path { param([string]$LiteralPath,[object]$PathType) return $global:active }
function Get-Content { return '{"polling_state":"waiting","last_check_utc":null,"next_check_utc":null,"consecutive_failures":0}' }
$stateDirectory='synthetic'
$global:owned=$true;$global:exited=$false;$global:active=$true;$running=Get-DocumentProcessorStatus
if(-not $running.dp_running -or $running.degraded){exit 52}
$global:owned=$false;$global:exited=$false;$global:active=$true;$degraded=Get-DocumentProcessorStatus
if($degraded.dp_running -or -not $degraded.degraded){exit 53}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


def test_status_formatters_are_readable_stable_and_keep_json_mode():
    text = source()
    assert "[switch]$Json" in text
    assert "if ($Json) { $status | ConvertTo-Json -Compress }" in text
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
foreach($name in @('ConvertTo-OperatorYesNo','Write-OperatorField','Write-ControlPlaneOperatorStatus','Write-DocumentProcessorOperatorStatus')){
  $node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq $name},$true)
  Invoke-Expression $node.Extent.Text
}
$control=[ordered]@{postgresql_running=$true;prefect_server_reachable=$false;work_pool_ready=$true;fresh_online_worker_count=0;manual_deployment_ready=$true;unattended_deployment_ready=$true;mailbox_run_conflict=$false;unattended_run_active=$false}
$dp=[ordered]@{dp_running=$false;dp_process_ownership_proven=$false;control_room_reachable=$true;work_pool_ready=$false;unattended_deployment_ready=$true;polling_active=$false;polling_state='stopped';current_bounded_run_active=$false;fresh_online_worker_count=0;degraded=$false;last_check_utc=$null;next_check_utc=$null;consecutive_failures=0}
$controlText=(Write-ControlPlaneOperatorStatus $control)-join "`n"
$dpText=(Write-DocumentProcessorOperatorStatus $dp)-join "`n"
if($controlText.IndexOf('PostgreSQL Running:') -gt $controlText.IndexOf('Fresh Workers:')){exit 61}
if($controlText -notmatch 'PostgreSQL Running:\s+Yes' -or $controlText -notmatch 'Prefect Server Reachable:\s+No'){exit 62}
if($dpText.IndexOf('DP Running:') -gt $dpText.IndexOf('Polling Active:')){exit 63}
if($dpText -notmatch 'Last Check:\s+Not yet' -or $dpText -notmatch 'Next Check:\s+Not scheduled'){exit 64}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


def test_stop_dp_owned_and_unowned_paths_are_separate():
    text = source()
    stop = text.split("function Stop-DocumentProcessor {", 1)[1].split("function Stop-ControlRoomInfrastructure", 1)[0]
    assert "Test-OwnedProcess $state.dp 'invoke_prefect_document_processor.ps1'" in stop
    assert "Stop-OwnedComponent -Name 'dp'" in stop
    assert "fresh worker is active but unattended ownership cannot be proven" in stop
    assert "Stop-ControlRoomWorker" not in stop


def test_stop_dp_owned_and_already_exited_behavior_in_windows_powershell_51():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Stop-DocumentProcessor'},$true)
Invoke-Expression $node.Extent.Text
function Test-PrefectServerReachable { return $true }
function Get-ControlPlaneStatus { return @{unattended_run_active=$false;fresh_online_worker_count=1} }
function Read-ControlState { return @{dp=@{pid=42;owned=$true;process_created_utc='synthetic'}} }
function Test-OwnedProcess { return $global:owned }
function Test-RecordedOwnedProcessExited { return $global:exited }
function Stop-OwnedComponent { $global:stopped=$true }
function Write-ControlState { $global:written=$true }
$global:owned=$true;$global:exited=$false;$global:stopped=$false
if((Stop-DocumentProcessor) -ne 'dp_stopped' -or -not $global:stopped){exit 54}
$global:owned=$false;$global:exited=$true;$global:written=$false
if((Stop-DocumentProcessor) -ne 'dp_already_exited_prefect_heartbeat_settling' -or -not $global:written){exit 55}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


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
    assert "$status.unattended_run_active" in block
    assert "$manualOwned" in block


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
    assert "Test-RecordedOwnedProcessExited" in helper
    assert "worker_already_exited_prefect_heartbeat_settling" in helper
    assert "Stop-Service" not in helper and "Stop-OwnedComponent -Name 'server'" not in helper
    assert "Stop-ControlRoomWorker" in block
    assert "Get-Process |" not in text
    assert "Stop-Process -Name" not in text


def test_stop_worker_recently_exited_owned_process_settles_fresh_heartbeat():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
foreach($name in @('Test-RecordedOwnedProcessExited','Stop-ControlRoomWorker')){
  $node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq $name},$true)
  Invoke-Expression $node.Extent.Text
}
$global:written=$false
function Read-ControlState { return @{worker=@{pid=42;owned=$true;process_created_utc='synthetic'}} }
function Write-ControlState([hashtable]$State) { $global:written=$true }
function Get-ProcessIdentity([int]$ProcessId) { return $null }
function Test-OwnedProcess { return $false }
function Get-ControlPlaneStatus { return @{fresh_online_worker_count=1} }
$result=Stop-ControlRoomWorker
if($result -ne 'worker_already_exited_prefect_heartbeat_settling' -or -not $global:written){exit 41}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


def test_stop_worker_unowned_fresh_worker_still_fails_closed():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Stop-ControlRoomWorker'},$true)
Invoke-Expression $node.Extent.Text
function Read-ControlState { return @{} }
function Get-ControlPlaneStatus { return @{fresh_online_worker_count=1} }
try { Stop-ControlRoomWorker; exit 42 } catch {
  if($_.Exception.Message -ne 'A fresh worker is active but wrapper ownership cannot be proven.'){exit 43}
}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


def test_reused_pid_fresh_worker_failure_preserves_local_state():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
foreach($name in @('Test-RecordedOwnedProcessExited','Stop-ControlRoomWorker')){
  $node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq $name},$true)
  Invoke-Expression $node.Extent.Text
}
$global:written=$false
function Read-ControlState { return @{worker=@{pid=42;owned=$true;process_created_utc='old'}} }
function Write-ControlState([hashtable]$State) { $global:written=$true }
function Get-ProcessIdentity([int]$ProcessId) { return @{pid=42;created_utc='reused';command_line='unrelated'} }
function Test-OwnedProcess { return $false }
function Get-ControlPlaneStatus { return @{fresh_online_worker_count=1} }
try { Stop-ControlRoomWorker; exit 45 } catch {
  if($_.Exception.Message -ne 'A fresh worker is active but wrapper ownership cannot be proven.'){exit 46}
}
if($global:written){exit 47}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


def test_reused_recorded_pid_cannot_authorize_heartbeat_settling():
    wrapper_path = str(WRAPPER).replace("'", "''")
    command = r"""
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('__WRAPPER__',[ref]$tokens,[ref]$errors)
$node=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Test-RecordedOwnedProcessExited'},$true)
Invoke-Expression $node.Extent.Text
function Get-ProcessIdentity([int]$ProcessId) { return @{pid=42;created_utc='reused';command_line='unrelated'} }
if(Test-RecordedOwnedProcessExited @{pid=42;owned=$true;process_created_utc='old'}){exit 44}
Write-Output $PSVersionTable.PSVersion.Major
""".replace("__WRAPPER__", wrapper_path)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "5"


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
