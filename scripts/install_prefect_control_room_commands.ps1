[CmdletBinding()]
param(
    [string]$ProfilePath = $PROFILE.CurrentUserAllHosts,
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [switch]$LoadCurrentSession,
    [switch]$SkipExecutionPolicyCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $SkipExecutionPolicyCheck) {
    $effectivePolicy = Get-ExecutionPolicy
    if ($effectivePolicy -eq 'Restricted') {
        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
        $effectivePolicy = Get-ExecutionPolicy
    }
    if ($effectivePolicy -in @('Restricted', 'AllSigned')) {
        throw 'The effective PowerShell execution policy does not permit this current-user profile section.'
    }
}

$resolvedRoot = (Resolve-Path -LiteralPath $RepositoryRoot -ErrorAction Stop).Path
$wrapperPath = Join-Path $resolvedRoot 'scripts\invoke_prefect_control_room.ps1'
if (-not (Test-Path -LiteralPath $wrapperPath -PathType Leaf)) {
    throw 'The verified Prefect control-room wrapper was not found.'
}

$beginMarker = '# BEGIN LTHHC PREFECT CONTROL ROOM COMMANDS'
$endMarker = '# END LTHHC PREFECT CONTROL ROOM COMMANDS'
$escapedWrapperPath = $wrapperPath.Replace("'", "''")
$mappings = [ordered]@{
    startui = 'StartUI'
    status = 'Status'
    preparerun = 'PrepareRun'
    runonce = 'RunOnce'
    stopworker = 'StopWorker'
    startdp = 'StartDP'
    statusdp = 'StatusDP'
    stopdp = 'StopDP'
    startdptraining = 'StartDPTraining'
    statusdptraining = 'StatusDPTraining'
    stopdptraining = 'StopDPTraining'
    restartui = 'RestartControlRoom'
    stopui = 'StopControlRoom'
}

$functionLines = foreach ($mapping in $mappings.GetEnumerator()) {
    "function global:$($mapping.Key) { & '$escapedWrapperPath' -Action '$($mapping.Value)' }"
}
$section = @($beginMarker) + $functionLines + @($endMarker)
$sectionText = $section -join "`n"

$profileDirectory = Split-Path -Parent $ProfilePath
if ([string]::IsNullOrWhiteSpace($profileDirectory)) {
    throw 'The current-user PowerShell profile path is invalid.'
}
New-Item -ItemType Directory -Path $profileDirectory -Force | Out-Null

$existing = if (Test-Path -LiteralPath $ProfilePath -PathType Leaf) {
    [IO.File]::ReadAllText($ProfilePath, [Text.Encoding]::UTF8)
} else { '' }
$pattern = '(?ms)^' + [regex]::Escape($beginMarker) + '.*?^' + [regex]::Escape($endMarker) + '[\r\n]*'
$withoutSection = [regex]::Replace($existing, $pattern, '').TrimEnd("`r", "`n")
$updated = if ([string]::IsNullOrEmpty($withoutSection)) {
    $sectionText + "`n"
} else {
    $withoutSection + "`n`n" + $sectionText + "`n"
}

$temporaryPath = Join-Path $profileDirectory ('.lthhc-profile-' + [Guid]::NewGuid().ToString('N') + '.tmp')
try {
    [IO.File]::WriteAllText($temporaryPath, $updated, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporaryPath -Destination $ProfilePath -Force
} finally {
    Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
}

if ($LoadCurrentSession) {
    Invoke-Expression $sectionText
}

Write-Output 'prefect_control_room_commands_installed'
