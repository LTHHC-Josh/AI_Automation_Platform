[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('StartUI', 'Status', 'PrepareRun', 'RunOnce', 'StopWorker', 'StopControlRoom', 'RestartControlRoom')]
    [string]$Action
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$prefect = Join-Path $repositoryRoot '.venv\Scripts\prefect.exe'
$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$postgresLauncher = Join-Path $PSScriptRoot 'invoke_prefect_postgresql.ps1'
$workerLauncher = Join-Path $PSScriptRoot 'invoke_prefect_mailbox_worker.ps1'
$readinessProbe = Join-Path $PSScriptRoot 'check_mailbox_prefect_readiness.py'
$stateDirectory = Join-Path $env:LOCALAPPDATA 'LTHHC\Prefect\control-room'
$statePath = Join-Path $stateDirectory 'owned-processes.json'
$apiUrl = 'http://127.0.0.1:4200/api'
$poolName = 'lthhc-local-process'
$deploymentName = 'lthhc-bounded-mailbox/manual-local'
$freshHeartbeatSeconds = 90

function Read-ControlState {
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { return @{} }
    try {
        $value = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        $state = @{}
        foreach ($property in $value.PSObject.Properties) {
            $record = @{}
            foreach ($field in $property.Value.PSObject.Properties) { $record[$field.Name] = $field.Value }
            $state[$property.Name] = $record
        }
        return $state
    } catch { return @{} }
}

function Write-ControlState([hashtable]$State) {
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
    $temporary = Join-Path $stateDirectory ('.owned-processes.' + [Guid]::NewGuid().ToString('N') + '.tmp')
    $State | ConvertTo-Json -Compress | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $statePath -Force
}

function Get-ProcessIdentity([int]$ProcessId) {
    $item = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $item -or $null -eq $item.CreationDate) { return $null }
    return @{
        pid = [int]$item.ProcessId
        parent_pid = [int]$item.ParentProcessId
        created_utc = ([DateTimeOffset]$item.CreationDate).ToUniversalTime().ToString('o')
        command_line = [string]$item.CommandLine
    }
}

function Test-ProcessIdentity([hashtable]$Identity) {
    if ($null -eq $Identity -or -not $Identity.ContainsKey('pid') -or -not $Identity.ContainsKey('created_utc')) { return $false }
    $current = Get-ProcessIdentity ([int]$Identity.pid)
    return ($null -ne $current -and $current.created_utc -eq [string]$Identity.created_utc)
}

function Test-OwnedProcess([hashtable]$Record, [string]$RequiredMarker) {
    if ($null -eq $Record -or -not $Record.ContainsKey('pid') -or -not $Record.ContainsKey('process_created_utc') -or $Record.owned -ne $true) { return $false }
    $processId = 0
    if (-not [int]::TryParse([string]$Record.pid, [ref]$processId) -or $processId -le 0) { return $false }
    $identity = Get-ProcessIdentity $processId
    if ($null -eq $identity -or $identity.command_line.IndexOf($RequiredMarker, [StringComparison]::OrdinalIgnoreCase) -lt 0) { return $false }
    return ($identity.created_utc -eq [string]$Record.process_created_utc)
}

function Test-RecordedOwnedProcessExited([hashtable]$Record) {
    if ($null -eq $Record -or -not $Record.ContainsKey('pid') -or -not $Record.ContainsKey('process_created_utc') -or $Record.owned -ne $true) { return $false }
    $processId = 0
    if (-not [int]::TryParse([string]$Record.pid, [ref]$processId) -or $processId -le 0) { return $false }
    return $null -eq (Get-ProcessIdentity $processId)
}

function Get-PostgreSqlService {
    $services = @(Get-Service | Where-Object { $_.Name -like 'postgresql*' })
    if ($services.Count -ne 1) { throw "Expected exactly one PostgreSQL service; found $($services.Count)." }
    return $services[0]
}

function Test-PrefectServerReachable {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "$apiUrl/health" -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch { return $false }
}

function Test-PrefectServerBackendSafe {
    try {
        $version = Invoke-RestMethod -Uri "$apiUrl/admin/version" -TimeoutSec 3
        $settings = Invoke-RestMethod -Uri "$apiUrl/admin/settings" -TimeoutSec 3
        return ($version -eq '3.8.4' -and $settings.server.database.driver -eq 'postgresql+asyncpg')
    } catch { return $false }
}

function Invoke-PrefectJson([string[]]$Arguments) {
    $output = & $prefect --profile 'lthhc-local' @Arguments 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'A read-only Prefect inspection failed.' }
    return ($output | Out-String | ConvertFrom-Json)
}

function Get-OptionalProperty($Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Test-ControlPlaneConfiguration {
    try {
        $pool = Invoke-PrefectJson -Arguments @('work-pool', 'inspect', $poolName, '--output', 'json')
        $deployment = Invoke-PrefectJson -Arguments @('deployment', 'inspect', $deploymentName, '--output', 'json')
        $schema = Get-OptionalProperty $deployment 'parameter_openapi_schema'
        $properties = Get-OptionalProperty $schema 'properties'
        $required = Get-OptionalProperty $schema 'required'
        $directLimit = Get-OptionalProperty $deployment 'concurrency_limit'
        $globalLimit = Get-OptionalProperty $deployment 'global_concurrency_limit'
        $limit = if ($null -ne $directLimit) { $directLimit } else { Get-OptionalProperty $globalLimit 'limit' }
        $options = Get-OptionalProperty $deployment 'concurrency_options'
        $schedules = Get-OptionalProperty $deployment 'schedules'
        $schedulesEmpty = $null -eq $schedules -or @($schedules).Count -eq 0
        $propertiesEmpty = $null -eq $properties -or @($properties.PSObject.Properties).Count -eq 0
        $requiredEmpty = $null -eq $required -or @($required).Count -eq 0
        return ($pool.type -eq 'process' -and $pool.concurrency_limit -eq 1 -and $pool.is_paused -eq $false -and $deployment.work_pool_name -eq $poolName -and $schedulesEmpty -and $propertiesEmpty -and $requiredEmpty -and $limit -eq 1 -and (Get-OptionalProperty $options 'collision_strategy') -eq 'CANCEL_NEW')
    } catch { return $false }
}

function Get-ControlPlaneStatus {
    $result = [ordered]@{
        postgresql_running = $false; prefect_server_reachable = $false
        work_pool_ready = $false; fresh_online_worker_count = 0
        mailbox_run_conflict = $false; manual_deployment_ready = $false
    }
    try { $result.postgresql_running = (Get-PostgreSqlService).Status -eq 'Running' } catch {}
    $result.prefect_server_reachable = Test-PrefectServerReachable
    if (-not $result.prefect_server_reachable) { return $result }
    try {
        $pool = Invoke-PrefectJson -Arguments @('work-pool', 'inspect', $poolName, '--output', 'json')
        $result.work_pool_ready = ($pool.type -eq 'process' -and $pool.status -eq 'READY' -and $pool.concurrency_limit -eq 1 -and $pool.is_paused -eq $false)
        $deployment = Invoke-PrefectJson -Arguments @('deployment', 'inspect', $deploymentName, '--output', 'json')
        $result.manual_deployment_ready = Test-ControlPlaneConfiguration
        $workers = Invoke-RestMethod -Method Post -Uri "$apiUrl/work_pools/$poolName/workers/filter" -ContentType 'application/json' -Body '{"limit":50,"offset":0}' -TimeoutSec 5
        $cutoff = [DateTimeOffset]::UtcNow.AddSeconds(-$freshHeartbeatSeconds)
        $result.fresh_online_worker_count = @($workers | Where-Object { $_.status -eq 'ONLINE' -and $null -ne $_.last_heartbeat_time -and [DateTimeOffset]::Parse($_.last_heartbeat_time) -ge $cutoff }).Count
        $body = @{ deployments = @{ id = @{ any_ = @($deployment.id) } }; limit = 200; offset = 0 } | ConvertTo-Json -Depth 5 -Compress
        $runs = Invoke-RestMethod -Method Post -Uri "$apiUrl/flow_runs/filter" -ContentType 'application/json' -Body $body -TimeoutSec 5
        $terminal = @('COMPLETED', 'FAILED', 'CANCELLED', 'CRASHED')
        $result.mailbox_run_conflict = @($runs | Where-Object { $_.state_type -notin $terminal }).Count -gt 0
    } catch {}
    return $result
}

function Start-OwnedComponent([string]$Name, [string]$Script, [string[]]$Arguments, [string]$Marker, [switch]$Interactive) {
    $state = Read-ControlState
    if ($state.ContainsKey($Name) -and (Test-OwnedProcess $state[$Name] $Marker)) { return }
    if ($state.ContainsKey($Name)) { $state.Remove($Name) }
    $argumentList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Script) + $Arguments
    $windowStyle = if ($Interactive) { 'Normal' } else { 'Hidden' }
    $process = Start-Process -FilePath 'powershell.exe' -ArgumentList $argumentList -WindowStyle $windowStyle -PassThru
    $identity = Get-ProcessIdentity $process.Id
    if ($null -eq $identity) {
        Invoke-TaskKill -ProcessId $process.Id -Force | Out-Null
        throw 'The started component process identity could not be proven.'
    }
    $state[$Name] = @{ pid = $process.Id; process_created_utc = $identity.created_utc; started_utc = [DateTimeOffset]::UtcNow.ToString('o'); owned = $true }
    Write-ControlState $state
}

function Invoke-TaskKill([int]$ProcessId, [switch]$Force) {
    $arguments = @('/PID', [string]$ProcessId)
    if ($Force) { $arguments += '/F' }
    $process = Start-Process -FilePath 'taskkill.exe' -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    return $process.ExitCode
}

function Wait-ForServer([int]$Seconds = 30) {
    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($Seconds)
    while ([DateTimeOffset]::UtcNow -lt $deadline) {
        if (Test-PrefectServerReachable) { return }
        Start-Sleep -Milliseconds 500
    }
    throw 'Prefect server did not become reachable.'
}

function Get-ProvenOwnedProcessTree([hashtable]$Record, [string]$Marker) {
    if (-not (Test-OwnedProcess $Record $Marker)) { return @() }
    $root = Get-ProcessIdentity ([int]$Record.pid)
    if ($null -eq $root) { return @() }
    $tree = @(@{ pid = $root.pid; parent_pid = $root.parent_pid; created_utc = $root.created_utc; depth = 0; is_root = $true })
    $queue = New-Object System.Collections.Queue
    $queue.Enqueue(@($root.pid, 0))
    $seen = @{}
    $seen[$root.pid] = $true
    $rootCreated = [DateTimeOffset]::Parse($root.created_utc)
    while ($queue.Count -gt 0) {
        $entry = $queue.Dequeue()
        $parentId = [int]$entry[0]
        $depth = [int]$entry[1]
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $parentId" -ErrorAction Stop)
        foreach ($child in $children) {
            $childId = [int]$child.ProcessId
            if ($seen.ContainsKey($childId)) { continue }
            if ($null -eq $child.CreationDate) { throw 'Owned process tree identity could not be proven.' }
            $childCreated = ([DateTimeOffset]$child.CreationDate).ToUniversalTime()
            if ($childCreated -lt $rootCreated) { throw 'Owned process tree ancestry was inconsistent.' }
            $identity = @{ pid = $childId; parent_pid = $parentId; created_utc = $childCreated.ToString('o'); depth = $depth + 1; is_root = $false }
            $tree += $identity
            $seen[$childId] = $true
            $queue.Enqueue(@($childId, $depth + 1))
        }
    }
    foreach ($identity in $tree) {
        if (-not (Test-ProcessIdentity $identity)) { throw 'Owned process tree changed before shutdown.' }
    }
    return $tree
}

function Stop-ProvenProcess([hashtable]$Identity) {
    if (-not (Test-ProcessIdentity $Identity)) { return }
    $exitCode = Invoke-TaskKill -ProcessId ([int]$Identity.pid)
    if ($exitCode -eq 0) {
        Wait-Process -Id ([int]$Identity.pid) -Timeout 5 -ErrorAction SilentlyContinue
        if (-not (Test-ProcessIdentity $Identity)) { return }
    }
    if (-not (Test-ProcessIdentity $Identity)) { return }
    $exitCode = Invoke-TaskKill -ProcessId ([int]$Identity.pid) -Force
    if ($exitCode -ne 0 -and (Test-ProcessIdentity $Identity)) { throw 'Owned process did not stop cleanly.' }
    Wait-Process -Id ([int]$Identity.pid) -Timeout 5 -ErrorAction SilentlyContinue
    if (Test-ProcessIdentity $Identity) { throw 'Owned process did not stop cleanly.' }
}

function Stop-OwnedComponent([string]$Name, [string]$Marker) {
    $state = Read-ControlState
    if (-not $state.ContainsKey($Name)) { return }
    $record = $state[$Name]
    if (Test-OwnedProcess $record $Marker) {
        for ($pass = 0; $pass -lt 10; $pass++) {
            $tree = @(Get-ProvenOwnedProcessTree $record $Marker)
            $descendants = @($tree | Where-Object { -not $_.is_root } | Sort-Object depth -Descending)
            if ($descendants.Count -eq 0) { break }
            foreach ($identity in $descendants) { Stop-ProvenProcess $identity }
        }
        $remaining = @(Get-ProvenOwnedProcessTree $record $Marker)
        if (@($remaining | Where-Object { -not $_.is_root }).Count -ne 0) { throw 'Owned process tree remained active.' }
        if ($remaining.Count -eq 1) { Stop-ProvenProcess $remaining[0] }
    }
    $state.Remove($Name)
    Write-ControlState $state
}

function Start-ControlRoom {
    $service = Get-PostgreSqlService
    if ($service.Status -ne 'Running') { Start-Service -Name $service.Name }
    if (-not (Test-PrefectServerReachable)) {
        Start-OwnedComponent -Name 'server' -Script $postgresLauncher -Arguments @('-Action', 'Server') -Marker 'invoke_prefect_postgresql.ps1'
        Wait-ForServer
    }
    Start-Process 'http://127.0.0.1:4200'
}

function Stop-ControlRoomWorker {
    $state = Read-ControlState
    $ownedWorker = $state.ContainsKey('worker') -and (Test-OwnedProcess $state.worker 'invoke_prefect_mailbox_worker.ps1')
    if (-not $ownedWorker) {
        $recordedOwnedWorkerExited = $state.ContainsKey('worker') -and (Test-RecordedOwnedProcessExited $state.worker)
        if ((Get-ControlPlaneStatus).fresh_online_worker_count -gt 0) {
            if (-not $recordedOwnedWorkerExited) {
                throw 'A fresh worker is active but wrapper ownership cannot be proven.'
            }
            $state.Remove('worker')
            Write-ControlState $state
            return 'worker_already_exited_prefect_heartbeat_settling'
        }
        if ($state.ContainsKey('worker')) {
            $state.Remove('worker')
            Write-ControlState $state
        }
        return 'worker_already_stopped'
    }
    $previousPythonPath = $env:PYTHONPATH
    try {
        $env:PYTHONPATH = $repositoryRoot
        & $python -c "from src.services.mailbox_acceptance_handoff_service import MailboxAcceptanceHandoffService; MailboxAcceptanceHandoffService().cleanup()"
        if ($LASTEXITCODE -ne 0) { throw 'Acceptance handoff cleanup failed.' }
    } finally { $env:PYTHONPATH = $previousPythonPath }
    Stop-OwnedComponent -Name 'worker' -Marker 'invoke_prefect_mailbox_worker.ps1'
    return 'worker_stopped'
}

function Stop-ControlRoomInfrastructure {
    $state = Read-ControlState
    $ownedWorker = $state.ContainsKey('worker') -and (Test-OwnedProcess $state.worker 'invoke_prefect_mailbox_worker.ps1')
    if ($ownedWorker -or (Get-ControlPlaneStatus).fresh_online_worker_count -gt 0) {
        throw 'Stop the worker before control-room maintenance.'
    }
    $serverReachable = Test-PrefectServerReachable
    $ownedServer = $state.ContainsKey('server') -and (Test-OwnedProcess $state.server 'invoke_prefect_postgresql.ps1')
    if ($serverReachable -and -not $ownedServer) {
        throw 'The reachable Prefect server is not wrapper-owned; stop it in its owning terminal.'
    }
    Stop-OwnedComponent -Name 'server' -Marker 'invoke_prefect_postgresql.ps1'
    $service = Get-PostgreSqlService
    if ($service.Status -eq 'Running') { Stop-Service -Name $service.Name }
}

switch ($Action) {
    'Status' {
        Get-ControlPlaneStatus | ConvertTo-Json -Compress
    }
    'StartUI' {
        Start-ControlRoom
        Write-Output 'control_room_started'
    }
    'PrepareRun' {
        $status = Get-ControlPlaneStatus
        if (-not ($status.postgresql_running -and $status.prefect_server_reachable -and (Test-PrefectServerBackendSafe) -and $status.manual_deployment_ready -and (Test-ControlPlaneConfiguration)) -or $status.mailbox_run_conflict -or $status.fresh_online_worker_count -ne 0) {
            throw 'Acceptance preparation control-plane guard failed.'
        }
        Start-OwnedComponent -Name 'worker' -Script $workerLauncher -Arguments @('-PrepareAcceptanceHandoff') -Marker 'invoke_prefect_mailbox_worker.ps1' -Interactive
        $deadline = [DateTimeOffset]::UtcNow.AddSeconds(90)
        while ([DateTimeOffset]::UtcNow -lt $deadline) {
            $state = Read-ControlState
            if (-not $state.ContainsKey('worker') -or -not (Test-OwnedProcess $state.worker 'invoke_prefect_mailbox_worker.ps1')) {
                throw 'Acceptance preparation or worker startup failed.'
            }
            if ((Get-ControlPlaneStatus).fresh_online_worker_count -eq 1) { break }
            Start-Sleep -Milliseconds 500
        }
        if ((Get-ControlPlaneStatus).fresh_online_worker_count -ne 1) { throw 'Prepared worker did not become ready.' }
        Write-Output 'acceptance_preparation_started'
    }
    'RunOnce' {
        $previousPythonPath = $env:PYTHONPATH
        try {
            $env:PYTHONPATH = $repositoryRoot
            & $python $readinessProbe
            if ($LASTEXITCODE -ne 0) { throw 'Mailbox Prefect readiness failed.' }
        } finally { $env:PYTHONPATH = $previousPythonPath }
        $status = Get-ControlPlaneStatus
        if ($status.mailbox_run_conflict -or $status.fresh_online_worker_count -ne 1) { throw 'Run-once conflict guard failed.' }
        & $prefect --profile 'lthhc-local' deployment run $deploymentName --watch
        if ($LASTEXITCODE -ne 0) { throw 'Manual bounded mailbox Prefect run failed.' }
    }
    'StopWorker' {
        Write-Output (Stop-ControlRoomWorker)
    }
    'StopControlRoom' {
        Stop-ControlRoomInfrastructure
        Write-Output 'control_room_stopped'
    }
    'RestartControlRoom' {
        Stop-ControlRoomInfrastructure
        Start-ControlRoom
        Write-Output 'control_room_restarted'
    }
}
