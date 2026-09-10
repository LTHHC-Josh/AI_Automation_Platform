# Program Compliance — pilot operation

## Reviewer workflow

Use Program Compliance in LT Automation Platform. Record Type separates Requirements,
Actionable Changes, Questions, Source Health, Coverage, Reference and Control rows.
TEST rows are synthetic acceptance examples, never official regulatory changes.

Open Source Section/Link and read Evidence / Before and After. Enter Applicability
Decision, Owner, Review Status, Decision Notes, Internal Target Date and Completion
Evidence as appropriate. Copy the displayed Current Revision value into Reviewed
Revision when the review of that version is complete. Do not use a formula that copies
Current Revision automatically: that would acknowledge future unseen changes.
Review Needed remains checked for a different or blank acknowledgment. System updates
preserve human fields. Complete describes the prior recorded human action, not automatic
compliance certification; a new revision can require review alongside that status.

The service-scope Question consolidates uncertainty. Answer the requested contracted and
active service lists in Decision Notes. After the system presents those proposed facts
with a new Current Revision, copy that revision into Reviewed Revision to confirm them.
An acknowledgment of the earlier question cannot silently approve new facts. No service is
excluded based on current staffing. Policy coverage remains Coverage Not Assessed.

On the Check Now Control row, enter a unique request label in Check Now Request.
While enabled, the next control sync reserves one bounded check and records its result.
This does not start a disabled service. Source-health failures remain separate from
successful no-change checks. The sheet is the actionable notification queue; no email,
SMS or regulatory submission automation is configured.

## Operator commands and activation boundary

Run from the repository with its .venv Python interpreter:

```
python -m src.program_compliance status
python -m src.program_compliance setup
python -m src.program_compliance check --discover
python -m src.program_compliance check --analyze
python -m src.program_compliance sync
python -m src.program_compliance backup
python -m src.program_compliance tick
python -m src.program_compliance start --minutes 60
python -m src.program_compliance stop
```

The real operator uses .venv/Scripts/python.exe, not an unrelated system interpreter.
Setup reconciles the single named sheet and its expected columns; it does not overwrite
an incompatible existing sheet. Credential acquisition reads the existing approved
environment locally without printing or changing it. Stored sheet identity has no default
fallback to any document or tracker sheet. Program state is under the owner's local
application-data LTHHC/ProgramCompliance directory, outside Git and DP state.

The checked-in default remains disabled; the owner's runtime schedule is explicitly activated with
`python -m src.program_compliance schedule --enable` after sharing verification. This registers the
owned LTHHC-ProgramCompliance task on quarter-hour boundaries. Daily source checks trigger at
01:00 America/Chicago; Sunday at 01:00 also requests broader discovery. Smartsheet synchronization
triggers every 15 minutes. These are trigger times, not exclusive windows. Work is bounded and
incremental; an already-running tick is not duplicated, and overdue daily/sync work catches up on the
next available tick. The scheduler's 90-minute ceiling accommodates queued admission plus bounded work.

The task runs while the user is logged in, with no boot/logon trigger. `python -m
src.program_compliance schedule` disables only this owned schedule; incompatible tasks are not
replaced. Optional manually started service launches remain finite (up to 24 hours). Stop remains
cooperative and Compliance-owned. Neither command starts/stops DP or Training.

Actual inference uses the shared LOCALAPPDATA/LTHHC/InferenceQueue SQLite metadata queue. DP has
priority, limited to three consecutive grants while Training or Compliance waits. Background requests
use arrival order. Only the active chat request owns capacity; an idle worker cannot block Compliance.
The queue stores identities, ownership and timing, never prompts, model responses or service memory.
New worker processes must load the updated transport. Direct external Ollama clients are outside this
platform's queue and must not be used to bypass it.

A timed-out, incomplete or orphaned active request blocks further inference until its server-side
completion is established. Never delete its reservation because a process is dead or a lease is old:
Ollama may still be generating. Do not restart Ollama automatically. Confirm outstanding server work
has ended and coordinate explicit recovery before clearing an uncertain reservation. Waiting requests
time out after 30 minutes; that is an admission failure, not a repeated inference. Compliance records
bounded retry backoff for admission timeout. Queue uncertainty requires operator attention.

## Recovery

Source fetches use bounded retries, download/time limits and prevalidated pinned public
IP connections with TLS validated for the official hostname. Every redirect is checked.
Raw snapshots are content-addressed; empty/failed parsing retains the prior valid version.
Public PDFs use a bounded subprocess, not a DP OCR worker. Missing cross-reference context
blocks its own analysis and remains visible as a coverage issue.

Each analysis is reserved before inference. Valid results are reused. Invalid/interrupted
results remain for diagnosis rather than blind model replay. Known transient local capacity
or transport failures have at most three attempts with increasing persisted backoff.
Unknown API contracts, incomplete output and ungrounded results do not become findings.

Outbound intents are saved before requests. A lost response reconciles the exact stable
Finding Key and revision. One match is reused; duplicates, missing previously bound rows
or unavailable reconciliation are blocked. Never delete an uncertain intent to force a
new row. Fix/reconcile the existing intent. Blank/null sheet cells compare equivalently.

Backup uses SQLite's backup API and copies all immutable snapshots with a digest manifest.
Store.restore validates schema, database integrity and every snapshot into a new directory;
it refuses to overwrite an existing destination. Restore acceptance uses isolated state.
Do not delete snapshots, events or decision history without an approved retention policy.

## Limits

The first operational baseline is section 3500, not the full handbook. Source discovery
and analysis are bounded and incremental. Licensing, contracts, current rule pages and
unretrieved references remain coverage gaps. An extracted quotation establishes evidence
traceability, not legal correctness. Human review remains authoritative for consequential
decisions. No patient data, private policies, regulatory submissions, automatic policy
adoption, other-program implementation or DP learning workflow is part of this service.

### Hidden background execution

The owned task invokes the repository virtual environment's pythonw.exe, which avoids a
console window. The Task Scheduler Hidden flag alone is not relied on to suppress windows.
The original console task's first run exited 0; when the reported blank repository terminal
was investigated, no matching terminal or Compliance process remained. The vanished window could
not be conclusively attributed. A console-free task run then exited 0 with zero repository
terminal windows observed. No terminal
or DP/Training process was stopped. Future manual background starts already use CREATE_NO_WINDOW.
Task exit status and durable Compliance records remain the operational diagnostics.
