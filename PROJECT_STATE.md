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
One human-approved existing-row/document correction and its resolution approval
have passed live readback. One bounded approved lesson is retained and included
by the production future-prompt renderer. Fresh-app restart preserves the same
case, generation, lesson and code job without repeating correction or resolution.
The optional local code update ended update_failed: no code was installed and no
activation quarantine remains. A later same-type document has now completed the
production extraction path; its approved guidance is available and included by
the same production prompt renderer. No request body was retained, and this does
not prove the lesson caused an improvement. Reviewer acceptance of the new output
and production generated-code promotion remain pending.

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
context source. Current `business_context_version` is 4. Role-specific views are
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

AUTH INIT accepts an independently validated candidate supported by a complete
explicit Type of Authorization: Initial statement. Competing/unselected options,
negation, generic Initial wording and client/service-history inference do not
qualify. History-based INIT still requires authoritative external context.
Unknown applicable subtype remains valid with specific review, independent of
category confidence. Other supported subtypes may use validated document evidence.
Service extraction recognizes HCPC Code/HCPCS and Modifier(s) labels across OCR
lines in the same supported service section; it never borrows another section's
modifier or fills one from a reference lookup. Each line retains its own evidence.

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
date evidence normalization accepts the same two-digit-year calendar interpretation
already used by filename policy. Date evidence still belongs to its own service
line; invalid dates or evidence from another line remain unsupported. The current
document cache contains short-year dates. Controlled post-fix replay accepted both
service lines' dates and removed the disputed date warning from the proposed update.
Initial and comment-driven analysis review reasons derive from final validated
state. The review reason/status/required trio is an analysis-generation snapshot:
only new reviewer comments driving new analysis may refresh it. Applying an
approved correction, resolution approval, retaining learning, unchanged polling
and reconciliation preserve that snapshot. AI Resolution Result separately reports
confirmed changes. Filename placeholders or reference-token
lookup failure do not automatically create extraction-review reasons.

The intake filename convention is:

`<LAST, FIRST [MIDDLE]>_<PAYER>_[SERVICE]_<DOCUMENT TYPE>_<DATE[-DATE]>.<EXT>`

Filename outcomes are `complete_business`, `partial_business`, and
`technical_fallback`. Approved placeholders are `[PAYER]`, `[SERVICE]`,
`[DOCUMENT TYPE]`, `[SUBTYPE]`, and `[DATE]`.

- Optional absent components are omitted.
- Multiple independently resolved service naming tokens are comma-separated,
  sorted deterministically and deduplicated. Different valid service tokens no
  longer force [SERVICE]; ambiguous individual reference matches still do.
  Current explicit business policy excludes program from filename lookup.
  Naming resolves by accepted code/modifier across all reference program rows,
  requiring one distinct naming token per identity. Conflicting tokens remain
  ambiguous even when a blank-program reference entry exists. Extracted program
  evidence and the generic program-qualified lookup remain available for future
  use; no unrelated validation or production mappings changed.
  The existing payer reference cache is available; no replacement list is needed.
  Payer naming accepts a whitespace-only name variant when the authoritative
  result is unique. Exact lookup retains precedence; explicit unsupported keys,
  ambiguous results, abbreviations and punctuation variants are not guessed.
  This consumes accepted payer evidence only, never sender or whole-document text.
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
Configured mode is local_correction; the service remains stopped after scoped
correction/resolution acceptance. Startup uses the existing fingerprint/owned
restart contract.

Current versions:
- `business_context_version`: 4
- `analysis_contract_version`: 4
- local preparation contract: 6
- local Ollama complete-input contract: 1 (verified server 0.33.3)
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
Unrelated replay value, acceptance and metadata changes still block correction.
An out-of-scope scalar confidence may now be preserved only when the replay
independently accepts the exact same displayed value and both existing/replay
confidences pass the configured acceptance threshold and candidate cap. The
validated replay is never changed or merged with another extraction attempt.
The scoped row patch preserves that existing confidence, recomputes the displayed
minimum from the actual projected value/confidence pairs, and includes preserved
pairs in exact preconditions/readback so concurrent edits still block application.
Classification confidence is not exempted. Verified-action
coverage means a requested filename correction cannot be Analysis Ready
when the saved plan contains no attachment-name change. Existing incomplete plans
also remain blocked when explicitly requested payer/service components still
contain placeholders, even if another filename component has improved.
Incomplete plans are retained for audit and blocked before approval can apply them. Proposal text
describes verified actions, and stale workflow-owned resolution text is cleared.
Proposal presentation names saved changes: resolved filename placeholders,
specific removed/added known review-warning categories and changed/cleared fields.
It distinguishes a date-warning correction from changing a date value. Only fixed
labels are rendered; unknown text is never echoed. Existing pre-application
presentation changes still require unchecked approval. The completed current
case's wording was refreshed only after its unchanged approved plan was applied
and verified; the original wording remains in sealed audit.
Only AI Resolution Result accepts an explicit empty clear; its SDK value is
ExplicitNull, and null/blank readback reconciles without another write. Other
workflow fields still require nonempty valid text. Exact human preconditions are
unchanged. A failed proposal publication cannot report analysis ready; the saved
verified plan remains available for publication without repeating inference.
Preparation errors retain
only fixed allowlisted categories. Blocked cases fail the cycle and expose
blocked_case_count/preparation_failure_categories, rather than reporting success.
An older blocked, unapplied case may regenerate once under preparation contract 4
with both approval boxes unchecked. It keeps the same identity, archives the old
generation, and reserves the new generation before inference. Unchanged polling,
interrupted inference and uncertain applied transactions never blindly replay.
Contract 4 permits the specifically blocked incomplete filename plan to
regenerate once, including an unapplied partial attachment-name plan after a
tested business-policy change; both approvals must remain unchecked. Unchanged
feedback/context reuse the validated intent analysis instead of another model
analysis request. Original-document evidence replay still validates the new plan.
Other retained blocked plans are not rearmed. Value-free final field/naming
diagnostics are sealed locally before mapping so preparation failures remain
inspectable without printing document values or rerunning inference blindly.
Extraction shape diagnostics now capture the raw model and normalized adapter
boundaries separately for each of the two independent attempts. Only fixed type,
presence and deterministic subtype-support categories are retained, bounded to
64 service-line shape records per attempt with an explicit omitted count. This
is a diagnostic retention bound, not an extraction limit. Nested service-line
objects/arrays are preserved as candidates rather than stringified, then rejected
locally with field-specific Invalid review reasons. No nested value is unwrapped
or inferred. Exact mapped-field difference diagnostics are sealed before the
unrelated-change guard throws; only code-approved column names, type/presence and
scope/change booleans are emitted. Raw confidence-only drift is distinguishable
from governing-value change; the same audit now separately records the scoped
projection's preserved-confidence and remaining-blocker counts. Diagnostics neither
refresh human review snapshots nor authorize correction or replay.
Contract 5 additionally permits one reserved replay of a version-4 blocked
authorization filename case with no verified change or unresolved requested
filename, scoped to subtype/service fields. Other version-4 failure scopes remain
blocked. Both approvals must be unchecked; same identity/audit and prior validated
intent are retained. Unchanged comments do not refresh the review snapshot, and
the new reservation prevents another automatic replay even if inference fails.
Contract 6 additionally permits one reserved re-entry for a version-5 blocked
authorization filename case with no plan, unrelated-field failure and requested
subtype/service scope. Human approvals must be unchecked. Source-only re-entry
retains the review snapshot and existing intent; no automatic application occurs.
All shared Ollama requests explicitly set num_ctx=8192 and num_predict=4096
(positive operational environment overrides), truncate=false and shift=false.
Local identity, verified API version and model capacity are checked before input.
Only done=true/done_reason=stop responses become candidates. Overflow, unknown
API contracts, incomplete responses and transport failure fail closed with fixed
safe categories, without automatic budget escalation or additional retries.

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

- The retained retry was correlated with an Ollama server truncation event:
  4,426 input tokens became 2,050. This proves incomplete input, not absent source
  evidence. Explicit 8K-context/no-truncate/no-shift protection passed 273 unique
  synthetic/mock regressions and real local synthetic overflow/success probes.
  The server rejected oversized input and reported 8192 runtime context for the
  successful probe. Source fix 8fee328 is pushed and all four Prefect deployments
  are refreshed to its executable source with no schedules, concurrency one /
  CANCEL_NEW on document deployments, no active runs or fresh workers at acceptance.
  After explicit operator approval, one same-case contract-6 cached/local replay
  completed with three requests. Retry prompt_eval_count=4426 proves full retry
  input; both responses completed normally. The case remains blocked at generation
  3 with no plan: Hours and Days Per Week governing values changed outside scope,
  service-line evidence remains unsupported/invalid, and subtype remains unresolved.
  Payer and scalar dates validate; filename still has service/subtype placeholders.
  No correction or attachment upload occurred; human controls/comments and review
  snapshot remained unchanged. A fresh-process unchanged cycle proved zero model
  calls, zero workflow writes and no generation change. Do not rearm or replay.

- One reserved diagnostic-only cached-source replay completed with three local
  model requests (classification and two independent extraction attempts).
  The same case/generation, review snapshot, human controls and row/document were
  unchanged; zero production writes and zero comment access. The exact blocker
  was five unrelated scalar confidence differences with unchanged governing
  values. Both candidates used ordinary service-line strings, not nested objects;
  their code values were absent from their own line excerpts, modifiers failed
  the existing single-modifier format, and subtype evidence was below threshold
  and noncanonical. These are retained candidate/evidence problems, not proof
  that the source document lacks those facts. No modifier or subtype was guessed.
  The scoped-confidence correction passed 226 synthetic/mock checks plus 14
  continuity/tracker checks (240 total); tracker Not Found 0 / Failed 0.
  Applying only the pure projection to the encrypted retained
  replay preserved five confidences and reduced unrelated differences to zero,
  with zero additional model/network calls. This does not resolve the requested
  filename evidence or authorize publication. This was the earlier contract-5
  diagnostic checkpoint; the newer contract-6 result above supersedes its runtime
  state. Training and DP remain stopped for exclusive maintenance.

- Value-free extraction/correction diagnostics and invalid service-line shape
  rejection passed 367 synthetic/mock checks, including isolated Prefect
  lifecycle, local update/rollback, approval/restart and durable recovery tests.
  Valid flat labeled candidates reach validation/mapping; malformed containers
  remain internal candidates and cannot become accepted strings. This proves an
  adapter defect, not the historical live candidate shape. The prior exact
  subtype/service failure remains unproven because that run did not retain the
  new diagnostics. No real model replay or row/document correction occurred in
  this checkpoint. Contract 5 remains consumed; human state is untouched.
  DP was stopped through its proven-owned wrapper for source maintenance;
  Training remains stopped. Manual/live/Training registrations were refreshed to
  executable source db4509d0a33897044530f30d2b507a9e4b940836: each is unique,
  parameterless, unscheduled and concurrency one/CANCEL_NEW. Control-plane readback
  shows no active manual/live/Training conflict or fresh worker. Continued DP
  polling remains authorized after exclusive diagnostic maintenance completes.

- Post-fix live revalidation under contract 5 reused the same case and validated
  feedback intent (zero feedback model calls), with one cached-source pipeline
  replay and two independent extraction attempts. It remained blocked with
  correction_unrelated_field_change; no plan, correction or attachment change was
  saved/applied. Snapshot, comments and human approvals stayed unchanged. Retained
  final diagnostics still show supported payer/dates, unresolved service/subtype,
  two unsupported service-line codes and invalid modifiers. A read-only comparison
  additionally proves both start/end-date confidences differ from current mapped
  confidences, outside the requested correction scope. The complete changed-column
  set, value differences and raw candidate shapes were not retained; confidence
  drift alone cannot be assumed to explain every difference. Prompt changes alone
  did not resolve this document. Fresh-app
  unchanged-cycle verification made zero model/replay/correction calls and kept
  the same generation. Manual/live/Training registration is current at d3114dc,
  with no schedules, no parameters and concurrency one/CANCEL_NEW. DP restarted
  after exclusive maintenance under continued operator authorization; Training
  remains stopped. DP status is waiting, ownership proven, one fresh worker, no
  active run, zero consecutive failures and not degraded. No additional replay is
  authorized by the consumed contract.

- The operator flagged the later row and supplied feedback. One scoped production
  analysis completed with correction_no_verified_change, no saved plan and zero
  corrections. Human controls/comments and review snapshot remained unchanged.
  Safe cached-source inspection confirmed service labels and an explicit Initial
  statement. Retained replay diagnostics showed two source-unsupported service
  codes and structurally invalid modifiers; code-only reference matches are
  ambiguous. No reference mapping or modifier was guessed. The blanket INIT veto
  is fixed and service-label prompt coverage improved, with 257 synthetic/mock
  checks passing. Real post-fix replay is not yet proven. DP was temporarily stopped
  through its owned wrapper for the exclusive replay/source-maintenance lease;
  continued polling remains authorized. Training is stopped.

- A different authorization document completed unattended processing on 2026-09-09:
  one new row, one attachment, one create/upload attempt each, zero failures,
  mailbox finalization and Workflow Summary completed. OCR/classification and two
  independently validated extraction attempts ran; attempt 1 was selected.
  Exact row identity, one matching attachment and protected correction-source
  binding were verified. AI Correction is unchecked. Displayed mapped fields have
  their confidence cells; absent mapped fields do not have stray confidence cells.
  Partial business naming resolved payer/date, with service and document-subtype
  placeholders remaining. Nine review reasons remain for human assessment; no
  claim is made that they are all correct. Approved same-type guidance was verified
  in the production renderer without exposing prompts or document values.
  DP returned to waiting, one owned worker, zero consecutive failures, not degraded.
  The operator explicitly authorized continued unattended polling; DP is left
  running. Training remains stopped. No correction/approval/comment was performed
  on this new row, and the new comment-driven snapshot rule remains unaccepted live.

- One scoped same-case local/cached evidence cycle under preparation contract 4
  created exactly one new generation. Payer, service and dates resolve; multiple
  service tokens are comma-separated. Only the legitimate unknown-subtype
  placeholder remains. The disputed service-line date warning is absent from
  the planned review update. The full polling sweep was not started, so other flagged cases were
  untouched. The verified plan was saved but initial publication failed locally:
  the writer rejected the requested blank stale-resolution clear. That narrow
  contract mismatch is fixed and publication-only live readback succeeded. The
  proposal matched the saved verified plan and human controls were unchanged.
  Subsequently the operator checked Approve AI Correction. One scoped saved-plan
  cycle applied the exact existing-row review update and attachment-name version,
  then verified readback with zero failures and zero model calls. Case identity,
  generation and plan were unchanged. Concise proposal wording was refreshed with
  original wording audited, without changing scope. The operator subsequently
  approved resolution. One scoped production cycle resolved the case, retained one
  bounded lesson and proved future-prompt inclusion. Fresh-app restart did not
  repeat correction/resolution or code generation. The optional local code job
  failed safely without installation; its exact internal failure cause was not
  retained. Other cases and human controls/comments were not modified. Training
  remains stopped.

- The new comment-driven review-snapshot boundary has 13 focused synthetic/mock
  checks: typed sealed intent, exact readback, lost-response reconciliation,
  restart without new inference, no blind uncertain-write retry, human ownership
  and application/resolution preservation. Older unapplied plans containing review
  writes fail closed; confirmed historical transactions can reconcile. Minimum
  field confidence still follows current validated production fields. Results name
  only confirmed changes, never unchanged review fields. This new rule has not yet
  received live comment-driven acceptance. The prior approved date-warning removal
  is verified and is not undone.

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

- Same-row correction and resolution approval have passed scoped live acceptance.
  A subsequent same-type processing run and guidance-renderer inclusion passed;
  reviewer-confirmed improvement, new comment-driven snapshot acceptance and actual
  generated-code promotion remain pending. Prompt inclusion alone does not prove
  model adherence or correction generalization.
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
  incomplete. INIT inferred from external client/service history still requires
  authoritative external context; only validated explicit statements qualify locally.
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

## Document Processor — Current Service Summary

Existing DP facts, limitations and verified baseline above remain unchanged. Its
same-case correction remains blocked at generation 3. No DP/Training runtime,
registration, patient data, learning or recovery state was operated on for this pilot.
The shared Ollama transport was mechanically extracted with focused regressions;
DP prompts and business behavior remain unchanged. Existing registrations were not refreshed.

## Document Processor — Pending Action

Use the retained encrypted full-context candidates and final diagnostics to fix service-section evidence/subtype support and investigate out-of-scope Hours/Days Per Week value changes. Prove the correction synthetically before any further replay or rearm. Preserve blocked generation 3, review snapshot, comments, approvals, existing row/document and idempotency; do not resend the document or request approval of an unverified proposal. DP and Training remain stopped during exclusive maintenance.

## Program Compliance Monitor — Current State

Original CLASS DSA pilot acceptance and shared-inference activation remain completed.
The authorized fresh baseline and feedback extension are verified in the same Program
Compliance sheet in LT Automation Platform. Full sheet/state backup and isolated restore
preceded the one authorized 44-row reset; previous human/source/review history is retained.
The bounded 148-source registry/discovery was checked, with 11 retrieval/parser failures.
Rebuilt output: 50 requirement/change rows, 11 organizational Topic parents,
70 total rows; zero TEST output or duplicate keys. Source states: {'assessed': 91, 'blocked': 11, 'gap': 46}.
Section states: {'assessed': 23, 'context_only': 772, 'gap': 102}. Gaps remain explicit, not no-change or legal coverage claims.

Human-owned Implementation Status is separate from Review Status. Agency-reported status,
notes and completion evidence bind to the Reviewed Revision and retained source/profile
support. Compatible Met reports suppress repeat work; changed/removed duties or relevant
context require reassessment without modifying human cells or erasing historical reports.
Stable collapsed new topic parents group requirements, questions, health/coverage and controls;
later user expansion and same-row human fields are preserved. Real readback, zero unchanged
model calls/writes, and a fresh-process backup/restore and same-sheet reconciliation passed.

62 Compliance tests (43 retained plus 19 new feedback/baseline/hierarchy cases), 4 continuity,
12 shared-queue, 13 context-contract and 57 Training regressions passed, synthetic/mock.
Live source retrieval, local Ollama and dedicated-sheet publication are separate real checks.
Only Compliance was paused during maintenance. The prior approved hidden schedule is restored:
daily 01:00 Central, Sunday discovery and 15-minute sync, with one actual inference and bounded
DP priority through the existing shared queue. DP/Training processes and learning/recovery
records remain untouched. LT Project Tracking remains unchanged (read-only reconciliation).
No policy inventory, comparison, drafting or independently certified compliance is included.

Authoritative full requirements, evidence and Next Service Action:
docs/program_compliance_plan.md. Reviewer guide: docs/program_compliance_operations.md.

## CURRENT NEXT START

Route by requested service. For Document Processor, follow the preserved Document Processor Pending Action above. For Program Compliance Monitor, read docs/program_compliance_plan.md and follow its Next Service Action. Preserve the other service's state and pending work; do not start, stop, repair or resume it implicitly.
