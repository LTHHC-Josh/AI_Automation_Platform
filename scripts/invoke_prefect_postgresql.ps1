[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('UpgradeDryRun', 'Upgrade', 'Server')]
    [string] $Action
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plainPassword = $null
$connectionUrl = $null
try {
    if ($env:PREFECT_SERVER_DATABASE_CONNECTION_URL -or $env:PREFECT_API_DATABASE_CONNECTION_URL) {
        throw 'Refusing to run with an inherited Prefect database connection setting.'
    }

    $secretPath = Join-Path $env:LOCALAPPDATA 'LTHHC\Prefect\postgres-password.txt'
    if (-not (Test-Path -LiteralPath $secretPath -PathType Leaf)) {
        throw 'The current-user Prefect PostgreSQL secret is not configured.'
    }
    $ciphertext = [IO.File]::ReadAllText($secretPath, [Text.Encoding]::UTF8).Trim()
    if ([string]::IsNullOrWhiteSpace($ciphertext)) {
        throw 'The current-user Prefect PostgreSQL secret is invalid.'
    }
    $securePassword = ConvertTo-SecureString -String $ciphertext
    $plainPassword = [Net.NetworkCredential]::new('', $securePassword).Password
    $connectionUrl = "postgresql+asyncpg://prefect_server:$plainPassword@localhost:5432/prefect_control_plane"
    $env:PREFECT_SERVER_DATABASE_CONNECTION_URL = $connectionUrl

    $prefect = Join-Path $PSScriptRoot '..\.venv\Scripts\prefect.exe'
    if (-not (Test-Path -LiteralPath $prefect -PathType Leaf)) {
        throw 'The repository Prefect executable was not found.'
    }
    switch ($Action) {
        'UpgradeDryRun' { & $prefect --profile 'lthhc-postgres-server' server database upgrade --dry-run -y }
        'Upgrade' { & $prefect --profile 'lthhc-postgres-server' server database upgrade -y }
        'Server' {
            & $prefect --profile 'lthhc-postgres-server' version
            if ($LASTEXITCODE -ne 0) {
                throw 'Prefect database-version verification failed.'
            }
            & $prefect --profile 'lthhc-postgres-server' server start --host 127.0.0.1 --port 4200
        }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Prefect action failed with exit code $LASTEXITCODE."
    }
} finally {
    Remove-Item Env:PREFECT_SERVER_DATABASE_CONNECTION_URL -ErrorAction SilentlyContinue
    Remove-Item Env:PREFECT_API_DATABASE_CONNECTION_URL -ErrorAction SilentlyContinue
    Remove-Variable securePassword,ciphertext -ErrorAction SilentlyContinue
    $plainPassword = $null
    $connectionUrl = $null
    Remove-Variable plainPassword,connectionUrl -ErrorAction SilentlyContinue
}
