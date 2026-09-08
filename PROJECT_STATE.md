# LTHHC A.I. Automation Platform - Project State

## Authority and Scope

This file is the authoritative current-state source for the LTHHC A.I.
Automation Platform. It contains current durable architecture, tested baseline,
limitations, operating rules, version state, and exactly one `CURRENT NEXT
START`.

Source-of-truth order:

1. Git committed source and tests.
2. Confirmed local uncommitted work that has been inspected and preserved.
3. `AGENTS.md` for durable repository safety and execution rules.
4. `PROJECT_STATE.md` for current project truth and the next starting point.
5. `PROJECT_HISTORY.md` for the complete cumulative audit trail.
6. `PROJECT_SMARTSHEET.md` and the `PROJECT_SMARTSHEET` sync model for a
   non-authoritative concise management presentation.

Never store PHI, OCR text, patient/member data, `source_text`, protected
filenames or paths, credentials, secrets, tokens, Smartsheet payload values,
Smartsheet row IDs, model files, or protected cache contents in these project
continuity layers.

## Current Phase and Business Scope

The automated document processor is the current Phase 1 priority. It processes
healthcare intake documents for LT Home Healthcare. MCO, payer, sender, and
source information are context, not document meaning.

The long-term platform may accept other approved Microsoft 365, EHR,
eligibility, and internal-system sources, but those are future adapters into the
shared platform. They are not current implementation priorities.

The current production sequence is:

mailbox intake
-> secure acquisition
-> local OCR/text extraction
-> document classification
-> intake/business subtype reasoning
-> field extraction
-> deterministic validation
-> business rules
-> filename assembly
-> Smartsheet row and attachment
-> review determination
-> mailbox finalization

Human review is a downstream exception workflow. It does not gate a supported,
validated production row write.

## Current Architecture and Safety Invariants

- Classification, extraction, deterministic validation, business rules,
  filename assembly, external writes, and human review remain separate.
- Local-model output is candidate reasoning. Deterministic validation and
  business rules own final production acceptance.
- Classification and extraction use separate local Ollama requests.
- A maximum of two extraction attempts may run. Candidates are validated
  independently and are never merged. The strongest deterministically supported
  candidate wins; ties retain attempt 1.
- Field and service-line `value`, `confidence`, and `source_text` remain together
  inside approved protected processing.
- Missing, unsupported, conflicting, ambiguous, invalid, low-confidence, or
  guessed values become null/unknown plus specific review where applicable.
- Optional absence remains blank with blank confidence and no review noise.
- Confidence never defaults automatically to 1.0. Category confidence,
  subtype certainty, extraction confidence, and service-line confidence remain
  separate.
- Requested visits are not approved visits. Units are not visits, sessions,
  equipment, or approval. Quantity, codes, dates, and generic status cannot prove
  approval.
- Top-level modifier ownership requires direct deterministic support.
- Payer/sender/source context cannot establish document type, subtype, service,
  modifier, or other business meaning.
- PHI may reach Smartsheet only through explicit approved mappings. Internal
  diagnostics, protected paths, cache metadata, credentials, tokens, and
  unrelated fields never pass through wholesale.

## Shared Business Context and Taxonomy

The repo-owned, PHI-free `DocumentProcessorBusinessContext` is the shared model
context source. Current `business_context_version` is 1. Role-specific views are
rendered for live classification, extraction, structural learning, intake
naming, and DP Training. Prompt context explains constraints; deterministic code
remains authoritative.

Confirmed top-level business families/tokens are:

- AUTH
- 2067
- POC
- VOE
- REFERRAL
- ASSESSMENT
- APPROVAL LETTER
- ADVERSE DETERMINATION LETTER
- ACK
- 3052
- PROVIDER NEWS
- CLINICAL PRACTICE GUIDELINES
- BAD FAX
- SPAM

VOE means Verification of Employment. Unsupported legacy labels are not silently
mapped into this taxonomy.

Approved AUTH intake naming tokens are:

- AUTH INIT
- AUTH NO CHANGE
- AUTH INCREASE
- AUTH DECREASE
- AUTH TERM
- AUTH STUB
- AUTH INBOUND
- AUTH GAP FILL
- AUTH NEW SVS
- AUTH MOD CHANGE
- AUTH RPM
- AUTH READMIT
- AUTH TASKS ADDED
- AUTH RESUME SVS

`INBOUND AUTH` normalizes to `AUTH INBOUND`. Labels are not merged unless their
business meaning is proven identical.

AUTH INIT may depend on authoritative external client/service context and cannot
be inferred from document text alone. Unknown applicable subtype is valid and
may require review. Other supported subtypes, including AUTH DECREASE, may be
resolved from explicit validated document evidence.

## Field, Quantity, Review, and Filename Semantics

Final field states are `not_present`, `missing_required`, `accepted`,
`low_confidence`, `unsupported`, `conflicting`, `ambiguous`, and `invalid`.
Production values and confidences reflect final validated state rather than raw
model confidence.

For a supported quantity, an explicit supported unit is preserved. With no
explicit unit, Hours is the current business default. The provenance remains
`explicit_document_evidence` or `business_default_hours`. Unsupported,
ambiguous, or conflicting explicit units require review. Unit handling never
implies approval or visit/session meaning.

Operator-facing review reasons use `<Business/Smartsheet Field>: <Problem>` and
derive from final validated state. Filename placeholders or reference-token
lookup failure do not automatically create extraction-review reasons.

The intake filename convention is:

`<LAST, FIRST [MIDDLE]>_<PAYER>_[SERVICE]_<DOCUMENT TYPE>_<DATE[-DATE]>.<EXT>`

Filename outcomes are `complete_business`, `partial_business`, and
`technical_fallback`. Approved placeholders are `[PAYER]`, `[SERVICE]`,
`[DOCUMENT TYPE]`, `[SUBTYPE]`, and `[DATE]`.

- Optional absent components are omitted.
- Meaningful unresolved components use the approved placeholder when core
  identity remains safe.
- A date range is used only when both applicable dates are explicitly and
  deterministically supported. Otherwise the supported single applicable date
  is used. An end date is never manufactured.
- Neither AUTH nor an AUTH subtype inherently requires a date range.
- Accepted payer/service production values remain accepted when their
  authoritative naming token is unresolved; the filename may use a placeholder
  without creating an extraction-review reason.
- The persisted attachment filename is authoritative during recovery and is not
  recomputed.

## Smartsheet Production and Recovery Contract

Smartsheet is the approved production destination, attachment destination,
human-review UI, and DP Training feedback/approval UI.

The production mapper uses explicit approved destinations only. Optional `None`
values are omitted before cell construction. No Smartsheet cell is constructed
without a serialized value. CHECKBOX accepts only booleans; DATE accepts the
validated normalized destination representation; TEXT_NUMBER accepts only
explicitly supported finite scalar text/numeric values. Containers,
dictionaries, arbitrary objects, non-finite numerics, and unsupported date or
Decimal objects fail locally.

Durable row-write request contract version 2 and mailbox job state schema version
3 require typed mapping/schema validation, duplicate-destination rejection,
writable/system-column checks, and structural request safety before reserving an
external attempt. An older durable failure may re-arm once under a newer validated
contract while reusing the same job identity. Exact reconciliation precedes any
future create: zero matches may permit one leased create, one match reconciles,
and multiple or unavailable reconciliation fails closed. Attachment handling is
blocked until row identity is proven.

API rejection diagnostics retain only a fixed safe category, valid numeric API
code, and HTTP status class. Response body, request payload, values, row IDs,
exception text, tokens, and sensitive response fields are never retained.

## Document Processor Training

DP Training is a distinct Prefect-visible service and the controlled human
correction/approval workflow. The configured protected capability mode is
`proposal_write`; Codex dispatch remains disabled. The last read-only status
check showed the service stopped, its pool and deployment ready, zero fresh
workers, and no degraded state.

Current versions:

- `business_context_version`: 1
- `analysis_contract_version`: 3
- protected correction-case schema version: 3
- sanitized implementation-task schema version: 2

Human-owned inputs are:

- AI Correction
- Approve AI Correction
- Approve AI Resolution
- Smartsheet Conversations/comments

DP Training-owned outputs are:

- AI Proposed Correction
- AI Correction Type
- AI Correction Status
- AI Resolution Result

The live Document Processor initializes AI Correction to false only on a new row
and cannot overwrite correction workflow state. DP Training never sets or clears
human checkboxes or writes comments.

Reviewer comments are untrusted PHI-bearing desired-behavior input. They remain
inside approved Smartsheet/local protected processing, cannot become production
field evidence, cannot invoke tools, and cannot directly form executable Codex
instructions.

Analysis v3 retains prior feedback and a distinct latest clarification. Compatible
requirements accumulate; a newer explicit conflict overrides only the affected
portion. Desired-business-behavior sufficiency is separate from technical root-
cause disposition. Filename corrections use controlled structural components for
canonical document type, payer when applicable, service when applicable, supported
date representation, and unrelated-field exclusion.

`AI Proposed Correction` is a concise deterministic reviewer summary rendered
from that structure. Detailed safety, placeholder, evidence, and implementation
context remain in protected analysis and are reconstructed for a future sanitized
implementation task. A proposal-write cycle cannot create an implementation job,
consume an approval edge, or dispatch Codex.

Dispatch diagnostics retain only allowlisted categories and bounded process exit
codes in protected case state, before workflow-result writes. Schema 1/2 cases
migrate without changing identity, attempts, or consumed approvals. Legacy failed
attempts without retained diagnostics remain `legacy_failure_unavailable`.
Nonzero child exit, startup failure, timeout, missing result, and invalid result
are distinguished without retaining stdout/stderr or exception text. Failed
implementation cycles report `completed_with_failures` and fail the Prefect flow;
the unchanged following cycle does not retry the consumed approval.

One row maps to one durable correction case. Comment/input revisions create a new
generation on the same identity, invalidate stale approval baselines, and become
idempotent on unchanged readback. Approval-dispatch capability remains a later
separately controlled production step.

## Prefect and Operator Runtime

The local control room uses self-hosted Prefect 3.8.4 with PostgreSQL 17.11.
Result persistence, flow/task retries, schedules, automations, and silent reboot
startup remain disabled unless separately approved.

Prefect 3.8.4 has a version-bounded upstream offline dry-run-only defect:
historical migration `14dc68cc5853` dereferences an unavailable offline result.
Online migration is unaffected. The database revision equals the sole installed
PostgreSQL head `9e9dadc36797`; this exception must be rechecked on every Prefect
version change.

Current deployments and pools are:

- `document-processor-live` / `lthhc-unattended-mailbox` ->
  `lthhc-dp-live-process`
- `document-processor-manual` / `lthhc-bounded-mailbox` ->
  `lthhc-local-process`
- `document-processor-training` / `lthhc-dp-training` ->
  `lthhc-dp-training-process`
- `prefect-control-room-test` remains on `lthhc-local-process`

Deployments are parameterless, concurrency one with `CANCEL_NEW`, and have no
server schedule. Live DP, Manual DP, and DP Training use separate ownership
markers and stop boundaries. DP Training permits one implementation job at a time
initially and never exposes PHI in Prefect parameters, names, logs, artifacts, or
state messages.

Operator commands remain:

- `startui`, `status`, `stopui`
- `startdp`, `statusdp`, `stopdp`
- `preparerun`, `runonce`, `stopworker`
- `startdptraining`, `statusdptraining`, `stopdptraining`

## Current Verified Baseline

- Project continuity is separated into authoritative current state, authoritative
  complete history, and a non-authoritative Smartsheet presentation. Hash checks
  prove the full legacy memory, development journal, and tracker-update payloads
  are preserved in history. The management summary is derived from the latest
  structured history checkpoint and fails closed above 1,800 characters.
- One controlled unattended production recovery reused the existing durable job
  identity under the typed request contract and completed row creation,
  attachment, and mailbox finalization safely.
- The accepted result used the intended business naming behavior, category 2067,
  unknown intake subtype, exact review reason `AI Document Subtype: Unknown`,
  independent classification confidence, blank unavailable optional fields, and
  AI Correction initialized unchecked. Misleading missing/confidence sentinel
  output was absent.
- DP Training read-only acceptance discovered the flagged cases, created/updated
  protected durable state, exposed only safe aggregate counts, and performed no
  workflow-field write or Codex dispatch.
- Analysis v3 synthetic coverage proves compatible clarification merging,
  conditional supported-date representation, AUTH INIT isolation, evidence-only
  production values, exactly-once versioned reanalysis, and unchanged-cycle
  idempotency.
- The reviewer-facing renderer passed focused and affected synthetic/mock,
  business-context, naming, PowerShell 5.1, and isolated Prefect checks. It retains
  detailed protected structure while producing concise Smartsheet text.
- Live, manual, and training Prefect pools/deployments are registered and isolated
  with concurrency one.
- Protected state paths remain ignored and DPAPI-sealed where required.

## Current Limitations and Pending Acceptance

- The subsequent fresh-approval implementation acceptance recorded exactly one
  failed attempt with retained codex_failed / exit 2. The installed CLI rejected
  the dispatcher's mutually exclusive --sandbox and --approve-for-me arguments.
  The redundant explicit sandbox argument is removed; --approve-for-me retains
  workspace-write plus automatic review. Synthetic parsing and a real isolated
  PHI-free result-schema probe passed after correction, with zero tool actions.
  The unchanged following live cycle did not retry the consumed approval.
  Training was stopped and proposal_write / dispatch-disabled mode restored.
  This fixes launch compatibility, not the approved document correction itself.
- The post-schema-fix controlled proposal-write cycle passed on the existing
  correction case after a normal new comment and unchecked approval. Exactly one
  new generation was created; exact readback, compatible filename structure and
  subtype, unchanged human controls/comments, and unchanged implementation
  attempts/job/consumed approval were verified. Training was stopped. This cycle
  did not exercise an unchanged following cycle or implementation dispatch.
- The controlled concise proposal-write acceptance passed: one changed case,
  one new generation, retained compatible structure, unchanged human controls,
  and an idempotent following cycle. The reviewer accepted the presentation.
- A separately approved implementation attempt then failed without retained
  specific cause. No code changes resulted; its approval remains consumed.
  Do not infer authentication, transport, model, or implementation cause.
- Training remains stopped in proposal_write mode with dispatch disabled. The
  diagnostic fix is synthetic-tested. A PHI-free CLI 0.151.0 protocol test proved
  the result schema was rejected for uniqueItems before result generation. The
  unsupported keyword is removed; uniqueness and exact result-layer vocabulary
  remain enforced locally. The corrected real protocol test passed with no tool
  actions. This reproduces a current blocker but does not reconstruct the lost
  historical child failure. A new generation and fresh human approval are still
  required before another implementation attempt.
- Windows PowerShell 7 ownership-status behavior differed from supported 5.1
  during acceptance. A timestamp-conversion issue is suspected, not proven.
  Use Windows PowerShell 5.1 for the wrappers pending separate investigation.
- No human approval may carry to a changed proposal/result generation.
- Always-on Windows service/startup integration is not enabled. Operators must
  explicitly start DP and DP Training after a host restart.
- Broader representative real-document taxonomy, extraction, filename, OCR
  accuracy/performance, restart, and unattended reliability acceptance remains
  incomplete.
- Small-detector OCR performance is promising but is not an approved universal
  production default. Package/model identities and effective inference settings
  need fuller production pinning.
- Existing text-only OCR caches cannot recover historical page/block relationships
  without new OCR.
- AUTH INIT requires an approved authoritative external-system context source.
- Legitimate service-reference conflicts remain unresolved until a supported
  discriminator is available.
- Future EHR, eligibility, scheduling, and broader company-AI integrations remain
  outside the active Phase 1 implementation scope.

## Current Operational Rules

- Do not start live DP, DP Training, mailbox processing, OCR, Ollama, or production
  Smartsheet operations merely to inspect project state.
- Capability changes require an owned DP Training restart and configured/effective
  mode agreement; mismatch fails closed.
- Preserve PID, creation-time, command-line marker, pool, and ownership checks for
  all worker/service stop operations.
- Preserve uncommitted work. Compile modified Python first, run focused then
  affected tests, run tracker synchronization, complete PHI/protected-path/diff
  review, and commit/push only when every gate passes.
- `PROJECT_HISTORY.md` is append-only for new checkpoints. Historical text is not
  rewritten to make it appear current.
- `PROJECT_SMARTSHEET.md` is regenerated from the latest structured history
  checkpoint and is never an authoritative recovery source.

## CURRENT NEXT START

Refresh training source registration for the CLI argument fix, then create a new
proposal generation on the same correction case using a normal reviewer comment
with Approve AI Correction unchecked. Verify the proposal, obtain a fresh human
approval edge, and perform one controlled implementation acceptance. Verify safe
diagnostics, commit/push gates, unchanged human controls, and no retry on the
following cycle. Do not reuse the consumed approval or approve resolution before
a separate document retest passes; stop DP Training afterward.
