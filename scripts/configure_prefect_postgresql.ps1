[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-ElevatedSession {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'This configuration script requires an elevated PowerShell session.'
    }
}

function Get-SinglePostgreSqlInstallation {
    $services = @(Get-CimInstance Win32_Service | Where-Object { $_.Name -like 'postgresql*' })
    if ($services.Count -ne 1) {
        throw "Expected exactly one installed PostgreSQL service; found $($services.Count)."
    }

    $service = $services[0]
    $servicePath = [Environment]::ExpandEnvironmentVariables($service.PathName.Trim())
    if ($servicePath.StartsWith('"')) {
        $serviceExecutable = $servicePath.Split('"')[1]
    } else {
        $serviceExecutable = $servicePath.Split(' ')[0]
    }
    $binDirectory = Split-Path -Parent $serviceExecutable
    $psql = Join-Path $binDirectory 'psql.exe'
    if (-not (Test-Path -LiteralPath $psql -PathType Leaf)) {
        throw 'The PostgreSQL service was found, but its matching psql executable was not.'
    }

    [pscustomobject]@{
        Service = $service
        Psql = $psql
    }
}

function Invoke-Psql {
    param(
        [Parameter(Mandatory)] [string] $Psql,
        [Parameter(Mandatory)] [string[]] $Arguments,
        [string] $StandardInput
    )

    if (-not $PSBoundParameters.ContainsKey('StandardInput')) {
        $output = & $Psql @Arguments 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw 'PostgreSQL command failed. Review PostgreSQL server diagnostics locally.'
        }
        return @($output)
    }

    $StandardInput | & $Psql @Arguments 1>$null 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw 'PostgreSQL command failed. Review PostgreSQL server diagnostics locally.'
    }
}

$adminPassword = $null
$rolePassword = $null
$randomNumberGenerator = $null
try {
    Assert-ElevatedSession
    if ($env:PGPASSWORD) {
        throw 'Refusing to run while an inherited PGPASSWORD is set.'
    }

    $installation = Get-SinglePostgreSqlInstallation
    $serviceName = $installation.Service.Name
    Set-Service -Name $serviceName -StartupType Manual
    if ((Get-Service -Name $serviceName).Status -ne 'Running') {
        Start-Service -Name $serviceName
    }

    $secretPath = Join-Path $env:LOCALAPPDATA 'LTHHC\Prefect\postgres-password.txt'
    if (Test-Path -LiteralPath $secretPath) {
        throw 'Refusing to overwrite the existing Prefect PostgreSQL secret.'
    }

    $secureAdminPassword = Read-Host 'PostgreSQL administrative password' -AsSecureString
    $adminPassword = [Net.NetworkCredential]::new('', $secureAdminPassword).Password
    if ([string]::IsNullOrWhiteSpace($adminPassword)) {
        throw 'The PostgreSQL administrative password cannot be empty.'
    }
    $env:PGPASSWORD = $adminPassword

    $baseArguments = @('-X', '-q', '-v', 'ON_ERROR_STOP=1', '-h', 'localhost', '-p', '5432', '-U', 'postgres', '-d', 'postgres')
    Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-c', "ALTER SYSTEM SET listen_addresses = 'localhost';"))
    Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-c', "ALTER SYSTEM SET port = '5432';"))
    Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-c', "ALTER SYSTEM SET password_encryption = 'scram-sha-256';"))
    Restart-Service -Name $serviceName

    $effectiveOutput = @(Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-At', '-c', "SELECT current_setting('listen_addresses') || '|' || current_setting('port') || '|' || current_setting('password_encryption');")))
    $effectiveLines = @($effectiveOutput | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
    if ($effectiveLines -notcontains 'localhost|5432|scram-sha-256') {
        throw 'PostgreSQL effective network or password-encryption settings are incompatible.'
    }

    $unsafeHbaCount = @(Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-At', '-c', "SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL OR (type LIKE 'host%' AND (address IS NULL OR address NOT IN ('127.0.0.1','::1') OR netmask NOT IN ('255.255.255.255','ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff')));")))
    if (@($unsafeHbaCount | ForEach-Object { "$_".Trim() }) -notcontains '0') {
        throw 'PostgreSQL pg_hba.conf contains an invalid or non-loopback host rule.'
    }

    $roleCount = @(Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-At', '-c', "SELECT count(*) FROM pg_roles WHERE rolname = 'prefect_server';")))
    $databaseCount = @(Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-At', '-c', "SELECT count(*) FROM pg_database WHERE datname = 'prefect_control_plane';")))
    if (@($roleCount | ForEach-Object { "$_".Trim() }) -notcontains '0' -or @($databaseCount | ForEach-Object { "$_".Trim() }) -notcontains '0') {
        throw 'Refusing to overwrite an existing Prefect PostgreSQL role or database.'
    }

    $randomBytes = New-Object byte[] 32
    $randomNumberGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
    $randomNumberGenerator.GetBytes($randomBytes)
    $rolePassword = ([BitConverter]::ToString($randomBytes) -replace '-', '').ToLowerInvariant()
    Invoke-Psql -Psql $installation.Psql -Arguments $baseArguments -StandardInput "CREATE ROLE prefect_server LOGIN PASSWORD '$rolePassword' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;"
    Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-c', 'CREATE DATABASE prefect_control_plane OWNER prefect_server;'))

    $roleFlags = @(Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-At', '-c', "SELECT CASE WHEN rolcanlogin THEN '1' ELSE '0' END || '|' || CASE WHEN rolsuper THEN '1' ELSE '0' END || '|' || CASE WHEN rolcreatedb THEN '1' ELSE '0' END || '|' || CASE WHEN rolcreaterole THEN '1' ELSE '0' END || '|' || CASE WHEN rolreplication THEN '1' ELSE '0' END FROM pg_roles WHERE rolname = 'prefect_server';")))
    $databaseOwner = @(Invoke-Psql -Psql $installation.Psql -Arguments ($baseArguments + @('-At', '-c', "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = 'prefect_control_plane';")))
    if (@($roleFlags | ForEach-Object { "$_".Trim() }) -notcontains '1|0|0|0|0' -or @($databaseOwner | ForEach-Object { "$_".Trim() }) -notcontains 'prefect_server') {
        throw 'The created Prefect PostgreSQL role or database failed privilege validation.'
    }

    $secretDirectory = Split-Path -Parent $secretPath
    [void](New-Item -ItemType Directory -Path $secretDirectory -Force)
    $secureRolePassword = ConvertTo-SecureString -String $rolePassword -AsPlainText -Force
    $ciphertext = ConvertFrom-SecureString -SecureString $secureRolePassword
    [IO.File]::WriteAllText($secretPath, $ciphertext + "`n", [Text.UTF8Encoding]::new($false))
    Write-Host 'PostgreSQL Prefect control-plane configuration completed.'
} finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    if ($randomNumberGenerator) {
        $randomNumberGenerator.Dispose()
    }
    Remove-Variable secureAdminPassword,secureRolePassword,ciphertext,randomBytes,randomNumberGenerator -ErrorAction SilentlyContinue
    $adminPassword = $null
    $rolePassword = $null
    Remove-Variable adminPassword,rolePassword -ErrorAction SilentlyContinue
}
