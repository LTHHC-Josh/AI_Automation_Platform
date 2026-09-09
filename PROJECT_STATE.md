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

### Local Correction and Bounded Code Updates

Production uses local Ollama, never Codex/cloud model dispatch. Approve AI
Correction authorizes an evidence-validated correction to the existing
row/document. Approve AI Resolution authorizes bounded per-type guidance and
necessary local code updates without a second approval.

The same-row workflow, isolated test runner and atomic local release/rollback
transaction are implemented. Automatic code editing is deliberately restricted
to one existing method body in filename policy or review-reason presentation.
Imports, public signatures, tests, approval handling, external writers and updater
code cannot be changed by the model. New calls and new string literals are
rejected. Other correction scopes retain guidance but explicitly report that code
updates are unsupported; this is not unrestricted self-programming or model-weight
training, and it does not guarantee error-free recognition.

Windows Sandbox is enabled and the post-restart isolation probe passed. The
production repository, credentials and documents are not shared with sandbox
tests. Networking/clipboard redirection are disabled. Local code-generation
positive and rejection probes passed their respective acceptance/safety checks.
No production document correction or generated-code promotion has been live-tested
in this checkpoint.

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
context source. Current `business_context_version` is 3. Role-specific views are
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

DP Training is the separate operator-owned correction service. Local modes are
schema_only, read_only, proposal_write and local_correction. The historical
approval_dispatch mode is a compatibility alias for local correction, not Codex.
Configured mode is local_correction; the service remains stopped pending controlled
acceptance. Startup uses the existing fingerprint/owned restart contract.

Current versions:
- `business_context_version`: 3
- `analysis_contract_version`: 4
- local preparation contract: 2
- legacy protected correction-case schema: 3
- local sealed correction/source/lesson/audit schema: 1
- resolution code-update authorization contract: 1

Human-owned: AI Correction, Approve AI Correction, Approve AI Resolution and
Conversations/comments. Processor creates AI Correction unchecked on new rows
only. No correction workflow writes human checkboxes or comments.

Workflow-owned: AI Proposed Correction, AI Correction Type, AI Correction Status,
AI Resolution Result. New input creates a generation on the existing stable case
identity. Stale approvals do not carry over. Original source binding requires the
durable row association and exact document fingerprint. Replay uses the existing
pipeline with cached OCR only; comments are intent, never field evidence.

Correction writes use explicit existing field mappings, typed validation, exact
preconditions and readback. Unsupported prior values may be explicitly cleared.
Attachment renaming uses a temporary source copy and a proven existing attachment
version. Original source bytes and original mailbox recovery names remain unchanged.
Each external boundary has a sealed durable intent. Uncertain updates reconcile;
an unproven attachment-version response is blocked rather than blindly repeated.
External/user changes are preserved.

Filename intent normalization now aligns the primary symptom, fixed behavior code
and Filename execution scope. Service Line correction revalidates only its review
projection; it never flattens line dates/quantity/status into top-level columns.
Unrelated replay changes still block aggregate correction. Preparation errors retain
only fixed allowlisted categories. Blocked cases fail the cycle and expose
blocked_case_count/preparation_failure_categories, rather than reporting success.
An older blocked, unapplied case may reanalyze once under preparation contract 2
with both approval boxes unchecked. It keeps the same identity, archives the old
generation, and reserves the new generation before inference. Unchanged polling,
interrupted inference and uncertain applied transactions never blindly replay.

Verified correction results move to Awaiting Resolution Approval. Fresh approval
retains only fixed PHI-free guidance, directly indexed by canonical document family:
at most eight active rules / 1800 characters. Historic cases are not scanned during
normal inference. No patient values, comments or model prose enter this guidance.
This improves context; it is not novel model-weight training.
The bounded five-case poll rotates its durable cursor, so resolved cases whose
human-owned flag remains checked cannot starve newer feedback.

Resolution also creates one sealed code-update authorization for the exact case
generation/plan. The local generator sees only controlled family/behavior and
approved source code, not document or feedback values. One generation attempt is
reserved before calling Ollama. Interrupted/invalid generation is not silently
repeated. No-change and unsupported-scope outcomes are explicit.

Candidates remain data on the host until restricted AST validation and immutable
synthetic tests run in a headless Windows Sandbox. Only staged tracked source,
tests, sanitized Python 3.13 runtime and explicitly selected dependency code are
shared read-only. No .env, Git metadata, production documents or credentials are
shared. Guest networking, clipboard, audio/video input and printer redirection are
disabled. SDK dependencies have no credentials and tests inject non-writing
adapters. Sandbox start/test/stop time budgets are 180/300/45 seconds. An exact
sealed ownership reservation precedes startup; cleanup failure blocks promotion.

Promotion changes one allowlisted source file atomically after proof matches the
candidate digest and baseline remains unchanged. Before/after source is sealed
for recovery; post-promotion tests can trigger exact rollback. Unrelated edits
block promotion/rollback rather than being overwritten. Runtime releases remain
local and are recorded in sealed release history, not automatically committed or
pushed to Git. Subsequent maintenance must reconcile those proven local edits.
No release is represented as a Git commit or a model retraining event.
A shared Windows process lease excludes mailbox/manual processing during source
promotion and post-install verification. A sealed activation quarantine survives
crashes and blocks new document processing until that same release verifies or
rolls back. The guard also covers direct DocumentProcessor replay. A busy or
unverified activation fails closed; no production process is killed.

Production factory never constructs a Codex dispatcher. Historical Codex classes
remain for audit/developer regressions only. Local model requests reject remote
endpoints and cloud aliases before sending protected prompts. Status retains JSON
compatibility and shows correction/resolution/guidance counts.

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

- Controlled local_correction cycle on 2026-09-09 processed three flagged cases;
  all became blocked, with zero corrections and zero Codex dispatches. The newest
  case recorded sufficient feedback but selected add_required_review_reason and
  produced no verified plan. Preparation exceptions are currently collapsed to
  Cannot Resolve Yet; the exact cause is not retained. Training stopped cleanly,
  no fresh workers remain, and human approval was observed unchecked. This is a
  failed proposal acceptance, despite the cycle reporting completed/none.

- Current controlled new-document run completed with one new row and attachment,
  zero failures and one extraction attempt. Partial business filename and review
  required are awaiting reviewer assessment. AI Correction initialized unchecked;
  protected correction source binding is proven. DP returned to waiting and stopped.

- Approved PHI-safe AUTH DECREASE naming correction is synthetic-tested: a
  top-level date can borrow a service-line endpoint only when the opposite
  endpoint agrees. Supported single dates remain single; unresolved dates use
  [DATE]. Canonical subtype, validated payer/service, and unrelated-field
  exclusion are covered. Shared context v2 now includes the generalized date
  and component rules; training rendering retains its 4,096-character bound.
  No real document retest or correction-row operation occurred.

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

- Full live acceptance of the redesigned same-row correction/resolution workflow
  remains pending. Do not equate synthetic or isolated code checks with a real
  patient-document acceptance.
- Automatic code updates cover only the allowlisted pure-function scopes described
  above. Other failures stay safe and visible; no generic autonomous repository
  rewrite is enabled.
- The actual model proposed a disallowed capability during a code-only probe; the
  candidate was rejected and nothing was promoted. A separate minimal synthetic
  defect produced an accepted bounded candidate. Model suggestions still require
  independent validation and tests.
- Lost/unproven attachment-version responses remain reconciliation-blocked rather
  than generating another upload.
- Correction replay requires the original cached source and OCR. It cannot invent
  missing evidence or recover lost page/block structure from text-only caches.
- Human approval does not prove a correction generalizes across all documents.
  Broader taxonomy, OCR, extraction and unattended reliability coverage remains
  incomplete. AUTH INIT still requires authoritative external context.
- No silent Windows reboot startup is enabled. Start the control room/Ollama and
  explicitly start the required DP or DP Training service.
- Use Windows PowerShell 5.1 for operator wrappers. The older PowerShell 7
  ownership-status discrepancy remains a separate investigation.
- Prior Codex acceptance, CLI repairs and Retest Required state are historical,
  preserved in PROJECT_HISTORY and Git; they are not the intended production loop.

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

Refresh affected source registration, then run one controlled DP Training cycle on the existing flagged cases with both approval boxes unchecked. Verify the same-case contract upgrade produces a filename/service-line-review proposal or a specific safe preparation blocker, without resubmission or production correction. Stop training after that cycle. Request human approval only for a verified proposal; full correction/resolution/later-document learning acceptance remains pending.
