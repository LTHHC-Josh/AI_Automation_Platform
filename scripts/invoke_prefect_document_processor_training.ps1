[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$prefect = Join-Path $repositoryRoot '.venv\Scripts\prefect.exe'
$stateDirectory = Join-Path $env:LOCALAPPDATA 'LTHHC\Prefect\control-room'
$readyPath = Join-Path $stateDirectory 'dp-training-ready.json'
$activationPath = Join-Path $stateDirectory 'dp-training-activate.signal'
$stopPath = Join-Path $stateDirectory 'dp-training-stop.signal'
$deploymentName = 'lthhc-dp-training/document-processor-training'
$poolName = 'lthhc-dp-training-process'
$workerName = 'lthhc-dp-training-worker'
$basePollSeconds = 300
$maximumBackoffSeconds = 1800
$startupCheckTimeoutSeconds = 30

if (-not (Test-Path -LiteralPath $python -PathType Leaf) -or -not (Test-Path -LiteralPath $prefect -PathType Leaf)) {
    throw 'The repository DP Training runtime is unavailable.'
}

$previousLocation = Get-Location
$worker = $null
$consecutiveFailures = 0
function Write-DpTrainingStatus([string]$PollingState, $LastCheckUtc, $NextCheckUtc) {
    $status = [ordered]@{
        polling_state = $PollingState
        last_check_utc = $LastCheckUtc
        next_check_utc = $NextCheckUtc
        consecutive_failures = $consecutiveFailures
    }
    $status | ConvertTo-Json -Compress | Set-Content -LiteralPath $readyPath -Encoding ASCII
}

try {
    Set-Location -LiteralPath $repositoryRoot
    $env:PYTHONPATH = $repositoryRoot
    $env:PYTHONIOENCODING = 'UTF-8'
    $env:DO_NOT_TRACK = '1'
    $env:PREFECT_WORKER_WEBSERVER_PORT = '8081'
    $readiness = Start-Process -FilePath $python -ArgumentList @((Join-Path $PSScriptRoot 'check_dp_training_start_readiness.py')) -WindowStyle Hidden -PassThru
    if (-not $readiness.WaitForExit($startupCheckTimeoutSeconds * 1000)) {
        if (-not $readiness.HasExited) { $readiness.Kill(); $readiness.WaitForExit() }
        throw 'DP Training readiness timed out.'
    }
    if ($readiness.ExitCode -ne 0) { throw 'DP Training readiness failed.' }
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
    Remove-Item -LiteralPath $readyPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $activationPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $stopPath -Force -ErrorAction SilentlyContinue
    $workerArguments = @(
        '--profile','lthhc-local','worker','start',
        '--pool',$poolName,'--name',$workerName,'--limit','1',
        '--with-healthcheck','--install-policy','never','--no-create-pool-if-not-found'
    )
    $worker = Start-Process -FilePath $prefect -ArgumentList $workerArguments -WindowStyle Hidden -PassThru
    $activationDeadline = [DateTimeOffset]::UtcNow.AddSeconds(120)
    while (-not (Test-Path -LiteralPath $activationPath -PathType Leaf)) {
        $worker.Refresh()
        if ($worker.HasExited) { throw 'DP Training worker failed.' }
        if ([DateTimeOffset]::UtcNow -ge $activationDeadline) { throw 'DP Training activation timed out.' }
        Start-Sleep -Milliseconds 500
    }
    Write-DpTrainingStatus -PollingState 'waiting' -LastCheckUtc $null -NextCheckUtc ([DateTimeOffset]::UtcNow.ToString('o'))
    while (-not $worker.HasExited) {
        Write-DpTrainingStatus -PollingState 'submitting' -LastCheckUtc ([DateTimeOffset]::UtcNow.ToString('o')) -NextCheckUtc $null
        & $prefect --profile 'lthhc-local' deployment run $deploymentName --watch
        if (Test-Path -LiteralPath $stopPath -PathType Leaf) { break }
        if ($LASTEXITCODE -eq 0) { $consecutiveFailures = 0 } else { $consecutiveFailures++ }
        $multiplier = [Math]::Pow(2, [Math]::Min($consecutiveFailures, 3))
        $waitSeconds = [int][Math]::Min($maximumBackoffSeconds, $basePollSeconds * $multiplier)
        $nextCheck = [DateTimeOffset]::UtcNow.AddSeconds($waitSeconds)
        $stateName = if ($consecutiveFailures -eq 0) { 'waiting' } else { 'backoff' }
        Write-DpTrainingStatus -PollingState $stateName -LastCheckUtc ([DateTimeOffset]::UtcNow.ToString('o')) -NextCheckUtc ($nextCheck.ToString('o'))
        Start-Sleep -Seconds $waitSeconds
        $worker.Refresh()
    }
    if (-not (Test-Path -LiteralPath $stopPath -PathType Leaf)) {
        throw 'DP Training worker exited.'
    }
} finally {
    Remove-Item -LiteralPath $readyPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $activationPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $stopPath -Force -ErrorAction SilentlyContinue
    if ($null -ne $worker -and -not $worker.HasExited) {
        Stop-Process -Id $worker.Id -Force -ErrorAction SilentlyContinue
    }
    Set-Location -LiteralPath $previousLocation
}
