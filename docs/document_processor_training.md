# Document Processor Training

Document Processor Training is the separate Prefect-visible correction and
approval service for the pre-production training period. Smartsheet remains
the reviewer interface. Prefect provides PHI-safe technical visibility only.

## Service operation

The parameterless `document-processor-training` deployment runs in the
`lthhc-dp-training-process` pool with concurrency one and `CANCEL_NEW`. It has
no server-side schedule or automation and does not start after reboot. The
operator commands are:

```powershell
startdptraining
statusdptraining
stopdptraining
```

This runtime owns only its dedicated worker and bounded poll loop. Starting or
stopping it does not start or stop the live Document Processor, PostgreSQL, or
the Prefect control room.

The protected-local `DP_TRAINING_MODE` capability gate has four values:

- `schema_only` validates column metadata and reads no row or comment content.
- `read_only` discovers flagged cases, checkpoints comments, and analyzes them
  locally without writing Smartsheet.
- `proposal_write` also permits the four workflow-owned Smartsheet fields.
- `approval_dispatch` also permits one approval-gated bounded Codex attempt.

The mode must be explicitly present and valid; a missing or invalid value fails
closed instead of silently defaulting to `schema_only`. The complete capability
snapshot is frozen when `startdptraining` succeeds. Changing the mode or either
gate while the service is running causes a safe runtime mismatch until the
operator runs `stopdptraining` and `startdptraining` again. Advancing a
production capability mode requires a separate controlled acceptance.
`proposal_write` and `approval_dispatch`
also require the exact protected-local
`DP_TRAINING_ALLOW_SMARTSHEET_WRITES=true` gate. `approval_dispatch` further
requires `DP_TRAINING_ALLOW_CODEX_DISPATCH=true`. These gates default disabled.
The mode and gates are never Prefect parameters or deployment job variables.
Only their PHI-safe mode/fingerprint handshake is inherited by the owned worker.

Promoting an unchanged case from `read_only` to `proposal_write` publishes the
single durable validated proposal generation; it does not analyze the same
input again. Exact readback makes later unchanged cycles reconciliation-only.
`proposal_write` never creates an implementation authorization or job, even if
an approval checkbox is already selected. Historical acceptance cases may be
durably marked implementation-blocked and display fixed current-state/retest
guidance while retaining the same proposal generation.

## Smartsheet ownership

There are seven correction columns plus the existing row Conversations area.

| Field | Owner | Allowed service behavior |
| --- | --- | --- |
| AI Correction | Human | Document Processor initializes `false` only on a brand-new row; DP Training never changes it. |
| AI Proposed Correction | DP Training | Writes the current locally analyzed proposal. |
| AI Correction Type | DP Training | Writes one controlled taxonomy value. |
| Approve AI Correction | Human | DP Training reads a current false-to-true edge and never changes it. |
| AI Correction Status | DP Training | Writes the visible correction lifecycle state. |
| Approve AI Resolution | Human | DP Training reads a current false-to-true edge and never changes it. |
| AI Resolution Result | DP Training | Writes a reviewer-readable implementation, waiting, or retest result. |
| Conversations/comments | Human | DP Training reads text and metadata incrementally; it never writes comments or reads comment attachments. |

The result column is exactly `AI Resolution Result`. There is no
`AI Correction Result` column.

## Reviewer workflow and approval generations

The reviewer checks `AI Correction` and adds a row comment. DP Training reads
the entire current row conversation in stable pages, ignores attachments, and
compares a protected digest with the last checkpoint. An unchanged checkpoint
is not analyzed twice. An edited, added, or deleted comment creates a new input
generation on the same durable correction case.

After local analysis, the service writes `Analysis Ready` or
`Needs More Information`. Analysis contract v2 separates whether the desired
business behavior is clear from whether its technical implementation layer is
known. A clear proposal may be `Analysis Ready` with a protected technical
disposition of `Needs Investigation`. `Needs More Information` is reserved for
missing, materially ambiguous, or conflicting reviewer intent. An external
authoritative dependency uses `Requires External System`.

The full conversation remains protected audit history, but the analyzer gets
prior reviewer feedback and the latest/current reviewer feedback as distinct
inputs. A coherent latest clarification may narrow or correct earlier intent.
An old AI proposal is never reviewer evidence. The visible correction type is
the deterministic primary symptom; related types remain protected locally.

`Approve AI Correction` authorizes only a
false-to-true edge observed for the exact current proposal generation, text,
type, and comment checkpoint. If the proposal or comments change while the
checkbox remains true, the old approval is stale. The approver must uncheck it
and later check it again for the new generation. The service never clears it.

One valid approval permits one bounded Codex process. A repository conflict or
unavailable runtime does not consume the implementation attempt. Once the
process starts, the generation is consumed and cannot retry automatically.
Only a revised proposal and a new human approval edge can authorize another
attempt.

A successful implementation writes a safe result and `Retest Required`.
Tests or a commit do not resolve the case. `Approve AI Resolution` must produce
a current false-to-true edge for the exact result generation and unchanged
comment checkpoint. A new comment reopens the same case and invalidates stale
approval. External dependencies and unresolved business questions use
`Requires External System`, `Needs More Information`, or
`Cannot Resolve Yet` rather than guessing.

## Protected and PHI-safe boundaries

Row context, comment text, comment metadata, proposals, and internal row
references stay in current-user DPAPI-sealed files under the ignored
`data/smartsheet_feedback/` boundary. They are not Prefect parameters, task
names, state messages, artifacts, ordinary logs, Git, tracker data, or project
continuity.

The local Ollama provider has no tools. Comments are untrusted evidence, not
instructions. Its output is constrained to approved fields, correction types,
behavior codes, and subsystem hypotheses, then deterministically validated.
Invalid output becomes `Needs Investigation`.

Analysis contract version and shared business-context version are stored with
each protected proposal. One unchanged active case created under an older
version may be reanalyzed once under the current versions, using the same
durable case identity and comment checkpoint. That creates one new proposal
generation, invalidates prior approval baselines, and becomes idempotent on the
next unchanged cycle. `proposal_write` remains incapable of Codex dispatch.

Codex receives only an opaque task digest, proposal generation, business and
analysis contract versions, controlled primary/related types, controlled
business concepts/layers, a fixed behavior-code description, and synthetic
regression requirements. It must inspect whether deterministic code, shared
business context, taxonomy, prompt rendering, mapping, or reference data is the
durable generalized layer. It never receives row IDs, comments, documents, OCR
text, filenames, patient values, or protected paths. The
dispatcher requires a clean synchronized repository, a global implementation
lock, one process with a bounded runtime, all test/tracker/Git gates, and a
verified pushed commit. It never resumes or retries a failed attempt and never
discards a partial workspace.

## Reviewer queue and notifications

Create a Smartsheet report named `AI Correction Queue` using the existing
sheet as its source and this filter:

```text
AI Correction = checked
AND AI Correction Status != Resolved
```

The report is a view, not a source of truth. Smartsheet-native notifications
may be configured for transitions to `Analysis Ready`, `Retest Required`, and
`Requires External System`. Notification subjects and bodies should contain
only the fixed status and an instruction to open the queue; do not include row
values, filenames, attachment names, comments, or patient information.

`statusdptraining` distinguishes the configured and runtime/effective mode and
shows whether they match. It otherwise exposes only runtime ownership,
deployment/pool readiness, polling state, safe timestamps, consecutive
failures, and aggregate case counts. Normal reviewers do not need PowerShell,
Prefect, Codex, ChatGPT, or repository access.
