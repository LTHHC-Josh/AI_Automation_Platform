# Prefect Local Control Room

This local control room contains one PHI-safe synthetic deployment, one
manual-only bounded mailbox deployment, one inactive-by-default unattended
mailbox deployment, and one inactive-by-default Document Processor Training
deployment against a
self-hosted Prefect 3.8.4 server whose control-plane database is native
PostgreSQL 17.11-1. Registering or inspecting the mailbox deployment does not
execute it. Microsoft Graph, Smartsheet, OCR/Paddle, Ollama, patient documents,
and the mailbox application remain behind a separate explicit authorization.

The Prefect API/UI and PostgreSQL are bound only to localhost. PostgreSQL,
the Prefect server, and the single process worker remain operator controlled.
Do not create a Windows scheduled task, login-start item, firewall rule, or
always-on Windows service configuration.

## Routine operator workflow

### Daily commands

Install the current-user commands once from the repository root. This preserves
the existing PowerShell profile, replaces only the delimited LTHHC section, and
uses current-user `RemoteSigned` only when the effective policy is `Restricted`:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& '.\scripts\install_prefect_control_room_commands.ps1'
```

Open a new PowerShell window, then use these commands from any directory:

```powershell
startui
status
preparerun
runonce
stopworker
startdp
statusdp
stopdp
startdptraining
statusdptraining
stopdptraining
restartui
stopui
```

To make the commands available immediately in the installing window, add
`-LoadCurrentSession` to the one-time install command. No administrator rights,
system PATH change, service, scheduled task, startup task, worker, or flow is
created by installation.

Use the single control-room wrapper from a repository-root PowerShell terminal:

```powershell
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StartUI'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'Status'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'PrepareRun'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'RunOnce'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StopWorker'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StartDP'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StatusDP'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StopDP'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StartDPTraining'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StatusDPTraining'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StopDPTraining'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'StopControlRoom'
& '.\scripts\invoke_prefect_control_room.ps1' -Action 'RestartControlRoom'
```

`Status` is read-only and reports a stable multi-line operator view containing
only PostgreSQL running state, localhost
server reachability, pool readiness, fresh online-worker count, mailbox-run
conflict state, and deployment readiness. Use the wrapper's `-Json` switch for
the unchanged machine-readable field names and values. `StartUI` starts the single
PostgreSQL service only when needed and launches the server through the
existing PostgreSQL launcher only when the localhost API is not already
reachable. It opens the localhost Prefect UI by default and never starts a
worker or deployment.

`PrepareRun` requires the PostgreSQL-backed server, safe pool
configuration, and parameterless deployment to be ready, with zero active
mailbox runs and zero fresh workers. It launches the
existing mailbox worker script with `-PrepareAcceptanceHandoff`, preserving its
same-boundary Graph gate, local popup, DPAPI handoff, exact-candidate proof,
cleanup, and fail-closed behavior. It waits for exactly one fresh worker and
does not invoke the deployment.

`RunOnce` reruns the unchanged boolean-only full readiness probe, requires
exactly one fresh worker and no conflicting mailbox run, then issues exactly
one parameterless watched invocation of
`lthhc-bounded-mailbox/document-processor-manual`.
It has no retry, fallback, custom parameter, run name, tag, or delayed start.

`StopWorker` cleans the acceptance handoff and terminates only the worker PID
whose wrapper ownership and command line are proven. It leaves PostgreSQL and
the Prefect server/UI running. A fresh worker without ownership proof causes a
PHI-safe failure and must be stopped in its owning terminal.

`StartDP` requires the localhost PostgreSQL/Prefect control room, both reviewed
parameterless deployments, zero active manual or unattended runs, and zero
fresh workers. It starts exactly one separately owned unattended launcher. The
wrapper first runs a lightweight PHI-safe startup check for Graph token
acquisition and protected local-state writability. It does not enumerate the
mailbox, initialize Paddle, contact Ollama, or inspect Smartsheet. Only after
that succeeds can the launcher start one worker; the launcher repeats the
boolean-only Graph gate in the worker's process/network boundary before worker
creation, then enters its five-minute polling loop.
It never creates a popup or DPAPI handoff. `StatusDP` is read-only and exposes
the same stable multi-line Yes/No presentation for only ownership,
control-plane/deployment/pool readiness, polling/run state,
safe last/next-check timestamps, consecutive failure count, fresh-worker count,
and a degraded boolean; `-Json` preserves machine-readable output. If one bounded run is active, `StopDP` records an owned
stop request and returns `dp_stop_requested_active_run`. The current bounded run
is not interrupted; the launcher exits after that run reaches a terminal state.
Otherwise it stops only the proven unattended process tree. A missing process
with wrapper ownership state settles cleanly; an unowned or PID-reused process
fails closed.

The operator-owned launcher invokes one parameterless flow, waits for its
terminal result, and normally waits 300 seconds before the next attempt.
Nonzero invocation outcomes use bounded exponential delays of 600, 1200, then
at most 1800 seconds; a successful bounded invocation resets the delay. Each
run inspects the newest ten unread Inbox messages through the existing metadata
rules, deterministically chooses candidate one from the newest-first eligible
list, re-fetches that exact identity from Inbox, and processes at most one
supported document. No eligible candidate is a successful no-op. There is no
fallback after selection. Deployment `CANCEL_NEW`, deployment concurrency one,
pool concurrency one, and worker limit one prevent overlap. A failed unread
candidate can be reconsidered only on a later polling tick; durable job
state, leases, uncertain-write blocks, and submission-key reconciliation remain
authoritative against duplicate business actions.

Graph authentication is compatible with this operator-launched unattended
mode: the existing authenticator is an MSAL confidential-client application
using client credentials and `acquire_token_for_client`, with no interactive
user prompt. Each process can acquire and renew app-only tokens from the
existing ignored environment/configuration boundary. Credentials and tokens
remain absent from Prefect parameters, wrapper state, logs, and tracked files.
If the ignored configuration or outbound authentication path is unavailable
after restart, startup fails before creating the worker with a fixed PHI-safe
failure category. OCR, Ollama, and Smartsheet are deferred until an eligible
document reaches the existing production path, where unavailable dependencies
remain fail-closed and the document remains recoverable.

`StopControlRoom` is maintenance-only. It refuses to proceed while a fresh or
wrapper-owned worker remains, stops only the proven wrapper-owned server, and
then stops the single PostgreSQL service through the documented boundary. It
also fails closed when a reachable server is externally owned.

`RestartControlRoom` applies the same worker and ownership guards, stops the
wrapper-owned server and PostgreSQL, then restarts PostgreSQL, one server, and
the localhost UI. It never starts a worker, prepares a handoff, or invokes a
deployment. Stale or mismatched PIDs are removed without termination. Wrapper
state contains only component names, PIDs, process-creation timestamps, start
timestamps, and ownership booleans
under `%LOCALAPPDATA%\LTHHC\Prefect\control-room`; it is not tracked and
contains no mailbox identity, document data, credential, path, payload, or
destination identifier.

Owned process-tree shutdown validates the root PID, creation identity, launcher
marker, and complete descendant ancestry. It stops validated children before
their parents. Graceful termination is attempted first; Windows `/F` fallback
is allowed only after the same PID/creation identity is immediately revalidated.
Legacy or stale state without creation identity cannot authorize termination.

PostgreSQL and the Prefect server/UI are intended to remain continuously
available on the local AI host; no startup task or service is created. No
server-side Prefect schedule is used, so a stopped worker or Windows reboot
cannot accumulate scheduled flow runs. The
unattended worker does not automatically restart after Windows reboot in this
checkpoint: run `startui`, verify the control room, then run `startdp`. After a
worker crash or ambiguous ownership state, use `statusdp`, then `stopdp` to
settle the owned process state before starting again.

`StartDPTraining` is independent of `StartDP`. It requires the separate
`lthhc-dp-training-process` process pool, the parameterless
`lthhc-dp-training/document-processor-training` deployment, concurrency one,
`CANCEL_NEW`, zero schedules, and zero active training runs. It starts one
wrapper-owned training worker and repeats bounded five-minute training cycles.
Its health server uses port `8081`, independently of the live worker's default
health port.
The default `schema_only` capability mode reads only destination metadata.
Later `read_only`, `proposal_write`, and `approval_dispatch` modes remain
explicit protected-local configuration choices and are never Prefect
parameters. `StatusDPTraining` exposes only ownership/readiness/polling state,
safe timestamps, failure counts, and aggregate correction counts.
`StopDPTraining` finishes the current bounded cycle and stops only the proven
training process tree. Neither DP command family stops the other, PostgreSQL,
or the Prefect server. A host reboot requires `startdptraining` again.

`StartUI` is primarily for reboot/crash recovery. The worker remains manual:
`PrepareRun` starts the guarded worker/handoff path, `RunOnce` invokes one run,
and `StopWorker` is the routine post-run action. `StopControlRoom` and
`RestartControlRoom` are maintenance actions. One-terminal operation is
supported: the server remains hidden and the worker opens its own interactive
PowerShell window for the existing acceptance popup. The explicit `PrepareRun`
and `RunOnce` actions remain separate. The UI remains a PHI-safe lifecycle
surface, not an approval or PHI-review surface.

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

## Terminal 2: deployment objects and operator-owned workers

Recreate the synthetic objects in the fresh control plane once:

```powershell
Set-Location 'C:\Projects\LTHHC-AI-Automation-Platform'
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' work-pool create 'lthhc-local-process' --type 'process'
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' work-pool set-concurrency-limit 'lthhc-local-process' 1
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' work-pool create 'lthhc-dp-training-process' --type 'process'
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' work-pool set-concurrency-limit 'lthhc-dp-training-process' 1
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deploy --all
```

For the mailbox registration checkpoint, deploy only the reviewed manual
deployment and inspect the resulting server metadata. These commands do not
create a flow run:

```powershell
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deploy 'src/orchestration/prefect_mailbox_workflow.py:bounded_mailbox_flow' --name 'document-processor-manual' --description 'Manual-only sealed-handoff one-message/one-document acceptance with PHI-safe operational output.' --tag 'manual' --tag 'phi-safe' --pool 'lthhc-local-process' --concurrency-limit 1 --collision-strategy 'CANCEL_NEW' --no-prompt
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deployment inspect 'lthhc-bounded-mailbox/document-processor-manual' --output json
```

The mailbox deployment has no schedule, trigger, or parameters. Its deployment
concurrency is one with `CANCEL_NEW`; the process pool concurrency and worker
limit also remain one. Its flow and task have zero Prefect retries, disabled
print logging, and disabled result persistence. Registration must stop here
until the operator separately authorizes a real dependency preflight and one
mailbox run.

The unattended deployment is also parameterless, has concurrency one with
`CANCEL_NEW`, and has no server-side schedule. Registration does not start a
worker or flow. Confirm its metadata before the first separately authorized
`startdp`:

```powershell
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deployment inspect 'lthhc-unattended-mailbox/document-processor-live' --output json
```

Start exactly one worker:

```powershell
$env:PYTHONIOENCODING='UTF-8'; $env:DO_NOT_TRACK='1'; & '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' worker start --pool 'lthhc-local-process' --name 'lthhc-local-worker' --limit 1 --with-healthcheck --install-policy 'never' --no-create-pool-if-not-found
```

## Terminal 3: UI and sequential acceptance

```powershell
Start-Process 'http://127.0.0.1:4200'
1..5 | ForEach-Object { & '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deployment run 'lthhc-phi-safe-control-room/prefect-control-room-test' --watch; if($LASTEXITCODE -ne 0){throw "Synthetic Prefect run $_ failed."} }
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

When a prior preparation reports `acceptance_no_eligible_candidate`, a
separately authorized metadata-only diagnostic can be run without starting a
worker, displaying the popup, creating a handoff, or triggering Prefect:

```powershell
$previousPythonPath=$env:PYTHONPATH; try { $env:PYTHONPATH=(Get-Location).Path; & '.\.venv\Scripts\python.exe' '.\scripts\prepare_mailbox_acceptance_handoff.py' --diagnostic-only } finally { $env:PYTHONPATH=$previousPythonPath }
```

Its JSON output is limited to eligible count and aggregate message counts for
not-unread state, no supported document, multiple supported documents,
unsupported non-inline document type, and unprovable document count. An
unprovable count also includes aggregate-only allowlisted reason counts for
request, response, item, attachment-type, inline-state, name, continuation-
link, and continuation-request failures. It never outputs identity, sender,
subject, attachment name, filename, continuation URL, Graph payload, or
content.

Use only the documented mailbox worker-launch command below. Its boolean-only Graph
authentication check runs in the same process and network boundary that
launches the worker, and the worker is not started when that boundary cannot
prove authentication readiness.

```powershell
& '.\scripts\invoke_prefect_mailbox_worker.ps1' -PrepareAcceptanceHandoff
```

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

The parameterless manual deployment opens one local acceptance-only popup from
inside its single application task. It inspects only the newest ten unread
Inbox messages through metadata, displays only numbered candidates, UTC
received timestamps, and deterministically proven supported-document counts,
and permits exactly one eligible one-document selection. The selected identity
remains in process memory, is re-fetched through the exact Inbox boundary, and
must still be available, unread, and contain exactly one supported document.
Cancel, close, invalid selection, movement, read-state change, and zero,
multiple, or unprovable document counts fail closed before attachment download,
OCR, Ollama, Smartsheet, or mailbox completion. There is no newest-unread
fallback, Prefect retry, or automatic retrigger. Normal unattended mailbox
enumeration remains unchanged.

```powershell
& '.\.venv\Scripts\prefect.exe' --profile 'lthhc-local' deployment run 'lthhc-bounded-mailbox/document-processor-manual' --watch; if($LASTEXITCODE -ne 0){throw 'Manual bounded mailbox Prefect run failed.'}
```

The UI should show flow `lthhc-bounded-mailbox`, deployment
`document-processor-manual`, one
authoritative `bounded-mailbox-application-run` task, zero Prefect retries,
worker health, native timestamps/durations, and PHI-safe lifecycle child task
runs. The child task-run names expose acceptance handoff, candidate
re-verification, document acquisition, OCR, document classification, subtype
classification, extraction attempt 1 start/completion, validation attempt 1,
retry decision, conditional extraction/validation attempt 2, candidate
selection, aggregate document processing, extraction, deterministic validation, business rules,
Smartsheet write and attachment handling, review determination/state, mailbox
finalization, and workflow completion where the application reaches those
boundaries. Started, completed, failed, skipped, cancelled, passed, and
review-required are semantic status suffixes; the lifecycle recorder itself
does not own or retry business work.

Slow-stage lifecycle parameters additionally expose wall time; real Ollama
total/load/prompt-evaluation/generation durations and prompt/generated token
counts when the provider returns them; selected attempt and retry booleans;
aggregate extraction/validation/document-processing wall time; and selected
existing OCR timing/count diagnostics. Missing provider metrics remain absent.
Lifecycle logs omit unpopulated fields. All parameters remain restricted to
the fixed operational allowlist. The protected handoff identity never
enters Prefect. The authoritative application task also retains its aggregate
log record containing stage, status, failure category, retryable, and aggregate
message/document/write/failure/row-attempt/attachment-attempt/pending/completed
counts. Application
success, including `no_documents`, reaches Completed; application failure
reaches Failed with only the sanitized failure category.

After exact-candidate proof, acquisition skip markers distinguish only fixed
safe causes: `message_already_handled`, `message_attachment_flag_false`, or
`attachment_download_no_candidates`. An exact one-document proof overrides a
contradictory message-level attachment flag and proceeds to the attachment
boundary. If that proven document cannot produce a downloadable candidate,
the message remains unread and the application fails safely rather than
returning successful `no_documents`. Already-handled state remains an
idempotent mark-read reconciliation and does not repeat document processing.

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
