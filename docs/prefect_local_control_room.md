# Prefect Local Control Room

This development checkpoint runs one PHI-safe synthetic flow against a
self-hosted Prefect server. It does not call Microsoft Graph, Smartsheet,
OCR/Paddle, Ollama, patient documents, or the production mailbox workflow.

The server is bound only to `127.0.0.1`. Startup remains manual; do not create
a Windows service, scheduled task, login-start item, firewall rule, or
unattended flow schedule.

## First-time setup

Run each physical line below as one complete PowerShell command. The commands
do not rely on display wrapping or implicit continuation.

```powershell
Set-Location 'C:\Projects\LTHHC-AI-Automation-Platform'
$env:PYTHONIOENCODING = 'UTF-8'
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\prefect.exe version
& .\.venv\Scripts\prefect.exe profile create 'lthhc-local'
& .\.venv\Scripts\prefect.exe --profile 'lthhc-local' config set PREFECT_API_URL='http://127.0.0.1:4200/api' PREFECT_SERVER_ANALYTICS_ENABLED=false PREFECT_SERVER_UI_SHOW_PROMOTIONAL_CONTENT=false PREFECT_SERVER_EPHEMERAL_ENABLED=false PREFECT_LOGGING_LOG_PRINTS=false PREFECT_RESULTS_PERSIST_BY_DEFAULT=false PREFECT_TASKS_DEFAULT_PERSIST_RESULT=false
```

Create the profile only once. On later sessions, use the existing profile.
The profile and default SQLite database are stored under the operator's local
Prefect home, outside this repository.

## Terminal 1: server

```powershell
Set-Location 'C:\Projects\LTHHC-AI-Automation-Platform'
$env:PYTHONIOENCODING = 'UTF-8'
$env:DO_NOT_TRACK = '1'
& .\.venv\Scripts\prefect.exe --profile 'lthhc-local' server start --host 127.0.0.1 --port 4200
```

Leave this terminal open.

## Terminal 2: deployment and worker

The pool creation, concurrency limit, and deployment commands are one-time
registration steps. Starting the worker is required on every manual session.

```powershell
Set-Location 'C:\Projects\LTHHC-AI-Automation-Platform'
$env:PYTHONIOENCODING = 'UTF-8'
$env:DO_NOT_TRACK = '1'
& .\.venv\Scripts\prefect.exe --profile 'lthhc-local' work-pool create 'lthhc-local-process' --type process
& .\.venv\Scripts\prefect.exe --profile 'lthhc-local' work-pool set-concurrency-limit 'lthhc-local-process' 1
& .\.venv\Scripts\prefect.exe --profile 'lthhc-local' deploy --all
& .\.venv\Scripts\prefect.exe --profile 'lthhc-local' worker start --pool 'lthhc-local-process' --type process --name 'lthhc-local-worker' --limit 1 --with-healthcheck
```

Leave the worker command running. On later sessions, skip pool creation and
deployment unless the versioned deployment definition changed.

## Terminal 3: UI and synthetic run

```powershell
Set-Location 'C:\Projects\LTHHC-AI-Automation-Platform'
$env:PYTHONIOENCODING = 'UTF-8'
$env:DO_NOT_TRACK = '1'
Start-Process 'http://127.0.0.1:4200'
& .\.venv\Scripts\prefect.exe --profile 'lthhc-local' deployment run 'lthhc-phi-safe-control-room/phi-safe-local' --watch
```

In the UI, confirm that the work pool is ready, the worker has a recent poll,
and one flow with one task completed. Only fixed synthetic names, statuses,
timestamps, durations, attempt counts, and the retryable boolean are expected.

## Clean shutdown

1. Wait for the synthetic run to reach a terminal state.
2. Press `Ctrl+C` in the worker terminal.
3. Press `Ctrl+C` in the server terminal.
4. Close the UI tab.

Keep the SQLite run history for later local inspection.

## Development limitation

Prefect 3.8.4 completed the synthetic process-worker runs and served healthy
UI, API, and worker-health endpoints on this Windows host. During worker
polling, its server also emitted non-fatal SQLite `database is locked` errors
from deployment-readiness updates. The configured run still reached
`Completed`, but this is not clean evidence for always-on production use.

SQLite remains acceptable only for this manual development checkpoint. Do not
enable unattended schedules or production mailbox work until the lock behavior
is resolved or a separately reviewed PostgreSQL deployment is accepted. Redis,
Docker, and PostgreSQL are not introduced by this checkpoint.
