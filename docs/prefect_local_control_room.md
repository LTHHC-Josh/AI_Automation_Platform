# Prefect Local Control Room

This manual development checkpoint runs one PHI-safe synthetic deployment
against a self-hosted Prefect 3.8.4 server whose control-plane database is
native PostgreSQL 17.11-1. It does not call Microsoft Graph, Smartsheet,
OCR/Paddle, Ollama, patient documents, or the dormant mailbox adapter.

The Prefect API/UI and PostgreSQL are bound only to localhost. PostgreSQL,
the Prefect server, and the single process worker remain manually operated.
Do not create a scheduled task, login-start item, firewall rule, unattended
flow schedule, or always-on Windows service configuration.

## One-time native PostgreSQL installation

Run the inspected installer from an elevated repository-root PowerShell
terminal. In the interactive wizard, select port `5432`, choose a unique
administrative password, retain the native server and command-line tools, and
omit optional Stack Builder packages.

```powershell
winget install --id PostgreSQL.PostgreSQL.17 --exact --version 17.11-1 --interactive --source winget --accept-package-agreements --accept-source-agreements
```

Configure the single discovered PostgreSQL installation. The script requires
elevation, prompts securely for the administrative password, creates the
least-privilege `prefect_server` role and owned `prefect_control_plane`
database, and stores only current-user DPAPI ciphertext under
`%LOCALAPPDATA%\LTHHC\Prefect`. It fails closed rather than overwriting an
existing role, database, port, service topology, or secret.

```powershell
& '.\scripts\configure_prefect_postgresql.ps1'
```

Create the password-free server profile once. The existing `lthhc-local`
profile remains the password-free client/worker profile.

```powershell
& '.\.venv\Scripts\prefect.exe' profile create 'lthhc-postgres-server' --from 'lthhc-local'
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-postgres-server' config set 'PREFECT_SERVER_DATABASE_MIGRATE_ON_START=false'
```

Neither profile may contain `PREFECT_SERVER_DATABASE_CONNECTION_URL` or its
compatibility alias. The launcher decrypts the role password and supplies the
canonical setting only to its child process.

## Start PostgreSQL and migrate the fresh control plane

Run each physical line below as one complete PowerShell command.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
$pgServices=@(Get-Service | Where-Object { $_.Name -like 'postgresql*' }); if($pgServices.Count -ne 1){throw "Expected exactly one PostgreSQL service; found $($pgServices.Count)."}; Start-Service -Name $pgServices[0].Name
& '.\scripts\invoke_prefect_postgresql.ps1' -Action 'UpgradeDryRun'
& '.\scripts\invoke_prefect_postgresql.ps1' -Action 'Upgrade'
```

Prefect 3.8.4 has a confirmed upstream offline-dry-run limitation: its
historical `14dc68cc5853` data migration dereferences a missing offline result
object. `UpgradeDryRun` therefore fails closed on this pinned version without
changing the database. Review that sanitized failure, then use `Upgrade` for
the real migration; normal migration execution was validated successfully.

The prior SQLite database remains untouched under the operator's local
Prefect home as a rollback artifact. Its synthetic history is not migrated.

## Terminal 1: PostgreSQL-backed server

```powershell
Set-Location 'C:\Projects\LTHHC-AI-Automation-Platform'
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& '.\scripts\invoke_prefect_postgresql.ps1' -Action 'Server'
```

Leave this terminal open. The launcher's `finally` block clears both database
setting names and all plaintext variables after failure or normal shutdown.

## Terminal 2: synthetic objects and one worker

Recreate the synthetic objects in the fresh control plane once:

```powershell
Set-Location 'C:\Projects\LTHHC-AI-Automation-Platform'
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' work-pool create 'lthhc-local-process' --type 'process'
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' work-pool set-concurrency-limit 'lthhc-local-process' 1
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deploy --all
```

Start exactly one worker:

```powershell
$env:PYTHONIOENCODING='UTF-8'; $env:DO_NOT_TRACK='1'; & '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' worker start --pool 'lthhc-local-process' --name 'lthhc-local-worker' --limit 1 --with-healthcheck --install-policy 'never' --no-create-pool-if-not-found
```

## Terminal 3: UI and sequential acceptance

```powershell
Start-Process 'http://127.0.0.1:4200'
1..5 | ForEach-Object { & '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deployment run 'lthhc-phi-safe-control-room/phi-safe-local' --watch; if($LASTEXITCODE -ne 0){throw "Synthetic Prefect run $_ failed."} }
```

Confirm API/UI health, worker health, a ready work pool with concurrency one,
and five sequential completed flows with one task each and zero retries.
Reviewed output must contain only fixed synthetic status/timing metadata and no
SQLite locking, `sqlite3`, database `OperationalError`, unexpected traceback,
PHI, protected path or filename, row ID, or submission key.

## Clean shutdown

Wait for the final run to reach a terminal state, press `Ctrl+C` in the worker
terminal, then press `Ctrl+C` in the server terminal. Stop PostgreSQL:

```powershell
$pgServices=@(Get-Service | Where-Object { $_.Name -like 'postgresql*' }); if($pgServices.Count -ne 1){throw "Expected exactly one PostgreSQL service; found $($pgServices.Count)."}; Stop-Service -Name $pgServices[0].Name
```

PostgreSQL is now the supported local Prefect control-plane database. SQLite
startup guidance is retired. The dormant mailbox adapter remains absent from
`prefect.yaml`; do not register it until the dry-run limitation has a supported
resolution or an explicitly accepted operational exception.
