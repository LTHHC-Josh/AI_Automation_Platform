# Prefect Local Control Room

This manual development control room contains one PHI-safe synthetic
deployment and one manual-only bounded mailbox deployment against a
self-hosted Prefect 3.8.4 server whose control-plane database is native
PostgreSQL 17.11-1. Registering or inspecting the mailbox deployment does not
execute it. Microsoft Graph, Smartsheet, OCR/Paddle, Ollama, patient documents,
and the mailbox application remain behind a separate explicit authorization.

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

Prefect 3.8.4 has a confirmed upstream dry-run-only limitation: Alembic offline
execution emits SQL and returns no cursor result, while historical migration
`14dc68cc5853` unconditionally dereferences `result.rowcount`.
`UpgradeDryRun` therefore fails closed on this pinned version without changing
the database. Online migration uses a real PostgreSQL result and completed
successfully. The accepted operational exception requires exactly one database
revision equal to the installed PostgreSQL head `9e9dadc36797`, zero affected
flow/task state-name invariant gaps, and successful synthetic PostgreSQL
acceptance. The exception must be rechecked on every Prefect version change.

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

For the mailbox registration checkpoint, deploy only the reviewed manual
deployment and inspect the resulting server metadata. These commands do not
create a flow run:

```powershell
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deploy 'src/orchestration/prefect_mailbox_workflow.py:bounded_mailbox_flow' --name 'manual-local' --description 'Manual-only bounded mailbox orchestration with PHI-safe operational output.' --tag 'manual' --tag 'phi-safe' --pool 'lthhc-local-process' --concurrency-limit 1 --collision-strategy 'CANCEL_NEW' --no-prompt
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deployment inspect 'lthhc-bounded-mailbox/manual-local' --output json
```

The mailbox deployment has no schedule, trigger, or parameters. Its deployment
concurrency is one with `CANCEL_NEW`; the process pool concurrency and worker
limit also remain one. Its flow and task have zero Prefect retries, disabled
print logging, and disabled result persistence. Registration must stop here
until the operator separately authorizes a real dependency preflight and one
mailbox run.

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

## Separately authorized manual mailbox acceptance

Do not perform this section as part of registration. Before a separately
authorized run, supply the approved submission-key column title through the
worker terminal's process-local environment or ignored local configuration.
Never paste its value into documentation, Prefect parameters, commands, logs,
or tracked files.

The readiness command returns only Graph auth/config, Smartsheet destination,
submission-key column, OCR config/model, Ollama/model, protected local storage,
PostgreSQL/Prefect, and aggregate `all_ready` booleans. It suppresses dependency
output and does not enumerate the mailbox, retrieve a document, run inference,
or perform a business write.

```powershell
$env:PYTHONPATH=(Get-Location).Path; & '.\.venv\Scripts\python.exe' '.\scripts\check_mailbox_prefect_readiness.py'; if($LASTEXITCODE -ne 0){throw 'Mailbox Prefect readiness failed.'}
```

Stop before triggering when any boolean is false; when the configured
submission-key column is missing, invalid, ambiguous, or the wrong type; when
the server, worker, pool, deployment, model, or protected storage is not ready;
when either concurrency limit is not one; when a mailbox run is already
Pending, Scheduled, or Running; or when any schedule, trigger, parameter,
Prefect retry, non-loopback endpoint, inherited database connection setting,
or additional online worker is present. Corrupt, inconsistent, uncertain,
permanently blocked, actively leased, or insufficient-evidence application
state also remains a stop condition and is never made retryable by Prefect.

After every readiness boolean is true and the operator has explicitly
authorized exactly one real run, use this command without parameters, tags,
custom run names, or delayed start options:

```powershell
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deployment run 'lthhc-bounded-mailbox/manual-local' --watch; if($LASTEXITCODE -ne 0){throw 'Manual bounded mailbox Prefect run failed.'}
```

The UI should show flow `lthhc-bounded-mailbox`, deployment `manual-local`, one
`bounded-mailbox-application-run` task, zero Prefect retries, worker health,
native timestamps/durations, and one allowlisted log record containing stage,
status, failure category, retryable, and aggregate message/document/write/
failure/row-attempt/attachment-attempt/pending/completed counts. Application
success, including `no_documents`, reaches Completed; application failure
reaches Failed with only the sanitized failure category.

The UI, state, logs, exceptions, names, and parameters must never expose a
patient/member name, sender, subject, filename or protected path, OCR or source
text, extracted value, row ID, submission key, provider/MCO detail, payload,
credential, token, configured model or endpoint value, or underlying
application exception text. Application idempotency and recovery remain
authoritative. A result with `retryable=false` is not retriggered.

## Clean shutdown

Wait for the final run to reach a terminal state, press `Ctrl+C` in the worker
terminal, then press `Ctrl+C` in the server terminal. Stop PostgreSQL:

```powershell
$pgServices=@(Get-Service | Where-Object { $_.Name -like 'postgresql*' }); if($pgServices.Count -ne 1){throw "Expected exactly one PostgreSQL service; found $($pgServices.Count)."}; Stop-Service -Name $pgServices[0].Name
```

PostgreSQL is now the supported local Prefect control-plane database. SQLite
startup guidance is retired. The mailbox adapter is registered only as the
manual, parameterless deployment described above; it has no schedule or
Prefect retries. The Prefect 3.8.4 dry-run limitation is covered only by the
version-bounded operational exception above and must be rechecked on upgrade.
