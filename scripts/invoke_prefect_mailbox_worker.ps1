[CmdletBinding()]
param(
    [switch]$PrepareAcceptanceHandoff
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$prefect = Join-Path $repositoryRoot '.venv\Scripts\prefect.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf) -or -not (Test-Path -LiteralPath $prefect -PathType Leaf)) {
    throw 'The repository worker runtime is unavailable.'
}

$previousLocation = Get-Location
try {
    Set-Location -LiteralPath $repositoryRoot
    $env:PYTHONPATH = $repositoryRoot
    $env:PYTHONIOENCODING = 'UTF-8'
    $env:DO_NOT_TRACK = '1'

    & $python (Join-Path $PSScriptRoot 'check_mailbox_worker_auth_readiness.py')
    if ($LASTEXITCODE -ne 0) {
        throw 'Worker authentication readiness failed.'
    }

    if ($PrepareAcceptanceHandoff) {
        & $python (Join-Path $PSScriptRoot 'prepare_mailbox_acceptance_handoff.py')
        if ($LASTEXITCODE -ne 0) {
            throw 'Mailbox acceptance handoff preparation failed.'
        }
    }

    & $prefect --profile 'lthhc-local' worker start --pool 'lthhc-local-process' --name 'lthhc-local-worker' --limit 1 --with-healthcheck --install-policy 'never' --no-create-pool-if-not-found
    if ($LASTEXITCODE -ne 0) {
        throw 'Prefect mailbox worker failed.'
    }
} finally {
    if ($PrepareAcceptanceHandoff) {
        & $python -c "from src.services.mailbox_acceptance_handoff_service import MailboxAcceptanceHandoffService; MailboxAcceptanceHandoffService().cleanup()"
    }
    Set-Location -LiteralPath $previousLocation
}
