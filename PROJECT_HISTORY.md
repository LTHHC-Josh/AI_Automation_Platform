# LTHHC A.I. Automation Platform - Project History

## Authority

This file is the authoritative, complete, Git-owned historical record. It is
independent of Smartsheet. New detailed checkpoints are appended here after
meaningful tested work; prior historical text is never shortened or rewritten.

`PROJECT_STATE.md` is authoritative for current truth. `PROJECT_SMARTSHEET.md`
and the `PROJECT_SMARTSHEET` sync model are non-authoritative presentations.

## Lossless Migration Manifest

Migration source commit: `9fe3abe3d3a3a0465472d67716d9c6dbfd129d8e`

Content map:

- Entire legacy `PROJECT_MEMORY.md` -> the verbatim legacy-memory snapshot below.
  Current facts were additionally reconciled into `PROJECT_STATE.md`; historical
  diary/checkpoints remain only authoritative here.
- Entire legacy `PROJECT_JOURNAL` string -> the verbatim development-journal
  snapshot below.
- Entire legacy tracker `updates` payload -> the verbatim tracker-update snapshot
  below. Runtime Smartsheet comments are now concise/non-authoritative.
- Legacy tracker executable wrapper -> replaced by the explicit
  `PROJECT_SMARTSHEET` presentation/sync layer; it contained no unique project
  history outside the preserved payloads.

Legacy `PROJECT_MEMORY.md` section map:

- Purpose and Source of Truth -> both: the durable authority model is reconciled
  in `PROJECT_STATE.md`; the original wording remains verbatim below.
- Current Phase 1 Priority -> both: current scope remains in state; detailed prior
  framing remains in history.
- Intended Phase 1 Production Runtime -> both: current Prefect topology and rules
  remain in state; chronological deployment/acceptance narrative remains here.
- Architecture and Safety Invariants -> both: current invariants remain in state;
  the complete prior statement remains here.
- Document Taxonomy and Training, including Accepted UTL Behavior -> both: current
  taxonomy/rules remain in state; test narrative and prior decisions remain here.
- Whole-Document Evidence and Learning -> both: current evidence rules remain in
  state; detailed development observations remain here.
- Smartsheet Production Contract and Smartsheet Schema Evolution -> both: current
  typed mapping/recovery rules remain in state; evolution history remains here.
- Authoritative Phase 1 End-User Feedback Model -> both: the now-current seven-
  column DP Training ownership/lifecycle is reconciled in state; superseded seed
  architecture and its evolution remain only here.
- Current Implemented Capabilities and Verified Current Baselines -> both: the
  current tested baseline is condensed in state; exhaustive test/run history
  remains here.
- Phase 1 Finish Line and Remaining Gaps -> both: active limitations remain in
  state; earlier ordered plans and completed gaps remain here.
- Developer Tool Evaluation Checkpoints -> both: still-applicable operating rules
  remain in state/`AGENTS.md`; original evaluation record remains here.
- Memory Maintenance -> superseded active procedure: replaced by the three-layer
  rules in `AGENTS.md` and `PROJECT_STATE.md`; original text remains here.
- Every chronological checkpoint following Memory Maintenance -> history only,
  except current facts separately reconciled into state.
- Legacy CURRENT NEXT START -> both: preserved verbatim here and carried exactly
  once in `PROJECT_STATE.md`.

Legacy tracker content map:

- `PROJECT_JOURNAL` -> history only as the complete development-journal snapshot.
- `updates` statuses/comments -> both: the full pre-migration payload remains here;
  current statuses and bounded comments feed the non-authoritative
  `PROJECT_SMARTSHEET` presentation.
- Sync counters and task lookup behavior -> `PROJECT_SMARTSHEET` executable layer.
- No prior Smartsheet response was an authoritative history store; failures or
  later cell limits cannot alter this file.

Verification metadata:

- Legacy memory normalized SHA-256: `7bd44e1eca8ba942192ad04388ac4a651dd9312677400f6d7f464eb2886acde6`
- Legacy journal normalized SHA-256: `a769e26ee70f3f9534eebe4541b265b9866b359819c837f842847ad2ff994d7e`
- Legacy tracker-updates normalized SHA-256: `031ee62000da8d2a1dc7cc5b08870e78160f3b9f22b7bc59380eba74830ffe4e`
- Legacy memory characters: `115945`
- Legacy journal characters: `407495`
- Legacy tracker-updates characters: `26273`

The snapshot markers are permanent audit boundaries. References inside them to
old filenames or historical procedures are preserved evidence, not active
instructions.

## Current Migration Checkpoint

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-04",
  "work_summary": "Migrated project continuity into authoritative current-state and complete-history layers with a separate bounded Smartsheet presentation.",
  "key_result": "All legacy memory, journal, and tracker-update content is preserved with hash-verified boundaries; no Smartsheet failure can remove the Git history.",
  "tests": "70 focused and affected synthetic deterministic/mock checks passed with zero failures; modified Python compiled.",
  "phi_handling": "Repository continuity remains PHI-free; no document-processing integration ran.",
  "limitation_acceptance": "The next controlled DP Training proposal-write acceptance remains pending.",
  "exact_next_start": "Add one normal minimal reviewer comment, such as `again`, to the existing active correction case, then perform one controlled live `proposal_write` DP Training acceptance. Verify the ordinary comment revision creates exactly one new proposal generation, retains the prior compatible canonical subtype/document type, payer, applicable service, and supported date/date-range structure, and writes a concise reviewer-facing `AI Proposed Correction` plus only the workflow-owned type/status fields needed for the generation. Verify human controls/comments remain unchanged, no Codex dispatch or implementation job occurs, and an unchanged following cycle is reconciliation-only/idempotent. Do not approve implementation during this acceptance, and stop DP Training cleanly afterward."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

### Work Performed

- Separated current truth, complete history, and bounded Smartsheet presentation.
- Preserved all legacy content before retiring either mixed source.
- Added fail-closed structured summary parsing and exact next-start agreement.
- Audited all 38 managed Smartsheet task rows before concise synchronization.
  Status differences were zero. The only comment difference was a 4,000-character
  live prefix of the 5,427-character Git source, proving truncation rather than
  unique Smartsheet history. Thirty-seven unmanaged rows remain untouched and
  outside this synchronization contract.

### Files Changed

- Added `PROJECT_STATE.md`, `PROJECT_HISTORY.md`, and `PROJECT_SMARTSHEET.md`.
- Added `src/services/project_smartsheet_service.py` and
  `tests/test_project_layer_migration.py`.
- Updated `AGENTS.md`, `update_project_tracker.py`, the bounded DP Training Codex
  prompt, tracker/Prefect continuity tests, and the reference-workbook guide.
- Retired `PROJECT_MEMORY.md` only after its complete content passed the independent
  embedded-payload hash verification.

### Validation State

Modified Python compiled. Eleven focused project-layer migration checks, three
tracker/WBS checks, seven PostgreSQL/Prefect continuity checks, and forty-nine DP
Training/Codex-boundary checks passed: 70 total, zero failed. Tests were synthetic
deterministic or mock/local-protected only. No mailbox/Graph, OCR, live Ollama,
production document processing, or correction workflow operation ran. Tracker
Smartsheet synchronization remains the final external presentation check before
commit.

## Verbatim Legacy PROJECT_MEMORY.md Snapshot

<!-- LEGACY_PROJECT_MEMORY_START -->
# LTHHC A.I. Automation Platform - Project Memory

## Purpose and Source of Truth

This file is the compact continuity layer for the LTHHC A.I. Automation
Platform. It records current architecture decisions, implemented capabilities,
verified baselines, known limitations, and the exact next starting point.

Source-of-truth order:

1. Git committed state for committed code.
2. Confirmed local uncommitted state for work not yet committed.
3. `AGENTS.md` for durable repository safety and execution rules.
4. This file for current project continuity.
5. `update_project_tracker.py` for detailed historical checkpoints and task
   synchronization.

If sources disagree, inspect and reconcile them rather than guessing.

Never store PHI, OCR text, patient/member data, `source_text`, protected
filenames or paths, credentials, secrets, tokens, Smartsheet payload values,
Smartsheet row IDs, model files, or protected cache contents in this file.

## Current Phase 1 Priority

The automated document processor is the current implementation priority. Do
not implement future EHR, eligibility, or unrelated company-AI subsystems
until the document processor meets its live completion criteria. Future
platform needs may influence architecture only to avoid dead ends.

The long-term direction remains a reusable company-wide AI and automation
platform for approved Microsoft 365, SharePoint/OneDrive, EHR, eligibility,
internal-system, and other healthcare sources. Those future sources must be
adapters into shared platform services rather than separate OCR, AI, review,
or integration stacks. This future direction is not a claim that those
subsystems are implemented or current work priorities.

The shared Phase 1 flow is:

approved email/fax/document sources
-> ingestion
-> OCR and structured whole-document evidence
-> family/type classification
-> subtype/purpose classification
-> extraction
-> deterministic validation
-> business rules
-> automatic Smartsheet row creation/population
-> downstream Smartsheet automations
-> downstream human review or feedback where needed

## Intended Phase 1 Production Runtime

Prefect 3.8.4 passed the repository-level architectural fit assessment and a
PHI-safe self-hosted development control-room acceptance on the Windows host.
It remains the intended Phase 1 orchestration/control-plane candidate, not an
application state or business-logic layer. Prefer self-hosted Prefect inside
the approved LTHHC environment. Do not depend on Prefect Cloud unless it is
separately reviewed and approved.

The accepted development topology is one localhost server/UI backed by native
PostgreSQL 17.11, one process work pool with concurrency one, one process
worker, and manual synthetic runs only. Five strictly sequential synthetic
runs completed with one task and zero retries each; API, worker health, and
pool readiness passed with no SQLite-locking or database operational errors.
The prior SQLite database remains untouched only as a local rollback artifact.

The application prerequisite boundary is implemented and registered only for
manual operation: an explicit downstream classification-review mode, PHI-safe
durable job-batch summary, and parameterless one-call Prefect adapter exist as
the `manual-local` deployment. The adapter uses the explicit PHI-safe
operator-purpose Run Type `Prefect bounded mailbox orchestration`; it has no
schedule, no parameters, and zero Prefect retries. The first authorized flow
run reached terminal Failed before mailbox enumeration because the execution
environment blocked the required outbound authentication connection. A later
authorized real run exposed one candidate message containing two candidate
documents and reached `row_write_pending`; it was safely cancelled. Final state
was Cancelled, uncertain state was absent, no duplicate business action was
detected, and all components were stopped.

The manual adapter now uses an acceptance-only local popup inside its single
application task. It inspects only the newest ten unread Inbox messages through
metadata, lists only candidates with exactly one deterministically supported
document, and displays only a candidate number, normalized UTC receipt time,
and supported-document count. The selected identity remains in process memory,
is re-fetched through the exact Inbox boundary, and must still be available,
unread, identity-matched, and contain exactly one supported document. Cancel,
invalid or unavailable selection, movement, read-state change, and zero,
multiple, or unprovable re-verification fail closed before attachment download,
OCR, Ollama, Smartsheet, or mailbox completion. There is no newest-unread
fallback. Normal unattended enumeration remains unchanged.

The popup-selected source is registered as
`lthhc-bounded-mailbox/manual-local`. A PHI-safe registration/read-only
verification found empty parameters, no schedule, no automations or triggers,
concurrency one with `CANCEL_NEW`, exactly one application task, and zero
Prefect retries. Registered entrypoint and current-HEAD assertions proved the
newest-ten metadata discovery, local popup selection, exact Inbox
re-verification, one-message/one-document limits, no newest-unread fallback,
and unchanged normal production enumeration. No worker, popup, mailbox access,
or flow ran, and PostgreSQL plus the Prefect server were stopped afterward.

The first explicitly authorized popup-selected acceptance passed the
same-boundary Graph authentication gate and every boolean readiness gate, then
consumed exactly one deployment invocation. Metadata-only discovery found zero
eligible candidates, so the acceptance guard failed closed with terminal
Prefect state Failed. The popup was not displayed, no candidate was selected,
and no attachment download, OCR, Ollama, Smartsheet operation, mailbox
completion, retry, fallback, or retrigger occurred. PostgreSQL, the Prefect
server, and the worker were stopped afterward. Prefect exposed the discovery
and terminal guard category. Dedicated PHI-safe `candidate_selection` and
`candidate_reverification` lifecycle events are now implemented. Selection
events expose only discovery completion, eligible count, popup-displayed and
candidate-selected booleans, duration, status, and sanitized category.
Re-verification events expose only availability and proof booleans for Inbox
membership, unread state, exact identity match, and exactly one supported
document. Candidate identity remains local to the application process and is
absent from events, logs, results, and repr output.

The updated popup source is registered as the same parameterless
`lthhc-bounded-mailbox/manual-local` deployment. Read-only metadata verification
found empty parameters and schema, no schedule or automations, concurrency one
with `CANCEL_NEW`, one application task, and zero retries. Registration created
no flow run; no worker, mailbox enumeration, popup, OCR, Ollama, or production
Smartsheet operation ran. PostgreSQL and the Prefect server were stopped after
verification.

A later explicitly authorized guarded acceptance stopped at preflight without
triggering the deployment. The same-boundary worker Graph authentication gate
passed, but the submission-key column configuration readiness boolean was
false, so aggregate readiness was false. No mailbox flow was created, no
mailbox content was enumerated or processed, and PostgreSQL, the Prefect
server, and the worker were stopped. The approved submission-key setting must
be restored only through the ignored local/process configuration boundary and
must pass the PHI-safe readiness gate before any newly authorized acceptance.
The exact approved setting was subsequently restored in that ignored boundary.
A configuration-only, columns-metadata-only live verification proved that the
setting is visible to configuration loading, resolves exactly one column, has
`TEXT_NUMBER` type, and has no system-column designation. No row, attachment,
mailbox, OCR, Ollama, PostgreSQL, worker, server, or Prefect flow operation ran.

The boolean-only readiness probe now proves the running server backend from
the server's own database-connectivity and non-secret driver settings instead
of the client profile's local backend report. Regression coverage requires a
PostgreSQL server to pass even when the client profile reports SQLite, and
requires actual SQLite or unproven server-backend state to fail closed. A live
authorized readiness run passed all eight booleans with PostgreSQL, the server,
one worker, pool concurrency one, and the manual deployment ready; no mailbox
flow ran.

The first mailbox acceptance failure was classified as a network/service
reachability defect, not an application configuration or credential-loading
defect. The parent readiness command ran with approved outbound access, while
the Prefect worker was launched inside a restricted network boundary. Both
paths used the same ignored dotenv/environment configuration, repository
working directory, Graph configuration loader, and authenticator. A dedicated
mailbox-worker launcher now runs the shared boolean-only Graph authentication
gate inside the same process/network boundary before starting the worker; it
fails closed without persisting credentials or changing the parameterless
deployment.

Mailbox run-conflict readiness now follows Prefect 3.8.4 state types rather
than requiring an empty deployment history. Completed, Failed, Cancelled, and
Crashed are confirmed terminal and allowed; Scheduled, Pending, Running,
Paused, Cancelling, missing, or unknown state is blocked. The live boolean-only
preflight passed every category with the one historical terminal failure and
zero active runs; it created no flow run.

Target live architecture:

Windows production AI host
-> local Ollama runtime ready
-> self-hosted Prefect server/UI ready
-> Prefect worker starts automatically
-> approved Microsoft 365/Outlook/Graph intake runs continuously
-> eligible document is safely claimed
-> OCR and whole-document AI processing
-> family/type and subtype/purpose classification
-> extraction
-> deterministic validation
-> business rules
-> automatic Smartsheet row and attachment through approved mappings
-> safe processing/job state persisted
-> downstream Smartsheet automations
-> worker continues processing future documents

Prefect's intended responsibilities are orchestration/control plane,
workflow/run status, retries and scheduling, worker health, queue/backlog
visibility, PHI-safe timings/status, and appropriate pause, resume, and
maintenance controls.

Prefect must not become a PHI viewing interface. Its UI, logs, diagnostics,
run names, task names, parameters, states, and exceptions must not expose
patient/member names, OCR text, extracted PHI values, `source_text`, protected
filenames or paths, Smartsheet payload values, row IDs, credentials, or
tokens.

Preserve runtime separation:

- Prefect orchestrates existing service boundaries.
- Existing document-processing services perform processing.
- Ollama provides the local LLM runtime.
- PaddleOCR provides OCR.
- Smartsheet remains the operational and end-user destination.
- Business rules remain in shared business-rule services, never in
  Prefect-specific flow or task code.

Before integration, inspect the actual application entry points, callers,
state boundaries, and Windows runtime requirements. Add the smallest Prefect
adapter around the existing processor rather than rewriting or duplicating
the document-processing pipeline.

## Architecture and Safety Invariants

- Classification, extraction, deterministic validation, business rules,
  external writes, and human review remain separate boundaries.
- Reuse shared OCR, evidence, classification, extraction, validation, review,
  integration, diagnostic, and orchestration services. Do not create
  family- or subtype-specific parser stacks when the generic framework can
  support the behavior.
- MCO, payer, sender, source, filename, logo, and template are context or
  metadata and must not determine document meaning.
- Extraction preserves `value`, `confidence`, and `source_text` for every
  field and service line. Confidence is never automatically assigned `1.0`.
- Missing, unsupported, conflicting, invalid, low-confidence, guessed,
  ambiguous, or insufficiently evidenced values remain null/unknown and
  require review where appropriate.
- Separate Ollama attempts are independently validated and never merged. The
  strongest deterministically supported candidate is selected; ties keep
  attempt 1. Model confidence, token count, and response length are not proof
  of correctness.
- Requested visits are not approved visits. Units are not automatically
  visits, sessions, equipment, or sufficient approval. Approval must not be
  inferred from quantity, code, dates, service lines, or generic status.
- Modifier ownership requires evidence from the same service line. Unresolved
  quantity meaning and modifier ownership remain human-review decisions.
- Review output preserves values, confidence, protected source evidence,
  actions, status/reasons, retry metadata, selected attempt, and
  reconciliation without rerunning or reinterpreting extraction.
- Review status and reasons accompany the automatically populated row when
  configured reliability rules require downstream review.
- Run Type is explicit PHI-safe operator text and is never inferred from
  document data.
- PHI remains within approved LTHHC systems and intentionally designed
  production integrations. Diagnostics expose only PHI-safe counts,
  booleans, timings, confidence/status metadata, evidence-present flags, safe
  configuration identifiers, and sanitized failure categories.
- Smartsheet is an approved production destination for explicitly mapped PHI
  and full document content. Map only intended destination fields; never pass
  document or review objects wholesale or include internal diagnostics,
  credentials, tokens, local paths, cache metadata, or unrelated fields.
- Model, dependency, and configuration choices must become explicit,
  reproducible, tested, reversible, and observable before unattended
  operation. Temporary dependency outages must not lose documents or create
  duplicate business actions.

## Document Taxonomy and Training

One reusable trainable framework supports many document families/types and
many subtypes/purposes. Family/type and subtype/purpose are separate
dimensions.

Current examples include:

- Authorization -> Renewal, Term, Stub, and future approved Authorization
  subtypes.
- 2067 -> UTL and future approved 2067 subtypes.

Authorization compatibility remains preserved. Renewal, Term, and Stub are
recognized taxonomy directions but require their exact trained and approved
production meanings before new behavior is implemented.

Training a family or subtype means using representative real documents and
the protected whole-document tester to establish:

- family and subtype;
- distinguishing indicators and wording/layout variation;
- important fields and concepts;
- strong versus supporting evidence;
- insufficient, missing, conflicting, or negated evidence;
- conclusions that must never be inferred;
- explicit approved Smartsheet mappings; and
- synthetic and regression coverage.

Training may improve classification, normalization, extraction schemas,
prompts, deterministic validation, business rules, reference data, OCR/model
configuration, or tests. It does not automatically mean retraining or
fine-tuning an LLM. Model observations and end-user feedback never promote a
production rule without deterministic validation, testing, and business
approval.

The processor reasons over the complete document and generalizes across
layouts, page locations, wording, formatting, and source organizations.
Coordinates may be optional evidence but are not required unless an approved
rule intentionally uses them. Unfamiliar or partially matching documents
remain unknown/review rather than being forced into a taxonomy.

### Accepted UTL Behavior

- 2067 is the document family/type.
- UTL is an internal LT Home Healthcare subtype/purpose of 2067 and means
  Unable To Locate.
- Literal `UTL`, a fixed page, and fixed coordinates are not required.
- Approved deterministic rule:

  supported 2067 family
  + deterministically supported `contact_failure`
  + no negated, contradictory, or mixed contact/location evidence
  -> subtype UTL

- 2067 alone, `annual_due` alone, Posted Date alone, literal UTL alone, or
  `contact_failure` outside the approved 2067 context does not independently
  imply UTL.
- Clear contact-failure evidence remains a deterministic normalized concept
  separate from the final subtype. Unsupported, conditional-only, negated,
  contradictory, or mixed evidence keeps the subtype unknown with review.

A real protected cache-only/local-Ollama acceptance passed on one known
four-page structured document: family 2067, subtype UTL, deterministic
`form_2067` and `contact_failure` supported, no family/subtype taxonomy review,
six valid evidence references, zero unsupported references, and zero Paddle
prediction calls. The prior real zero-valid-reference grounding defect is
resolved. This accepts the behavior for that known case; it does not prove
universal coverage across every future 2067 layout or subtype.

## Whole-Document Evidence and Learning

- Structured OCR preserves document/page/block reading order and protected
  provenance when available. Legacy text-only caches remain usable but cannot
  reconstruct historical page/block relationships without rerunning OCR; they
  are labeled `unavailable_legacy_flat` and are not regenerated automatically.
- Deterministic concepts and model-proposed observations remain visibly
  separate.
- Model observations must ground to valid request-local evidence aliases.
  Invalid references remain unsupported and contribute only PHI-safe failure
  counts and review state.
- The protected tester is a development and training tool for the full
  document processor. It reuses the selected processed document and may
  surface PHI-safe structure, family/subtype, modeled fields, deterministic
  concepts, model observations, contradictions, schema gaps, review reasons,
  coverage, and provenance.
- Protected literal evidence, OCR text, patient values, source filenames and
  paths, and `source_text` never appear in ChatGPT/Codex output.
- Cache-only evaluation cannot silently fall through to PaddleOCR. Paddle is
  initialized lazily only after validation, fingerprinting, and cache lookup
  establish that fresh prediction is permitted.
- `analyzed_evidence_block_count` may report zero even when all structured
  blocks were delivered and page coverage is complete. This is a reporting
  limitation, not proof of missing evidence.
- `learning_review_recommended` may remain true for novel or conflicting model
  observations even when deterministic production taxonomy is supported. It
  must not be conflated with family/subtype or top-level review state.

## Smartsheet Production Contract

- Smartsheet is an approved secure production destination for PHI and full
  explicitly mapped business content.
- After deterministic validation and business rules, the production flow
  attempts automatic row creation/population for every processed document,
  family, and subtype.
- Human review is downstream exception handling and is not an approval gate or
  prerequisite for row creation.
- Populate every explicitly mapped field with every sufficiently supported
  value, including PHI where intentionally mapped.
- Unsupported, missing, ambiguous, conflicting, invalid, guessed,
  low-confidence, or insufficiently supported values remain blank/null/unknown.
  Never invent a value or destination mapping.
- Unknown or review-required family/subtype still produces a row containing
  supported values and review metadata unless a real configuration,
  destination-validation, or write failure prevents a safe write.
- Existing downstream Smartsheet automations act on the populated row.
- The source document follows the approved attachment-upload path. OCR text
  and `source_text` have no approved Smartsheet destination and remain
  unmapped.
- Mailbox document jobs use protected digest-only atomic state. Confirmed or
  reconciled row references are persisted locally, attachment work resumes on
  the known row, and uncertain row/attachment outcomes remain fail-closed.
- Durable mailbox submission requires an explicitly configured, operator-
  approved technical submission-key column with no default. The application
  does not create or rename that column. Read-only live inspection found one
  exact-title, non-system TEXT_NUMBER column, and the corrected normalized-
  metadata schema gate passes.
- Production attachment naming uses the intake-team convention through the
  shared manual/unattended recovery path. It produces a complete business
  filename, a partial business filename with fixed placeholders, or the
  deterministic technical fallback; the protected source is never renamed.

The generic family/subtype-aware policy resolver uses the current explicit
field policies for Authorization, 2067/UTL, unknown taxonomy, and future
trained families unless an approved exact policy is registered. The current
nine extracted-value mappings are:

- Authorization Status
- Authorization #
- Service Codes
- Diagnosis Codes
- Start Date
- End Date
- Authorized Units
- Hours
- Days Per Week

Their confidence destinations and universal AI review/processing metadata are
validated before submission. Values below the existing 0.85 field-confidence
threshold, unavailable confidence, and deterministically unsupported values
remain blank in mapped value columns while protected review evidence is
preserved internally.

## Smartsheet Schema Evolution

The live destination schema is a Phase 1 testing scaffold, not the final
production schema. A separately authorized read-only `get_columns` inspection
completed successfully and found:

- 29 columns;
- no correction columns;
- no dropdown options;
- no enforced column validation;
- no column formulas;
- no same-sheet formula dependencies; and
- no cross-sheet formula references visible in column metadata.

The existing integration and installed SDK surface did not expose Smartsheet
automation definitions, so the inspection did not prove that automations are
absent or identify their internal dependencies. No rows, cells, row IDs,
payloads, option values, formula text, or PHI were requested or returned in
the approved output, and the sheet was not modified.

Current mappings are not the final field set. As representative document
training reveals operationally useful fields, the operator may approve new
Smartsheet columns. Each approved field then receives an explicit mapping,
deterministic validation, and regression coverage. The platform never
auto-creates, renames, infers, or maps columns. Mapping architecture must
support new approved fields without redesign.

## Authoritative Phase 1 End-User Feedback Model

End users work entirely in Smartsheet, not in the codebase. The intentionally
minimal Phase 1 model is:

- one generic checkbox/flag indicating that the AI result on the row is
  incorrect; and
- the row's existing Smartsheet comments/conversation for the end user's
  explanation.

The original AI-written row values remain visible. A flag turns the row into a
controlled investigation case; it does not directly correct operational
cells. Phase 1 does not require separate per-field correction columns,
separate family/subtype correction columns, or effective-value columns. The
exact checkbox title remains intentionally undecided until implementation is
authorized.

The platform now has a standalone, read-only, mock-tested ingestion boundary
for normalized flag state and row discussions. It uses injected readers,
requires a configured checkbox title and protected source scope, accepts only
literal internal booleans, and stores protected cases under the ignored
`data/smartsheet_feedback/` boundary. Stable row-correlation and comment-
snapshot digests make unchanged readback idempotent while allowing a later
added or edited comment to create a new case revision. Only PHI-safe counts,
statuses, and allowlisted categories leave the boundary.

No live Smartsheet reader or SDK value normalization is implemented, and the
checkbox column has not been created. A flag or comment never automatically
retrains a model, changes prompts, modifies production rules, or promotes
model observations. The technical owner investigates the case locally,
identifies the correct layer, implements an evidence-backed change, and adds
regression coverage before controlled production promotion.

This design may evolve only when later evidence proves that more structure is
needed and the operator approves it.

## Current Implemented Capabilities

- Microsoft Graph mailbox access and attachment handling.
- Durable local mailbox message idempotency and protected candidate ordering.
- Durable per-attachment mailbox jobs with atomic state, processing leases,
  exact submission-key row reconciliation, attachment reconciliation, and
  handled/read completion only after every message job completes.
- Local PaddleOCR with protected flat and structured cache support.
- Local Ollama classification, extraction, and opt-in whole-document learning
  analysis.
- Field/service-line value, confidence, and source-evidence preservation.
- Controlled extraction retry with independent candidate validation and
  deterministic selection.
- Evidence validation, Authorization business rules, review output, and
  staff-friendly Smartsheet review summaries.
- Central family/subtype taxonomy with Authorization compatibility and
  accepted 2067/UTL deterministic resolution.
- Generic automatic Smartsheet mapping, destination validation, row writing,
  review metadata, partial-success propagation, and source attachment.
- Read-only Smartsheet feedback-ingestion contracts with injected row and
  discussion readers, strict normalized booleans, protected revisioned case
  storage, idempotent snapshots, and PHI-safe public results. No live adapter
  or production caller is connected.
- Local classification-review and PHI-safe ignored feedback storage from an
  earlier operator-driven workflow. This remains a separate development
  capability and is not the authoritative Smartsheet end-user feedback model.
- PHI-safe Graph, mailbox, OCR, evaluation, and integration diagnostics.
- Opt-in local protected document listing/selection/review and cache-only
  evaluation.
- Acceptance-only PHI-safe local mailbox candidate selection with bounded
  metadata discovery, exact Inbox re-verification, and no newest-unread
  fallback. Normal unattended enumeration is unchanged.
- Validated business-reference workbook boundary and production filename
  assembly with complete/partial/technical outcomes, fixed placeholders, and
  durable restart-safe attachment-name persistence.
- Prefect 3.8.4 pinned with a self-hosted localhost server/UI, native process
  work pool/worker, versioned synthetic deployment, PHI-safe flow/task, and
  copy/paste-verified Windows operator guide. The parameterless mailbox adapter
  is import/mock-tested and registered as a manual-only deployment. One later
  real run reached application processing with one candidate message and two
  candidate documents before safe operator cancellation; the exactly-one-
  message/exactly-one-document guard was added afterward and verified
  read-only. That registered manual path now uses a local popup-selected
  candidate with newest-ten metadata discovery, exact Inbox re-verification,
  and no newest-unread fallback. A later guarded acceptance stopped at
  preflight because the submission-key configuration readiness gate was false;
  no flow ran.

## Verified Current Baselines

### Generic Production Row

- Generic family/subtype mapping, including shared 2067/UTL routing, passed 59
  focused synthetic deterministic/mock checks and 144 affected regressions
  with zero failures.
- Unknown taxonomy and review-required rows remain writeable with supported
  values and review metadata.
- No subtype-specific writer or destination column was introduced.

### Family/Subtype and Grounding

- Family/subtype and grounding changes passed 57 focused synthetic
  deterministic/mock checks and 214 affected regressions with zero failures.
- The accepted real 2067/UTL cache-only result is recorded under Accepted UTL
  Behavior. It used real cached OCR and real local Ollama but no Paddle
  prediction or external integration.

### Production and Integration Safety

- One explicitly authorized real production item completed Graph retrieval,
  attachment download, local OCR/AI processing, validation, business rules,
  Smartsheet row creation, attachment upload, mailbox handled/read state, and
  durable idempotency. This proves one controlled path, not unattended or
  universal acceptance.
- Automatic-write regressions passed 286 synthetic deterministic/mock checks
  with zero failures after removal of the obsolete human-approval write gate.
- Partial-success/retry regressions passed 12 focused and 123 affected tests
  with zero failures.
- One explicitly authorized PHI-free synthetic live acceptance created one
  technical-key-only row and one tiny attachment. Deterministically suppressed
  application responses were reconciled to exactly one existing row and one
  existing attachment without duplicate mutation; a repeated recovery call
  was a no-op. The captured attachment and row were deleted, and exact-key
  cleanup verification returned zero matches.
- Graph security and mailbox diagnostic regressions remain synthetic/mock for
  negative authentication and legacy live-output cases.

### Prefect Development Control Room

- Prefect 3.8.4 was installed in the Python 3.13.14 project virtual
  environment and passed dependency validation.
- The installed CLI help verified the documented profile, configuration,
  server, pool, concurrency, deployment, worker, and run command signatures.
  UTF-8 output and explicit per-command profile selection are required for
  copy/paste-safe PowerShell 5.1 startup from a stopped system.
- Five focused synthetic checks passed. Two manual localhost process-worker
  runs reached Completed with one flow and one task; UI, API, and worker-health
  endpoints returned success. No Graph, Smartsheet, OCR/Paddle, Ollama,
  patient-document, or production mailbox operation occurred.
- Full-orchestration, durable recovery, mailbox-handling, partial-success, and
  automatic-write regressions passed. The older persistent-idempotency script
  was reconciled to the current supported-attachment and delayed-completion
  interfaces and now proves handled-state survival across processor instances
  only after durable attachment completion.
- The application now returns allowlisted stage/status, sanitized failure
  category, fail-closed retryability, bounded durable attempt totals, and
  bounded completion/pending counts. Uncertain, corrupt/inconsistent,
  duplicate/permanent-blocked, active-lease, and insufficient-evidence states
  remain non-retryable. The pending count is invocation-local, not global
  mailbox backlog.
- Native PostgreSQL 17.11 is installed as a manual-start, loopback-only service
  with SCRAM, a least-privilege Prefect role/database, and a current-user DPAPI
  secret boundary. Prefect reported PostgreSQL 17.11 through the process-local
  launcher. Five sequential process-worker runs completed with five tasks,
  run count one, zero retries, pool concurrency one, and healthy API/worker
  endpoints. Server, worker, and PostgreSQL were stopped afterward.
- Prefect 3.8.4's offline `database upgrade --dry-run` is a verified upstream
  dry-run-only defect: Alembic emits SQL and returns no cursor result while
  historical migration `14dc68cc5853` dereferences `result.rowcount`. Online
  migration uses a real result and is unaffected. The database has exactly one
  revision equal to the sole installed PostgreSQL head `9e9dadc36797`; aggregate
  flow/task state-name invariant gaps are zero. The explicit exception applies
  only to Prefect 3.8.4 and must be rechecked on every version change.
- The manual mailbox deployment retains the fixed application entrypoint,
  empty parameters, no schedules or automations, manual/PHI-safe tags,
  deployment concurrency one with CANCEL_NEW, pool concurrency one, one
  application task, and zero retries. The current source adds acceptance-only
  popup selection, bounded metadata discovery, exact Inbox re-verification,
  and PHI-safe stage events. Registration metadata and current-HEAD source
  assertions passed without creating a worker or flow.

### Authorization

- A controlled real cached-OCR/local-Ollama Authorization regression selected
  retry attempt 2, preserved two supported service lines and row-owned
  modifier evidence, cleared unsupported dates/statuses, required review, and
  passed its semantic harness with PHI output suppressed.
- Quantity reconciliation remains within one candidate; top-level units,
  approved visits, service-line quantities, and modifier ownership are never
  inferred across unsupported evidence.

### OCR Performance

- Paddle 3.2.0 and PaddleOCR 3.7.0 on the current CPU environment were used in
  the controlled comparison.
- `PP-OCRv6_medium_det` with `PP-OCRv6_medium_rec` required about 2670 seconds
  for eager prediction and about 2675 seconds total.
- Changing only detection to `PP-OCRv6_small_det` while retaining
  `PP-OCRv6_medium_rec` reduced prediction to about 107 seconds: approximately
  25 times faster and about a 96 percent reduction.
- Both configurations made one document submission and one prediction and
  produced four pages and 144 blocks. The small-det result preserved the
  preselected PHI-safe indicators 2067, Posted Date, annual, and deterministic
  `contact_failure` on that controlled document.
- About 99.8 percent of the medium-det runtime was inside eager
  `PaddleOCR.predict()`. Structured evidence construction, conversion,
  serialization, and cache writes were negligible and are not supported
  causes of the slowdown.
- Small detection plus medium recognition is a strong candidate, not an
  approved universal production default. One document does not prove accuracy
  equivalence across all layouts and purposes.
- The historical approximately seven-minute configuration is unknown. There
  is no evidence that it used the small detector.
- Package/model defaults remain insufficiently pinned. Production OCR model,
  package, and effective inference settings must become explicit and
  controlled rather than relying silently on defaults.

## Phase 1 Finish Line and Remaining Gaps

The document processor is complete only when it is live in the approved
environment and reliably performs:

automatic ingestion
-> OCR and whole-document understanding
-> family/subtype recognition
-> extraction
-> deterministic validation
-> business rules
-> automatic full Smartsheet row population through explicit mappings
-> downstream Smartsheet automations
-> downstream human review where needed
-> simple incorrect-AI checkbox/comment feedback
-> controlled technical improvement loop

Completion also requires acceptable performance, explicit model/configuration
control, safe retries and restarts, no lost documents, no duplicate business
actions, PHI-safe operational diagnostics, sufficient real-document
acceptance coverage, hardened durable idempotency/mailbox-state ordering for
unattended operation, and final separately authorized end-to-end production
acceptance.

### Live / Unattended Definition

Phase 1 is live only when the document processor:

- starts automatically after a production-host reboot;
- runs without ChatGPT, Codex, or an interactive PowerShell session;
- does not require an operator to start each document;
- continuously monitors approved Outlook/Graph sources;
- safely claims and processes eligible documents automatically;
- survives temporary failures and resumes safely after restart;
- prevents duplicate business actions;
- exposes PHI-safe operational health information; and
- writes supported results automatically to Smartsheet.

A manual script successfully processing a document is useful acceptance
evidence but does not make Phase 1 live.

### Ordered Path to Live Production

1. Reconcile authoritative project truth.
2. Implement the minimal Smartsheet incorrect-AI checkbox/comment feedback
   path.
3. Keep the Smartsheet schema/mapping layer extensible as document training
   reveals useful fields.
4. Continue training and validating document families/subtypes with
   representative real documents.
5. Finish whole-document tester and learning-report quality.
6. Productionize OCR model configuration/performance and validate the
   small-det plus medium-rec candidate.
7. Harden retries, restart recovery, idempotency, attachment handling, and
   mailbox handled-state ordering.
8. Run one separately authorized, preflight-gated manual mailbox deployment
   acceptance without enabling schedules or Prefect retries.
9. Finish unattended Outlook/Graph ingestion behavior.
10. Finish PHI-safe operational monitoring and readiness.
11. Run broad representative real-document acceptance.
12. Validate the Smartsheet incorrect-AI checkbox/comment feedback loop.
13. Run Codex Security as a production-readiness security checkpoint.
14. Configure always-on Windows deployment, startup, and recovery.
15. Run controlled real Outlook -> processor -> Smartsheet end-to-end
    acceptance.
16. Perform a limited live rollout.
17. Promote to unattended production only after acceptance gates pass.

Current gaps and limitations include:

- The incorrect-AI checkbox does not yet exist in the inspected live schema.
  Its exact title requires approval, and no live flagged-row/comment adapter,
  SDK checkbox normalization, or production caller is implemented. The local
  injected-reader ingestion and protected case-storage boundary is complete
  only at the synthetic/mock level.
- The PHI-safe self-hosted Prefect PostgreSQL control room and parameterless
  mailbox adapter are implemented, and the adapter is registered only as a
  manual deployment. PostgreSQL removed the observed SQLite
  locking, and
  the Prefect 3.8.4 dry-run-only defect has a version-bounded operational
  exception backed by online migration, head-revision, invariant, and synthetic
  acceptance. Automatic startup, scheduling, and Prefect retries remain
  disabled.
- The technical Smartsheet submission-key title was supplied session-only for
  authorized read-only acceptance. Exactly one matching TEXT_NUMBER column
  exists and passes the corrected non-system-column schema gate. Controlled
  exact-key row and attachment read-after-write reconciliation passed with one
  PHI-free synthetic case and deterministic cleanup.
- The controlled acceptance proves the existing fail-safe reconciliation path
  for one synthetic case, not broad production reliability. Unattended retries
  from uncertain row or attachment outcomes remain disabled pending broader
  operational acceptance.
- OCR small-det accuracy needs broader representative-document acceptance
  before any production-default change.
- Paddle/PaddleOCR packages, resolved model identities, and effective runtime
  configuration are not yet fully pinned for reproducible deployment.
- Existing text-only OCR caches cannot recover historical page/block
  relationships without new OCR.
- Final taxonomy and explicit Smartsheet mappings will expand through
  evidence-backed document training.
- Quantity meaning, final approval, and modifier ownership remain conservative
  where deterministic evidence is insufficient.
- The first protected local review comparison and broader real-document
  acceptance remain incomplete.
- Intake filename-subtype coverage is intentionally incomplete. `AUTH INIT`
  requires approved external client/service context and cannot be inferred
  from document evidence; unknown supported categories/subtypes use fixed
  placeholders and downstream review rather than guesses.
- Legitimate service-reference conflicts remain unresolved until the owner
  provides a supported discriminator; description and other existing fields
  must not be used to invent priority.
- Future EHR, eligibility, queue/resource scheduling, and other company-AI
  subsystems remain future direction, not active Phase 1 implementation.

## Developer Tool Evaluation Checkpoints

Tool evaluation must not distract from Phase 1 document-processor completion.
Codex should proactively call out when the project reaches one of these
evidence-based checkpoints:

- WarpGrep: evaluate only if Codex repository search/inspection becomes a
  meaningful time, token, or context bottleneck. Complete a security, privacy,
  and data-flow review first. Never expose protected documents, OCR text,
  PHI-bearing caches, `.env` values, secrets, credentials, or protected paths.
- Superpowers: evaluate when a genuinely complex Phase 1 multi-file
  implementation or refactor could materially benefit from subagents. Test it
  first on a PHI-safe task and verify that every subagent follows `AGENTS.md`,
  preserves uncommitted work, and does not broaden scope.
- Codex Security: use as a production-readiness gate after functional
  document-processing completion and before unattended go-live.
- `create-plan`: do not adopt by default. The existing `/plan` workflow is
  sufficient unless evidence demonstrates a material gap.
- `gh-fix-ci`: defer until GitHub Actions/CI is a regular validation boundary.

## Memory Maintenance

Every update to this file must reconcile the entire affected current-state
model. Preserve statements that remain current, rewrite superseded truth,
remove conflicts, and consolidate duplicates. Do not append new rules beneath
older conflicting rules. Retain older test observations only when they remain
useful and are clearly labeled historical. Keep the file concise enough to be
an authoritative working context and keep exactly one `CURRENT NEXT START`.

Before editing or implementation, inspect actual Git state, callers,
interfaces, tests, runtime configuration, and relevant tracker checkpoints.
After meaningful tested work, update the tracker and this file consistently;
run the tracker and require `Not Found : 0` and `Failed : 0` before commit.

Begin Day and End of Day follow the full procedures in `AGENTS.md`. Begin Day
must read this entire file and verify Git/local/remote state. End of Day must
reach a safe tested checkpoint, reconcile tracker and memory, complete the Git
safety review, commit and push, verify synchronization, and leave one exact
next start. Neither procedure authorizes PHI-sensitive or external operations
without the required separate approval.

Startdp progress and bounded-startup checkpoint:

- Read-only post-interruption evidence proved the silent start reached a
  correctly owned DP runtime and descendant worker in healthy `waiting` state.
  The operator saw no progress because the StartDP dispatch buffered the
  function stream through an outer `Write-Output` expression.
- Startup also had unbounded Prefect CLI inspections and parent/child Graph-
  auth subprocess calls. Prefect CLI and Graph startup checks are now bounded
  at 30 seconds, consistent with the existing Graph transport timeout; worker
  readiness remains bounded at 90 seconds through five-second API requests.
- StartDP now immediately flushes five fixed PHI-safe progress stages, a
  periodic worker-wait indication, stable success output, and fixed failure
  stage/category output. Readable status/statusdp and `-Json` are preserved.
- An incomplete or interrupted startup after DP ownership is recorded now
  cleans the proven owned process tree in `finally`. External/unproven and
  PID-reused processes remain protected. The existing live runtime was not
  stopped or otherwise mutated during this code checkpoint.
- Modified Python/tests compiled, modified PowerShell parsed in Windows
  PowerShell 5.1, and focused/affected synthetic deterministic, mock, isolated-
  profile, and isolated local Prefect regressions passed. The known disposable
  host-CIM fixture remained excluded after the real DP identity was separately
  proven. No new startdp, worker/deployment start, live mailbox/Graph document
  access, protected OCR/Ollama, production document Smartsheet operation, or
  mailbox mutation occurred.

First unattended document-result diagnosis checkpoint:

- Read-only Prefect/control-state evidence proved one completed unattended
  document workflow with retry, extraction attempt 2, review required,
  automatic row/attachment success, mailbox finalization, and return to
  waiting. Durable job state retained only safe completion/attempt counts; it
  does not persist the historical review reason list.
- The attachment name equaled the AI Submission Key because the durable
  Smartsheet recovery service intentionally used `job_key + extension` as both
  the row reconciliation key and technical attachment name. Manual and
  unattended processing share this same recovery path.
- The intended evidence-driven filename policy and temporary naming service
  are implemented and synthetic-tested, but production filename assembly is
  still intentionally unwired. Current production extraction does not supply
  the policy's separately supported person-name parts and authoritative payer,
  service, and optional workflow reference lookups. Those values must not be
  reconstructed from a combined name, sender, payer context, filename, or
  unsupported evidence.
- Retry triggered, attempt count, and selected attempt are copied only as
  operational metadata. They are not inputs to `ReviewDecisionService` and do
  not cause review. Classification, subtype, populated-field confidence,
  validation, and business rules remain separate.
- For an authorization with any positive quantity, the committed conservative
  business rule adds the safe deterministic category
  `authorization_quantity_requires_verification`; this is intentional because
  quantity meaning and sufficient approval remain unresolved. A 100%
  classification confidence and all displayed field confidences above the
  field threshold can therefore coexist with recommended review.
- The historical run's complete reason set cannot be proven from retained
  PHI-safe evidence: Prefect persisted only the review boolean and the row
  mapping stored a generalized summary. Do not infer whether quantity was the
  only reason or whether additional validation/business-rule reasons existed.
- Corrected two proven defects for future results. The recognized successful
  authorized-units reconciliation action no longer creates review by itself,
  and Smartsheet `AI Review Reasons` now receives deduplicated fixed PHI-safe
  reason codes instead of generalized `manual review needed` prose. Unknown
  reasons become safe category/cause codes without carrying source text or
  values.
- Focused/affected synthetic deterministic/mock/local-file tests passed for
  review decisions, retry/attempt-2 independence, classification/field-
  confidence separation, reason-code mapping, filename policy/input/builder,
  attachment naming, durable recovery, explicit Smartsheet mapping, and
  orchestration. No live mailbox/Graph, OCR/Ollama, deployment, production
  Smartsheet write/upload, or mailbox mutation occurred.

Production filename assembly checkpoint:

- The shared manual/unattended recovery boundary assembles only independently
  validated naming evidence and authoritative reference tokens. Combined
  patient name, sender, mailbox metadata, source filename, and payer/source
  context are never used to infer business components.
- The production filename target is
  `<LAST, FIRST [MIDDLE]>_<PAYER>_[SERVICE]_<DOCUMENT TYPE>_<DATE[-DATE]>.<EXT>`.
  Optional absent components are omitted; meaningful unresolved components
  use fixed placeholders when core person identity and the extension are safe.
- The exact attachment name and fixed-safe decision metadata are persisted
  before external row creation. Restart/reconciliation never recomputes a
  stored name. The AI Submission Key remains solely the durable row,
  idempotency, and reconciliation key.
- Focused and affected synthetic deterministic/mock/local-file checks passed
  for policy composition, authoritative lookup ambiguity, technical fallback,
  extraction schema/prompt safeguards, temporary-copy safety, durable recovery,
  duplicate prevention, and the preserved review-decision/reason changes. No
  live mailbox/Graph, OCR/Ollama, deployment, production Smartsheet write or
  attachment upload, or mailbox mutation occurred.

Validated confidence/source-support consistency checkpoint:

- Classification confidence, subtype evidence confidence, scalar extraction
  confidence, service-line confidence, and displayed minimum field confidence
  remain separate. The current production scalar-field acceptance threshold is
  `>= 0.85`; exact equality passes. The deterministic 0.95 value is a cap on
  model-reported extraction confidence, not the production review threshold.
  Classification confidence is never substituted for a field confidence and
  missing classification confidence is not assigned 1.0.
- Deterministic invalidation now preserves the original candidate value and
  confidence inside the protected review contract while setting the validated
  production value to null and validated confidence to zero. Service-line
  candidate evidence is likewise preserved while unsupported individual row
  components remain null. Neither candidate values nor candidate confidence
  are mapped into validated production columns.
- Numeric Smartsheet confidence columns now describe only mapped, validated
  production values. Missing, invalidated, unsupported, or below-threshold
  values leave both production value and numeric confidence blank unless an
  explicitly text-capable confidence destination carries a fixed safe status.
  `AI Minimum Field Confidence` is calculated only from displayed validated
  field confidences. Classification confidence remains confined to its own
  column.
- Review-reason summarization now preserves service-line scope. Unsupported
  modifier, quantity, date, status, and service-code row components receive
  `service_line_*` reason codes; low row confidence becomes
  `service_line_low_confidence`; unresolved top-level modifier ownership becomes
  `modifier_ownership_unresolved`. These no longer collapse into misleading
  top-level or `document_details_low_confidence` categories.
- A reusable PHI-safe field diagnostic exposes only category, candidate
  confidence, threshold result, source-support proof, validated-value presence,
  validation result, review trigger, and safe reason code. Filename diagnostics
  expose only person/payer/service/date/workflow readiness, qualifier state,
  and Business versus Technical Fallback. Unsupported required naming evidence
  continues to fail closed to the deterministic technical filename.
- Quantity meaning remains a separate business-rule concern:
  `authorization_quantity_requires_verification` remains valid even when a
  quantity is confidently extracted and source-supported. Retry/attempt 2 and
  successful authorized-units reconciliation remain non-review triggers.

Smartsheet action visibility checkpoint:

- Durable recovery now reports fixed PHI-safe row actions (`created`,
  `reconciled_existing`, `skipped`, or `failed`) and attachment actions
  (`uploaded`, `reconciled_existing`, `skipped`, or `failed`). An already
  completed durable job is an intentional skip; an existing row or attachment
  proven during the current recovery attempt is reconciliation, not a new
  external action.
- Prefect lifecycle tasks use action-specific operator labels for row creation,
  row reconciliation, row skips, attachment uploads, attachment
  reconciliation, and attachment skips. The Workflow Summary includes both
  actions, row/attachment attempt counts, written/failed counts, completed
  document count, and final status. Visibility remains best effort.
- `written_count` counts newly created rows and no longer increases for
  reconciliation or an already-completed no-op. Durable row and attachment
  attempt counters increase only when the corresponding external create or
  upload call actually occurs, including a lost response later confirmed by
  exact reconciliation.
- Exact-key and exact-attachment reconciliation, restart safety, duplicate
  prevention, mailbox completion ordering, and shared manual/unattended
  semantics are unchanged. Focused and affected synthetic deterministic/mock
  tests passed without live mailbox/Graph, protected OCR/Ollama, deployment,
  production Smartsheet write/upload, or mailbox mutation.

Review-state and business-filename resolution checkpoint:

- Formalized the PHI-safe validation states `not_present`,
  `missing_required`, `accepted`, `low_confidence`, `unsupported`,
  `conflicting`, `ambiguous`, and `invalid`. Authorization requiredness remains
  sourced from the existing business rule; optional extraction/service-line
  fields are not promoted to required fields.
- Explicitly absent optional evidence now has no validated confidence entry,
  does not lower minimum displayed confidence, and does not create validation
  or review noise. Unsupported candidates retain protected candidate evidence
  but remain absent from validated production values/confidences.
- Service-line low-confidence review now uses the original candidate line
  confidence, not the post-validation 0.50 safety downgrade caused by rejecting
  one child component. Specific source-support and modifier-ownership reasons
  remain when their present candidate evidence actually fails validation.
- Smartsheet AI Review Reasons are concise, deterministic, human-readable,
  PHI-safe phrases. Fixed internal codes remain available separately for
  diagnostics and Workflow Summary categories.
- Authoritative payer lookup now tolerates an omitted optional key only when
  one payer result remains. Service lookup tolerates absent optional modifier/
  program dimensions only when all compatible rows yield one naming token;
  ambiguity still fails closed. A single supported service date is correctly
  marked naming-ready because the filename policy already supports a single
  date or a range.
- The ignored reference cache passed read-only schema validation with nonzero
  payer and service tables. Workflow Summary now includes safe filename
  component readiness, qualifier state, business/fallback result, review reason
  count, and fixed reason categories. Historical live fallback component(s)
  were not persisted before this checkpoint, so the prior run cannot be
  retrospectively attributed to one specific component without exposing or
  rerunning protected evidence.

AI Correction human-feedback mapping checkpoint:

- The approved production row mapping explicitly initializes the Smartsheet
  checkbox `AI Correction` to false only when creating a brand-new AI document
  row. Its value is independent of review-required state, review status,
  review reasons, and confidence.
- Destination readiness requires the exact `AI Correction` column and proves
  its schema type is `CHECKBOX`; no column identifier is hard-coded.
- After creation the checkbox is human-owned. Durable exact-key row
  reconciliation, restart recovery, completed-job no-op, and attachment-only
  reconciliation do not update existing rows, so checked and unchecked human
  feedback are preserved.
- No Smartsheet Conversations/comments read, parse, or write behavior was
  added. Focused and affected synthetic deterministic/mock tests passed with
  no live Smartsheet, Graph/mailbox, protected OCR/Ollama, deployment, or
  mailbox mutation.

Final-state consistency, quantity-unit, workflow, and filename checkpoint:

- Review confidence now evaluates each populated final field explicitly.
  Missing confidence remains a field-specific review condition but is not
  converted into a synthetic 0% aggregate. Low-confidence reasons identify
  the exact safe field/category; accepted fields at or above 0.85 do not
  receive low-confidence review.
- A validated plural service-code production field supersedes redundant
  singular helper-field conflict/support/confidence noise. Naming reference
  lookup failures remain filename-only and cannot create extraction review.
  Authorization status `None` is correctly treated as missing required rather
  than the literal text `None` or an unsupported status.
- Supported authorization quantity is source-validated. An explicit supported
  unit (Hours, Units, Visits, or Sessions) is preserved with
  `explicit_document_evidence` provenance. When no unit claim exists, Hours is
  applied with `business_default_hours` provenance. An explicit unsupported,
  conflicting, or ambiguous unit fails closed; the default never replaces it.
  Quantity/unit does not establish approval, visits, sessions, or sufficiency.
- The approved `Authorized Units` Smartsheet cell renders quantity with the
  separately resolved unit while its confidence remains the quantity's own
  validated confidence. Successful authorized-units reconciliation remains
  informational and does not itself trigger review.
- Legacy authorization routing does not determine the intake-team filename
  subtype. The separate naming subtype must be supported by explicit document
  evidence or approved authoritative context; `AUTH INIT` specifically
  requires external context and is never inferred from renewal/initial routing.
- Review summaries prefer concise field/category-specific reasons, remove
  generic document-detail noise when a specific reason exists, and distinguish
  required missing fields from optional absence. Fixed internal categories
  remain available for PHI-safe diagnostics.
- Filename assembly can use one independently validated top-level service code
  when no service-line representation exists, keeps authoritative lookup
  failures scoped to naming, aligns date readiness with top-level or line
  dates, and emits a fixed `filename_failure_category` on technical fallback.
- Workflow Summary now includes filename failure category, final-state counts,
  quantity presence, and unit-source category without values. AI Correction
  remains create-time false and human-owned; comments remain untouched.

Intake-team business filename checkpoint:

- The authoritative production target is
  `<LAST, FIRST [MIDDLE]>_<PAYER>_[SERVICE]_<DOCUMENT TYPE>_<DATE[-DATE]>.<EXT>`.
  First and last name must be independently validated; middle name and service
  are optional when genuinely absent. A valid single date or ordered range is
  used. Supported extensions are normalized to uppercase in business names.
- Every new processed document attempts business composition. The three fixed
  outcomes are `complete_business`, `partial_business`, and
  `technical_fallback`. Unresolved payer, expected service, document type,
  authorization naming subtype, or naming date uses `[PAYER]`, `[SERVICE]`,
  `[DOCUMENT TYPE]`, `[SUBTYPE]`, or `[DATE]` and produces a partial business
  name. Technical fallback is reserved for unresolved independent first/last
  identity, unsupported extension, or unsafe composition.
- Intake naming subtype is separate from the legacy classifier subtype used
  for routing. Authorization vocabulary is centrally defined as `AUTH INIT`,
  `AUTH NO CHANGE`, `AUTH INCREASE`, `AUTH DECREASE`, `AUTH TERM`, `AUTH STUB`,
  `AUTH INBOUND`, `AUTH GAP FILL`, `AUTH NEW SVS`, `AUTH MOD CHANGE`, `AUTH RPM`,
  `AUTH READMIT`, `AUTH TASKS ADDED`, and `AUTH RESUME SVS`. `INBOUND AUTH`
  canonicalizes to `AUTH INBOUND`. `AUTH INIT` requires authoritative external
  context; legacy initial/renewal labels never supply it. Unknown authorization
  naming subtype becomes `AUTH [SUBTYPE]` and exactly one human reason,
  `AI Document Subtype: Unknown`, without changing category confidence.
- Known non-authorization top-level tokens are centralized for 2067, POC, VOE,
  REFERRAL, ASSESSMENT, APPROVAL LETTER, ADVERSE DETERMINATION LETTER, ACK,
  3052, PROVIDER NEWS, CLINICAL PRACTICE GUIDELINES, BAD FAX, and SPAM. The
  existing deterministically supported authorization-termination route maps to
  `AUTH TERM`; service termination remains unresolved rather than being merged.
- Authoritative payer and service failures never guess or expose a value.
  Payer failure uses `[PAYER]`. Service is omitted when not applicable, uses a
  resolved token only when all supported service identities agree, and uses
  `[SERVICE]` when expected but unresolved. Naming lookup failure remains
  separate from extraction validation.
- Review output continues to derive from final validation state. Optional
  absence does not create review noise. Partial-business filename placeholders
  are naming diagnostics only and never independently create review. Technical
  fallback retains fixed actionable naming reasons. Legacy request-selection
  evidence remains protected internal metadata and is not an operator review
  field or an alias for document subtype.
- Workflow Summary reports business attempt, complete/partial/technical result,
  document-type/subtype readiness, placeholder count/categories, optional
  omission count, and technical fallback reason without values. These safe
  decision fields are persisted with the exact protected attachment name, so a
  restart never recomputes the name or loses its safe filename diagnostics.
- The AI Submission Key remains internal to durable row/idempotency/
  reconciliation state and is not the normal attachment filename. Source files
  are never renamed; only temporary upload copies use the selected filename.
- Focused and affected synthetic deterministic/mock/local-safe regressions and
  isolated local Prefect visibility passed. No live mailbox/Graph, protected
  OCR/Ollama, production Smartsheet/document, comment, deployment, worker, or
  mailbox mutation occurred.

Current-source registration and payer-readiness checkpoint:

- Refreshed all three standardized deployments from clean committed HEAD
  `5e47350db37e2996b393aab57aa4e2ae1fcc6d63` using the repository-supported
  Prefect 3.8.4 `deploy --all --no-prompt` mechanism. All registered versions
  changed, each entrypoint/work-pool/current-repository pull contract matches,
  and schedules and parameters remain empty. Manual/live concurrency remains
  one with `CANCEL_NEW`.
- Historical flow-run counts were unchanged by registration. Direct Prefect
  API verification found zero active runs for all three deployments and zero
  fresh workers. The process pool configuration is unpaused process type with
  concurrency one; its runtime status is expectedly not ready without a worker.
- The ignored last-known-good reference cache and metadata are present and
  valid, with nonzero payer and service mappings. No live Graph reference
  download was performed.
- No approved local input contains the payer intended for the next test
  document. Therefore `payer_evidence_available=false`, exact match count is
  zero because no lookup input was available, and resolution is `unavailable`.
  This does not prove either a reference-data gap or a code defect, and no
  payer mapping was broadened, aliased, inferred, or changed.

Final-state review scoping and presentation checkpoint:

- Review ownership is now explicit across layers. Final validated field state
  and business requiredness create review reasons; authoritative filename-token
  lookup failures and partial-business placeholders remain Workflow Summary
  diagnostics and cannot create payer, service, date, document-type, or subtype
  review by themselves.
- Authorization intake naming subtype is the single owner of the unresolved
  subtype condition. An unresolved applicable subtype produces exactly
  `AI Document Subtype: Unknown`; a supported intake subtype supersedes an
  unknown legacy routing subtype without altering document-category confidence.
- The legacy `request_type` extraction candidate remains available in the
  protected review contract, but it is internal-only: its validation actions,
  confidence, and state do not enter operator review reasons, minimum displayed
  confidence, or Workflow Summary final-state counts.
- Smartsheet-facing reasons now use the fixed `<Business Field>: <Problem>`
  presentation. Specific validation failures supersede broad missing-rule
  duplicates. Authorization start-date failures retain exact missing, invalid,
  conflicting, or unverified scope; service-line quantity/status/date/modifier
  failures retain service-line scope; generic document-information wording is
  removed whenever a specific category exists.
- A successful supported service-line reconciliation is authoritative for final
  `authorized_units` state and suppresses the superseded top-level source-action
  and broad missing-quantity reason. Genuine service-line quantity failures
  remain reviewable and supersede duplicate generic quantity wording.
- Existing complete/partial/technical filename policy, persisted attachment
  identity, duplicate prevention, manual/unattended shared path, AI Correction
  human ownership, and comments boundary are unchanged. Focused and affected
  tests used only synthetic data, mocks, local temporary files, and an isolated
  local Prefect server; no live mailbox/Graph, protected OCR/Ollama, production
  Smartsheet document/comment, deployment/worker, or mailbox mutation occurred.

Smartsheet uncertain-row recovery checkpoint:

- The retained PHI-safe durable state proves the failed business-action cycle
  crossed the application row-create boundary once, did not establish a row
  identity, and never attempted an attachment. The former implementation then
  performed exact-key reconciliation but collapsed authoritative zero matches
  and reconciliation unavailability into the single non-retryable
  `row_write_outcome_unknown` state. Retained evidence cannot distinguish a
  transport exception from an unusable success response or prove wire-level
  issuance.
- Row creation now persists a leased `row_create_in_flight` state before the
  client boundary. Confirmed creates become `created`; exactly one exact-key
  match becomes `reconciled_existing`; multiple matches block permanently;
  unavailable reconciliation remains `reconcile_only`; and an authoritative
  zero-match result becomes `retry_ready`. A later bounded cycle may create
  only after acquiring the same durable job lease and repeating exact-key
  zero-match reconciliation. The original durable job is reused, so recovery
  does not require resending the document.
- Smartsheet SDK sends now have a default 30-second HTTP timeout, configurable
  only by the positive numeric `SMARTSHEET_HTTP_TIMEOUT_SECONDS` setting.
  Definite API rejection, timeout, invalid response, and otherwise uncertain
  transport outcomes use fixed PHI-safe categories. The legacy direct retry
  boundary blocks existing and uncertain row outcomes; durable mailbox recovery
  is the only path that may re-enter after exact reconciliation.
- Row and attachment attempt counters are durably reserved immediately before
  their external client calls. Reconciliation never increments them. Attachment
  lookup/upload remains blocked until row identity is proven, and an uncertain
  attachment is never blindly uploaded again.
- Prefect lifecycle visibility now distinguishes Row Create Attempted, Row
  Created, Row Reconciled, Row Write Failed, Row Outcome Unresolved, and
  Attachment Blocked. Workflow Summary adds row-outcome proof, reconciliation
  cardinality/recovery state, attachment-blocked, retryable, and recoverable
  fields without identifiers or values.
- Modified Python compiled and focused/affected synthetic deterministic, mock,
  local temporary-state, and isolated local Prefect regressions passed. No live
  mailbox/Graph, protected OCR/Ollama, production Smartsheet operation,
  deployment/worker start, attachment upload, or mailbox mutation occurred.

Prior uncertain-row recovery next-start checkpoint:

Refresh the affected deployment/source registration, then perform a controlled
recovery of the existing durable uncertain mailbox job without resending the
document. Verify exact-key reconciliation first; if it proves zero matches,
verify the job becomes retry-ready and a later bounded same-job cycle performs
at most one leased create attempt. Confirm no duplicate row, attachment remains
blocked until row identity is proven, the new Prefect/Workflow Summary recovery
states are accurate, mailbox finalization occurs only after row and attachment
completion, and the DP returns cleanly to waiting before stopdp.

First unattended start failure diagnosis and correction checkpoint:

- The first live startdp partially started the wrapper-owned unattended worker
  before running the full manual application preflight. The fixed registered
  worker name proves its provenance. That preflight's Prefect probe incorrectly
  required exactly one total worker history record; Prefect contained the new
  online unattended worker plus an older offline manual record, so
  `postgresql_prefect_ready` deterministically failed and the wrapper reduced
  it to the generic application-readiness error.
- The full preflight also initialized Paddle and probed Ollama and Smartsheet
  before unattended waiting began. No document was passed to OCR, but model
  initialization was unnecessary for an empty/waiting inbox and caused the
  observed Paddle/oneDNN startup messages.
- Failure cleanup proved and stopped the wrapper-owned process tree and removed
  the DP ownership record. The worker's last heartbeat remained fresh briefly,
  explaining fresh worker count one while dp_running was false. Read-only
  follow-up found the fixed worker record OFFLINE with a stale heartbeat and
  found no matching live launcher or worker process; no cleanup was required or
  performed during diagnosis.
- StartDP now runs a lightweight categorized startup check before any DP
  process or worker creation. It verifies only Graph token acquisition and
  protected local-state writability, does not enumerate the mailbox or touch
  document content, and returns only graph-auth, storage, or unavailable safe
  categories. The launcher retains its same-process/network Graph check before
  worker creation. OCR, Ollama, and Smartsheet remain deferred to the existing
  production path and fail closed only when an eligible document requires them.
- Corrected the shared full preflight to require exactly one fresh online
  worker using the established 90-second heartbeat window while tolerating
  historical offline records. Manual runonce readiness remains fail-closed for
  zero, multiple, stale, malformed, or unproven workers.
- Normal status and statusdp now render stable multi-line PHI-safe operator
  views with Yes/No values and readable null timestamps. Explicit `-Json`
  preserves the original machine-readable fields. A fresh heartbeat without a
  proven DP now marks statusdp degraded during settlement.
- Focused/affected synthetic deterministic, mock, isolated-profile, and
  Windows PowerShell 5.1 checks passed. Twenty-two wrapper checks passed; the
  known isolated real-host CIM test again could not obtain its disposable root
  identity (exit 21) before exercising shutdown assertions. No startdp,
  worker/deployment run, live mailbox/Graph document access, protected OCR,
  Ollama, production document Smartsheet operation, attachment upload, or
  mailbox mutation occurred during this correction.

Deployment registration and operator-command installation checkpoint:

- Started only the repository-owned PostgreSQL-backed Prefect control room;
  no worker or document flow was started. Registered all three reviewed
  parameterless sources as `prefect-control-room-test`,
  `document-processor-manual`, and `document-processor-live` through the
  repository `prefect deploy --all --no-prompt` mechanism.
- Read-only metadata verified the exact qualified flow/deployment names, the
  `lthhc-local-process` work pool, zero parameters, zero schedules, zero
  automations, and no active flow runs. Manual/live concurrency is one with
  `CANCEL_NEW`; source retains zero retries, disabled result persistence, and
  the separate manual versus operator-owned unattended entrypoints.
- Removed only the replaced `manual-local` and `phi-safe-local` deployment
  registrations. Exactly the three standardized names remain. Historical flow
  runs were retained, and production-server run count remained unchanged.
- Installed the current-user profile mappings for startui/status/restartui/
  stopui, preparerun/runonce/stopworker, and startdp/statusdp/stopdp. A fresh
  Windows PowerShell 5.1 process resolved every function to its exact wrapper
  action. The pre-existing Set-Location customization and all content outside
  the single installer-managed section were preserved byte-for-byte.
- Exercised statusdp read-only: the DP was stopped, ownership absent, polling
  stopped, no bounded run active, and no fresh worker present. Focused
  deployment/installer/worker-boundary tests passed; the control-room test used
  only its isolated temporary Prefect server and fixed synthetic in-memory
  flow. No registered deployment run, mailbox/Graph discovery, protected OCR,
  Ollama, production document Smartsheet operation, attachment upload, or
  mailbox mutation occurred.

Unattended Document Processor implementation checkpoint:

- Added a separate parameterless `lthhc-unattended-mailbox` flow and
  `document-processor-live` deployment. Each invocation uses the existing
  production orchestration path, discovers newest-first eligible unread Inbox
  metadata, selects at most one supported document, and preserves exact Inbox
  re-verification with no fallback. An empty discovery is a successful no-op.
- Added operator-owned `startdp`, `statusdp`, and `stopdp` controls while
  preserving `preparerun`, `runonce`, and `stopworker` as the manual recovery/
  test path. Named control locking, ownership PID/creation/marker proof, pool
  and deployment concurrency one, and active-run checks prevent duplicate or
  overlapping unattended/manual work. Stop requests allow an active bounded
  run to finish and never stop PostgreSQL, the Prefect server, or manual/
  external workers.
- The Windows launcher owns one process worker and invokes one watched bounded
  deployment at a time. Normal empty/success polling waits five minutes;
  nonzero outcomes back off to ten, twenty, then at most thirty minutes.
  Status exposes only safe ownership/readiness/poll state, last/next timestamps,
  failure count, and active-run/degraded booleans.
- Graph authentication is noninteractive MSAL confidential-client application
  authentication using the existing client-credentials configuration boundary.
  Readiness fails closed before worker activation; credentials and tokens do
  not enter Prefect parameters, state, logs, or tracked files.
- Standardized active source/config/documentation names to
  `prefect-control-room-test`, `document-processor-manual`, and
  `document-processor-live`. Historical checkpoint names remain unchanged.
  No deployments were registered or removed in this implementation checkpoint.
- Compiled modified Python; all modified PowerShell parsed in Windows
  PowerShell 5.1. Focused/affected synthetic deterministic, mock, isolated
  profile, and isolated local Prefect checks passed. Twenty wrapper checks
  passed; one isolated real-host process-tree check could not begin because
  the host CIM lookup returned no process identity twice (exit 21). No live
  mailbox/Graph, protected OCR, Ollama, production document Smartsheet,
  worker/deployment, attachment, or mailbox mutation operation occurred.

Prefect stage-duration and worker-settlement checkpoint:

- Replaced immediate `*-started` marker task runs for OCR, document and subtype
  classification, extraction attempts, and validation attempts with fixed,
  PHI-free child task runs that enter Running at the existing application
  `stage_observer` start event and reach a terminal state at its corresponding
  completion/failure event. Application services remain authoritative and the
  bounded application boundary is still invoked exactly once.
- Added one PHI-safe `Workflow Summary` task with allowlisted aggregate result
  counts, review/retry state, selected extraction attempt, stage durations, and
  already-supported Ollama timing/token diagnostics. Visibility remains best
  effort and cannot replace the authoritative application result.
- StopWorker now distinguishes a definitively absent, previously wrapper-owned
  process from a live unowned or PID-reused process. A lingering fresh Prefect
  heartbeat after proven local exit returns the safe settlement status
  `worker_already_exited_prefect_heartbeat_settling`; active unowned and
  mismatched/reused PID cases still fail closed without killing a process or
  discarding the unresolved ownership record.
- Python compilation, synthetic deterministic/mock application regressions,
  isolated local Prefect one/two-attempt duration checks, Windows PowerShell
  5.1 parse/behavior checks, and an isolated real-host owned process-tree test
  passed. The temporary Prefect harness retained its known non-fatal Windows
  cleanup warning in one run. No live mailbox/Graph, protected OCR, Ollama,
  production document Smartsheet, worker/deployment, attachment upload, or
  mailbox mutation operation occurred.

Completed live acceptance and operator-command verification checkpoint:

- A real guarded mailbox run reached terminal `Completed` after exact-candidate
  re-verification and acquisition proof, OCR, classification, extraction,
  deterministic validation, business rules, production Smartsheet row write
  and attachment upload, review-required state, mailbox finalization, and
  workflow completion. Only PHI-safe lifecycle/status evidence is retained in
  project truth.
- The DPAPI-sealed single-use handoff, Graph attachment metadata boundary,
  exact-candidate acquisition proof, Prefect lifecycle visibility, and
  slow-stage OCR/Ollama observability were exercised through the reviewed
  guarded acceptance path.
- The current-user PowerShell profile exposes `startui`, `status`, `preparerun`,
  `runonce`, `stopworker`, `restartui`, and `stopui`. After reboot, the operator
  manually verified `startui`, `restartui`, `status`, `stopui`, stopped-state
  `status`, and restoration with `startui` in Windows PowerShell 5.1.
- The Prefect UI/control plane is intended to remain running continuously and
  the worker remains manual. Normal operation is `preparerun`, `runonce`, then
  `stopworker`; `startui` is for reboot/crash recovery, while `restartui` and
  `stopui` are maintenance commands.
- Windows PowerShell 5.1 compatibility and wrapper-owned process-tree shutdown
  are corrected and covered by isolated real-host and synthetic/mock checks.

Control-room wrapper checkpoint:

- Replaced tree-wide `taskkill /T` shutdown after a live Windows failure where
  nested Prefect children prevented non-forceful parent termination. New state
  records the safe root creation timestamp in addition to PID/start time.
  Shutdown proves the current root marker and creation identity, snapshots and
  validates descendant PID/parent/creation identity, stops deepest children
  first, attempts graceful exact-PID termination, and uses `/F` only after
  immediate identity revalidation. Stale/reused PIDs cannot authorize a kill.
- Windows PowerShell 5.1 isolated testing passed a root, multiple children,
  nested grandchild, already-exited child, forced fallback, stale identity, and
  unrelated-process survival. Read-only diagnosis found the live failed restart
  left legacy stale server state that cannot safely authorize orphan cleanup;
  the wrapper intentionally treats that reachable server as externally owned.
- Corrected the Windows PowerShell 5.1 ownership-check defect: .NET Framework
  does not provide `String.Contains(string, StringComparison)`. The wrapper now
  uses the supported `IndexOf(string, StringComparison) -ge 0` equivalent, so
  case-insensitive command-line ownership proof remains strict for worker,
  stop, and restart paths. A real Windows PowerShell 5.1 isolated function test
  passed match, mismatch, and missing-PID cases without touching live state.
- Added an idempotent current-user PowerShell-profile installer for the exact
  single-word commands `startui`, `status`, `preparerun`, `runonce`,
  `stopworker`, `restartui`, and `stopui`. Each function delegates once to the
  authoritative wrapper by verified absolute repository path and works from
  any directory. Existing profile content is preserved; only a delimited LTHHC
  section is replaced. Installation starts no control-plane or mailbox action.
- Added `scripts/invoke_prefect_control_room.ps1` with approved `StartUI`,
  `Status`, `PrepareRun`, `RunOnce`, `StopWorker`, `StopControlRoom`, and
  `RestartControlRoom` actions.
- It orchestrates the existing PostgreSQL launcher, worker/auth/handoff
  launcher, full readiness probe, and unchanged parameterless deployment.
  Preparation and invocation remain separate guarded operator actions.
  PostgreSQL and the server/UI are intended to remain available continuously;
  worker stop is routine while control-room stop/restart are maintenance-only.
- Local ignored ownership state contains only component names, PIDs,
  timestamps, and ownership booleans. Stop validates both owned PID and
  expected command-line marker and does not terminate unowned processes.
- Static/synthetic checks cover syntax, action separation, duplicate/stale PID
  guards, exact one-run invocation, PHI-safe state/output allowlists, and
  conservative stop behavior. No live mailbox/Graph, worker, deployment, OCR,
  Ollama, production Smartsheet document operation, attachment upload, or
  mailbox mutation occurred.

Implemented checkpoint:

- Added a fixed-name, current-user DPAPI-sealed handoff outside Git and
  configuration. It is exclusive, expires after exactly 15 minutes, is
  atomically claimed by one consumer, and is deleted on claim or launcher
  cleanup.
- Separated popup preparation from exact preselected-candidate processing.
  Preparation retains newest-ten metadata discovery and the existing PHI-safe
  popup; the worker-created flow performs no mailbox enumeration or fallback.
- Added the handoff-backed application entrypoint and changed the unchanged
  parameterless one-task/zero-retry Prefect adapter to use it.
- Added optional worker-launch preparation and unconditional cleanup. Normal
  production enumeration, durable state, idempotency, uncertain-write
  handling, and mailbox completion ordering remain unchanged.
- Synthetic deterministic/mock focused and affected checks passed. A real
  current-user Windows DPAPI synthetic roundtrip passed outside the restricted
  sandbox. No live mailbox, popup, flow, OCR, Ollama, Smartsheet, or mailbox
  completion operation ran.

Lifecycle visibility checkpoint:

- Projected the existing authoritative application stage callbacks into
  Prefect lifecycle child task runs. Business operations remain inside their
  existing services and the application boundary is still invoked exactly
  once.
- Operator-facing task names now cover acceptance handoff, exact candidate
  re-verification, document acquisition, OCR, document classification,
  subtype classification, extraction, deterministic validation, business
  rules, Smartsheet write/attachment, review determination/state, mailbox
  finalization, and workflow completion.
- Lifecycle inputs are strictly normalized to safe names, statuses, durations,
  attempts, aggregate counts, review-required boolean, and sanitized failure
  category. Visibility failure cannot replace the authoritative application
  failure path.
- A synthetic/mock local Prefect flow completed against an isolated temporary
  server and its API contained the application task plus every expected
  lifecycle task-run name. No Graph, protected document, OCR, Ollama,
  production Smartsheet, mailbox mutation, popup, or DPAPI identity was used.
- The deployment remains parameterless with concurrency one and `CANCEL_NEW`.
  Runtime task shape changed from one task total to one authoritative
  application task plus lifecycle-only child task runs; all tasks have zero
  retries and disabled result persistence.

Lifecycle-visible deployment registration checkpoint:

- Registered the reviewed current source as
  `lthhc-bounded-mailbox/manual-local` through the established PostgreSQL-
  backed local Prefect procedure.
- Read-only API and source verification proved the exact flow/deployment and
  entrypoint, zero parameters and empty parameter-schema properties, zero job
  variables, zero schedules, zero automations/triggers, concurrency one with
  `CANCEL_NEW`, zero flow/task retries, disabled flow/task result persistence,
  exactly one authoritative application invocation, and all expected
  lifecycle child-task definitions.
- The deployment retained three historical runs before and after registration,
  proving registration created no flow run. The existing worker record was
  offline and online-worker count remained zero.
- Deployment metadata contained none of the prohibited protected-identity or
  payload markers checked. No worker, mailbox/Graph access, popup, handoff
  preparation, OCR, Ollama, production Smartsheet operation, mailbox mutation,
  or deployment run occurred.
- Only PostgreSQL and the localhost Prefect server were started; both were
  stopped after verification.

Acceptance eligibility diagnostic checkpoint:

- Confirmed newest-ten discovery includes only messages returned by the
  unread Inbox query and requires a valid message mapping/identity, exact
  `isRead is False`, a provable metadata-only supported-document count, and
  exactly one supported non-inline file attachment with extension PDF, PNG,
  JPG/JPEG, TIF, or TIFF.
- Zero eligible candidates previously collapsed four actual per-message
  exclusions: state not exactly unread, zero supported documents, multiple
  supported documents, or unprovable document count. Exact-candidate
  unavailable/read/Inbox/identity failures occur only after selection and
  cannot explain zero discovery candidates.
- Added aggregate candidate-selection diagnostics for not-unread, no supported
  document, multiple supported documents, unsupported non-inline document
  type, and unprovable count. Attachment names and identities are never
  retained in the diagnostic result.
- Added `--diagnostic-only` preparation mode. It uses a noninteractive selector,
  creates no handoff, and returns only the allowlisted aggregate JSON. Normal
  eligibility, popup preparation, production enumeration, exact re-
  verification, and no-fallback behavior are unchanged.
- Focused and affected tests were synthetic deterministic/mock only. No live
  mailbox/Graph access, popup, handoff, Prefect run, OCR, Ollama, production
  Smartsheet operation, or mailbox mutation occurred.
- An affected concurrent-consumer regression exposed a separate Windows lock
  contention race in the uncommitted handoff service; transient permission
  contention now follows the existing bounded lock retry and the one-consumer
  test passes.

Attachment metadata proof diagnostic checkpoint:

- The observed live aggregate narrowed the sole candidate to an unprovable
  attachment count. Before this checkpoint that could mean initial request
  failure, invalid response collection, invalid attachment item, or invalid
  non-inline file name; the existing aggregate could not distinguish them.
- Added aggregate-only counts for request, response, item, type, inline-state,
  name, pagination-link, and pagination-request failures. Only fixed category
  names and integer counts reach diagnostic output.
- Corrected the metadata request to select only declared properties, accept
  both Graph type-annotation spellings, validate required type/inline metadata,
  and consume validated same-host v1.0 continuation links until the exact count
  is proven. Invalid or failed continuation remains ineligible.
- Eligibility, exactly-one enforcement, production enumeration, no fallback,
  protected-identity handling, and processing/write semantics are unchanged.
- Compilation and focused/affected synthetic deterministic/mock regressions
  passed. An isolated synthetic Prefect lifecycle regression also passed with
  no external integration; it emitted a non-fatal Windows temporary-file
  cleanup warning after completion. No live mailbox/Graph, popup, handoff,
  OCR, Ollama, production Smartsheet, or mailbox mutation occurred in this
  checkpoint.

Slow-stage Prefect performance visibility checkpoint:

- Reused the existing `stage_observer` boundary; OCR, LLM, validation,
  candidate selection, business rules, review, writes, and mailbox logic remain
  authoritative in the application and visibility remains best-effort.
- Added fixed child-task markers for extraction attempt 1 start/completion,
  validation attempt 1, retry decision, conditional extraction/validation
  attempt 2, candidate selection, and aggregate document-processing completion.
- OCR completion exposes wall time plus selected existing safe OCR timing/count
  diagnostics. Classification and extraction completions expose wall time plus
  real Ollama total/load/prompt-evaluation/generation durations and prompt/
  generated token counts when present. Retry booleans, selected attempt,
  attempt count, total extraction/validation wall time, and total document wall
  time are visible through fixed allowlisted fields.
- Unavailable provider metrics remain absent. Lifecycle logging now omits
  unpopulated fields instead of emitting repeated `field=None` noise.
- Synthetic deterministic/mock one- and two-attempt processing checks passed,
  including validation per attempt, both selected-attempt outcomes, retry
  behavior, metric mapping, aggregate timing, protected-key exclusion, and
  unchanged processing semantics. An isolated synthetic local Prefect flow
  completed and exposed the expected task names; its known non-fatal Windows
  temporary-database cleanup warning occurred after completion.
- No live Graph/mailbox, protected-document OCR, local Ollama, production
  Smartsheet write, attachment upload, popup, handoff, worker, or mailbox
  mutation occurred.

Slow-stage deployment registration checkpoint:

- Registered the updated `lthhc-bounded-mailbox/manual-local` source through
  the documented PostgreSQL-backed local Prefect procedure. Registration
  succeeded without invoking the deployment.
- Read-only metadata verified the exact name/entrypoint, zero parameters and
  parameter-schema properties, zero job variables, no schedule or automations,
  concurrency one with `CANCEL_NEW`, and no protected metadata markers.
- Static/current-source verification proved zero flow/application/lifecycle
  retries, disabled result persistence, exactly one authoritative application
  invocation, all new slow-stage lifecycle names, and the existing aggregate
  extraction and deterministic-validation names.
- Deployment count remained one and flow-run count remained four before and
  after registration. Zero workers had a fresh heartbeat; one historical
  worker record retained a stale `ONLINE` label with a roughly five-hour-old
  heartbeat. No worker was started or stopped.
- Focused control-plane, readiness, and worker-boundary checks passed 24/24;
  synthetic deterministic/mock plus real local Prefect/PostgreSQL read-only
  metadata. No handoff, Graph/mailbox, OCR, Ollama, production Smartsheet, flow
  run, attachment upload, or mailbox mutation occurred. PostgreSQL was stopped
  after verification; a pre-existing localhost Prefect process was not
  terminated.

Post-reverification zero-document diagnosis checkpoint:

- The PHI-safe `handsome-wolverine` evidence proves exact reverification
  succeeded with one supported document but processing exited before the
  attachment lifecycle boundary. Current source had exactly two successful
  zero-document exits there: durable `already_handled` reconciliation or a
  false/missing message-level `hasAttachments` flag. Existing logs did not
  distinguish them, and the protected identity was intentionally unavailable,
  so the historical leaf cause cannot be proven. Aggregate local state confirms
  handled markers exist but cannot safely bind one to this run.
- Fixed the proven defect that discarded the exact one-document proof before
  `process_message`. The preselected and same-process selected paths now carry
  the proof into normal processing, where it overrides a contradictory message
  attachment flag without weakening the one-document guard or no-fallback rule.
- Aligned download filtering with metadata proof by accepting both Graph file-
  attachment type spellings. A proven document that produces no download
  candidate now returns a sanitized acquisition error and remains unread rather
  than being marked handled and converted to successful `no_documents`.
- Added PHI-safe `document-acquisition-skipped` reasons for
  `message_already_handled`, `message_attachment_flag_false`, and
  `attachment_download_no_candidates`. Identity, names, content, paths, and
  provider detail remain excluded.

Corrected-source deployment registration checkpoint:

- Registered the corrected current workspace source as
  `lthhc-bounded-mailbox/manual-local` through the documented localhost,
  PostgreSQL-backed Prefect procedure. Registration succeeded and did not
  invoke the deployment; its deployment flow-run count remained one before and
  after registration.
- Read-only metadata verified the exact flow/deployment name and entrypoint,
  zero parameters/schema properties/job variables, no schedule or automation,
  concurrency one with `CANCEL_NEW`, and zero checked protected metadata
  markers. Current registered-path source retains zero flow/application/
  lifecycle retries, disabled result persistence, exactly one authoritative
  application call, every lifecycle/performance definition, and the corrected
  exact-candidate acquisition behavior.
- Contrary to the requested zero-worker precondition, one pre-existing local
  worker process had a fresh ONLINE heartbeat before registration and remained
  online afterward. This checkpoint did not start, stop, or mutate that worker.
  The no-schedule/no-trigger deployment and unchanged run count prove
  registration itself created no execution.
- Compilation and 85 focused synthetic deterministic/mock/local-safe tests
  passed. The synthetic Prefect lifecycle test produced its known non-fatal
  Windows temporary-database cleanup warning after successful completion. No
  handoff, Graph/mailbox, protected OCR, Ollama, production document
  Smartsheet operation, attachment upload, mailbox mutation, or deployment run
  occurred.

Typed Smartsheet row contract and API-rejection recovery checkpoint:

- Fixed the structural path that allowed optional `None` values and values not
  proven compatible with their destination type to reach Smartsheet Cell
  construction. Optional absence is now omitted before construction, and no
  Cell is admitted unless its serialized form contains a non-null value.
- Destination validation now requires unique mapped destinations, strict
  positive-integer column IDs, supported type metadata, and proven non-system
  writable state. `CHECKBOX` accepts only a literal boolean; `DATE` accepts only
  normalized ISO `YYYY-MM-DD` text; and `TEXT_NUMBER` accepts only strings,
  integers, and finite floats. Containers, dictionaries, arbitrary objects,
  booleans in text/number columns, `Decimal`/date objects, non-finite numbers,
  and other unsupported values fail locally. AI Correction remains literal
  `False`; review/retry/reconciliation metadata mapped to text/number columns
  uses explicit `Yes`/`No` text.
- Request contract version 2 and durable state schema version 3 persist only
  aggregate typed-validation evidence plus allowlisted API rejection category,
  numeric API code when valid, and HTTP status class. Response bodies, request
  payloads/values, row IDs, exception text, tokens, and sensitive provider
  fields are not retained in the diagnostic result or workflow summary.
- The same durable job may re-arm once only when its prior request contract is
  older. Every contract-v2 attempt reservation requires a fresh lease, exact
  reconciliation with zero matches, and passing mapping/schema/type evidence.
  One match reconciles the existing row; multiple or unavailable reconciliation
  fails closed; a second create under the upgraded contract is impossible.
  Direct retry remains blocked, and attachment processing remains blocked until
  row identity is proven.
- Modified Python compiled. Focused and affected synthetic deterministic/mock,
  local temporary-state, adjacent Smartsheet/mailbox, and isolated local Prefect
  checks passed. The Prefect check emitted only its known non-fatal sandboxed
  memo-store warning. No startdp, worker/deployment run, live mailbox/Graph,
  protected OCR/Ollama, production Smartsheet document/comment operation,
  attachment upload, or mailbox mutation occurred.

Successful typed-contract live recovery checkpoint:

- The controlled unattended recovery reused the existing durable job identity
  under request contract version 2. Exact reconciliation and the guarded
  recovery path completed without a duplicate row.
- The production Smartsheet row, attachment, and mailbox workflow completed.
  Business naming behavior produced the expected result.
- The operator-visible classification remained category `2067`, intake subtype
  `unknown`, and review reason exactly `AI Document Subtype: Unknown`.
  Classification confidence remained independently owned.
- Optional unavailable production fields remained blank, the misleading
  missing/confidence sentinel was absent, and `AI Correction` initialized
  unchecked. These are PHI-safe structural facts only.

Document Processor Training implementation checkpoint:

- Added the fourth parameterless Prefect deployment
  `document-processor-training` with application identity `lthhc-dp-training`,
  a dedicated `lthhc-dp-training-process` pool, concurrency one with
  `CANCEL_NEW`, zero flow/task retries, disabled result persistence, no schedule,
  and no automatic reboot start. Its worker health endpoint uses port 8081 so it
  can coexist with the live DP worker.
- Added exact `startdptraining`, `statusdptraining`, and `stopdptraining`
  operator mappings. Training and live DP have separate workers/process trees,
  shared serialized ownership-state mutation, and independent stop behavior.
- Extended the existing Smartsheet feedback seed with seven-column schema/type/
  writability validation, correction-only discovery, flagged-row protected
  context loading, paginated Conversations/comment reads, attachment exclusion,
  incremental comment checkpoints, and one DPAPI-sealed durable case per row.
- Human ownership remains absolute for `AI Correction`,
  `Approve AI Correction`, `Approve AI Resolution`, and comments. DP Training
  alone may update `AI Proposed Correction`, `AI Correction Type`,
  `AI Correction Status`, and exact result field `AI Resolution Result`.
- Added controlled correction taxonomy/status transitions, versioned proposal
  and result hashes, false-to-true approval generation tracking, stale-approval
  rejection, new-comment reopening, durable write intent/readback reconciliation,
  one implementation start per cycle, and real-retest resolution approval.
- Local Ollama analysis treats comments as untrusted evidence, has no tools, is
  schema/vocabulary constrained, and falls back to `Needs Investigation`.
  Codex receives only deterministic PHI-safe structural tasks and is guarded by
  a clean/synchronized Git preflight, global lock, one bounded ephemeral process,
  no resume/retry, all compile/test/tracker/Git gates, and pushed-commit proof.
- Capability modes require an explicit protected-local setting; `schema_only`
  remains the metadata-only mode. Production proposal writes and Codex dispatch
  each remain behind separate disabled protected-local gates pending controlled
  acceptance. Synthetic/mock/local-safe tests passed;
  no live flagged row/comment, protected OCR/Ollama, production correction write,
  mailbox operation, deployment run, or worker start occurred.
- The metadata-only registration now contains exactly the four intended
  deployments and no extras. All use current committed local source, empty
  parameters, and zero schedules; server automations and active target runs are
  zero. The training pool has concurrency one and no worker. The existing fresh
  live DP worker remained untouched. A real PowerShell 5.1 `-File` installer
  acceptance exposed and fixed deferred `$PSScriptRoot` resolution before the
  profile was changed. The real `statusdptraining` acceptance also fixed
  duplicate-case process `PATH` inheritance and safe fast-child-exit handling;
  it now reports ready `schema_only`, stopped, zero training workers/runs/cases,
  and not degraded without starting the service.

DP Training read-only activation-preparation checkpoint:

- Set only `DP_TRAINING_MODE=read_only` through the existing ignored `.env`
  protected-local configuration boundary. No Smartsheet-write or Codex-dispatch
  gate was added or enabled.
- The readiness probe and `statusdptraining` both resolved `read_only` while DP
  Training remained stopped, with zero training workers or active cycles and no
  degraded state. These checks do not enumerate rows or read comments.
- Static and synthetic coverage proved exact seven-column validation,
  correction-column-only discovery until a literal checked flag is reverified,
  paginated comment reads without attachments, one DPAPI-sealed case per row,
  unchanged-input idempotency, same-case generation updates for comment changes,
  and the absence of all Smartsheet write, checkbox mutation, and Codex-dispatch
  paths in `read_only` mode.
- Sixty-seven focused synthetic deterministic/mock/local-safe checks passed.
  No production row/comment was read, no Smartsheet or mailbox state was mutated,
  no protected Ollama analysis ran, and no worker/deployment was started.

DP Training capability-mode propagation correction checkpoint:

- The first controlled startup exposed a split configuration path: the status
  readiness child loaded the ignored repository `.env` and reported `read_only`,
  while neither parent launcher nor worker received that child-only environment.
  The application read its mode before the Smartsheet client later loaded the
  same file, silently captured `schema_only`, and returned `schema_ready` without
  row discovery. Prefect's process worker inherited its worker environment and
  did not sanitize the value; deployment parameters and job variables remained
  empty.
- Added one absolute-path protected capability loader shared by readiness and the
  application. Missing, invalid, changed, or runtime-mismatched configuration now
  fails closed before Smartsheet construction or polling. The validated mode and
  mutation-gate fingerprint are frozen at startup, inherited by only the owned
  worker/process tree, and must still match the protected file on every cycle.
  Capability changes require `stopdptraining` then `startdptraining`.
- Startup now proves the application-visible safe mode/fingerprint before worker
  activation. `statusdptraining` distinguishes configured and runtime/effective
  modes and reports their match without exposing the fingerprint. Prefect cycle
  summaries include only the effective safe mode alongside existing aggregate
  fields; configuration mismatch is non-retryable and PHI-safe.
- Focused and affected synthetic deterministic/mock/local-safe checks passed for
  all four modes, fail-closed missing/invalid/mismatch behavior, read-only/write/
  dispatch separation, PowerShell 5.1, protected DPAPI state, Smartsheet mapping/
  write/recovery, mailbox idempotency/orchestration, and isolated Prefect flows.
  A stopped-service status acceptance reported configured `read_only`, runtime
  `not_running`, zero training workers/active cycles, and no degraded state.
- No production flagged row/comment was read during this correction, no
  Smartsheet or mailbox state was mutated, and no Codex, protected OCR, or Ollama
  operation ran.

DP Training read-only acceptance and proposal-write preparation checkpoint:

- The operator-confirmed live `read_only` acceptance ran with matching
  configured/effective mode, discovered exactly one flagged row, and created or
  updated exactly one protected correction case. No correction-field write,
  Codex dispatch, or failure occurred, and DP Training returned to waiting.
- The retained case has exactly one durable validated proposal generation and
  zero implementation attempts, implementation job identities, or consumed
  approval generations. It is now durably marked as historical acceptance input
  so it cannot authorize implementation, even in a later dispatch-capable mode.
- Corrected promotion behavior so an unchanged case analyzed in `read_only` can
  publish its existing validated generation after `proposal_write` is enabled.
  It is not reanalyzed and does not create another generation; exact unchanged
  readback makes later cycles reconciliation-only.
- Approval authorization and implementation-job creation are now exclusive to
  `approval_dispatch`. `proposal_write` can never consume an approval edge,
  create an implementation job, or dispatch Codex. Historical cases also carry
  fixed current-state/retest guidance without asserting that an older issue
  remains present in current code.
- Protected configuration is `proposal_write` with the Smartsheet-write gate
  enabled and Codex-dispatch gate explicitly disabled. Readiness and stopped-
  service status report the configured mode, zero training workers, and no
  degraded state. No production row/comment read or Smartsheet mutation occurred
  during preparation.

Shared Document Processor business context and correction-analysis v2 checkpoint:

- Added one PHI-free immutable `DocumentProcessorBusinessContext` at business
  context version 1. It owns the confirmed document taxonomy, canonical naming
  tokens, authorization intake subtype vocabulary, filename placeholders and
  outcomes, field states, current confidence policies, quantity/unit semantics,
  review/Smartsheet roles, forbidden inferences, and DP Training semantics.
  Existing deterministic taxonomy, naming, validation, filename, quantity/unit,
  and review services derive their duplicated constants from this source.
- Local classification, both extraction attempts, structural learning, and DP
  Training correction analysis receive compact role-specific rendered views.
  Intake naming has no separate model call and consumes the same structured
  vocabulary through deterministic naming services. Context version/role/size
  are PHI-safe metrics; prompt/context content is not logged or sent to Prefect.
  Deterministic validation and business rules remain authoritative.
- Correction analysis contract version 2 separates desired-behavior sufficiency
  from technical disposition and adds controlled primary/related correction
  types plus feedback relationship and structural filename/subtype concepts.
  A coherent latest reviewer clarification is distinct from prior feedback and
  may narrow it; old AI proposal text remains excluded from reviewer evidence.
  Clear business intent can become `Analysis Ready` even when the implementation
  layer needs investigation, while absent/ambiguous/conflicting intent alone uses
  `Needs More Information`.
- Filename symptoms are selected deterministically before implementation-layer
  hypotheses. A supported filename/subtype case uses primary `Filename` with
  protected related `Document Subtype`; proposal language is rendered only from
  controlled structural concepts. Reviewer-provided payer, service, date, or
  subtype values never become production evidence. `AUTH DECREASE` may use
  explicit validated document evidence; `AUTH INIT` is forced to authoritative
  external context and `Requires External System`.
- Protected correction cases migrate in place to state schema version 2. An
  unchanged active case analyzed under an older analysis/business-context basis
  can receive exactly one version-keyed reanalysis with the same durable identity
  and comment checkpoint. It creates one new proposal generation, invalidates
  prior approval baselines, and is idempotent thereafter. `proposal_write` still
  cannot create an implementation job or dispatch Codex.
- Sanitized implementation task schema version 2 carries only controlled
  versions, primary/related types, structural concepts, behavior, technical
  disposition, possible durable layers, synthetic regression requirements, and
  generalization prohibitions. The bounded Codex result must report durable
  changed layers and prove context-version behavior; local AI can never update
  shared context directly.
- Modified Python compiled. Focused and affected synthetic deterministic/mock,
  local protected-state, PowerShell 5.1, Smartsheet boundary, and isolated local
  Prefect checks passed. No live Smartsheet row/comment was read or mutated, and
  no live DP/DP Training, Codex, mailbox/Graph, OCR, or Ollama operation ran.

Dedicated Live Document Processor work-pool checkpoint:

- Live DP now routes only through the dedicated `lthhc-dp-live-process` pool and
  explicitly named `lthhc-dp-live-worker`. Manual DP remains on
  `lthhc-local-process`; DP Training remains on `lthhc-dp-training-process`.
- `startdp` creates only the Live DP-owned launcher/worker on the live pool.
  `statusdp` reports the live pool explicitly, and `stopdp` uses only the live
  ownership record and live-pool heartbeat count. Manual and training stop paths
  retain their distinct ownership markers and cannot stop Live DP.
- The local Prefect control plane now has all three process pools registered with
  concurrency one. The live, manual, and training deployments are parameterless,
  retain concurrency one with `CANCEL_NEW`, have zero schedules/job variables,
  and target their exact service pools. Metadata acceptance found zero online
  workers, zero active target runs, and zero automations; no worker or flow ran.
- Modified Python compiled. Focused and affected synthetic deterministic/mock,
  Windows PowerShell 5.1, and isolated local Prefect checks passed. Read-only
  `statusdp` reported the dedicated live pool ready, stopped, zero workers, and
  not degraded. No document, mailbox, Smartsheet, OCR, Ollama, or other PHI-
  sensitive operation ran.

DP Training supplemental-clarification repair checkpoint:

- A PHI-safe protected-case inspection proved the latest clarification reached
  analysis contract v2 with all three reviewer-comment revisions, was classified
  as `Clarifies Prior`, and produced a validated filename analysis. The raw model
  structure retained only canonical type and payer requirements; service and
  supported-date concepts were absent before validation. They were not removed by
  normalization, deterministic rendering, row-state evidence checks, or write
  idempotency.
- Analysis contract version 3 now requires additive clarification semantics:
  compatible desired-behavior requirements accumulate chronologically, while a
  newer explicit conflict overrides only the affected component. A deterministic
  controlled merge extracts only filename-policy directives from protected
  feedback and never treats reviewer values as production evidence.
- The controlled filename proposal vocabulary now expresses canonical document
  type, payer when applicable, service when applicable, and supported date
  representation. The renderer requires a range only when both applicable dates
  are explicitly and deterministically supported, otherwise uses a supported
  single applicable date, and retains the approved `[DATE]` placeholder for an
  unresolved applicable naming date. Neither AUTH nor any AUTH subtype implies a
  range, and `AUTH INIT` retains its authoritative external-context restriction.
- Business context remains version 1 because shared model-visible business truth
  did not change; the analysis interpretation/contract changed. The existing
  active contract-v2 case is eligible for exactly one same-identity, same-comment-
  checkpoint reanalysis under contract v3. The version-keyed attempt invalidates
  stale approval state, can create one new validated proposal generation, and is
  idempotent on later unchanged cycles. `proposal_write` remains unable to create
  an implementation job or dispatch Codex.
- Modified Python compiled. Focused and affected synthetic deterministic/mock,
  naming/business-context, PowerShell 5.1, and isolated local Prefect checks
  passed. No live Smartsheet mutation, Codex dispatch, mailbox/Graph, OCR, or live
  Ollama operation ran.

DP Training reviewer-facing proposal rendering checkpoint:

- `AI Proposed Correction` now receives a concise deterministic business summary
  rendered only from validated structural analysis. Filename proposals identify
  the supported document/subtype behavior and the applicable validated payer,
  service, and supported date/date-range components in one short sentence, with a
  second short exclusion sentence only when the structure requires it.
- Detailed evidence boundaries, placeholder behavior, date-selection constraints,
  technical disposition, and implementation context remain in the protected
  validated analysis. The PHI-safe implementation-task builder reconstructs that
  detailed behavior from the persisted controlled structure rather than using the
  shortened reviewer text as its authority.
- Analysis contract remains version 3 and business context remains version 1.
  This is presentation-only: clarification precedence, structural requirements,
  proposal generation/hash binding, approval ownership, case persistence,
  idempotency, and proposal-write dispatch prohibition are unchanged.
- Synthetic coverage proves a normal minimal follow-up comment creates exactly one
  new proposal generation while retained compatible feedback supplies the full
  structure; the next unchanged cycle is a no-op. Modified Python compiled, and
  focused plus affected DP Training, business-context, naming, PowerShell 5.1,
  and isolated Prefect checks passed. No live Smartsheet correction processing,
  mailbox/Graph, OCR, live Ollama, or Codex operation ran.

## CURRENT NEXT START

Add one normal minimal reviewer comment, such as `again`, to the existing active
correction case, then perform one controlled live `proposal_write` DP Training
acceptance. Verify the ordinary comment revision creates exactly one new proposal
generation, retains the prior compatible canonical subtype/document type, payer,
applicable service, and supported date/date-range structure, and writes a concise
reviewer-facing `AI Proposed Correction` plus only the workflow-owned type/status
fields needed for the generation. Verify human controls/comments remain unchanged,
no Codex dispatch or implementation job occurs, and an unchanged following cycle
is reconciliation-only/idempotent. Do not approve implementation during this
acceptance, and stop DP Training cleanly afterward.
<!-- LEGACY_PROJECT_MEMORY_END -->

## Verbatim Legacy PROJECT_JOURNAL Snapshot

<!-- LEGACY_PROJECT_JOURNAL_START -->
============================================================
LTHHC AI AUTOMATION PLATFORM - DEVELOPMENT JOURNAL
============================================================

Last updated: 2026-08-10

Repository:
LTHHC-Josh/AI_Automation_Platform

Local project:
C:\\Projects\\LTHHC-AI-Automation-Platform

------------------------------------------------------------
DEVELOPMENT WORKFLOW
------------------------------------------------------------

1. Inspect current repository files and interfaces.
2. Trace dependencies before changing code.
3. Preserve the approved architecture.
4. Implement the feature.
5. Run real or clearly identified synthetic tests.
6. Update this project tracker after meaningful tested work.
7. Verify that secrets and PHI are excluded.
8. Commit and push only tested, safe source files.

Always provide complete file contents when code must be replaced.

Temporary helper scripts and project-tracker update scripts must be
delivered as one complete PowerShell block. The block must use a
single-quoted here-string piped to Set-Content at the exact file path,
include the complete script contents, run the script and related
commands, and remove the temporary script when appropriate.

Do not ask the user to create temporary files manually, choose their
paths, paste partial script contents into an editor, or assemble a
script from separate snippets.

------------------------------------------------------------
APPROVED ARCHITECTURE
------------------------------------------------------------

Microsoft 365 shared mailbox
  -> Microsoft Graph
  -> Attachment download
  -> Local PaddleOCR
  -> Local Ollama
  -> Structured extraction
  -> Controlled extraction retry when structurally incomplete
  -> Independent deterministic candidate validation
  -> Stronger supported candidate selection
  -> Business rules
  -> Automatic Smartsheet row population
  -> Conditional downstream human-review exception workflow

Shared mailbox:

ai@lthhc.com

Local AI stack:

OCR provider:
PaddleOCR

LLM provider:
Ollama

Model:
llama3.1:8b

Execution:
Local and in-house

Documents, OCR text, patient information, member IDs, authorization
numbers, medical information, and credentials must not be sent to
external AI services.

------------------------------------------------------------
CURRENT DOCUMENT-PROCESSING FLOW
------------------------------------------------------------

File
  -> OCR or cached OCR text
  -> Separate Ollama classification request
  -> Separate Ollama structured-extraction request
  -> Structural completeness check
  -> Optional single controlled extraction retry
  -> Preserve field-level value, confidence, and source_text
  -> Preserve optional authorization service-line records
  -> Independently validate each extraction candidate
  -> Select the stronger deterministically supported candidate
  -> Synchronize corrected flat extraction values
  -> Deterministic business rules
  -> Automatic intentionally mapped Smartsheet row population
  -> Conditional downstream human-review exception workflow
  -> Document result

Classification and extraction intentionally remain separate.

Extraction candidates are never merged.

Values from one attempt are never copied into another attempt.

When two validated candidates have the same deterministic score, the
first attempt is retained.

A combined Ollama request was tested on 2026-07-31. It improved runtime
by only approximately 2.3 percent and materially reduced extraction
accuracy. The combined implementation was rejected and the separate
request flow was restored.

------------------------------------------------------------
MICROSOFT GRAPH STATUS
------------------------------------------------------------

Microsoft Entra app registration:
Completed and tested

Authentication:
OAuth 2.0 client-credentials flow through MSAL

Shared mailbox:
ai@lthhc.com

Verified Graph behavior:

- Authenticate with Microsoft Graph
- Retrieve unread inbox messages
- Enumerate attachments
- Ignore inline signature images
- Download supported non-inline attachments
- Save attachments under data/incoming
- Process downloaded documents
- Mark messages read only after successful processing
- Leave failed messages available for retry
- Prevent duplicate processing

Mailbox processing and duplicate prevention were tested successfully.

Dedicated authentication-error testing remains incomplete for:

- Invalid credentials
- Expired client secrets
- Missing Microsoft Graph permissions
- Microsoft Graph authorization failures
- Sanitized authentication-error logging

------------------------------------------------------------
LOCAL OCR STATUS
------------------------------------------------------------

Production OCR provider:
PaddleOCR

Current behavior:

- Processes scanned and image-only PDF documents
- Uses PaddleOCR locally
- Supports real document OCR
- Stores OCR cache under data/ocr_cache
- Uses a SHA-256 document hash for cache identification
- Uses hash-only OCR cache filenames
- Reuses cached OCR text when the document has not changed
- Migrates compatible legacy cache files to hash-only filenames
- Treats cached OCR text as PHI
- Does not log patient-bearing document names or cache paths
- Sanitizes OCR exceptions before logging

The following paths and data must never be committed:

.env
data/incoming/
data/ocr_cache/
patient documents
OCR text containing PHI
local model files
credentials
tokens

Real scanned authorization OCR was completed successfully.

OCR cache reuse was tested successfully.

Privacy-safe cache logging was verified with a real local run.

PaddleOCR model initialization is deferred until fresh prediction is required.
Cached text reuse and cache-only misses do not initialize the Paddle engine.

------------------------------------------------------------
LOCAL OLLAMA STATUS
------------------------------------------------------------

Provider:
Ollama

Model:
llama3.1:8b

Execution:
CPU-only on the current laptop

Connection testing confirmed:

- Local Ollama server is reachable
- llama3.1:8b is installed
- Classification requests work
- Structured-extraction requests work
- Structured JSON responses work
- Field-level value, confidence, and source_text can be returned
- Optional authorization service-line records can be returned
- Flat extraction fields remain available for backward compatibility

Classification and extraction remain separate requests.

The provider currently sends:

- temperature 0
- configurable deterministic seed routing
- seed 42 for the first extraction attempt by default
- seed 43 for the second extraction attempt by default
- structured JSON schema
- a generic verification addendum on controlled retry attempts

Changing the seed alone did not improve semantic completeness during the
observed real retry event.

Repeated requests can still produce complete or incomplete extraction
patterns even when model, schema, temperature, and base prompt remain
unchanged.

The seed remains available for controlled local testing and PHI-safe
diagnostics but is not treated as proof of deterministic output.

Attempt 1 uses the established extraction prompt.

Attempt 2 appends generic verification instructions that require the
model to reread the OCR text, reconstruct service lines independently,
verify row-level code and quantity evidence, avoid cross-row mixing, and
return null or omit unsupported values rather than guessing.

The retry prompt contains no payer-specific, service-code-specific, or
document-specific conclusion.

------------------------------------------------------------
PHI-SAFE OLLAMA METRICS STATUS
------------------------------------------------------------

The platform now captures PHI-safe Ollama response metadata.

The following values may be retained:

- request_type
- attempt
- seed
- retry_prompt_applied
- done
- done_reason
- total_duration
- load_duration
- prompt_eval_count
- prompt_eval_duration
- eval_count
- eval_duration
- generation_tokens_per_second

Durations returned by Ollama are converted from nanoseconds to seconds.

The following data is explicitly excluded from processing metrics:

- OCR text
- prompt content
- response content
- extracted values
- source_text
- patient identifiers
- member identifiers
- authorization identifiers
- medical information

The Document model now contains:

processing_metrics

DocumentProcessor now measures separately:

- OCR wall time
- Classification wall time
- Extraction wall time
- Validation wall time
- Business-rule wall time
- Human-review wall time
- Total wall time

DocumentProcessor also records:

- Extraction attempt count
- Whether retry was triggered
- Whether raw structure required retry
- Whether validated structure required retry
- Selected extraction attempt
- Per-attempt wall time
- Per-attempt Ollama metadata

------------------------------------------------------------
REPEATABILITY INVESTIGATION
------------------------------------------------------------

The known Molina authorization regression was run repeatedly.

Observed complete extraction pattern:

- Two service-line records
- Service code preserved on both rows
- Quantity 1 preserved
- Quantity 6 preserved
- Top-level service_codes preserved
- Top-level authorized_units preserved
- Approximately 1201 extraction-generation tokens
- Approximately 284 to 293 seconds of extraction time

Observed incomplete extraction pattern:

- Two nominal service-line records
- One row preserved service code and quantity 6
- One row retained dates and status but lost service code and quantity
- Top-level service_codes became unsupported or null
- Top-level authorized_units retained only quantity 6
- Approximately 1080 extraction-generation tokens
- Approximately 195 seconds of extraction time

Both patterns reported:

done_reason:
stop

The incomplete result was therefore not caused by an explicit model
token-limit completion reason.

The incomplete run generated 121 fewer tokens than the complete runs.

The prompt evaluation counts remained identical:

Classification prompt_eval_count:
1925

Extraction prompt_eval_count:
2633

The faster failed runs were confirmed to be shorter semantically
incomplete model generations.

The deterministic validator correctly refused to invent or restore
values missing from model-provided evidence.

------------------------------------------------------------
CONTROLLED EXTRACTION RETRY STATUS
------------------------------------------------------------

A controlled authorization extraction retry is implemented across
DocumentProcessor and OllamaProvider.

Retry applies only to:

- authorization
- authorization_renewal

A retry can be triggered when:

- Extraction output is not a dictionary
- fields is missing or invalid
- service_lines is missing or invalid
- Top-level service_code exists while service_codes is empty
- A service-code result exists but no non-empty service-line rows exist
- A service-line row contains contextual values such as dates or status
  but has neither service code nor quantity
- Multiple service-line rows exist and a row lacks service code or
  quantity

Token count alone does not trigger a retry.

A shorter response can still be valid for a simpler document.

Only one retry is allowed.

Attempt routing is explicit:

- Attempt 1 uses the configured base seed, currently 42.
- Attempt 2 uses the deterministic alternate seed, currently 43.
- Attempt 1 uses the established extraction prompt.
- Attempt 2 appends a generic row-by-row verification addendum.
- Temperature remains 0 for both attempts.
- Retry prompt usage and seed values are recorded in PHI-safe metrics.

The retry addendum requires a fresh reading of the OCR text and
independent reconstruction of every service line. It requires row-level
evidence for service codes and quantities, prohibits combining values
from different rows, and instructs the model to return null or omit an
unsupported row rather than guess.

The two candidates are converted and deterministically validated
independently.

Candidates are never merged.

The candidate score considers supported structure only:

- Number of rows with both service code and quantity
- Number of rows with service code
- Number of rows with quantity
- Number of supported row values
- Number of supported selected top-level values

Model generation length is not used as proof of correctness.

Model confidence is not used as proof of correctness.

When the second candidate has a stronger deterministic score, the second
candidate is selected.

When both candidates have the same score, the first candidate is
retained.

A real retry event was observed before the generic retry prompt was
added. Attempt 1 used seed 42 and attempt 2 used seed 43. Both attempts
produced the same incomplete 1080-token pattern, so attempt 1 was
retained on a deterministic score tie. Semantic regression failed, and
human review remained active.

The generic retry verification prompt was then implemented and passed
synthetic tests. A real incomplete-first-attempt event using the new
retry prompt has not yet been observed.

------------------------------------------------------------
FIELD-LEVEL EVIDENCE STATUS
------------------------------------------------------------

Field-level extraction evidence is preserved on the Document model.

Each extracted field can retain:

- value
- confidence
- source_text

The platform also retains backward-compatible flat structures:

- extracted_data
- field_confidences

The DocumentProcessor converts Ollama extraction output into evidence
records, then synchronizes corrected values and confidence scores back
into the flat structures used by business rules and human review.

Original source_text remains preserved after deterministic correction.

This feature was tested successfully with real cached OCR text and real
local Ollama extraction.

------------------------------------------------------------
AUTHORIZATION SERVICE-LINE STATUS
------------------------------------------------------------

AuthorizationServiceLine is implemented as a neutral structured model.

Each service-line record can preserve:

- service_code
- modifier
- quantity
- start_date
- end_date
- status
- confidence
- source_text

Document now supports:

- service_lines
- existing flat extraction fields
- field-level evidence
- processing metrics
- validation actions
- human-review results

The Ollama extraction schema supports both:

- fields
- service_lines

The DocumentProcessor preserves valid service-line records while
retaining existing flat-field behavior.

The service-line structure does not apply payer-specific meaning.

It does not automatically interpret units as visits, sessions,
equipment quantities, or sufficient approval.

------------------------------------------------------------
DETERMINISTIC EVIDENCE VALIDATION STATUS
------------------------------------------------------------

A deterministic evidence-validation service is implemented and active
between extraction and business rules.

Current non-business-specific flat-field checks include:

- Normalize supported dates to YYYY-MM-DD
- Verify normalized dates appear in source evidence
- Deduplicate service-code lists
- Deduplicate authorized-unit lists
- Validate structured identifiers against source evidence
- Validate service-code tokens against source evidence
- Validate modifier structure
- Compare service_code with service_codes
- Clear request_type when checkbox or selection evidence is unsupported
- Clear approved_visits when approval context is unsupported
- Clear fields that require source evidence but have none
- Set invalidated field confidence to 0.0
- Preserve source_text after invalidation
- Emit deterministic validation actions
- Synchronize corrected values before business rules execute

Current service-line checks include:

- Remove service-line rows without source evidence
- Normalize service-line confidence
- Cap model confidence of 1.0 at 0.95
- Validate service-code support against row evidence
- Validate modifier structure and row-level support
- Validate quantity support against row evidence
- Normalize and validate service-line dates
- Validate status against row evidence
- Downgrade unsupported rows to no more than 0.50 confidence
- Emit low-confidence review actions below 0.85
- Remove duplicate service-line records
- Remove rows with no remaining supported structured values
- Detect supported top-level modifiers that cannot be reliably assigned
  to a validated service line
- Require review for unresolved modifier-to-service-line relationships
- Never copy a top-level modifier into a service line automatically

Current modifier relationship action:

Service-line modifier relationship requires verification

The validator remains separate from payer-specific and LTHHC business
rules.

------------------------------------------------------------
TOP-LEVEL CONFIDENCE NORMALIZATION STATUS
------------------------------------------------------------

Deterministic top-level confidence normalization is implemented.

Populated top-level extraction fields with model-reported confidence of
1.0 or 100 percent are capped at 0.95 before field-specific validation.

This prevents raw model certainty from being treated as deterministic
verification.

Current behavior:

- Populated values are capped at no more than 0.95.
- Existing confidence below 0.95 is preserved.
- Empty values receive confidence 0.0.
- Invalidated values receive confidence 0.0.
- Unsupported or conflicting evidence can be downgraded below 0.95.
- The confidence cap alone does not create a review action.
- Specific validation and business-rule failures still require review.
- Empty optional fields are excluded from minimum-field-confidence
  calculations.
- Numeric zero and boolean false remain meaningful populated values.

Files changed:

- src/services/evidence_validation_service.py
- src/services/review_decision_service.py
- tests/test_evidence_validation_service.py
- tests/test_review_decision_service.py
- tests/test_top_level_confidence_validation.py

Synthetic deterministic tests:

- Top-level confidence validation: 6 passed, 0 failed
- Evidence validation: 27 passed, 0 failed
- Review decision: 18 passed, 0 failed
- Document processor: 16 passed, 0 failed

Synthetic total:

Passed: 67
Failed: 0

Real Molina regression:

- Real cached PaddleOCR text
- Real local Ollama classification and extraction
- Supported populated top-level fields capped at 95 percent
- Empty or invalidated fields remained at 0 percent
- Minimum populated field confidence was 95 percent
- Human review remained active for legitimate validation and
  business-rule reasons
- PHI output remained suppressed

Real result:

Passed: 1
Failed: 0

Latest real performance:

- Total processing time: approximately 461.73 seconds
- OCR wall time: approximately 0.00 seconds using cached OCR
- Classification wall time: approximately 75.25 seconds
- Extraction wall time: approximately 386.48 seconds
- Extraction attempt count: 1
- Retry triggered: False
- Selected extraction attempt: 1

Limitations:

- A confidence of 0.95 means strongly supported model output, not final
  human verification.
- The unresolved top-level modifier-to-service-line relationship still
  requires review.
- Authorization quantity meaning still requires confirmation.
- A successful real retry where attempt 2 produces a stronger candidate
  has not yet been observed.

Exact next starting point:

Review business-rule handling for authorization quantities and determine
whether supported service-line quantities can be classified safely
without treating units, visits, sessions, or equipment quantities as
equivalent.


------------------------------------------------------------
AUTHORIZATION RULE REGISTRY CLEANUP STATUS
------------------------------------------------------------

The active authorization business-rule implementation was confirmed as:

src/business_rules/rules/authorization_rule.py

The obsolete parallel implementation was removed:

src/business_rules/authorization_rule.py

RuleFactory continues to load plugins from:

src.business_rules.rules

Registry verification confirmed:

- authorization resolves to AuthorizationRule
- authorization_renewal resolves to AuthorizationRenewalRule
- both classes come from src.business_rules.rules.authorization_rule
- no root-level authorization rule is registered
- no duplicate registry implementation remains active

Files changed:

- Deleted src/business_rules/authorization_rule.py
- Added tests/test_authorization_rule_registry.py

Synthetic deterministic registry test:

Passed: 5
Failed: 0

------------------------------------------------------------
AUTHORIZATION QUANTITY RULE STATUS
------------------------------------------------------------

The active authorization rule now recognizes positive quantities from:

- approved_visits
- authorized_units
- validated authorization service-line quantities

A supported quantity is treated only as evidence that a quantity exists.

The rule does not automatically interpret a quantity as:

- visits
- sessions
- units
- equipment quantities
- recurring services
- sufficient approval

When no positive quantity exists, the rule returns:

Missing authorization quantity

When a positive quantity exists but its meaning has not been confirmed,
the rule returns:

Authorization quantity requires verification

The action is emitted only once even when both flat fields and service
lines contain quantities.

Files changed:

- src/business_rules/rules/authorization_rule.py
- tests/test_authorization_quantity_rule.py

Synthetic deterministic quantity tests:

Passed: 8
Failed: 0

Related regression tests:

- Authorization registry: 5 passed, 0 failed
- Review decision: 18 passed, 0 failed
- Document processor: 16 passed, 0 failed

Related synthetic total:

Passed: 47
Failed: 0

------------------------------------------------------------
LATEST REAL QUANTITY REGRESSION
------------------------------------------------------------

The known Molina authorization regression was processed using:

- Real cached local PaddleOCR text
- Real local Ollama classification
- Real local Ollama extraction
- Deterministic evidence validation
- Updated authorization quantity business rules
- Human-review decision
- PHI-safe diagnostics

Verified real behavior:

- Two validated service-line records were preserved
- Positive quantities 1 and 6 were preserved
- Top-level authorized_units contained 6 and 1
- Missing authorization quantity was not returned
- Authorization quantity requires verification was returned
- Quantity meaning was not guessed
- Human verification remained required
- PHI output remained suppressed

Real result:

Passed: 1
Failed: 0

Real or mock:

Real cached OCR and local Ollama processing

Latest real performance:

- Total processing time: approximately 369.27 seconds
- OCR wall time: approximately 0.00 seconds using cached OCR
- Classification wall time: approximately 67.83 seconds
- Extraction wall time: approximately 301.43 seconds
- Extraction attempt count: 1
- Retry triggered: False
- Selected extraction attempt: 1
- Classification generation rate: approximately 6.46 tokens/second
- Extraction generation rate: approximately 5.56 tokens/second

Limitations:

- Quantity type remains unresolved without explicit supporting evidence.
- Units are not treated as visits.
- A positive quantity is not automatically treated as sufficient
  approval.
- The unresolved modifier-to-service-line relationship still requires
  review.
- A real retry where attempt 2 produces a stronger validated candidate
  has not yet been observed.

Exact next starting point:

Inspect the human-review output model and downstream document result
interfaces to determine how unresolved quantity type, modifier
relationships, and validation reasons should be presented to a reviewer
before mailbox-to-Smartsheet automation may proceed.


------------------------------------------------------------
REAL MOLINA AUTHORIZATION TEST STATUS
------------------------------------------------------------

A real cached authorization document was processed using:

- Real cached local PaddleOCR text
- Real local Ollama classification
- Real local Ollama extraction
- Real field-level evidence preservation
- Real authorization service-line extraction
- Real deterministic evidence validation
- Real deterministic business rules
- Real human-review decision
- Real PHI-safe Ollama timing and token metrics

Latest verified service-line result:

- Document type remained authorization
- Classification confidence remained 90 percent
- Exactly two service-line records were preserved
- Both service-line records preserved service code S9110
- One service-line record preserved quantity 1
- One service-line record preserved quantity 6
- Both service-line records preserved supported date ranges
- Dates were normalized to YYYY-MM-DD
- Both service-line records preserved Approved status
- Top-level modifier U1 remained supported
- Row-level source evidence did not reliably associate U1 with a
  specific service line
- Unsupported row-level modifier assignment was cleared
- The unresolved modifier relationship generated a validation action
- Human review remained required
- Raw source evidence and PHI were not printed

Latest real semantic regression result:

Passed: 1
Failed: 0

Real or mock:

Real cached OCR and real local Ollama processing

Latest normal-path retry result:

Extraction attempt count:
1

Extraction retry triggered:
False

Raw retry required:
False

Validated retry required:
False

Selected extraction attempt:
1

Latest real classification metrics:

Classification wall time:
Approximately 66.47 seconds

Classification Ollama duration:
Approximately 64.41 seconds

Classification prompt_eval_count:
1925

Classification eval_count:
54

Classification seed:
42

Latest real extraction metrics:

Extraction wall time:
Approximately 305.00 seconds

Extraction Ollama duration:
Approximately 302.96 seconds

Extraction prompt_eval_count:
2633

Extraction eval_count:
1201

Extraction attempt:
1

Extraction seed:
42

Latest total processing time:

Approximately 371.47 seconds

The real complete-first-attempt path passed.

The controlled retry path has been observed with real local Ollama
processing.

Observed real retry event before the generic retry prompt:

- Extraction attempt count was 2.
- Retry was triggered after deterministic validation cleared unsupported
  structure.
- Raw retry required was False.
- Validated retry required was True.
- Attempt 1 used seed 42.
- Attempt 2 used seed 43.
- Both attempts generated 1080 tokens.
- Both validated candidates had the same deterministic score.
- Attempt 1 was retained.
- Semantic regression failed.
- Human review remained active.
- No candidates were merged.
- Missing values were not invented.

The generic retry verification prompt has passed synthetic testing.

A real incomplete-first-attempt event in which the new generic retry
prompt produces a stronger validated second candidate has not yet been
observed.

The real test remains a regression fixture for the known local
authorization document. Its expected values must not be treated as
universal payer or service-code rules.

------------------------------------------------------------
SYNTHETIC DOCUMENT-PROCESSOR TEST STATUS
------------------------------------------------------------

Test file:

tests/test_document_processor.py

Verified conversion behavior:

- Missing service_lines returns an empty list
- Non-list service_lines returns an empty list
- Service-line row relationships are preserved
- Service-line confidence is normalized
- Empty service-line dictionaries are ignored
- Invalid service-line items are ignored
- Existing flat fields remain separate

Verified retry behavior:

- Complete authorization extraction does not trigger raw retry
- Complete validated authorization does not trigger retry
- Structurally incomplete service line triggers raw retry
- Missing service_codes list triggers raw retry
- Non-authorization documents do not use authorization retry
- Validation-cleared service-line structure triggers retry
- Stronger independently validated candidate is selected
- Equal candidates preserve the first attempt
- Candidates are never merged

Result:

Passed: 16
Failed: 0

Real or mock:

Synthetic deterministic test

------------------------------------------------------------
SYNTHETIC OLLAMA SERVICE-LINE TEST STATUS
------------------------------------------------------------

Test file:

tests/test_ollama_service_lines.py

Verified behavior:

- Extraction schema requires service_lines
- Empty service_lines are preserved
- Non-list service_lines return an empty list
- Service-line row relationships are preserved
- Confidence is normalized
- Empty rows are removed
- Invalid items are removed
- Attempt 1 uses the configured base seed
- Attempt 2 uses the deterministic alternate seed
- Retry seed selection is deterministic
- Invalid attempt values default safely to attempt 1
- Attempt 1 uses the established extraction prompt unchanged
- Attempt 2 appends the controlled verification prompt
- The retry prompt remains generic and contains no payer-specific values

Result:

Passed: 14
Failed: 0

Real or mock:

Synthetic deterministic test

------------------------------------------------------------
SYNTHETIC LLM ATTEMPT-ROUTING TEST STATUS
------------------------------------------------------------

Test file:

tests/test_llm_attempt_routing.py

Verified behavior:

- The default extraction attempt is 1
- A second extraction attempt is forwarded through LLMService to the
  configured provider

Result:

Passed: 2
Failed: 0

Real or mock:

Synthetic provider-routing test

------------------------------------------------------------
SYNTHETIC EVIDENCE-VALIDATION TEST STATUS
------------------------------------------------------------

Test file:

tests/test_evidence_validation_service.py

Verified behavior includes:

- Missing source evidence clears protected fields
- Supported identifiers remain intact
- Unsupported identifiers are cleared
- Supported dates normalize correctly
- Unsupported dates are cleared
- Duplicate service codes are removed
- Conflicting service-code fields downgrade confidence
- Invalid modifier structures are cleared
- Ambiguous request types are cleared
- Requested visits are not accepted as approved visits
- Clear approval context can preserve approved visits
- Flat fields remain synchronized
- Service-line dates normalize correctly
- Rows without source evidence are removed
- Unsupported service-line codes are cleared
- Invalid service-line modifiers are cleared
- Unsupported quantities are cleared
- Unsupported dates are cleared
- Unsupported statuses are cleared
- Full model confidence is reduced for deterministic verification
- Duplicate service lines are removed
- Low-confidence service lines generate review actions
- Unresolved top-level modifiers generate relationship review actions
- Supported row-level modifiers avoid the relationship action
- No modifier avoids the relationship action
- Validation actions are deduplicated

Result:

Passed: 27
Failed: 0

Real or mock:

Synthetic deterministic test

------------------------------------------------------------
SYNTHETIC REVIEW-DECISION TEST STATUS
------------------------------------------------------------

Test file:

tests/test_review_decision_service.py

Verified behavior:

- Clean documents can receive Verified by AI
- Validation actions trigger human review
- Field confidence below 85 percent triggers review
- Classification confidence below 90 percent triggers recommended review
- Classification confidence below 75 percent triggers required review
- Successful business-rule actions do not trigger review
- Business-rule failures trigger review
- Duplicate review reasons are removed
- Missing structured data triggers review

Result:

Passed: 18
Failed: 0

Real or mock:

Synthetic deterministic test

------------------------------------------------------------
AUTHORIZED-UNIT RECONCILIATION STATUS
------------------------------------------------------------

A deterministic same-candidate reconciliation check is implemented for
authorized_units and supported authorization service-line quantities.

The reconciliation is deliberately limited:

- It runs only when authorized_units already contains a populated
  extracted value.
- It compares that existing flat value with independently validated
  service-line quantities from the same extraction candidate.
- It may restore a supported quantity omitted from the flat list when
  the same candidate preserved that quantity on a validated service
  line.
- It never combines values from separate Ollama attempts.
- It never creates authorized_units when the flat field is missing or
  empty.
- It never interprets quantities as visits, sessions, equipment,
  recurring services, or sufficient approval.
- It preserves source_text.
- It uses the lowest supporting confidence.
- It emits a human-review validation action when reconciliation occurs.

Validation action:

Authorized units were reconciled from supported service-line evidence

Synthetic reconciliation result:

Passed: 7
Failed: 0

Synthetic regression results:

- Evidence validation: 27 passed, 0 failed
- Document processor: 16 passed, 0 failed
- Authorization quantity rules: 8 passed, 0 failed
- Review decision: 18 passed, 0 failed

Combined synthetic result:

Passed: 76
Failed: 0

------------------------------------------------------------
LATEST REAL RECONCILIATION REGRESSION
------------------------------------------------------------

The known Molina authorization regression was rerun after implementing
same-candidate authorized-unit reconciliation.

Real result:

Passed: 1
Failed: 0

Real or mock:

Real cached PaddleOCR text and real local Ollama processing

Verified output:

- Document type remained authorization.
- Classification confidence remained 90 percent.
- Exactly two service-line records were preserved.
- Service-line quantities 1 and 6 were preserved.
- Top-level authorized_units preserved both 6 and 1.
- Semantic regression passed.
- Human verification remained required.
- Authorization quantity still required verification.
- PHI output remained suppressed.
- Extraction attempt count was 1.
- Retry was not triggered.
- Attempt 1 was selected.

Latest timing:

- Total processing time: approximately 369.83 seconds
- Classification wall time: approximately 66.24 seconds
- Extraction wall time: approximately 303.59 seconds
- Extraction eval count: 1201
- Extraction generation rate: approximately 5.51 tokens per second

Repeatability status:

Completed successfully.

Three consecutive real cached-OCR and local-Ollama executions passed.
Each run triggered validated retry, selected the stronger second
candidate, preserved quantities 1 and 6, reconciled authorized_units
from same-candidate service-line evidence, retained human review, and
suppressed PHI output.


------------------------------------------------------------
THREE-RUN REAL REPEATABILITY RESULT
------------------------------------------------------------

The known Molina authorization regression completed three consecutive
successful real runs after same-candidate authorized-unit reconciliation
was implemented.

Final result:

Successful consecutive runs: 3 of 3

REPEATABILITY RESULT:

PASSED

Real or mock:

Real cached PaddleOCR text and real local Ollama processing

All three runs confirmed:

- Document type remained authorization.
- Classification confidence remained 90 percent.
- Attempt 1 produced the known incomplete 1080-token extraction pattern.
- Deterministic validation identified incomplete supported structure.
- Raw retry required remained False.
- Validated retry required remained True.
- Controlled extraction retry was triggered.
- Attempt 1 used seed 42.
- Attempt 2 used seed 43.
- Attempt 2 produced the stronger 1198-token extraction pattern.
- Attempt 2 was selected by deterministic candidate scoring.
- Candidates were independently validated.
- Candidates were never merged.
- Both service-line records preserved service code S9110.
- Service-line quantities 1 and 6 were preserved.
- Top-level authorized_units preserved both quantities after
  same-candidate deterministic reconciliation.
- Reconciled authorized_units confidence was reduced to 50 percent using
  the lowest supporting confidence.
- Human verification remained required.
- Authorization quantity interpretation remained unresolved.
- Modifier-to-service-line ownership remained unresolved.
- PHI output remained suppressed.
- Semantic regression passed.

Run results:

Run 1:

- Passed: 1
- Failed: 0
- Total time: approximately 579.08 seconds
- Extraction attempts: 2
- Selected attempt: 2
- Attempt 1 eval count: 1080
- Attempt 2 eval count: 1198

Run 2:

- Passed: 1
- Failed: 0
- Total time: approximately 624.75 seconds
- Extraction attempts: 2
- Selected attempt: 2
- Attempt 1 eval count: 1080
- Attempt 2 eval count: 1198

Run 3:

- Passed: 1
- Failed: 0
- Total time: approximately 474.30 seconds
- Extraction attempts: 2
- Selected attempt: 2
- Attempt 1 eval count: 1080
- Attempt 2 eval count: 1198

Conclusion:

The controlled retry, independent validation, deterministic candidate
selection, same-candidate quantity reconciliation, and human-review
safeguards successfully handled the known variable extraction pattern
in three consecutive real executions.

The repeatability investigation for this regression fixture is complete.

This result does not prove universal model determinism. Repeated local
Ollama output still varied between incomplete attempt 1 and stronger
attempt 2 patterns. Reliability was achieved through controlled retry
and deterministic safeguards rather than reliance on model consistency.


------------------------------------------------------------
STRUCTURED HUMAN-REVIEW OUTPUT STATUS
------------------------------------------------------------

A neutral structured human-review output contract is implemented.

Files:

- src/services/review_output_service.py
- tests/test_review_output_service.py
- tests/test_review_output_integration.py

Document model integration:

- src/models/document.py now contains review_output.
- src/document_processing/document_processor.py attaches review_output
  only after extraction, validation, business rules, review decisions,
  and PHI-safe processing metrics are complete.
- The review-output service does not rerun or reinterpret extraction,
  validation, business rules, quantities, approval, modifiers, or
  review decisions.

The review output preserves:

- document type
- classification confidence
- extracted field value
- extracted field confidence
- extracted field source_text
- authorization service-line relationships
- service-line confidence
- service-line source_text
- validation actions
- business-rule actions
- human-review status
- human-review reasons
- minimum populated field confidence
- extraction attempt count
- extraction retry status
- selected extraction attempt
- authorized-unit reconciliation status

The review output deliberately excludes:

- raw OCR text
- local document file path

The exclusion applies to the neutral review handoff contract and
diagnostic output. It does not remove validated PHI-bearing field values
or source evidence required for authorized local review and future
approved Smartsheet mapping.

PHI handling:

- OCR and Ollama processing remain local and in-house.
- Structured PHI remains available in memory for approved operational
  workflows.
- Console output, processing metrics, test results, tracker content,
  temporary scripts, and Git history remain PHI-safe.
- Future Smartsheet writes may include approved PHI fields only through
  the approved LTHHC Smartsheet workspace and confirmed column mapping.
- Failed Smartsheet writes must never log or print the row payload.
- source_text must not be written to Smartsheet unless an approved
  destination and operational requirement are confirmed.

Synthetic deterministic results:

Review-output service:

Passed: 8
Failed: 0

Review-output integration:

Passed: 7
Failed: 0

Related regression results:

Review-decision service:

Passed: 18
Failed: 0

DocumentProcessor:

Passed: 16
Failed: 0

Combined synthetic result:

Passed: 49
Failed: 0

Latest real Molina review-output regression:

Passed: 1
Failed: 0

Real or mock:

Real cached PaddleOCR text and real local Ollama processing

Verified real behavior:

- Review output was attached to the completed Document.
- Nineteen field review records were retained.
- Two authorization service-line records were retained.
- Field value, confidence, and source_text structures were available.
- Human-review status matched the processed Document.
- Human-review reasons matched the processed Document.
- Validation actions were preserved.
- Business-rule actions were preserved.
- Extraction attempt count was preserved.
- Retry status was preserved.
- Selected extraction attempt was preserved.
- Raw OCR text was not exposed by the review-output contract.
- The local document path was not exposed by the review-output contract.
- Semantic regression passed.
- PHI output remained suppressed.

Latest real execution:

- Total processing time: approximately 383.60 seconds
- OCR wall time: approximately 0.00 seconds using cached OCR
- Classification wall time: approximately 73.59 seconds
- Extraction wall time: approximately 310.00 seconds
- Extraction attempt count: 1
- Retry triggered: False
- Selected extraction attempt: 1
- Review-output field count: 19
- Review-output service-line count: 2

Current limitations:

- Review output is an in-memory contract and is not yet serialized for
  an external system.
- Smartsheet column mappings are not yet defined or tested.
- No automatic Smartsheet row creation is enabled.
- Quantity meaning remains unresolved.
- Units are not automatically interpreted as visits, sessions,
  equipment, recurring services, or sufficient approval.
- Modifier-to-service-line ownership remains unresolved.
- source_text may contain PHI and must remain restricted to approved
  systems and workflows.
- The known Molina authorization remains a regression fixture and not a
  universal payer or service-code rule.

Exact next starting point:

Define a deterministic Smartsheet row-mapping contract from the
structured review output using synthetic data. Confirm required,
optional, review-only, and prohibited columns before enabling any
Smartsheet write. Preserve PHI-bearing operational values while keeping
logs, errors, metrics, tests, and Git history PHI-safe.


------------------------------------------------------------
KNOWN EXTRACTION AND VALIDATION LIMITATIONS
------------------------------------------------------------

The current llama3.1:8b extraction output is not approved for automatic
processing without human review.

Observed limitations:

- Service-line extraction varies between repeated real runs.
- The model may omit a service code or quantity from one row.
- The model may inconsistently populate service_codes and
  authorized_units.
- A fixed seed does not guarantee semantically identical output in the
  current local runtime.
- A supported top-level modifier may not be reliably associated with a
  specific service-line row.
- Ambiguous checkbox labels may be treated as selected by the model.
- Initial Request may be returned without reliable selection evidence.
- Requested visit quantities may be presented as approved values.
- The model may assign 1.0 confidence to ambiguous or weakly supported
  fields.
- Current confidence handling is conservative but not fully calibrated.
- Person names, payer names, provider names, descriptions, and some
  free-text values are not yet fully checked against source evidence.
- Authorized-unit values are retained but their business meaning has not
  been confirmed.
- Quantity validation currently uses exact token support and may require
  expansion for decimals, ranges, recurring quantities, or other
  confirmed document formats.
- Prompt instructions alone do not reliably enforce evidence rules.
- The retry path can improve resilience but does not guarantee a
  complete second result.
- Changing only the seed did not improve the observed real incomplete
  retry result.
- A retry may approximately double extraction time when both attempts
  require full local inference.
- The generic retry verification prompt was observed in three consecutive
  real incomplete-first-attempt events and produced a stronger second
  candidate each time.
- A stronger independently validated second candidate was selected in
  three consecutive real retry events.

Human review remains required whenever deterministic evidence or
business rules are incomplete.

------------------------------------------------------------
AUTHORIZATION BUSINESS-RULE STATUS
------------------------------------------------------------

Authorization documents may contain:

- visits
- sessions
- units
- recurring monthly services
- equipment quantities
- modifiers
- multiple service lines
- date ranges

Current conservative behavior:

- Do not require approved_visits when authorized_units exist.
- Do not automatically treat authorized_units as sufficient approval.
- Do not automatically treat requested visits as approved visits.
- Do not automatically assign a top-level modifier to a service line.
- Do not infer initial, renewal, extension, continuation, amendment,
  denial, or partial approval without reliable evidence.
- Require human verification for authorization quantity interpretation.
- Require human verification when subtype evidence is ambiguous.
- Require human verification when modifier-to-service-line ownership is
  unresolved.

The tested Molina document remains a regression fixture only.

No universal Molina, S9110, U1, RPM, quantity, or service-line mapping
has been implemented.

Required, optional, and conditionally required fields still need to be
confirmed with management.

Formal business-rule training has not yet started.

------------------------------------------------------------
TRAINING STATUS
------------------------------------------------------------

Training currently means building confirmed operational knowledge,
including:

- confirmed document labels
- extraction schemas
- prompt rules
- payer terminology
- corrected examples
- aliases
- service-code mappings
- modifier mappings
- validation rules
- business rules
- Smartsheet mappings
- human-review feedback

The current work remains focused on completing and stabilizing the
technical pipeline before formal business-rule training.

Do not hard-code conclusions from one document.

Fine-tuning is not currently required or approved as the next step.

------------------------------------------------------------
HUMAN-REVIEW STATUS
------------------------------------------------------------

The ReviewDecisionService is implemented, active, and synthetically
tested.

Human review can be triggered by:

- Missing document type
- Classification confidence below threshold
- Field confidence below threshold
- Missing structured extraction data
- Deterministic evidence-validation actions
- Business-rule actions other than registered success actions
- Unsupported evidence
- Ambiguous request type
- Unsupported approved quantity
- Authorization quantity requiring verification
- Unsupported service-line evidence
- Low-confidence service-line records
- Unresolved modifier-to-service-line relationships

Current statuses:

Verified by AI
Human Review Recommended
Human Review Required

Duplicate review reasons are removed.

Human review is functioning as a safety control.

The controlled retry does not bypass human review.

------------------------------------------------------------
PRIVACY AND SECURITY STATUS
------------------------------------------------------------

Privacy-safe OCR cache behavior was added and tested.

PHI-safe Ollama metric capture was added and tested.

Current safeguards include:

- Hash-only OCR cache filenames
- No document filenames in normal OCR cache logs
- No cache paths in normal OCR cache logs
- Sanitized OCR exceptions
- PHI-safe Molina regression output
- No raw service-line source_text in test output
- No raw OCR text in test output
- No patient identifiers in tracker content
- No prompts or model response content in processing metrics
- No extracted values in Ollama metrics
- No candidate values printed as retry diagnostics beyond existing
  approved regression fields

Before every commit, verify:

- .env is ignored
- data/incoming is ignored
- data/ocr_cache is ignored
- no PDF is staged
- no OCR text is staged
- no PHI is staged
- no token or credential is staged

------------------------------------------------------------
FILES CREATED OR MODIFIED IN CURRENT FEATURE
------------------------------------------------------------

Modified:

scripts/test_molina_document.py
src/ai/llm/llm_provider.py
src/ai/llm/llm_service.py
src/ai/llm/providers/mock_provider.py
src/ai/llm/providers/ollama_provider.py
src/document_processing/document_processor.py
tests/test_document_processor.py
tests/test_ollama_service_lines.py
update_project_tracker.py

Created:

tests/test_llm_attempt_routing.py

Existing files used without requiring changes:

src/models/document.py
src/services/evidence_validation_service.py
tests/test_evidence_validation_service.py
tests/test_review_decision_service.py

------------------------------------------------------------
TESTS RUN FOR CURRENT FEATURE
------------------------------------------------------------

Syntax checks:

python -m compileall

Result:

Passed for the modified Python files.

Formatting and whitespace check:

git diff --check

Result:

Passed with no output.

Synthetic DocumentProcessor test:

python -m tests.test_document_processor

Result:

Passed: 16
Failed: 0

Real or mock:

Synthetic deterministic test

Synthetic Ollama service-line and retry-prompt test:

python -m tests.test_ollama_service_lines

Result:

Passed: 14
Failed: 0

Real or mock:

Synthetic deterministic test

Synthetic LLM attempt-routing test:

python -m tests.test_llm_attempt_routing

Result:

Passed: 2
Failed: 0

Real or mock:

Synthetic provider-routing test

Synthetic evidence-validation test:

python -m tests.test_evidence_validation_service

Result:

Passed: 27
Failed: 0

Real or mock:

Synthetic deterministic test

Synthetic review-decision test:

python -m tests.test_review_decision_service

Result:

Passed: 9
Failed: 0

Real or mock:

Synthetic deterministic test

Real Molina semantic regression:

python -m scripts.test_molina_document

Result:

Passed: 1
Failed: 0

Real or mock:

Real cached PaddleOCR text
Real local Ollama classification
Real local Ollama extraction
Real deterministic evidence validation
Real business rules
Real human-review decision

Latest real path tested:

Complete first extraction
No retry required
First attempt selected
Semantic regression passed
Human review remained active

Previously observed real retry path:

Incomplete first extraction
Retry triggered after validation
Attempt 1 used seed 42
Attempt 2 used seed 43
Both attempts produced the same incomplete result
Candidates tied
First attempt selected
Semantic regression failed
Human review remained active
Candidates were not merged

New generic retry-prompt status:

Implemented
Synthetic tests passed
Real incomplete-first-attempt recovery not yet observed

------------------------------------------------------------
CURRENT FEATURE RESULT
------------------------------------------------------------

Implemented and tested:

- Conservative authorization quantity business rules
- Removal of the obsolete duplicate authorization-rule implementation
- Top-level confidence normalization
- Empty optional fields excluded from minimum-confidence calculation
- Populated fields without confidence remain conservatively scored
- Same-candidate authorized-unit reconciliation
- Preservation of value, confidence, and source_text
- Controlled authorization extraction retry
- Independent deterministic candidate validation
- Stronger-candidate selection without candidate merging
- Human-review routing for unsupported or ambiguous evidence
- PHI-safe real regression diagnostics

Focused synthetic results:

- Service-line quantity reconciliation: 7 passed, 0 failed
- Evidence validation: 27 passed, 0 failed
- Top-level confidence validation: 6 passed, 0 failed
- Document processor: 16 passed, 0 failed
- Authorization quantity rule: 8 passed, 0 failed
- Authorization rule registry: 5 passed, 0 failed
- Review decision: 18 passed, 0 failed

Combined focused result:

Passed: 87
Failed: 0

Real repeatability result:

- Three consecutive runs passed.
- Each run used real cached PaddleOCR text and real local Ollama.
- Each run produced an incomplete first candidate.
- Validated incompleteness triggered controlled retry.
- Each stronger second candidate was selected.
- Candidates were never merged.
- Quantities 1 and 6 were preserved.
- authorized_units was reconciled using evidence from the selected
  candidate only.
- Human review remained required.
- PHI output remained suppressed.

This proves the safeguards handle the known Molina regression fixture
repeatedly. It does not prove universal model determinism or remove the
need for human review.

------------------------------------------------------------
EXACT NEXT DEVELOPMENT STEP
------------------------------------------------------------

Define and test the structured human-review output and downstream
handoff contract before mailbox-to-Smartsheet automation proceeds.

The review payload must preserve and clearly expose:

- Extracted value
- Confidence
- source_text reference without printing PHI in logs
- Validation actions
- Business-rule actions
- Review status
- Review reasons
- Selected extraction attempt
- Whether retry occurred
- Whether authorized_units was reconciled
- Low-confidence service-line evidence
- Unresolved authorization quantity meaning
- Unresolved modifier-to-service-line ownership

Start by inspecting:

src/models/document.py
src/services/review_decision_service.py
src/document_processing/document_processor.py
tests/test_review_decision_service.py

Then define the smallest neutral review-output model or serialization
contract that uses existing validated data without duplicating
validation or business-rule logic.

Do not send PHI to external services.
Do not enable automatic Smartsheet routing until the human-review
contract and confirmed field mappings are tested.

------------------------------------------------------------
NEXT SESSION START COMMANDS
------------------------------------------------------------

git status --short
git diff --stat
git diff --check
git --no-pager diff --cached --name-status
git --no-pager diff --cached --check

Then inspect:

src/models/document.py
src/services/review_decision_service.py
src/document_processing/document_processor.py
tests/test_review_decision_service.py
update_project_tracker.py

Run the focused deterministic tests before changing the review-output
contract.

============================================================

------------------------------------------------------------
SMARTSHEET DOCUMENT ROW MAPPING STATUS
------------------------------------------------------------

The future operational Smartsheet destination will use one row per
processed document.

The original source document will be attached to that row after the
operational sheet, attachment workflow, access controls, and PHI-safe
error handling are approved.

The currently connected Smartsheet is the project tracker only.

The project tracker sheet, sheet ID, columns, and rows must not be used
for authorization or patient-document records.

The future operational sheet has not yet been created.

Implemented local boundaries:

- Policy-driven structured review-output field mapping
- One logical row mapping per document
- Required destination-column detection
- Review-only column identification
- Prohibited raw OCR, file-path, processing-metric, and source_text
  mappings
- Deterministic collection serialization
- Preservation of numeric zero and boolean false
- Human-review gating before automatic write readiness
- Destination-column name and positive-ID validation
- Missing destination-column detection
- Invalid and duplicate destination-ID detection
- PHI-safe destination-validation output containing names and IDs only

No Smartsheet SDK cells were created.

No Smartsheet row was created or updated.

No operational Smartsheet connection was attempted.

Files changed:

- src/models/smartsheet_mapping.py
- src/models/smartsheet_destination_validation.py
- src/services/smartsheet_review_row_mapping_service.py
- src/services/smartsheet_destination_validation_service.py
- tests/test_smartsheet_review_row_mapping.py
- tests/test_smartsheet_review_mapping_integration.py
- tests/test_smartsheet_destination_validation.py

Synthetic deterministic tests:

- Smartsheet destination validation: 12 passed, 0 failed
- Document-to-Smartsheet mapping integration: 9 passed, 0 failed
- Smartsheet review-row mapping: 12 passed, 0 failed
- Review-output service regression: 8 passed, 0 failed
- Review-output integration regression: 7 passed, 0 failed

Synthetic total:

Passed: 48
Failed: 0

Real or mock status:

- Synthetic deterministic only
- No mock external write
- No real external integration
- No operational destination sheet exists yet

PHI handling:

- Test values and source evidence were not printed
- Raw OCR text was excluded from the mapping contract
- Local file paths were excluded from the mapping contract
- source_text was preserved in local review output but prohibited from
  Smartsheet mapping
- Destination validation retained column names and IDs only
- No Smartsheet payload was logged

Limitations:

- The operational one-row-per-document sheet has not been created
- The final operational column list has not been approved
- The original-document attachment workflow is not implemented
- The current Smartsheet credentials and sheet ID belong only to the
  project tracker
- No authorization-document row may be written using the tracker sheet
- Service-line values remain represented within the document-level
  review contract and require an approved one-row serialization policy

Document-classification requirement:

Document identification is a first-class platform result because source
documents arrive in nonstandard formats from multiple service
coordinators.

The classification contract must be expanded before operational inbox
training begins.

Termination classification is restricted to termination or
discontinuation of an authorization or authorized service.

Employee, provider, vendor, and other administrative terminations must
not be classified as authorization or service termination.

Exact next starting point:

Implement and test a two-level document classification contract with
document category and subtype while preserving conservative unknown
handling and the existing separate local classification and extraction
requests.


------------------------------------------------------------
TWO-LEVEL DOCUMENT CLASSIFICATION STATUS
------------------------------------------------------------

Document identification is now represented as a two-level local
classification contract.

Classification fields:

- document_category
- document_subtype
- document_type
- confidence
- classification_reason

document_type remains a backward-compatible routing value for existing
extraction and authorization-retry behavior.

Current document categories:

- authorization
- referral
- termination
- denial
- assessment
- plan_of_care
- claim
- other
- unknown

Current authorization subtypes:

- initial
- renewal
- extension
- continuation
- amendment
- partial_approval
- unknown

Current termination subtypes:

- authorization_termination
- service_termination
- unknown

Termination scope is restricted to an authorization or authorized
service being terminated, discontinued, revoked, ended, closed, or
stopped.

Employee, provider, vendor, contract, and administrative terminations
must not be classified as authorization or service termination.

Classification and extraction remain separate local Ollama requests.

The classifier uses supported document purpose and content rather than
assuming a standard template, sender, logo, filename, payer, or service
coordinator format.

Unknown, missing, conflicting, invalid, or incompatible classification
values remain unknown or require human review.

The classifier does not infer a subtype from the presence of unselected
checkbox labels.

Legacy routing behavior:

- authorization initial and unknown subtype route as authorization
- authorization renewal, extension, continuation, and amendment route
  as authorization_renewal
- other categories route using their category value

A neutral business rule is implemented for recognized categories that
do not yet have category-specific business rules.

The neutral rule produces no business-rule actions.

No rule actions does not mean the document is verified. Classification
review, deterministic validation, field confidence, and human-review
decisions remain separate.

Unsupported internal document-routing values still raise an error.

Classification review gating now requires or recommends human review
when:

- document category is unknown
- document category is unsupported
- classification confidence is below configured thresholds
- authorization subtype is unknown
- termination subtype is unknown
- category and subtype are incompatible
- category is other
- classification reason is missing

Unknown termination subtype requires human review because the platform
must distinguish termination of the authorization as a whole from
termination of a specific authorized service.

Unknown authorization subtype currently recommends review rather than
inventing initial, renewal, extension, continuation, amendment, or
partial approval.

Files changed:

- src/ai/llm/providers/mock_provider.py
- src/ai/llm/providers/ollama_provider.py
- src/business_rules/rule_factory.py
- src/business_rules/rules/neutral_rule.py
- src/document_processing/document_processor.py
- src/models/document.py
- src/services/review_decision_service.py
- src/services/review_output_service.py
- tests/test_classification_review_gating.py
- tests/test_document_classification_contract.py
- tests/test_neutral_business_rule.py
- tests/test_processor_classification_integration.py
- tests/test_review_decision_service.py

Synthetic deterministic and provider-routing tests:

- Classification review gating: 11 passed, 0 failed
- Review decision service: 18 passed, 0 failed
- Processor classification integration: 10 passed, 0 failed
- Neutral business-rule routing: 6 passed, 0 failed
- Document classification contract: 15 passed, 0 failed
- Document processor regressions: 16 passed, 0 failed
- Review-output service regressions: 8 passed, 0 failed
- Review-output integration regressions: 7 passed, 0 failed
- LLM extraction-attempt routing: 2 passed, 0 failed

Synthetic total:

Passed: 93
Failed: 0

Real or mock status:

- Synthetic deterministic tests
- Synthetic provider-routing tests
- No PaddleOCR prediction
- No local Ollama request
- No Microsoft Graph call
- No Smartsheet call
- No external integration

PHI handling:

- No OCR text was printed
- No extracted document values were printed
- No patient documents were used
- No patient-identifying paths were used
- Classification metrics retained PHI-safe metadata only
- Review output continues to exclude raw OCR text and local file paths
- No source_text or Smartsheet payload was logged

Limitations:

- The taxonomy is an approved initial classification contract and will
  require expansion from human-confirmed inbox examples
- No real local Ollama classification has yet been run against examples
  of referral, initial authorization, renewal, authorization
  termination, or service termination
- No approved training-example storage contract exists yet
- PHI-bearing documents and OCR text must remain local
- Human corrections must be captured without committing patient data,
  OCR text, source evidence, or identifying document paths
- The operational Smartsheet destination sheet does not yet exist
- The original-document attachment workflow is not implemented
- Category-specific business rules for non-authorization documents have
  not yet been defined

Exact next starting point:

Design a PHI-safe classification feedback and regression-fixture
contract that records human-confirmed category and subtype labels without
committing patient documents, OCR text, identifying paths, or extracted
PHI.


------------------------------------------------------------
PHI-SAFE CLASSIFICATION FEEDBACK AND FINGERPRINT STATUS
------------------------------------------------------------

A PHI-safe feedback contract records human-confirmed document
classification labels without retaining document content or patient
information.

Feedback fields:

- document_fingerprint
- predicted_category
- predicted_subtype
- confirmed_category
- confirmed_subtype
- classification_confidence
- correction_required
- reviewer_confirmation_status
- created_at

A reusable local DocumentFingerprintService now calculates lowercase
SHA-256 fingerprints by reading source files in one-megabyte chunks.

Fingerprint results contain exactly:

- fingerprint
- byte_count
- success
- status

Fingerprint results never contain:

- source paths
- filenames
- document content
- OCR text
- source_text
- extracted values
- patient identifiers
- exception messages

Failure results use PHI-safe statuses and return no fingerprint. Failed
or incomplete reads return a deterministic byte count of zero.

PaddleOCR now uses DocumentFingerprintService for OCR-cache identity.
The former private PaddleOCR file-hashing implementation and direct
hashlib dependency were removed. Existing cache filenames continue to
use only the lowercase SHA-256 fingerprint.

A local ClassificationFeedbackWorkflowService now coordinates:

1. local document fingerprinting;
2. validated feedback construction from ReviewOutput classification
   metadata;
3. local allowlisted JSONL storage.

The workflow source path is supplied only to the local fingerprint
service. It is not copied into feedback, storage, logs, or results.

Workflow results contain exactly:

- fingerprint
- byte_count
- success
- status

The feedback review adapter reads only category, subtype, and
classification confidence from ReviewOutput. It does not mutate the
review output or copy fields, service lines, source evidence, review
reasons, validation actions, business-rule actions, or other
PHI-bearing values.

Reviewer confirmation status remains deterministic:

- unchanged labels require confirmed
- changed labels require corrected

Validated feedback records are stored locally as JSON Lines under:

data/classification_feedback/classification_feedback.jsonl

The entire data/classification_feedback directory remains ignored by
Git.

The storage service accepts only ClassificationFeedback objects and
serializes an exact allowlist of feedback keys.

Duplicate detection and append execution remain inside an atomic local
lock-directory boundary. Repeated workflow submission for the same
fingerprint is idempotent: the initial submission is stored and later
submissions return duplicate_fingerprint without writing another record.

Files changed:

- src/ai/ocr/providers/paddle_ocr_provider.py
- src/services/document_fingerprint_service.py
- src/services/classification_feedback_workflow_service.py
- tests/test_document_fingerprint_service.py
- tests/test_paddle_ocr_fingerprint_integration.py
- tests/test_classification_feedback_workflow_service.py

Affected regressions also verified:

- src/services/classification_feedback_service.py
- src/services/classification_feedback_review_service.py
- src/services/classification_feedback_storage_service.py
- tests/test_classification_feedback_service.py
- tests/test_classification_feedback_review_integration.py
- tests/test_classification_feedback_storage_service.py
- tests/test_classification_feedback_storage_locking.py

Tests:

- Document fingerprint service: 10 passed, 0 failed
- PaddleOCR fingerprint integration: 3 passed, 0 failed
- Classification feedback workflow: 7 passed, 0 failed
- Classification feedback contract: 11 passed, 0 failed
- Feedback-to-review integration: 11 passed, 0 failed
- Local feedback storage: 11 passed, 0 failed
- Concurrent storage locking: 4 passed, 0 failed

Affected regression total:

Passed: 57
Failed: 0

Real or mock status:

- Synthetic deterministic local-file tests
- Synthetic deterministic integration tests
- Synthetic deterministic local workflow tests
- Synthetic concurrent local-storage tests
- PaddleOCR prediction was not called
- Local Ollama was not called
- Microsoft Graph was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- Only synthetic document bytes were used
- No patient documents were used
- No OCR text was printed or stored by these tests
- No source_text was copied into feedback storage
- No extracted document values were stored
- No identifying source paths or filenames were returned
- No email content was used
- Feedback storage contained only allowlisted classification metadata
- Test files and feedback stores used temporary local directories
- The ignored production feedback directory was not read or printed

Limitations:

- The production human-review submission path does not yet invoke
  ClassificationFeedbackWorkflowService
- No user interface currently submits reviewer confirmation
- The workflow has not been tested with a real PHI-bearing document
- PaddleOCR integration was tested with a synthetic cache hit; no fresh
  PaddleOCR prediction was performed
- The JSONL store does not provide administrative retention, export,
  migration, or recovery tooling
- Lock timeout behavior has not been tested with separate
  operating-system processes
- Feedback records are not yet converted into committed synthetic
  regression fixtures
- Document mutation during fingerprint calculation is not explicitly
  detected
- Human-confirmed labels do not authorize retaining or committing source
  documents, OCR text, source evidence, or extracted PHI

------------------------------------------------------------
EXPLICIT REVIEW CONFIRMATION SUBMISSION STATUS
------------------------------------------------------------

A production-facing ReviewConfirmationSubmissionService now provides
the explicit boundary between a completed local human review and the
classification feedback workflow.

The service accepts:

- one already-processed Document
- the Document's existing attached ReviewOutput
- reviewer-confirmed document category
- reviewer-confirmed document subtype
- explicit reviewer confirmation status
- optional PHI-safe timestamp

Accepted confirmation statuses:

- confirmed
- corrected

Any blank, pending, unsupported, or implicit confirmation status is
rejected before the feedback workflow is called.

The service does not rerun:

- OCR
- classification
- extraction
- deterministic validation
- candidate selection
- business rules
- review decisions
- review-output construction

The existing ReviewOutput object is passed unchanged to the feedback
workflow. The processed Document and its review snapshot are not
mutated.

The source document path is used only as the local input to the existing
fingerprint workflow. It is not returned, logged, copied into feedback,
or included in storage.

Submission results contain exactly:

- fingerprint
- byte_count
- success
- status

Submission results exclude:

- source paths
- filenames
- OCR text
- raw document text
- extracted values
- field evidence
- source_text
- review fields
- service lines
- patient identifiers
- storage payloads

Files changed:

- src/services/review_confirmation_submission_service.py
- tests/test_review_confirmation_submission_service.py

Focused and affected tests:

- Review confirmation submission boundary: 12 passed, 0 failed
- Classification feedback workflow: 7 passed, 0 failed
- Classification feedback review integration: 11 passed, 0 failed

Test total:

Passed: 30
Failed: 0

Real or mock status:

- Synthetic deterministic boundary tests
- Synthetic deterministic workflow tests
- Synthetic deterministic review integration tests
- OCR was not called
- Ollama was not called
- Extraction was not called
- Deterministic validation was not called
- Business rules were not called
- Microsoft Graph was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No OCR text was printed or stored
- No extracted values were returned
- No source_text was copied into feedback
- No source paths were returned or printed
- Existing review output was passed unchanged
- Only synthetic local objects were used
- Feedback storage was not inspected or printed

Limitations:

- No end-user interface currently invokes this service
- No mailbox or Smartsheet workflow invokes this service
- Reviewer identity and authorization are not yet represented
- The service does not persist a separate review-submission audit event
- A real human correction has not yet been submitted
- The service assumes Document.file_path remains locally available when
  the reviewer submits feedback
- Explicit confirmation improves the classification feedback dataset
  but does not automatically retrain or modify Ollama model weights

------------------------------------------------------------
LOCAL CLASSIFICATION REVIEW INTERACTION STATUS
------------------------------------------------------------

A reusable local ClassificationReviewInteraction now provides the
smallest reviewer-facing interaction for confirming or correcting one
completed document classification.

The interaction receives one already-processed Document with an
attached ReviewOutput.

It displays only:

- predicted document category
- predicted document subtype
- classification confidence
- PHI-safe submission status

It does not display:

- source path
- filename
- OCR text
- raw document text
- classification reason
- extracted field values
- field evidence
- source_text
- service lines
- patient identifiers
- feedback-storage payloads

Reviewer actions:

- Confirm the predicted category and subtype
- Correct the category and subtype
- Cancel without submitting feedback

A confirmation uses the existing predicted labels and submits status
confirmed.

A correction requires both category and subtype and submits status
corrected.

Blank corrections, invalid selections, missing review output, and
invalid document objects are rejected before the submission service is
called.

The interaction calls ReviewConfirmationSubmissionService only after
an explicit reviewer choice.

The interaction does not rerun:

- document processing
- OCR
- classification
- extraction
- deterministic validation
- candidate selection
- business rules
- review decisions
- review-output construction

The processed Document and existing ReviewOutput are not mutated.

Files changed:

- src/ui/classification_review_interaction.py
- tests/test_classification_review_interaction.py

Focused and affected tests:

- Classification review interaction: 12 passed, 0 failed
- Review confirmation submission: 12 passed, 0 failed
- Classification feedback workflow: 7 passed, 0 failed

Test total:

Passed: 31
Failed: 0

Real or mock status:

- Synthetic deterministic UI-boundary tests
- Synthetic deterministic submission-boundary tests
- Synthetic deterministic workflow tests
- Document processing was not called
- OCR was not called
- Ollama was not called
- Microsoft Graph was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No OCR text was displayed
- No source paths were displayed
- No extracted values were displayed
- No source_text was displayed
- No classification reason was displayed
- Entered correction labels were not echoed
- No feedback-storage payload was displayed
- Only category, subtype, confidence, and status were displayed
- All test data was synthetic

Limitations:

- The interaction is reusable but is not yet attached to the general
  application menu
- The interaction is not yet attached to MailboxProcessor
- No persistent review queue currently exists
- Processed Document objects must remain available in memory
- Reviewer identity and authorization are not represented
- A real human reviewer has not yet submitted feedback
- The interaction improves the feedback workflow but does not retrain
  or modify Ollama model weights

------------------------------------------------------------
MAILBOX REVIEW SESSION COORDINATOR STATUS
------------------------------------------------------------

A local MailboxReviewSessionService now coordinates explicit review of
already-processed mailbox documents without modifying mailbox ingestion.

The service receives existing MessageProcessingResult objects and
invokes ClassificationReviewInteraction once for each processed
Document, in the original message and document order.

The coordinator does not:

- fetch mailbox messages
- download attachments
- process documents
- run OCR
- call Ollama
- perform classification
- perform extraction
- run deterministic validation
- apply business rules
- mark messages as read
- write to Smartsheet
- automatically submit feedback

Each document still requires an explicit reviewer action through the
existing ClassificationReviewInteraction.

The coordinator tracks only PHI-safe session metadata:

- message_count
- document_count
- submitted_count
- cancelled_count
- failed_count
- success
- status

Session results exclude:

- message identifiers
- email subjects
- source paths
- filenames
- OCR text
- raw document text
- extracted values
- source evidence
- source_text
- review content
- correction labels
- fingerprints
- storage payloads
- patient identifiers

Session statuses:

- completed
- completed_with_cancellations
- completed_with_failures
- no_documents
- invalid_message_results
- invalid_message_result

A cancelled review is counted separately and does not make the session
fail.

A failed submission is counted and causes the session result to report
completed_with_failures.

An empty message collection or a collection containing no processed
documents is treated as a successful no-op with status no_documents.

Existing MessageProcessingResult objects and their processed_documents
lists are not mutated.

Files changed:

- src/services/mailbox_review_session_service.py
- tests/test_mailbox_review_session_service.py

Focused and affected tests:

- Mailbox review session coordinator: 13 passed, 0 failed
- Classification review interaction: 12 passed, 0 failed
- Review confirmation submission: 12 passed, 0 failed

Test total:

Passed: 37
Failed: 0

Real or mock status:

- Synthetic deterministic coordinator tests
- Synthetic deterministic UI-boundary tests
- Synthetic deterministic submission-boundary tests
- Mailbox ingestion was not called
- Attachment download was not called
- Document processing was not called
- OCR was not called
- Ollama was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No mailbox message identifiers were returned
- No email subjects were returned
- No source paths were returned
- No filenames were returned
- No OCR text was returned
- No extracted values were returned
- No source_text was returned
- No review content was returned
- No correction labels were returned
- No fingerprints were returned
- No storage payloads were returned
- Only counts, booleans, and status were returned
- All test data was synthetic

Limitations:

- The coordinator is not yet connected to MailboxProcessor
- The coordinator is not yet invoked by a production command or menu
- Processed Document objects must remain available in memory
- No persistent review queue exists
- Reviewer identity and authorization are not represented
- No resume or recovery mechanism exists for interrupted review sessions
- No real mailbox messages or patient documents were used
- The existing scripts/test_mailbox_processor.py remains PHI-unsafe for
  real documents because it prints paths, OCR text, and extracted values

------------------------------------------------------------
MAILBOX REVIEW ORCHESTRATION STATUS
------------------------------------------------------------

A separate MailboxReviewOrchestrationService now connects mailbox
processing to the explicit local review session without merging their
responsibilities.

The orchestration service:

- calls MailboxProcessor.process_unread_messages exactly once
- validates and normalizes the requested unread-message limit
- passes the returned in-memory MessageProcessingResult collection
  directly to MailboxReviewSessionService
- forwards the optional created_at value
- preserves review-session counts and status
- sanitizes mailbox and review exceptions into fixed status values

The orchestration service does not inspect, print, log, copy, or return:

- message identifiers
- email subjects
- attachment paths
- filenames
- OCR text
- raw document text
- extracted values
- field evidence
- source_text
- review content
- reviewer correction labels
- fingerprints
- storage payloads
- patient identifiers

Orchestration results contain exactly:

- message_count
- document_count
- submitted_count
- cancelled_count
- failed_count
- success
- status

Supported orchestration statuses include:

- completed
- completed_with_cancellations
- completed_with_failures
- no_documents
- invalid_top
- mailbox_processing_failed
- review_session_failed

Mailbox ingestion remains owned by MailboxProcessor.

Explicit human review remains owned by MailboxReviewSessionService and
ClassificationReviewInteraction.

Files added:

- src/services/mailbox_review_orchestration_service.py
- tests/test_mailbox_review_orchestration_service.py

Focused orchestration tests:

Passed: 11
Failed: 0

Real or mock status:

- Mock orchestration test
- MailboxProcessor was mocked
- MailboxReviewSessionService was mocked
- Microsoft Graph was not called
- Attachment download was not called
- Document processing was not called
- OCR was not called
- Ollama was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No message identifiers were returned
- No email subjects were returned
- No source paths were returned
- No filenames were returned
- No OCR text was returned
- No extracted values were returned
- No source_text was returned
- No review content was returned
- No fingerprints were returned
- No storage payloads were returned
- Only counts, booleans, and status were returned
- All test data was synthetic

------------------------------------------------------------
PHI-SAFE MAILBOX REVIEW COMMAND STATUS
------------------------------------------------------------

A separate opt-in MailboxReviewCommand now provides a PHI-safe local
command boundary for the mailbox-review orchestration workflow.

The command runs only when explicitly invoked.

It is not attached to an automatic startup path or general application
menu.

The command:

- calls MailboxReviewOrchestrationService exactly once
- accepts an optional unread-message limit
- accepts an optional created_at value
- returns the orchestration result unchanged
- prints only PHI-safe summary fields

Displayed fields:

- message_count
- document_count
- submitted_count
- cancelled_count
- failed_count
- success
- status

The command does not print:

- message identifiers
- email subjects
- attachment paths
- filenames
- created_at
- OCR text
- raw document text
- extracted values
- source evidence
- source_text
- review content
- correction labels
- fingerprints
- storage payloads
- patient identifiers
- exception details

Files added:

- src/ui/mailbox_review_command.py
- tests/test_mailbox_review_command.py

Focused command tests:

Passed: 8
Failed: 0

Affected regression results:

- Mailbox review orchestration: 11 passed, 0 failed
- Mailbox review session: 13 passed, 0 failed

Combined tested result:

Passed: 32
Failed: 0

Real or mock status:

- Mailbox review command test used a mocked orchestration service
- Mailbox review orchestration test used mocked mailbox and review
  services
- Mailbox review session test was synthetic deterministic
- Microsoft Graph was not called
- Attachment download was not called
- Document processing was not called
- OCR was not called
- Ollama was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No mailbox data was displayed
- No source paths were displayed
- No filenames were displayed
- No OCR text was displayed
- No extracted values were displayed
- No source_text was displayed
- No review evidence was displayed
- No correction labels were displayed
- No fingerprint was displayed
- Only counts, success, and status were displayed
- All test data was synthetic

Limitations:

- The real opt-in command has not yet been executed against Microsoft
  Graph
- No real mailbox messages or patient documents were used
- No persistent review queue exists
- Processed Document objects remain in memory only
- Reviewer identity and authorization are not represented
- No resume or recovery exists for interrupted review sessions
- The command is not attached to a general application menu
- The existing scripts/test_mailbox_processor.py remains PHI-unsafe for
  real documents because it prints paths, OCR text, and extracted values
- Smartsheet submission is not enabled by this command

------------------------------------------------------------
REAL MAILBOX REVIEW EXECUTION STATUS
------------------------------------------------------------

The PHI-safe opt-in mailbox review command completed its first real
Graph-backed execution successfully.

Execution command:

python -m src.ui.mailbox_review_command --top 1

Real result:

- message_count: 1
- document_count: 1
- submitted_count: 1
- cancelled_count: 0
- failed_count: 0
- success: True
- status: completed

Real or mock status:

- Microsoft Graph mailbox access was real
- Attachment handling was real
- OCR used real cached OCR text
- Fresh PaddleOCR prediction was not performed
- Local Ollama classification and extraction were real
- Human review interaction was real
- Reviewer confirmation was explicit
- Classification feedback was stored locally
- Smartsheet was not called
- No external AI service was called

PHI handling:

- No message identifier was printed by the PHI-safe command
- No email subject was printed by the PHI-safe command
- No attachment path was printed by the PHI-safe command
- No filename was printed by the PHI-safe command
- No OCR text was printed by the PHI-safe command
- No extracted values were printed by the PHI-safe command
- No source_text was printed by the PHI-safe command
- No review evidence was printed by the PHI-safe command
- No feedback-storage payload was printed
- The final summary contained only counts, success, and status

Important limitation:

This was a real cached-OCR integration run, not a fresh OCR prediction.
The known document bytes matched an existing local OCR cache entry.

The existing PaddleOCR initialization behavior still created or loaded
local model objects before cached OCR text was reused.

The successful run confirms the current integration path:

Microsoft Graph
  -> attachment handling
  -> cached local OCR text
  -> real local Ollama
  -> structured processing
  -> explicit classification review
  -> local classification feedback storage
  -> PHI-safe command summary

Smartsheet submission remains disabled.

------------------------------------------------------------
CLASSIFICATION REVIEW WORDING STATUS
------------------------------------------------------------

The reviewer-facing menu wording was revised from:

Correct classification

to:

Revise classification

The change avoids implying that an alternate reviewer entry is
necessarily objectively correct. The underlying workflow remains
unchanged:

- Confirm classification keeps the predicted category and subtype
- Revise classification accepts reviewer-entered category and subtype
- Cancel submits no feedback

No extraction, validation, business-rule, review-output, fingerprint, or
feedback-storage behavior changed.

Affected test results:

- Classification review interaction: 12 passed, 0 failed
- Mailbox review session: 13 passed, 0 failed
- Mailbox review command: 8 passed, 0 failed

Combined result:

Passed: 33
Failed: 0

Test classification:

- Synthetic deterministic UI-boundary tests
- Synthetic deterministic coordinator tests
- Mock command-boundary tests

During these regression tests:

- Microsoft Graph was not called
- Attachment download was not called
- Document processing was not called
- OCR was not called
- Ollama was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No OCR text was displayed
- No source paths were displayed
- No extracted values were displayed
- No source_text was displayed
- No review evidence was displayed
- Only approved PHI-safe review metadata and status were displayed

Current limitations:

- The real integration used cached OCR rather than fresh OCR
- Only one real mailbox message and one document were processed
- The known document was used rather than a new document format
- No persistent review queue exists
- Processed Document objects remain in memory only
- Reviewer identity and authorization are not represented
- No interrupted-session resume or recovery exists
- Smartsheet submission is not enabled
- The model-reported confidence value is not deterministic proof of
  classification correctness
- The existing scripts/test_mailbox_processor.py remains PHI-unsafe for
  real documents because it prints paths, OCR text, and extracted values

Exact next starting point:

Run the complete end-of-day Git safety review. Confirm the classification
review wording change and this tracker update are the only intended
changes. Verify protected paths remain ignored, review the complete
noninteractive diff, confirm no PHI, OCR text, patient documents,
identifying paths, credentials, secrets, tokens, cache files, model
files, or temporary scripts are present, then stage only reviewed safe
files, commit, push, verify branch synchronization, and confirm a clean
working tree.


------------------------------------------------------------
FRESH OCR MAILBOX AND MAILBOX HANDLING STATUS
------------------------------------------------------------

A real Microsoft Graph-backed mailbox review run completed successfully
using a new document that did not have an existing OCR cache entry.

Execution command:

python -m src.ui.mailbox_review_command --top 1

Verified real processing path:

- Microsoft Graph mailbox access was real
- One unread inbox message was selected
- Attachment handling was real
- No OCR cache entry was found for the document
- A fresh local PaddleOCR prediction was performed
- OCR text was stored in the secured local OCR cache
- Local Ollama classification and extraction were real
- Explicit human classification review was performed
- The reviewer confirmed the predicted classification
- Classification feedback was stored locally
- Smartsheet was not called
- No external AI service was called

PHI-safe command result:

- message_count: 1
- document_count: 1
- submitted_count: 1
- cancelled_count: 0
- failed_count: 0
- success: True
- status: completed

This closes the previously outstanding fresh-OCR mailbox integration
gap. The earlier real mailbox test used cached OCR; this later run
verified the fresh local PaddleOCR path.

Mailbox unread-state diagnostic:

Microsoft Graph initially reported the visible test message as read even
though the Outlook client displayed it as unread. After explicitly
marking the message read and then unread in Outlook, Graph reported one
unread inbox message and the mailbox command processed it successfully.

This confirms that the unread-message Graph query itself behaved as
implemented. It also demonstrates that Read/Unread state is not a
sufficient long-term processing-state or idempotency mechanism.

Mailbox handling was then improved so successfully inspected messages
without a processable document do not remain indefinitely in the unread
queue.

New mailbox behavior:

- A message with no attachments is marked read after successful
  inspection.
- A message containing only unsupported attachments is marked read
  after successful inspection.
- A message whose attachment service returns no downloadable files is
  marked read after successful inspection.
- A message with a successfully processed supported document is marked
  read.
- Attachment-download failures remain unread for retry.
- Supported-document processing failures remain unread for retry.
- Mixed document success and processing failure remains unread for
  retry.
- Missing message IDs are not marked read.
- Mark-read failures remain explicit failures.
- Raw attachment-download exception details are not propagated.
- Raw document-processing exception details are not propagated.
- Identifying filenames are not embedded in mailbox-processing error
  strings.

MessageProcessingResult.succeeded continues to represent successful
document processing and is not redefined to mean that a message was
merely inspected or intentionally skipped.

Files changed:

- src/graph/mailbox_processor.py
- tests/test_mailbox_handling.py
- update_project_tracker.py

Focused mailbox-handling test:

Passed: 9
Failed: 0

Real or mock:

Mock mailbox-boundary test

Affected regression tests:

- Mailbox review orchestration: 11 passed, 0 failed
- Mailbox review session: 13 passed, 0 failed
- Mailbox review command: 8 passed, 0 failed

Combined tested result:

Passed: 41
Failed: 0

Test classification:

- Mailbox handling: mock boundary test
- Mailbox review orchestration: mock
- Mailbox review session: synthetic deterministic
- Mailbox review command: mock command-boundary
- Fresh mailbox integration: real Microsoft Graph
- Fresh OCR: real local PaddleOCR
- Classification and extraction: real local Ollama
- Human review: real explicit confirmation
- Classification feedback storage: real local storage
- Smartsheet: not called
- External AI: not called

PHI handling:

- No patient document was committed
- No OCR text was added to the tracker
- No patient identifiers were added to the tracker
- No source_text was added to the tracker
- No identifying document path or filename was added to the tracker
- No feedback payload was printed
- Mailbox command output contained only approved review metadata and
  PHI-safe counts, success, and status
- New mailbox error strings suppress raw exception details and
  identifying filenames
- data/incoming remains local-only
- data/ocr_cache remains local-only
- data/classification_feedback remains local-only

Current limitations:

- Read/Unread state is still the current mailbox selection mechanism
- A durable explicit processing-state or idempotency mechanism is not
  yet implemented
- Reviewer identity and authorization are not represented
- No interrupted-review resume or persistent review queue exists
- Smartsheet review submission is not enabled
- Final operational document taxonomy is still pending the confirmed
  list of possible document types
- A model-reported confidence value is not deterministic proof of
  correctness

Exact next starting point:

Complete Git safety review for the mailbox-handling implementation and
tracker update. Verify protected local data paths remain ignored, review
the complete noninteractive diff, confirm no PHI, OCR text, patient
documents, identifying paths, credentials, secrets, tokens, cache files,
model files, or temporary scripts are present, then stage only the
reviewed safe files, commit, push, verify synchronization, and confirm a
clean working tree.

After this change is safely committed, design the smallest durable
mailbox processing-state and idempotency boundary so production
processing does not rely solely on Outlook Read/Unread state.


------------------------------------------------------------
DURABLE MAILBOX MESSAGE IDEMPOTENCY STATUS
------------------------------------------------------------

Mailbox ingestion now has durable local message-level handled state.

Purpose:

Prevent a successfully handled Graph message from repeating attachment
download, document processing, OCR, Ollama processing, and human review
if the same message later appears unread again.

Implementation:

- Graph message IDs are normalized locally.
- Raw Graph message IDs are never persisted.
- SHA-256 of the message ID is used as the handled-marker filename.
- Marker content is the constant text handled.
- Durable state is stored under:
  data/mailbox_processing_state/
- The state directory is ignored by Git.
- MailboxProcessor checks durable state before attachment download.
- Already-handled messages skip attachment and document processing.
- Already-handled messages retry only the Graph mark-read operation.
- Successfully handled messages are recorded before mark-read.
- A mark-read failure preserves the handled marker so expensive
  document processing is not repeated.
- Attachment-download failures are not recorded as handled.
- Document-processing failures are not recorded as handled.
- Mixed document success and failure is not recorded as handled.
- State-check failures block processing.
- State-storage failures leave messages unread.
- Missing or invalid message IDs are not recorded.

State result contract:

- handled
- stored
- duplicate
- success
- status

The contract excludes:

- Graph message IDs
- message subjects
- senders
- email content
- attachment names
- local document paths
- OCR text
- extracted values
- source_text
- patient identifiers

Files changed:

- .gitignore
- src/graph/mailbox_processor.py
- src/services/mailbox_processing_state_service.py
- tests/test_mailbox_handling.py
- tests/test_mailbox_processing_state_service.py
- tests/test_mailbox_persistent_idempotency.py
- update_project_tracker.py

Focused processing-state tests:

Passed: 9
Failed: 0

Test type:

Synthetic deterministic local-state

Mailbox handling regression:

Passed: 12
Failed: 0

Test type:

Mock mailbox boundary

Mailbox review orchestration regression:

Passed: 11
Failed: 0

Test type:

Mock orchestration

Mailbox review session regression:

Passed: 13
Failed: 0

Test type:

Synthetic deterministic coordinator

Mailbox review command regression:

Passed: 8
Failed: 0

Test type:

Mock command boundary

Persistent state across separate MailboxProcessor instances:

Passed: 1
Failed: 0

Test type:

Synthetic deterministic local-state integration

Combined automated result:

Passed: 54
Failed: 0

Real external verification:

A previously processed Graph message was marked unread again and the
mailbox review command was rerun.

Observed second-run result:

- Messages: 1
- Documents: 0
- Submitted: 0
- Cancelled: 0
- Failed: 0
- Success: True
- Status: no_documents

This confirmed that the real Graph message was recognized as already
handled and did not re-enter document review.

Real or mock:

- Microsoft Graph: Real
- Durable mailbox state: Real local state
- Attachment processing on repeat run: Skipped
- OCR on repeat run: Not rerun
- Ollama on repeat run: Not rerun
- Human review on repeat run: Not rerun
- Smartsheet: Not called

PHI handling:

- No raw Graph message ID is stored in durable state.
- Durable filenames contain only SHA-256-derived identifiers.
- Marker content contains only the constant handled status.
- No email body, subject, sender, attachment name, document path,
  OCR text, extracted value, or source_text is stored in processing
  state.
- Tests use synthetic identifiers.
- Console verification used only PHI-safe counts, booleans, and status.
- data/mailbox_processing_state/ is ignored by Git.

Limitations:

- State is message-level, not document-level across different emails.
- Identical attachment bytes arriving in a different Graph message are
  treated as a new mailbox event.
- Concurrent processing claims are not implemented.
- Interrupted-run lease recovery is not implemented.
- Marker cleanup and retention policy is not yet defined.
- State is local to this installation.
- The current durable marker represents successful mailbox ingestion,
  not a persistent end-to-end human-review queue.

Exact next starting point:

Complete Git safety review, stage only the reviewed mailbox-idempotency
files and tracker update, commit, push, verify branch synchronization,
and confirm a clean worktree.

Atomic claims and interrupted-run recovery remain future production
hardening work and are not required before continuing higher-value
workflow development.


------------------------------------------------------------
REVIEWED SMARTSHEET WRITE BOUNDARY STATUS
------------------------------------------------------------

A controlled reviewed-write boundary is now implemented between the
existing logical Smartsheet mapping/destination-validation services and
the existing Smartsheet client.

Purpose:

Prevent unreviewed, unmapped, stale, mismatched, or invalid data from
reaching the Smartsheet row-write client.

Implementation:

- SmartsheetReviewedWriteService accepts only:
  - SmartsheetRowMappingResult
  - SmartsheetDestinationValidationResult
- The service refuses writes when the logical mapping is not ready.
- The service refuses writes when destination validation is not ready.
- The mapping column names must exactly match the validated destination
  column names.
- Every destination column ID is rechecked immediately before write.
- Boolean, zero, negative, missing, and invalid column IDs are rejected.
- One Smartsheet row is created only after all boundaries pass.
- The service invokes the existing SmartsheetClient.add_row method.
- The write-result contract contains only:
  - written
  - column_count
  - success
  - status
- The write result excludes:
  - mapped values
  - Smartsheet cell payloads
  - row payloads
  - row IDs
  - OCR text
  - source_text
  - filenames
  - local document paths
  - patient data

The existing logical mapping boundary continues to prohibit source_text,
raw OCR text, file paths, and processing metrics from Smartsheet
mapping.

The existing destination validator continues to resolve approved logical
column names to real positive Smartsheet column IDs before writing.

Files added:

- src/services/smartsheet_reviewed_write_service.py
- tests/test_smartsheet_reviewed_write_service.py
- tests/test_smartsheet_reviewed_write_integration.py

Focused reviewed-write tests:

Passed: 13
Failed: 0

Test type:

Mock Smartsheet write-boundary test

Existing document-to-Smartsheet mapping regression:

Passed: 9
Failed: 0

Test type:

Synthetic deterministic

Existing Smartsheet destination validation regression:

Passed: 12
Failed: 0

Test type:

Synthetic deterministic

Reviewed-write integration test:

Passed: 4
Failed: 0

Test type:

Synthetic deterministic integration with mocked Smartsheet client

Combined automated result:

Passed: 38
Failed: 0

Real Smartsheet destination-schema validation:

- Real Smartsheet API called
- Read-only sheet schema retrieval succeeded
- Rows read: 0
- Rows written: 0
- Required reviewed-write logical columns were present
- Missing mapped columns: 0
- Invalid column IDs: 0
- No document or row values were accessed

Real synthetic Smartsheet write:

- Real Smartsheet API called
- Mapping ready: True
- Destination ready: True
- Write ready: True
- Mapped columns: 12
- Missing columns: 0
- Invalid columns: 0
- Write attempted: True
- Write success: True
- Rows written: 1
- Column count: 12
- Status: written
- Microsoft Graph was not called
- PaddleOCR was not called
- Ollama was not called
- No patient data was used
- Only synthetic test values were written
- The Smartsheet row payload was not printed or logged

PHI handling:

- No real patient information was used in the external-write test.
- No OCR text was sent to or printed for Smartsheet.
- No source_text was mapped or written.
- No source document path or filename was mapped or written.
- No Smartsheet payload was printed or logged.
- No Smartsheet write result contains mapped values.
- .env remained Git-ignored.
- Smartsheet credentials were not printed.
- The configured destination sheet was validated using column titles and
  IDs only before the first write.

Limitations:

- The current reviewed-write service is not yet wired into the mailbox
  human-review session automatically.
- Classification confirmation alone does not authorize a Smartsheet
  write.
- The service requires an already-approved complete ReviewOutput mapping.
- A production policy/configuration for all document types is not yet
  centralized.
- The current mapping is focused on the existing authorization workflow.
- Service-line records are not written as independent Smartsheet rows.
- No real patient-bearing Smartsheet write has been performed.
- The synthetic integration-test row may remain in the test destination
  until intentionally removed.
- Real write retry/idempotency semantics for Smartsheet are not yet
  implemented.


------------------------------------------------------------
SMARTSHEET SHEET ROUTING CORRECTION
------------------------------------------------------------

The project tracker and reviewed AI-output destination now use separate
Smartsheet configuration boundaries.

Cause found during real integration testing:

SMARTSHEET_SHEET_ID had temporarily been changed from the project-tracker
sheet to the new AI reviewed-output destination. Existing tracker
services correctly continued using SMARTSHEET_SHEET_ID, which caused
update_project_tracker.py to search the AI destination for project task
names.

Correction:

- SMARTSHEET_SHEET_ID again identifies the project-tracker sheet.
- SMARTSHEET_PROJECT_TRACKER_SHEET_ID records the explicit local
  project-tracker destination.
- SMARTSHEET_AI_DESTINATION_SHEET_ID identifies the reviewed AI-output
  destination.
- SmartsheetClient now accepts a sheet-ID environment-variable name.
- Existing SmartsheetClient() callers preserve their original
  SMARTSHEET_SHEET_ID behavior.
- SmartsheetReviewedWriteService explicitly selects
  SMARTSHEET_AI_DESTINATION_SHEET_ID when no client is injected.
- No duplicate Smartsheet client or tracker service was created.

Files changed or added:

- src/clients/smartsheet_client.py
- src/services/smartsheet_reviewed_write_service.py
- tests/test_smartsheet_reviewed_write_service.py
- tests/test_smartsheet_reviewed_write_integration.py
- tests/test_smartsheet_sheet_routing.py
- update_project_tracker.py

Routing-focused tests:

Passed: 5
Failed: 0
Real or mock: Synthetic deterministic/mock
External integration: Not called

Affected reviewed-write, mapping, and destination regressions:

Passed: 38
Failed: 0
Real or mock: Synthetic deterministic/mock

Combined automated Smartsheet result:

Passed: 43
Failed: 0

Real external routing verification:

- Project-tracker connection succeeded.
- Project-tracker expected schema was present.
- AI-destination connection succeeded.
- AI-destination expected schema was present.
- Routing verification was read-only.
- Rows read: 0
- Rows written: 0
- Only column metadata was inspected.

Prior real synthetic Smartsheet write:

- Real Smartsheet API called.
- Mapping ready: True.
- Destination ready: True.
- Write ready: True.
- One synthetic row was written successfully.
- No patient data was used.
- Microsoft Graph was not called.
- PaddleOCR was not called.
- Ollama was not called.
- The row payload was not printed or logged.

PHI handling:

- No patient information was used in routing tests.
- No Smartsheet row values were read during routing verification.
- No OCR text or source_text was printed or logged.
- No patient document path or filename was printed or written.
- Smartsheet credentials and .env values were not printed.
- .env remained Git-ignored.
- Only PHI-safe schema metadata was inspected.

Limitations:

- Classification confirmation alone does not authorize a Smartsheet
  write.
- Reviewed writing is not yet automatically connected to the complete
  mailbox human-review workflow.
- Production mapping policy for all document types is not yet
  centralized.
- Service-line records are not yet written as independent rows.
- No real patient-bearing Smartsheet write has been performed.
- Smartsheet write retry/idempotency semantics are not yet implemented.

Exact next starting point after this commit:

Design the explicit workflow connection from a completely reviewed
ReviewOutput through logical mapping, destination validation, and
controlled Smartsheet writing.

Human review must remain the authority that decides whether automation
may proceed. Classification confirmation alone must not authorize the
write.

Exact next starting point:

Complete Git safety review and commit the reviewed Smartsheet write
boundary.

After that commit, design the explicit workflow connection that allows a
complete reviewed ReviewOutput to proceed through mapping, destination
validation, and Smartsheet writing.

Do not authorize Smartsheet writing merely because classification was
confirmed. The complete review/write-readiness boundary must remain
separate.


------------------------------------------------------------
COMPLETE REVIEW TO SMARTSHEET WORKFLOW STATUS
------------------------------------------------------------

Implemented and tested the explicit human-review authority boundary
required before reviewed AI output can proceed to Smartsheet.

Architecture completed:

ReviewOutput
-> explicit complete-review approval
-> logical Smartsheet mapping
-> destination validation
-> controlled reviewed write

Classification confirmation remains a separate feedback workflow and
cannot authorize Smartsheet writing.

Implementation:

- CompleteReviewApprovalService requires an explicit complete-review
  decision.
- Approval and rejection are separate explicit reviewer decisions.
- A ReviewOutput with unresolved human-review requirements cannot be
  approved for downstream automation.
- CompleteReviewApprovalResult contains only:
  - approved
  - success
  - status
- CompleteReviewApprovalInteraction provides a separate local final
  approval interaction.
- The interaction displays only PHI-safe workflow metadata:
  - field count
  - service-line count
  - whether review remains required
  - review-reason count
  - approval status
- Field values, service-line values, source_text, OCR text, patient data,
  classification reason, filenames, and paths are not displayed.
- MailboxCompleteReviewSessionService coordinates complete-review
  decisions separately from the existing classification-feedback
  mailbox session.
- SmartsheetReviewSubmissionService requires a valid successful
  CompleteReviewApprovalResult before mapping, destination validation,
  or controlled writing can proceed.
- A successful classification-feedback result cannot satisfy the
  complete-review approval contract.
- CompleteReviewSmartsheetWorkflowService coordinates:
  - explicit complete-review interaction
  - complete-review approval result
  - approval-gated Smartsheet submission
- Rejection, cancellation, unresolved review, invalid review output,
  mapping failure, and destination failure prevent writing.
- Existing SmartsheetReviewedWriteService remains the final narrow
  mapped-and-validated write boundary.

Files added:

- src/services/complete_review_approval_service.py
- src/services/complete_review_smartsheet_workflow_service.py
- src/services/mailbox_complete_review_session_service.py
- src/services/smartsheet_review_submission_service.py
- src/ui/complete_review_approval_interaction.py
- tests/test_classification_confirmation_smartsheet_gate.py
- tests/test_complete_review_approval_interaction.py
- tests/test_complete_review_approval_service.py
- tests/test_complete_review_smartsheet_workflow_service.py
- tests/test_mailbox_complete_review_session_service.py
- tests/test_smartsheet_review_submission_service.py

Focused and affected automated tests:

Passed: 120
Failed: 0

Test types:

- Synthetic deterministic
- Synthetic deterministic UI-boundary
- Synthetic deterministic coordinator
- Mock Smartsheet write-boundary
- Synthetic deterministic integration with mocked Smartsheet client
- Synthetic deterministic/mock coordinator

External systems:

- Real Smartsheet write: Not called
- Microsoft Graph: Not called
- PaddleOCR: Not called
- Ollama: Not called
- Classification feedback storage: Not called during the new safety-gate
  test

Safety behavior proven:

- Explicit complete-review approval is required before submission.
- Classification confirmation alone cannot authorize writing.
- Classification success=True cannot authorize writing.
- Classification status text "approved" cannot impersonate complete
  approval.
- Rejected complete reviews do not reach Smartsheet submission.
- Cancelled complete reviews do not reach Smartsheet submission.
- Unresolved human-review requirements do not reach submission.
- Invalid review output does not reach submission.
- Mapping and destination readiness remain independent required gates.
- Review output is not re-extracted, reinterpreted, or mutated by the
  approval workflow.

PHI handling:

- Automated tests used synthetic values only.
- No patient documents were used.
- No OCR text was printed or transmitted.
- No field or service-line source_text was printed or transmitted.
- No patient-bearing local path or filename was printed.
- No Smartsheet row payload was printed.
- PHI-safe workflow result contracts contain only booleans, counts, and
  statuses where applicable.
- No real patient-bearing Smartsheet write was performed.
- .env and protected local data locations remain outside the intended
  commit.

Limitations:

- The complete-review workflow is not yet connected to the live mailbox
  command/orchestration path.
- Available Smartsheet columns and mapping policies still need an
  explicit production orchestration source.
- Production mapping policy for all document types is not centralized.
- Service-line records are not yet written as independent Smartsheet
  rows.
- Real Smartsheet write retry/idempotency semantics remain future work.
- No real patient-bearing end-to-end write has been performed.

Exact next starting point after this commit:

Inspect the existing mailbox command/orchestration callers and design the
smallest explicit connection that invokes the separate complete-review
workflow after document processing while preserving classification
feedback as a separate step.

Do not allow classification confirmation to authorize Smartsheet
writing. Preserve human complete-review approval as the authority that
decides whether automation may proceed.



------------------------------------------------------------
FULL MAILBOX REVIEW / SMARTSHEET ORCHESTRATION - 2026-08-07
------------------------------------------------------------

Feature completed:

Added an explicit opt-in mailbox workflow that preserves
classification review as a separate step and requires separate
complete-review approval before any Smartsheet write may proceed.

Implemented production boundaries:

- Mailbox complete-review Smartsheet coordinator
- PHI-safe Smartsheet destination schema reader
- Explicit document-type Smartsheet mapping-policy registry
- Smartsheet reviewed-write configuration resolver
- Full mailbox review orchestration service
- Separate explicit full mailbox review command

Files changed:

src/services/mailbox_complete_review_smartsheet_service.py
src/services/smartsheet_destination_schema_service.py
src/services/smartsheet_mapping_policy_service.py
src/services/smartsheet_review_configuration_service.py
src/services/mailbox_full_review_orchestration_service.py
src/ui/mailbox_full_review_command.py
tests/test_mailbox_complete_review_smartsheet_service.py
tests/test_smartsheet_destination_schema_service.py
tests/test_smartsheet_mapping_policy_service.py
tests/test_smartsheet_review_configuration_service.py
tests/test_mailbox_full_review_orchestration_service.py
tests/test_mailbox_full_review_command.py

Focused tests:

Mailbox complete-review Smartsheet boundary:
13 passed, 0 failed.
Synthetic deterministic/mock.

Smartsheet destination schema reader:
10 passed, 0 failed.
Synthetic deterministic/mock.

Smartsheet mapping policy registry:
10 passed, 0 failed.
Synthetic deterministic.

Smartsheet review configuration resolver:
6 passed, 0 failed.
Synthetic deterministic/mock.

Full mailbox review orchestration:
10 passed, 0 failed.
Mock.

Full mailbox review command:
8 passed, 0 failed.
Mock.

Affected regression:

196 passed, 0 failed.

Test classification:

Synthetic deterministic and mock.

No real Smartsheet write occurred during the affected regression.
Microsoft Graph was not called during the affected regression.
OCR was not called during the affected regression.
Ollama was not called during the affected regression.

PHI handling:

Only synthetic values, counts, booleans, statuses, mapping metadata,
and destination column metadata were used or displayed.

No OCR text, source_text, patient data, filenames, identifying paths,
Smartsheet payload values, row IDs, credentials, or tokens were
printed or committed by these tests.

Safety behavior:

Classification confirmation remains separate from complete-review
approval.

Classification confirmation cannot authorize Smartsheet writing.

Complete-review rejection or cancellation prevents writing.

Missing or unconfigured mapping policy fails closed.

Missing destination columns fail closed.

The existing classification-only mailbox command remains separate.

Limitations:

Production Smartsheet mapping policies are intentionally not
hard-coded yet.

No payer-, service-code-, modifier-, subtype-, or fixture-specific
mapping policy was inferred.

The full mailbox command therefore cannot perform a production write
until explicitly approved production mapping policies are supplied.

Real Smartsheet retry/idempotency remains future work.

Independent service-line row writing remains future work.

No real patient-bearing end-to-end Smartsheet write was performed.

Exact next starting point:

Define and approve the production SmartsheetColumnPolicy mappings for
each supported document type, then connect those approved policies to
the SmartsheetMappingPolicyService used by the explicit full mailbox
review command.

Do not invent payer-, service-code-, modifier-, or document-specific
mapping decisions.

Do not allow classification confirmation to authorize Smartsheet
writing.

Preserve complete-review approval as the authority that decides
whether automation may proceed.

------------------------------------------------------------
SMARTSHEET DEMO SCHEMA AND APPROVED AUTHORIZATION POLICY - 2026-08-07
------------------------------------------------------------

Feature:
Prepared the reviewed Smartsheet path for the live authorization demo.

Files changed:

- src/services/smartsheet_destination_schema_service.py
- tests/test_smartsheet_destination_schema_service.py
- src/services/smartsheet_mapping_policy_service.py
- tests/test_smartsheet_mapping_policy_service.py
- src/services/smartsheet_review_configuration_service.py
- tests/test_smartsheet_review_configuration_service.py

Changes:

- Real Smartsheet SDK column collections are accepted as iterables instead
  of requiring a plain Python list.
- Destination column capitalization is preserved in mapping policies.
- Document-type and source-field keys remain normalized.
- Explicitly approved authorization mappings are registered:
  authorization_status -> Authorization Status
  service_codes -> Service Codes
  authorized_units -> Authorized Units
  start_date -> Start Date
  end_date -> End Date
- No payer-, service-code-, modifier-, or document-specific business
  conclusions were added.
- Complete human-review approval remains required before writing.

Focused tests:

- Smartsheet destination schema reader: 11 passed, 0 failed
- Smartsheet mapping policy registry: 10 passed, 0 failed
- Smartsheet review configuration resolver: 7 passed, 0 failed

Affected regression execution:

- 8 affected regression scripts completed successfully
- Script failures: 0
- Final full-mailbox orchestration group: 10 passed, 0 failed
- Synthetic deterministic/mock only

Real external read-only validation:

- AI destination schema read succeeded
- Destination column count: 13
- Approved authorization policy count: 5
- Configuration resolution status: ready
- Smartsheet rows read: 0
- Smartsheet rows written: 0

PHI handling:

- Only column metadata, field names, counts, booleans, and statuses were
  displayed.
- No OCR text, patient data, source_text, filenames, document paths,
  row values, or Smartsheet payload values were printed or committed.

Limitations:

- No real authorization document has yet been processed through this
  newly approved configuration.
- No real Smartsheet row has been written during this work.
- Service-line rows remain review-output data and are not independently
  written as multiple Smartsheet rows.
- Human approval remains required before a reviewed result may write.

Exact next starting point:

Run the live boss demo from a new unread authorization-type mailbox
attachment through Graph, local PaddleOCR, local Ollama, deterministic
validation, business rules, classification review, complete human review,
and the approved AI-destination Smartsheet write. Keep PHI-bearing values,
OCR text, filenames, paths, source_text, and payload values out of
terminal/chat output.


------------------------------------------------------------
DEMO-ONLY CLASSIFICATION REVIEW BYPASS - 2026-08-07
------------------------------------------------------------

Feature:
Added an explicit demo-only option allowing the AI classification and
extraction result to proceed without classification confirmation.

Files changed:

- src/services/mailbox_full_review_orchestration_service.py
- src/ui/mailbox_full_review_command.py
- tests/test_mailbox_full_review_orchestration_service.py
- tests/test_mailbox_full_review_command.py

Behavior:

- Normal production behavior remains unchanged by default.
- --demo-skip-classification-review bypasses only the classification
  review/feedback interaction.
- The existing AI classification and extraction result is preserved.
- Deterministic validation and business rules remain active.
- Complete human-review approval remains mandatory before Smartsheet
  writing.
- Classification bypass does not itself grant write authority.
- Demo output remains PHI-safe.

Focused tests:

- Full mailbox orchestration: 11 passed, 0 failed
- Full mailbox review command: 9 passed, 0 failed
- Synthetic deterministic/mock only

Affected regressions:

- 5 affected regression scripts completed successfully
- Script failures: 0
- Final command group: 9 passed, 0 failed
- Synthetic deterministic/mock only

External systems:

- Microsoft Graph: Not called
- Attachment download: Not called
- OCR: Not called
- Ollama: Not called
- Smartsheet external API: Not called
- Smartsheet rows written: 0

PHI handling:

- Only counts, booleans, statuses, and demo-mode metadata were displayed.
- No OCR text, patient data, extracted values, source_text, filenames,
  local document paths, Smartsheet payloads, or row values were printed
  or committed.

Limitations:

- Demo bypass has not yet been exercised against a fresh real mailbox
  authorization attachment.
- Final complete-review approval is intentionally still required before
  any real Smartsheet write.
- The bypass is for demonstration only and is not presented as trained
  production classification behavior.

Exact next starting point:

Run the live boss demo using a new unread authorization-type attachment
with --demo-skip-classification-review. Allow local PaddleOCR and Ollama
to classify and extract independently, preserve deterministic validation
and business rules, and stop at the final complete-review decision before
any Smartsheet write. Keep PHI-bearing values, OCR text, filenames, paths,
source_text, and Smartsheet payload values out of terminal/chat output.


------------------------------------------------------------
AUTHORIZATION RENEWAL SMARTSHEET POLICY - 2026-08-07
------------------------------------------------------------

Feature:
Extended the explicitly approved authorization Smartsheet mapping policy
to authorization_renewal after a real demo document was independently
classified by Ollama as authorization_renewal.

Files changed:

- src/services/smartsheet_review_configuration_service.py
- tests/test_smartsheet_review_configuration_service.py

Approved mapping for authorization_renewal:

- authorization_status -> Authorization Status
- service_codes -> Service Codes
- authorized_units -> Authorized Units
- start_date -> Start Date
- end_date -> End Date

Behavior:

- authorization and authorization_renewal now use the same explicitly
  approved five-column mapping.
- No payer-, code-, modifier-, quantity-, or document-specific business
  meaning was inferred.
- Deterministic validation and business rules remain unchanged.
- Complete human-review approval remains mandatory before Smartsheet
  writing.
- Classification alone still cannot authorize a write.

Focused test:

- Smartsheet review configuration resolver: 8 passed, 0 failed
- Synthetic deterministic/mock

Affected regressions:

- 5 affected regression scripts completed successfully
- Script failures: 0
- Final full mailbox command group: 9 passed, 0 failed
- Synthetic deterministic/mock only

Real external validation:

- authorization_renewal configuration resolved successfully against the
  real AI destination Smartsheet schema.
- Approved policy count: 5
- Destination column count: 13
- Read-only metadata validation
- Smartsheet rows written: 0

Real demo diagnostic:

- One real document was processed.
- Ollama document type: authorization_renewal
- Review output present: True
- Human review required: True
- Initial Smartsheet configuration failed safely with
  policy_not_configured before this approval was added.
- Cached OCR was used during the diagnostic run.

PHI handling:

- No OCR text, patient data, extracted values, source_text, filenames,
  document paths, Smartsheet payloads, or row values were displayed or
  committed.
- Diagnostics were limited to document type, counts, booleans, statuses,
  and configuration metadata.

Limitations:

- The newly approved authorization_renewal mapping has not yet completed
  a real Smartsheet write.
- The real document still requires final complete-review approval before
  writing.
- Cached OCR diagnostic execution is not described as fresh OCR.

Exact next starting point:

Rerun the live boss demo using the existing demo-only classification
review bypass. Allow the real document to proceed through the approved
authorization_renewal mapping, deterministic validation, business rules,
and final complete-review approval. Write to the AI destination
Smartsheet only after explicit complete-review approval. Keep PHI-bearing
values, OCR text, filenames, paths, source_text, and Smartsheet payload
values out of terminal/chat output.


------------------------------------------------------------
COMPLETE REVIEW RECOMMENDATION APPROVAL GATE - 2026-08-07
------------------------------------------------------------

Feature:
Corrected the complete-review approval and Smartsheet submission gates so
that an explicitly approved Human Review Recommended result may proceed,
while Human Review Required remains blocked.

Files changed:

- src/services/complete_review_approval_service.py
- src/services/smartsheet_review_row_mapping_service.py
- src/services/smartsheet_review_submission_service.py
- tests/test_complete_review_approval_service.py
- tests/test_smartsheet_review_row_mapping.py
- tests/test_smartsheet_review_submission_service.py

Behavior:

- Human Review Recommended may proceed only after explicit complete-review
  approval.
- Human Review Required remains blocked.
- Automatic mapping without explicit complete-review approval remains
  blocked when needs_human_review is true.
- Existing review metadata is preserved.
- Classification confirmation remains insufficient write authority.
- No deterministic validation or business-rule conclusions were weakened.

Focused tests:

- Complete review approval service: 10 passed, 0 failed
- Smartsheet review row mapping: 14 passed, 0 failed
- Approval-gated Smartsheet submission: 11 passed, 0 failed
- Synthetic deterministic/mock only

Affected regressions:

- Complete review approval interaction: 8 passed, 0 failed
- Complete review Smartsheet workflow: 8 passed, 0 failed
- Smartsheet review mapping integration: 9 passed, 0 failed
- Smartsheet reviewed write integration: 4 passed, 0 failed
- Mailbox complete review Smartsheet service: 13 passed, 0 failed
- Mailbox full review orchestration: 11 passed, 0 failed
- Mailbox full review command: 9 passed, 0 failed

Real demo finding:

- Real local document classified as authorization_renewal.
- Classification confidence: 0.90.
- Minimum field confidence: 0.95.
- Review status: Human Review Recommended.
- Review reason count: 7.
- Explicit approval was previously blocked by review_still_required.
- No Smartsheet row was written during the failed demo attempt.

PHI handling:

- No OCR text, patient data, extracted values, filenames, paths,
  source_text, or Smartsheet payload values were printed or committed.
- Diagnostics were limited to counts, confidence values, statuses,
  document classification labels, and booleans.

Limitations:

- The corrected recommended-review approval path has not yet completed a
  real Smartsheet write.
- Required-review cases remain intentionally blocked.
- Real local diagnostic reused cached OCR text.

Exact next starting point:

Retry the same real boss demo after resetting only the durable handled
marker for the unread demo message. Allow the authorization_renewal
document to proceed through final complete-review approval. If the result
remains Human Review Recommended and the reviewer explicitly approves it,
verify that one row is written to the approved AI-destination Smartsheet.
Keep all PHI-bearing values and payload contents out of terminal/chat
output.


------------------------------------------------------------
REAL BOSS DEMO SMARTSHEET WRITE SUCCESS - 2026-08-07
------------------------------------------------------------

Feature:
Completed the real boss-demo workflow through one successful reviewed
Smartsheet row write.

Real external integration result:

- Messages processed: 1
- Documents processed: 1
- Demo classification review skipped: true
- Final complete-review approval: approved
- Approved documents: 1
- Smartsheet rows written: 1
- Rejected documents: 0
- Failed documents: 0
- Workflow success: true
- Workflow status: completed

Review state:

- Fields present: 19
- Service lines present: 1
- Review reason count: 7
- Review was Human Review Recommended.
- Explicit complete-review approval authorized the reviewed submission.
- Human Review Required behavior remains blocked by deterministic tests.

Test classification:

- Real Microsoft Graph mailbox integration
- Real attachment processing
- Real local OCR/Ollama workflow
- Real complete-review interaction
- Real external Smartsheet write
- Demo-only classification-review bypass enabled

PHI handling:

- No patient data, OCR text, extracted values, filenames, local paths,
  source_text, message identifiers, or Smartsheet payload values were
  copied into chat or tracker output.
- Only counts, booleans, confidence/review metadata, and workflow statuses
  were reported.

Limitations:

- The live run used the latest supported local demo attachment and may
  reuse locally cached OCR text when the OCR cache is available.
- The demo bypass skips classification review only.
- Production automation still requires the existing explicit mappings,
  validation, business-rule, review, and approval boundaries.

Exact next starting point:

Preserve this successful boss-demo baseline. Next development should start
from the clean synchronized repository and should not broaden Smartsheet
mappings or bypass Human Review Required without a separately confirmed
business requirement.


------------------------------------------------------------
ENHANCED AUTHORIZATION DEMO FIELD MAPPING - 2026-08-10
------------------------------------------------------------

Feature:

Expanded the approved authorization and authorization-renewal review
mapping for the enhanced boss demo while preserving deterministic
validation, explicit mapping policy, human-review authority, and PHI-safe
diagnostics.

Implementation:

- Authorization Status now represents only an actual authorization
  decision or supported authorization state.
- Request wording is not treated as an authorization decision.
- Blended status text such as Approved Requested is deterministically
  rejected rather than written as a final status.
- Authorization status must retain direct source evidence.
- Added hours to the structured Ollama extraction contract.
- Added days_per_week to the structured Ollama extraction contract.
- Hours and days_per_week may be extracted only from direct document
  evidence.
- Hours and days_per_week must not be derived from units, visits,
  sessions, service codes, date ranges, or arithmetic.
- SmartsheetColumnPolicy now supports an explicitly approved optional
  confidence destination column.
- Review-field confidence is mapped directly from the existing
  ReviewField confidence value.
- Low confidence is preserved and is not increased to satisfy a
  threshold.
- source_text is still not mapped to Smartsheet.
- DOB remains unmapped.
- Authorization and authorization_renewal use the same explicitly
  approved mapping policy.

Approved value mappings:

- authorization_status -> Authorization Status
- authorization_number -> Authorization #
- service_codes -> Service Codes
- diagnosis_code -> Diagnosis Codes
- start_date -> Start Date
- end_date -> End Date
- authorized_units -> Authorized Units
- hours -> Hours
- days_per_week -> Days Per Week

Approved confidence mappings:

- authorization_number -> Authorization # Conf.
- service_codes -> Service Codes Conf.
- diagnosis_code -> Diagnosis Codes Conf.
- authorized_units -> Authorized Units Conf.
- hours -> Hours Conf.
- days_per_week -> Days Per Week Conf.

Files changed:

- src/ai/llm/providers/ollama_provider.py
- src/models/smartsheet_mapping.py
- src/services/evidence_validation_service.py
- src/services/smartsheet_mapping_policy_service.py
- src/services/smartsheet_review_configuration_service.py
- src/services/smartsheet_review_row_mapping_service.py
- tests/test_evidence_validation_service.py
- tests/test_ollama_service_lines.py
- tests/test_smartsheet_review_configuration_service.py
- tests/test_smartsheet_review_row_mapping.py

Focused tests:

- Evidence validation: 29 passed, 0 failed
- Smartsheet mapping policy registry: 10 passed, 0 failed
- Smartsheet review configuration resolver: 8 passed, 0 failed
- Smartsheet review row mapping: 15 passed, 0 failed
- Ollama service-line schema and prompt: 17 passed, 0 failed

Focused total:

Passed: 79
Failed: 0

Affected regressions:

- Review output service: 8 passed, 0 failed
- Smartsheet destination schema reader: 11 passed, 0 failed
- Smartsheet reviewed write boundary: 13 passed, 0 failed
- Authorization quantity rules: 8 passed, 0 failed
- Authorization rule registry: 5 passed, 0 failed

Affected regression total:

Passed: 45
Failed: 0

Combined automated result:

Passed: 124
Failed: 0

Test classification:

- Synthetic deterministic
- Synthetic deterministic/mock
- Mock Smartsheet write-boundary
- No real OCR prediction was called
- No real Ollama generation was called
- Microsoft Graph was not called
- No real Smartsheet row write occurred

Real external read-only Smartsheet validation:

- Real AI-destination Smartsheet API called
- Configuration success: True
- Configuration status: ready
- Approved policy count: 9
- Destination column count: 23
- Rows read: 0
- Rows written: 0
- Only column metadata was accessed

PHI handling:

- No patient data was printed or copied into tests or tracker output.
- No OCR text was printed.
- No source_text was printed or written to Smartsheet.
- No patient document filename or identifying local path was printed.
- No Smartsheet row payload values were printed.
- No credentials, tokens, or .env contents were printed.
- Real Smartsheet verification used only PHI-safe schema metadata.
- Synthetic tests used synthetic values only.

Limitations:

- Hours and days_per_week have not yet been exercised through a real
  local Ollama extraction run.
- The enhanced nine-field policy has not yet performed a real reviewed
  Smartsheet row write.
- The original document is not yet attached to the Smartsheet row.
- Document renaming for the enhanced demo is not yet implemented.
- A non-interactive explicit complete-review approval command option is
  not yet implemented.
- Human Review Required remains intentionally blocked.
- Authorization quantity meaning remains governed by the existing
  deterministic business-rule and review boundaries.
- No payer-, service-code-, modifier-, or fixture-specific conclusion
  was introduced.

Exact next starting point:

Preserve this tested mapping baseline. Next inspect the existing full
mailbox review command, complete-review approval interaction, reviewed
Smartsheet write service, and Smartsheet client attachment capabilities.

Implement the smallest explicit non-interactive complete-review approval
option without weakening Human Review Required, then implement the
reviewed-row attachment boundary and deterministic document-renaming
behavior.

After focused and affected tests pass, run the real local
OCR/Ollama/review workflow and perform a real Smartsheet write only after
explicit complete-review approval. Keep patient data, OCR text,
filenames, paths, source_text, and Smartsheet payload values out of
terminal and chat output.


------------------------------------------------------------
NON-INTERACTIVE COMPLETE REVIEW AND SMARTSHEET ROW ATTACHMENT STATUS
------------------------------------------------------------

Implemented explicit non-interactive complete-review approval.

CLI flag:

--approve-complete-review

The flag does not bypass the complete-review approval service.

It sends the explicit approved decision through the same
CompleteReviewApprovalService boundary used by interactive approval.

Current safety behavior remains:

- Human Review Recommended may proceed only after explicit complete
  review approval.
- Human Review Required remains blocked.
- Classification confirmation does not authorize Smartsheet writing.
- Existing interactive approval remains available when the explicit
  flag is not supplied.

Implemented Smartsheet row attachment support.

Current flow:

approved complete review
  -> deterministic Smartsheet mapping
  -> destination validation
  -> create reviewed Smartsheet row
  -> prepare temporary locally renamed document copy
  -> attach temporary copy to the newly created row
  -> remove temporary copy

The original local document is not renamed or modified.

Temporary test naming convention:

LTHHC_AUTH_TEST_<12-character SHA-256 fingerprint prefix>.<extension>

This is a temporary test policy only. The final LTHHC document naming
convention has not yet been defined.

The existing local DocumentFingerprintService supplies the SHA-256
fingerprint. Patient data, OCR text, source_text, authorization values,
original filename, and original path are not used in the test filename.

Smartsheet Python SDK support was confirmed locally:

attach_file_to_row(sheet_id, row_id, _file)

The installed SDK accepts a string path or file stream for _file.

SmartsheetReviewedWriteResult now preserves only PHI-safe write state:

- written
- column_count
- attachment_written
- success
- status

It does not return the Smartsheet row ID, filename, local path,
fingerprint, mapped payload, OCR text, source_text, or patient data.

If row creation succeeds but attachment preparation or attachment fails,
the result reports the partial state safely. The already-created
Smartsheet row is not automatically deleted.

Files added:

- src/services/document_attachment_naming_service.py
- tests/test_document_attachment_naming_service.py

Files changed include:

- src/clients/smartsheet_client.py
- src/services/smartsheet_reviewed_write_service.py
- src/services/smartsheet_review_submission_service.py
- src/services/complete_review_smartsheet_workflow_service.py
- src/services/mailbox_complete_review_smartsheet_service.py
- src/services/mailbox_full_review_orchestration_service.py
- src/ui/complete_review_approval_interaction.py
- src/ui/mailbox_full_review_command.py
- related focused and regression tests

Non-interactive approval testing completed before attachment work:

Focused:
54 passed
0 failed

Affected regressions:
52 passed
0 failed

Total for that tested checkpoint:
106 passed
0 failed

All were synthetic deterministic or mock tests.
No external Smartsheet, Microsoft Graph, OCR, or Ollama calls occurred.

Attachment and forwarding tests completed:

Document attachment naming:
2 passed
0 failed
Synthetic deterministic local-file test

Smartsheet reviewed write:
17 passed
0 failed
Mock Smartsheet write-boundary test

Approval-gated Smartsheet submission:
11 passed
0 failed
Synthetic deterministic/mock

Complete-review Smartsheet workflow:
9 passed
0 failed
Synthetic deterministic/mock

Mailbox complete-review Smartsheet boundary:
14 passed
0 failed
Synthetic deterministic/mock

Full mailbox review orchestration:
12 passed
0 failed
Mock

Full mailbox review command:
10 passed
0 failed
Mock

PHI handling:

- Synthetic values and synthetic files only were used in these tests.
- No real patient document was read during attachment tests.
- No Smartsheet external API write occurred.
- No Microsoft Graph call occurred.
- No OCR call occurred.
- No Ollama call occurred.
- No mapped Smartsheet payload was printed.
- No real filename, local patient path, OCR text, source_text, or patient
  data was printed.

Limitations:

- The attachment filename convention is temporary.
- A real Smartsheet row attachment has not yet been performed.
- If row creation succeeds and attachment later fails, the row can
  remain in Smartsheet and the result reports the failure safely.
- Automatic rollback of a successfully created row is not implemented.
- Final production naming requirements remain unresolved.
- Real OCR/Ollama/review/Smartsheet execution still requires explicit
  complete-review approval before writing.

Exact next starting point:

Perform the real boss-demo preflight using the latest supported local
attachment already used for testing. Keep patient data, OCR text,
source_text, filenames, local paths, fingerprints, row IDs, and
Smartsheet payload values out of terminal and chat output. Run real local
OCR/Ollama/review, require explicit complete-review approval, then write
the reviewed row and attach the temporary renamed copy to Smartsheet.

------------------------------------------------------------
SMARTSHEET ATTACHMENT STREAM AND VISIBLE CONFIDENCE FIX - 2026-08-10
------------------------------------------------------------

Feature:

Corrected the Smartsheet attachment upload boundary and aligned the
Smartsheet-facing minimum-field-confidence value with the confidence
columns actually displayed on the destination row.

Attachment correction:

- Installed Smartsheet Python SDK version 4.3.0 was inspected locally.
- Its attach_file_to_row multipart operation places the supplied object
  directly into files["file"].
- The prior implementation supplied a local path string.
- The real external test showed that Smartsheet accepted that string as
  a generic file attachment rather than uploading the document bytes.
- The attachment appeared as a generic file named file and could not be
  opened after download.
- SmartsheetClient now opens the prepared temporary document in binary
  mode and passes the real file stream to the SDK.
- The stream retains the temporary renamed attachment filename.
- The stream is closed immediately after the SDK call returns.
- The existing temporary attachment preparation and cleanup boundary is
  preserved.
- The original local source document remains unchanged.

Smartsheet minimum confidence correction:

- Internal ReviewOutput.minimum_field_confidence remains unchanged.
- Human-review decisions continue to use the full populated extraction
  field set.
- Smartsheet AI Minimum Field Confidence now represents the minimum only
  among populated fields that have explicit displayed confidence
  destination columns in the approved mapping policy.
- Hidden internal extraction fields no longer create a Smartsheet
  minimum that cannot be reconciled with the confidence cells visible
  to a reviewer.
- Individual mapped confidence values remain unchanged.
- Confidence values below the 0.85 review threshold remain preserved
  without being increased or normalized upward.

Files changed:

- src/clients/smartsheet_client.py
- src/services/smartsheet_review_row_mapping_service.py
- tests/test_smartsheet_client.py
- tests/test_smartsheet_review_row_mapping.py

Focused tests:

- Smartsheet client attachment boundary: 1 passed, 0 failed
- Smartsheet review row mapping: 18 passed, 0 failed

Focused total:

Passed: 19
Failed: 0

Affected regressions:

- Smartsheet reviewed write boundary: 17 passed, 0 failed
- Approval-gated Smartsheet submission: 11 passed, 0 failed
- Complete-review Smartsheet workflow: 9 passed, 0 failed
- Mailbox complete-review Smartsheet boundary: 14 passed, 0 failed
- Full mailbox review orchestration: 12 passed, 0 failed
- Full mailbox review command: 10 passed, 0 failed
- Classification-to-Smartsheet safety gate: 3 passed, 0 failed

Affected regression total:

Passed: 76
Failed: 0

Combined automated result:

Passed: 95
Failed: 0

Test classification:

- Synthetic deterministic tests
- Mock Smartsheet SDK attachment boundary
- Mock reviewed-write and workflow boundaries
- No real Smartsheet external API call during the fix tests
- No Microsoft Graph call
- No PaddleOCR call
- No local Ollama request

PHI handling:

- Synthetic values and synthetic attachment bytes only were used.
- No real patient document was read by the attachment boundary test.
- No OCR text was printed.
- No source_text was printed.
- No patient values were printed.
- No Smartsheet payload was printed.
- No row ID was printed.
- No real patient filename or local path was printed.

Limitations:

- The corrected binary-stream attachment path has not yet been verified
  with a new real Smartsheet attachment.
- The temporary attachment naming convention remains a test convention.
- Automatic rollback of a created row after a later attachment failure
  is not implemented.
- The internal human-review minimum confidence intentionally continues
  to evaluate all populated extracted fields and may differ from the
  Smartsheet-facing minimum used for reviewer display.

Exact next starting point:

After this fix is committed and synchronized, run one controlled real
Smartsheet attachment verification through the existing complete-review
approval boundary. Verify only PHI-safe attachment metadata and success
status. Do not print document values, OCR text, source_text, filenames,
local paths, fingerprints, row IDs, or Smartsheet payload values.

------------------------------------------------------------
SMARTSHEET REVIEW VISIBILITY AND RUN TYPE - 2026-08-10
------------------------------------------------------------

Feature:

Expanded the reviewed AI-destination row metadata so reviewers can see
the AI document classification, the reasons a document requires or
recommends review, and an explicit PHI-safe operational Run Type.

Smartsheet review visibility:

New mapped review metadata columns:

- AI Document Category
- AI Document Subtype
- AI Review Reasons

AI Review Reasons uses the authoritative ReviewOutput.review_reasons
collection and serializes reasons deterministically in preserved order.

The mapping does not rerun extraction, reinterpret values, or expose
source_text.

Run Type:

Added the existing Smartsheet column:

- Run Type

Run Type is explicit workflow metadata and is not extracted or inferred
from OCR, Ollama, filenames, document content, or patient data.

Allowed values:

- Production
- Boss Demo
- Attachment Verification
- Classification Metadata Test
- End-to-End Test

Production is the default.

Invalid or unavailable Run Type values fail the logical mapping closed.

Run Type is propagated through:

MailboxFullReviewCommand
-> MailboxFullReviewOrchestrationService
-> MailboxCompleteReviewSmartsheetService
-> CompleteReviewSmartsheetWorkflowService
-> SmartsheetReviewSubmissionService
-> SmartsheetReviewRowMappingService

Classification confirmation remains separate from complete-review
approval and does not authorize a Smartsheet write.

Files changed:

- src/services/complete_review_smartsheet_workflow_service.py
- src/services/mailbox_complete_review_smartsheet_service.py
- src/services/mailbox_full_review_orchestration_service.py
- src/services/smartsheet_review_row_mapping_service.py
- src/services/smartsheet_review_submission_service.py
- src/ui/mailbox_full_review_command.py
- tests/test_complete_review_smartsheet_workflow_service.py
- tests/test_mailbox_complete_review_smartsheet_service.py
- tests/test_mailbox_full_review_command.py
- tests/test_mailbox_full_review_orchestration_service.py
- tests/test_smartsheet_review_row_mapping.py
- tests/test_smartsheet_review_submission_service.py

Final tested results:

Smartsheet review-row mapping:
23 passed, 0 failed.
Synthetic deterministic.

Approval-gated Smartsheet submission:
11 passed, 0 failed.
Synthetic deterministic/mock.

Full mailbox review command:
11 passed, 0 failed.
Mock command boundary.

Complete-review Smartsheet workflow:
10 passed, 0 failed.
Synthetic deterministic/mock.

Mailbox complete-review Smartsheet boundary:
15 passed, 0 failed.
Synthetic deterministic/mock.

Full mailbox review orchestration:
13 passed, 0 failed.
Mock full-orchestration.

Document-to-Smartsheet mapping integration:
9 passed, 0 failed.
Synthetic deterministic.

Smartsheet reviewed-write boundary:
17 passed, 0 failed.
Mock Smartsheet write boundary.

Combined final current-feature result:

Passed: 109
Failed: 0

External systems during automated tests:

- Microsoft Graph: Not called
- PaddleOCR: Not called
- Ollama: Not called
- Smartsheet external write: Not called

Real Smartsheet metadata-only verification:

- Schema read success: True
- Schema status: ready
- Destination column count: 27
- Required new column count: 4
- Required new columns found: 4
- Missing new column count: 0
- Rows read: 0
- Rows written: 0

Verified destination columns:

- AI Document Category
- AI Document Subtype
- AI Review Reasons
- Run Type

Corrected real attachment verification:

The previously corrected binary-stream Smartsheet attachment path was
subsequently exercised through the real external boundary and manually
confirmed successful.

No document filename, patient value, OCR text, source_text, local path,
row ID, or Smartsheet payload value was included in tracker or chat
output.

PHI handling:

- Automated tests used synthetic values only.
- Review-reason tests did not print mapped values or source evidence.
- Raw OCR text is not mapped.
- source_text remains prohibited from Smartsheet mapping.
- Local patient-document paths are not mapped.
- Run Type accepts only approved PHI-safe operational labels.
- Smartsheet payload values were not printed or logged.
- Real schema verification used column metadata only.

Limitations:

- AI Review Reasons currently reflects the authoritative combined review
  reasons, which can include classification, deterministic validation,
  and business-rule reasons.
- A new real patient-bearing row has not yet been written with the new
  classification/review-reason/Run Type metadata.
- A fresh complete-review approval is required for any new real row.
- Automatic rollback after a successful row write followed by attachment
  failure is still not implemented.
- Smartsheet retry/idempotency remains future production hardening.

Exact next starting point:

Before the next real write, audit all deterministic validation-action and
business-rule-action producers used by AI Review Reasons to confirm that
the sheet-visible reason strings contain only generic PHI-safe reason
text and never interpolate extracted values or source_text.

Then run the controlled real boss-demo path using the latest supported
local attachment, explicit Run Type "Boss Demo", real local OCR/Ollama,
deterministic validation, business rules, and complete human review.

Write only after a fresh explicit complete-review approval.

Keep patient data, OCR text, extracted values, source_text, filenames,
local paths, fingerprints, row IDs, and Smartsheet payload values out of
terminal and chat output.


------------------------------------------------------------
RUN TYPE TEST PURPOSE AND DATE CONFIDENCE - 2026-08-11
------------------------------------------------------------

Feature:

Changed Smartsheet Run Type from fixed environment/demo labels to
explicit PHI-safe operator-supplied text describing why the execution
was performed.

Run Type behavior:

- No automatic Production fallback.
- No Boss Demo or other fixed environment/demo choices.
- Test runs require explicit nonblank Run Type text.
- Run Type is never inferred from OCR, extracted values, filenames,
  local paths, patient data, or document content.
- Mapper rejects blank values, values over 120 characters, and values
  containing carriage returns or line feeds.
- CLI requires --run-type.
- Run Type remains workflow metadata and not extracted document data.

Date confidence mapping:

Added existing Smartsheet confidence columns:

- Start Date Conf.
- End Date Conf.

Mappings:

- start_date -> Start Date / Start Date Conf.
- end_date -> End Date / End Date Conf.

The existing generic confidence-column mapping is used. These displayed
confidence values participate in the existing AI Minimum Field
Confidence calculation.

AI Review Reasons PHI-safety audit:

Reviewed review-decision, deterministic evidence-validation, review
output, document-processing, and authorization business-rule reason
producers.

Observed sheet-visible reason producers use generic fixed reason text,
controlled field names, confidence thresholds, and service-line
numbers. No reviewed producer interpolated extracted document values or
source_text into review reasons.

Added a synthetic deterministic regression proving document values,
source_text, and classification-reason text do not enter
ReviewDecisionService review reasons through the normal reviewed path.

Focused and affected regression results:

- Smartsheet review configuration: 8 passed, 0 failed
- Smartsheet review row mapping: 24 passed, 0 failed
- Mailbox full-review command: 11 passed, 0 failed
- Complete-review Smartsheet workflow: 10 passed, 0 failed
- Mailbox complete-review Smartsheet service: 15 passed, 0 failed
- Mailbox full-review orchestration: 13 passed, 0 failed
- Smartsheet review submission: 11 passed, 0 failed
- Smartsheet review mapping integration: 9 passed, 0 failed
- Review decision: 19 passed, 0 failed
- Reviewed Smartsheet write integration: 4 passed, 0 failed

Total listed regression passes:

124 passed
0 failed

Test classification:

Synthetic deterministic and mock only for this change set.

External boundaries:

- Microsoft Graph not called.
- Fresh PaddleOCR not called.
- Ollama not called.
- Smartsheet external write API not called.
- No new real Smartsheet row was written.

PHI handling:

- Synthetic test values only.
- OCR text and source_text were not printed.
- Smartsheet payload values were not printed.
- Review-reason regression verifies synthetic document values and
  source evidence are excluded from review reasons.
- Stale fixed Run Type label audit returned no matches.

Limitations:

Operator-supplied Run Type cannot be semantically guaranteed PHI-free
by current validation. CLI/help and project policy prohibit patient
information, document values, filenames, paths, and source_text.
Mapper validation checks structure, not general PHI detection.

No fresh real OCR/Ollama execution was performed for this change set.

Exact next starting point:

Run the controlled real local OCR/Ollama/review path with explicit
PHI-safe Run Type:

Review reason visibility and date confidence columns

Keep patient data, OCR text, extracted values, source_text, filenames,
local paths, payload values, and row IDs out of terminal/chat output.

A fresh explicit complete-review approval is required before any new
real Smartsheet row is written.


------------------------------------------------------------
CLASSIFICATION CORRECTION PROPAGATION AND WRITE SUMMARY - 2026-08-12
------------------------------------------------------------

Feature:

Fixed two defects discovered during a controlled real mailbox review and
Smartsheet write.

Classification correction propagation:

Human-confirmed classification corrections were previously stored as
classification feedback but the existing in-memory Document and
ReviewOutput retained the original predicted classification.

That allowed a later explicitly approved Smartsheet write to use the
original predicted subtype instead of the human-confirmed subtype.

After successful classification-feedback storage, the confirmed category
and subtype now update both:

- Document classification state
- Existing ReviewOutput classification state

The change does not rerun classification, OCR, Ollama, extraction,
validation, business rules, or review-output construction.

A failed feedback-storage result does not mutate classification state.

Smartsheet write-summary correction:

A successful reviewed row with an attachment returns:

written=True
success=True
status=written_with_attachment

MailboxCompleteReviewSmartsheetService previously counted a successful
write only when status was exactly written.

The coordinator now treats success=True plus written=True as the
successful-write contract, so successful rows with attachments are
counted as written instead of failures.

Files changed:

- src/services/review_confirmation_submission_service.py
- src/services/mailbox_complete_review_smartsheet_service.py
- tests/test_review_confirmation_submission_service.py
- tests/test_mailbox_complete_review_smartsheet_service.py

Real test that exposed the defects:

- Real mailbox processing was used.
- Cached local OCR text was used.
- Local Ollama classification/extraction path ran.
- Explicit local classification review was performed.
- Classification feedback was stored.
- Explicit complete-review approval was given.
- A real Smartsheet row and attachment were observed.
- The human-confirmed subtype did not reach the written row.
- The final summary reported the successful attached write as a failure.

No row values, patient data, OCR text, source_text, identifying filenames,
local document paths, Smartsheet payload values, or row IDs were copied
into tracker or chat output.

Focused and affected regression results after the fixes:

- Review confirmation submission: 12 passed, 0 failed
- Mailbox complete-review Smartsheet service: 16 passed, 0 failed
- Classification review interaction: 12 passed, 0 failed
- Mailbox review session: 13 passed, 0 failed
- Mailbox full-review orchestration: 13 passed, 0 failed
- Complete-review Smartsheet workflow: 10 passed, 0 failed
- Approval-gated Smartsheet submission: 11 passed, 0 failed

Total:

87 passed
0 failed

Test classification:

Synthetic deterministic and mock for post-fix verification.

External boundaries during post-fix regression tests:

- Microsoft Graph not called.
- OCR not called.
- Ollama not called.
- Smartsheet external API not called.
- No additional real row was written during post-fix regression testing.

PHI handling:

- Synthetic test values only.
- OCR text and source_text were not printed.
- Smartsheet payload values were not printed.
- Failure results remain PHI-safe.
- Classification correction tests use classification labels only.
- No external integration was invoked by the regression suites.

Limitations:

The two defects are covered by synthetic deterministic/mock regressions
but have not yet been reverified with a second real external Smartsheet
write after the fixes.

Exact next starting point:

After this tested change is committed and pushed, run one controlled real
full mailbox review with a brand-new unread supported attachment and the
PHI-safe Run Type:

Classification correction propagation and attachment write summary

If classification requires correction, confirm only a locally verified
supported category/subtype.

A fresh explicit complete-review approval is required before the next
real Smartsheet row is written.

Verify only PHI-safe outcomes such as classification labels, counts,
booleans, write success, attachment presence, and final status. Keep
patient data, OCR text, extracted values, source_text, filenames, local
document paths, payload values, and row IDs out of terminal/chat output.


------------------------------------------------------------
SERVICE-LINE CONFIDENCE REVIEW NOISE CLEANUP - 2026-08-12
------------------------------------------------------------

Feature:

Removed a redundant service-line review reason created solely when raw
model confidence of 1.0 was conservatively capped to 0.95.

The deterministic 1.0 to 0.95 confidence cap remains unchanged.

The cap itself no longer emits:

Service line N confidence requires deterministic verification

A service line still emits a low-confidence review action when its final
validated confidence is below the existing 0.85 threshold.

Unsupported or invalid service-line evidence continues to generate
targeted review reasons. No authorization safety rule was weakened.

Files changed:

- src/services/evidence_validation_service.py
- tests/test_evidence_validation_service.py

Focused test:

- Evidence validation: 29 passed, 0 failed

Affected regressions:

- Review decision: 19 passed, 0 failed
- Review output service: 8 passed, 0 failed
- Review output integration: 7 passed, 0 failed
- Document-to-Smartsheet mapping integration: 9 passed, 0 failed

Combined automated result:

Passed: 72
Failed: 0

Test classification:

Synthetic deterministic only.

External boundaries during this change:

- Microsoft Graph not called.
- PaddleOCR not called.
- Ollama not called.
- Smartsheet external API not called.
- No new row was written.

PHI handling:

- Synthetic test values only.
- No OCR text or source_text was printed.
- No patient values, filenames, local paths, Smartsheet payloads, or row
  IDs were printed.
- Review-reason behavior remains generic and PHI-safe.

Related controlled real verification completed before this cleanup:

- One real mailbox document completed successfully.
- Human-confirmed classification correction was submitted.
- Complete-review approval was explicitly given.
- Approved: 1
- Written: 1
- Failed: 0
- Success: True
- Status: completed
- The written row was manually confirmed to use the human-confirmed
  renewal subtype.
- The row attachment was manually confirmed present.
- No row values, patient data, OCR text, source_text, filename, path,
  payload value, or row ID was copied into tracker output.

Limitation:

The remaining service-line review reasons have not yet been changed.
Unsupported date, status, modifier, low-confidence, and unresolved
authorization-quantity conditions remain active where deterministic
evidence does not support them.

Exact next starting point:

Inspect the current service-line date, status, modifier, and source_text
validation contracts together with the Ollama service-line extraction
prompt and tests.

Determine whether the remaining review reasons reflect genuinely
unsupported evidence or whether service-line source evidence is too
narrow to support otherwise valid extracted values.

Do not weaken evidence requirements, infer modifier ownership, or
interpret authorization quantity meaning without deterministic support.


------------------------------------------------------------
SOURCE-AGNOSTIC AUTHORIZATION AND SERVICE-LINE EVIDENCE - 2026-08-12
------------------------------------------------------------

Feature:

Completed the source-agnostic authorization naming cleanup and strengthened
the Ollama service-line extraction evidence contract.

Authorization naming cleanup:

- Removed payer-specific identifier guidance from the production Ollama
  extraction prompt.
- Authorization identifier labels are interpreted using surrounding
  label-value relationships and document evidence.
- Identifier meaning must not be inferred from payer, sender, filename,
  or template.
- Renamed the single-document authorization test runners from
  payer-specific names to document-purpose names.
- Production provider and renamed authorization runners contain no
  payer-specific Molina references.
- Remaining Molina references in the focused prompt test are intentional
  negative assertions verifying payer-specific prompt language is absent.

Service-line extraction guidance:

- Every non-null service-line field must be directly supported by the
  same service-line source evidence.
- service_code, modifier, quantity, dates, and status must each be
  supported by that row's evidence before being returned.
- A value appearing elsewhere in the document is not sufficient evidence
  for a service-line field.
- The stronger prompt guidance remains aligned with the existing
  deterministic evidence-validation contract.
- No service-line values from separate Ollama attempts are merged.

Files changed:

- AGENTS.md
- scripts/test_molina_document.py removed
- scripts/test_molina_timing.py removed
- scripts/test_authorization_document.py added
- scripts/test_authorization_timing.py added
- src/ai/llm/providers/ollama_provider.py
- tests/test_ollama_service_lines.py
- update_project_tracker.py

Compilation:

Modified provider, focused test, and renamed authorization runners compiled
successfully.

Focused Ollama service-line regression:

Passed: 19
Failed: 0

Affected evidence-validation regression:

Passed: 29
Failed: 0

Affected document-processor regression:

Passed: 16
Failed: 0

Combined automated result:

Passed: 64
Failed: 0

Test classification:

Synthetic deterministic.

The renamed real-document authorization runners were compiled but were not
executed during this checkpoint.

External boundaries during these regression tests:

- Microsoft Graph not called.
- PaddleOCR not called.
- Ollama not called.
- Smartsheet external API not called.
- No real Smartsheet row was written.

PHI handling:

- Synthetic deterministic test data only.
- No OCR text was printed or copied into tracker output.
- No patient data or extracted patient values were printed.
- No source_text containing PHI was printed.
- No identifying protected filename or local patient path was printed.
- No Smartsheet payload values or row IDs were printed.
- Rename verification used only safe source-code paths and reference
  counts.

Limitations:

- The strengthened service-line prompt has not yet been exercised through
  a new real local Ollama extraction run.
- The renamed authorization runners have not yet been executed after the
  naming cleanup.
- Real cached OCR behavior has not yet been reverified against the stronger
  same-row evidence prompt.
- Quantity meaning and modifier ownership remain conservative and require
  deterministic support or human review.
- No new real Smartsheet write was performed or authorized during this
  checkpoint.

Exact next starting point:

Run one controlled local authorization test through the renamed
single-document harness using real cached OCR and real local Ollama.

Keep OCR text, patient data, extracted values, source_text, protected
filenames, local patient paths, credentials, payload values, and row IDs
out of terminal and chat output.

Verify only PHI-safe counts, booleans, attempts, confidence metadata,
review status/reason counts, selected attempt, reconciliation state, and
success/failure.

Do not perform a real Smartsheet write without a fresh explicit
complete-review approval.


------------------------------------------------------------
PROJECT MEMORY AND BEGIN/END DAY CONTINUITY - 2026-08-13
------------------------------------------------------------

Feature:

Implemented a durable project continuity layer so work can resume from a
compact, committed project memory rather than relying on conversation
history alone.

Project memory:

Added `PROJECT_MEMORY.md` as the current-state continuity source.

The file records:

- source-of-truth ordering
- platform goal
- current architecture
- safety invariants
- implemented capabilities
- recent tested baseline
- known limitations and open questions
- Begin Day procedure
- End of Day procedure
- exactly one authoritative CURRENT NEXT START

The file explicitly prohibits PHI, OCR text, patient/member data,
source_text, protected filenames and paths, credentials, secrets, tokens,
Smartsheet payload values, and Smartsheet row IDs.

AGENTS continuity:

Replaced the volatile Current Work section in `AGENTS.md` with durable
Project Continuity rules.

`AGENTS.md` now defines:

- `PROJECT_MEMORY.md` as the current continuity layer
- Begin Day behavior
- End of Day behavior
- preservation and reconciliation of uncommitted work
- Git/local-state verification before continuing
- prohibition on automatically executing PHI-sensitive operations during
  Begin Day

Source-of-truth responsibilities are now separated:

- Git committed state: authoritative committed code
- confirmed local uncommitted state: work not yet committed
- AGENTS.md: durable repository and execution rules
- PROJECT_MEMORY.md: current project state and next start
- update_project_tracker.py: detailed historical checkpoints and project
  task synchronization

Continuity validation:

Passed: 14
Failed: 0

Validated behavior:

- AGENTS contains Project Continuity
- stale Current Work section removed
- AGENTS references PROJECT_MEMORY
- Begin Day procedure present
- End of Day procedure present
- PROJECT_MEMORY purpose present
- source-of-truth order present
- tested baseline present
- limitations section present
- Begin Day procedure present in memory
- End of Day procedure present in memory
- exactly one CURRENT NEXT START exists
- current 19/29/16 regression baseline preserved
- fresh explicit complete-review approval requirement preserved

Test classification:

Synthetic deterministic repository-text validation.

External boundaries:

- Microsoft Graph not called.
- PaddleOCR not called.
- Ollama not called.
- Smartsheet external API not called.
- No real patient document was accessed.
- No real Smartsheet row was written.

PHI handling:

- No patient data was used.
- No OCR text was used.
- No source_text was used.
- No protected patient filename or local patient path was used.
- No credentials, secrets, tokens, payload values, or row IDs were used.
- Validation inspected repository instruction and continuity text only.

Files changed:

- AGENTS.md
- PROJECT_MEMORY.md
- update_project_tracker.py

Limitations:

- PROJECT_MEMORY.md must be maintained whenever current project state,
  tested baseline, limitations, or CURRENT NEXT START changes.
- Begin Day still requires inspection of actual Git and local state rather
  than trusting the memory file blindly.
- Git remains authoritative for committed code.
- The project tracker remains the detailed historical record.
- The continuity system does not itself execute local-only commands or
  PHI-sensitive operations.

Exact next starting point:

Use the new Begin Day procedure to rehydrate project state, then run one
controlled local authorization test through the renamed single-document
authorization harness.

Use real cached OCR and real local Ollama while keeping PHI-bearing data
local.

Report only PHI-safe counts, booleans, attempts, confidence metadata,
review status and reason counts, selected attempt, reconciliation state,
and success/failure.

Do not perform a real Smartsheet write without a fresh explicit
complete-review approval.


------------------------------------------------------------
CODEX / WORK WEEKLY CAPACITY CONTINUITY - 2026-08-13
------------------------------------------------------------

Feature:

Added Codex/Work weekly-capacity planning to durable project memory.

Behavior:

- Codex and Work share the weekly usage limit.
- The exact reset timestamp shown in Codex and Work Analytics is
  authoritative when known.
- The currently known reset is August 18, 2026 at 1:26 PM local time.
- The known timestamp is current-cycle information and must be replaced
  after reset when a new authoritative timestamp is observed.
- Begin Day considers both remaining useful capacity and time until reset.
- Appropriate Codex work includes workspace inspection, complex
  multi-file edits, debugging, refactoring, caller/reference analysis,
  and architecture review.
- Worthwhile capacity should be used before expiration when it materially
  improves the work.
- Codex must never be used merely to consume credits.
- Codex must preserve uncommitted work, follow AGENTS.md, remain PHI-safe,
  and respect local PHI/OCR/Ollama boundaries.

Files changed:

- PROJECT_MEMORY.md
- update_project_tracker.py

Test classification:

Synthetic deterministic repository-text validation.

External boundaries:

- Microsoft Graph not called.
- PaddleOCR not called.
- Ollama not called.
- Smartsheet not called.
- No patient document accessed.

PHI handling:

No PHI, OCR text, source_text, protected patient filename/path,
credentials, secrets, tokens, payload values, or row IDs were used.

Limitations:

- Usage balance and reset timestamp are not continuously monitored.
- A new reset timestamp must be observed from Codex and Work Analytics
  after the current reset cycle.
- Codex selection remains task-driven rather than automatic.

Exact next starting point:

Continue from the authoritative CURRENT NEXT START in PROJECT_MEMORY.md.

During Begin Day, also consider worthwhile Codex work against the current
known reset timestamp.


------------------------------------------------------------
CONTROLLED AUTHORIZATION RETRY AND HARNESS CONTRACT - 2026-08-14
------------------------------------------------------------

Run Type:

Controlled Authorization Regression

Retry fix:

- Authorization raw and validated completeness checks now request the
  existing single controlled retry when no supported service-line rows
  remain, even when top-level service-code fields are also empty.
- Authorization-only scope, independent candidate validation, no candidate
  merging, deterministic selection, and attempt-1 tie behavior remain
  unchanged.
- No payer, service code, modifier, quantity, date, filename, or source
  conclusion was added to production retry logic.

Synthetic validation:

- Authorization harness contract: 5 passed, 0 failed.
- Document processor: 17 passed, 0 failed.
- Evidence validation: 29 passed, 0 failed.
- Ollama service lines: 19 passed, 0 failed.
- Review-output service: 8 passed, 0 failed.
- Review-output integration: 7 passed, 0 failed.
- Combined synthetic result: 85 passed, 0 failed.
- All modified Python files compiled successfully.

Real cached-OCR/local-Ollama verification:

- Classification: authorization.
- Extraction attempt count: 2.
- Raw retry required: False.
- Validated retry required: True.
- Retry triggered: True.
- Selected attempt: 2.
- Final service-line count: 2.
- Supported service-code and quantity evidence remained on both rows.
- A modifier remained only where row evidence supported it.
- Unsupported row dates and statuses were cleared.
- Unsupported authorization status was cleared.
- Human review required: True.
- Review output remained attached and preserved final review state.
- Microsoft Graph and Smartsheet were not called.
- No external AI was used.

Semantic harness correction:

The previous harness required authorization status and service-line dates
and statuses to remain populated even when deterministic evidence did not
support them. It also always required the modifier-relationship action.

The corrected contract now verifies that supported values remain supported,
unsupported values are cleared with validation actions, modifier-relationship
review is required only when a supported top-level modifier remains unresolved
across validated rows, human review remains required, review output preserves
final state, and retry metadata matches the controlled checkpoint.

PHI handling:

- Real processing remained local and PHI output was suppressed.
- No OCR text, source_text, patient values, protected filenames or paths,
  credentials, tokens, Smartsheet payload values, or row IDs were recorded.
- All harness-correction tests used synthetic deterministic data only.

Codex / Work Analytics:

- Weekly usage remaining observed: 99%.
- Authoritative reset: August 20, 2026 at 9:53 AM local time.
- Source: Codex and Work Analytics.
- This observation supersedes the prior August 18 reset value.
- The reason for the platform timestamp change is unknown and was not
  inferred.

Limitations:

- The corrected semantic harness has not yet been rerun against the
  controlled real cached-OCR/local-Ollama regression.
- Quantity meaning remains conservative and requires deterministic support
  or human review.
- No real Smartsheet write was performed or authorized.

Exact next starting point:

Run one controlled local authorization test through the corrected
single-document harness. Verify only PHI-safe retry metadata, supported-value
presence, cleared-value evidence flags, review state, reason counts, selected
attempt, service-line count, and semantic success/failure.

Do not expose PHI-bearing data and do not perform a real Smartsheet write
without fresh explicit complete-review approval.


------------------------------------------------------------
CONTROLLED AUTHORIZATION REGRESSION FINAL PASS - 2026-08-14
------------------------------------------------------------

Run Type:

Controlled Authorization Regression

Verified real result:

- Semantic regression: PASSED.
- Passed: 1.
- Failed: 0.
- Real cached OCR and real local Ollama were used locally.
- Extraction attempt count: 2.
- Retry triggered: True.
- Raw retry required: False.
- Validated retry required: True.
- Selected attempt: 2.
- Final service-line count: 2.
- Supported service-code and quantity structure remained preserved.
- Unsupported authorization and service-line values remained cleared with
  validation and review reasons.
- Human review required: True.
- Review output remained attached and preserved final state.
- Raw OCR text and the local document path were excluded from review output.

External boundaries:

- Microsoft Graph was not called.
- Smartsheet was not called and no row was written.
- No external AI was used.
- PHI output remained suppressed.

Continuity:

- The retry fix is verified in real cached-OCR/local-Ollama execution.
- The corrected authorization harness is verified in the same controlled
  real execution.
- Weekly usage remaining remains the observed 99%.
- The authoritative Codex and Work Analytics reset remains August 20, 2026
  at 9:53 AM local time.
- This newer observation supersedes the historical August 18 value; the
  reason for the timestamp change is unknown and was not guessed.

Limitations:

- Authorization quantity meaning remains intentionally conservative when
  deterministic evidence is insufficient.
- Modifier ownership remains unresolved without row evidence.
- No real Smartsheet write was performed or authorized.

Exact next starting point:

Inspect the existing authorization service-line quantity-reconciliation
boundary, callers, and synthetic tests. Confirm supported quantities are
preserved only within one independently validated candidate and are never
interpreted as visits, sessions, equipment, approval, or sufficient
authorization.

Make a code change only if inspection demonstrates a concrete gap. Do not
invent quantity meaning without confirmed business requirements.


------------------------------------------------------------
AUTHORIZATION QUANTITY RECONCILIATION SAFETY CHECKPOINT - 2026-08-14
------------------------------------------------------------

Feature:

Inspected the authorization service-line quantity-reconciliation boundary
end to end across deterministic validation, independent extraction-candidate
selection, authorization business rules, review output, and reviewed
Smartsheet mapping.

Verified behavior:

- Reconciliation uses only supported quantities from one independently
  validated candidate.
- Separate extraction attempts are never merged and ties retain attempt 1.
- Missing or null top-level authorized units are not inferred.
- Unsupported row quantities are cleared and excluded from reconciliation.
- Supported quantities remain eligible when another row field is unresolved;
  conservative confidence and review actions are preserved.
- Approved visits remain separate and unchanged.
- Quantity is not interpreted as visits, sessions, equipment, recurring
  services, approval, or sufficient authorization.
- Authorization business rules continue to require human verification.
- Review output preserves validated quantity state, confidence, evidence, and
  review metadata without reinterpretation.
- Smartsheet mapping performs no quantity conversion or reinterpretation.
- No production code change was required.

Files changed:

- tests/test_document_processor.py
- tests/test_service_line_quantity_reconciliation.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Synthetic deterministic and mock validation:

- Service-line quantity reconciliation: 10 passed, 0 failed.
- Document processor: 18 passed, 0 failed.
- Evidence validation: 29 passed, 0 failed.
- Authorization quantity rules: 8 passed, 0 failed.
- Review-output service: 8 passed, 0 failed.
- Smartsheet review-mapping integration: 9 passed, 0 failed.
- Ollama prompt and schema guardrails: 19 passed, 0 failed.
- Combined: 101 passed, 0 failed.
- All modified Python test files compiled successfully.

External and PHI boundaries:

- No patient document or protected data was accessed.
- Microsoft Graph, PaddleOCR, Ollama, the reviewed-document Smartsheet
  workflow, and external AI were not called during inspection or regression
  testing.
- No OCR text, patient values, source evidence, protected filenames or paths,
  credentials, secrets, tokens, payload values, or row IDs were exposed.

Limitations:

- Quantity business meaning and final approval remain human-review decisions.
- Modifier ownership remains unresolved without row evidence.
- No real Smartsheet write was performed or authorized.

Codex / Work Analytics continuity:

- Weekly usage remaining remains the observed 99%.
- The authoritative reset remains August 20, 2026 at 9:53 AM local time.
- The reason for the reset timestamp change remains unknown and was not
  guessed.

Exact next starting point:

Inspect the existing Microsoft Graph authentication-error boundary in
src/graph/auth.py, its configuration, callers, and current synthetic tests.
Add dedicated mock regression coverage for invalid credentials, expired
secrets, missing permissions, Graph authorization failures, and sanitized
error handling. Make a production change only if a failing synthetic
regression demonstrates a concrete gap. Do not make a live Graph request or
use real credentials or tokens.


------------------------------------------------------------
MICROSOFT GRAPH SANITIZED FAILURE BOUNDARY - 2026-08-14
------------------------------------------------------------

Feature:

Inspected and corrected the Microsoft Graph configuration, authentication,
request, authorization, caller, and diagnostic-entry-point failure boundary.

Confirmed pre-fix gap:

- MSAL/provider authentication descriptions were included in raised errors.
- Raw MSAL construction and token-acquisition exceptions could escape.
- Raw Graph 401/403, request, and response-decoding exceptions could escape.
- Uncaught diagnostic entry points could display those raw exceptions.

Implemented behavior:

- Added application-owned sanitized categories: configuration_error,
  authentication_failed, authorization_failed, and graph_request_failed.
- Missing configuration reports missing environment-variable names only and
  never reports values.
- Provider descriptions, response bodies, credentials, secrets, tokens, and
  authorization headers are not included in sanitized error output.
- Blank or failed token acquisition stops before any Graph request.
- HTTP 401 and 403 responses map to authorization_failed.
- Other request and response-decoding failures map to graph_request_failed.
- Successful token acquisition still returns the token internally without
  printing or logging it.
- Sanitized failures retain no provider exception cause or context.
- Existing RuntimeError compatibility is preserved through subclasses.

Files changed:

- src/graph/auth.py
- src/graph/client.py
- src/graph/config.py
- src/graph/errors.py
- tests/test_graph_security_boundary.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Synthetic deterministic and mock validation:

- Initial red regression: 1 passed, 11 failed.
- Final Graph security boundary: 17 passed, 0 failed.
- Ten affected mailbox suites: 108 passed, 0 failed.
- Combined final result: 125 passed, 0 failed.
- All five modified Graph/security Python files compiled successfully.

External and PHI boundaries:

- Microsoft Graph and MSAL were mocked only.
- No real credentials or .env values were read or printed.
- No live Graph, patient-document, PaddleOCR, Ollama, reviewed-document
  Smartsheet, or external-AI operation occurred.
- No protected data, provider detail, credential, secret, token, response
  payload, OCR text, protected filename/path, or row ID was exposed.

Limitations:

- Verification is mock-only; no live negative authentication or authorization
  request was performed.
- Legacy Graph/mailbox diagnostic scripts still contain direct output of
  message metadata, identifiers, paths, OCR text, or extracted values and must
  not be run against live data before their output boundary is corrected.

Codex / Work Analytics continuity:

- Weekly usage remaining remains the observed 99%.
- The authoritative reset remains August 20, 2026 at 9:53 AM local time.
- The reason for the reset timestamp change remains unknown and was not
  guessed.

Exact next starting point:

Inspect scripts/test_graph_connection.py, scripts/test_graph_attachments.py,
scripts/check_graph_read_status.py, and scripts/test_mailbox_processor.py.
Add mocked stdout regressions for their current message metadata, identifier,
path, OCR-text, and extracted-value exposure, then make the smallest changes
needed to restrict output to PHI-safe counts, booleans, timings, confidence
metadata, and sanitized statuses. Do not run a live mailbox or real document.


------------------------------------------------------------
AUTOMATIC SMARTSHEET PRODUCTION FLOW CLARIFICATION - 2026-08-14
------------------------------------------------------------

Authoritative business requirement:

- Normal production processing automatically creates or populates the
  intentionally mapped Smartsheet row after deterministic validation and
  business rules.
- Human review is a downstream exception workflow and is not a write gate.
- Review-required rows must preserve supported values, keep unsupported or
  unreliable values null/unknown, and carry review status and reasons.
- The existing configured review thresholds remain unchanged; no new
  threshold was invented.
- Smartsheet is an approved production destination for intentionally mapped
  PHI and full document content.
- PHI or document content may reach Smartsheet only through an explicit
  production mapping/write path. Internal diagnostics, credentials, tokens,
  local paths, cache metadata, and unrelated internal fields remain excluded.

Durable continuity changes:

- AGENTS.md now defines automatic Smartsheet population before conditional
  downstream human review.
- PROJECT_MEMORY.md records the clarified architecture and implementation
  gap and contains one authoritative next start.
- Earlier tracker entries describing complete-review approval as write
  authority remain historical; this checkpoint supersedes that architecture
  decision.

Inspected implementation gap:

- SmartsheetReviewSubmissionService requires a successful explicit approval
  result before mapping or writing.
- CompleteReviewSmartsheetWorkflowService invokes an approval interaction
  before submission.
- Mailbox and full-review orchestration propagate explicit approval state.
- SmartsheetReviewRowMappingService blocks review-required rows unless a
  narrow approval exception applies and currently prohibits source_text.
- Existing focused tests encode these approval-gated assumptions.
- Correcting this coherently spans several active interfaces, so no broad
  production refactor was made during the durable-rule reconciliation.

External and PHI boundaries:

- Eleven focused Smartsheet/review-boundary suites passed: 120 passed,
  0 failed.
- Tests used synthetic deterministic or mocked data only and documented the
  current approval-gated contracts that are now obsolete.
- update_project_tracker.py compiled successfully.
- No real Smartsheet write is performed for this checkpoint.
- Microsoft Graph, PaddleOCR, Ollama, patient documents, and external AI are
  not called.
- No protected data, payload values, credentials, tokens, filenames, paths,
  OCR text, or source evidence is exposed.

Exact next starting point:

Add focused synthetic red regressions for automatic Smartsheet population of
both verified and review-required null-safe rows, then reconcile row mapping,
submission, complete-review workflow, mailbox orchestration, command options,
and callers as the smallest coherent interface change. Preserve review
status/reasons, configured thresholds, deterministic validation, explicit
destination mapping, and all no-inference rules. Use mocked Smartsheet only.
After this production boundary is green, resume the deferred legacy
Graph/mailbox diagnostic-output hardening task.


------------------------------------------------------------
AUTOMATIC SMARTSHEET WRITE BOUNDARY IMPLEMENTED - 2026-08-14
------------------------------------------------------------

Implemented production boundary:

- Deterministic validation and business rules continue to precede submission.
- Normal mailbox processing now automatically submits the intentionally
  mapped row without a complete-review approval result or approval flag.
- Review-required rows still write with review status and reasons; human
  review is downstream exception handling.
- Missing and unsupported values remain null or omitted under the existing
  mapping rules.
- Required missing destination data and destination-validation failures still
  prevent the writer call.
- Classification confirmation remains downstream feedback, not a write
  credential.
- The command path no longer requires an approval option.
- The full document continues through the existing explicit attachment-upload
  path.
- OCR text and source_text have no explicit Smartsheet destination and remain
  unmapped.
- No new columns or mappings were introduced, and document/review/internal
  objects are not serialized wholesale.

Regression evidence:

- Focused red result for obsolete approval gating: 5 passed, 8 failed.
- Final affected regression baseline: 286 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- No PHI or protected data was accessed.
- No real Microsoft Graph, PaddleOCR, Ollama, patient-document, Smartsheet
  production-write, or external-AI operation occurred.

Exact next starting point:

Resume the deferred legacy Graph/mailbox diagnostic stdout hardening for
scripts/test_graph_connection.py, scripts/test_graph_attachments.py,
scripts/check_graph_read_status.py, and scripts/test_mailbox_processor.py.
Use synthetic/mock stdout regressions first. Remove protected subjects, sender
addresses, message IDs, paths, raw OCR, extracted values, and raw error text.
Retain only PHI-safe counts, booleans, confidence/status/timing metadata. Do
not change mailbox or document-processing behavior. Do not run live Graph,
mailbox, or documents.


------------------------------------------------------------
LEGACY GRAPH/MAILBOX DIAGNOSTIC STDOUT HARDENED - 2026-08-14
------------------------------------------------------------

Work completed:

- Hardened scripts/test_graph_connection.py,
  scripts/test_graph_attachments.py, scripts/check_graph_read_status.py,
  and scripts/test_mailbox_processor.py.
- Added tests/test_legacy_graph_mailbox_diagnostic_stdout.py with synthetic
  marker-based stdout and sanitized-failure coverage.
- Removed subjects, sender addresses, received identifying metadata, message
  IDs, filenames, paths, raw OCR/document text, extracted values, raw mailbox
  errors, and raw provider diagnostics from covered script output.
- Confirmed source_text and field-evidence values remain excluded.
- Retained PHI-safe counts, booleans, safe sequence numbers, document/review
  status, confidence metadata, action/reason counts, and application-owned
  sanitized failure categories.
- No EmailService, AttachmentService, MailboxProcessor, mark-as-read,
  idempotency, document-processing, validation/business-rule, review, or
  automatic-Smartsheet behavior changed.

Regression evidence:

- Initial focused red result: 2 passed, 16 failed.
- Final focused stdout regression: 22 passed, 0 failed.
- Affected Graph/mailbox regressions: 121 passed, 0 failed.
- Combined: 143 passed, 0 failed.
- Compilation: 5 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- No protected stdout exposure remains in the covered paths.
- No PHI or protected data was accessed.
- No live Microsoft Graph, mailbox, attachment, PaddleOCR, Ollama,
  patient-document, production-Smartsheet, or external-AI operation occurred.

Limitation:

- Verification is mock-only; the hardened diagnostics were not run against a
  live mailbox.

Exact next starting point:

Inspect the existing automatic Smartsheet row-write and attachment-upload
boundary for the previously tracked partial-success and retry/idempotency
limitation. Use focused mocked red regressions first for a successful row
creation followed by attachment failure and for a subsequent retry. Determine
the smallest safe correction that prevents duplicate rows or explicitly
preserves partial-success state without changing deterministic validation,
business rules, automatic writing, downstream review, or explicit destination
mappings. Do not run a real Smartsheet write, Graph, OCR, Ollama, mailbox, or
patient document.


------------------------------------------------------------
SMARTSHEET PARTIAL-SUCCESS RETRY SAFETY - 2026-08-14
------------------------------------------------------------

Work completed:

- Updated src/services/smartsheet_review_submission_service.py to preserve a
  created-row/failed-attachment result as written=True and success=False.
- Added an explicit retry operation that requires the prior PHI-safe
  submission result, blocks retry when that result confirms an existing row,
  and permits retry only when no row was created.
- Updated src/services/mailbox_complete_review_smartsheet_service.py to count
  the existing row, retain the failure, and report
  completed_with_partial_success.
- Added tests/test_smartsheet_partial_success_retry.py with mocked first-write,
  attachment-failure, retry, mailbox-summary, orchestration, destination,
  optional-attachment, review-required, and output-suppression coverage.
- No external row identifier is stored or exposed by the retry contract.

Regression evidence:

- Initial focused red result: 6 passed, 5 failed.
- Final focused partial-success/retry regression: 12 passed, 0 failed.
- Affected Smartsheet/mailbox regressions: 123 passed, 0 failed.
- Combined: 135 passed, 0 failed.
- Compilation: 3 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- Normal first-attempt automatic writes, destination validation,
  review-required writes, optional attachment handling, mapping,
  deterministic validation, business rules, review thresholds, mailbox
  mark-as-read/idempotency, and no-inference protections remained unchanged.
- No result representation, status, stdout, or stderr exposed external row
  identifiers, payload values, credentials, tokens, PHI, filenames, paths, or
  provider details.
- No PHI or protected data was accessed.
- No real Smartsheet, Microsoft Graph, mailbox, attachment, PaddleOCR, Ollama,
  patient-document, or external-AI operation occurred.

Limitation:

- Attachment upload cannot resume against an already-created row because no
  safe persisted row reference exists. Explicit retry is safe only while the
  prior PHI-safe submission result remains available. After process-state loss,
  manual resubmission cannot be safely deduplicated and must not be attempted
  blindly.

Exact next starting point:

Prepare the smallest PHI-safe controlled real-document training/evaluation
cycle without fine-tuning. First inspect the existing single-document/local
test harnesses and classification-feedback/error-capture boundaries. Define a
controlled procedure and safe result contract for local real documents using
cached OCR and local Ollama only when explicitly authorized. Return only
PHI-safe metadata to ChatGPT/Codex. Do not automatically run patient documents
during preparation, and do not perform a live Smartsheet write, Graph request,
mailbox operation, external-AI call, or model fine-tune.


------------------------------------------------------------
GENERIC PHI-SAFE LOCAL EVALUATOR - 2026-08-19
------------------------------------------------------------

Work completed:

- Added scripts/evaluate_local_document.py as an explicit operator-controlled
  numeric-selection entry point with required PHI-safe Run Type, cached-OCR/
  protected-document access authorization, and local-Ollama authorization.
- Added src/services/local_document_evaluation_service.py with an explicit
  aggregate-only result contract, allowlisted category/status metadata,
  deterministic counts, safe timing fields, nested stdout/stderr suppression,
  and application-owned failure categories.
- Added an optional synchronous LocalProtectedReviewConsumer protocol for a
  local-only in-memory protected-document handoff. The protected Document is
  not present in result objects and is not serialized, logged, or persisted.
- Added src/ai/ocr/errors.py and opt-in OCR cache-only propagation through
  OCRService, DocumentProcessor, and PaddleOCRProvider.
- Cache-only misses stop with a sanitized application error before PaddleOCR
  prediction. Existing callers retain the default non-cache-only behavior.
- Added tests/test_local_document_evaluation_service.py and
  tests/test_ocr_cache_only.py with synthetic authorization, output-
  suppression, sanitized-error, aggregate-contract, cache-hit/miss, caller-
  compatibility, and CLI-preflight coverage.
- The fixture-specific authorization regression remained unchanged.

Regression evidence:

- Initial focused red result: 1 passed, 18 failed.
- Final focused evaluator/cache-only result: 21 passed, 0 failed.
- Affected processor, OCR, review, classification-feedback, authorization-
  harness, and automatic-Smartsheet regressions: 108 passed, 0 failed.
- Combined: 129 passed, 0 failed.
- Compilation: 8 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- One combined in-process run encountered a Windows temporary-directory
  PermissionError in the existing concurrent classification-feedback locking
  suite. It passed 4/0 in isolation; all other affected tests passed 104/0 in
  a separate process. The concurrency test was not weakened or removed.
- No PHI or protected data was accessed.
- No patient document, PaddleOCR prediction, local Ollama request, Microsoft
  Graph, mailbox, production Smartsheet workflow, or external AI ran.

Production compatibility and PHI boundary:

- Existing DocumentProcessor and OCRService callers omit the new opt-in flag,
  so normal production OCR can still execute and mailbox processing remains
  unchanged.
- Deterministic validation, business rules, review thresholds, extraction
  retry/candidate selection, classification feedback, and automatic
  Smartsheet submission were not changed.
- Evaluator result, repr, status, stdout, and stderr exclude filenames, paths,
  fingerprints, OCR/document text, extracted and service-line values, source
  evidence, protected review objects, patient/provider details, authorization
  values, credentials, tokens, provider diagnostics, destination payloads,
  and row identifiers.

Limitation:

- A concrete approved local protected-review UI/consumer remains required
  before the first controlled real-document training/evaluation run. The
  current protocol defines only the synchronous in-memory handoff.

Exact next starting point:

Implement the smallest concrete local protected-review UI/consumer required
before the first controlled real-document training run. Keep it local-only;
display protected extracted values only inside the approved local UI; never
print, log, persist without approval, or expose those values to ChatGPT/Codex;
allow local comparison with the source document; preserve the aggregate-only
evaluator result; leave production paths unchanged; and do not run a real
patient document yet.


------------------------------------------------------------
LOCAL PROTECTED-REVIEW UI IMPLEMENTED - 2026-08-19
------------------------------------------------------------

Work completed:

- Added src/ui/local_protected_review.py with an opt-in synchronous Tkinter
  review window for local protected comparison.
- The window provides an OS-default source-document action without displaying
  the path, plus overview, extracted-field/evidence, service-line, and
  validation/business-rule/review sections with Done and normal-close actions.
- Added application-owned protected_review_unavailable and
  protected_review_failed categories in
  src/services/local_protected_review_errors.py.
- Integrated the concrete consumer into scripts/evaluate_local_document.py
  through the explicit --protected-review option.
- Extended the aggregate evaluator contract only with PHI-safe requested,
  completed, and status metadata.
- Added tests/test_local_protected_review.py and extended the evaluator tests
  for local-only in-memory display, safe errors, output suppression, no
  persistence/clipboard operations, explicit CLI opt-in, and unchanged
  no-consumer behavior.

Regression and visual evidence:

- Initial synthetic red result: 0 passed, 8 failed.
- Final protected-review UI/evaluator result: 27 passed, 0 failed.
- Affected cache-only OCR, document-processor, review-output, automatic-
  Smartsheet, and mailbox-Smartsheet result: 62 passed, 0 failed.
- Combined: 89 passed, 0 failed.
- Compilation: 6 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- A real local Tkinter visual smoke test used only synthetic non-PHI values.
  Both windows rendered, all review sections were present, the injected Open
  action worked, and Done and normal-close actions exited successfully.
- The visual test created no extra output file, performed no clipboard write,
  emitted no synthetic protected marker to stdout/stderr, and took no
  screenshot.

Production compatibility and PHI boundary:

- DocumentProcessor/OCR behavior, validation, business rules, review
  decisions, extraction retry/candidate selection, Graph/mailbox, automatic
  Smartsheet submission, classification feedback, and the fixture-specific
  authorization harness remain unchanged.
- UI contents remain local-only and in memory and are excluded from evaluator
  serialization, logs, persistence, and external responses.
- No PHI or protected data was accessed.
- No patient document, real PaddleOCR, local Ollama request, Microsoft Graph,
  mailbox, production Smartsheet workflow, or external AI ran.

Exact next starting point:

Run the first controlled real-document training/evaluation cycle. Require an
explicit operator-selected numeric document index, explicit PHI-safe Run Type,
explicit protected local document/cache-access authorization, and explicit
local-Ollama authorization. Prefer cached OCR for the first run and use
LocalProtectedReviewConsumer for the operator's local protected comparison.
Do not use Graph/mailbox, production Smartsheet, or external AI. Return only an
aggregate PHI-safe summary to ChatGPT/Codex and do not expose the filename/path,
OCR text, extracted values, source_text, or evidence outside the local
protected UI.


------------------------------------------------------------
GRAPH ATTACHMENT ENUMERATION DIAGNOSTIC CHECKPOINT - 2026-08-19
------------------------------------------------------------

Work completed:

- Inspected the production mailbox preflight, email service, attachment
  service, Graph client, sanitized error boundary, and focused callers/tests.
- Confirmed the production AttachmentService attachment-listing GET endpoint,
  method, parameters, and response handling were not defective and remain
  unchanged.
- Identified the earlier graph_request_failed result as incorrect PowerShell
  interpolation of the $select query key in a custom read-only probe rather
  than a production endpoint failure.
- Added allowlisted PHI-safe Graph request diagnostic metadata for operation
  category, HTTP status, response presence, coarse content type, and failure
  kind. Raw provider errors, identifiers, request URLs, response bodies,
  credentials, and tokens remain excluded.
- Added focused synthetic attachment-enumeration and sanitization regressions.

Files:

- src/graph/attachment_service.py
- src/graph/client.py
- src/graph/email_service.py
- src/graph/errors.py
- tests/test_graph_attachment_enumeration.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Initial focused red: 0 passed, 4 failed.
- Expanded focused red: 2 passed, 2 failed.
- Focused final: 6 passed, 0 failed.
- Affected Graph/mailbox regressions: 52 passed, 0 failed.
- Combined: 58 passed, 0 failed.
- Compilation: 5 changed Python files passed.
- Classification: synthetic deterministic/mock.
- No PHI or protected data was accessed by tests.
- No live Graph, mailbox, OCR, Ollama, Smartsheet, patient-document, or external
  AI operation was performed by tests.
- An approved live read-only production-service preflight found exactly one
  unread candidate and exactly one processable attachment.
- The live preflight performed no attachment download, document processing,
  mailbox mutation, OCR, Ollama, or Smartsheet write.

Limitation:

- The first true production-path execution has not yet run; the successful live
  check was read-only preflight only.

Exact next starting point:

Run the first true end-to-end production-path test against the single verified
unread/processable mailbox item.


------------------------------------------------------------
FIRST PRODUCTION END-TO-END CHECKPOINT - 2026-08-19
------------------------------------------------------------

Production milestone:

- Exactly one intended mailbox message completed the production path.
- Microsoft Graph retrieval and attachment download passed.
- Real local OCR, classification, and local Ollama processing passed.
- Deterministic validation and business rules completed.
- Intentional Smartsheet mapping and destination validation passed.
- The Smartsheet row write and document attachment upload passed with no
  partial success.
- Mailbox handled/read state and the durable idempotency marker completed.
- Total elapsed time was 542.992 seconds.
- Classification: real production integration using local AI; external AI was
  not used.

PHI boundary:

- No PHI, protected filename, extracted value, source_text, payload content,
  external row identifier, local protected path, credential, or token is
  recorded in this checkpoint.

Exact next starting point:

Implement deterministic human-readable Smartsheet AI Review Reasons while
preserving full technical reasons internally, then add the inspected,
synthetic-tested reference-table and filename-component architecture. Do not
run live Graph/mailbox, patient-document, OCR, Ollama, production Smartsheet,
or external-AI operations. Do not commit the new implementation checkpoint.


------------------------------------------------------------
REVIEW SUMMARY, CONFIDENCE, AND REFERENCE ARCHITECTURE - 2026-08-19
------------------------------------------------------------

Work completed:

- Added deterministic staff-friendly Smartsheet review-reason summaries while
  preserving the complete technical reason list in ReviewOutput.
- Added explicit confidence-availability tracking so unavailable confidence is
  not converted to numeric zero.
- Added missing/not-extracted and unsupported/cleared confidence statuses only
  for confirmed text-capable destination columns. Numeric-only destinations
  never receive status text.
- Added validated standard-library XLSX loading for PAYOR LISTING and SERVICES
  LISTING plus optional future DOCUMENT TYPES support.
- Added exact composite-key lookups, safe rejection of ambiguous or malformed
  mappings, an injectable Graph/SharePoint metadata/download boundary, and an
  ignored version-aware last-known-good cache.
- Added an explicit-policy filename-component builder without connecting it to
  production attachment naming.

Verification:

- Confidence regression: 5 passed, 0 failed.
- Focused configuration, policy, review-output, and mapping regressions:
  61 passed, 0 failed.
- Affected processing, validation, review, Smartsheet, and mailbox
  regressions: 223 passed, 0 failed.
- Compilation: 20 modified Python files passed.
- git diff --check passed.
- Classification: synthetic deterministic and mock.
- No live Graph, mailbox, patient document, OCR, Ollama, production Smartsheet
  write, or external AI operation occurred.

Safety and limitations:

- Review thresholds, validation, business rules, automatic Smartsheet write
  sequencing, and the existing production attachment naming path are
  unchanged.
- Reference lookup failures never guess, and the cache remains ignored.
- No real reference workbook, PHI, protected filename, source evidence,
  payload, external identifier, credential, token, cache, model, patient file,
  or temporary file is included.
- Final filename rules, authoritative SharePoint source configuration, and the
  production filename integration point remain unresolved.

Exact next starting point:

Inspect every actual project-tracker task currently Not Started or In Progress
and reconcile it against committed code, tests, continuity, tracker history,
and Git evidence. Change only evidence-supported statuses, add the durable
tracker-reconciliation rule, and leave uncertain or future work unchanged.


------------------------------------------------------------
PROJECT TRACKER WBS RECONCILIATION - 2026-08-19
------------------------------------------------------------

Work completed:

- Read all 75 actual project-tracker tasks and inspected every one of the 33
  tasks currently Not Started or In Progress.
- Compared each task with committed source, committed tests, project memory,
  tracker checkpoint history, and Git history.
- Advanced 16 statuses where committed evidence was sufficient.
- Left 17 statuses unchanged where requirements, approval, accuracy
  benchmarking, user acceptance, go-live, or hypercare evidence was
  incomplete or absent.
- Added a durable repository rule requiring affected WBS/task reconciliation
  after meaningful tested work without inferring completion.
- Added synthetic repository-text validation for exact intended task names and
  statuses, unchanged uncertain tasks, the durable rule, and a single current
  next start.

Safety:

- Tracker output and continuity contain task names, statuses, counts, and
  PHI-safe implementation summaries only.
- No row identifiers, tracker payload values, credentials, tokens, PHI, or
  protected data are recorded.

Exact next starting point:

Resolve the remaining filename business rules and establish the authoritative
SharePoint reference-workbook drive/item configuration before wiring
reference-driven filename generation into production. Confirm person-name
ordering, service-token requirements, separators, date source, timestamp
rules, and the definitive INBOUND RENEW definition/token without guessing.


------------------------------------------------------------
DETERMINISTIC FILENAME POLICY CHECKPOINT - 2026-08-20
------------------------------------------------------------

Work completed:

- Added a deterministic filename policy using confirmed LAST FIRST
  MIDDLE/INITIAL person order, underscore-separated major components, optional
  service and form dimensions, AUTH INIT for supported initial authorization,
  2067 form/workflow coexistence, MMDDYY single dates, MMDDYY-MMDDYY supported
  ranges, no timestamp, and PDF extension preservation.
- Required reference-derived, unambiguous payer and applicable service tokens.
  Unsupported or non-naming-relevant service components are omitted; relevant
  unresolved lookups block naming without guessing.
- Kept renewal naming blocked because the final INBOUND RENEW token remains
  unresolved, and kept ambiguous state/notice date ownership blocked.
- Added an explicit guarded attachment boundary. Normal production callers do
  not supply a filename policy and retain the existing fingerprint filename.
  An explicitly supplied incomplete policy falls back safely and returns a
  PHI-safe naming-review status.
- Hid generated filenames and temporary paths from policy, builder, and
  attachment-preparation result representations.
- Established the local Graph reference configuration contract using
  GRAPH_REFERENCE_DRIVE_ID and GRAPH_REFERENCE_ITEM_ID, with eTag-preferred
  versioning, lastModifiedDateTime fallback, and protected last-known-good
  cache behavior.

Verification:

- Initial policy red: 1 failed because the policy module did not exist.
- Attachment-boundary red: 3 failed because guarded policy arguments were not
  implemented.
- Configuration red: 1 failed because configured identifiers appeared in the
  configuration representation.
- Final representation-safety red: 1 failed because a generated temporary
  filename appeared in the preparation-result representation.
- Focused final: 43 passed, 0 failed.
- Affected Smartsheet/mailbox regressions: 67 passed, 0 failed.
- Compilation: all 9 changed Python files passed.
- git diff --check passed.
- Classification: synthetic deterministic and mock.
- No live Graph, mailbox, OCR, Ollama, patient-document, Smartsheet, or external
  AI operation occurred during implementation verification.

Safety and limitations:

- Production orchestration does not construct or pass filename policies, so
  production naming remains disabled.
- The authoritative SharePoint drive/item values are not configured in the
  local protected environment boundary.
- The official renewal workflow token and single-date ownership rule for
  state communications/notices remain unresolved.
- No PHI, protected filename/path, workbook content, configured identifier,
  URL, credential, token, payload, row identifier, cache, or patient file is
  recorded in this checkpoint.

Exact next starting point:

Resolve the authoritative reference workbook drive/item identity through a
read-only Microsoft Graph/SharePoint metadata discovery path, store values only
in the ignored local configuration boundary, and run a PHI-safe read-only
reference refresh/validation. Do not enable production filename wiring.


------------------------------------------------------------
AMBIGUITY-SAFE SERVICE REFERENCE LOOKUP - 2026-08-20
------------------------------------------------------------

Work completed:

- Confirmed three live SERVICES LISTING conflicts are legitimate business
  distinctions, not duplicate mappings to collapse.
- Preserved the existing three-part HCPCS/BILL CODE + MODIFIERS + PROGRAM key
  and existing workbook schema without requiring PRIORITY.
- Allowed multiple naming results under one key to load while returning
  unresolved/ambiguous at lookup instead of choosing one.
- Kept unique mappings deterministic and kept DESCRIPTION informational only;
  no priority or other discriminator is inferred from free text or key fields.
- Kept production filename orchestration disabled and unchanged.

Verification:

- Initial corrected-rule red: the loader still required the rejected PRIORITY
  schema and could not load existing unique service mappings.
- Focused reference/filename boundary: 46 passed, 0 failed.
- Affected Smartsheet/mailbox regressions: 67 passed, 0 failed.
- Classification: synthetic deterministic and mock.
- No mailbox document, OCR, Ollama, patient data, Smartsheet write, production
  rename, or external AI operation occurred.

Limitations and operator action:

- The authoritative workbook can retain its legitimate conflicting rows.
- Those keys intentionally remain unresolved until the owner defines how a
  supported discriminator is determined from source documents.
- No production caller currently performs service lookup for filename
  generation, and production filename wiring remains disabled.

Exact next starting point:

Rerun the PHI-safe live reference refresh against the unchanged authoritative
workbook and verify ambiguous service lookups, unchanged-version cache reuse,
and last-known-good protection. Keep production filename wiring disabled while
the source-document priority rule remains unresolved.


------------------------------------------------------------
LIVE SHAREPOINT REFERENCE REFRESH VERIFIED - 2026-08-20
------------------------------------------------------------

Work completed:

- Ran only the configured authoritative SharePoint reference refresh through
  the existing read-only Microsoft Graph boundary.
- Verified source configuration, metadata lookup, version availability, and
  workbook download without recording protected identifiers or source details.
- Validated PAYOR LISTING and SERVICES LISTING. Optional DOCUMENT TYPES was not
  present.
- Verified that legitimate conflicting service mappings load and remain
  unresolved/ambiguous rather than invalidating the workbook.
- Refreshed the ignored local cache, verified unchanged-version reuse on a
  second run, and verified malformed refresh preserves last-known-good state.
- Kept production filename orchestration disabled.

Verification and PHI handling:

- Classification: real external integration for read-only Graph metadata and
  workbook download; deterministic local workbook/cache validation.
- Sanitized failure category: none.
- No mailbox document, OCR, Ollama, Smartsheet write, production rename, or
  external AI operation occurred.
- No identifiers, URLs, tokens, credentials, local paths, workbook contents,
  or protected data are recorded here.

Limitations:

- The official renewal workflow naming token remains unresolved.
- Deterministic ownership/source evidence for single-date state
  communication/notice naming remains unresolved.
- Neither rule may be guessed, and production filename wiring remains disabled.

Exact next starting point:

Resolve the remaining filename business rules before production filename wiring,
specifically:

- official renewal workflow naming token
- deterministic ownership/source evidence for single-date state communication/notice naming

Do not guess either rule.


------------------------------------------------------------
2067 DOCUMENT TYPE / WORKFLOW SEPARATION - 2026-08-20
------------------------------------------------------------

Work completed:

- Clarified 2067 as a document/form type only, separate from optional
  workflow/context.
- Added an explicit resolved-reference workflow input. A 2067 can coexist with
  supported INBOUND RENEW, INIT, or a future supported workflow value without
  a fixed two-choice list.
- A 2067 with no supported workflow omits workflow without guessing. An
  explicitly unresolved or ambiguous workflow blocks final naming with review.
- Preserved the independently supported authorization-initial rule, including
  coexistence with 2067.
- Kept actual authorization-renewal naming separate: renewal does not inherit
  INBOUND RENEW, and RENEW AUTH was not hard-coded.
- Kept production filename orchestration disabled.

Files changed:

- src/services/filename_policy_service.py
- src/services/reference_filename_builder_service.py
- tests/test_filename_policy_service.py
- tests/test_reference_filename_builder.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Initial focused run: compilation passed; filename policy stopped at 1 failed
  assertion because the optional-2067 branch preceded the existing independent
  authorization-initial rule. The smallest ordering correction was applied.
- Final focused synthetic deterministic: 20 passed, 0 failed.
- Affected attachment/reference/Smartsheet/mailbox synthetic deterministic and
  mock regressions: 36 passed, 0 failed.
- Both modified Python services compiled successfully.
- git diff --check passed.

PHI and integration safety:

- Synthetic values and local synthetic file bytes only.
- No protected data, OCR text, source_text, patient value, protected filename or
  path, payload, external identifier, credential, token, or workbook content
  was accessed or exposed.
- No mailbox processing, OCR, Ollama, Graph, Smartsheet external call, real file
  rename, production filename wiring, or external AI operation occurred.

Limitations and exact next starting point:

- INBOUND RENEW is supported only when supplied as approved 2067
  workflow/context; it is not an authorization-renewal naming rule.
- The official naming token/rule for actual authorization-renewal documents and
  deterministic single-date ownership for state communications/notices remain
  unresolved.
- Resolve those two rules without guessing before enabling production filename
  wiring.


------------------------------------------------------------
AUTHORIZATION RENEWAL / 2067 POSTED DATE POLICY - 2026-08-20
------------------------------------------------------------

Work completed:

- Encoded the owner-confirmed RENEW AUTH token for actual authorization
  renewals without reusing 2067 workflow context.
- Added a separate optional supported qualifier dimension. NO CHANGE may
  follow RENEW AUTH only when supplied as a resolved input; it is never used
  to infer renewal, cannot decorate a non-renewal workflow, and is never
  guessed when missing or unresolved.
- Inspected historical local filename structure without displaying filenames.
  No existing NO CHANGE filename example was available. Qualifier formatting
  therefore follows the established uppercase token and underscore-separated
  major-component grammar.
- Preserved 2067 as a form/document dimension separate from workflow.
  Independently supported INBOUND AUTH and future database-backed workflow
  values may coexist with it. INIT is not inferred from the 2067 or client
  assumptions.
- Added a dedicated resolved Posted Date policy input. A 2067 uses only that
  value for its single naming date; authorization start/end dates and other
  candidates cannot override it. Missing, unsupported, conflicting, or invalid
  Posted Date blocks deterministic naming with review.
- Kept non-2067 date handling, ambiguous service-reference behavior, guarded
  attachment fallback, and disabled production filename orchestration
  unchanged.

Files changed:

- src/services/filename_policy_service.py
- src/services/reference_filename_builder_service.py
- tests/test_filename_policy_service.py
- tests/test_reference_filename_builder.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Both modified Python services compiled successfully.
- Focused synthetic deterministic: 27 passed, 0 failed.
- Affected synthetic deterministic/mock regressions: 61 passed, 0 failed.
- Combined: 88 passed, 0 failed.

PHI and integration safety:

- Tests used synthetic values, mocked integrations, and synthetic local bytes.
- Historical filename inspection returned aggregate token-pattern counts only;
  no protected filename, path, patient value, OCR text, source_text, document
  content, payload, identifier, credential, or token was displayed or stored.
- No mailbox processing, OCR, Ollama, Graph, Smartsheet external call, real
  file rename, production filename wiring, protected-data processing, or
  external AI operation occurred.

Limitations and exact next starting point:

- Production orchestration does not yet construct Posted Date, 2067 workflow,
  or renewal qualifier policy inputs. Extraction and deterministic validation
  do not expose a dedicated Posted Date field.
- INIT versus renewal refinement for inbound 2067 activity requires future
  internal client-system/database context.
- Define the smallest validated source-field boundary for Posted Date,
  supported 2067 workflow context, and optional renewal qualifiers before
  production filename wiring. Keep ambiguous service-reference distinctions
  review-safe and do not enable production filename generation until all
  required inputs are deterministic.


------------------------------------------------------------
VALIDATED FILENAME INPUT BOUNDARY - 2026-08-20
------------------------------------------------------------

Work completed:

- Added dedicated posted_date and renewal_qualifier fields to the existing
  value/confidence/source_text extraction contract instead of overloading
  authorization start/end dates.
- Added prompt constraints prohibiting Posted Date inference from other dates,
  document position, or filename and prohibiting qualifier inference from
  quantities, unchanged-looking hours, filenames, or generic wording.
- Extended deterministic evidence validation so Posted Date requires an
  explicit matching Posted Date label and renewal qualifiers require explicit
  matching qualifier evidence. Invalidated values become null with zero
  confidence while source_text remains preserved for authorized local review.
- Added a separate validated filename-input service. It preserves field
  confidence and source evidence internally but exposes only resolved lookup
  values to filename policy.
- Accepted 2067 workflow context only as an explicit resolved business-context
  lookup. The service never derives workflow from 2067, classification subtype,
  document content, filename, or client-existence assumptions and remains open
  to future approved database-backed values.
- Required an independently approved matching qualifier reference in addition
  to deterministic source evidence. A qualifier cannot infer renewal, and
  missing, unsupported, ambiguous, conflicting, mismatched, or non-applicable
  claims remain unresolved/review-safe.
- Kept production filename construction, attachment naming, file renaming,
  mailbox processing, and external writes disconnected and unchanged.

Files changed:

- src/ai/llm/providers/ollama_provider.py
- src/services/evidence_validation_service.py
- src/services/filename_validated_input_service.py
- tests/test_filename_validated_input_service.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Three production Python modules and the focused test compiled successfully.
- Focused synthetic deterministic: 80 passed, 0 failed.
- Affected synthetic deterministic/mock regressions: 164 passed, 0 failed.

PHI and integration safety:

- Tests used synthetic evidence and mocked/local-only boundaries. Evidence
  values and source_text were not printed.
- No mailbox document, OCR, Ollama request, Graph call, Smartsheet external
  write, real file rename, protected-data processing, production filename
  generation, or external AI operation occurred.

Limitations and exact next starting point:

- Production orchestration does not construct or consume validated filename
  inputs. No approved runtime provider yet supplies 2067 workflow context or
  supported qualifier reference values.
- Ambiguous service-reference distinctions still lack an approved source-
  document discriminator and remain unresolved.
- Define a non-production filename-request assembly boundary combining
  validated inputs with resolved payer/service references without renaming or
  writing files. Identify approved runtime workflow/qualifier context providers
  before any production filename wiring.


------------------------------------------------------------
CACHE-ONLY EVALUATOR LAZY PADDLE INITIALIZATION - 2026-08-20
------------------------------------------------------------

Work completed:

- Changed PaddleOCRProvider to defer Paddle engine creation until a validated
  document has no current or legacy cache result and fresh OCR prediction is
  permitted.
- Preserved OCRService, OCRFactory, DocumentProcessor, provider registration,
  validation, shared fingerprinting, cache lookup/migration, cache-only miss,
  prediction, cache write, and sanitized evaluator boundaries.
- Added constructor-level synthetic proof that cache-only hits and misses do
  not initialize Paddle, plus proof that a normal cache miss initializes
  Paddle once when prediction is required.

Files changed:

- src/ai/ocr/providers/paddle_ocr_provider.py
- tests/test_ocr_cache_only.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Modified production provider and focused test compiled successfully.
- Cache-only OCR focused tests: 9 passed, 0 failed.
- Paddle fingerprint integration: 3 passed, 0 failed.
- Local evaluator: 18 passed, 0 failed.
- DocumentProcessor: 18 passed, 0 failed.
- Processor classification integration: 10 passed, 0 failed.
- Combined synthetic deterministic/mock: 58 passed, 0 failed.
- A PHI-safe synthetic constructor/cache-boundary probe constructed the
  default DocumentProcessor, returned cached OCR in cache-only mode, observed
  zero Paddle initializations, and made zero Ollama requests.

PHI, compatibility, and limitations:

- No protected document or cache content was processed or displayed. No real
  Paddle prediction, Ollama request, Graph/mailbox, Smartsheet, filename
  operation, production write, or external AI operation occurred.
- Normal non-cache production callers remain unchanged and still initialize
  Paddle when prediction is required after a cache miss.
- The protected single-item evaluator has not yet been rerun.

Exact next starting point:

Run the explicitly authorized single-item cache-only local evaluator against
the already selected protected document. Verify cached OCR is reached without
Paddle initialization, then allow only approved local Ollama and protected
local review. Do not fetch mailbox content, rerun OCR, write Smartsheet,
rename files, enable production filename wiring, or use external AI. Return
aggregate PHI-safe results only.


------------------------------------------------------------
REUSABLE PHI-SAFE SINGLE-DOCUMENT LEARNING REPORT - 2026-08-20
------------------------------------------------------------

Work completed:

- Extended the existing local evaluator with explicit --learning-report mode;
  the positive numeric selector, Run Type, cache/protected-data authorization,
  and local-Ollama authorization remain mandatory.
- Kept cache-only OCR and the existing classification, extraction, independent
  candidate validation, business rules, and review path unchanged.
- Added one local-only structured Ollama learning request over the complete OCR
  text and a separate sanitizer/report builder. No newest-file heuristic or
  duplicate processing architecture was added.
- Added value-free report sections for document/form structure and page count,
  modeled-field inventory, date roles, authorization/service structure,
  supported business concepts, schema gaps, review/attempt state, unresolved
  ambiguity names, and development implications marked as observed evidence or
  proposed interpretation.
- Added a conservative safe-label gate. Unsafe or unknown model-proposed labels
  become generic unmodeled field/concept categories instead of being exposed.
  Novel concept/schema-gap observations are explicitly marked as not
  deterministically validated and cannot change production rules automatically.

Files changed:

- scripts/evaluate_local_document.py
- src/ai/llm/llm_provider.py
- src/ai/llm/llm_service.py
- src/ai/llm/providers/ollama_provider.py
- src/services/local_document_evaluation_service.py
- src/services/local_document_learning_report_service.py
- tests/test_local_document_evaluation_service.py
- tests/test_local_document_learning_report_service.py
- tests/test_llm_attempt_routing.py
- tests/test_ollama_service_lines.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Focused learning-report, evaluator, routing, and Ollama schema/prompt tests:
  46 passed, 0 failed.
- Affected cache-only OCR, protected-review, DocumentProcessor, and processor
  classification regressions: 46 passed, 0 failed.
- Combined synthetic deterministic/mock: 92 passed, 0 failed.
- All eleven changed Python files compiled successfully.

PHI, compatibility, and limitations:

- Tests used synthetic values and mocked providers only. Protected markers,
  source paths, values, evidence text, and narrative text were excluded from
  serialized reports.
- No protected document or cached PHI was accessed. No real Paddle, OCR,
  Ollama, Graph/mailbox, Smartsheet, rename, filename wiring, or external AI
  operation occurred.
- The mode is explicit opt-in and has not yet been run against a protected real
  document. Unknown semantic labels remain withheld until added to the safe
  structural vocabulary through reviewed evidence.

Exact next starting point:

Run the reusable analyzer once against an explicit operator-selected numeric
document index using --learning-report, cached OCR only, and approved local
Ollama. Verify comprehensive PHI-safe output before using observed evidence and
proposed interpretations for planning. Do not select by newest-file heuristic,
fetch mailbox content, rerun OCR, write Smartsheet, rename files, enable
production filename wiring, or use external AI.


------------------------------------------------------------
PHI-SAFE LOCAL DOCUMENT NUMERIC LISTING - 2026-08-20
------------------------------------------------------------

Work completed:

- Extended the existing local evaluator and selector with --list-documents.
- Listing returns only numeric index, relative recency order, file type, and
  cached-OCR availability and requires none of the evaluation-only arguments.
- Listing and evaluation share one stable candidate enumeration. An internal
  ignored selection snapshot detects candidate additions, removals, content
  changes, or ordering changes and blocks evaluation before processor
  construction with a sanitized category until the operator relists.
- Normal evaluation still requires an explicit positive document index; no
  newest-document heuristic or automatic selection was introduced.
- Recorded the durable knowledge-architecture decision to keep the reusable
  company AI brain native to project rules, tested continuity, authoritative
  references, executable semantics, PHI-safe evidence reports, deterministic
  rules, review outputs, and tracker history rather than adopting Obsidian.
  Learning-report evidence cannot automatically become a production rule.

Files changed:

- scripts/evaluate_local_document.py
- src/services/local_document_evaluation_service.py
- tests/test_local_document_evaluation_service.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Modified Python compiled successfully.
- Focused local evaluator/listing tests: 23 passed, 0 failed.
- Affected protected-review, learning-report, and fingerprint regressions: 23
  passed, 0 failed.
- Combined synthetic deterministic/mock: 46 passed, 0 failed.

PHI, compatibility, and limitations:

- Synthetic files and mocked processors only were used. Forbidden filenames,
  paths, fingerprints, protected markers, and content were absent from safe
  listing output.
- Listing performs local fingerprinting and cache-file existence checks only;
  it does not construct the processor, read OCR cache text, invoke Paddle or
  Ollama, classify/extract/validate a document, or call Graph, mailbox,
  Smartsheet, rename, filename wiring, or external AI.
- The internal selection snapshot remains inside the already-ignored
  protected OCR-cache boundary and is never emitted or committed.

Exact next starting point:

Run --list-documents, explicitly choose one numeric index, and then run the
reusable analyzer once with --learning-report, cached OCR only, and approved
local Ollama. If selection state changed, relist. Do not fetch mailbox content,
rerun OCR, write Smartsheet, rename files, enable production filename wiring,
or use external AI.


------------------------------------------------------------
LOCAL PROTECTED DOCUMENT SELECTOR - 2026-08-20
------------------------------------------------------------

Work completed:

- Added explicit --select-document mode to the existing local learning
  analyzer and reused the synchronous Tkinter protected-UI architecture.
- The protected window derives and displays candidate filenames locally. The
  selector returns only a stable numeric index; filenames and paths never
  enter CLI output, safe result objects, continuity, tracker detail, or logs.
- Candidate enumeration and snapshot recording remain owned by the evaluator
  service. The selected index follows the existing snapshot-change check
  before cache-only processing; no newest-document selection was added.
- Cancellation and selector unavailability fail safely before processor
  construction. Existing --document-index and --list-documents automation
  modes remain unchanged.

Files changed:

- scripts/evaluate_local_document.py
- src/services/local_document_evaluation_service.py
- src/ui/local_protected_review.py
- tests/test_local_document_evaluation_service.py
- tests/test_local_protected_review.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Five changed Python files compiled successfully.
- Focused selector, evaluator, and protected-UI tests: 39 passed, 0 failed.
- Affected learning-report tests: 4 passed, 0 failed.
- Combined synthetic deterministic/mock: 43 passed, 0 failed.

PHI, compatibility, and limitations:

- Tests used synthetic paths and values only. Protected display labels were
  available only to an injected local selector view and were absent from
  captured stdout, stderr, repr, and safe mappings.
- No protected document or real filename was displayed or processed. No OCR,
  Paddle, Ollama, Graph/mailbox, Smartsheet, clipboard, persistence, rename,
  production filename wiring, or external AI operation occurred.
- The real protected selector window and subsequent analyzer run have not yet
  been operator-executed.

Exact next starting point:

Run the reusable analyzer once through --select-document with
--learning-report, cached OCR only, and approved local Ollama. Keep the source
filename inside the protected UI and verify only sanitized structural output
is returned. Do not fetch mailbox content, rerun OCR, write Smartsheet, rename
files, enable production filename wiring, or use external AI.


------------------------------------------------------------
READ-ONLY LEARNING INBOX REFRESH - 2026-08-20
------------------------------------------------------------

Work completed:

- Added explicit --refresh-top N for the local learning workflow, restricted
  to 1-25 newest inbox messages and valid only with --select-document.
- Added a dedicated read-only EmailService query selecting only internal
  message ID and attachment-presence fields, ordered newest-first.
- Added a narrow refresh adapter around existing Graph attachment enumeration.
  It downloads only supported, non-inline attachments into the existing
  protected candidate area and returns only sanitized counts/status.
- Existing local filenames are skipped without overwrite or rename. After a
  successful refresh, the unchanged protected selector records its snapshot
  and returns only the chosen numeric index.
- The adapter has no mark-read, handled/idempotency-state, DocumentProcessor,
  OCR, Ollama, Smartsheet, or production filename dependency.

Files changed:

- scripts/evaluate_local_document.py
- src/graph/email_service.py
- src/graph/attachment_service.py
- src/services/local_document_inbox_refresh_service.py
- tests/test_local_document_inbox_refresh_service.py
- tests/test_graph_attachment_enumeration.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Six changed Python files compiled successfully.
- Focused synthetic/mock refresh tests: 5 passed, 0 failed.
- Affected Graph, evaluator, and protected-selector regressions: 46 passed, 0
  failed.
- Combined synthetic deterministic/mock: 51 passed, 0 failed.

PHI, compatibility, and limitations:

- Tests used synthetic message/attachment metadata and local temporary files.
  Protected markers were absent from stdout, stderr, repr, and safe mappings.
- No live Graph/inbox call, protected attachment, real filename, mailbox
  mutation, durable mailbox state, OCR, Paddle, Ollama, Smartsheet, rename,
  production filename wiring, or external AI operation occurred.
- The first operator-controlled live refresh and protected selection have not
  run. A filename collision is intentionally skipped and requires operator
  review rather than overwrite or automatic rename.

Exact next starting point:

Run one explicitly limited read-only refresh followed by --select-document and
--learning-report using cached OCR and approved local Ollama. Verify counts-only
refresh output and confirm the source message remains unread/unhandled. Do not
rerun OCR, write Smartsheet, rename files, enable production filename wiring,
or use external AI.


------------------------------------------------------------
EXPLICIT LOCAL OCR FOR DOCUMENT LEARNING - 2026-08-20
------------------------------------------------------------

Work completed:

- Added explicit --authorize-local-ocr to the existing learning evaluator.
  Without it, the existing cache-only boundary remains enforced.
- Authorization changes only the existing DocumentProcessor cache-only
  argument. The selected document is still protected by explicit numeric/UI
  selection and the unchanged selection snapshot.
- The existing Paddle provider checks validated fingerprint-based current and
  legacy caches before lazy initialization. An authorized cache miss may run
  local Paddle once and write through the existing protected cache mechanism;
  a cache hit never initializes Paddle.
- Early processing failures now truthfully preserve a requested learning
  report with sanitized blocked status.

Files changed:

- scripts/evaluate_local_document.py
- src/services/local_document_evaluation_service.py
- tests/test_local_document_evaluation_service.py
- tests/test_local_document_fresh_ocr_authorization.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Five changed Python files compiled successfully.
- Focused synthetic deterministic/mock tests: 38 passed, 0 failed.
- Affected synthetic deterministic/mock regressions: 52 passed, 0 failed.
- Combined: 90 passed, 0 failed.

PHI, compatibility, and limitations:

- Tests used synthetic protected markers, temporary candidates, mocked Paddle
  prediction, and mocked learning analysis. Protected filenames, paths, OCR
  text, and values were absent from evaluator stdout, stderr, repr, and safe
  mappings.
- No real protected document, Paddle prediction, Ollama request, live inbox,
  mailbox mutation, Smartsheet write, rename, production filename wiring, or
  external AI operation occurred.

Exact next starting point:

Run one explicitly limited read-only refresh followed by protected selection
and learning analysis with explicit local OCR authorization. Verify only the
selected document is processed, protected cache creation/reuse is correct,
output remains PHI-safe, and the source message remains unread/unhandled. Do
not write Smartsheet, rename files, enable production filename wiring, or use
external AI.


------------------------------------------------------------
PROTECTED CANDIDATE ORDERING AND SELECTED IDENTITY - 2026-08-21
------------------------------------------------------------

Work completed:

- Corrected the shared local-document candidate boundary to order supported
  files by local modification time in nanoseconds, newest first, with a
  deterministic internal filename tie-breaker.
- The same ordered list now feeds PHI-safe --list-documents output, the local
  protected Tkinter selector, candidate snapshots, and --document-index
  evaluation. Individual UIs do not perform separate ordering.
- A successful protected selection now records only the selected numeric index
  alongside the existing ignored candidate snapshot. Evaluation rejects a
  different numeric index while that selection is current; no selected hash,
  filename, path, or modification timestamp is exposed.
- Confirmed that the earlier cache diagnostic used selector 1 while the
  intended protected example was selector 9 and their fingerprints differed.
  The earlier selector-1 OCR-cache conclusion is therefore invalidated.

Files changed:

- src/services/local_document_evaluation_service.py
- tests/test_local_document_evaluation_service.py
- tests/test_local_document_inbox_refresh_service.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Four modified Python files compiled successfully.
- Focused evaluator/selector tests: 29 passed, 0 failed.
- Affected refresh tests: 5 passed, 0 failed.
- Affected protected-review UI tests: 12 passed, 0 failed.
- Affected fresh-OCR authorization tests: 2 passed, 0 failed.
- Affected learning-report tests: 4 passed, 0 failed.
- Combined synthetic deterministic/mock: 52 passed, 0 failed.

PHI, compatibility, and limitations:

- Tests used only synthetic temporary files, mock processors, synthetic
  protected markers, and local timestamp metadata. Safe outputs contained no
  filenames, paths, fingerprints, modification timestamps, OCR text, values,
  source evidence, credentials, tokens, or destination identifiers.
- No protected document, OCR cache content, Paddle prediction, Ollama request,
  live Graph/inbox operation, mailbox mutation, Smartsheet write, rename,
  production filename wiring, or external AI operation occurred.
- Candidate recency uses local filesystem modification time as the existing
  authoritative local source. Equal timestamps use an internal deterministic
  filename ordering without exposing that value.

Exact next starting point:

After commit, list and reselect the intended protected document under the
corrected newest-first order. With separate explicit authorization, repeat
only the cache-only deterministic marker-presence check against that confirmed
selection. Do not rerun Paddle or Ollama, refresh the inbox, write Smartsheet,
rename files, enable production filename wiring, or use external AI.


------------------------------------------------------------
AUTHORITATIVE GRAPH RECENCY DOCUMENT ORDERING - 2026-08-21
------------------------------------------------------------

Work completed:

- Replaced filesystem-mtime candidate ordering with validated Microsoft Graph
  received recency at the shared listing/selector/snapshot/evaluation boundary.
- Added an ignored, fingerprint-keyed local recency registry with atomic writes,
  schema validation, and non-reversible message and attachment tie-break keys.
- Byte-identical filename collisions can promote an existing local candidate
  without overwrite; different-content collisions receive no recency claim.
- Authoritative candidates sort first by newest Graph receipt, then deterministic
  message and attachment keys. Legacy candidates follow in fingerprint order.
- Advanced the selection snapshot contract so an ordering change invalidates a
  stale protected selection before processing.

Verification:

- Modified Python files compiled successfully.
- Focused and affected synthetic deterministic/mock tests: 64 passed, 0 failed.
- No live Graph call, protected document access, OCR, Ollama, mailbox mutation,
  Smartsheet write, rename, production filename wiring, or external AI occurred.
- Safe results exposed no message identifiers, received timestamps, filenames,
  paths, fingerprints, registry contents, OCR text, or protected values.

Exact next starting point:

After commit, perform one explicitly authorized limited read-only refresh to
populate authoritative recency metadata, then list and reselect locally. Do not
run OCR or Ollama or process a protected document.


------------------------------------------------------------
DUPLICATE-BYTE PROTECTED CANDIDATE IDENTITY - 2026-08-21
------------------------------------------------------------

Work completed:

- Separated local candidate identity from source-byte fingerprint identity so
  distinct local files with identical bytes remain independently selectable.
- Advanced the private recency registry to candidate-keyed schema v2, binding
  each recency claim to the opaque local candidate and current source bytes.
- Preserved Graph received recency authority and deterministic opaque-candidate
  tie-breaking for authoritative and legacy duplicates.
- Advanced snapshots to version 4 so path, bytes, membership, ordering, or
  selected-index changes stop stale selection before processing.
- Existing fingerprint-only schema-v1 recency is ignored rather than assigned
  ambiguously; a later authorized refresh will repopulate candidate metadata.

Verification:

- Modified Python files compiled successfully.
- Focused and affected synthetic deterministic/mock tests: 69 passed, 0 failed.
- Duplicate bytes, independent recency, legacy ordering, exact selection,
  snapshot invalidation, collision safety, and safe output were covered.
- Live read-only acceptance populated schema-v2 recency, opened the protected
  selector, preserved duplicate-byte entries, and operator-confirmed the actual
  newest inbox document at index 1 without processing it.
- No live Graph refresh, protected document processing, OCR, Ollama, mailbox
  mutation, Smartsheet write, rename, or external AI occurred.

Exact next starting point:

After commit, use the current snapshot-protected selection for the authorized
PHI-safe cached-OCR marker check. Do not rerun OCR or Ollama or refresh inbox.


------------------------------------------------------------
SYNTHETIC CONTACT-FAILURE NORMALIZATION - 2026-08-21
------------------------------------------------------------

Work completed:

- Added a reusable deterministic contact-failure normalization boundary that
  preserves supplied confidence and source evidence.
- Clear inability or failed attempts to reach a member support
  contact_failure. Conditional service consequences strengthen the result only
  when contact-failure evidence is independently present.
- Unsupported and ambiguous wording remains null/unknown with review required.
- Contact failure remains separate from literal document text and workflow UTL;
  no UTL mapping or production caller was added.

Verification:

- Focused synthetic deterministic tests: 7 passed, 0 failed.
- Focused plus affected learning-report, evidence-validation, and review-output
  regressions: 48 passed, 0 failed.
- No protected data, OCR, Paddle, Ollama, Graph, Smartsheet, rename, or external
  AI operation occurred.

Exact next starting point:

After commit, leave the normalization boundary unwired until a consumer and any
workflow mapping are explicitly approved. Do not infer UTL automatically.


------------------------------------------------------------
WHOLE-DOCUMENT LEARNING ANALYZER ARCHITECTURE - 2026-08-21
------------------------------------------------------------

Work completed:

- Added protected structured OCR document/page/block models while preserving
  raw_text and the existing production processing contracts.
- Paddle and searchable-PDF providers preserve ordered pages and blocks when
  available. Paddle adds a protected hash-named structured cache sidecar;
  legacy text-only cache hits remain cache-only and explicitly report that
  page/layout relationships are unavailable.
- The opt-in local learning request now receives one complete evidence envelope
  with opaque page/block references and modeled-field context. Layout and
  coordinates are optional hints and never fixed requirements.
- Added strict referenced observations, coverage, contradictions, nullable
  confidence, repeated/conflicting candidate status, and schema-version-2
  synthesis. Invalid references are downgraded to unsupported/review.
- Added generalized PHI-safe novel observations. Unsafe proposed labels never
  enter the report; a safe category and report-local ordinal preserve the gap.
- Literal evidence, normalized concepts, and production rules remain separate.
  Learning output cannot infer UTL, approval, or visits or change production.

Files changed:

- Structured OCR/evidence models, OCR provider/service implementations,
  DocumentProcessor attachment, Ollama learning schema/prompt, local evaluator,
  learning report/sanitizer, and focused synthetic tests.
- PROJECT_MEMORY.md and update_project_tracker.py.

Verification:

- Modified Python files compiled successfully.
- Focused synthetic deterministic/mock checks: 58 passed, 0 failed.
- Affected synthetic deterministic/mock regressions: 149 passed, 0 failed.
- No protected data was accessed. No real OCR, Paddle prediction, Ollama,
  Graph, mailbox mutation, Smartsheet, rename, or external AI operation ran.

Limitations and exact next starting point:

- Legacy text-only cache content cannot recover page/block relationships without
  OCR and remains explicitly unavailable rather than triggering OCR.
- Review this uncommitted diff and evidence. If approved, stage only reviewed
  safe files, commit, push, and verify sync. A protected cache/local-Ollama
  acceptance run requires separate explicit authorization afterward.


------------------------------------------------------------
PHI-SAFE OCR PERFORMANCE DIAGNOSTICS - 2026-08-24
------------------------------------------------------------

Work completed:

- Added per-request PHI-safe phase diagnostics to the normal Paddle provider
  path without changing OCR inputs, cache formats, or production return types.
- Cache lookup, Paddle initialization, eager/lazy prediction, ordinal result
  consumption, conversion/traversal, block construction, and both cache writes
  now have separate counts and timings.
- Safe runtime metadata includes package versions, sanitized device class,
  allowlisted thread settings, nullable oneDNN status, fixed configuration
  identifiers, and safe input/size buckets.
- Deterministic invariants flag repeated prediction/submission or result
  conversion and confirm cache serialization causes no extra provider call or
  application source reread.
- Diagnostics flow through OCRService and DocumentProcessor processing metrics
  to the PHI-safe local evaluation result.

Verification:

- Modified Python files compiled successfully.
- Focused synthetic deterministic/mock checks: 21 passed, 0 failed.
- Affected processor, evaluator, learning-report, and classification
  regressions: 62 passed, 0 failed.
- No wall-clock thresholds were used.
- No protected data, real OCR, Paddle prediction, Ollama, Graph, Smartsheet,
  rename, or external integration ran.

Limitations and exact next starting point:

- Paddle's effective internal PDF render DPI, scale, and batch size remain
  `unknown` when the installed public API does not expose them.
- The diagnostics identify a boundary but intentionally apply no performance
  correction.
- After review and commit, perform exactly one separately authorized protected
  fresh OCR run through the normal selector/provider path. Use only the safe
  phase report to select the smallest evidence-backed correction, and do not
  rerun OCR if downstream processing fails.


------------------------------------------------------------
EFFECTIVE PADDLEOCR CONFIGURATION DIAGNOSTICS - 2026-08-24
------------------------------------------------------------

Work completed:

- Corrected the misleading oneDNN diagnostic boundary without changing OCR
  behavior, constructor arguments, prediction calls, packages, or runtime
  configuration.
- The global Paddle `FLAGS_use_mkldnn` value is now reported separately from
  PaddleOCR's effective parsed `enable_mkldnn` setting.
- Effective CPU threads, MKLDNN cache capacity, and inference engine are read
  from the initialized PaddleOCR configuration. Missing or invalid values stay
  unknown and are not inferred from the global flag.
- Existing safe package versions and fixed model/config identifiers remain.

Verification:

- Modified Python files compiled successfully.
- Focused synthetic deterministic/mock diagnostics: 8 passed, 0 failed.
- Affected cache/provider/authorization/fingerprint regressions: 16 passed,
  0 failed.
- Tests prove global and effective oneDNN values may differ, unknown values
  remain unknown, and instrumentation preserves OCR results and call counts.
- No real OCR, protected document, Ollama, Graph, production Smartsheet,
  package change, or external AI operation ran.

Exact next starting point:

Review and commit this diagnostic correction. Do not run protected OCR
automatically. Any later controlled performance comparison must change one
effective inference setting only and must not treat the global Paddle flag as
PaddleOCR's effective oneDNN state.


------------------------------------------------------------
WHOLE-DOCUMENT FAMILY/SUBTYPE GROUNDING - 2026-08-25
------------------------------------------------------------

Work completed:

- Added a centralized reusable family/subtype taxonomy while preserving all
  existing Authorization and termination legacy routes.
- Added 2067 as a family and UTL as a separate subtype. The approved rule
  requires supported 2067 plus uncontradicted deterministic contact_failure;
  annual, Posted Date, literal UTL, and 2067 alone remain insufficient.
- Added whole-document deterministic concept evidence with protected source
  text, nullable confidence, page/block provenance, repetition, and conflicts.
- Replaced free-form model references with compact request-local aliases, a
  request-bound strict schema, deterministic alias resolution, and safe
  invalid-reference counts.
- Learning report schema version 3 separates family, subtype, deterministic
  concepts, model observations, modeled fields, coverage, contradictions,
  schema gaps, and novel observations without returning protected values.
- No 2067 Smartsheet mapping or subtype-specific write action was added.

Verification:

- Modified Python compiled successfully.
- Focused synthetic deterministic/mock tests: 37 passed, 0 failed.
- Affected synthetic deterministic/mock regressions: 213 passed, 0 failed.
- No protected document, OCR, Paddle prediction, real Ollama, Graph,
  Smartsheet, rename, or external integration ran.

Exact next starting point:

After review and commit, run one explicitly authorized cache-only protected
whole-document/local-Ollama acceptance with the existing structured OCR cache.
Do not rerun OCR. Verify grounded references and the PHI-safe 2067/UTL report
before requesting any missing production Smartsheet mapping decision.


------------------------------------------------------------
REAL 2067/UTL WHOLE-DOCUMENT ACCEPTANCE - 2026-08-25
------------------------------------------------------------

Work completed:

- Completed the generalized family/subtype, deterministic-concept, and
  learning-evidence grounding implementation without adding a 2067-specific
  processing stack or production Smartsheet mapping.
- Corrected deterministic 2067 form-marker recognition for bounded compact
  identifiers while rejecting unrelated embedded-number forms.
- Preserved separate protected provenance for deterministic `form_2067`,
  `contact_failure`, positive contact evidence, and model observations.
- Preserved legacy Authorization family/subtype routing and automatic-write
  boundaries.

Files:

- PROJECT_MEMORY.md
- src/ai/llm/providers/ollama_provider.py
- src/business_rules/rule_factory.py
- src/document_processing/document_processor.py
- src/models/document.py
- src/models/document_concept.py
- src/models/document_taxonomy.py
- src/models/learning_document_evidence.py
- src/services/classification_feedback_service.py
- src/services/deterministic_document_concept_service.py
- src/services/document_classification_resolution_service.py
- src/services/learning_evidence_grounding_service.py
- src/services/learning_label_sanitizer.py
- src/services/local_document_evaluation_service.py
- src/services/local_document_learning_report_service.py
- src/services/review_decision_service.py
- src/services/review_output_service.py
- tests/test_document_family_subtype_training.py
- tests/test_llm_attempt_routing.py
- tests/test_local_document_learning_report_service.py
- tests/test_processor_classification_integration.py
- update_project_tracker.py

Verification:

- Modified Python compiled successfully.
- Focused synthetic deterministic/mock checks: 57 passed, 0 failed.
- Affected synthetic deterministic/mock regressions: 214 passed, 0 failed.
- Real cached OCR / real local Ollama acceptance completed successfully on one
  protected four-page, 144-block document. Cache-only mode used the structured
  sidecar, Paddle prediction count remained zero, and no external integration
  was invoked.
- The accepted result resolved family 2067 and subtype UTL with supported
  deterministic `form_2067` and `contact_failure`. Family and subtype required
  no taxonomy review, six evidence references grounded successfully, zero
  references were unsupported, and literal UTL text was not required.
- PHI handling: protected OCR text, source evidence, document identity, paths,
  values, dates, IDs, provider details, raw model output, and Smartsheet data
  were excluded from tests, tracker content, Git, and reported diagnostics.

Limitations:

- UTL identification is accepted for this known case; full end-to-end
  Smartsheet field and mapping acceptance remains pending.
- The learning report currently records zero analyzed evidence blocks despite
  delivery of all 144 blocks and complete page coverage.
- Model-proposed novel or conflicting observations may independently recommend
  learning review even when authoritative production taxonomy is supported;
  this does not change production family/subtype or top-level review state.
- One accepted protected case does not establish universal equivalence across
  every future 2067 layout or subtype.

Exact next starting point:

Inspect the existing 2067/UTL extraction, validation, business-rule,
Smartsheet destination, and automatic-write contracts and callers. Establish
the exact approved UTL row fields and mappings, identify only the smallest
unresolved business mapping decisions, preserve Authorization behavior, and
implement only approved reusable mapping behavior before separately
authorized end-to-end Smartsheet acceptance.


------------------------------------------------------------
GENERIC PRODUCTION SMARTSHEET ROW CONTRACT - 2026-08-25
------------------------------------------------------------

Work completed:

- Extended the existing explicit mapping-policy boundary with authoritative
  family/subtype resolution and backward-compatible legacy routing.
- Made the current approved extracted-field policies the shared production
  default so every processed document, including unknown taxonomy cases, can
  produce an automatic metadata/attachment row after validation and business
  rules.
- Routed 2067/UTL through the same configuration, mapping, destination,
  submission, and attachment services used by Authorization. No subtype-
  specific writer or new destination column was added.
- Omitted mapped values below the existing field-confidence threshold or
  without reliable support while preserving review metadata and protected
  evidence internally.
- Added configuration validation for every universal operational metadata
  column emitted by the row mapper.
- Recorded that the current nine approved extracted mappings are an evolving
  Phase 1 checkpoint, not the final production schema. New fields require
  operator-approved destination columns, explicit mapping, validation, and
  tests; columns are never created or inferred automatically.

Files:

- PROJECT_MEMORY.md
- src/services/mailbox_complete_review_smartsheet_service.py
- src/services/smartsheet_mapping_policy_service.py
- src/services/smartsheet_review_configuration_service.py
- src/services/smartsheet_review_row_mapping_service.py
- tests/test_generic_smartsheet_production_mapping.py
- tests/test_mailbox_complete_review_smartsheet_service.py
- tests/test_smartsheet_partial_success_retry.py
- tests/test_smartsheet_review_configuration_service.py
- tests/test_smartsheet_review_mapping_integration.py
- tests/test_smartsheet_review_row_mapping.py
- update_project_tracker.py

Verification:

- All modified Python compiled successfully.
- Focused synthetic deterministic/mock checks: 59 passed, 0 failed.
- Affected synthetic deterministic/mock regressions: 144 passed, 0 failed.
- No real Smartsheet, Graph, OCR/Paddle, Ollama, protected document, filename,
  or external integration execution occurred.
- PHI handling: tests used synthetic values; OCR text, source_text, protected
  identity, paths, credentials, tokens, payload values, and row IDs were not
  printed, stored in continuity data, or added to Git.

Limitations:

- The live destination schema and existing correction/review workflows have
  not yet been inspected for the platform-wide feedback requirement.
- Correction/readback, immutable AI-versus-human value separation, effective-
  value resolution, and confident-but-incorrect feedback remain required
  Phase 1 work.
- Durable cross-process row/attachment idempotency and mailbox handled-state
  ordering remain production-hardening gaps.

Exact next starting point:

After explicit authorization, inspect the AI destination Smartsheet column
metadata and workflow dependencies read-only. Reconcile exact existing
review/correction titles, types, allowed values, formulas, and automations
without reading row values or modifying the sheet. Reuse sufficient existing
columns and propose only the minimum evidence-backed additions, requiring
approval before any sheet or correction/readback implementation change.


------------------------------------------------------------
MINIMAL SMARTSHEET INCORRECT-AI FEEDBACK INGESTION - 2026-08-25
------------------------------------------------------------

Work completed:

- Added a standalone read-only feedback-ingestion service with injected row,
  discussion, and protected case-storage dependencies.
- Required a nonblank configurable checkbox title and protected source scope;
  accepted only normalized literal boolean flag states.
- Read discussions only for valid flagged row references and preserved only
  nonblank comments inside protected local cases. Comment-free flagged rows
  still produce valid `comments_missing` cases.
- Added stable protected row-correlation and comment-snapshot digests.
  Exclusive digest-named JSON creation detects unchanged repeats, while added
  or edited comments produce a new case revision.
- Exposed only PHI-safe counts, success/status, and deduplicated allowlisted
  categories. Existing Smartsheet writers and production callers were not
  changed.
- Added `data/smartsheet_feedback/` to the ignore and never-commit boundaries.

Files:

- .gitignore
- AGENTS.md
- PROJECT_MEMORY.md
- src/services/smartsheet_feedback_case_storage_service.py
- src/services/smartsheet_feedback_ingestion_service.py
- tests/test_smartsheet_feedback_ingestion_service.py
- update_project_tracker.py

Verification:

- New Python modules and focused test compiled successfully.
- Focused synthetic deterministic/mock suite: 18 passed, 0 failed.
- Affected Smartsheet configuration, mapping, submission, reviewed writing,
  partial-success retry, mailbox automatic submission, generic production
  mapping, and automatic-write regressions: 100 passed, 0 failed.
- No live Smartsheet, Graph, OCR/Paddle, Ollama, patient document, model,
  prompt, mapping, rule, write, or external integration operation occurred.
- PHI handling: synthetic protected values stayed in memory or temporary
  storage; comments, row identifiers, source scope, payloads, filenames,
  credentials, tokens, and protected errors were absent from public results,
  stdout/stderr, tracker content, and Git.

Limitations:

- No live Smartsheet adapter or production caller is connected.
- The checkbox title remains unapproved and the column was not created.
- Actual SDK/API checkbox metadata and value representation have not been
  inspected, so live normalization into the strict internal boolean contract
  remains unresolved.
- Feedback cases do not retrain models or modify prompts, mappings, rules,
  document processing, original AI-written cells, or any Smartsheet content.

Exact next starting point:

After operator approval of the exact checkbox title and manual column
creation, inspect the live checkbox metadata/value representation read-only,
define its deterministic normalization into the internal boolean contract,
and implement/mock-test the least-privilege adapter that reads only flag state
and row discussions.


------------------------------------------------------------
DURABLE MAILBOX-TO-SMARTSHEET RECOVERY HARDENING - 2026-08-25
------------------------------------------------------------

Work completed:

- Added protected digest-only per-attachment job identity and exact-schema,
  atomic JSON state with leases, safe stale-lock recovery, attempt counts,
  protected row references, and fail-closed corrupt/version handling.
- Changed supported attachment acquisition to verified document-digest names
  with same-directory temporary writes, flush/fsync, and atomic replacement.
- Made flat and structured OCR cache replacement atomic.
- Delayed message handled/read completion until every processable job reaches
  durable attachment completion; no-attachment messages retain existing
  completion behavior.
- Split row creation and attachment-to-known-row operations while preserving
  the standalone compatibility wrapper.
- Added a no-default technical submission-key configuration boundary,
  least-privilege exact-row and known-row attachment metadata reads, durable
  row/attachment reconciliation, and fail-closed uncertain states.
- Added no polling, scheduler, backoff loop, queue, worker, or Prefect runtime.

Files:

- PROJECT_MEMORY.md
- src/ai/ocr/providers/paddle_ocr_provider.py
- src/clients/smartsheet_client.py
- src/graph/attachment_service.py
- src/graph/mailbox_processor.py
- src/services/document_attachment_naming_service.py
- src/services/mailbox_complete_review_smartsheet_service.py
- src/services/mailbox_document_job_state_service.py
- src/services/mailbox_document_smartsheet_recovery_service.py
- src/services/mailbox_full_review_orchestration_service.py
- src/services/smartsheet_reviewed_write_service.py
- src/services/smartsheet_submission_key_configuration_service.py
- tests/test_mailbox_document_job_recovery.py
- tests/test_mailbox_handling.py
- update_project_tracker.py

Verification:

- Modified Python files compiled successfully.
- New recovery/state/order checks: 6 passed, 0 failed.
- Focused and affected synthetic deterministic/mock mailbox, OCR cache,
  document processing, Authorization, generic 2067/UTL, unknown taxonomy,
  configuration, mapping, destination, reviewed-write, partial-success,
  submission, and orchestration suites passed.
- No live Graph, Smartsheet, OCR/Paddle, Ollama, protected document, model, or
  external integration operation occurred.
- PHI handling: only synthetic values and digest-only local state were used;
  no protected identifiers, filenames, paths, OCR text, source_text, payload
  values, row IDs, credentials, tokens, or provider details were exposed.

Limitations:

- The operator-approved technical submission-key column does not yet exist or
  have a configured title; production durable mailbox submission fails closed.
- Live read-after-write and attachment-metadata reconciliation have not been
  acceptance-tested and uncertain outcomes are never retried automatically.
- Prefect polling, scheduling, retry timing, queues, workers, and operational
  controls remain a separate later checkpoint.

Exact next starting point:

Obtain the exact operator-approved technical submission-key column title and
manually create the column outside application code. Then separately authorize
least-privilege live schema, exact-key, and attachment-metadata acceptance.
Validate uncertain-outcome behavior before Prefect integration or any policy
that permits unattended uncertain retries.


------------------------------------------------------------
CONTROLLED SMARTSHEET READ-ONLY RECONCILIATION - 2026-08-27
------------------------------------------------------------

Work completed:

- Changed destination schema inspection from whole-sheet retrieval to the
  Smartsheet SDK 4.3.0 columns-only boundary with include-all pagination.
- Corrected exact technical-key lookup to use supported Get Sheet pagination,
  request only the resolved technical column, and fail closed on invalid or
  inconsistent sheet version, row-count, or page metadata.
- Preserved all mapping, row/attachment write, recovery-state, retry, and
  uncertain-outcome behavior.
- Performed the separately authorized live read-only schema gate with the
  approved title supplied only in the child process.

Files:

- PROJECT_MEMORY.md
- src/clients/smartsheet_client.py
- src/services/smartsheet_destination_schema_service.py
- tests/test_smartsheet_client_read_boundaries.py
- tests/test_smartsheet_destination_schema_service.py
- update_project_tracker.py

Verification:

- Modified Python files compiled successfully.
- Read-boundary and schema checks: 20 passed, 0 failed.
- Recovery checks: 6 passed, 0 failed.
- Affected configuration, destination-validation, reviewed-write,
  automatic-write, and partial-success suites: 63 passed, 0 failed.
- Synthetic deterministic/mock checks used only synthetic technical metadata;
  no external API, OCR/Paddle, Ollama, Graph, or protected document operation
  occurred during those suites.
- Live read-only schema acceptance resolved exactly one exact-title column with
  TEXT_NUMBER type, but detected a system-column designation and stopped before
  row pages, exact-key lookup, or attachment metadata.
- No Smartsheet create, update, delete, or upload method was invoked. Live
  output contained only allowlisted booleans, categories, and timing buckets;
  no titles, IDs, keys, values, rows, attachment names, credentials, tokens, or
  provider errors were exposed.

Limitations:

- The approved technical column is not acceptable for controlled key writes
  while it retains a system-column designation. Application code did not and
  will not modify the column.
- Exact-key live acceptance is not run because the schema prerequisite failed.
- Attachment live acceptance remains blocked without an independently
  designated safe row.
- Read-after-write and uncertain-outcome reconciliation remain unproven, and
  uncertain row or attachment outcomes remain prohibited from automatic retry.

Exact next starting point:

Resolve the live technical-column design outside application code so the exact
approved title identifies one non-system TEXT_NUMBER column. Then rerun the
read-only schema and existing-value exact-key gates. Independently designate a
safe test row before attachment-metadata acceptance. Any later read-after-write
acceptance still requires explicit authorization for a PHI-free synthetic row,
optional synthetic attachment, response-loss simulation, and cleanup.


------------------------------------------------------------
SMARTSHEET SYSTEM-COLUMN CLASSIFICATION CORRECTION - 2026-08-27
------------------------------------------------------------

Work completed:

- Replaced SDK-wrapper truthiness in the read-only schema acceptance boundary
  with deterministic normalized-value classification.
- A truthy wrapper whose normalized content is None now means no system-column
  designation. AUTO_NUMBER, CREATED_BY, CREATED_DATE, MODIFIED_BY, and
  MODIFIED_DATE remain system-column designations; unexpected nonempty values
  fail conservatively as present.
- No title-specific logic, row/attachment behavior, mapping, write, recovery,
  retry, schema mutation, or external-write behavior changed.

Files:

- PROJECT_MEMORY.md
- src/services/smartsheet_destination_schema_service.py
- tests/test_smartsheet_destination_schema_service.py
- update_project_tracker.py

Verification:

- Modified Python files compiled successfully.
- Focused and affected synthetic deterministic/mock checks: 93 passed, 0
  failed.
- Live columns-metadata-only acceptance resolved exactly one exact-title
  column, confirmed acceptable TEXT_NUMBER type, classified normalized system
  metadata as absent, and passed the corrected schema gate.
- No row, attachment, create, update, delete, upload, Graph, OCR/Paddle,
  Ollama, patient-document, or Prefect operation occurred.
- PHI-safe live output contained only booleans and allowlisted categories; no
  titles, IDs, keys, values, credentials, tokens, or provider objects were
  emitted.

Limitations and exact next starting point:

- Exact-key and attachment-metadata live acceptance remain incomplete.
- Perform existing-value exact-key acceptance using only the validated
  technical column and without printing or persisting values or row references.
- Independently designate a safe test row before attachment-metadata acceptance.
- Read-after-write and uncertain-outcome behavior still require separate
  explicit authorization before any unattended uncertain retry policy.


------------------------------------------------------------
PHI-FREE SMARTSHEET RECONCILIATION ACCEPTANCE - 2026-08-27
------------------------------------------------------------

Work completed:

- Added deterministic mock coverage for an accepted-but-lost row response,
  exactly-one row reconciliation, an accepted-but-lost attachment response,
  exactly-one attachment reconciliation, duplicate prevention, and a durable
  second-call no-op.
- Ran one explicitly authorized live acceptance using one PHI-free synthetic
  technical-key-only row and one tiny synthetic attachment.
- Injected response loss only after each real SDK response was accepted and
  its cleanup identifier was retained in memory.
- Reconciled the existing row and attachment through the current recovery
  service without a second create or upload.
- Deleted only the captured synthetic attachment and row, then verified zero
  remaining exact-key matches.
- Removed the temporary live acceptance harness after cleanup.

Files:

- PROJECT_MEMORY.md
- tests/test_mailbox_document_job_recovery.py
- update_project_tracker.py

Verification:

- Modified Python compiled successfully.
- Focused and affected synthetic deterministic/mock checks: 107 passed, 0
  failed; no external integration was called by those suites.
- Live schema gate passed; preflight exact-key category was zero.
- Exactly one row add and one attachment upload occurred. Both suppressed-
  response boundaries reconciled to exactly one existing artifact, duplicate
  row creation was prevented, and the repeated recovery call was a no-op.
- Exactly one captured attachment deletion and one captured row deletion
  occurred. Post-cleanup exact-key category was zero.
- No existing row was targeted; unrelated row cells were not requested.
- No schema change, Graph, OCR/Paddle, Ollama, patient-document, Prefect, or
  unattended retry operation occurred.
- Output contained only allowlisted statuses, booleans, count categories, and
  timing buckets. Titles, IDs, keys, values, filenames, paths, credentials,
  tokens, provider objects, and provider errors were excluded.

Limitations and exact next starting point:

- One PHI-free synthetic case proves the controlled boundary, not broad
  production reliability, and does not authorize unattended uncertain retries.
- Perform a repository-level Prefect integration and fit assessment against
  current entry points, durable state, Windows runtime, PHI-safe diagnostics,
  and retry boundaries. Plan the smallest self-hosted adapter without rewriting
  processing services and keep unattended uncertain retries disabled.


------------------------------------------------------------
PREFECT PHI-SAFE LOCAL CONTROL ROOM - 2026-08-27
------------------------------------------------------------

Work completed:

- Pinned Prefect 3.8.4 in the project dependency file and installed it in the
  Python 3.13.14 project virtual environment.
- Added one parameterless PHI-safe synthetic flow and one bounded synthetic
  task with zero retries, disabled print capture, and disabled result
  persistence. No production application service is imported or callable.
- Added a versioned local process-pool deployment and a Windows operator guide
  using one complete PowerShell command per physical line.
- Verified the profile, config, server, work-pool, concurrency, deploy, worker,
  and deployment-run syntax against installed Prefect 3.8.4 CLI help.
- Corrected Windows CP1252 output failure with explicit UTF-8 configuration and
  corrected first-run profile ordering by configuring the named profile before
  using it explicitly on each command.
- Started the localhost server/UI and native process worker, registered the
  concurrency-one pool and synthetic deployment, completed two synthetic runs,
  verified UI/API/worker health, and stopped both processes.

Files:

- PROJECT_MEMORY.md
- docs/prefect_local_control_room.md
- prefect.yaml
- requirements.txt
- src/orchestration/__init__.py
- src/orchestration/prefect_control_room.py
- tests/test_prefect_control_room.py
- update_project_tracker.py

Verification:

- Prefect 3.8.4 resolved exactly and pip reported no broken requirements.
- New modules and focused test compiled successfully.
- Focused synthetic local-Prefect checks: 5 passed, 0 failed.
- Two local self-hosted synthetic process-worker runs reached Completed; UI,
  API, and worker-health endpoints returned success.
- Affected mock/synthetic checks passed: full orchestration 13, durable recovery
  8, mailbox handling 12, Smartsheet partial-success 12, and automatic-write
  boundary 13.
- The older persistent-idempotency script failed its first legacy assertion
  because its mock still implements the removed attachment interface and expects
  handled/read completion before durable business completion. No Prefect change
  touched that behavior; current handling and recovery suites passed.
- No Graph, Smartsheet write, OCR/Paddle, Ollama, patient document, protected
  state enumeration, production mailbox workflow, or uncertain retry ran.

Limitations:

- The in-app browser surface was unavailable, so UI availability was verified
  through its localhost HTTP endpoint plus Prefect run/pool state rather than a
  visual browser inspection.
- Prefect 3.8.4 repeatedly emitted non-fatal SQLite database-lock errors from
  deployment-readiness updates during worker polling. Runs and health remained
  successful, but SQLite is accepted only for this bounded manual checkpoint.
- The production callable remains disconnected. Its interactive feedback tail
  and authoritative retry-disposition contract must be addressed in application
  code before a Prefect production wrapper.
- No schedule, service, automatic startup, PostgreSQL, Redis, Docker, or
  unattended uncertain-state retry was introduced.

Exact next starting point:

Perform a PHI-free persistence decision checkpoint for the Prefect 3.8.4
Windows/SQLite deployment-readiness locking. Either prove a clean supported
SQLite configuration or prepare a separate PostgreSQL hosting plan for
approval. Keep the production callable, schedules, automatic startup, and
unattended uncertain retries disabled.


------------------------------------------------------------
PREFECT MAILBOX APPLICATION BOUNDARY - 2026-08-27
------------------------------------------------------------

Work completed:

- Reconciled the stale cross-instance mailbox idempotency regression to the
  current supported-attachment and delayed handled/read completion contracts.
- Added explicit interactive, downstream, and demo classification-review modes.
  Downstream mode leaves review as downstream exception handling and does not
  invoke the local interactive classification-feedback tail.
- Added an application-owned PHI-safe durable job-batch summary with aggregate
  row/attachment attempts, bounded completion/pending counts, sanitized failure
  category, and fail-closed retryability.
- Added a parameterless one-call Prefect mailbox adapter with zero retries,
  disabled result persistence/print capture, sanitized exceptions, and fixed
  approved Run Type `Prefect bounded mailbox orchestration`.
- Kept the adapter absent from prefect.yaml; no mailbox deployment or schedule
  was registered or executed.
- Documented the exact SQLite-to-PostgreSQL production gate.

Verification:

- New/modified Python modules compiled successfully.
- Prefect mailbox readiness: 8 passed, 0 failed; synthetic/mock.
- Persistent cross-instance idempotency: 1 passed, 0 failed; synthetic local
  durable state with mocked attachment/document boundaries.
- Full mailbox orchestration: 13 passed, 0 failed; mock.
- Full mailbox command: 12 passed, 0 failed; mock.
- Affected mailbox handling, durable recovery, mailbox Smartsheet coordination,
  partial-success, automatic-write, mapping, and synthetic Prefect regressions
  passed with no external integration.
- The approved fixed Run Type was accepted and preserved by the current mapping
  contract rather than inferred or added as an environment convention.
- No Graph, Smartsheet write, OCR/Paddle, Ollama, patient document, production
  mailbox workflow, protected-state enumeration, schedule, or uncertain retry
  ran.

Safety and limitations:

- Uncertain row/attachment outcomes, corrupt/inconsistent or unavailable state,
  duplicate/permanent blocks, active leases, row-write pending state without a
  durably reconstructible processed result, and insufficient evidence are all
  non-retryable.
- Pending/completion counts cover only explicitly selected jobs from the bounded
  invocation and are not a global mailbox backlog.
- The adapter is import/mock-tested only. SQLite locking remains unresolved and
  blocks mailbox deployment registration, Prefect retries, scheduling,
  automatic startup, multiple workers, and always-on production.

Exact next starting point:

Run a PHI-free Prefect persistence decision checkpoint using the intended
single-server/single-worker production-shaped topology. Prove a supported
SQLite soak with zero lock errors or prepare a separate PostgreSQL hosting plan
for approval. Do not register or run the dormant mailbox adapter or enable
schedules, startup, Prefect retries, or uncertain-state retries.


------------------------------------------------------------
PREFECT POSTGRESQL CONTROL PLANE - 2026-08-27
------------------------------------------------------------

Work completed:

- Installed native PostgreSQL 17.11 and configured the single discovered
  service for manual startup, localhost-only listening, port 5432, and SCRAM.
- Created a least-privilege Prefect login/database and stored only current-user
  DPAPI ciphertext outside the repository.
- Added fail-closed configuration and process-local launcher scripts, a
  password-free server profile, focused tests, and PostgreSQL operator guidance.
- Preserved the old SQLite database as a rollback artifact and kept the dormant
  mailbox adapter absent from prefect.yaml.

Verification:

- PowerShell AST parsing and affected Python compilation passed.
- PostgreSQL-focused synthetic deterministic checks: 6 passed, 0 failed.
- Existing synthetic Prefect checks: 5 passed, 0 failed.
- Prefect 3.8.4 reported PostgreSQL 17.11; pip check found no broken packages.
- Real local Prefect/PostgreSQL migration execution succeeded. Five strictly
  sequential synthetic flows and five tasks completed with run count one, zero
  retries, pool concurrency one/READY, and API/worker health 200.
- Reviewed server/worker output contained no SQLite locking, sqlite3,
  OperationalError, unexpected traceback, PHI, or protected identifiers.
- No Graph, Smartsheet, OCR/Paddle, Ollama, patient document, mailbox adapter,
  schedule, or external production integration ran.

Limitation and exact next start:

- Prefect 3.8.4 offline migration dry-run deterministically fails at historical
  data migration 14dc68cc5853 because its offline result object is null. The
  launcher fails closed and removes secret-bearing state; real migration and
  runtime acceptance passed. Resolve this pinned-version dry-run defect or
  obtain an explicit operational exception before registering the dormant
  manual-only mailbox deployment. Keep startup, schedules, Prefect retries,
  and unattended uncertain-state retries disabled.


------------------------------------------------------------
PREFECT 3.8.4 DRY-RUN EXCEPTION - 2026-08-27
------------------------------------------------------------

Assessment:

- Classified the failure as an upstream dry-run-only defect. Alembic offline
  SQL emission returns no cursor result, while historical migration
  14dc68cc5853 unconditionally dereferences result.rowcount.
- Confirmed the online path uses a real PostgreSQL connection/result and that
  the migration source remains unchanged in Prefect 3.8.5.dev1 and current
  upstream main. No matching upstream fix or issue was found.
- Accepted a narrow operational exception for pinned Prefect 3.8.4 only; it
  expires and must be re-evaluated on every Prefect version change.

Read-only verification:

- Derived one installed PostgreSQL migration head: 9e9dadc36797 across 116
  revisions.
- Queried exactly one database revision equal to that installed head.
- Flow and task state-name invariant-gap counts were both zero.
- Existing evidence remains: real online migration succeeded, Prefect reported
  PostgreSQL 17.11, and five sequential synthetic flows/tasks completed with
  zero retries and healthy API/worker endpoints.
- PostgreSQL was stopped after verification; ports 4200, 8080, and 5432 had no
  listeners, and process password/connection settings were absent.
- No Graph, Smartsheet, OCR/Paddle, Ollama, patient document, mailbox adapter,
  schema mutation, schedule, or retry operation ran.

Exact next starting point:

Review addition of the existing bounded_mailbox_flow to prefect.yaml as a
second manual-only, parameterless deployment using lthhc-local-process,
concurrency one, no schedule, no Prefect retries, application-owned DOWNSTREAM
mode, and the existing fixed approved Run Type. Do not execute it or enable
automatic startup, schedules, or unattended uncertain-state retries.


------------------------------------------------------------
PREFECT MANUAL MAILBOX REGISTRATION - 2026-08-28
------------------------------------------------------------

Work completed:

- Added bounded_mailbox_flow to prefect.yaml as a second manual-only,
  parameterless deployment on lthhc-local-process with deployment concurrency
  one, CANCEL_NEW, no schedule, no trigger, and no Prefect retries.
- Preserved the one-call application boundary, fixed top 10, application-owned
  DOWNSTREAM review mode, and approved Run Type. Expanded the single Prefect log
  record only with PHI-safe aggregate counts.
- Added a fail-closed, no-argument readiness command whose public output is
  limited to seven category booleans and all_ready. Live dependency probes were
  not executed in this checkpoint.
- Updated the PostgreSQL operator guide with registration, stop conditions,
  exact future manual command, and PHI-safe UI expectations.

Verification:

- Modified Python files compiled successfully.
- Readiness boundary: 5 passed, 0 failed; synthetic deterministic/mock.
- Prefect mailbox boundary: 10 passed, 0 failed; synthetic deterministic/mock.
- PostgreSQL control-plane checks: 7 passed, 0 failed; synthetic deterministic.
- Synthetic Prefect control room: 5 passed, 0 failed. Full mailbox orchestration,
  command, durable idempotency, handling, job recovery, automatic submission,
  partial-success, automatic-write, and submission regressions passed without
  external integration. pip check found no broken requirements.
- Registered lthhc-bounded-mailbox/manual-local against Prefect 3.8.4 on
  PostgreSQL 17.11. Read-only metadata verified the fixed entrypoint, empty
  parameters, no schedules or automations, manual/phi-safe tags, matching pool,
  concurrency one, CANCEL_NEW, and pool concurrency one.
- The registered deployment has zero flow runs. No worker was started and no
  Graph, Smartsheet, OCR/Paddle, Ollama, patient document, or mailbox operation
  ran. Prefect and PostgreSQL were stopped; database environment settings were
  absent after launcher cleanup.

Limitation and exact next start:

- The approved submission-key column setting is currently absent from local
  configuration, so the real-run preflight must fail closed until the operator
  supplies it without exposing its value.
- Obtain separate explicit authorization, start the manual PostgreSQL server
  and exactly one worker, run the boolean-only dependency preflight, require
  every boolean true and zero existing mailbox runs, then trigger exactly one
  manual lthhc-bounded-mailbox/manual-local run with --watch. Do not enable a
  schedule, Prefect retry, automatic startup, second worker, or unattended
  retry of uncertain/non-retryable application state.


------------------------------------------------------------
PREFECT RUNNING-BACKEND READINESS CORRECTION - 2026-08-28
------------------------------------------------------------

Work completed:

- Replaced the readiness probe's client-profile database report with proof
  from the actual running server: API health, database connectivity, server
  version, and the server's non-secret configured database driver.
- Made the PostgreSQL launcher declare its fixed async PostgreSQL driver only
  in the child process environment and remove it during normal or exceptional
  cleanup. The password and complete database URL remain unreported.
- Kept every pool, deployment, zero-run, concurrency, schedule, parameter,
  retry, and single-worker readiness condition unchanged.

Verification:

- Modified Python compiled successfully.
- Readiness preflight: 6 passed, 0 failed; synthetic deterministic/mock. It
  proves a SQLite-reporting client with a PostgreSQL server passes, while an
  actual SQLite server or unproven backend fails closed.
- Mailbox readiness: 10 passed, 0 failed; synthetic deterministic/mock.
- PostgreSQL control-plane: 7 passed, 0 failed; synthetic deterministic.
- Synthetic Prefect control room: 5 passed, 0 failed; no external integration.
- An authorized live boolean-only readiness run returned every category true
  and all_ready true with PostgreSQL, the localhost server, exactly one worker,
  pool concurrency one, and the manual deployment ready.
- No mailbox deployment, mailbox enumeration, Smartsheet write, patient OCR,
  Ollama patient inference, patient-document processing, schedule, or retry ran.

Exact next starting point:

Obtain separate explicit authorization for exactly one operator-controlled
mailbox acceptance. Reconfirm the boolean-only readiness gate immediately
before triggering the single manual deployment run. Do not enable schedules,
Prefect retries, automatic startup, a second worker, or unattended uncertain-
state retries.


------------------------------------------------------------
FIRST MANUAL PREFECT MAILBOX ACCEPTANCE - 2026-08-28
------------------------------------------------------------

Acceptance evidence:

- Started the documented PostgreSQL-backed Prefect server and exactly one
  concurrency-one worker, supplied the approved submission-key setting only
  process-locally, and reran the boolean-only readiness gate.
- All eight readiness booleans were true. The deployment had zero prior runs
  and zero Pending, Scheduled, or Running runs before the trigger.
- Triggered exactly one lthhc-bounded-mailbox/manual-local flow. No second run,
  schedule, Prefect retry, concurrency change, schema change, or manual
  retrigger occurred.
- The single flow and application task reached terminal Failed. The PHI-safe
  application contract reported stage mailbox_processing, sanitized category
  application_boundary_failed, and retryable false.
- The execution environment blocked the required outbound authentication
  connection before mailbox enumeration. Therefore no mailbox enumeration,
  patient-document processing, OCR inference, Ollama inference, Smartsheet
  business write, attachment write, or mailbox handled/read transition ran.
- Aggregate application counts and handled-ordering evidence were unavailable
  because the application boundary did not return a result.
- After evidence capture, the worker, Prefect server, and PostgreSQL were
  stopped. The deployment has exactly one total run and zero active runs.

Exact next starting point:

Perform a PHI-safe infrastructure-only checkpoint that proves the Prefect
worker process can reach the approved authentication service. Do not enumerate
mail, process documents, write Smartsheet, or trigger another deployment run.
Any retry of the failed manual deployment requires separate explicit
authorization after that infrastructure gate passes.


------------------------------------------------------------
PREFECT WORKER AUTH BOUNDARY CORRECTION - 2026-08-28
------------------------------------------------------------

Verified root cause:

- Classified the first acceptance failure as network/service reachability.
  Readiness ran with approved outbound access, while the Prefect worker and its
  flow child ran inside a restricted network boundary.
- Source tracing confirmed both paths used the same repository working
  directory, ignored dotenv/environment credential source, Graph configuration
  loader, authenticator, and application service construction. Configuration
  was present; authentication failed before mailbox enumeration because the
  worker boundary could not reach the approved authentication service.

Correction:

- Added one shared PHI-safe Graph authentication readiness function used by
  both the full readiness command and the worker boundary.
- Added a boolean-only worker authentication check and fail-closed PowerShell
  launcher. The check executes in the same process/network boundary before the
  worker starts; a failed check prevents worker startup.
- Kept credentials in the existing ignored local/process environment boundary.
  No credential, endpoint, identifier, or value enters Prefect parameters,
  deployment metadata, logs, results, or tracked configuration.
- Preserved the parameterless manual deployment, concurrency one, zero Prefect
  retries, application-owned retryability, and existing business boundaries.

Verification:

- Modified Python compiled and the worker launcher parsed successfully.
- Worker auth boundary: 6 passed, 0 failed; synthetic deterministic/mock.
- Prefect readiness: 6 passed, 0 failed; synthetic deterministic/mock.
- Mailbox readiness: 10 passed, 0 failed; synthetic deterministic/mock.
- PostgreSQL control-plane: 7 passed, 0 failed; synthetic deterministic.
- Graph security: 17 passed, 0 failed; synthetic deterministic/mock.
- Full mailbox orchestration: 13 passed, 0 failed; mock.
- Full mailbox command: 12 passed, 0 failed; mock.
- Synthetic Prefect control room: 5 passed, 0 failed.
- No live Graph, mailbox, Smartsheet, OCR, Ollama, patient-document, or Prefect
  mailbox deployment operation ran during this correction.

Exact next starting point:

With separate authorization, run only the new mailbox-worker launcher from a
network-approved process boundary, require its boolean auth gate and worker
health to pass, then stop the worker without triggering the deployment. A
second one-run mailbox acceptance remains blocked until that infrastructure-
only proof passes and receives separate explicit authorization.


------------------------------------------------------------
PREFECT TERMINAL-RUN READINESS CORRECTION - 2026-08-28
------------------------------------------------------------

Work completed:

- Replaced the mailbox readiness gate's zero-history requirement with the
  exact Prefect 3.8.4 terminal state-type contract.
- Allowed only Completed, Failed, Cancelled, and Crashed history. Scheduled,
  Pending, Running, Paused, Cancelling, missing, unknown, malformed, or
  unprovable state remains fail-closed.
- Paginated all deployment history so an active/conflicting run cannot be
  hidden behind terminal history. Every other readiness condition is unchanged.

Verification:

- Modified Python compiled successfully.
- Prefect readiness: 7 passed, 0 failed; synthetic deterministic/mock.
- Mailbox readiness: 10 passed, 0 failed; synthetic deterministic/mock.
- Worker auth boundary: 6 passed, 0 failed; synthetic deterministic/mock.
- PostgreSQL control-plane: 7 passed, 0 failed; synthetic deterministic.
- Live boolean-only readiness returned every category true with one historical
  terminal Failed run, zero active runs, and exactly one healthy worker.
- No mailbox flow, Graph enumeration, Smartsheet write, patient OCR, Ollama
  inference, patient-document processing, schedule, retry, or schema change ran.
- Worker, Prefect server, and PostgreSQL were stopped after evidence capture.

Exact next starting point:

Obtain separate explicit authorization for exactly one replacement manual
mailbox acceptance. Reconfirm the boolean-only readiness gate, require every
category true and zero active/conflicting runs, then trigger one manual run
only. Do not enable schedules, Prefect retries, concurrency increases, or any
automatic/manual retrigger.


------------------------------------------------------------
PREFECT MANUAL ACCEPTANCE GUARD AND STAGE VISIBILITY - 2026-08-28
------------------------------------------------------------

Work completed:

- Recorded the safely cancelled real acceptance: one candidate message, two
  candidate documents, `row_write_pending`, terminal Cancelled, no uncertain
  state, no duplicate business action, and all components stopped.
- Replaced the Prefect adapter's hard-coded `top=10` with explicit manual
  limits of one candidate message and one supported document.
- Added an application-owned pre-processing guard. It requests one additional
  message to prove overflow, reuses the discovered collection, counts supported
  documents from attachment metadata without requesting content, and fails
  closed on exceeded or unprovable counts before attachment download, OCR,
  Ollama, Smartsheet, mailbox completion, or automatic retry.
- Preserved the single bounded Prefect application task, zero Prefect retries,
  application-owned durable state/idempotency/reconciliation, and unchanged
  `row_write_uncertain` / `attachment_write_uncertain` behavior.
- Added PHI-safe stage/timing/attempt/count events for mailbox discovery,
  attachment download, OCR, classification, subtype classification,
  extraction, validation, business rules, Smartsheet row write, attachment
  upload, mailbox completion, downstream review, and completion where reached.

Files:

- src/document_processing/document_processor.py
- src/graph/attachment_service.py
- src/graph/mailbox_processor.py
- src/orchestration/prefect_mailbox_workflow.py
- src/services/mailbox_full_review_orchestration_service.py
- tests/test_mailbox_prefect_readiness.py
- tests/test_prefect_manual_acceptance_guard.py
- docs/prefect_local_control_room.md
- PROJECT_MEMORY.md
- prefect.yaml
- update_project_tracker.py

Verification:

- Modified Python compiled successfully.
- Focused manual-guard and Prefect boundary: 14 passed, 0 failed; synthetic
  deterministic/mock.
- Affected mailbox, attachment, orchestration, recovery, Smartsheet,
  document-processor, worker-boundary, preflight, PostgreSQL-control-plane, and
  Prefect-control-room regressions: 97 passed, 0 failed; synthetic
  deterministic/mock, including one local synthetic Prefect server run.
- No real Graph/mailbox enumeration, protected attachment download, OCR,
  Ollama, Smartsheet, patient-document, mailbox mutation, or mailbox Prefect
  flow ran. Diagnostics and tests used only synthetic values, aggregate counts,
  allowlisted statuses/categories, attempts, and timings.

Limitations:

- The new guarded source has not yet been redeployed or exercised against a
  real mailbox. The cancelled run is operational evidence for the defect, not
  acceptance evidence for the correction.
- Stage events remain inside the existing single application task; internal
  services were not split into Prefect tasks.

Exact next starting point:

Perform a PHI-safe registration/read-only verification checkpoint for the
updated lthhc-bounded-mailbox/manual-local deployment. Verify empty parameters,
no schedule/automation, concurrency one with CANCEL_NEW, one application task,
and zero retries. Do not start the mailbox worker, enumerate mailbox content,
or trigger a real mailbox flow.


------------------------------------------------------------
PREFECT GUARDED DEPLOYMENT READ-ONLY VERIFICATION - 2026-08-28
------------------------------------------------------------

Work completed:

- Reconciled the completed PHI-safe registration/read-only verification for
  lthhc-bounded-mailbox/manual-local at Git commit
  b2d15c71a3f6508803e59e467287c3bbddd98bf9.
- Confirmed that the registered deployment was found with empty parameters,
  no schedule, no automations or triggers, concurrency one with CANCEL_NEW,
  exactly one application task, and zero Prefect retries.
- Confirmed that the mailbox worker was not started, no mailbox flow was
  created, and PostgreSQL plus the Prefect server were stopped after the
  bounded verification.

Files:

- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Narrow static/runtime assertions and deployment-metadata verification
  passed with no discrepancies; real local Prefect/PostgreSQL, read-only.
- Repository history and the clean synchronized Git state support the guarded
  source and registered deployment revision.
- No Graph mailbox enumeration, attachment download, OCR, Ollama, Smartsheet
  write, patient-document processing, mailbox worker, or mailbox Prefect flow
  ran. Only PHI-safe booleans, counts, configuration metadata, and statuses
  were retained.

Limitations:

- The guarded deployment has not yet completed a real mailbox acceptance.
- A real run still requires separate explicit authorization, the documented
  same-boundary worker authentication gate, and every PHI-safe readiness
  boolean to pass immediately before the one allowed trigger.

Exact next starting point:

Obtain separate explicit authorization for exactly one guarded real mailbox
acceptance. Then start only the documented PostgreSQL, Prefect server, and
same-boundary mailbox-worker launcher; require its Graph authentication gate
and every PHI-safe mailbox readiness boolean to pass before triggering the
parameterless lthhc-bounded-mailbox/manual-local deployment exactly once. Stop
without triggering if any gate is false, and do not enable schedules, Prefect
retries, increased concurrency, or any automatic/manual retrigger.


------------------------------------------------------------
GUARDED MAILBOX ACCEPTANCE PREFLIGHT STOP - 2026-08-28
------------------------------------------------------------

Outcome:

- Began the explicitly authorized exactly-one guarded mailbox acceptance from
  clean synchronized Git commit
  299fb68b9f4868f80f41309e06b243b2f7e4c14d.
- Confirmed the static one-message/one-document limits, zero Prefect retries,
  parameterless manual deployment, concurrency one, and CANCEL_NEW.
- Started only the documented PostgreSQL component, Prefect server, and
  same-boundary mailbox-worker launcher.
- The worker Graph authentication gate passed. The full PHI-safe readiness
  result was false because the submission-key column configuration readiness
  boolean was false.
- Stopped before triggering. Deployment-trigger count was zero; no mailbox
  flow was created, no candidate counts were produced, and the acceptance
  guard or application pipeline did not run.
- Stopped the worker, Prefect server, and PostgreSQL and verified all three
  components stopped.

Files:

- PROJECT_MEMORY.md
- update_project_tracker.py

Verification classification and PHI handling:

- Real external integration: same-boundary Graph authentication readiness and
  approved dependency/configuration readiness only.
- Real local integration: PostgreSQL, Prefect server, and one Prefect worker.
- No mailbox enumeration, attachment download, OCR, Ollama processing,
  Smartsheet write, mailbox mutation, patient-document processing, schedule,
  retry, or deployment flow occurred.
- Evidence retained only PHI-safe booleans, component statuses, and a zero
  trigger count. No protected values or identifiers were retained.

Limitation:

- A guarded real mailbox acceptance remains unexecuted because the required
  submission-key configuration gate did not pass. No retry or retrigger is
  authorized by this checkpoint.

Exact next starting point:

Restore the approved Smartsheet submission-key column setting only in the
existing ignored local/process configuration boundary, without exposing or
tracking its value. Run a PHI-safe configuration-only verification proving
that the submission-key column resolves uniquely with the required type. Do
not start PostgreSQL, the Prefect server, the mailbox worker, enumerate mailbox
content, or trigger a flow. Any later guarded real mailbox acceptance requires
new separate explicit authorization and every readiness boolean true.


------------------------------------------------------------
SUBMISSION-KEY CONFIGURATION-ONLY VERIFICATION - 2026-08-28
------------------------------------------------------------

Work completed:

- Confirmed the exact approved submission-key column setting was restored in
  the existing ignored local configuration boundary and became visible to the
  existing configuration service.
- Performed one live columns-metadata-only read through the existing
  Smartsheet destination client.
- Resolved exactly one configured column, verified TEXT_NUMBER type, and
  verified that normalized system-column metadata was absent.

Files:

- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Configuration and schema boundaries: 24 passed, 0 failed; synthetic
  deterministic/mock. No external API was called by these tests.
- Live configuration-only verification passed every required boolean; real
  external read-only Smartsheet columns metadata.
- No Smartsheet row/cell read or write, attachment operation, mailbox access,
  OCR, Ollama, PostgreSQL, Prefect server, worker, or Prefect flow ran.
- The configured title, column identifier, credentials, tokens, provider
  output, and unrelated configuration values were neither printed nor tracked.

Exact next starting point:

Obtain new separate explicit authorization for exactly one guarded real
mailbox acceptance. Then start only the documented PostgreSQL, Prefect server,
and same-boundary mailbox-worker launcher; require its Graph authentication
gate and every PHI-safe mailbox readiness boolean to pass before triggering the
parameterless lthhc-bounded-mailbox/manual-local deployment exactly once. Stop
without triggering if any gate is false, and do not enable schedules, Prefect
retries, increased concurrency, or any automatic/manual retrigger.


------------------------------------------------------------
ACCEPTANCE-ONLY MAILBOX SELECTION POPUP - 2026-08-31
------------------------------------------------------------

Work completed:

- Added a synchronous local Tkinter popup for manual acceptance that receives
  only numbered PHI-safe candidate models, normalized UTC receipt times, and
  deterministically proven supported-document counts.
- Added a separate acceptance-only ingestion path that inspects the newest ten
  unread Inbox messages through metadata, retains the index-to-message mapping
  only in process memory, and never changes normal unattended enumeration.
- Added exact Inbox-scoped re-fetch and re-verification. The selected candidate
  must remain available, unread, identity-matched, and contain exactly one
  supported document. Cancel, invalid/unavailable selection, movement,
  read-state change, and zero, multiple, or unprovable counts fail closed with
  no newest-unread fallback.
- Kept Prefect parameterless with one application task, zero retries,
  concurrency one, and CANCEL_NEW. Business logic remains in the application
  services and the existing durable processing/write/completion path is reused.

Files:

- src/models/mailbox_acceptance.py
- src/ui/mailbox_acceptance_selection.py
- src/graph/email_service.py
- src/graph/mailbox_processor.py
- src/services/mailbox_full_review_orchestration_service.py
- src/orchestration/prefect_mailbox_workflow.py
- prefect.yaml
- docs/prefect_local_control_room.md
- tests/test_mailbox_acceptance_selection.py
- tests/test_graph_attachment_enumeration.py
- tests/test_mailbox_prefect_readiness.py
- tests/test_prefect_postgresql_control_plane.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Verification:

- Modified Python compiled successfully.
- Focused popup, exact-Graph-boundary, and Prefect-adapter checks: 25 passed,
  0 failed; synthetic deterministic/mock.
- Affected mailbox guard, orchestration, handling, persistent idempotency,
  uncertain-write/recovery, Smartsheet, worker, readiness, deployment, and
  control-plane checks: 114 passed, 0 failed, plus the silent durable recovery
  harness with exit code 0; synthetic deterministic/mock/local-state.
- No live mailbox access, attachment download, OCR, Ollama, production
  Smartsheet row/attachment write, worker start, PostgreSQL start, or manual
  mailbox deployment invocation ran. The required project-tracker
  synchronization updated only project-status rows.
  One affected Prefect control-room regression started and stopped its own
  temporary localhost server and completed one PHI-free synthetic wiring flow;
  it did not invoke the mailbox adapter or any external integration.
- Protected synthetic identities were absent from popup models, display rows,
  repr, stdout/stderr, sanitized failures, Prefect parameters, and public
  results.

Limitation:

- The popup-selected source has not been registered or verified against live
  deployment metadata, and no live popup or mailbox acceptance has run.

Exact next starting point:

Perform a PHI-safe registration and read-only deployment-metadata verification
for the popup-selected lthhc-bounded-mailbox/manual-local source. Verify empty
parameters, no schedule or automations, concurrency one with CANCEL_NEW, one
application task, zero Prefect retries, and the acceptance-only newest-ten
metadata discovery boundary. Do not start the mailbox worker, enumerate
mailbox content, display the popup, or trigger a mailbox flow. Stop PostgreSQL
and the Prefect server after the bounded verification.


------------------------------------------------------------
POPUP-SELECTED DEPLOYMENT REGISTRATION VERIFICATION - 2026-08-31
------------------------------------------------------------

Work completed:

- Registered the current committed popup-selected source as
  lthhc-bounded-mailbox/manual-local through the documented manual-only
  Prefect command.
- Verified empty parameters and parameter schema, no schedule, no automations
  or triggers, deployment concurrency one with CANCEL_NEW, the fixed manual
  entrypoint and tags, zero online workers, and no mailbox flow created.
- Proved from current-HEAD source and focused tests that the registered
  entrypoint contains one parameterless flow, exactly one application task,
  zero Prefect retries, newest-ten unread Inbox metadata discovery, exactly-one
  selection/document enforcement, exact Inbox re-verification, no
  newest-unread fallback, guard failure before expensive processing, and
  unchanged normal production enumeration.

Verification:

- Static current-HEAD/parent AST assertions passed every required source and
  architecture boolean.
- Popup, Graph metadata, Prefect adapter, deployment control-plane, and legacy
  guard checks: 36 passed, 0 failed; synthetic deterministic/mock/static.
- Real local Prefect/PostgreSQL deployment registration and read-only metadata
  inspection passed. The two existing historical deployment runs were
  unchanged and zero runs were created on the verification date.
- PostgreSQL and the Prefect server were the only components started and were
  stopped afterward. No worker, mailbox enumeration, popup, attachment
  download, OCR, Ollama, production Smartsheet operation, or mailbox flow ran.

Files:

- PROJECT_MEMORY.md
- update_project_tracker.py

Exact next starting point:

Obtain new separate explicit authorization for exactly one popup-selected
guarded real mailbox acceptance. From a clean synchronized state, start only
the documented PostgreSQL, Prefect server, and same-boundary mailbox-worker
launcher; require the Graph authentication gate and every PHI-safe readiness
boolean to pass; then trigger the parameterless
lthhc-bounded-mailbox/manual-local deployment exactly once. Select exactly one
eligible candidate in the local popup and observe only that run to terminal
state. Cancel, no eligible candidate, or failed exact-candidate re-verification
must stop without fallback, retry, or retrigger. Stop every started component
afterward.


------------------------------------------------------------
POPUP-SELECTED GUARDED MAILBOX ACCEPTANCE - 2026-08-31
------------------------------------------------------------

Work completed:

- Revalidated the clean synchronized source, registered parameterless manual
  deployment, no schedule or automations, concurrency one with CANCEL_NEW,
  one application task, zero Prefect retries, newest-ten metadata discovery,
  exact-candidate re-verification, one-document guard, and no fallback.
- Started only the documented PostgreSQL service, Prefect server, and
  same-boundary mailbox worker. The worker Graph gate and every PHI-safe
  readiness boolean passed.
- Consumed exactly one authorized deployment invocation. Metadata-only
  discovery found zero eligible candidates, so the application failed closed
  at the acceptance guard before displaying the popup or performing any
  expensive or business operation. No retry, fallback, or retrigger occurred.
- Stopped PostgreSQL, the Prefect server, and the worker after the terminal
  Failed state.

Verification:

- Real external integration: Graph authentication and all boolean readiness
  gates passed; the single deployment reached terminal Failed with safe
  category acceptance_no_eligible_candidate.
- Candidate message count was zero and candidate document count was zero. No
  candidate was selected; uncertain write state and duplicate business action
  were absent because row and attachment attempts never began.
- PHI-safe Prefect output exposed mailbox discovery and the terminal acceptance
  guard category. Dedicated candidate-selection and candidate-reverification
  stage events remain absent, so stage visibility is partial.
- No attachment download, OCR, Ollama, Smartsheet write/upload, mailbox
  completion, retry, fallback, or second flow invocation occurred.

Files:

- PROJECT_MEMORY.md
- update_project_tracker.py

Exact next starting point:

Add PHI-safe candidate_selection and candidate_reverification stage events to
the existing acceptance-only application boundary without exposing the
selected identity or changing production enumeration. Cover popup display,
selection/cancel, exact re-verification success/failure, and no-fallback
behavior with synthetic/mock tests; then register and read-only verify the
unchanged parameterless, one-task, zero-retry, concurrency-one CANCEL_NEW
deployment. Do not perform another live mailbox acceptance without separate
explicit authorization and an operator-provided eligible unread Inbox
candidate containing exactly one supported document.


------------------------------------------------------------
POPUP CANDIDATE STAGE OBSERVABILITY - 2026-08-31
------------------------------------------------------------

Work completed:

- Added a PHI-safe popup outcome contract that distinguishes selected,
  cancelled, closed, no-selection, invalid, and unavailable outcomes while
  retaining only the safe candidate ordinal and lifecycle booleans.
- Added candidate_selection events with discovery completion, eligible count,
  popup-displayed, candidate-selected, duration, status, and sanitized failure
  category.
- Added candidate_reverification start/completed/failed events with only safe
  proof booleans for availability, Inbox membership, unread state, exact
  identity match, and exactly one supported document.
- Extended the Prefect stage adapter with explicit allowlisted fields. Normal
  production enumeration, application business logic, durable state,
  idempotency, uncertain-write handling, and mailbox completion ordering were
  unchanged.

Verification:

- Modified Python compiled successfully.
- Focused acceptance-popup, Prefect adapter, Graph metadata, and manual guard
  checks: 32 passed, 0 failed; synthetic deterministic/mock.
- Affected orchestration, handling, persistent idempotency, durable recovery,
  Smartsheet reconciliation, readiness, worker-boundary, and deployment checks:
  90 passed, 0 failed; synthetic deterministic/mock/local-state.
- Protected synthetic identities were absent from events, logs, results, and
  repr output. No live mailbox, popup, worker, flow, OCR, Ollama, or production
  Smartsheet operation ran.
- Registered the updated source through the documented manual deployment
  command. Read-only metadata verification found empty parameters/schema, no
  schedule or automations, concurrency one with CANCEL_NEW, one application
  task, and zero retries. Deployment run count remained three. PostgreSQL and
  the Prefect server were stopped afterward.

Files:

- src/models/mailbox_acceptance.py
- src/ui/mailbox_acceptance_selection.py
- src/graph/mailbox_processor.py
- src/orchestration/prefect_mailbox_workflow.py
- tests/test_mailbox_acceptance_selection.py
- tests/test_mailbox_prefect_readiness.py
- tests/test_prefect_manual_acceptance_guard.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Exact next starting point:

Perform a read-only architecture checkpoint for the smallest PHI-safe
same-boundary pre-invocation candidate handoff. Specify how an operator can
designate one Inbox candidate and prove it remains available, unread, in Inbox,
and contains exactly one supported document before a deployment invocation is
consumed, while binding a later guarded acceptance to that exact candidate
without placing its identity in Prefect parameters, logs/results, tracked or
ignored configuration, or durable project truth. Preserve the popup-only
acceptance path, newest-ten boundary, exact re-verification, no fallback,
one-task/zero-retry deployment, and unchanged production enumeration. Do not
access the live mailbox or trigger another flow without separate explicit
authorization.

Implemented follow-on checkpoint (2026-08-31):

- Added src/services/mailbox_acceptance_handoff_service.py with a fixed-name,
  current-user DPAPI-sealed, exclusive, exactly-15-minute, atomic one-consumer
  acceptance record outside Git, Prefect metadata, environment, and config.
- Split popup preparation from exact preselected-candidate processing. The
  parameterless one-task/zero-retry Prefect adapter now atomically claims the
  handoff and re-fetches only that exact Inbox identity with every proof
  repeated and no enumeration or fallback.
- Added scripts/prepare_mailbox_acceptance_handoff.py and optional
  -PrepareAcceptanceHandoff worker-launch preparation with cleanup.
- Focused and affected tests are synthetic deterministic/mock. A synthetic
  Windows current-user DPAPI roundtrip passed outside the restricted sandbox.
  Protected synthetic identity was absent from ciphertext, filenames, repr,
  logs, results, and exceptions. No live mailbox, popup, flow, OCR, Ollama,
  Smartsheet, or mailbox-completion operation ran.

Exact next start: obtain separate explicit authorization, then run one guarded
live acceptance through -PrepareAcceptanceHandoff and the unchanged
parameterless manual-local deployment. Stop after its first terminal result,
verify one-time cleanup, and reconcile the PHI-safe outcome.

Prefect lifecycle visibility checkpoint (2026-08-31):

- Reused the existing stage-observer boundaries to create PHI-safe Prefect
  lifecycle child task runs without moving or duplicating business logic.
- The UI-visible names cover acceptance handoff, exact candidate
  re-verification, document acquisition, OCR, document classification,
  subtype classification, extraction, deterministic validation, business
  rules, Smartsheet write/attachment, review determination/state, mailbox
  finalization, and workflow completion.
- The parameterless deployment, concurrency one, CANCEL_NEW, zero retries,
  one authoritative application call, write ordering, durable recovery,
  idempotency, uncertain-write handling, and mailbox completion semantics are
  unchanged. Runtime task shape is now the application task plus visibility-
  only child task runs.
- Lifecycle metadata is strictly allowlisted and the DPAPI-protected identity
  cannot enter Prefect inputs, names, logs, results, or exceptions.
- Focused and affected verification was synthetic deterministic/mock. One
  isolated local Prefect synthetic flow completed and its API exposed every
  expected safe task-run name. No live Graph, mailbox, protected document,
  OCR, Ollama, production Smartsheet, popup, or mailbox mutation occurred.

Exact next start: register the updated manual-local source and read-only verify
its unchanged parameterless/no-schedule/concurrency-one deployment metadata
and zero-retry lifecycle source. Do not run the mailbox deployment. Obtain
separate authorization before one guarded real lifecycle-visible acceptance.

Lifecycle-visible deployment registration checkpoint (2026-08-31):

- Registered current reviewed source as lthhc-bounded-mailbox/manual-local
  through the established local PostgreSQL-backed Prefect procedure.
- Read-only API/source verification passed for exact name/entrypoint, zero
  parameters and schema properties, zero job variables, schedules,
  automations/triggers, concurrency one with CANCEL_NEW, zero flow/task
  retries, disabled result persistence, one authoritative application call,
  and the expected lifecycle child-task definitions.
- Deployment run count was three before and after registration. The existing
  worker record was offline and online-worker count remained zero.
- Focused Prefect/deployment/worker/handoff checks: 29 passed, 0 failed;
  synthetic deterministic/mock/static plus real local read-only Prefect API.
- No worker, mailbox/Graph access, popup, handoff preparation, OCR, Ollama,
  production Smartsheet operation, mailbox mutation, or deployment flow ran.
  PostgreSQL and the localhost Prefect server were stopped afterward.

Exact next start: obtain separate explicit authorization for one guarded real
acceptance, start only the documented components, prepare the sealed handoff,
require every readiness/proof gate, invoke the parameterless manual-local
deployment once, watch its lifecycle tasks to terminal, then stop and verify
cleanup without retry, fallback, or retrigger.

Acceptance eligibility aggregate diagnostics checkpoint (2026-08-31):

- Traced the newest-ten unread Inbox eligibility boundary. A message is
  eligible only when metadata shape and identity are valid, isRead is exactly
  false, supported attachment count is provable, and exactly one supported
  non-inline file has PDF/PNG/JPG/JPEG/TIF/TIFF extension.
- Added aggregate-only exclusion counts for not unread, no supported document,
  multiple supported documents, unsupported non-inline document type, and
  unprovable count. No per-message identity or attachment name is retained.
- Added --diagnostic-only to the handoff preparation command. It never displays
  the popup, creates a handoff, starts a worker, or invokes Prefect.
- Eligibility behavior, exactly-one enforcement, no fallback, normal
  production enumeration, and protected-identity boundaries are unchanged.
- Focused/affected synthetic deterministic and mock checks passed. No live
  mailbox/Graph, popup, handoff, Prefect run, OCR, Ollama, production
  Smartsheet, or mailbox mutation occurred.
- A separate Windows handoff-lock contention race found by the affected
  regression was corrected by treating transient PermissionError as bounded
  lock contention; atomic one-consumer behavior remains verified.

Exact next start: obtain authorization for one metadata-only diagnostic and
run the documented prepare_mailbox_acceptance_handoff.py --diagnostic-only
PowerShell command. Use only its aggregate counts to identify the zero-
eligible cause. Do not start a worker or trigger Prefect.

Attachment metadata proof diagnostic checkpoint (2026-08-31):

- The authorized aggregate result isolated one unprovable attachment count,
  but the prior result could not distinguish request, response, item, or name
  failure branches.
- Added aggregate-only, allowlisted reason counts for request, response, item,
  attachment type, inline state, name, pagination link, and continuation
  request failures. No identity, name, URL, payload, or provider detail is
  retained or emitted.
- Corrected the Graph metadata boundary to select only declared attachment
  properties, accept both documented type-annotation spellings, validate type
  and inline state, and follow validated same-host v1.0 continuation links.
  Any ambiguity still fails closed and exactly-one eligibility is unchanged.
- Compilation and focused/affected synthetic deterministic/mock checks passed;
  a synthetic local Prefect lifecycle regression also passed without external
  integrations. No live mailbox/Graph, popup, handoff, OCR, Ollama, production
  Smartsheet, mailbox mutation, worker, or deployment run occurred.

Exact next start: obtain authorization for one repeat metadata-only diagnostic
using prepare_mailbox_acceptance_handoff.py --diagnostic-only. Use only the new
aggregate reason counts to confirm the exact live failure branch after the
Graph response-contract correction; do not start a worker or trigger Prefect.

Slow-stage Prefect performance visibility checkpoint (2026-08-31):

- Extended the existing application-owned stage observer with fixed Prefect
  child-task markers for extraction attempt 1 start/completion, validation
  attempt 1 completion, retry decision, conditional attempt 2 extraction and
  validation, candidate selection, and aggregate document-processing
  completion. No business work moved into Prefect.
- OCR completion maps wall time and selected existing allowlisted OCR timing/
  count diagnostics. Classification and each extraction attempt map wall time
  and the real Ollama total/load/prompt-evaluation/evaluation durations plus
  prompt/evaluation token counts when returned. Missing metrics remain absent.
- Added retry-triggered/raw/validated booleans, selected attempt, attempt count,
  and aggregate extraction/validation/document wall times. Lifecycle logs now
  exclude unpopulated None fields.
- Files: src/document_processing/document_processor.py,
  src/orchestration/prefect_mailbox_workflow.py,
  tests/test_processor_classification_integration.py,
  tests/test_prefect_mailbox_lifecycle_visibility.py,
  tests/test_mailbox_prefect_readiness.py,
  tests/test_ollama_service_lines.py, docs/prefect_local_control_room.md,
  PROJECT_MEMORY.md, and this tracker.
- Focused/affected synthetic deterministic and mock suites passed for one- and
  two-attempt processing, per-attempt validation, both selection outcomes,
  retry behavior, provider mapping, strict metadata allowlisting, lifecycle
  names, one-boundary orchestration, handoff, worker, and mailbox guards. One
  isolated local synthetic Prefect flow completed and exposed the expected
  names; the known non-fatal Windows temporary-database cleanup warning
  occurred after completion.
- PHI handling: only fixed stages/statuses, booleans, nonnegative counts, and
  bounded durations enter visibility. Protected keys/content and provider
  exception text are excluded. No live Graph/mailbox, protected OCR, local
  Ollama, production Smartsheet, popup, handoff, worker, flow deployment run,
  attachment upload, or mailbox mutation occurred.

Exact next start: register the updated lthhc-bounded-mailbox/manual-local
source through the documented PostgreSQL-backed procedure and perform only
read-only deployment/source verification. Prove unchanged zero parameters,
schedule/automation absence, concurrency one with CANCEL_NEW, zero retries and
result persistence, one authoritative application call, the new lifecycle
task definitions, and no new flow run. Do not start a worker or invoke the
deployment; another live acceptance requires separate explicit authorization.

Slow-stage deployment registration checkpoint (2026-08-31):

- Registered the updated lthhc-bounded-mailbox/manual-local source through the
  documented PostgreSQL-backed Prefect procedure. The deployment was not run.
- Read-only verification proved the exact deployment name and entrypoint, zero
  parameters and parameter-schema properties, zero job variables, no schedule,
  no automations/triggers, concurrency one with CANCEL_NEW, zero flow and task
  retries, disabled result persistence, and exactly one authoritative
  application invocation.
- Verified all current slow-stage lifecycle definitions, including OCR and
  classification start/completion, both conditional extraction attempts and
  validations, retry decision, candidate selection, document-processing
  completion, and the existing aggregate extraction and deterministic-
  validation completions.
- Deployment count remained one and flow-run count remained four before and
  after registration. Deployment metadata contained zero checked protected
  identity/payload markers.
- Zero workers had a fresh heartbeat. Prefect retained one historical worker
  record with a stale ONLINE label and a roughly five-hour-old heartbeat; no
  worker was started or stopped.
- Focused control-plane, readiness, and worker-boundary checks: 24 passed, 0
  failed; synthetic deterministic/mock plus real local Prefect/PostgreSQL
  read-only metadata. No handoff, Graph/mailbox, OCR, Ollama, production
  Smartsheet, flow run, attachment upload, or mailbox mutation occurred.
  PostgreSQL was stopped after verification; a pre-existing localhost Prefect
  process was preserved.

Exact next start: obtain separate explicit authorization for one guarded live
acceptance. Start only the documented components, prepare the sealed handoff,
require every readiness and exact-candidate proof gate, invoke the
parameterless manual-local deployment exactly once, and observe the new
PHI-safe slow-stage timing tasks to terminal. Do not retry, fall back, or
retrigger; stop every component started for the run afterward.

Post-reverification zero-document diagnosis checkpoint (2026-08-31):

- Traced the PHI-safe handsome-wolverine outcome from handoff claim through
  successful exact one-document reverification into successful no_documents.
  Absence of the attachment lifecycle marker proves the old source exited in
  one of exactly two pre-download branches: durable already-handled
  reconciliation or a false/missing message attachment flag. Existing output
  did not distinguish them and the protected identity was intentionally
  unavailable; aggregate local state cannot safely prove the historical leaf.
- Fixed the code defect that discarded the exact supported-document proof when
  calling process_message. Selected/preselected acceptance now carries the
  proven count, which overrides only a contradictory message-level attachment
  flag while preserving exactly-one enforcement and no fallback.
- Aligned download type filtering with metadata proof by accepting both legal
  Graph fileAttachment type spellings. A proven document with zero download
  candidates now remains unread and returns a sanitized acquisition failure
  instead of being finalized as successful no_documents.
- Added fixed PHI-safe document-acquisition skip reasons for already-handled,
  false attachment flag, and no download candidate. No identity, filename,
  content, path, payload, or provider detail enters diagnostics.
- Files: src/graph/mailbox_processor.py, src/graph/attachment_service.py,
  tests/test_mailbox_acceptance_selection.py, tests/test_mailbox_handling.py,
  tests/test_graph_attachment_enumeration.py,
  tests/test_mailbox_full_review_orchestration_service.py,
  docs/prefect_local_control_room.md, PROJECT_MEMORY.md, and this tracker.
- Focused preselected, mailbox handling, Graph metadata/download, no_documents,
  durable idempotency/recovery, and Prefect lifecycle checks were synthetic
  deterministic/mock only. No live Graph/mailbox, protected OCR, Ollama,
  production Smartsheet, handoff preparation, deployment run, or mailbox
  mutation occurred during diagnosis or correction.

Exact next start: register the corrected manual-local source and perform the
established read-only deployment/source verification. Do not start a worker or
invoke the deployment. Confirm unchanged parameters, schedule, concurrency,
retries, result persistence, one application invocation, lifecycle definitions,
run count, and zero fresh workers before seeking separate authorization for
another guarded live performance-observability run.

Corrected-source deployment registration checkpoint (2026-08-31):

- Registered the corrected current source as
  lthhc-bounded-mailbox/manual-local through the documented localhost,
  PostgreSQL-backed Prefect procedure without invoking the deployment.
- Read-only metadata verified the exact flow/deployment name and entrypoint,
  zero parameters/schema properties/job variables, no schedule or automation,
  concurrency one with CANCEL_NEW, and zero checked protected metadata markers.
- Static registered-path verification proved zero flow/application/lifecycle
  retries, disabled result persistence, one authoritative application call,
  all lifecycle/performance definitions, and the corrected exact-candidate
  acquisition branches and safe diagnostic categories.
- Deployment flow-run count remained one before and after registration. One
  pre-existing local worker process had a fresh ONLINE heartbeat before and
  after registration; this checkpoint did not start, stop, or mutate it and
  does not claim the requested zero-worker invariant.
- Compilation and 85 focused synthetic deterministic/mock/local-safe tests
  passed. No handoff, Graph/mailbox, protected OCR, Ollama, production document
  Smartsheet operation, attachment upload, mailbox mutation, or deployment run
  occurred.

Exact next start: through the owning operator terminal, stop the pre-existing
online Prefect worker and read-only prove zero fresh workers and unchanged run
count. After separate explicit authorization, use the documented
invoke_prefect_mailbox_worker.ps1 -PrepareAcceptanceHandoff path and invoke the
manual-local deployment exactly once to observe its PHI-safe performance
lifecycle. Do not start a second worker, retry, fall back, or retrigger.

Prefect control-room wrapper checkpoint (2026-08-31):

- Fixed Windows process-tree shutdown after live taskkill /T reported that
  nested Prefect children required force and the wrapper failed closed. The
  wrapper now stores root process-creation identity, proves every descendant's
  PID/parent/creation lineage, stops deepest children before parents, attempts
  graceful exact-PID termination first, and uses /F only after immediate
  identity revalidation. It never applies tree-wide force to an unvalidated
  process set and removes ownership state only after successful shutdown.
- A destructive isolated Windows PowerShell 5.1 test passed with a disposable
  root, multiple children, nested grandchild, already-exited child, and an
  unrelated process that survived. A mock proved graceful failure followed by
  identity-revalidated force. Stale/reused PID rejection also passed. The real
  Prefect control room and PostgreSQL service were inspected read-only only and
  were not stopped or restarted.
- Fixed the live Windows PowerShell 5.1 MethodException in process ownership
  validation. .NET Framework lacks the two-argument
  String.Contains(string, StringComparison) overload; the wrapper now uses
  IndexOf(string, StringComparison) -ge 0 with the same OrdinalIgnoreCase
  semantics and no weakening of PID/command-line proof.
- A real powershell.exe 5.1 isolated function test passed case-insensitive
  ownership, mismatch rejection, and missing-PID rejection. Direct host probes
  confirmed the other flagged wrapper/installer APIs are supported. The live
  Prefect server, PostgreSQL service, workers, and control-room state were not
  mutated.
- Added scripts/install_prefect_control_room_commands.ps1 with an idempotent,
  delimited current-user PowerShell-profile section for startui, status,
  preparerun, runonce, stopworker, restartui, and stopui. Each function invokes
  exactly one approved wrapper action through the verified absolute repository
  path and works from any directory. Existing profile content is preserved.
- An isolated temporary-profile/fake-wrapper acceptance proved idempotency,
  existing-content preservation, fresh-process command availability, exact
  mappings, outside-repository operation, and no accidental action chaining.
  No real user profile or control-room action was used during testing.
- Added scripts/invoke_prefect_control_room.ps1 as the single routine operator
  entrypoint with approved StartUI, Status, PrepareRun, RunOnce, StopWorker,
  StopControlRoom, and RestartControlRoom actions.
- Reused the existing PostgreSQL launcher, mailbox worker/auth/handoff
  launcher, full readiness probe, and exact parameterless deployment command.
  StartUI cannot create a worker or run; PrepareRun cannot run the deployment;
  RunOnce has one watched invocation and no retry, fallback, custom parameters,
  names, tags, or delayed start. StopWorker leaves server/PostgreSQL running;
  control-room stop/restart are worker-guarded maintenance actions.
- Added PHI-safe ignored ownership state containing only component name, PID,
  timestamp, and ownership. Stop requires PID plus command-line ownership proof
  and leaves unrelated or externally started processes untouched.
- Updated docs/prefect_local_control_room.md and PROJECT_MEMORY.md. Static and
  synthetic deterministic tests cover syntax, action separation, duplicate
  prevention, stale PID handling, exact one-run invocation, safe stopping, and
  protected-marker exclusion. A real local read-only Status check covered the
  running PostgreSQL/server and zero-fresh-worker state without mutation.
- No live Graph/mailbox, handoff preparation, popup, worker, deployment run,
  OCR, Ollama, production Smartsheet document operation, attachment upload, or
  mailbox mutation occurred.

Exact next start: keep the reachable PostgreSQL-backed Prefect server/UI
running and use Status for PHI-safe observation. Reconcile any unowned fresh
worker through its owning terminal. Obtain separate explicit authorization
before one guarded PrepareRun, RunOnce, StopWorker sequence; never retry, fall
back, or retrigger. Use StartUI for reboot/crash recovery and StopControlRoom
or RestartControlRoom only for maintenance after the worker is stopped. Stop an
externally owned reachable server in its owning terminal before wrapper-managed
maintenance.

Mailbox acceptance, observability, and operator checkpoint (2026-08-31):

- Reconciled the reviewed DPAPI-sealed single-use handoff, exact candidate
  re-verification, corrected Graph attachment metadata boundary, downstream
  acquisition proof, Prefect lifecycle visibility, and slow-stage OCR/Ollama
  performance observability.
- Confirmed PHI-safe evidence from one real guarded run reaching terminal
  Completed after OCR, classification, extraction, deterministic validation,
  business rules, production Smartsheet row write, attachment upload, review-
  required state, mailbox finalization, and workflow completion.
- Reconciled the simplified control-room wrapper and installed current-user
  commands: startui, status, preparerun, runonce, stopworker, restartui, and
  stopui. After reboot, the operator manually verified start, restart, running
  status, stop, stopped status, and restored start behavior in Windows
  PowerShell 5.1.
- The Prefect UI/control plane remains continuously available; the worker is
  manual. Routine flow is preparerun, runonce, stopworker. StartUI is reboot/
  crash recovery; RestartUI and StopUI are maintenance commands.
- End-of-day verification compiled every modified Python file and passed the
  focused/affected synthetic deterministic, mock, isolated local Prefect, and
  isolated real Windows PowerShell 5.1 checks for handoff, Graph metadata,
  exact-candidate acquisition, idempotency/recovery, lifecycle/performance,
  wrapper, installer, compatibility, and owned process-tree shutdown. Modified
  PowerShell scripts parsed with zero errors.
- No live mailbox/Graph access, popup, worker, deployment run, protected OCR,
  Ollama, production document Smartsheet write/upload, or mailbox mutation was
  performed during this checkpoint.

Exact next start: perform one fresh guarded live mailbox run using the
simplified operator workflow (preparerun, runonce, stopworker) with a newly
eligible document, observe the Prefect slow-stage performance lifecycle through
terminal state, and evaluate PHI-safe OCR/Ollama timing data for optimization
opportunities. Do not perform that live run as part of this checkpoint.

Prefect stage-duration and worker-settlement checkpoint (2026-08-31):

- Replaced misleading immediate started-marker task runs with PHI-free Prefect
  child task runs whose Running-to-terminal lifetime follows the existing
  authoritative application observer boundary for OCR, document/subtype
  classification, extraction attempts 1/2, and validation attempts 1/2.
  Business logic and the one-call application boundary remain unchanged.
- Added a best-effort Workflow Summary task containing only allowlisted
  aggregate counts, review/retry state, attempt selection, stage durations,
  and existing safe Ollama timing/token diagnostics. No protected identity,
  document content, extracted values, paths, payloads, or row IDs can enter it.
- StopWorker now returns a safe heartbeat-settlement result when valid local
  wrapper ownership state proves its recorded process is absent even though
  Prefect briefly reports a fresh heartbeat. Active unowned workers and
  mismatched/reused PIDs still fail closed; unknown processes are never killed,
  and unresolved state is preserved.
- Compiled modified Python and passed focused/affected synthetic deterministic,
  mock, isolated local Prefect, Windows PowerShell 5.1, and isolated real-host
  process-tree checks. No live mailbox/Graph, protected OCR, Ollama, production
  document Smartsheet, worker/deployment, attachment, or mailbox mutation
  operation occurred.

Exact next start: design and implement the unattended Document Processor
operating mode with operator commands startdp, statusdp, and stopdp while
preserving preparerun/runonce/stopworker as the manual recovery/test path.

Unattended Document Processor implementation checkpoint (2026-09-01):

- Implemented a separate parameterless one-candidate unattended Prefect flow,
  application entrypoint, and operator-owned Windows polling launcher. It
  reuses production mailbox processing, exact Inbox re-verification, durable
  idempotency/leases, explicit Smartsheet mappings, review state, mailbox
  finalization, stage visibility, and the PHI-safe Workflow Summary.
- Added startdp/statusdp/stopdp through the existing wrapper and profile
  installer. Named control locking, proven PID/creation/marker ownership,
  manual/live active-run guards, pool/deployment concurrency one, and worker
  limit one prevent duplicate runtimes and overlap. Active-run stop is graceful;
  PostgreSQL, Prefect server/UI, manual workers, and external processes remain
  independent.
- Polling is bounded at one watched invocation followed by five minutes on
  success/no candidate. Nonzero outcomes back off to ten, twenty, then at most
  thirty minutes. Status exposes only safe ownership/readiness/poll state,
  last/next timestamps, failure count, and active/degraded booleans.
- Confirmed existing Graph authentication uses noninteractive MSAL
  confidential-client credentials and can reacquire app-only tokens. The
  boolean-only same-boundary readiness check fails before worker activation;
  no token or credential is persisted in Prefect or wrapper state.
- Renamed active source/config/docs references to prefect-control-room-test,
  document-processor-manual, and document-processor-live. Historical evidence
  was retained. Registered deployments were not mutated in this checkpoint.
- Compiled modified Python and passed focused/affected synthetic deterministic,
  mock, isolated-profile, and isolated local Prefect regressions for selection,
  exact re-verification/no fallback, sequential candidates, no-candidate wait,
  idempotency/recovery, manual/live conflicts, launcher/installer contracts,
  lifecycle visibility, and Workflow Summary safety. All modified PowerShell
  parsed with zero errors in Windows PowerShell 5.1. Twenty wrapper checks
  passed; one real-host process-tree check could not begin because CIM returned
  no identity for its new synthetic root twice (exit 21).
- No live mailbox/Graph, protected OCR, Ollama, production document Smartsheet,
  worker/deployment, attachment, or mailbox mutation operation occurred.

Exact next start: register the renamed parameterless deployments from reviewed
committed source and perform PHI-safe read-only metadata verification for
prefect-control-room-test, document-processor-manual, and
document-processor-live. Then install and verify the updated current-user
command mappings without starting the DP. Obtain separate authorization before
the first guarded live startdp acceptance.

Standardized deployment registration and command installation checkpoint
(2026-09-01):

- Started only the repository-owned PostgreSQL-backed Prefect control room and
  registered prefect-control-room-test, document-processor-manual, and
  document-processor-live through the reviewed deploy-all configuration. No
  worker or deployment run was started; production-server flow-run count stayed
  unchanged at eleven.
- Read-only inspection verified exact qualified flow/deployment mappings,
  lthhc-local-process, zero parameters, zero schedules, zero automations, zero
  active runs, and zero fresh workers. Manual/live concurrency is one with
  CANCEL_NEW. Static/current-source checks preserve zero retries, disabled
  result persistence, the synthetic-only test boundary, manual popup/handoff
  behavior, and operator-owned unattended polling.
- Deleted only the replaced manual-local and phi-safe-local deployment
  registrations. Historical run records were retained. Exactly the three
  standardized deployment names remain active.
- Installed all ten operator functions into the single managed current-user
  profile section. Fresh Windows PowerShell 5.1 resolution proved each exact
  wrapper action. Hash comparison proved all content outside the managed
  section remained byte-for-byte unchanged, including the existing automatic
  Set-Location customization.
- Read-only statusdp reported the DP stopped, no proven DP ownership, stopped
  polling, zero active bounded runs, and zero fresh workers. Focused synthetic
  deterministic, isolated-profile, mock, and isolated local Prefect tests
  passed 21/21. The isolated control-room flow used a temporary server and
  fixed PHI-safe in-memory data only.
- No registered deployment run, live mailbox/Graph discovery, protected OCR,
  Ollama, production document Smartsheet operation, attachment upload, or
  mailbox mutation occurred.

Exact next start: perform the first controlled live unattended Document
Processor acceptance using startdp/statusdp/stopdp, with one newly eligible
unread test document, observe one complete automatic Prefect workflow through
terminal state, verify automatic polling returns to waiting state afterward,
then stop the DP cleanly.

First unattended start failure diagnosis and correction checkpoint
(2026-09-01):

- Proved the failed startdp created the fixed-name unattended worker before the
  full application preflight. The Prefect readiness probe required exactly one
  total worker history record, but the server returned the new online DP worker
  plus an older offline manual record. `postgresql_prefect_ready` therefore
  deterministically failed and the wrapper emitted only its generic error.
- The full preflight unnecessarily constructed Paddle and contacted local
  Ollama/Smartsheet readiness boundaries before waiting. Paddle initialization
  emitted the observed oneDNN messages but processed no document.
- Proven wrapper failure cleanup stopped the owned process tree and removed DP
  ownership state. Prefect's fresh heartbeat briefly outlived the process,
  explaining fresh worker one with dp_running false. Later read-only evidence
  found the fixed worker OFFLINE/stale and no matching live launcher or worker;
  no destructive cleanup was required or performed in this diagnosis.
- Replaced pre-worker full readiness with a categorized lightweight check for
  Graph token acquisition and protected state writability. It runs before any
  DP process/worker creation and cannot enumerate inbox contents, initialize
  OCR, contact Ollama, or inspect Smartsheet. The worker-boundary Graph check
  remains before worker creation. Document dependencies still fail closed in
  the unchanged production processing path.
- Corrected full manual preflight to accept historical offline records while
  requiring exactly one fresh online worker within the established 90-second
  window. Zero, multiple, stale, malformed, and unproven online state fails.
- Added stable multi-line Yes/No status and statusdp output with readable null
  timestamps. Explicit -Json preserves original structured field names. Fresh
  heartbeat settlement without proven DP ownership is now degraded.
- Compiled modified Python, parsed modified PowerShell with zero Windows
  PowerShell 5.1 errors, and passed 78 focused/affected synthetic deterministic,
  mock, isolated-profile, and configuration checks. Twenty-two wrapper checks
  passed; the known disposable real-host CIM test again failed before its
  assertions because the new root identity was unavailable (exit 21).
- No startdp, worker/deployment run, live mailbox/Graph document access,
  protected OCR, Ollama, production document Smartsheet operation, attachment
  upload, or mailbox mutation occurred during correction.

Exact next start: perform a second controlled live startdp acceptance with no
unread document required at startup. Verify the DP enters waiting/polling
state, verify readable status/statusdp output and optional -Json compatibility,
then introduce one newly eligible unread test document and observe exactly one
automatic document-processing run through terminal state before stopping the
DP cleanly.

Startdp progress and bounded-startup checkpoint (2026-09-01):

- Read-only identity, descendant, heartbeat, and polling evidence proved the
  interrupted attempt reached a correctly owned waiting DP runtime. It was not
  an unowned orphan and was not stopped in this checkpoint.
- StartDP's dispatch buffered its output through an outer Write-Output
  expression. Prefect CLI inspections and both Graph-auth subprocess boundaries
  also lacked explicit timeouts.
- StartDP now flushes five PHI-safe stages before slow work, periodically
  reports worker waiting, and emits stable success or fixed failure stage/
  category output. Existing readable status/statusdp and -Json are preserved.
- Prefect CLI and parent/child Graph startup checks are bounded at 30 seconds,
  consistent with the existing Graph transport timeout. Parent cleanup proves
  PID/creation identity. Worker readiness remains bounded at 90 seconds via
  five-second API requests.
- Incomplete/interrupted startup after ownership recording cleans the proven
  DP tree in finally. External/unproven and stale/reused processes remain
  protected.
- Modified Python/tests compiled and modified PowerShell parsed in Windows
  PowerShell 5.1. Focused/affected synthetic deterministic/mock, isolated-
  profile, and isolated local Prefect checks passed. The known disposable host
  CIM fixture remained excluded after the live identity was separately proven.
  No new startdp, worker/deployment start, mailbox/Graph document access,
  protected OCR/Ollama, production document Smartsheet operation, or mailbox
  mutation occurred.

Exact next start: in the owning operator terminal, verify the interrupted DP is
still proven-owned with statusdp and stop it with stopdp before any new start.
Install the committed wrapper mapping if needed, then perform one controlled
no-document startdp acceptance and verify real-time five-stage progress,
waiting status, readable/JSON status compatibility, and clean stopdp. Defer the
one-document acceptance until that startup/stop proof passes.

First unattended document-result diagnosis checkpoint (2026-09-01):

- Read-only safe evidence proved the first unattended document workflow
  completed retry/attempt 2, row and attachment writes, review state, mailbox
  finalization, and return to waiting. Durable state does not retain the
  historical review reason list.
- The attachment matched the AI Submission Key because durable recovery uses
  job_key plus extension as both its exact row key and technical attachment
  reconciliation name. Manual and unattended modes share that path.
- The intended filename policy exists but production assembly remains unwired.
  Current runtime lacks separately validated person-name parts and approved
  payer/service/optional workflow reference lookups. No combined name, sender,
  payer context, or unsupported evidence was reinterpreted to enable it.
- Retry and attempt 2 are operational metadata, not review inputs.
  Classification and field confidence remain separate. Authorization quantity
  independently produces authorization_quantity_requires_verification under
  the existing conservative quantity rule, so 100% classification and high
  field confidence can coexist with recommended review.
- The historical run's full exact reason set cannot be recovered from retained
  safe metadata, so this checkpoint does not claim quantity was its only
  reason.
- Successful authorized-units reconciliation no longer triggers review by
  itself. Smartsheet review reasons now map to fixed, deduplicated PHI-safe
  reason codes rather than generalized manual-review prose; unknown reasons
  reduce to category/cause codes without values or source evidence.
- Focused/affected synthetic deterministic/mock/local-file regressions passed
  for review decisions, retry/confidence independence, reason mapping, filename
  policy/input/builder, naming, recovery, explicit Smartsheet mapping, and
  orchestration. No live mailbox/Graph, OCR/Ollama, deployment, production
  Smartsheet write/upload, or mailbox mutation occurred.

Exact next start: design and implement the production filename-policy assembler
using only independently validated name components and authoritative reference
lookups. Keep the AI Submission Key solely for row/idempotency reconciliation,
provide a deterministic non-PHI fallback, and prove manual/unattended parity
plus restart-safe attachment reconciliation synthetically. Do not perform
another live document run before review and separate authorization.

Production filename assembly checkpoint (2026-09-01):

- Wired the shared manual/unattended recovery path to the existing filename
  policy. It accepts only separately evidenced person components, exact
  authoritative payer/service workbook results, supported dates, and supported
  workflow classification. It never parses combined patient name or uses
  sender, mailbox, filename, or payer context as document meaning.
- Extended extraction with optional separate person components and program;
  prompt and deterministic boundaries require independent source support and
  prohibit combined-name splitting or context inference.
- Complete authorization input preserves the established component ordering
  and date normalization. Unresolved input now produces a clearly labeled,
  full-fingerprint technical fallback with a safe extension. The durable AI
  Submission Key is no longer the normal attachment name.
- Persisted the exact expected attachment name before external row creation in
  ignored protected job state. Legacy state remains readable; restart and
  uncertain-outcome reconciliation compare the same exact name and retain
  duplicate-upload prevention. Only temporary upload copies are renamed.
- Preserved quantity-review, successful-reconciliation, retry/attempt-2,
  classification-confidence, and PHI-safe review-reason corrections.
- Compilation and focused/affected synthetic deterministic/mock/local-file
  regressions passed. No live mailbox/Graph, OCR/Ollama, deployment, production
  Smartsheet write/upload, or mailbox mutation occurred.

Exact next start: register/refresh any affected deployment/source registration
if required, then perform one controlled live unattended document run to verify
the intended Smartsheet attachment filename, PHI-safe specific review reason
output, Workflow Summary, and clean return to waiting state.

Validated confidence/source-support consistency checkpoint (2026-09-01):

- Confirmed the committed scalar-field production threshold is >=0.85 and the
  0.95 constant is the extraction-confidence cap, not the review threshold.
  Exact equality at any configured threshold passes. Classification confidence
  remains separate and is never substituted for field confidence.
- Deterministic invalidation now retains original candidate evidence only in
  the protected review contract while validated value/confidence become
  null/zero. Unsupported service-line components retain protected candidate
  evidence but remain null in validated row state.
- Production mapping now emits numeric confidence only beside an accepted
  validated value. Missing, unsupported, invalidated, and below-threshold
  values leave production value/confidence blank; displayed minimum confidence
  uses only mapped validated fields.
- Service-line review reasons now retain component scope instead of collapsing
  to misleading top-level or document-details categories. Modifier ownership
  has its own fixed safe code. Quantity-meaning verification remains independent
  of source support and confidence.
- Added PHI-safe field and filename-readiness diagnostics containing only
  categories, booleans, confidences, thresholds, statuses, and safe reason
  codes. Unsupported required filename evidence still produces the technical
  fallback; restart-safe naming reconciliation is unchanged.
- Focused/affected synthetic deterministic/mock tests passed without live
  mailbox/Graph, protected OCR/Ollama, deployment execution, production
  document Smartsheet write/upload, or mailbox mutation.

Exact next start: refresh registration/source if required, then perform one
controlled unattended live document run to verify validated Smartsheet values
and confidences are internally consistent with deterministic source-support/
review reasons, verify business filename versus technical fallback behavior,
verify Workflow Summary, and confirm clean return to waiting before stopdp.

Smartsheet action visibility checkpoint (2026-09-01):

- Added fixed PHI-safe row actions for created, reconciled-existing, skipped,
  and failed outcomes, plus attachment actions for uploaded,
  reconciled-existing, skipped, and failed outcomes. Already-completed durable
  jobs now report intentional skips; exact existing-state matches found during
  the current attempt report reconciliation.
- Replaced generic Smartsheet lifecycle labels with action-specific Prefect
  task labels. Workflow Summary now includes row/attachment actions, both
  durable external-attempt counters, written/failed counts, completed document
  count, and final status without external IDs or document data.
- Corrected `written_count` so reconciliation/no-op does not count as a newly
  created row. Corrected lost-response row reconciliation so the durable row
  attempt counter records the create call that actually occurred. Attachment
  attempts remain upload-call-only.
- Focused and affected synthetic deterministic/mock tests covered new writes,
  uploads, exact reconciliation, completed-state skips, lost responses,
  counter behavior, PHI-safe Prefect visibility, and unchanged duplicate and
  recovery protections. No live mailbox/Graph, protected OCR/Ollama,
  deployment, production Smartsheet write/upload, or mailbox mutation ran.

Exact next start: perform one controlled unattended live run with a different
document to verify full OCR/extraction/validation behavior, validated
Smartsheet value/confidence consistency, business filename versus technical
fallback, specific review reasons, Workflow Summary action states, and clean
return to waiting before stopdp.

Review-state and business-filename resolution checkpoint (2026-09-01):

- Added deterministic accepted/not-present/missing-required/low-confidence/
  unsupported/conflicting/ambiguous/invalid field states without treating all
  extraction-schema fields as business-required. Existing authorization rules
  remain the requiredness authority.
- Optional absent evidence no longer receives a validated zero-confidence
  entry or generates source-support/low-confidence review noise. Unsupported
  candidates remain preserved only in the protected review contract.
- Corrected service-line low-confidence review to use original candidate
  confidence rather than the safety downgrade caused by an unsupported child.
  Smartsheet review reasons now use concise human-readable PHI-safe phrases;
  fixed technical categories remain available for diagnostics.
- Added ambiguity-safe authoritative payer/service lookup across omitted
  optional key/modifier/program dimensions and aligned date readiness with the
  established single-date-or-range filename policy. The local ignored
  reference cache passed count/boolean-only schema validation.
- Workflow Summary now exposes only safe filename component readiness,
  qualifier state, business/fallback result, review reason count, and fixed
  reason categories. Focused and affected synthetic deterministic/mock/local-
  file tests passed without live mailbox/Graph, protected OCR/Ollama,
  deployment, production Smartsheet document write/upload, or mailbox mutation.

Exact next start: refresh source/deployment registration if required, then
perform one controlled unattended live run with a different document to verify
optional absent fields do not trigger review, accepted confidence aligns with
review reasons, Smartsheet AI Review Reason is human-readable and concise,
filename readiness is visible, business filename resolves when all required
evidence exists, Workflow Summary is accurate, and DP returns cleanly to
waiting.

AI Correction human-feedback mapping checkpoint (2026-09-01):

- Added the exact `AI Correction` production mapping as a create-time false
  checkbox. The value is deliberately independent of AI review status,
  reasons, review-required state, and confidence.
- Configuration now requires the destination column to exist and have
  `CHECKBOX` type while continuing to resolve its identifier from live schema
  metadata rather than source code.
- Exact-row reconciliation, restart recovery, completed-state no-op, and
  attachment reconciliation retain their existing no-row-update behavior and
  therefore preserve both checked and unchecked human feedback. No comments or
  Conversations API behavior was added.
- Focused and affected synthetic deterministic/mock mapping, configuration,
  destination, write, recovery, orchestration, and Prefect visibility tests
  passed without live Smartsheet, Graph/mailbox, protected OCR/Ollama,
  deployment, production attachment, or mailbox mutation.

Exact next start: refresh source/deployment registration if required, then
perform one controlled unattended live run with a different document to verify
AI Correction initializes unchecked, optional absent fields do not trigger
review, accepted confidence aligns with review reasons, AI Review Reason is
human-readable and concise, business filename resolves when supported,
Workflow Summary is accurate, and DP returns cleanly to waiting.

Final-state consistency and quantity-unit checkpoint (2026-09-02):

- Replaced generic aggregate extraction-confidence review with final-field-
  specific reasons. Missing confidence no longer becomes a synthetic 0%
  minimum, accepted >=0.85 fields remain accepted, and optional absence stays
  blank without confidence/review noise.
- Prevented redundant singular service-code validation/confidence noise from
  contradicting an accepted plural production service-code field. Required
  authorization-status absence is now recognized as missing, and naming lookup
  failures remain scoped to filename resolution.
- Added explicit authorization-unit extraction/validation and provenance.
  Supported explicit Hours/Units/Visits/Sessions are preserved; silence applies
  business-default Hours; unsupported/ambiguous/conflicting explicit claims
  fail closed. The approved quantity cell renders the unit without implying
  approval or changing quantity confidence.
- Removed unconditional renewal workflow verification because accepted
  authorization+renewal already resolves `RENEW AUTH` under committed policy.
  Successful units reconciliation remains informational.
- Added safe filename failure category, top-level validated service identity
  support, and final validation/quantity/unit counters to Workflow Summary.
  Focused and affected synthetic deterministic/mock tests passed without live
  mailbox/Graph, protected OCR/Ollama, deployment, production Smartsheet
  document/comment operation, or mailbox mutation.

Exact next start: refresh registration/source if required, then perform one
controlled unattended live run with a different document to verify accepted
production fields and confidences match final validation/review state, quantity
defaults to Hours when no explicit unit is present, AI Review Reason is concise
and actionable, business filename resolves when supported, Workflow Summary
diagnostics are accurate, AI Correction initializes unchecked, and DP returns
cleanly to waiting.

Unified optional-absence and graceful filename checkpoint (2026-09-02):

- Made authorization end date optional in the shared requiredness model and
  authorization rule. Optional absence remains blank without confidence or
  review, while a present unreliable candidate continues to fail closed.
- Preserved authorization subtype `unknown` as a valid final classification
  with one specific recommended-review reason and independent category
  confidence. Unknown subtype no longer blocks filename construction or
  invents a workflow token.
- Added final-state metadata to the protected review field contract and made
  production mapping accept only final `accepted` fields. Removed all textual
  missing/cleared confidence sentinels from production cells.
- Business naming now requires only supported person first/last, authoritative
  payer, one supported date, and a safe extension. Optional middle, service,
  form, workflow, and qualifier components degrade by omission. Safe original
  PDF/TIF/TIFF/PNG/JPG/JPEG extensions are preserved.
- Filename assembly consumes final validation state instead of repeating raw
  source substring checks, keeps independently valid service-line siblings,
  and never recomputes a durable expected attachment name during recovery.
- Added PHI-safe Workflow Summary naming-attempt, required-failure,
  optional-omission, result/failure-category, and component-state fields.
  Focused and affected synthetic deterministic/mock tests passed without live
  mailbox/Graph, protected OCR/Ollama, deployment, production Smartsheet or
  comment operation, or mailbox mutation.

Exact next start: refresh registration/source, then perform one controlled
unattended live run with a different document to verify optional end-date
absence remains blank without review, unknown subtype (if produced) has only
the specific subtype reason without changing category confidence, optional
filename components are omitted without technical fallback, required filename
failures remain fail-closed, Workflow Summary naming counts/states are
accurate, quantity/unit and AI Correction behavior remain correct, and DP
returns cleanly to waiting.

Subtype presentation and exact filename-decision checkpoint (2026-09-02):

- Corrected the generic review presenter that treated subtype as a legacy
  request-type alias. Supported unknown-subtype reasons now deduplicate to the
  fixed safe code `document_subtype_unknown` and exact operator-facing text
  `AI Document Subtype: Unknown`; document-category confidence remains
  independent.
- PHI-safe read-only prior-run evidence proved business naming was attempted
  and the exact fallback was `payer_reference_unresolved`. Production keeps
  exact authoritative lookup fail-closed and does not guess a mapping.
- Filename assembly now invokes the approved policy for every valid new
  Document, evaluates required person/payer/date/extension readiness
  independently, and derives the attachment decision and Workflow Summary
  diagnostics from the same result. Optional component omission cannot set a
  fallback flag.
- Resumed jobs report the durable business/technical filename decision already
  stored for reconciliation rather than a contradictory recomputed result;
  persisted technical fallback uses a fixed safe category and is never renamed.
- 2067 naming prefers a supported posted date and may use the existing
  supported single-date/range path when posted date is absent. Safe extension
  readiness and exact required-failure counts are now visible without values.
- Compilation and 31 focused/affected synthetic deterministic/mock/local-safe
  test scripts passed. Isolated Prefect tests used temporary synthetic flows;
  no live mailbox/Graph, protected OCR/Ollama, production Smartsheet document
  or comment operation, deployment/worker start, or mailbox mutation occurred.

Exact next start: refresh deployment/source registration and confirm the
approved authoritative payer reference contains the intended test payer
mapping without exposing its value, then perform one controlled unattended
live run with a different document. Verify exact unknown-subtype presentation,
optional omission, required-failure categories and counts, extension readiness,
final filename decision, AI Correction, and clean return to waiting before
stopdp.

Current-source registration and payer-readiness checkpoint (2026-09-02):

- Refreshed all three standardized deployments from clean committed HEAD
  `5e47350db37e2996b393aab57aa4e2ae1fcc6d63` with the installed Prefect 3.8.4
  repository mechanism. Registered versions changed; exact entrypoints, pool,
  current-repository pull steps, empty schedules/parameters, and manual/live
  concurrency-one `CANCEL_NEW` contracts passed PHI-safe verification.
- Registration created no flow run. Direct API verification found zero active
  runs for every deployment and zero fresh workers; the unpaused process pool
  retains concurrency one and is expectedly not ready without a worker.
- The ignored last-known-good reference cache and metadata loaded successfully
  with nonzero payer/service mappings. No approved local input supplied the
  intended test payer, so no exact lookup was possible: evidence is unavailable,
  match count is zero, and resolution is `unavailable`. This is not yet proof
  of a reference-data gap or application defect.
- No live mailbox/Graph document or reference download, OCR/Ollama, deployment
  run, worker startup, Smartsheet/comment operation, or mailbox mutation ran.

Exact next start: provide the intended test payer through an approved
local-only non-logged input and run the exact authoritative cache lookup with
only safe readiness/cardinality output. Proceed to one controlled unattended
live document run only after one unique match; otherwise correct only the
authoritative workbook and refresh the last-known-good cache first.

Intake-team filename vocabulary and placeholder checkpoint (2026-09-02):

- Replaced the former workflow-oriented filename contract with the observed
  intake target `<LAST, FIRST [MIDDLE]>_<PAYER>_[SERVICE]_<DOCUMENT TYPE>_<DATE[-DATE]>.<EXT>`.
  Every new document attempts composition. Complete business, partial business,
  and technical fallback are explicit outcomes.
- Added one centralized canonical document-type/subtype vocabulary. Supported
  authorization tokens include INIT, NO CHANGE, INCREASE, DECREASE, TERM, STUB,
  INBOUND, GAP FILL, NEW SVS, MOD CHANGE, RPM, READMIT, TASKS ADDED, and RESUME
  SVS. `INBOUND AUTH` canonicalizes to `AUTH INBOUND`; INIT remains unavailable
  without authoritative external context and is never inferred from legacy
  initial/renewal routing.
- Added fixed placeholders for unresolved payer, expected service, document
  type, authorization subtype, and date. Optional absence is omitted. Technical
  fallback is limited to unresolved independent first/last identity,
  unsupported extension, or unsafe composition.
- Production filename assembly uses only final validated evidence and exact
  authoritative reference resolution. Unknown authorization subtype becomes
  `AUTH [SUBTYPE]` and exactly one operator-facing review reason,
  `AI Document Subtype: Unknown`, without changing category confidence.
- The exact attachment name and fixed-safe decision diagnostics are persisted
  before an external row attempt. Recovery and reconciliation reuse that name
  and never recompute it; AI Submission Key remains internal to idempotency and
  reconciliation.
- Workflow Summary now reports complete/partial/technical result, document type
  and subtype readiness, placeholder count/categories, omission count, and a
  fixed technical fallback reason without values. Manual and unattended modes
  share the same processor and recovery boundary.
- Modified the filename policy/builder/assembly/naming/recovery services,
  document and taxonomy models, extraction/validation/review/Smartsheet layers,
  Prefect summary, and corresponding deterministic/mock tests. Twenty-one
  focused and affected test scripts passed, including 283 explicitly reported
  assertions plus the silent recovery suite. Modified Python compiled. Tests
  used only synthetic data, mocks, local temporary files, and isolated
  temporary Prefect servers; external integrations were not called.
- No live mailbox/Graph, protected OCR/Ollama, deployment/worker, production
  Smartsheet document/comment, or mailbox mutation occurred. Real recognition
  coverage and authoritative-reference outcomes still require the next
  controlled live acceptance.

Exact next start: refresh all affected Prefect deployment/source registrations
from the committed intake-naming source, then perform one controlled unattended
live run with a different document to verify complete versus partial business
filename behavior, fixed placeholders and Workflow Summary diagnostics, exact
AI Document Subtype presentation/review, AI Correction initialized unchecked,
action-specific Smartsheet lifecycle states, and clean return to waiting before
stopdp.

Final-state review scoping and presentation checkpoint (2026-09-02):

- Made final validated field state and explicit business requiredness the sole
  source of extraction review. Partial-business payer, service, date, document-
  type, and subtype placeholders remain filename/Workflow Summary diagnostics
  and no longer generate review by themselves.
- Centralized authorization subtype review ownership in the final intake naming
  subtype. Unknown produces exactly `AI Document Subtype: Unknown`; supported
  intake state supersedes an unknown legacy routing subtype without changing
  category confidence. Legacy `request_type` remains protected internal
  evidence and is excluded from operator reasons, displayed minimum confidence,
  and final-state counts.
- Smartsheet-facing presentation now uses fixed `<Business Field>: <Problem>`
  wording. Specific start-date and service-line conditions supersede broad
  missing/generic wording, and filename reference failures cannot masquerade as
  extraction-validation failures.
- Successful supported service-line quantity reconciliation now supersedes the
  earlier top-level source failure and broad missing-quantity action in final
  diagnostic, review, and Smartsheet mapping state. Genuine service-line
  failures remain reviewable with service-line scope.
- Existing filename persistence/recovery, duplicate prevention, manual/
  unattended parity, AI Correction human ownership, and comments boundaries
  remain unchanged. Modified Python compiled and focused/affected synthetic
  deterministic/mock/local-safe tests passed, including isolated local Prefect
  visibility. External integrations were not called and no protected values or
  identifiers were logged.

Exact next start: refresh all affected Prefect deployment/source registrations
from the committed review-scoping source, then perform one controlled unattended
live run with a different document. Verify accepted production values and
confidences have no contradictory review reason, partial-business placeholders
remain naming-only diagnostics, unresolved applicable subtype produces exactly
`AI Document Subtype: Unknown`, specific required/date/service-line reasons and
Workflow Summary categories are accurate, AI Correction initializes unchecked,
and the DP returns cleanly to waiting before stopdp.

Smartsheet uncertain-row recovery checkpoint (2026-09-03):

- Retained PHI-safe durable evidence proves one application row-create attempt,
  no proven row identity, and zero attachment attempts. The prior recovery path
  performed exact-key reconciliation after the unconfirmed result but collapsed
  zero matches and reconciliation unavailability into one non-retryable unknown
  state; retained evidence cannot prove wire-level issuance or distinguish a
  transport exception from an unusable success response.
- Added a leased durable row-create-in-flight boundary and fixed reconciliation
  states. Confirmed creation reports created; one exact match reports reconciled;
  multiple matches block; unavailable reconciliation remains reconcile-only;
  authoritative zero matches become retry-ready. A later bounded same-job cycle
  must lease and reconcile zero again before any new create, preventing blind
  duplicate writes and avoiding a document resend.
- Added a default 30-second Smartsheet HTTP send timeout with a positive numeric
  environment override and fixed safe API-rejected, timeout, invalid-response,
  and uncertain-outcome categories. The legacy direct retry path now blocks
  uncertain row outcomes; durable exact-key mailbox recovery owns re-entry.
- Row/attachment attempt counters represent application external-call attempts;
  reconciliation does not inflate them. Attachment handling remains blocked
  until row identity is proven. Prefect and Workflow Summary now expose safe
  create-attempt, outcome-proof, reconciliation-cardinality, recovery-state,
  attachment-blocked, retryable, and recoverable semantics.
- Python compilation and focused/affected synthetic deterministic, mock,
  temporary durable-state, and isolated local Prefect tests passed. No live
  mailbox/Graph, protected OCR/Ollama, production Smartsheet action,
  deployment/worker start, attachment upload, comments access, or mailbox
  mutation occurred.

Exact next start: refresh the affected deployment/source registration, then
perform a controlled recovery of the existing durable uncertain mailbox job
without resending the document. Verify exact reconciliation first; after an
authoritative zero-match result, allow at most one later leased same-job create,
keep attachment blocked until row identity is proven, confirm Prefect/Workflow
Summary recovery states and safe mailbox finalization, and return the DP to
waiting before stopdp.

Typed Smartsheet row contract and API-rejection recovery checkpoint
(2026-09-03):

- Fixed the structural defect that allowed optional nulls and values without a
  proven destination-type contract to reach Cell construction. Optional absence
  is omitted; serialized Cells require non-null values. CHECKBOX is boolean-only,
  DATE is normalized ISO date text, and TEXT_NUMBER is limited to explicit text,
  integer, and finite-float scalars. Containers, arbitrary objects, Decimal/date
  objects, text-column booleans, and non-finite numbers fail locally. AI
  Correction remains literal false while text review flags use Yes/No.
- Added destination type and system/writable metadata validation, duplicate-
  destination and strict column-ID checks, aggregate PHI-safe diagnostics, and
  fixed API-rejection metadata. No response body, request payload/value, row ID,
  exception text, token, or sensitive response field is retained.
- Added request contract version 2 and durable state schema version 3. The same
  durable job may re-arm only once from an older contract. Every v2 attempt
  reservation requires a lease, exact zero-match reconciliation, and successful
  mapping/schema/type evidence. One match reconciles existing; multiple or
  unavailable reconciliation fails closed; attachments remain blocked until row
  identity is proven; direct retry cannot bypass durable recovery.
- Modified Python compiled. Focused and affected synthetic deterministic/mock,
  local temporary-state, adjacent Smartsheet/mailbox, and isolated local Prefect
  checks passed. No startdp, worker/deployment run, mailbox/Graph access,
  protected OCR/Ollama, production Smartsheet document/comment operation,
  attachment upload, or mailbox mutation occurred.

Exact next start: refresh the affected Prefect deployment/source registrations
from the committed typed-row source, then perform one controlled recovery of the
existing durable row-write API-rejected job without resending. Reuse its exact
durable identity and reconcile first: one match reconciles existing, multiple or
unavailable fails closed, and zero permits at most one leased contract-v2 create.
Verify typed diagnostics, duplicate prevention, attachment gating, mailbox
finalization, and clean return to waiting before stopdp.

Successful typed-contract recovery and DP Training checkpoint (2026-09-03):

- The controlled unattended recovery reused the exact durable job identity and
  completed the typed-contract row, attachment, and mailbox lifecycle without a
  duplicate. Business naming succeeded; category 2067, intake subtype unknown,
  exact review reason `AI Document Subtype: Unknown`, independent classification
  confidence, blank optional unavailable fields, unchecked AI Correction, and
  absence of the misleading sentinel were confirmed using PHI-safe facts only.
- Implemented the distinct parameterless `document-processor-training` Prefect
  service with `lthhc-dp-training`, a dedicated process pool/worker, concurrency
  one and `CANCEL_NEW`, no schedule, zero retries, disabled result persistence,
  and exact `startdptraining`/`statusdptraining`/`stopdptraining` commands. The
  health port and process ownership boundaries permit independent live DP and
  Training operation.
- Extended the existing feedback seed with exact seven-column validation,
  least-privilege flagged-row/context reads, paginated comment checkpoints,
  attachment exclusion, DPAPI-sealed one-row/one-case durability, strict
  taxonomy/status transitions, proposal/result generations, stale approval
  protection, write reconciliation, reopen/retest handling, and exact four-field
  workflow write authority.
- Added schema-constrained tool-free local analysis and a deterministic PHI-safe
  Codex task boundary. One valid proposal approval permits one bounded ephemeral
  implementation process only after clean/synchronized Git and repository-lock
  checks; no retry/resume or destructive workspace cleanup exists. A distinct
  human result approval is required after real retest.
- Metadata-only registration produced exactly the four intended deployments on
  current committed local source, zero schedules/automations/active target runs,
  and a concurrency-one training pool with no worker. A real PowerShell 5.1
  `-File` profile-installer acceptance exposed and fixed deferred repository-root
  resolution before the profile was changed. Real `statusdptraining` acceptance
  also fixed duplicate-case process `PATH` inheritance and safe fast-child-exit
  handling, then returned ready `schema_only`, stopped, zero workers/runs/cases,
  and not degraded without starting DP Training.
- Compilation, PowerShell 5.1 parsing, focused correction/command/readiness/
  DPAPI tests, affected Smartsheet mapping/write/recovery/idempotency suites, and
  isolated Prefect lifecycle/control-wrapper checks passed using synthetic,
  mock, or local-safe data. No live Smartsheet row/comment read or correction
  mutation, protected OCR/Ollama, mailbox operation, worker start, or deployment
  invocation occurred.

DP Training read-only activation preparation (2026-09-03):

- Set only `DP_TRAINING_MODE=read_only` through the existing ignored `.env`
  protected-local configuration mechanism. Smartsheet-write and Codex-dispatch
  gates remain absent/disabled.
- PHI-safe readiness and `statusdptraining` resolved `read_only` while the
  service remained stopped with zero training workers/active cycles and no
  degraded state. No row or comment enumeration occurred.
- Sixty-seven focused synthetic deterministic/mock/local-safe checks proved
  seven-column validation, least-privilege discovery, literal-checkbox handling,
  paginated attachment-free comments, one DPAPI-sealed case per row, unchanged-
  input idempotency, same-case comment-generation updates, and no write, human-
  checkbox mutation, or Codex path in `read_only` mode.
- No production row/comment was read, no Smartsheet or mailbox state was mutated,
  no protected Ollama analysis ran, and no worker/deployment was started.

Exact next start: perform one controlled live `read_only` DP Training acceptance
against one intentionally flagged `AI Correction` row. Start DP Training, verify
exactly one protected correction case is discovered/updated, verify row/comment
content remains local/protected, verify no Smartsheet correction-field writes
occur, verify no Codex dispatch occurs, verify PHI-safe Prefect/status counts,
then stop DP Training cleanly.

DP Training capability-mode propagation correction (2026-09-03):

- Proved the status path loaded protected `.env` in a short readiness child while
  the launcher/worker did not receive that environment. The application then
  captured its silent `schema_only` default before the Smartsheet client loaded
  dotenv, exactly explaining the observed `schema_ready` cycle. Registered
  deployment parameters and job variables remained empty; installed Prefect
  process-worker source confirmed normal worker-environment inheritance.
- Added a shared absolute-path protected capability loader, explicit required
  mode validation, startup-frozen mode/gate fingerprint, owned-worker inheritance,
  per-cycle file/runtime comparison, and fail-closed safe mismatch categories.
  Capability changes now require a DP Training restart and cannot hot-escalate.
- `startdptraining` verifies the application-visible safe mode before activation.
  `statusdptraining` now distinguishes configured and runtime/effective modes and
  their match. Prefect summaries add only the safe effective mode; the deployment
  remains parameterless with no job variables.
- Focused and affected synthetic deterministic/mock/local-safe checks passed for
  configuration, all four capability modes, readiness, command ownership,
  PowerShell 5.1, DPAPI protection, Smartsheet mapping/write/recovery, mailbox
  idempotency/orchestration, and isolated Prefect lifecycle behavior. The real
  stopped-service status check showed configured `read_only`, runtime
  `not_running`, zero workers/active cycles, and no degraded state.
- No production row/comment read, Smartsheet mutation, Codex dispatch, mailbox
  operation, protected OCR, or Ollama operation occurred during implementation.

Exact next start: perform one controlled live `read_only` acceptance against the
existing flagged row. Prove configured/runtime mode agreement before polling,
exactly one protected case discovery/update, no correction-field write, no Codex
dispatch, PHI-safe Prefect/status output, and clean `stopdptraining` settlement.

DP Training read-only acceptance and proposal-write preparation (2026-09-04):

- The operator-confirmed live read-only acceptance proved matching configured
  and effective mode, exactly one flagged case, protected case creation/update,
  no correction-field write, no Codex dispatch, no failure, and clean return to
  waiting.
- The retained case has one durable validated proposal generation and zero
  implementation attempts, job identities, or consumed approval generations.
  It is durably marked historical acceptance input and cannot authorize an
  implementation even in a later dispatch-capable mode.
- Corrected mode-promotion behavior so proposal-write publishes the unchanged
  durable validated generation without reanalysis or a duplicate generation;
  exact unchanged readback makes a later cycle reconciliation-only.
- Restricted approval authorization and implementation-job creation to
  approval-dispatch. Proposal-write cannot consume approval, create a job, or
  launch Codex. Historical output carries fixed current-state/retest guidance
  rather than claiming the earlier issue remains in current code.
- Protected mode is proposal-write, Smartsheet writes are enabled, and Codex
  dispatch is explicitly disabled. PHI-safe readiness and stopped-service status
  passed with zero training workers. Focused and affected tests were synthetic,
  mock, protected-local-state, or isolated local Prefect only. No production row
  or comment was read and no Smartsheet/mailbox mutation occurred.

Exact next start: perform one controlled live proposal-write DP Training
acceptance against the existing historical flagged case. Verify one validated
proposal/type/status generation, exact-four-field workflow ownership, preserved
human controls/comments, zero Codex dispatch, and unchanged-second-cycle
idempotency. Do not approve implementation for this historical case.

Shared Document Processor business context and correction-analysis v2
checkpoint (2026-09-04):

- Added one PHI-free immutable business-context version 1 and deterministic
  role-specific views for live classification, both extraction attempts,
  structural learning, intake naming, and DP Training. Existing taxonomy,
  naming, validation, confidence, quantity/unit, filename, review, correction,
  and external-dependency constants now derive from the shared structured source
  where they previously duplicated the same business truth.
- Correction analysis contract version 2 separates clear desired behavior from
  technical/root-cause certainty. It adds controlled primary/related types,
  technical disposition, feedback relationship, and structural filename/subtype
  concepts. Latest reviewer clarification is presented separately from prior
  history and may coherently narrow it; old AI proposal text is never evidence.
- Deterministic symptom-first validation maps filename composition failures to
  primary `Filename` and retains `Document Subtype` as a protected related type.
  Proposals are rendered from controlled concepts only. Reviewer values cannot
  become production evidence. `AUTH DECREASE` may use explicit validated
  document evidence, while `AUTH INIT` remains an authoritative external-system
  dependency.
- Protected correction-case schema version 2 migrates version 1 in place and
  retains durable identity/comment checkpoints. One unchanged active older-basis
  case may reanalyze exactly once under analysis contract v2/business context v1,
  create one new proposal generation, invalidate stale approvals, and become
  idempotent. Proposal-write still cannot dispatch Codex.
- Sanitized implementation task/result versioning now requires controlled
  generalized concepts, durable-layer reporting, shared-context assessment,
  context-version verification, synthetic regressions, and PHI/generalization
  prohibitions. Local AI never mutates business context.
- Modified Python compiled. Focused and affected synthetic deterministic/mock,
  protected-local-state, PowerShell 5.1, Smartsheet boundary, and isolated local
  Prefect checks passed. No live Smartsheet row/comment read or mutation, DP/DP
  Training start, Codex dispatch, mailbox/Graph, OCR, or Ollama operation ran.

Exact next start: perform one controlled live proposal-write DP Training
acceptance against the existing active flagged correction case. Prove one
version-keyed reanalysis under analysis contract v2/business context v1 reuses
the durable identity/checkpoint, creates one validated new proposal generation,
writes only the four workflow-owned fields, preserves human controls/comments,
and creates no implementation job or Codex dispatch. An unchanged second cycle
must be reconciliation-only. Do not approve implementation during acceptance.

Dedicated Live Document Processor work-pool checkpoint (2026-09-04):

- Added and registered `lthhc-dp-live-process` for only the parameterless
  `document-processor-live` deployment and explicitly named its owned worker
  `lthhc-dp-live-worker`. Manual DP remains on `lthhc-local-process`; DP Training
  remains on `lthhc-dp-training-process`.
- `startdp`, `statusdp`, and `stopdp` now use the dedicated live pool while
  preserving PID, creation-time, command-line marker, and cross-service conflict
  guards. Manual and training worker launch/stop ownership remains isolated.
- Metadata-only local Prefect registration proved all three pools are process
  pools with concurrency one, all three target deployments retain concurrency
  one with `CANCEL_NEW`, empty parameters/job variables, and zero schedules.
  There were zero online workers, active target runs, and automations. No worker
  or flow was started.
- Modified Python compiled. Focused/affected synthetic deterministic, mock,
  Windows PowerShell 5.1, and isolated local Prefect regressions passed. Actual
  read-only `statusdp` reported the live pool ready, stopped, zero workers, and
  not degraded. No mailbox/document, Smartsheet, OCR, Ollama, or PHI-sensitive
  operation ran.

Exact next start: perform one controlled live proposal-write DP Training
acceptance against the existing active flagged correction case. Prove one
version-keyed reanalysis under analysis contract v2/business context v1 reuses
the durable identity/checkpoint, creates one validated new proposal generation,
writes only the four workflow-owned fields, preserves human controls/comments,
and creates no implementation job or Codex dispatch. An unchanged second cycle
must be reconciliation-only. Do not approve implementation during acceptance.

DP Training supplemental-clarification repair (2026-09-04):

- PHI-safe protected-case forensics proved the latest clarification reached
  analysis contract v2 with all three reviewer-comment revisions. The validated
  raw model structure omitted service and supported-date requirements; no later
  validation, normalization, rendering, row-state, or write-idempotency boundary
  removed them.
- Analysis contract version 3 now merges compatible filename-policy requirements
  chronologically and lets a newer explicit conflict override only its affected
  component. The deterministic merge emits controlled structural concepts only;
  reviewer values never become production evidence.
- The proposal vocabulary and renderer now support canonical document type,
  payer when applicable, service when applicable, and conditional supported date
  representation. A range requires two explicitly and deterministically supported
  applicable dates; otherwise a supported single date or the approved unresolved
  `[DATE]` policy applies. AUTH and AUTH DECREASE do not imply a range, and AUTH
  INIT retains its external-context restriction.
- Business context remains version 1 because shared business semantics did not
  change. The existing active contract-v2 case is eligible exactly once for an
  unchanged-input contract-v3 reanalysis with the same durable identity and
  comment checkpoint. Stale approval state is invalidated, a changed validated
  output creates one proposal generation, and later unchanged cycles are
  idempotent. Proposal-write remains non-dispatchable.
- Modified Python compiled. Focused and affected synthetic deterministic/mock,
  naming/business-context, PowerShell 5.1, and isolated local Prefect tests passed.
  No live Smartsheet mutation, Codex dispatch, mailbox/Graph, OCR, or live Ollama
  operation ran.

Exact next start: perform one controlled live proposal-write DP Training
acceptance against the existing active flagged correction case. Verify exactly
one unchanged-input analysis-contract-v2-to-v3 reanalysis under business context
v1 preserves durable case identity and comment checkpoint, creates one validated
proposal generation containing canonical type, payer when applicable, service
when applicable, and supported date representation, writes only workflow-owned
fields, and preserves human controls/comments. Verify zero implementation jobs or
Codex dispatch and unchanged-second-cycle idempotency. Do not approve
implementation during acceptance.

DP Training reviewer-facing proposal rendering refinement (2026-09-04):

- Kept analysis contract v3 and business context v1 unchanged. The validated
  structural analysis still retains filename subtype, payer, service, supported
  date representation, exclusions, evidence boundaries, placeholder policy,
  technical disposition, and implementation context.
- Refined only `build_proposal`, the deterministic `AI Proposed Correction`
  presentation boundary. It now emits a concise business summary from controlled
  structure and omits internal validation, evidence, placeholder, technical, and
  implementation boilerplate. Reviewer text and patient-specific values are never
  copied into the summary.
- The protected implementation-task builder continues reconstructing the detailed
  behavior from validated structural fields. Proposal generations, hash binding,
  human checkbox ownership, clarification precedence, protected case storage,
  idempotency, and proposal-write dispatch prohibition remain unchanged.
- Synthetic tests prove a minimal normal follow-up comment creates one new
  generation without replacing compatible prior context, preserves the complete
  filename structure, and becomes a no-op on the next unchanged cycle. Modified
  Python compiled; focused and affected DP Training, business-context, naming,
  PowerShell 5.1, and isolated Prefect checks passed. No live Smartsheet correction
  processing, mailbox/Graph, OCR, live Ollama, or Codex operation ran.

Exact next start: add one normal minimal reviewer comment, such as `again`, to the
existing active correction case, then run one controlled live proposal-write DP
Training acceptance. Verify exactly one new generation retains the full prior
compatible filename structure and writes the concise reviewer proposal plus only
the required workflow-owned type/status fields. Verify human controls/comments
remain unchanged, zero implementation job/Codex dispatch, unchanged-next-cycle
idempotency, and a clean DP Training stop. Do not approve implementation.
<!-- LEGACY_PROJECT_JOURNAL_END -->

## Verbatim Legacy Tracker Updates Snapshot

<!-- LEGACY_TRACKER_UPDATES_START -->

    (
        "LTHHC AI Platform",
        "In Progress",
        (
            "Core document automation is operating through a tested production "
            "path. Deterministic filename policy and ambiguity-safe service "
            "references are synthetic-tested, and the configured authoritative "
            "reference workbook passed live read-only refresh and cache safety "
            "verification. The 2067 document type is now separated from optional "
            "supported workflow context. Generic family/subtype-aware automatic "
            "Smartsheet mapping now covers every processed document with the "
            "current explicit policies; the evolving destination schema and "
            "platform-wide correction/readback contract now has a first-class "
            "Prefect-visible DP Training implementation. It extends the prior "
            "feedback seed with exact correction-column ownership, protected "
            "comment/case handling, two human approval generations, controlled "
            "local analysis, and a bounded PHI-safe Codex dispatcher. The "
            "read-only flagged-row/comment acceptance passed. The protected "
            "local mode is now `proposal_write` with Codex dispatch disabled. "
            "A shared PHI-free versioned business context now supplies live-model "
            "and correction-analysis role views while deterministic services remain "
            "authoritative. Correction analysis v3 preserves compatible prior "
            "filename intent across supplemental clarifications, deterministically "
            "represents applicable service and supported date behavior without using "
            "reviewer values as production evidence, and permits one version-keyed "
            "reanalysis of the current contract-v2 case. Reviewer-facing proposals now "
            "render concise business summaries while protected structural analysis "
            "remains authoritative; minimal-comment proposal-write and unchanged-cycle "
            "idempotency acceptance remains pending. Live DP now "
            "has its own registered Prefect process pool and owned worker identity; "
            "manual DP and DP Training retain their separate existing pools."
        ),
    ),
    (
        "Design Security Model",
        "In Progress",
        (
            "Implemented PHI boundaries, local AI processing, protected caches, "
            "sanitized Graph failures, explicit destination mapping, and "
            "PHI-safe diagnostics. DP Training adds current-user DPAPI-sealed "
            "correction cases, untrusted-comment schema validation, strict "
            "human/workflow ownership, PHI-safe Prefect state, and a deterministic "
            "no-PHI Codex boundary; broader platform security design continues."
        ),
    ),
    (
        "Install PaddleOCR",
        "Completed",
        "PaddleOCR is installed and verified through real local OCR execution.",
    ),
    (
        "Extract Image Text",
        "Completed",
        (
            "Implemented and tested local scanned-document text extraction with "
            "protected hash-based cache reuse."
        ),
    ),
    (
        "Handle Low Confidence",
        "Completed",
        (
            "Implemented configured confidence evaluation, deterministic review "
            "routing, candidate-preserving null-safe validation, and omission of "
            "unsupported or low-confidence production values/confidences while "
            "protected evidence and scoped downstream review metadata remain "
            "preserved."
        ),
    ),
    (
        "Install Base Model",
        "Completed",
        "Installed and verified the configured local Ollama base model.",
    ),
    (
        "Handle Retry Logic",
        "Completed",
        (
            "Implemented and tested one controlled extraction retry with "
            "independent candidate validation, deterministic selection, and no "
            "attempt merging."
        ),
    ),
    (
        "Benchmark Performance",
        "In Progress",
        (
            "Added PHI-safe stage timing and recorded controlled real local "
            "performance observations; broader representative benchmarking is "
            "not complete."
        ),
    ),
    (
        "Create Rules Engine",
        "Completed",
        (
            "Implemented the separate deterministic business-rule service and "
            "document-type rule registry with synthetic coverage."
        ),
    ),
    (
        "Validate Required Fields",
        "Completed",
        (
            "Implemented deterministic required-evidence and destination-required "
            "field validation with null-safe failure behavior."
        ),
    ),
    (
        "Normalize Values",
        "Completed",
        (
            "Implemented deterministic normalization for supported dates, lists, "
            "identifiers, confidences, and service-line structures."
        ),
    ),
    (
        "Generate Exceptions",
        "Completed",
        (
            "Implemented deterministic validation, business-rule, and review "
            "reasons plus downstream human-review exception metadata."
        ),
    ),
    (
        "Handle API Errors",
        "Completed",
        (
            "Implemented and tested application-owned sanitized Graph and "
            "Smartsheet failure boundaries without provider details or secrets. "
            "Smartsheet API rejection diagnostics now retain only a fixed safe "
            "category, valid numeric API code, and HTTP status class; response "
            "bodies, payloads, values, row IDs, exception text, and sensitive "
            "provider fields are excluded."
        ),
    ),
    (
        "System Testing",
        "In Progress",
        (
            "Completed the first successful single-item production end-to-end "
            "run; broader system scenarios and remaining integrations continue."
        ),
    ),
    (
        "Performance Testing",
        "In Progress",
        (
            "Captured PHI-safe real local stage and total timings; comprehensive "
            "load and representative performance testing remains pending."
        ),
    ),
    (
        "Production Deployment",
        "In Progress",
        (
            "The automatic mailbox-to-Smartsheet path completed one controlled "
            "production run. The deterministic filename policy and safe fallback "
            "boundary are synthetic-tested, and the authoritative references passed "
            "live read-only refresh. RENEW AUTH, optional supported qualifiers, 2067 "
            "INBOUND AUTH context, and Posted Date-only 2067 naming are now "
            "synthetic-tested. A separate validated-input boundary now requires "
            "dedicated evidence and approved context. Production filename wiring "
            "remains disabled pending assembly and runtime context providers. "
            "Prefect 3.8.4 now provides a PHI-safe manual localhost PostgreSQL "
            "17.11 control-room checkpoint with a synthetic process-worker "
            "deployment and five completed sequential runs. An explicit "
            "application-owned downstream-review mode, durable PHI-safe result, "
            "and parameterless one-call mailbox adapter are implemented and "
            "mock-tested. After one real run exposed one message with two "
            "documents and was safely cancelled, the manual adapter gained an "
            "acceptance-only local popup with safe numbered labels, newest-ten "
            "metadata discovery, exact Inbox re-verification, one-message/one-"
            "document enforcement, no newest-unread fallback, and PHI-safe "
            "stage visibility. That popup-selected source is now registered "
            "and passed read-only deployment-metadata verification without a "
            "worker or flow. A separate operator-owned unattended mode is now "
            "implemented with one bounded candidate per watched invocation, "
            "five-minute polling, bounded failure backoff, explicit startdp/"
            "statusdp/stopdp controls, and manual/live conflict guards. Its "
            "three standardized deployments are now registered and passed "
            "guarded PHI-safe read-only verification before live acceptance. "
            "The first startdp attempt exposed and corrected historical-offline-"
            "worker counting plus an overbroad pre-worker readiness boundary; "
            "startup is now lightweight/categorized before worker creation and "
            "operator status is readable with preserved JSON compatibility. "
            "A later controlled start reached a correctly owned waiting runtime "
            "but buffered its operator output; startup now flushes five PHI-safe "
            "stages, bounds Prefect/Graph checks, reports fixed failure categories, "
            "and cleans proven owned processes on interruption. "
            "The first unattended document completed and exposed submission-key "
            "attachment naming. The shared production assembler now uses only "
            "separately supported person components, exact authoritative payer/"
            "service lookups, supported dates, and supported workflow context; "
            "unresolved evidence receives a full-fingerprint technical fallback. "
            "Expected attachment identity is persisted in ignored protected job "
            "state before external row creation for restart-safe reconciliation, "
            "while the submission key remains the row/idempotency key. "
            "Retry/attempt 2 is not a review trigger; conservative quantity rules "
            "can require review independently of 100% classification confidence. "
            "Successful quantity reconciliation no longer triggers review by "
            "itself, and mapped review reasons now use fixed PHI-safe codes. "
            "Prefect retries, "
            "server-side scheduling, and silent automatic startup remain "
            "disabled. Live DP now targets its dedicated registered process pool, "
            "while manual DP and DP Training remain independently routed. The "
            "pinned Prefect 3.8.4 offline dry-run defect now has a version-bounded "
            "operational exception backed by online migration, exact head, "
            "state-invariant, and synthetic acceptance evidence."
        ),
    ),
    (
        "Design Solution Architecture",
        "Completed",
        (
            "Completed the approved local-first architecture using Microsoft "
            "Graph, local PaddleOCR, local Ollama, field-level evidence, "
            "authorization service-line extraction, deterministic candidate "
            "validation, controlled retry, business rules, automatic "
            "Smartsheet population, and downstream exception review."
        ),
    ),
    (
        "Define Integration Architecture",
        "Completed",
        (
            "Completed integration architecture for Microsoft Graph mailbox "
            "ingestion followed by local OCR, separate local LLM requests, "
            "structured extraction, controlled retry, evidence validation, "
            "business rules, automatic Smartsheet population, and conditional "
            "downstream human review."
        ),
    ),
    (
        "Design AI Pipeline",
        "Completed",
        (
            "Implemented provider-based OCR and LLM architecture with "
            "registries, factories, field-level evidence, neutral service-line "
            "records, PHI-safe metrics, deterministic attempt routing, a "
            "generic retry verification prompt, deterministic validation, "
            "business rules, automatic destination handoff, and conditional "
            "human review."
        ),
    ),
    (
        "Configure Branch Strategy",
        "Completed",
        (
            "Git repository is connected to GitHub and the development "
            "workflow is validated. Secrets, PHI, incoming documents, and OCR "
            "cache must remain excluded from commits."
        ),
    ),
    (
        "Validate Development Environment",
        "Completed",
        (
            "Validated Python, PaddleOCR, Ollama, llama3.1:8b, Microsoft Graph, "
            "Git, synthetic tests, real cached-document processing, and "
            "PHI-safe local performance instrumentation."
        ),
    ),
    (
        "Create OCR Service",
        "Completed",
        (
            "Implemented local PaddleOCR with SHA-256 hash-only caching, cache "
            "reuse, privacy-safe logging, sanitized exceptions, legacy cache "
            "migration, and lazy engine initialization only when prediction is "
            "required after cache lookup."
        ),
    ),
    (
        "Extract PDF Text",
        "Completed",
        (
            "Successfully extracted real scanned PDF text locally and verified "
            "that unchanged documents reuse cached OCR text."
        ),
    ),
    (
        "Unit Test OCR",
        "Completed",
        (
            "Validated direct PaddleOCR, real scanned PDF OCR, cache creation, "
            "cache reuse, PHI-safe cache logging, cache-only operation without "
            "engine initialization, and normal cache-miss engine startup."
        ),
    ),
    (
        "Create Prompt Templates",
        "In Progress",
        (
            "Implemented separate local Ollama classification and extraction "
            "prompts with field-level evidence and service-line records. The "
            "whole-document learning prompt now uses request-local evidence "
            "aliases and a request-bound reference schema. "
            "Repeated extraction can still vary, so controlled retry and human "
            "review remain active."
        ),
    ),
    (
        "Implement Classification",
        "In Progress",
        (
            "Implemented local Ollama classification with structured JSON and "
            "PHI-safe request metrics. A centralized family/subtype registry "
            "preserves Authorization behavior and now supports grounded 2067 "
            "with deterministic UTL resolution from uncontradicted contact-"
            "failure evidence. One real protected cache-only/local-Ollama "
            "acceptance resolved the known 2067/UTL case with supported "
            "deterministic family and subtype evidence. Other future subtypes "
            "remain untrained."
        ),
    ),
    (
        "Implement Data Extraction",
        "In Progress",
        (
            "Implemented field-level extraction, neutral service-line "
            "extraction, PHI-safe generation metrics, deterministic attempt "
            "routing, and one controlled retry with a generic verification "
            "prompt. A controlled real authorization run triggered validated "
            "retry, selected attempt 2, and recovered supported service-line "
            "structure while unsupported values remained cleared. Dedicated Posted "
            "Date and renewal-qualifier evidence fields now use the same preserved "
            "value/confidence/source_text contract with strict no-inference prompt "
            "guidance."
        ),
    ),
    (
        "Validate AI Output",
        "In Progress",
        (
            "Implemented independent deterministic validation and scoring of "
            "extraction candidates. Candidates are never merged; the stronger "
            "supported candidate is selected and ambiguity remains routed to "
            "human review. Quantity reconciliation was verified to remain "
            "within one independently validated candidate without inference "
            "or attempt merging. Filename-specific validation now requires explicit "
            "Posted Date and qualifier ownership evidence and rejects ambiguity or "
            "unsupported claims without changing existing authorization validation. "
            "Final-state review ownership now excludes filename-placeholder and "
            "internal request-selection noise, while successful supported quantity "
            "reconciliation supersedes its earlier top-level candidate failure."
        ),
    ),
    (
        "Apply Business Rules",
        "In Progress",
        (
            "Authorization rules remain conservative and separate from "
            "evidence validation. Supported quantity without an explicit unit uses "
            "the approved Hours business default without implying approval; explicit "
            "unsupported or ambiguous units and unresolved modifier ownership remain "
            "review conditions. Specific final-state validation now supersedes broad "
            "missing-rule duplicates."
        ),
    ),
    (
        "Unit Test Rules",
        "In Progress",
        (
            "Real authorization testing confirms that unresolved quantity and "
            "modifier relationships route to human review. Synthetic retry, "
            "candidate-selection, quantity-reconciliation, validator, review, "
            "mapping, filename-placeholder separation, operator-presentation, and "
            "cross-layer final-state tests pass. Quantity never implies approval; "
            "remaining business semantics require explicit deterministic support."
        ),
    ),
    (
        "Integration Testing",
        "In Progress",
        (
            "Tested Graph ingestion, local OCR, separate local Ollama requests, "
            "PHI-safe metrics, service-line extraction, deterministic attempt "
            "routing, controlled retry logic, independent candidate "
            "validation, business rules, and human review. Real retry detection "
            "and recovery are verified locally with cached OCR and local "
            "Ollama, and the corrected semantic harness passes in the "
            "controlled real regression. Graph failure handling now uses "
            "sanitized application-owned categories. Automatic Smartsheet row "
            "population is implemented after validation and business rules, "
            "with review status and reasons preserved for downstream exception "
            "handling. The full document uses explicit attachment upload; OCR "
            "text and source_text have no configured destination. Legacy "
            "Graph/mailbox diagnostic output is now limited to PHI-safe "
            "counts, booleans, confidence/status metadata, and sanitized "
            "failure categories. Smartsheet attachment partial success now "
            "preserves the existing-row state and blocks explicit duplicate "
            "retry when the prior PHI-safe result is available; process-restart "
            "resume remains unavailable without safe persisted row state. The "
            "generic local evaluator now requires numeric selection, explicit "
            "Run Type and local execution authorization, enforces cache-only "
            "OCR without fallback or Paddle initialization, suppresses nested "
            "output, and returns only "
            "aggregate metadata. Its opt-in learning mode reuses the numeric "
            "selection and processed document for one additional local-only "
            "whole-document evidence request. It preserves page/block relations "
            "when available, checks referenced coverage, and returns versioned "
            "sanitized field status, conflicts, nullable confidence, novel "
            "schema gaps, and non-automatic development implications. Legacy "
            "text-only caches remain usable with layout explicitly unavailable. "
            "The opt-in local Tkinter protected-review "
            "consumer now provides an in-memory source-document, field/evidence, "
            "service-line, and validation/review comparison surface while "
            "aggregate external results remain PHI-safe. "
            "Local document candidates are now ordered by authoritative Graph "
            "received recency at the "
            "shared listing/selector/snapshot/evaluation boundary, and a current "
            "protected selection records its numeric identity internally. "
            "Snapshot mismatches stop before processing without exposing source "
            "identity. Production Graph "
            "attachment enumeration now retains only allowlisted diagnostic "
            "metadata, and a live read-only preflight verified one unread "
            "candidate with one processable attachment without mutation. A "
            "deterministic filename policy and guarded attachment fallback now "
            "have synthetic coverage; normal production callers still use the "
            "existing filename behavior. Ambiguous service reference keys now "
            "remain unresolved without requiring workbook row collapse. The "
            "configured authoritative workbook passed live metadata, download, "
            "required-sheet, cache-reuse, and last-known-good verification."
            " The filename boundary now treats 2067 as a document/form type and "
            "accepts only independently supported optional workflow context without "
            "inferring client status or renewal meaning. Actual authorization "
            "renewals use RENEW AUTH, supported qualifiers remain separate, and "
            "2067 naming requires a resolved Posted Date while production filename "
            "wiring remains disabled. A separate validated-input boundary now "
            "preserves dedicated evidence and accepts only explicit approved 2067 "
            "workflow context; it is not connected to production callers."
            " The generalized whole-document family/subtype path also passed "
            "one real protected cache-only/local-Ollama acceptance: structured "
            "OCR was reused with zero prediction calls, family 2067 and subtype "
            "UTL resolved from deterministic evidence, and all six returned "
            "learning references grounded with zero unsupported references. "
            "The later generic production-row checkpoint routes 2067/UTL, "
            "Authorization, unknown taxonomy, and future trained families through "
            "one family/subtype-aware mapping boundary using the current explicit "
            "approved fields. Live schema inspection, evolving operational fields, "
            "correction/readback, and end-to-end Smartsheet acceptance remain "
            "pending. A separate read-only incorrect-AI feedback boundary now "
            "stores idempotent protected comment snapshots behind injected "
            "readers; live checkbox normalization and adapter wiring remain "
            "pending approval and inspection. The technical submission-key "
            "column now passes corrected live columns-only type and non-system "
            "metadata acceptance. One controlled PHI-free live case also passed "
            "exact-key row and attachment read-after-write reconciliation, "
            "duplicate prevention, deterministic cleanup, and post-cleanup "
            "zero-match verification. Durable mailbox recovery now persists a "
            "leased create-in-flight state, reconciles uncertain outcomes before "
            "any re-entry, blocks unavailable or ambiguous outcomes, and permits "
            "a later same-job retry only after authoritative zero-match proof and "
            "a fresh lease. Attachment handling remains blocked until row identity "
            "is proven; direct uncertain row retries remain blocked. The typed row "
            "contract now omits optional nulls, validates CHECKBOX, DATE, and "
            "TEXT_NUMBER scalars plus writable/system-column state before Cell "
            "construction, and requires exact zero-match reconciliation plus passing "
            "typed validation before a version-2 attempt can be durably reserved. "
            "An older failed durable job can re-arm only once under the newer "
            "contract; one match reconciles, while multiple or unavailable results "
            "fail closed."
        ),
    ),
    (
        "Register Azure App",
        "Completed",
        (
            "Created and tested the Microsoft Entra application registration "
            "used by the Microsoft Graph client-credentials workflow."
        ),
    ),
    (
        "Connect Mailbox",
        "Completed",
        (
            "Connected to the ai@lthhc.com shared mailbox and successfully "
            "retrieved unread messages through Microsoft Graph."
        ),
    ),
    (
        "Configure Graph Permissions",
        "Completed",
        (
            "Configured and tested the required Microsoft Graph application "
            "permissions and tenant administrator consent for the shared "
            "mailbox workflow."
        ),
    ),
    (
        "Unit Test Mail Connector",
        "Completed",
        (
            "Tested unread-message retrieval, attachment enumeration and "
            "download, inline-image filtering, mark-read-after-success "
            "behavior, retry preservation, and duplicate prevention."
        ),
    ),
    (
        "Download Attachments",
        "Completed",
        (
            "Implemented and tested supported non-inline attachment download, "
            "including filtering of inline signature images."
        ),
    ),
    (
        "Implement Authentication",
        "Completed",
        (
            "Implemented and tested OAuth 2.0 client-credentials "
            "authentication through MSAL for Microsoft Graph."
        ),
    ),
    (
        "Handle Authentication Errors",
        "Completed",
        (
            "Implemented and mock-tested sanitized configuration, authentication, "
            "authorization, request, and response-decoding failures. Provider "
            "details, credentials, tokens, and exception context are excluded, "
            "and failed token acquisition cannot reach a Graph request."
        ),
    ),
<!-- LEGACY_TRACKER_UPDATES_END -->

## DP Training Failure Diagnostics and Acceptance Reconciliation - 2026-09-08

Final checkpoint gates: project tracker returned Updated 1, Unchanged 37,
Not Found 0, Failed 0. Continuity/WBS tests passed again after regeneration.
Protected paths remained ignored and reviewed Git diff passed whitespace checks.
The verified isolated test database/journals were removed after the test process
exited; no production runtime was terminated. Temporary patch artifacts were
removed from the chat workspace; the prior acceptance reports remain preserved.

The local PHI-safe acceptance reports recorded one successful controlled
proposal_write acceptance: one changed case among two flagged cases, one proposal
generation, retained compatible structure, matching concise readback, unchanged
human controls/comments, no dispatch, idempotent following cycle, and clean stop.
The reviewer subsequently accepted the presentation and separately approved one
implementation attempt. That attempt failed; no code changed and no automatic
retry occurred. Training was stopped and capability returned to proposal_write
with dispatch disabled. These reports had not yet been incorporated into Git
continuity. Original failure cause is unavailable, not guessed.

Source inspection proved that child output was discarded, result files removed,
and dispatch failure category was not retained in the case. Cycle summaries could
say completed/none despite implementation_failed_count being positive. The fix
persists fixed categories and bounded exit codes before workflow-result writes,
distinguishes startup/nonzero-exit/timeout/missing-result/invalid-result boundaries,
and makes failed cycles fail Prefect after preserving their safe summary. Raw
child output, result text, exception text, identifiers, and protected values are
not diagnostics. Schema 3 migrates existing schema 1/2 cases without changing
identity or consuming/re-arming approvals. Historical unknown failures are labeled
legacy_failure_unavailable. No existing protected case was migrated live here.

Files changed: dispatcher, training application, protected case repository,
Prefect training adapter, training and Prefect tests, current state, history,
derived Smartsheet presentation, and tracker task presentation.

Validation: modified Python compiled; 53 focused training tests, 5 configuration,
5 readiness, 7 Windows PowerShell 5.1 command tests, 5 business-context, 11 continuity,
3 tracker/WBS, and 5 isolated Prefect tests passed (94 total, zero failed).
Synthetic deterministic/mock tests only; temporary isolated Prefect servers were
used, not production deployments or workers. The Prefect harness emitted a
Windows temporary-database cleanup warning after successful tests; this does not
prove a production runtime issue. No PowerShell source was changed.

Current read-only control-plane check: training stopped, no active bounded run,
zero fresh training workers, pool/deployment ready, proposal_write configured,
not degraded. No production mailbox/Graph, OCR/Ollama, document write/upload, or
feedback/comment access occurred during this implementation. Project tracker
presentation synchronization is the only intended external write at this checkpoint.

Limitations: the old child failure cannot be reconstructed. A nonzero child exit
still does not distinguish authentication/network/model causes; no such cause is
claimed. A PHI-free isolated runtime check is next. No consumed approval was
retried or silently re-armed. Separate PowerShell 7 ownership compatibility
remains unproven; use the supported 5.1 wrapper. Deployment refresh is deferred
until the runtime prerequisite has been checked.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Retained safe DP Training dispatch diagnostics and corrected failed-cycle reporting; reconciled prior live acceptance records.",
  "key_result": "Proposal acceptance passed. The later approved attempt failed with unavailable historical cause. Schema 3 preserves case identity and consumed approvals; failed cycles now fail Prefect.",
  "tests": "94 synthetic/mock/isolated Prefect checks passed; modified Python compiled. Harness temporary-database cleanup warning noted.",
  "phi_handling": "No document/feedback operations or child dispatch; fixed categories and counts only. Tracker presentation sync only.",
  "limitation_acceptance": "Training stopped and dispatch disabled. No blind retry; original child cause remains unknown.",
  "exact_next_start": "Perform a PHI-free isolated Codex runtime/result-contract smoke check without repository edits or production integration access; resolve any diagnosed dispatch prerequisite before refreshing training registration and proposing a new generation with a fresh human approval edge. Do not retry the consumed approval generation."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Codex Result Schema Runtime Compatibility - 2026-09-08

The isolated PHI-free protocol test used installed codex-cli 0.151.0, an ephemeral
temporary workspace, read-only sandbox, no approved tool actions, synthetic stdin,
and the exact repo result schema. User configuration and rules were excluded for
the probe; existing CLI authentication was reused without reading credentials.
Raw child output stayed in memory and only fixed categories/counts were reported.
Before the fix: exit 1, result_schema_unique_items_rejected, no result, zero tool
actions. After the fix: exit 0, valid synthetic incomplete result, zero tool
actions. The test did not request or claim an implementation, test success, commit,
or push. It did not consume a correction approval or access protected cases.

The API rejects uniqueItems in the output schema. Removed that keyword and added
local duplicate-layer rejection and exact result-vocabulary validation before
accepting a successful implementation. The schema's required fields, enum values,
version gates, commit verification, and additionalProperties=false remain intact.
An initial synthetic test caught use of the distinct proposal vocabulary; this was
corrected to the exact Codex result vocabulary and covered by a schema-alignment
test. The prior live failure's discarded diagnostics cannot prove historical cause;
this is a reproducible present defect, not a guessed historical attribution.

Files changed: src/contracts/dp_training_codex_result.schema.json,
src/services/document_processor_training_codex_service.py,
tests/test_document_processor_training.py, PROJECT_STATE.md, PROJECT_HISTORY.md,
PROJECT_SMARTSHEET.md, and tracker presentation. No PowerShell source changed.

Validation: modified Python compiled; final synthetic/mock runs passed 54 training,
5 configuration, 5 readiness, 7 Windows PowerShell 5.1 command, 5 business-context,
11 continuity, and 3 tracker/WBS tests (90 total, zero failed). One real external
PHI-free CLI test failed as expected before the fix and one passed afterward.
No mailbox/Graph, OCR/Ollama, production document write/upload, correction feedback,
comments, or live implementation dispatch occurred. Tracker presentation and safe
source registration are the only intended project/control-plane writes.

Remaining acceptance: a full production-configured implementation attempt has not
passed. No blind retry or consumed-approval re-arm is authorized. Use the same case,
a deliberately new proposal generation, fresh human approval, and bounded execution.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Fixed reproduced Codex result-schema API rejection while preserving deterministic result validation.",
  "key_result": "Unsupported uniqueItems moved to local enforcement. Real isolated CLI probe changed from rejected to valid synthetic result with zero tool actions.",
  "tests": "90 synthetic/mock checks passed; modified Python compiled; real PHI-free before/after protocol test verified the fix.",
  "phi_handling": "No protected document/feedback access or implementation dispatch; tracker/control-plane maintenance only.",
  "limitation_acceptance": "Training remains stopped; historical cause not reconstructed; full implementation acceptance requires a new generation and fresh approval.",
  "exact_next_start": "Refresh affected training source registration if required, then create a new proposal generation on the existing correction case using a normal reviewer comment. Verify proposal correctness, require a fresh Approve AI Correction false-to-true edge, perform one controlled implementation acceptance, and verify retained safe diagnostics, commit/push gates, unchanged human controls, and no retry on the following cycle. Do not approve resolution until a separate document retest passes; stop DP Training afterward."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Post-schema-fix Controlled Proposal Acceptance - 2026-09-08

The operator unchecked correction approval and supplied a new ordinary comment
on the existing case. A protected in-memory preflight found exactly one revised
existing flagged case and confirmed proposal_write with dispatch disabled. The
supported Windows PowerShell 5.1 owned wrapper ran one training cycle and was
stopped afterward. Real external feedback reads and workflow-owned proposal
writes passed: generation increment one, exact proposal readback, compatible
filename structure and subtype retained, human controls and comments unchanged.
Implementation attempt count, job identity, and consumed approval generation
remained unchanged; implementation_started_count was zero. No live inbox DP,
mailbox access/mutation, document OCR, document row creation/attachment upload,
comment writes, or implementation dispatch occurred. Training analysis used the
approved existing local integration; no protected values were emitted.

Application code was unchanged. Files changed: PROJECT_STATE.md,
PROJECT_HISTORY.md, and generated PROJECT_SMARTSHEET.md. A temporary acceptance
helper held protected facts only in memory and emitted booleans/counts. This
acceptance did not exercise the unchanged following cycle or implementation.
The new proposal still requires human review and a fresh approval edge.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Passed controlled post-schema-fix proposal acceptance on the existing correction case.",
  "key_result": "Exactly one new generation; exact readback, compatible structure and subtype retained; human controls/comments unchanged; no implementation dispatch; training stopped.",
  "tests": "Real proposal-only acceptance passed. Continuity and tracker regressions checked separately before checkpoint commit.",
  "phi_handling": "Approved feedback reads/local analysis/proposal writes only; protected values remained local or in Smartsheet; safe booleans/counts reported.",
  "limitation_acceptance": "Reviewer must inspect the new proposal. No implementation or unchanged-following-cycle acceptance was performed in this cycle.",
  "exact_next_start": "Have the reviewer inspect the new AI Proposed Correction on the existing case. If correct, require a fresh Approve AI Correction false-to-true edge, refresh training source registration if required, and perform one controlled implementation acceptance. Verify retained safe diagnostics, commit/push gates, unchanged human controls, and no retry on the following cycle. Do not approve resolution until a separate document retest passes; stop DP Training afterward."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Controlled Dispatch Argument Rejection and Fix - 2026-09-08

The operator confirmed a fresh Approve AI Correction edge after reviewing the
current proposal. Protected preflight verified exactly one eligible existing
case, current proposal/type/comment digest, unchecked resolution approval,
clean synchronized Git, and no active training worker/run. Training source was
refreshed. The owned Windows PowerShell 5.1 runtime temporarily used
approval_dispatch with dispatch enabled. Exactly one implementation attempt was
recorded; it failed with retained codex_failed and exit 2. No implementation
commit or document correction resulted. The consumed generation was not rearmed.
The unchanged following live cycle recorded zero additional dispatches. Human
controls/comments and proposal generation were unchanged. Training was stopped;
proposal_write and disabled dispatch were restored using only exact gate edits.

Installed codex-cli 0.151.0 deterministically rejects the dispatch command's
combination of --sandbox workspace-write and --approve-for-me. A synthetic
argument probe reproduced exit 2 with the mutual-exclusion diagnostic. Removing
only the explicit sandbox pair passed argument parsing and stopped at an
intentionally absent schema before any model task. An isolated real PHI-free
protocol probe with the corrected approval option and exact result schema then
returned exit 0, the expected deliberately incomplete synthetic result, and zero
tool actions. User configuration/rules were excluded in that protocol probe;
production-configured implementation still requires separate acceptance. The
installed CLI help establishes that --approve-for-me selects workspace-write
plus automatic review; no sandbox bypass or weaker approval policy was added.
OpenAI Docs was consulted; installed CLI evidence established this version-specific
argument contract. The earlier discarded historical failure is not reconstructed.

Changed files: src/services/document_processor_training_codex_service.py,
tests/test_document_processor_training.py, PROJECT_STATE.md, PROJECT_HISTORY.md,
and generated PROJECT_SMARTSHEET.md. Regression assertions prohibit the conflicting
sandbox flag and dangerous bypass in the approved bounded launch. Both modified
Python files compiled. The final direct synthetic/mock test runs passed 54
training, 5 configuration, 5 readiness, 7 Windows PowerShell 5.1 command, 5
business-context, 11 continuity, and 3 tracker tests: 90 passed, zero failed.
Tracker synchronization, full diff/protected-path review, and Git synchronization
are checked before this checkpoint is committed.
Temporary probes emit only safe categories/counts and are removed after use.
No mailbox/Graph content, document OCR, production document row creation/upload,
mailbox mutation, or comment write occurred. Existing training feedback reads and
workflow-owned status/result writes were the approved production integration;
no protected values appeared in diagnostics. AI Correction ownership is unchanged.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Diagnosed and fixed mutually exclusive CLI arguments after one controlled approval dispatch failed.",
  "key_result": "Retained exit 2; removed redundant sandbox argument while preserving automatic review and workspace-write. Following live cycle did not retry; training stopped and dispatch disabled.",
  "tests": "90 synthetic/mock checks passed; modified Python compiled. Real isolated PHI-free argument/result-schema probes passed after correction; protocol exit 0 with zero tool actions.",
  "phi_handling": "Approved feedback reads/workflow-state writes only; no document processing or comment writes; safe categories/counts retained.",
  "limitation_acceptance": "Launch fix verified, document correction not implemented. Failed approval remains consumed; production-configured implementation acceptance still pending.",
  "exact_next_start": "Refresh training source registration for the CLI argument fix, then create a new proposal generation on the same correction case using a normal reviewer comment with Approve AI Correction unchecked. Verify the proposal, obtain a fresh human approval edge, and perform one controlled implementation acceptance. Verify safe diagnostics, commit/push gates, unchanged human controls, and no retry on the following cycle. Do not reuse the consumed approval or approve resolution before a separate document retest passes; stop DP Training afterward."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Post-launch-fix Proposal Cycle and Readback Limitation - 2026-09-08

The operator supplied a new comment with correction approval unchecked.
Preflight verified one changed existing case, clean synchronized Git, stopped
training, and proposal_write with dispatch disabled. Training registration was
refreshed to the committed launch fix. One owned PowerShell 5.1 cycle created
exactly one proposal generation; exact Smartsheet readback, retained structure
and subtype, unchanged implementation attempt counts, no approval consumption,
and zero implementation starts were verified. Training returned to waiting and
was stopped. No application code changed or implementation was attempted.

The aggregate before/after snapshot across flagged rows did not match. The
acceptance harness therefore reported incomplete at readback rather than claiming
unchanged human inputs. The original snapshot existed only in process memory
and was not retained after exit; its exact difference cannot be reconstructed.
A subsequent approved read-only check of the unique active case proved current
proposal and processed comment-checkpoint agreement, AI Correction checked,
both approvals unchecked, and a ready false-edge approval baseline. No cause or
actor is inferred for the earlier snapshot mismatch. Future dispatch must repeat
the application's exact-current-proposal/comment/approval checks.

Files changed: PROJECT_STATE.md, PROJECT_HISTORY.md, generated
PROJECT_SMARTSHEET.md only. Real external proposal acceptance was partial as
described, not a fully passed unchanged-input acceptance. Continuity/tracker
regressions and tracker synchronization are checked before commit. Approved
feedback reads/local analysis and workflow-owned proposal writes occurred; no
document processing, mailbox access/mutation, production document row creation
or attachment upload, comment write, or Codex implementation dispatch occurred.
Protected values remained in approved processing; diagnostics were booleans/counts.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Refreshed training registration and generated one new proposal after the CLI launch fix.",
  "key_result": "Exact proposal readback and retained structure/subtype; no dispatch or approval consumption; training stopped. Current active-case comment/proposal checkpoint matches with approvals unchecked.",
  "tests": "Real proposal-cycle checks passed except aggregate unchanged-input snapshot. Continuity/tracker regressions checked before commit.",
  "phi_handling": "Approved feedback reads/local analysis/proposal writes only; no document or implementation operations; protected values not emitted.",
  "limitation_acceptance": "Aggregate initial/final controls/comments snapshot differed; cause not reconstructed. Reverify current inputs before fresh approval dispatch.",
  "exact_next_start": "Have the reviewer inspect the current AI Proposed Correction and approve it only if correct. Before a controlled implementation acceptance, reverify the exact proposal/comment checkpoint and fresh Approve AI Correction edge; refresh source registration if required. Verify safe diagnostics, commit/push gates, human controls, and no retry on the following cycle. Preserve any concurrent reviewer change and stop for stale approval. Do not approve resolution before a separate document retest passes; stop DP Training afterward."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Configured Runtime Acceptance Failure - 2026-09-08

The operator checked Approve AI Correction for the current proposal. Protected
preflight verified exactly one fresh eligible approval, current proposal/type
and comment checkpoint, clean synchronized Git, and no training conflict.
Training registration was refreshed. One controlled approval_dispatch cycle
recorded one attempt that exited with retained codex_failed / exit 1. No approved
document correction or implementation commit resulted. The unchanged following
live cycle started zero additional implementations. Safe final per-field checks
showed zero changes to each human checkbox and zero changed comment checkpoints;
the active case and proposal generation were unchanged. Training stopped and
proposal_write / disabled dispatch were restored. No consumed approval was reset.

The prior argument conflict is absent. Diagnostic-only synthetic probes using
the normal user CLI configuration reproduced exit 1 and no result/tool actions.
The selected model is gpt-6-astra at medium reasoning. Allowlisted diagnostics
establish a model-metadata fallback and invalid-model/session requirement, but
not its precise unmet capability. A WebSocket diagnostic context was observed;
it does not prove that transport is the root cause. No unsupported-account or
authentication cause is claimed. Standalone CLI is 0.151.0; a comparison with the
app-bundled 0.153.4 failed to complete its 120-second subprocess probe. That is
not proof that the bundled runtime supports this production contract. Probe
cleanup completed; a process-marker check found zero remaining synthetic probes.
No global configuration, model selection, provider, or application code changed.
OpenAI Docs was used for troubleshooting guidance; local diagnostic evidence
remains authoritative for this installation. Ignoring user configuration in
earlier successful protocol probes did not test the configured production model.

Files changed: PROJECT_STATE.md, PROJECT_HISTORY.md, generated
PROJECT_SMARTSHEET.md only. The live implementation acceptance failed safely;
the following no-retry and human-ownership checks passed. Continuity/tracker
regressions and tracker synchronization are checked before checkpoint commit.
Approved training feedback reads/workflow-state writes occurred. No document
processing, mailbox/Graph document access, document OCR, production document row
creation/upload, mailbox mutation, or comment writes occurred. No protected
values or raw child diagnostics were emitted. Temporary helpers are removed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Controlled dispatch failed at configured CLI startup; stopped live approval cycling pending runtime readiness.",
  "key_result": "One attempt, retained exit 1, no automatic retry; all human controls/comments unchanged; training stopped and dispatch disabled. No document correction implemented.",
  "tests": "Live implementation acceptance failed; following-cycle no-retry/ownership checks passed. Synthetic configured CLI probes reproduced failure; bundled comparison incomplete.",
  "phi_handling": "Approved training feedback/state integration only; no document processing or comment writes; fixed diagnostic categories/counts only.",
  "limitation_acceptance": "Exact Astra model/session prerequisite remains unresolved. Earlier ignore-config probes do not prove production readiness; no model switch or approval rearm.",
  "exact_next_start": "Resolve the configured Codex implementation runtime prerequisite using bounded PHI-free diagnostics without consuming another correction approval. Classify the Astra model/session requirement and prove the actual intended launch, model, configuration, result contract, and cleanup before another live acceptance. Do not silently change the model or retry the consumed generation. Only after readiness passes, arrange a new proposal generation and fresh human approval on the same case. Keep training stopped and dispatch disabled meanwhile; do not approve resolution before a separate document retest passes."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Standalone Astra Runtime Upgrade and Verified Startup - 2026-09-08

A synthetic no-tools request using normal configuration recovered the exact safe
API rejection: gpt-6-astra requires a newer Codex version. This establishes the
startup cause, not a speculative WebSocket/authentication defect. The installed
official @openai/codex package was upgraded from 0.151.0 to 0.153.4. Model,
reasoning effort, provider, user configuration, application code, durable case,
approval consumption, and production data were not changed.

Two real external synthetic protocol checks passed: an isolated directory and
the actual repository working directory. Both used normal configured Astra,
the current dispatcher approval option, ephemeral execution, and the exact
training result schema. Both returned exit 0 and the expected deliberately
incomplete synthetic result, with zero tool actions. Neither used ignore-config
or ignore-rules. Probes had bounded timeouts and owned-child cleanup. No live
training, mailbox, OCR/Ollama, document write/upload, or comments were accessed.

This is a runtime installation fix, not implementation of the approved correction.
The consumed generation is not rearmed. Training remains stopped and dispatch
disabled. Source files did not change and do not require deployment refresh for
this package upgrade. Continuity and dispatcher/readiness regressions are run
before commit; tracker synchronization must report Not Found 0 / Failed 0.
Files changed: PROJECT_STATE.md, PROJECT_HISTORY.md, PROJECT_SMARTSHEET.md.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Fixed configured Astra startup by upgrading standalone Codex from 0.151.0 to 0.153.4.",
  "key_result": "Exact API rejection proved an outdated CLI. Normal-config synthetic launches passed in isolated and actual project directories; exit 0, exact result schema, zero tools.",
  "tests": "Two real synthetic API protocol checks passed; dispatcher/readiness and continuity/tracker regressions run before commit.",
  "phi_handling": "Synthetic inputs only; no live training, document processing, comments, or approval changes. Tracker receives only safe project summary.",
  "limitation_acceptance": "Startup fixed; document correction not implemented. Previous approval remains consumed; no model/config switch.",
  "exact_next_start": "With configured Astra startup verified on standalone Codex 0.153.4, arrange one new proposal generation and fresh human approval on the same correction case; never reset the consumed approval. Verify the exact current proposal and comment checkpoint, then perform one controlled implementation acceptance with safe diagnostics, commit/push gates, unchanged human controls, and no retry of a consumed generation. Keep training stopped and dispatch disabled outside that acceptance. Do not approve resolution before a separate document retest passes."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Explicit Same-Proposal Infrastructure Recovery - 2026-09-08

The operator explicitly approved recovery of an unchanged previously approved
proposal after a verified infrastructure repair, without checkbox/comment edits.
Added authorize_runtime_recovery as an administrative application operation, not
a polling trigger. Caller attestation must represent proven pre-implementation
CLI failure and a passed configured runtime/schema probe, not inference from a
generic exit code. Exact expected prior attempt and one eligible case are required.
Current proposal/hash, comment checkpoint, production context and human approval
are verified. Pending write ambiguity blocks recovery. A sealed per-generation
reservation is persisted before the workflow-owned status write. Consumed approval,
attempt history, proposal generation and case/job identity are never reset.
Ordinary dispatch rechecks exact current approval; one successful recovery reaches
Retest Required. Failed recovery is not automatically retried or granted again.

Production repository operation locking serializes cycles/recovery; existing
implementation lock and clean/synchronized Git guards remain. Stale operation
locks fail closed rather than guessing process ownership. No schema migration:
the fixed repair audit is stored in the existing sealed transition history.

Files: training application and contracts, protected correction storage, new
test_dp_training_runtime_recovery.py, and the three continuity layers. Python
compilation passed. Synthetic/mock focused/affected tests: recovery 7, training
54, configuration 5, readiness 5, PowerShell 5.1 commands 7, business context 5:
83 passed, 0 failed. Continuity/tracker regressions run before commit. No live
recovery has occurred at this checkpoint; no patient data or external document
operations occurred. Tracker receives only a safe project checkpoint.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Added explicit one-time same-proposal recovery after verified CLI infrastructure repair.",
  "key_result": "Preserves human controls, feedback, consumed approval and identity; exact rechecks, durable reservation and operation lock prevent blind/concurrent retries.",
  "tests": "83 focused/affected synthetic/mock tests passed, including 7 recovery cases and PowerShell 5.1; Python compilation passed.",
  "phi_handling": "Synthetic tests only; no document operations or human-input writes. Sealed audit, safe diagnostics.",
  "limitation_acceptance": "Live same-generation recovery pending. Stale locks fail closed. Real document retest remains required after implementation.",
  "exact_next_start": "Perform the explicitly authorized one-time runtime-repair recovery of the existing unchanged approved correction generation. Recheck runtime readiness and exact proposal, feedback, human controls, and context; preserve consumed approval and case identity. Run one bounded implementation and verify commit/push gates, unchanged human inputs, and an idempotent following cycle. Keep training stopped outside acceptance. A real document test and separate resolution approval remain required after successful implementation."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->


## Approved Supported Authorization Filename Correction - 2026-09-08

Implemented exactly one approved structural filename task. The existing canonical
AUTH DECREASE vocabulary already resolves explicit validated evidence. Inspection
found production assembly independently filled absent top-level date endpoints
from service lines, allowing unrelated intervals to form a range. The smallest
correction permits that fallback only when the opposite endpoint agrees; wholly
line-owned dates keep their existing path. No end date is inferred from AUTH or
its subtype. Validated payer/service naming and approved placeholders remain.
Synthetic coverage asserts exact DECREASE composition, single/range behavior,
unresolved/unsupported/low-confidence subtype safety, missing date placeholder,
unrelated quantity exclusion, and no mutation of final document state.

Durable layers changed: Deterministic Code, Business Context, Prompt / Context
Rendering, and Other (tests/continuity/tracker). Shared-context assessment found
the date rules in project state but absent from the versioned shared source.
Added generalized supported-date and unrelated-field rules, advanced context 1
to 2, registered its semantic digest, and updated bounded training rendering.
Taxonomy, mapping, references, thresholds, and external systems are unchanged.
Analysis contract remains 3. No patient-specific or payer-specific rule was added.

Files: src/services/production_filename_assembly_service.py,
src/models/document_processor_business_context.py,
src/services/document_processor_business_context_service.py,
tests/test_intake_filename_architecture.py,
tests/test_document_processor_business_context.py,
tests/test_project_layer_migration.py, PROJECT_STATE.md,
PROJECT_HISTORY.md, generated PROJECT_SMARTSHEET.md, update_project_tracker.py.
Initial working tree was clean; no preexisting uncommitted work was displaced.

Compilation passed in the repository virtual environment. Focused tests: intake
architecture 20 and business context 5. Affected regressions: production assembly
28, filename policy 12, validated inputs 10, attachment naming 5, reference
builder 4, processor integration 13, persistent idempotency 2, training 54.
Total 153 passed, zero failed, synthetic deterministic/mock classification.
Default Python initially lacked requests; using the existing virtual environment
resolved that environment issue. Context-bound tests caught oversized rendering;
compact equivalent wording passed without increasing the 4,096-character limit.
Continuity 11 and tracker 3 tests passed (167 total synthetic/mock checks).
The continuity version assertion now follows the shared version constant.
Approved real project-tracker synchronization passed: Updated 2, Unchanged 36,
Not Found 0 / Failed 0. No document/correction integration was used. System Testing stays In Progress; no broader
WBS completion is inferred. Full diff, ignore, staging, commit and push gates apply.

PHI handling: synthetic fixtures only, local temporary synthetic state, no real
patient values/files/identifiers, mailbox, OCR, Ollama, protected state, document
or correction rows/comments accessed. Only approved PHI-safe project tracker
synchronization may contact Smartsheet. No real document acceptance is claimed.
Persisted attachment names remain authoritative; this does not rename old output.
Context v2 may invalidate old analysis/approval baselines; the owning workflow
must enforce current-version checks rather than silently reusing approval.

Exact next start: Verify this bounded implementation result and local/remote Git synchronization in the owning acceptance workflow. Separately authorize a real document retest and verify unchanged human inputs and following-cycle idempotency before resolution approval. Do not reuse a stale context-version approval; keep training stopped outside acceptance.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Implemented one approved PHI-safe AUTH DECREASE filename correction.",
  "key_result": "Prevents unrelated top-level/service-line endpoints forming a range; preserves supported single date and canonical validated components. Shared context v1 to v2.",
  "tests": "153 focused/affected synthetic/mock tests passed; Python compiled. Continuity/tracker gates checked before commit.",
  "phi_handling": "Synthetic inputs only; no protected data or document/correction integration. Only approved project tracker sync.",
  "limitation_acceptance": "Real document retest and separate resolution approval remain pending; persisted recovery filenames stay authoritative.",
  "exact_next_start": "Verify this bounded implementation result and local/remote Git synchronization in the owning acceptance workflow. Separately authorize a real document retest and verify unchanged human inputs and following-cycle idempotency before resolution approval. Do not reuse a stale context-version approval; keep training stopped outside acceptance."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Same-Generation Runtime Recovery Acceptance Passed - 2026-09-08

The operator authorized the one-time infrastructure recovery and its real retest.
Preflight proved stopped training, zero fresh workers/runs, clean synchronized
Git and unchanged standalone runtime 0.153.4. Existing normal-config/schema probes
had passed. Recovery verified exact current proposal, comment checkpoint, context
and checked human approval, then reserved the single audit grant without resetting
consumed approval or altering human inputs. No new proposal/case was created.

One bounded shared-application cycle dispatched the sanitized implementation:
started 1, completed 1, failed 0, failure category none. Parent verified the result
contract and pushed/clean commit 331442e252acb8d7caf775c3e54df0c6164d7dff.
The next unchanged application cycle started zero implementations. Exact in-memory
before/after checks proved human checkboxes/comments unchanged, same generation,
same consumed approval, and four cumulative attempts (three prior failures plus
one successful recovery). Durable status is Retest Required. No resolution was
approved. This acceptance used the real shared application/dispatcher, not Prefect
worker startup or a deployment invocation; the stopped wrapper's last-cycle counts
can still reflect its previous run.

The child implemented supported filename date ownership and business context v2.
Its 167 synthetic/mock checks and tracker passed; parent recovery/affected checks
totaled 98 before acceptance. The child prompt was corrected to permit only the
approved PHI-safe project tracker while denying document/correction integrations.
Recovery writer preconditions allow reading human approval cells, never writing
them. No human feedback or identifiers were emitted.

All four existing deployments refreshed. Prefect ignores --version with --all;
individual --name registration then proved exact implementation version and
repository source. No schedules/parameters added; manual/live/training concurrency
remains one/CANCEL_NEW. Training stopped, no fresh worker or active bounded run,
no degraded state. No mailbox, document OCR/Ollama, document row/attachment write,
mailbox mutation, or comment write occurred. Approved correction reads and only
workflow-owned status/result writes occurred. This is not real document acceptance.

Final files: three continuity layers only. Protected paths remain ignored.
Continuity/recovery regressions and tracker are rerun before final commit.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Real one-time same-proposal recovery completed the approved filename correction.",
  "key_result": "One implementation succeeded; following cycle started zero. Human inputs, generation and consumed approval unchanged. Retest Required; source registrations verified.",
  "tests": "Child: 167 synthetic/mock checks and tracker passed. Parent: 98 recovery/affected checks; live bounded recovery and no-retry readback passed.",
  "phi_handling": "Approved correction reads/workflow-only writes; no human-input writes, document operations, or exposed protected values.",
  "limitation_acceptance": "Training stopped. Real document retest still required before resolution approval; old persisted filenames are unchanged.",
  "exact_next_start": "Perform one controlled unattended real-document retest with a different eligible document. Verify supported filename components and date ownership, single date versus supported range/placeholder, final validated values and review reasons, Workflow Summary, and clean return to waiting before stopdp. Inspect the result before checking Approve AI Resolution on the existing correction case. Keep DP Training stopped until the separately controlled resolution step. Do not resend the identical processed document as a new-output test; recovery preserves its persisted attachment name."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Local-Only Correction Redesign - Partial Checkpoint 2026-09-08

User superseded Codex production dispatch with local Ollama only. Approve AI
Correction authorizes correction of the existing row/document; Approve AI
Resolution authorizes bounded learning and necessary automatic code updates,
without another manual approval. This is not model-weight training and does not
promise error-free processing. Generated code cannot execute with production
credentials merely because tests pass.

Preserved partial work: DPAPI source/case/audit storage; original cached-evidence
replay; explicit typed same-row updates and null clears; owned attachment version
updates; per-boundary durable reservation/readback; no retry of an unresolved
write; human checkboxes/comments unchanged. Production factory selects local
workflow, never Codex. Ollama role context/local-target guard and bounded eight-rule,
1800-character document-family guidance are implemented. This continuation added
exact-resolution code-update authorization, idempotent across restart, with fixed
safe fields only. No executable backend is connected. Result presentation states
that application code has not changed. Context v3 supersedes the uncommitted
no-code-ever restriction, but analyzer output cannot authorize itself.

Files span training wrappers/readiness/factory/contracts/Prefect observer, Ollama
provider, shared business context, mailbox completion source index, new local
correction memory/workflow/evidence executor and code-update authorization services,
and their synthetic tests. Full current diff is preserved, not committed as complete.
Earlier partial checks are not treated as final acceptance. This continuation ran
5 authorization, 25 local correction, 5 shared context, 54 legacy training,
5 readiness, 5 configuration, 7 PowerShell command, and 10 AI Correction tests:
116 passed after correcting context wording and the safe summary-field allowlist.
Modified Python compiled. Diff whitespace and protected ignore checks passed.

Remaining: independently enforced execution isolation, local code generation,
immutable regression gate, deployment quiescence/promotion/rollback, integration
with pending authorization, full affected regressions, continuity reconciliation
and live acceptance. Docker/Windows Sandbox commands and virtualization services
were not found by the limited local discovery; this is not proof that the host
cannot support isolation. No installation, production code promotion, live DP,
worker, mailbox, OCR/Ollama inference, document Smartsheet operation or comment
operation occurred in this continuation. No new live-test readiness is claimed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Partial local-only same-row correction and resolution-authorized learning implementation.",
  "key_result": "Existing-row correction/readback and bounded type guidance are synthetic-tested. Resolution records one code-update authorization; execution remains blocked pending verified isolation.",
  "tests": "116 focused synthetic/mock checks passed, including PowerShell 5.1 command tests; modified Python compiled and diff/ignore checks passed.",
  "phi_handling": "No live document/model/row/comment operations in this continuation. No protected values exposed. Project tracker sync only.",
  "limitation_acceptance": "Uncommitted and not live-ready. No isolated code runner or promotion/rollback adapter yet; no automatic code deployment claimed.",
  "exact_next_start": "Implement and verify the isolated local-Ollama code-generation/test/promotion runner for resolution-authorized updates, with no production credentials or protected-data access, independent immutable safety tests, crash-safe promotion and rollback. Preserve the pending same-resolution authorization and same-row correction work. Complete affected regressions, tracker and Git gates before any live acceptance; do not start DP or DP Training yet."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Local Correction, Isolated Updates and Acceptance Gates - 2026-09-08

Preserved the interrupted local-only redesign. Production factory now selects
the same-row local workflow; legacy Codex classes are not instantiated even when
the historical dispatch switch is enabled. Local Ollama identity checks reject
remote endpoints/cloud aliases. Approve AI Correction authorizes evidence-only
existing-row and attachment-version correction; Approve AI Resolution authorizes
bounded per-family guidance and constrained necessary local code updates.

Added source-only local generation, one existing method-body AST guard, immutable
six-suite regression staging, headless network-disabled Windows Sandbox runner,
sealed ownership before VM startup, exact owned cleanup, candidate-digest proof,
atomic one-file release and exact rollback. New imports/calls/string literals,
signatures, approval/writer/updater changes and arbitrary repository edits are
denied. Current automatic code scopes are filename policy and review presentation;
unsupported scopes are explicitly reported, not falsely marked installed. Runtime
releases are local sealed provenance, not automatic Git commits or weight training.

User enabled/restarted Windows Sandbox. Real isolation probes proved guest
execution, no active network adapter and no production repository visibility.
The real six-suite runner passed with cleanup proven. Credential-dependent naming
fixtures were corrected to inject non-writing adapters, preserving assertions.
A real code-only Ollama synthetic candidate passed the AST contract; another
candidate was denied for capability expansion. No generated production code was
promoted. No document values or comments entered these model/VM probes.

The explicit end-to-end acceptance clarification added a later-document prompt
test after resolution/restart, plus interrupted-promotion recovery tests. Found
and closed a promotion window: a shared Windows process lease now excludes manual,
unattended and direct document processing during post-install verification. A
sealed quarantine survives a crash; only same-release verification or exact
rollback clears it. Unrelated edits and external processes remain untouched.

Files changed: training wrapper/readiness/factory/contracts/Prefect observer;
Ollama provider and shared business context; mailbox source-binding hook;
DocumentProcessor and full mailbox orchestration source guard; local correction
memory/workflow/evidence executor; code authorization/candidate/test/release/update
services; Windows Sandbox runner and source-activation gate; focused correction,
code-update, authorization, isolation, activation, context, readiness, training and
naming-fixture tests; tracker and the three continuity layers.

Validation at this checkpoint: modified Python compiled. Focused synthetic/mock
checks passed: correction 29, code pipeline 13, authorization 5, sandbox 9,
activation 5, context 5, legacy training 54, readiness 5. Affected checks passed:
configuration 5, PowerShell commands 7, AI Correction 10, destination typing 18,
mapping 25, filename assembly 28, intake naming 20, filename policy 12, review
presentation 14, reference builder 4, document processor 19, full orchestration
15, orchestration 11, durable recovery 21, isolated Prefect 5. Prefect emitted a
temporary SQLite cleanup warning after passing; this is not a production failure.
Two initially misnamed test paths were skipped then corrected and executed.
Final continuity/tracker/PowerShell 5.1/Git gates follow this record before commit.
Final gates passed: continuity 11 and tracker reconciliation 3, bringing the
focused/affected total to 353 unique checks. Actual Windows PowerShell 5.1 parsed
both modified wrappers with zero errors. Tracker Not Found: 0 / Failed: 0.
The final six-suite real Sandbox run passed, exit zero and cleanup proven.
The polling fairness regression proves checked resolved cases cannot starve
later feedback; only a bounded numeric cursor is retained. A stale generated
summary was regenerated before the successful continuity/tracker rerun.

Full live chain remains unproven: new document processing, reviewer flag/proposal
approval, same-row/document correction, resolution approval, and useful approved
learning on a later document. Synthetic stages do not prove clinical correctness
or generalization. Configured training mode remains proposal_write until controlled
setup; no DP/worker/deployment start, mailbox/Graph content, document OCR/Ollama,
production document row/attachment write, mailbox mutation or comment operation
occurred in this implementation checkpoint. Project tracker is the only external
Smartsheet sync. Bounded learning is fixed guidance, not unrestricted self-teaching.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Local-only same-row correction, resolution learning and isolated code-update transaction implemented.",
  "key_result": "Existing-row readback, family-scoped learning reuse, crash quarantine and exact rollback are synthetic-tested. No production Codex dispatch.",
  "tests": "353 focused/affected checks passed; real offline Sandbox and code-only Ollama probes completed. PowerShell 5.1 parse and tracker 0/0 passed.",
  "phi_handling": "Synthetic/code-only probes; no document, mailbox or correction-row/comment operations. Project tracker only.",
  "limitation_acceptance": "Live full-chain acceptance pending. Code updates limited to filename/review method bodies; guidance is not weight training.",
  "exact_next_start": "Refresh committed registrations and verify local_correction readiness. Complete controlled acceptance: process one new document, flag its existing row, approve the proposal, verify existing-row/document correction, approve resolution, and verify approved learning reaches a later same-type document. Confirm restart/idempotency and rollback evidence, local Ollama only, and unchanged human controls. Stop DP Training cleanly. Do not declare end-to-end readiness before this chain is proven; no resubmission is needed to resolve the original correction."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Local Correction Pre-Live Registration - 2026-09-08

Implementation 7a3dfe63452c3cd6d77a21c8a676a6f6745563e0 committed/pushed;
local/remote divergence zero and clean source. Refreshed all four existing
deployments individually with that version. Read-only verification proved unique
names, exact entrypoints, repository pull-step directory, expected pools,
parameterless operation and zero schedules/automations/active runs. Manual/live/
training retain one/CANCEL_NEW. No unexpected deployments or fresh workers.
Installed API query limit is 200; source directory is in set_working_directory
pull steps, not the legacy nullable path property. Probe was corrected accordingly.

Changed only the ignored local training mode from proposal_write to
local_correction. Configuration/protected-state/write-gate readiness passed;
local Ollama identity metadata proved local, without inference. Both DP runtimes
remain stopped; test Sandbox inventory is empty. No worker/deployment invocation,
document processing, row/attachment/comment operation or mailbox mutation occurred.
Registration is control-plane maintenance, not live acceptance.

Files: three continuity layers only for this pre-live checkpoint. Prior 353
synthetic/mock/isolated checks and real code-only probes remain the tested baseline.
Continuity/tracker checks rerun before final metadata commit. No unrestricted
automatic code editing or full live acceptance is claimed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "Local correction implementation pushed; four source registrations and local-only readiness verified.",
  "key_result": "Same-row correction, resolution guidance and guarded local code updates implemented. Training configured local_correction but stopped; no workers or active runs.",
  "tests": "353 checks passed; real offline Sandbox/code-only Ollama probes passed their gates. PowerShell 5.1 and tracker 0/0 passed.",
  "phi_handling": "Control-plane registration and local metadata only; no document or correction-row/comment operations.",
  "limitation_acceptance": "Full live chain remains pending. Automatic code scope is filename/review method bodies; bounded guidance is not weight training.",
  "exact_next_start": "Complete controlled acceptance: process one new document, flag its existing row, approve the proposal, verify existing-row/document correction, approve resolution, and verify approved learning reaches a later same-type document. Confirm restart/idempotency and rollback evidence, local Ollama only, and unchanged human controls. Stop DP Training cleanly. Source registrations and local_correction prerequisites are verified; do not declare end-to-end readiness before this chain is proven. No resubmission is needed to resolve the original correction."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Controlled New-Document Acceptance - 2026-09-08

Operator supplied one new inbox test document and explicitly authorized the
controlled run. Clean synchronized b8860b1 source was verified; registered runtime
source remained 7a3dfe6 with no subsequent code changes. startdp passed all five
startup stages. One owned live worker executed exactly one observed bounded flow.

Real evidence: exact candidate readiness/reverification passed, acquisition and
OCR completed, local classification and Extraction Attempt 1 ran, deterministic
validation/business actions completed. No retry or second extraction attempt.
Workflow Summary: completed, document_count=1, written_count=1, failed_count=0,
row_action=created, attachment_action=uploaded, row_attempt_count=1,
attachment_attempt_count=1, completed_document_count=1, row_outcome_proven=true.
Initial exact reconciliation found zero matches before the confirmed create.
Filename result partial_business with three placeholders; review required with
four reasons. Values, filenames, IDs, source evidence and reason payloads were
not exposed.

Narrow readback used the single newly updated durable job and only the explicitly
selected AI Correction checkbox column. Durable stage attachment_written, exact
row identity proven, one row/upload attempt, protected correction source binding
ready, and AI Correction=false were confirmed. DP status then proved waiting,
no active bounded run and zero failures; stopdp returned dp_stopped. Training
was not started. The reviewer must assess the output in Smartsheet before
flagging an actual issue and approving any proposed correction.

This is real Graph, approved local OCR/Ollama, production row/attachment and
mailbox-finalization acceptance, not synthetic evidence. No raw document data
entered Codex output. No comment access/write, correction-row update, human
checkbox modification, generated-code update or learning approval occurred.
The observation helper initially queried default ID order instead of newest
runs; corrected expected-start descending order identified the one actual run.
No second run was created by diagnostics.

Files changed: current state, appended history and generated tracker summary only.
Full correction-to-learning chain remains pending; successful ingestion is not
proof of correction correctness or learned generalization. Continuity/tracker
checks and Git gates follow before committing this milestone.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-08",
  "work_summary": "First new-document live acceptance completed under the local-only correction implementation.",
  "key_result": "One row created and one attachment uploaded; one extraction attempt, zero failures. AI Correction unchecked, correction source bound, DP returned to waiting and stopped.",
  "tests": "Real production pipeline and narrow checkbox/durable-state readback passed. Prior 353 regression checks remain baseline.",
  "phi_handling": "Authorized Graph/local OCR/Ollama/Smartsheet document processing; only safe counts/statuses exposed. No comment or correction operation.",
  "limitation_acceptance": "Partial business filename and human review required. Reviewer assessment, correction/resolution approvals and later-document learning acceptance remain pending.",
  "exact_next_start": "Review the newly created acceptance row. If a real correction is needed, the reviewer flags AI Correction and adds a comment, leaving both approval boxes unchecked. Run controlled local_correction training, review and approve the proposal, verify the same-row/document correction, then approve resolution and verify bounded learning on a later same-type document. Preserve human controls, restart/idempotency and rollback protections. Do not declare full-chain acceptance complete yet; do not resend the original document."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Controlled Local Correction Proposal Blocked - 2026-09-09

Reviewer flagged the new acceptance row and supplied an ordinary filename/date
warning comment. No further reviewer detail was needed: protected analysis
recorded desired_behavior_sufficient=true. Exact durable job/case association
proved the new generation blocked, plan absent, approval observed unchecked,
and behavior_code=add_required_review_reason. That selected behavior does not
represent the reported filename/date-warning intent. The exact preparation
exception is swallowed by the current workflow and was not reconstructed or
guessed. No replay retry was performed by diagnostics.

Control room was initially unavailable. Initial StartUI failed because Windows
service permissions denied PostgreSQL startup; operator started it. Existing
PowerShell process-scoped execution convention was used without changing system
policy. One owned training worker and one bounded local_correction cycle ran.
A graceful stop request was placed during the active cycle. Three flagged cases
were analyzed sequentially; all became blocked. Summary nevertheless reported
completed, failure_category=none, implementation_failed_count=0. This summary
must not be mistaken for successful correction acceptance.

Real local analysis/cached-evidence replay and workflow-field proposal writes
occurred through the approved application path. Read-only diagnostics emitted
only fixed categories, counts and booleans. No protected values, comments,
filenames, identities or source text were emitted. correction_applied_count=0,
codex_dispatch_count=0; no human checkbox writes, resolution approval, generated
code promotion, mailbox acquisition/mutation or new document submission occurred.
Final status: training stopped, no active bounded run, no fresh workers,
degraded=false. Application source unchanged and prior regression baseline
retained. Only continuity layers changed for this checkpoint; continuity/tracker
checks run before committing. Full end-to-end acceptance remains unproven.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Controlled local correction proposal acceptance reached a safe blocker.",
  "key_result": "Three flagged cases blocked; zero corrections and Codex dispatches. New feedback was sufficient but selected an inconsistent review behavior; no safe plan resulted. Training stopped.",
  "tests": "Real local training cycle and PHI-safe durable/status inspection. Prior 353 checks remain baseline; continuity and tracker checks rerun.",
  "phi_handling": "Approved local feedback/evidence processing and workflow-field writes only. No protected values emitted; no human controls or mailbox mutation.",
  "limitation_acceptance": "Proposal acceptance failed. Exact preparation cause is not retained; completed cycle status does not prove a ready proposal.",
  "exact_next_start": "Diagnose the existing blocked local correction generation: reviewer intent was sufficient, but analysis selected add_required_review_reason for filename/date-warning feedback and preparation produced no safe plan. Retain fixed PHI-safe preparation failure categories, correct proven intent/scope defects, test and preserve the same case and human approvals, then perform one controlled proposal verification. Do not resend the document or approve the blocked proposal. Full correction/resolution/later-document learning acceptance remains pending."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Correction Intent and Preparation Recovery Fix - 2026-09-09

Read-only allowlisted inspection of the exact latest durable case proved primary
Filename / Filename Missing Component, incompatible add_required_review_reason,
affected fields Payer and Service Line, and no Filename execution field. The old
adapter necessarily raises correction_field_not_mapped before source access for
that combination. This narrows the previously swallowed failure from committed
branch ordering and retained controlled enums, without replaying protected data.
The earlier aggregate checkpoint cannot prove every older case reached replay;
the latest case failed before replay. No raw feedback/values were emitted.

Analysis contract 4 canonicalizes filename behavior and ensures Filename enters
the execution scope. Prompt guidance explicitly distinguishes disputed existing
warnings from requests for additional warnings and retains multi-symptom fields.
Service Line is an evidence/review projection only: no new production column and
no top-level quantity/date/status guessing. Full deterministic validation,
unrelated-field guards, typed updates and human ownership remain unchanged.

Preparation contract 2 persists fixed safe error categories and reports blocked
cases as completed_with_failures; Prefect therefore fails while retaining the
safe summary. New summary fields are blocked_case_count and
preparation_failure_categories. Previously blocked unapplied cases may reanalyze
once with unchecked approvals, under their same stable identity and new audited
generation. Reservation precedes inference; crashes do not create endless model
retries. Applying/resolved/awaiting-resolution cases are not rearmed by this rule.
Comments/checkboxes are not modified. No blind external replay or autoapproval.

Files: training contracts, local workflow, evidence-only executor, local Ollama
provider instructions, local-correction/training/Prefect tests, three continuity
layers. Modified Python compiled. Focused local correction 37; training 54;
configuration 5; readiness 5; runtime recovery 8; AI Correction 10; code pipeline
13; code authorization 5; activation gate 5; PS5.1 commands 7; row mapping 25;
destination typing 18; intake filename 20; filename assembly 28; business context
5; isolated Prefect 6: 251 unique checks passed. Continuity 11 and tracker
reconciliation 3 follow before commit. One summary schema regression initially
required its explicit safe-field expectation updated; rerun passed. Isolated
Prefect tests passed with the previously observed temporary SQLite cleanup warning.
No production server/deployment used by those tests.

PHI handling: protected local enum/field-name inspection only; all regression
fixtures synthetic/mock, plus real Windows process-lock and isolated Prefect
checks. No live mailbox/OCR/Ollama/document row/attachment/comment operations,
worker startup, code promotion or protected-state mutation in this fix task.
Project tracker is the only external write. Protected ignores/diff review and
tracker gates required before commit. Live proposal acceptance remains pending;
this fix does not assert that payer/service/date evidence or reference data can
resolve, and genuine uncertainty will still block an unsafe correction.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Fixed filename correction intent/scope and blocked-preparation reporting; added same-case contract recovery.",
  "key_result": "Retained safe enums prove the prior pre-replay field-scope rejection. Filename routing now aligns; service-line review remains evidence-bound. One audited retry is allowed with unchecked approvals.",
  "tests": "251 focused/affected synthetic/mock/isolated checks passed. Modified Python compiled; continuity/tracker checks follow.",
  "phi_handling": "Safe local enums only; no live document/model/feedback operations or protected-state mutation. Project tracker only.",
  "limitation_acceptance": "Live proposal verification remains pending. Genuine evidence/reference uncertainty and unrelated-field changes still fail closed.",
  "exact_next_start": "Refresh affected source registration, then run one controlled DP Training cycle on the existing flagged cases with both approval boxes unchecked. Verify the same-case contract upgrade produces a filename/service-line-review proposal or a specific safe preparation blocker, without resubmission or production correction. Stop training after that cycle. Request human approval only for a verified proposal; full correction/resolution/later-document learning acceptance remains pending."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Controlled Same-Case Retry and Proposal Coverage Guard - 2026-09-09

User directed continuation. Refreshed all four existing registrations to clean
67c7bc8 source. Prefect deploy --all ignored the version option; readback proved
correct working-directory source, zero schedules/parameters, then a version-only
DeploymentUpdate set and verified all four commit labels. No new deployment.
One owned local_correction cycle ran and graceful stop was requested. Same-case
upgrade reused existing identities; three flagged cases, two updated generations,
one proposed and two blocked; zero corrections, implementation attempts or Codex
dispatches. Training stopped; the immediate fresh heartbeat was settling only.

Exact protected association and selected workflow-cell readback proved the latest
row had a published matching Analysis Ready proposal, both approvals unchecked.
Its plan changed only AI Review Reasons, with no attachment change. The disputed
service-line date warning remained, overall dates were unchanged and unknown
subtype review remained. Thus neither reported issue was resolved; the valid
review-text update must not be represented as completed filename/date correction.

Authoritative cache loaded validly (12 payer mappings, 28 service mappings).
Approved row service-code-only lookup reported two codes, both ambiguous, no
unique naming match. Modifier/program were not inferred. This is not proof of the
replay's exact composite lookup or payer evidence, which the old plan did not
retain. No reference values or mappings were exposed or changed. The committed
multi-service naming rule also intentionally requires one shared resolved token.
No new business naming rule or delimiter was invented.

Added verified-action proposal rendering and a coverage gate: requested Filename
with no attachment change blocks as correction_requested_filename_unresolved,
including a previously proposed plan before approval execution. Old plan/audit
remain intact; no replay or human checkbox write. Presentation-only refresh cannot
consume an already checked approval. Stale workflow-owned resolution text is
cleared on a new proposal. This prevents misleading readiness, not a claim that
the unresolved source/reference facts have been repaired.

Files: local correction workflow, synthetic tests, continuity layers. Python
compilation passed. Local correction 41, training 54, AI Correction 10, code update
pipeline 13 = 118 checks passed. Prior 265-check baseline retained; continuity and
tracker gates rerun. Real controlled cached-evidence/local-model/feedback/proposal
operations occurred before this additional guard; no mailbox access, document
row correction, attachment update, checkbox mutation, code promotion or cloud
dispatch. The tracker is approved management-only. Full acceptance remains blocked.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Same-case live retry exposed an incomplete proposal; added verified-action coverage guard.",
  "key_result": "Routing fixed, but only review text changed; filename and disputed date warning did not resolve. Guard prevents misleading approval. Authoritative service code-only matches are ambiguous.",
  "tests": "118 focused/affected checks passed; prior 265-check baseline. Real controlled proposal cycle/readback; zero corrections or dispatches.",
  "phi_handling": "Approved local evidence/feedback and proposal operations; safe categories only. No human controls, mailbox mutation or document correction.",
  "limitation_acceptance": "Not end-to-end ready. Do not guess missing reference distinctions or call a partial unrelated update the requested fix.",
  "exact_next_start": "Publish the verified-action coverage guard to the existing proposal without re-extraction or approval. Preserve the same case and human controls. Investigate unresolved payer/service naming evidence and service-line date support; both displayed service codes have ambiguous code-only authoritative naming matches, so do not guess modifier/program or naming tokens. A review-text-only change that retains the disputed date warning is not the requested fix. Obtain authoritative business reference clarification if needed before another evidence replay; no resubmission or automatic approval."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Short-Year Evidence Validation and Safe Proposal Block - 2026-09-09

Committed 26b94ea coverage guard was registered for training and one saved-plan
cycle published the safe blocked state. Exact durable inspection proves
correction_requested_filename_unresolved and the old plan retained. Training
stopped. No automatic correction or approval occurred; no re-extraction was
needed for that existing-plan guard.

Source inspection found DATE_PATTERN/DATE_FORMATS accepted only four-digit years,
while FilenamePolicyService already accepted slash-separated two-digit years.
A count-only read of the exact fingerprint-associated existing flat OCR cache
found four two-digit-year and eight four-digit-year date tokens. No OCR, model or
document-value output occurred in that probe. This proves format mismatch exists
in relevant evidence, not that it alone explains every latest service-line warning.

Validator now accepts two-digit-year slash/hyphen date tokens with datetime's
same century interpretation already used by filename policy. Four-digit dates
are not truncated. Invalid dates, missing evidence and another line's date remain
rejected; no source borrowing, confidence inflation or quantity/approval inference.
No reference mapping or business naming token was guessed or modified.

Files: evidence_validation_service.py, test_short_year_date_evidence.py and three
continuity layers. Modified Python compiled. Permanent short-year tests 5,
evidence validation 29, quantity reconciliation 10, intake filename 20,
document processor 19, field diagnostics 12, row mapping 25, filename assembly 28,
local correction 41 = 189 unique synthetic/mock checks passed. Continuity and
tracker gates rerun. Prior coverage guard checks remain valid. Temporary probe
scripts are removed after use; protected paths remain ignored.

Remaining boundary: both displayed service codes have ambiguous code-only naming
matches. Their exact composite modifier/program evidence and payer readiness were
not retained by the replay plan. A safe filename cannot be forced from these
facts. Obtain authoritative local naming/reference clarification, and retain safe
component diagnostics on the next same-document evidence replay rather than
performing repeated blind model runs. Date fix is not yet live accepted. Neither
reported document correction has been applied, and full-chain readiness is not
claimed. No mailbox mutation, human-control write or cloud model dispatch.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Blocked the incomplete live proposal and fixed short-year date evidence validation.",
  "key_result": "Saved plan cannot be approved as a filename fix when no rename exists. Validator now agrees with filename date parsing while preserving service-line ownership. Training stopped.",
  "tests": "189 focused/affected synthetic checks passed; modified Python compiled. Prior live guard publication verified; date replay remains pending.",
  "phi_handling": "Exact cache date-format counts only; no text or values emitted. No document correction, human-control write or mailbox mutation.",
  "limitation_acceptance": "Filename references remain unresolved; code-only service matches are ambiguous. Do not guess mappings or claim end-to-end readiness.",
  "exact_next_start": "Resolve the authoritative filename naming-rule/reference ambiguity locally before another full correction replay; code-only service matches are ambiguous and payer composite readiness remains unproven. Preserve the existing blocked case and unchecked approvals. Refresh source registration for the short-year date-validation fix, then verify exact service-line evidence and naming diagnostics on the same document after supported reference clarification. Do not guess mappings, resend the document, or approve a plan that does not resolve the requested correction. Training is stopped; full acceptance remains incomplete."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Comma-Separated Authoritative Services - 2026-09-09

Operator clarified that two service names are separated by a comma. Shared
production filename assembly previously required every resolved lookup to return
one identical token, incorrectly forcing a placeholder for distinct valid services.
It now joins sorted distinct authoritative tokens with a comma. Each individual
lookup must still resolve; no modifier/program or payer mapping is inferred.
Existing supported identity selection and filename safety checks remain unchanged.
Manual, unattended and correction replay share this assembly. Persisted mailbox
attachment names are not recomputed; correction remains a separate approved path.
The payer reference list is pending and no document-specific mapping was added.

Files: production_filename_assembly_service.py,
test_production_filename_assembly_service.py and the three continuity layers.
Modified Python compiled. Synthetic/mock checks: assembly 30, policy 12,
builder 4, reference architecture 10, intake 20, correction 41, human feedback 10,
recovery 21 = 148 passed. Recovery functions ran with isolated temporary-path
fixtures (the file has no direct runner). Coverage includes order independence,
deduplication, unresolved individual lookups, temporary copy/source preservation,
persisted-name recovery, human ownership and correction safeguards.
Continuity/tracker gates run before commit. No live document, model, mailbox,
training, attachment or correction operation occurred; only approved PHI-safe
management tracker synchronization. No protected reference contents were read.
Full same-document and end-to-end acceptance remain pending; this change does not
prove the current document's individual reference matches have resolved.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Implemented approved comma-separated multi-service filename naming.",
  "key_result": "Distinct authoritative service tokens now join deterministically instead of forcing a placeholder. Individual ambiguous lookups remain unresolved; persisted names and approval protections are unchanged.",
  "tests": "148 synthetic/mock filename, reference, correction, feedback and recovery checks passed; modified Python compiled.",
  "phi_handling": "Synthetic data only. No live document, model, mailbox, correction or attachment operation. Management tracker only.",
  "limitation_acceptance": "Payer list and individual service reference resolution remain pending. No full live acceptance claimed.",
  "exact_next_start": "Obtain the operator's authoritative payer full-name/filename-token list through the approved local reference mechanism, and resolve any remaining service composite lookup ambiguity without guessing. Then refresh source registration and perform a controlled same-document correction verification for short-year date support and comma-separated service naming. Preserve the blocked case, existing job identity and human approvals; do not resend the document or approve an incomplete correction. Training remains stopped and full acceptance remains pending."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Existing Payer Reference Word-Spacing Compatibility - 2026-09-09

Operator confirmed the already-linked payer reference sheet is authoritative.
Read-only cache load succeeded with 12 payer rows and the supplied full-name
lookup resolved. Count/boolean-only inspection of the existing fingerprint-bound
OCR cache found the joined-word spelling, not the reference's spaced spelling.
No OCR engine, model, mailbox, comments or production row operation was run.
The prior plan did not retain the extracted payer, so this proves a relevant
lookup incompatibility, not the complete prior extraction/replay root cause.

PayorReferenceTable now permits whitespace-only compatibility after exact name
lookup fails, only for an omitted key and a unique authoritative result. Explicit
unsupported keys, competing results, abbreviations, punctuation variants and
substring matches remain unresolved. No hard-coded payer, alias list, fuzzy
matching or whole-document inference was added. Production assembly still
requires accepted field evidence. Read-only real cache verification proves both
word-spacing forms resolve to the same authoritative result. No values printed.

Files: reference_table_service.py, test_reference_table_architecture.py,
test_production_filename_assembly_service.py and three continuity layers.
Modified Python compilation passed. Synthetic/mock tests: reference 12,
assembly 31, local correction 41, AI Correction ownership 10, policy 12,
intake 20 = 126 passed. Tests cover collisions, unsupported explicit keys,
no abbreviation/punctuation inference, accepted evidence reaching naming and
low-confidence evidence remaining a placeholder. Continuity/tracker gates run
before commit. Same-document live acceptance remains pending; persisted names,
approvals, reference workbook and existing correction state were not modified.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Fixed whitespace-only payer naming lookup using the existing authoritative cache.",
  "key_result": "Cache is available; joined/spaced forms resolve to the same unique result. No replacement list, guessed alias or sender inference. Accepted field evidence remains mandatory.",
  "tests": "126 synthetic/mock checks and modified Python compilation passed; real read-only cache verification returned safe booleans only.",
  "phi_handling": "Existing protected cache inspection emitted booleans/counts only. No model, OCR, mailbox, comments or production row/attachment operation.",
  "limitation_acceptance": "Old extracted payer was not retained; live correction remains unverified. Existing case and human approvals unchanged.",
  "exact_next_start": "Refresh source registration and prepare one controlled same-document correction verification of whitespace-tolerant authoritative payer lookup, short-year date support and comma-separated service naming. Preserve the blocked case and audit history, retain human approval controls, and resolve any remaining individual service lookup ambiguity without guessing. Capture safe final naming diagnostics before presenting a new verified proposal; do not resend the document or approve an incomplete correction. The existing reference sheet is authoritative and no replacement payer list is needed. Training remains stopped; full acceptance is pending."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Audited Same-Case Preparation Upgrade - 2026-09-09

Training read-only status proves stopped, no active run and zero fresh workers.
Contract 3 permits one audited preparation upgrade of a blocked incomplete
filename plan without an attachment action and with both human approvals unchecked.
Other retained failures, applying/uncertain outcomes and checked approvals do not
rearm. Existing audit and reservation-before-inference remain intact. No new
feedback or document resubmission is needed. Executor retains value-free field
and naming diagnostics in sealed local audit storage before mapping failures.

Files: local_document_correction_workflow.py, evidence_only_correction_executor.py,
test_local_document_correction.py and continuity layers. Modified Python compiled;
44 correction, 54 training and 10 feedback synthetic/mock tests passed (108).
Tests prove one upgrade, audit preservation, approval/failure-scope exclusion,
no interrupted hot retry, and no values/source text/paths in retained diagnostics.
Tracker/continuity and Git safety gates precede commit. No live preparation or
row correction occurred in this checkpoint. Controlled same-case replay follows;
no complete workflow acceptance is claimed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Enabled one audited same-case preparation upgrade after verified naming fixes.",
  "key_result": "Incomplete filename plan may regenerate once with unchecked approvals; uncertain writes remain excluded. Value-free diagnostics persist before mapping failure.",
  "tests": "108 synthetic/mock correction, training and feedback checks passed; modified Python compiled.",
  "phi_handling": "Safe status only; no document processing or correction in this checkpoint. Diagnostics leakage regression passed.",
  "limitation_acceptance": "Controlled live same-case preparation remains pending. No approval or complete correction acceptance claimed.",
  "exact_next_start": "Refresh source registration and prepare one controlled same-document correction verification of whitespace-tolerant authoritative payer lookup, short-year date support and comma-separated service naming. Preserve the blocked case and audit history, retain human approval controls, and resolve any remaining individual service lookup ambiguity without guessing. Capture safe final naming diagnostics before presenting a new verified proposal; do not resend the document or approve an incomplete correction. The existing reference sheet is authoritative and no replacement payer list is needed. Training remains stopped; full acceptance is pending."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Controlled Replay: Payer and Dates Resolved, Service Still Unresolved - 2026-09-09

Registered training source b1fab8a and ran one bounded local training cycle with
graceful stop requested. Same case advanced under preparation contract 3 to a
proposal with one row update and an attachment-name change. No correction was
applied. Sealed final diagnostics prove accepted payer/start/end, two accepted
service codes/modifiers and both lines' accepted date endpoints. Payer and date
naming readiness are true; disputed service-line date reason is absent from the
proposed review text. Service-line status remains unsupported, not guessed.
Service naming readiness is false and the proposed name still contains [SERVICE].
Exact individual reference failure category was not retained; do not claim a
specific missing/ambiguous mapping is proven by this replay. Training stop reported
already exited with heartbeat settling. No document resubmission or mailbox run.

Requested-component coverage now blocks a proposed attachment change when an
explicitly requested payer/service component still has its placeholder. A change
to payer alone cannot be called the requested full filename correction. Unrelated
unknown subtype placeholders remain allowed. Existing saved proposals use the
same guard before approval. Files: local_document_correction_workflow.py,
test_local_document_correction.py and continuity layers. Python compiled;
45 correction plus 54 training synthetic/mock tests passed (99). Prior 10 human
ownership checks remain valid. Tracker/continuity gates precede commit.
Live local Ollama/cached-OCR and approved proposal operations occurred; diagnostics
only exposed booleans, confidences and field states. No correction upload, human
checkbox change, cloud dispatch, source-code promotion or mailbox mutation.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Controlled same-case replay verified payer/date fixes; blocked incomplete service naming correction.",
  "key_result": "Payer and both service-line date checks pass. Service token still unresolved. Partial improvement cannot satisfy explicitly requested missing components.",
  "tests": "99 correction/training synthetic checks passed; live local replay diagnostics verified payer/date readiness. Full correction not applied.",
  "phi_handling": "Approved local replay/proposal path; only safe diagnostics emitted. No correction upload, human-control change, mailbox mutation or cloud dispatch.",
  "limitation_acceptance": "Service lookup outcome needs narrower diagnosis. Do not approve an incomplete filename proposal or claim end-to-end completion.",
  "exact_next_start": "Publish the tested requested-component coverage guard to the saved same-case proposal without repeating inference. Payer naming and both service-line dates passed controlled replay; service naming remains unresolved despite accepted code/modifier evidence. Diagnose exact individual service reference outcomes with value-free lookup diagnostics before any further correction replay. Preserve verified work, case/job identity, audit and human controls; do not approve the partial filename correction, guess mappings or resend the document. Full acceptance remains pending."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Exact Service Reference Blocker and Stopped Runtime - 2026-09-09

Committed 738f827 was registered for training. One saved-proposal guard cycle
blocked the current incomplete filename correction, retaining its plan and audit.
StopDPTraining returned dp_training_stopped. No correction was applied.

One narrowly scoped local Ollama/cached-OCR diagnostic replay then completed one
extraction attempt and deterministic validation, without a row/attachment writer.
It used the same protected source binding/fingerprint and retained safe lookup
facts in sealed audit storage. Two accepted service identities had explicit
modifier and program inputs. Each code exists in the authoritative reference;
each code/modifier pair exists; neither exact program-qualified key exists and
both production lookup calls returned not_resolved, not ambiguous. No values,
tokens, source text, identifiers or protected paths were printed. The source
document and reference workbook were not changed. No mailbox or cloud call.

This narrows the remaining blocker to the authoritative relationship between
the validated document program and SERVICES LISTING program-qualified entries.
It does not authorize treating a payer/product program as a service program,
omitting a conflicting discriminator, or inventing a compatible mapping. Business
reference clarification is required before another model replay. Payer naming
and both service-line dates already passed the preceding controlled replay.
Unsupported service-line status remains safely reviewed. No human approval was
checked, consumed for correction, or replaced by developer approval.

Temporary diagnostic helpers removed after completion. Application code remains
at the tested requested-component guard; only final continuity truth changes.
Prior 99 correction/training checks and 10 human-ownership checks apply; 14
continuity checks and tracker/Git safety gates rerun at this coherent checkpoint.
No full correction/resolution/later-document learning acceptance is claimed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Verified payer/date fixes and isolated the exact remaining service reference blocker.",
  "key_result": "Both code/modifier pairs exist; neither program-qualified lookup resolves. Incomplete proposal blocked and retained. Training stopped; no correction applied.",
  "tests": "Prior 99 correction/training plus 10 ownership checks; one bounded cached/local diagnostic replay with one extraction attempt. Continuity gates rerun.",
  "phi_handling": "Safe booleans/categories retained locally; no values emitted. No correction write/upload, mailbox mutation or cloud model dispatch.",
  "limitation_acceptance": "Authoritative program-to-service reference clarification required. No more inference before that boundary is resolved; approvals remain human-owned.",
  "exact_next_start": "Obtain authoritative clarification in the SERVICES LISTING reference for the document's explicitly validated program with each supported service code/modifier pair. Both pairs exist, but neither program-qualified lookup resolves. Do not omit the program, guess another mapping or rerun inference before this reference/business relationship is settled. Then regenerate the same-case verified proposal, require human Approve AI Correction, verify existing-row/attachment correction, require human Approve AI Resolution and prove bounded same-type learning reuse. Payer/date fixes are live-evidenced; the incomplete proposal is blocked, Training is stopped and full acceptance remains pending."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Explicit Program-Independent Filename Policy - 2026-09-09

Operator clarified program is currently unimportant for filename/column output
and may be used later. Added ServiceReferenceTable.lookup_for_filename(code,
modifier), which considers compatible rows across programs and requires one
distinct authoritative naming token. A blank-program entry cannot conceal a
conflicting program-specific token. Production assembly uses this naming-only
lookup; generic program-qualified lookup and extracted program evidence remain
unchanged for future consumers. No guessing, reference edits or unrelated PHI
mapping changes. Shared manual/unattended/correction naming remains identical.
Persisted attachment names and human approvals are unchanged.

Files: reference_table_service.py, production_filename_assembly_service.py,
test_reference_table_architecture.py, test_production_filename_assembly_service.py
and continuity layers. Python compilation passed. Synthetic/mock tests: reference
13, assembly 32, correction 45, human ownership 10, intake 20, filename policy 12
= 132 passed. Read-only real cache aggregate: 25 code/modifier pairs, 22 unique
filename resolutions, 3 ambiguous. No values exposed. This does not identify
which aggregate pair belongs to the current document; no exact same-case lookup
success is claimed without retained inputs or controlled verification.
No inference, OCR, mailbox, training startup, document write/upload or comment
operation occurred. Approved management tracker sync and continuity/Git checks
complete the checkpoint. Full correction/resolution/reuse acceptance is pending.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Implemented explicit program-independent service filename lookup.",
  "key_result": "Naming uses accepted code/modifier only and rejects competing tokens across program rows. Program evidence and generic lookup remain preserved.",
  "tests": "132 synthetic/mock checks and Python compilation passed. Safe read-only cache aggregate: 22 unique pairs, 3 ambiguous.",
  "phi_handling": "Synthetic data and reference counts only; no model replay, mailbox, training or production document operation.",
  "limitation_acceptance": "Same-case proposal regeneration and human-approved correction/learning acceptance remain pending. No guessing of ambiguous reference tokens.",
  "exact_next_start": "Program has been explicitly excluded from current filename naming. Prepare an audited same-case proposal regeneration using the program-independent code/modifier lookup and existing payer/date fixes; preserve the old blocked plan and human controls. Verify each service token resolves uniquely, then obtain human Approve AI Correction for the complete existing-row/document correction, verify readback, obtain human Approve AI Resolution, and prove bounded same-type learning reuse. Do not guess competing service tokens or resend the document. Training remains stopped; no further inference ran during the program-policy update."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Same-Case Program-Policy Regeneration - 2026-09-09

Preparation contract 4 allows one upgrade of the specifically blocked incomplete
filename plan, including a partial but unapplied attachment-name change. Phase,
version and unchecked human controls remain mandatory; applying/uncertain states
still reconcile rather than regenerate. Old plan and case identity remain audited.
Unchanged feedback/context reuse the validated stored intent analysis, avoiding
another model analysis call. Only original-source replay supplies new values.
Changed context still requires analysis. Reservation precedes either path; failed
or interrupted preparation is not hot-retried.

Files: local_document_correction_workflow.py, test_local_document_correction.py,
continuity layers. Modified Python compiled. 46 correction, 54 training and 10
human-ownership synthetic/mock tests passed (110). No live operation yet; scoped
controlled verification follows registration. PHI-safe tracker and continuity
checks precede commit. Saved approvals and document row are unchanged.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Prepared one audited same-case regeneration for the approved naming policy.",
  "key_result": "Unchanged validated intent is reused; old partial plan retained in audit. Evidence replay and fresh human approval still required.",
  "tests": "110 synthetic/mock correction, training and ownership checks passed; modified Python compiled.",
  "phi_handling": "Synthetic-only verification; no live document or row operation in this checkpoint.",
  "limitation_acceptance": "Controlled same-case proposal verification follows; no complete correction/learning acceptance claimed.",
  "exact_next_start": "Program has been explicitly excluded from current filename naming. Prepare an audited same-case proposal regeneration using the program-independent code/modifier lookup and existing payer/date fixes; preserve the old blocked plan and human controls. Verify each service token resolves uniquely, then obtain human Approve AI Correction for the complete existing-row/document correction, verify readback, obtain human Approve AI Resolution, and prove bounded same-type learning reuse. Do not guess competing service tokens or resend the document. Training remains stopped; no further inference ran during the program-policy update."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Verified Naming Plan and Explicit Resolution Clear - 2026-09-09

One scoped production-workflow cycle reused unchanged intent and ran real local
Ollama against existing cached evidence. No mailbox discovery, OCR acquisition,
new document row, attachment upload, cloud model or human-control write occurred.
Two pre-inference harness checks failed at the protected runtime handshake;
neither reserved a generation nor ran inference. The corrected scoped harness
uses the same configured capability fingerprint, production lock and adapters,
filtering discovery to the current case only. Training deployment was refreshed
to 9a6b989 with no schedule, concurrency 1/CANCEL_NEW; no worker was started.

Result: exactly one generation; verified attachment-name plan and one review-field
update; payer/service/date readiness true, comma-separated services, no disputed
service-line date warning. Only unknown-subtype placeholder remains. Human
approvals unchanged/unchecked. Full polling and other flagged cases untouched.
Actual correction/resolution/learning acceptance remains pending.

Readback exposed a separate local publication defect: _publish requested an
empty AI Resolution Result to clear stale failure text, but the writer rejected
all empty strings. No external publication occurred for that request. The writer
now permits only that exact empty workflow-result clear, converts it to SDK
ExplicitNull and reconciles null/blank readback. Other empty fields, whitespace,
None, containers and human-field writes remain rejected. Exact human preconditions
are unchanged. Failed publication no longer increments analysis_ready_count; the
saved plan retries publication without repeating inference.

Files: local_document_correction_workflow.py,
smartsheet_document_processor_training_service.py,
test_document_processor_training.py, test_local_document_correction.py and
continuity layers. Modified Python compiled. 57 training/writer + 48 correction
+ 10 human-ownership synthetic/mock tests passed (115), including actual installed
SDK null serialization, lost-response reconciliation and no second write.
Live evidence was processed only in approved local/Smartsheet adapters; diagnostics
contain booleans/categories only. Publication-only verification follows this fix.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Verified same-case naming and fixed stale-resolution clear publication.",
  "key_result": "Payer, comma-separated services and dates resolve; date warning removed. Only unknown subtype remains. Saved plan awaits publication-only verification.",
  "tests": "115 synthetic/mock checks and Python compilation passed; one real cached/local same-case replay, zero corrections applied.",
  "phi_handling": "Protected evidence stayed local; only safe diagnostic categories exposed. Human approvals unchanged; no mailbox, cloud model, row correction or attachment upload.",
  "limitation_acceptance": "Human correction/resolution approval and learning reuse remain pending. No further model replay is needed for publication.",
  "exact_next_start": "Publish and read back the existing verified same-case proposal without reanalysis or evidence replay. Payer, comma-separated service tokens and dates now resolve; only unknown subtype remains. Then obtain human Approve AI Correction, verify the existing-row/document correction, obtain human Approve AI Resolution, and prove bounded same-type learning reuse. Preserve human controls and other flagged cases. Do not resend the document. Training remains stopped."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Same-Case Proposal Publication Verified - 2026-09-09

After 2a26ce8 was committed/pushed, one publication-only operation used the
existing production writer and correction-case lock. Exact input/context,
unchecked approvals and the saved verified plan were checked first. Readback
proves Analysis Ready, exact proposal/type match, stale AI Resolution Result
cleared and all three human controls unchanged. No generation, inference,
correction write or attachment upload occurred. The previous scoped local replay
already proved payer/service/date naming readiness, comma-separated services and
absence of the disputed date warning. Only unknown subtype remains unresolved.
Other flagged cases were not advanced. The runtime/worker was not started.

Files: continuity layers only for this live acceptance checkpoint; prior code
checkpoint has 115 focused synthetic/mock plus 14 continuity checks passing.
Only value-free booleans/categories were emitted. Temporary scoped verification
helpers are removed after use. Approved management tracker sync and Git gates
complete the checkpoint. Human correction approval is now the real boundary;
resolution approval, actual correction and later learning reuse remain unproven.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Published and verified the existing complete requested correction proposal.",
  "key_result": "Analysis Ready readback matches saved plan; stale result cleared and human controls unchanged. Payer/services/dates resolved; only unknown subtype remains.",
  "tests": "115 focused plus 14 continuity synthetic/mock checks passed. Live publication-only readback passed with zero model calls or applied corrections.",
  "phi_handling": "Approved workflow-owned fields only; safe booleans emitted. No mailbox, cloud model, document correction, attachment upload or human-control write.",
  "limitation_acceptance": "Awaiting human correction approval. Actual correction, resolution approval and learning reuse remain pending; Training stopped.",
  "exact_next_start": "Obtain human Approve AI Correction for the existing Analysis Ready proposal. Payer, comma-separated service tokens and dates are verified; only unknown subtype remains. Apply the saved same-row/document plan without reanalysis, verify row and attachment readback, then obtain human Approve AI Resolution and prove bounded same-type learning reuse. Preserve human controls and other flagged cases. Do not resend the document. Training remains stopped pending the human approval."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Approved Same-Plan Correction and Concrete Proposal Wording - 2026-09-09

Operator approved the saved correction and requested concise wording describing
what changes, explicitly including the date issue. Before changing presentation,
one scoped cycle consumed the actual checked Approve AI Correction through the
existing production state machine. Exact existing plan, generation and identity
were preserved. Original source/attachment identity and durable update intents
remained authoritative. The approved review-field update and attachment version
completed and passed readback; correction_applied_count=1, failures=0, model
calls=0. Human controls unchanged; Approve AI Resolution remains unchecked.
No mailbox, new document row, OCR, cloud inference or comments write occurred.

The proposal renderer now derives concrete text from saved before/after state:
resolved filename placeholders, named known review warnings removed/added, and
specific changed/cleared fields. No protected values or unknown reason text are
echoed. A date-warning removal is not described as changing accepted dates.
Existing pending-approval presentation safeguards remain unchanged. After the
approved plan completed, current proposal wording alone was refreshed under the
case lock with unchanged context/plan and original wording sealed in audit.
Readback proved it names payer/services and the service-line date warning;
there is no generic unclassified warning clause. No second correction/model call.

Files: local_document_correction_workflow.py, test_local_document_correction.py
and continuity layers. Modified Python compiled. Synthetic/mock tests: correction
51, training/writer 57, human ownership 10 = 118 passed. Live test classification:
approved Smartsheet existing-row/document update and readback; protected local
source used only by approved adapter, safe booleans emitted. Temporary helpers
removed after use. Tracker and continuity checks precede commit. Full resolution,
approved learning reuse and production generated-code promotion remain pending.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Applied the approved same-row/document correction and clarified proposal wording.",
  "key_result": "Readback passed; same plan/generation, zero model calls, human controls unchanged. Proposal explicitly names filename and date-warning corrections.",
  "tests": "118 focused synthetic/mock tests and Python compilation passed. One approved live correction and wording readback passed with zero failures.",
  "phi_handling": "Approved existing-row/attachment adapters only; no values emitted, mailbox access, OCR, cloud model, human-control or comment write.",
  "limitation_acceptance": "Awaiting human resolution approval. Learning reuse and production code promotion remain unproven; Training stopped.",
  "exact_next_start": "Have the operator inspect the corrected existing row and attachment, then check Approve AI Resolution if correct. The approved same-plan correction has passed readback: payer and comma-separated services are in the filename and the incorrect service-line date warning is removed. Consume only that fresh resolution approval, verify bounded approved learning and any permitted local update outcome, then prove later same-type reuse with controlled acceptance. Preserve human controls and other flagged cases; do not resend the corrected document. Training remains stopped pending resolution approval."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Resolution Accepted and Comment-Driven Review Snapshot - 2026-09-09

The operator approved the verified resolution. One scoped production-workflow
cycle consumed that fresh approval on the existing case, without document replay
or repeated correction. Case resolved_count=1, approved_lesson_count=1; the bounded
guidance is included by the production future-prompt renderer. Same plan and
generation, exact workflow-result readback and unchanged human controls were
verified. The optional local code update reached update_failed; no generated code
was installed, no activation quarantine remains, and no second generation was
attempted. Its exact failure cause is not retained; do not invent one. Fresh-app
restart verified the same case, lesson and code job with zero new resolution or
correction. Training and workers were not started. Later-document reuse is not yet
proven merely by prompt inclusion.

An additional approved business clarification makes AI Review Reason, Status and
Required an analysis-generation snapshot. Only new comments driving new analysis
may refresh it. Applying a saved correction, resolution approval, guidance
retention, unchanged polling and reconciliation preserve it. Preparation separates
candidate review before/after from correction updates. The workflow reserves a
review_refresh generation before a typed, sealed-intent, exact-readback write.
Lost responses reconcile; an unproven intent never repeats the update. Changed
comments/context cannot bypass an unresolved prior boundary. Own snapshot changes
advance the input digest without generating another analysis. Older unapplied
review-write plans fail closed rather than silently changing approved scope;
confirmed older transactions remain reconcilable. Minimum field confidence stays
with the current validated production fields.

AI Resolution Result uses fixed field/action labels from confirmed before/after
changes, with exact row readback before completion. It does not claim unchanged
review values were updated. The historical approved correction removed one
service-line date warning; read-only exact plan/current comparison proved it is
absent and five reasons remain. This happened under the prior approved behavior
and was not undone. No raw reasons or values were exposed. A raw boolean-only
review-required probe was not semantically reliable for text destinations and is
not used to claim review-required state.

Files: evidence_only_correction_executor.py, local_document_correction_workflow.py,
test_local_document_correction.py, new test_review_snapshot_lifecycle.py and the
three continuity layers. Modified Python compiled. Synthetic/mock tests passed:
snapshot 13, correction 51, training/writer 57, human ownership 10, reason summary
14, review decision 21, Smartsheet mapping 25, local-code authorization 5,
local-code pipeline 13, activation gate 5 = 214. Rollback tests are synthetic/mock,
not a real installed-code rollback. After regenerating the derived summary,
continuity checks passed 11 migration + 3 tracker tests (228 total checks).
Management tracker: Updated 1, Unchanged 37, Not Found 0, Failed 0. The initial
continuity check correctly rejected the still-old generated snapshot; no tracker
call ran until it was regenerated and checks passed. Protected-path and full diff
review passed. Temporary scoped helpers are removed after use.

Live classification: approved resolution workflow and protected guidance retention,
local-only optional code-update attempt, fresh-app restart and approved Smartsheet
readback. Only categories/counts/booleans emitted. No new mailbox/document access,
OCR, document extraction, attachment upload, cloud model, human-control write or
comment write. The new snapshot implementation itself has synthetic/mock coverage
only; no new live comment-driven analysis or correction was performed for it.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Accepted resolution and separated comment-driven review snapshots from correction results.",
  "key_result": "One approved lesson retained and included in future prompts; restart idempotent. Review refresh now has a separate typed/readback boundary.",
  "tests": "214 affected synthetic/mock checks and Python compilation passed. Scoped live resolution, guidance inclusion and restart verified.",
  "phi_handling": "Safe categories only; human controls unchanged. No mailbox, OCR, document replay, cloud model or comment write.",
  "limitation_acceptance": "Optional local code update failed safely; no installation. Later-document reuse and new snapshot live acceptance remain pending; Training stopped.",
  "exact_next_start": "Perform controlled acceptance with a different document of the same type to verify approved guidance reuse. For new flagged feedback, verify a new comment-driven analysis refreshes the review snapshot once; correction and resolution preserve it while AI Resolution Result describes confirmed changes. Verify restart/idempotency, preserve human controls and other cases, then stop Training cleanly. Do not resend the resolved document or retry the failed optional code-generation job blindly."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Later Same-Type Document Completed; Continuous DP Authorized - 2026-09-09

The operator supplied a different test document and explicitly authorized DP to
continue polling rather than stopping after every test. The first narrow-start
request was rejected by execution review before any startup; after the operator
clarified continuous polling authorization, the existing StartDP wrapper completed
all five stages. Live registration reflects source 7cbaf16. No new schedule or
silent reboot startup was added; Training was not started.

One new authorization document completed the full unattended path: OCR,
classification, two independent extraction/validation attempts, candidate selection
(attempt 1), business actions, new row creation, new attachment upload, mailbox
finalization and Workflow Summary. Document/written/completed counts are one;
failure count zero; row/attachment attempts one each; row outcome proven. This was
not reconciliation-only processing. The second extraction was the built-in bounded
retry, not a second flow or manual resubmission. Long OCR/model stages were
observed without interrupting or repeating them.

Read-only approved-adapter verification selected exactly one newly completed
durable job. Row identity, exactly one matching attachment, original correction
source binding and unchecked AI Correction were proven. Mapped value/confidence
presence mismatches are zero in both directions. This is a presence consistency
check, not independent proof of every extracted value or review warning.
Partial business filename has service and document-subtype placeholders; payer
and naming dates resolved. Nine review reasons remain. The operator must judge
the actual output in the approved sheet; no document values were exposed here.

The new document family matches the approved lesson. Direct-indexed bounded
guidance is present and included by the production extraction prompt renderer;
source wiring uses that renderer for extraction. No request body was captured or
printed, and no claim is made that the lesson caused improvement or that every
model instruction was followed. The prior optional code-update failure was not
retried. Correction workflow/comments/approvals for the new row were untouched.

Post-run status: DP running, ownership proven, polling waiting, no active bounded
run, one fresh owned worker, zero consecutive failures and not degraded. DP remains
running under explicit operator authorization. Training remains stopped pending
reviewer feedback. New comment-driven snapshot behavior still requires live
acceptance. The read-only watcher and readback helpers were removed after use.

Classification: real approved Graph/mailbox intake, local OCR/Ollama, explicitly
mapped Smartsheet row/attachment and mailbox finalization, plus read-only local
state/control-plane/Smartsheet verification. Safe booleans/counts/categories only;
no PHI, payload values, source text, identifying names, IDs or secrets emitted.
No cloud model, comment access/write or human-checkbox write. Tracked changes are
continuity layers only; current tested implementation is unchanged. Continuity
checks passed: 11 migration and 3 tracker tests, zero failures. Management tracker:
Updated 1, Unchanged 37, Not Found 0, Failed 0. Protected-path checks and full diff
review passed; no application code changed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Completed the later same-type unattended document test; continuous polling authorized.",
  "key_result": "One new row/attachment, zero failures; two extraction attempts, first selected. Exact readback and unchecked AI Correction verified. DP returned to waiting.",
  "tests": "Real approved end-to-end processing and readback passed; mapped value/confidence presence checks passed. Existing source unchanged.",
  "phi_handling": "Approved local and mapped production adapters only; safe counters/categories emitted. No cloud model, human-control write or comment access.",
  "limitation_acceptance": "Service/subtype placeholders and nine review reasons await assessment. Guidance inclusion is verified, not causal improvement. Training stopped; DP running.",
  "exact_next_start": "Have the operator review the new completed row and attachment, especially the service/subtype placeholders and remaining review warnings. If a correction is needed, flag that existing row and add ordinary feedback. Then perform scoped comment-driven Training acceptance: refresh the review snapshot once, obtain correction approval, apply/read back the saved existing-row/document plan, obtain resolution approval, and verify idempotency while preserving human controls and other cases. DP remains running by explicit operator authorization; Training is stopped. Do not resend either processed document or blindly retry the prior failed code-generation job."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Explicit Authorization Labels and Reserved Same-Case Recovery - 2026-09-09

The operator supplied comments on the new flagged row. One scoped production
Training analysis used local Ollama and the original protected cached source.
It completed blocked with correction_no_verified_change: zero corrections, no
saved plan, no attachment change, no review-snapshot refresh. Human controls and
comments were unchanged; blocked proposal/status readback matched. One feedback
analysis and one cached-source pipeline replay ran, not a full flagged-case sweep.
DP was stopped using only its proven-owned wrapper to release the shared source
lease. Training remained stopped. No Graph/mailbox access or fresh OCR was needed.

Read-only value-free diagnostics confirmed two service-code labels, two modifier
labels and an explicit Initial authorization statement in the cached source.
No same-OCR-block code/modifier pairing was proven. Code-only authoritative
reference lookup was ambiguous for both codes. Retained replay diagnostics showed
source-unsupported service-line codes and invalid modifiers, not accepted pairs
being rejected by the reference lookup. Exact malformed candidate shapes were not
retained, so no speculative parser repair or reference widening was performed.

The user-approved labeled Initial clarification exposed a deterministic blanket
external-context veto. Shared context v4 and the naming validator now accept a
complete, confidence-qualified Type of Authorization: Initial candidate statement.
Generic Initial wording, competing options, negation, missing candidate, wrong
category and low confidence still fail closed. Inferring new-client/service
history still requires authoritative external evidence. Category confidence and
intake subtype remain separate; internal subtype key remains init, filename token
AUTH INIT. Extraction instructions now recognize HCPC Code/HCPCS and Modifier(s)
labels within one supported service section, require scalar child values and owned
supporting evidence, and prohibit cross-section/reference-based guessing. Existing
prompt size bounds remain enforced; redundant wording was condensed, not expanded
without limit. Live service recognition improvement is not yet proven.

Preparation contract 5 narrowly rearms a version-4 blocked authorization filename
case only for the addressed no-verified-change/unresolved-filename failure and
subtype/service scope. Existing pre-v4 migration guards remain. The reservation
precedes inference, keeps the same identity/audit, reuses unchanged validated
intent, preserves approvals and excludes other version-4 failures. No unchanged
comment review-snapshot refresh or automatic correction is authorized by upgrade.

Files: shared business-context model/renderer, intake naming vocabulary, Ollama
extraction prompt, local correction workflow, context regression, two new synthetic
label/recovery regression files, and continuity layers. Modified Python compiled.
257 focused/affected synthetic/mock checks passed: labels 12, context 5, intake 20,
Ollama schema/prompt 21, evidence 29, production naming 32, validated naming 10,
reference builder 4, quantities 10, review reasons 14, snapshot 13, correction 51,
AI Correction ownership 10, mailbox recovery 21, label-upgrade recovery 5. The
mailbox test module has no runner; all 21 functions were explicitly invoked with
isolated synthetic temporary state. Initial prompt-bound failure was corrected
and the affected suites rerun. No synthetic test contacted an external adapter.
Continuity checks also passed (11 migration + 3 tracker), 271 total checks.
Management tracker: Updated 1, Unchanged 37, Not Found 0, Failed 0. Protected paths
remain ignored, and git diff --check passed. No PowerShell source changed.

PHI handling: fixed categories/counts/booleans only; no values, identifiers,
filenames, source, comments or secrets emitted. Live activity before the fix was
the authorized scoped local analysis, protected cached evidence, approved row
readback and workflow-only blocked-state publication. No correction write,
attachment upload, mailbox mutation, human-checkbox/comment write or cloud model.
Real post-fix revalidation remains pending; no success claim is made for the row.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Fixed explicit Initial evidence handling and service-label instructions; reserved narrow same-case recovery.",
  "key_result": "Shared context v4 accepts validated labeled Initial without history inference. Preparation v5 permits one guarded replay, preserving approvals and snapshot.",
  "tests": "257 synthetic/mock checks passed; Python compiled. Prompt size, evidence, naming, recovery, snapshot and human ownership covered.",
  "phi_handling": "Safe categories only. Scoped prior analysis blocked without correction; no cloud model or human-control/comment write.",
  "limitation_acceptance": "Current row remains blocked; real post-fix replay pending. No reference/modifier guessing. DP paused for exclusive maintenance; Training stopped.",
  "exact_next_start": "Refresh affected source registrations, then perform one scoped same-case cached-source revalidation under preparation contract 5. Reuse validated feedback intent, preserve the existing review snapshot on unchanged comments, and require both approvals unchecked. Verify a saved evidence-supported subtype/service/filename correction before requesting approval; do not claim success if still blocked. No resubmission or blind replay. Resume authorized DP polling after exclusive maintenance; keep Training stopped outside scoped acceptance."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## Label-Fix Live Replay Remains Safely Blocked - 2026-09-09

Implementation d3114dc was committed, pushed and synchronized before revalidation.
Manual, live and Training registrations were refreshed to that source. Read-only
verification proved unique registrations, no schedules, parameterless invocation,
concurrency one and CANCEL_NEW. Control-room readiness was true with no active
manual/live/Training conflict and zero fresh workers before the scoped replay.

One scoped production cycle used the new tested contract-5 reservation on the
existing blocked case, with both human approvals unchecked and unchanged input.
The validated intent was reused: zero feedback model calls. One cached-source
DocumentProcessor replay completed classification and two independently validated
extraction attempts, followed by deterministic candidate selection. No fresh OCR
or mailbox document acquisition was needed. The result remained blocked with
correction_unrelated_field_change, no saved plan, no applied correction, no
attachment change and no review-snapshot refresh. Blocked proposal/status readback
matched; human controls and comments remained unchanged.

Retained value-free diagnostics prove supported payer/start/end-date state at
candidate confidence 0.90, while both service-line codes remain unsupported and
modifiers invalid. Service and document-subtype placeholders remain; payer/date
readiness is true and the final naming result is partial_business. These are
diagnostics of the replay, not production field updates. Exact out-of-scope
column differences and candidate shapes were not retained by the existing
diagnostic contract. A further read-only comparison proves both start/end-date
confidences differ from their current mapped cells, outside the requested scope.
The full difference set and whether actual date values also changed cannot be
proven from retained diagnostics; no confidence-only explanation is assumed.
The tested explicit-label policy correction is real, but prompt
changes did not resolve the current document; no successful proposal is claimed.

A fresh-app unchanged follow-up preserved the same case generation and made zero
feedback model, document replay, correction or attachment calls. The consumed
reservation cannot hot-retry. It did not start a full Training sweep or modify
other cases. No code generation, resolution approval, human-checkbox write,
comment write or cloud model occurred. Production DP was restarted through the
existing owned wrapper after the exclusive replay, under the operator's explicit
continuous-polling authorization. Training remains stopped. The restarted DP may
perform normal authorized bounded mailbox scans; this is distinct from Training's
cache-only replay. No claim is made that the current row is ready for approval.
Final runtime readback proved DP ownership, waiting state, one fresh worker, no
active bounded run, zero consecutive failures and no degradation. Training has
zero fresh workers and is stopped. Temporary scoped diagnostic helpers were
removed after use; no protected data was removed.

Classification: real approved local Ollama/cached evidence and mapped workflow
publication/readback, plus read-only protected state/control-plane checks and
normal owned-DP startup/authentication. Only fixed safe categories/counts/booleans
emitted. The sandboxed process inventory was denied; its zero count was discarded
and an approved read-only inventory confirmed the active replay. No underlying
provider errors, values, filenames, IDs, comments or secrets were printed.

Post-acceptance continuity checks passed: 11 migration and 3 tracker regressions.
Management tracker: Updated 1, Unchanged 37, Not Found 0, Failed 0. Full continuity
diff and git diff --check passed. This checkpoint changes documentation only;
registered executable source remains d3114dc. No further model replay was made.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Verified the committed label fix through one guarded same-case replay; correction remains blocked.",
  "key_result": "Intent reused, two extraction attempts validated, no correction applied. Unchanged follow-up was idempotent with zero inference. DP resumed; Training stopped.",
  "tests": "Prior 271 source/continuity checks passed; real scoped replay, readback and restart-idempotency checks completed. Recognition acceptance failed safely.",
  "phi_handling": "Safe diagnostics only; approvals/comments unchanged. Cache-only Training replay, local Ollama, no cloud model or document correction/upload.",
  "limitation_acceptance": "Service/subtype remain unresolved; unrelated-field change blocks the plan. Exact changed columns/candidate shapes were not retained. Do not approve or blindly replay.",
  "exact_next_start": "Resolve the current blocked correction without another blind extraction: add value-free candidate-shape and exact mapped-field-difference diagnostics at the normalization/validation and unrelated-change boundaries, reproduce the service-line/explicit-subtype failure with synthetic cross-layer tests, and fix only the proven defect. Preserve current human controls, review snapshot and same-case recovery; contract 5 is already consumed. Do not request approval or resend a document until an evidence-supported saved correction is verified. DP polling remains authorized; pause only for exclusive source/replay maintenance. Training stays stopped."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## 2026-09-09 — Extraction shape and correction difference checkpoint

Continued from clean synchronized main at 7e8fb113cbc1565b8202eb1655d4d9b803074342,
without resetting the existing correction or replaying the document. Read current
instructions/state/history and inspected the provider, candidate validation,
subtype, mapping, correction guard and their callers/tests. Stopped only the
proven-owned waiting DP for source maintenance; Training was already stopped.
No active bounded run was interrupted. Control room and PostgreSQL were not stopped.

Proven source defect: service-line code/modifier/date/status and evidence
containers could be stringified by the provider/processor adapter before
deterministic validation, hiding their original invalid structure. They now
remain raw internal candidates, and deterministic type checks reject invalid
containers, booleans or inappropriate numbers before production mapping. No
nested candidate is unwrapped and no evidence, modifier or subtype is guessed.
Unsupported service-line production fields stay blank. Fixed field-specific
Invalid review reasons replace generic interpretation of these new shape actions.
Valid flat supported code/modifier evidence still passes the same validation.

Added ExtractionShapeDiagnosticService version 1. Raw model structure is recorded
before normalization; normalized adapter structure is recorded before validation.
Both extraction attempts retain independent diagnostics and the selected attempt
is recorded separately. Output is restricted to fixed field names, logical types,
presence/multiline flags, counts and deterministic subtype-evidence categories.
Only 64 line shapes per attempt are retained, with an omitted count; processing
itself is not limited to 64 lines. Projection is repeated before sealed audit
storage and discards unknown keys/values. Diagnostics do not stringify unknown
objects or add model calls, prompts or token consumption. The existing complete
explicit-label subtype rule is unchanged; ambiguous/competing evidence still
fails closed independently from category confidence.

Added CorrectionDifferenceDiagnosticService version 1. Immediately before the
unrelated-field guard, it records exact differences using the same comparison
semantics as the guard. Emitted names come only from static approved mappings.
Unknown columns are counted without exposing their names. Records distinguish
value/confidence/metadata, current/replay type and presence, requested/dependent/
ignored/blocked scope and whether a confidence change also changes its governing
value. Distinct safe diagnostics are retained by digest plus a latest pointer.
No field values, IDs or hashes are exposed. Confidence-only changes still block
when outside scope; this checkpoint does not weaken whole-candidate consistency,
replace human controls, mix extraction attempts or refresh review snapshots.

Synthetic tests reproduce valid labeled service/subtype candidates and invalid
container cases through adapter, validation and mapping. They verify value-free
projection, bounded retention, subtype confidence/support separation, exact
confidence-only versus governing-value changes, unknown-column suppression,
guard-before-write behavior, independently retained attempts, AI Correction
ownership and unchanged correction/recovery behavior. The historical live model
shape and full changed-column set remain unavailable: do not infer that nested
containers were the actual live cause. No live replay was performed to fill that
gap. Existing contract 5 is still consumed; no case, approval or retry re-arm was
changed. The current row is not claimed corrected or ready for approval.

Files: ollama_provider.py; document_processor.py; evidence_validation_service.py;
evidence_only_correction_executor.py; review_reason_summary_service.py; new
extraction_shape_diagnostic_service.py and correction_difference_diagnostic_service.py;
new test_extraction_correction_diagnostics.py; test_local_document_correction.py;
PROJECT_STATE.md; PROJECT_HISTORY.md; derived PROJECT_SMARTSHEET.md; and
update_project_tracker.py. No PowerShell was modified.

Validation: modified Python compilation passed before tests. Final unique test
counts: diagnostics 15, local correction 51, explicit labels 12, Ollama adapter 21,
DocumentProcessor 19, evidence validation 29, review reason 14, label recovery 5,
review snapshot 13, AI Correction 10, quantity rule 8, intake naming 20, production
filename assembly 32, business context 5, scalar confidence 6, missing-confidence
mapping 6, service quantity reconciliation 10, validated filename inputs 10,
reference architecture 13, project migration 11, tracker reconciliation 3, durable
mailbox recovery 21, bounded local code pipeline 13, code approval 5, Training
restart recovery 8 and isolated Prefect lifecycle 7: total 367 passed, zero failed.
Classification: synthetic deterministic/mock, with isolated local Prefect only.
No live Ollama, OCR, Graph/mailbox content, document write/upload, comments or
approval mutation occurred. Full source/test/continuity diff and git diff --check
passed; all six protected-path ignore checks passed and sensitive-pattern review
found no matches. Management tracker: Updated 3, Unchanged 35, Not Found 0,
Failed 0. Continuity migration/tracker checks were rerun after the update and
passed. Registration remains at the prior executable source until
explicit refresh; DP and Training are stopped at this source checkpoint.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Added safe extraction-shape and exact correction-difference diagnostics; rejected malformed service-line containers before production mapping.",
  "key_result": "Independent attempts remain separate. Invalid candidates are preserved internally. Confidence drift is visible but cannot bypass correction scope or human ownership.",
  "tests": "367 synthetic/mock checks passed, including isolated Prefect, rollback, restart, mapping and recovery. Modified Python compiled.",
  "phi_handling": "Only fixed labels, types, counts and flags retained. No live model, document replay, correction, comments or approval changes.",
  "limitation_acceptance": "Current live case remains blocked; historical raw shapes were not retained. Contract 5 is consumed. DP paused for maintenance; Training stopped.",
  "exact_next_start": "Refresh affected source registrations, then use one explicitly bounded diagnostic-only cached-source replay of the existing blocked case to capture raw/adapter shapes and exact mapped-field differences. Preserve the consumed generation, review snapshot, comments, approvals and row/document; do not blindly re-arm contract 5 or resend the document. Reproduce the proven cause synthetically before changing validation or correction scope. Training stays stopped; resume authorized DP polling after exclusive maintenance and current-source verification."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## 2026-09-09 — Diagnostic source registration verified

Committed and pushed the tested diagnostic source as
db4509d0a33897044530f30d2b507a9e4b940836; local/remote divergence zero and clean
tree verified. Refreshed the manual, live and Training deployment registrations
using the installed Prefect profile/deploy mechanism. Exact JSON readback proves
each deployment unique, current at that executable commit, zero schedules, zero
parameters and concurrency one/CANCEL_NEW. Old-name deployment count is zero.
The first PowerShell readback wrapped the response array incorrectly; its derived
counts were discarded, and typed JSON verification established the actual result.
Control-room/PostgreSQL readiness is true, no active manual/live/Training run
conflict exists and each worker count is zero. No worker or deployment invocation
was started. DP and Training remain stopped for exclusive diagnostic maintenance.
No document, model, mailbox, comment or correction operation occurred.

The current case remains blocked and consumed under contract 5. Source refresh
does not grant another production attempt or change human approval. Next is a
bounded diagnostic-only replay with writes disabled, not a production retry.
This checkpoint updates continuity only; the 367 source checks remain applicable.
The first continuity test caught a stale generated summary before any tracker
write. Regenerated it, then all 11 migration and 3 tracker checks passed.
Tracker: Updated 1, Unchanged 37, Not Found 0, Failed 0. Summary length 1,195
characters. Full continuity diff and git diff --check passed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Committed diagnostic source and refreshed manual, live and Training registrations.",
  "key_result": "Unique current deployments, no schedules/parameters, concurrency one/CANCEL_NEW. No active run conflict or fresh worker. DP and Training remain stopped.",
  "tests": "367 source checks passed; exact typed registration and PHI-safe control-plane readback verified.",
  "phi_handling": "Control-plane operations only. No model replay, document write/upload, mailbox, comments or approval changes.",
  "limitation_acceptance": "Current correction remains blocked; contract 5 is consumed. Diagnostic instrumentation is registered but has not been exercised on that document.",
  "exact_next_start": "Use one explicitly bounded diagnostic-only cached-source replay of the existing blocked case to capture raw/adapter shapes and exact mapped-field differences. Preserve the consumed generation, review snapshot, comments, approvals and row/document; do not blindly re-arm contract 5 or resend the document. Reproduce the proven cause synthetically before changing validation or correction scope. Training stays stopped; resume authorized DP polling after exclusive maintenance. Registered executable source is db4509d0a33897044530f30d2b507a9e4b940836."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## 2026-09-09 — Proven confidence-only correction blocker and retained evidence

Executed the one authorized diagnostic-only cached-source replay, reserving a
separate sealed receipt before inference. It used three local Ollama requests:
classification and two independently validated extraction attempts. All raw
candidates and the validated snapshot remain in approved current-user encrypted
local audit storage. The temporary transport boundary allowed only local model
requests and approved read-only Smartsheet schema/selected-row/attachment access;
production writes and comments were blocked. Cached OCR was reused, no fresh OCR
or Graph/mailbox document operation occurred. The replay completed with the same
correction_unrelated_field_change category, no plan, and proven unchanged case,
generation and row. Zero production writes, uploads or comment access occurred.

Exact retained differences prove five out-of-scope scalar confidence changes:
Authorization # Conf., Days Per Week Conf., End Date Conf., Hours Conf. and
Start Date Conf. Their governing mapped values did not change. Service Codes
Conf. was requested; the minimum was dependent; AI Correction's initialization
difference was ignored and never written. The two extraction attempts both used
ordinary scalar service-line strings, disproving nested containers as this run's
cause. Service-code candidates were absent from their own line excerpts;
modifiers failed the current single-modifier format. The subtype candidate was
noncanonical, with confidence 0.80 below the existing 0.85 threshold. Those facts
do not prove the document lacks the evidence. They do not justify borrowing
other sections' evidence, splitting/guessing modifiers or inflating confidence.

Implemented CorrectionRowProjectionService as an existing-row patch boundary,
not an extraction merger. Preserve only code-approved scalar confidence pairs
outside requested scope when the replay independently maps the identical
nonempty accepted value and both confidence values are finite numeric, within
the configured acceptance threshold and candidate maximum (inclusive). Missing,
changed, unsupported, invalid, low-confidence and classification confidence
differences remain guarded. No source candidate, value/confidence evidence,
validation, reference or naming policy is changed. The displayed minimum uses
the actual projected explicit value/confidence pairs. Preserved pairs enter
exact fresh-read and apply/restart preconditions; concurrent edits block writes.
Requested fields retain the selected candidate's confidence. Raw differences and
projection counts are sealed together to avoid stale/misleading diagnostics.
Human checkboxes/comments and analysis-generation review-snapshot ownership are
unchanged. No contract bump, rearm, inference retry or production correction.

Applying the pure projection to the retained encrypted replay reduced unrelated
differences from five to zero, retaining five original confidences. This check
made zero model calls, zero network requests and no case changes. It does not
prove the requested filename components resolved. The case is not ready for
approval; extraction/evidence coverage still needs correction using retained
data rather than another blind replay. DP and Training remain stopped during
exclusive maintenance; continued DP polling remains authorized afterward.

Files: new correction_row_projection_service.py; evidence_only_correction_executor.py;
new test_correction_confidence_projection.py; PROJECT_STATE.md; this history;
update_project_tracker.py; derived PROJECT_SMARTSHEET.md. No PowerShell changed.
Initial synthetic fixture assertions incorrectly expected duplicate identical
lines to survive deduplication and rejected subtype evidence to be erased; the
fixtures were corrected to test distinct lines and final subtype resolution.
Production evidence preservation was not weakened to satisfy those assertions.

Validation before continuity: modified Python compilation passed; projection 15,
local correction 51, extraction diagnostics 15, review snapshot 13, AI Correction
10, label recovery 5, intake filename 20, production filename assembly 32,
missing-confidence mapping 6, durable mailbox recovery 21, local code pipeline 13,
code authorization 5, Training restart 8 and explicit labels 12: 226 passed,
zero failed. All are synthetic deterministic/mock; durable tests used isolated
temporary state with explicit fixture invocation, not an empty script run.
Separate real diagnostic classification: cached-source/local Ollama and read-only
Smartsheet, no protected content exposed. Git fetch succeeded and local/remote
divergence was zero before changes. Registration remains at the prior executable
commit until explicitly refreshed; no deployment/worker was started here.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-09",
  "work_summary": "Diagnosed the blocked correction and fixed unrelated accepted-confidence drift in scoped row patches.",
  "key_result": "Retained replay proves five confidence-only blockers now project to zero. Values, human state and candidates remain unchanged; no case rearm or publication.",
  "tests": "226 synthetic/mock checks passed; modified Python compiled. Retained-candidate projection passed without further inference or network.",
  "phi_handling": "One reserved local-model/cached-source diagnostic; candidates encrypted locally. No production write, upload, comments, mailbox access or approval change.",
  "limitation_acceptance": "Service-line evidence and subtype remain unresolved. Current row is not corrected; consumed case stays blocked. DP and Training stopped for maintenance.",
  "exact_next_start": "Use the retained encrypted candidates and cached source structure to resolve incomplete service-section evidence and the noncanonical low-confidence subtype candidate, without another model replay or relaxed validation. Prove a supported filename recovery path synthetically before re-arming the consumed case. Preserve the same generation, review snapshot, comments, approvals and row/document. Refresh affected source registration before runtime use; Training stays stopped and authorized DP polling resumes after exclusive maintenance."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

Checkpoint completion: 11 continuity migration and 3 tracker reconciliation tests
passed, bringing the unique synthetic/mock total to 240. Management tracker:
Updated 2, Unchanged 36, Not Found 0, Failed 0. Derived summary is 1,297 characters.
Protected-path ignore checks passed for all six guarded locations. Full reviewed
source/test/continuity diff and git diff --check passed. Temporary diagnostic
scripts and their two generated bytecode files are removed; encrypted diagnostic
receipts/candidates remain retained for safe continuation, not discarded.

## 2026-09-10 - Proven local-model truncation and complete-input recovery contract

Read-only retained encrypted metrics and fixed server-log metadata correlate the
failed second extraction with a truncation event: input 4426, retained 2050.
The first attempt evaluated 4074 tokens; the second returned complete-looking
JSON despite truncated input. Candidate completeness was not input completeness.
No raw server log, source text, model result, patient value or identifier was emitted.
Installed local server 0.33.3 and model context capacity 131072 were verified.

The shared provider now verifies local identity, exact tested API contract and
authoritative model capacity before protected input. Explicit configurable 8192
context / 4096 maximum output replace automatic defaults. Native truncate=false
and shift=false prohibit input/context discard. Only done=true/reason=stop may
be parsed as candidates. Unknown API versions, invalid budgets, incomplete output
and transport errors fail closed with fixed safe categories. Metrics whitelist
finite numeric counts/timings and fixed completion categories; no exception text.
No confidence/evidence policy change, candidate merging, new model or cloud use.

Preparation contract 6 permits one narrowly scoped blocked version-5 filename
case re-entry, both human approvals unchecked, same identity and archived prior
generation. Reservation precedes inference; interruption does not hot-retry.
Intent is reused only with unchanged row/comment digest. No source-only review
snapshot refresh and no correction application before fresh approval.

Files: ollama_provider.py; local_document_correction_workflow.py;
test_ollama_context_contract.py; test_context_correction_recovery.py;
test_label_correction_recovery.py; docs/local_ollama_context_contract.md;
PROJECT_STATE.md; PROJECT_HISTORY.md; update_project_tracker.py; derived
PROJECT_SMARTSHEET.md. No PowerShell modifications.

Validation: modified Python compiled. 273 unique synthetic/mock checks passed:
context boundary 13, context recovery 5, label recovery 5, local correction 51,
confidence projection 15, explicit labels 12, Ollama service lines 21,
diagnostics 15, review snapshot 13, AI Correction 10, local code pipeline 13,
code authorization 5, Training restart 8, migration 11, tracker reconciliation 3,
intake filename 20, production filename assembly 32, durable recovery 21.
An initial sandbox bytecode denial was rerun with authorized repository access.
A quoting error prevented the first durable runner from starting; a corrected
isolated runner executed all 21 tests. Neither was reported as a passing test.

Real local synthetic API probes: oversized input rejected with no candidate;
small valid response completed, runtime context readback 8192. No document input,
OCR, mailbox access or production write/upload occurred in these probes.
The document-specific full-context recovery remains pending; API success does
not prove model correctness. DP and Training remain stopped for maintenance.

Checkpoint gates: regenerated summary and continuity/tracker tests passed after
refreshing the initially stale generated snapshot. Tracker Updated 2, Unchanged
36, Not Found 0, Failed 0. Protected ignore checks and git diff --check passed.
An attempted completion-note insertion used a stale anchor and made no change;
the note was inserted at this verified checkpoint boundary instead.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-10",
  "work_summary": "Proved silent Ollama input truncation and implemented a fail-closed complete-input contract.",
  "key_result": "Explicit context/output budgets and no truncation/context shift; one reserved same-case contract-6 recovery preserves human controls.",
  "tests": "273 synthetic/mock checks passed; Python compiled. Local synthetic overflow rejection and 8192-context success probes passed.",
  "phi_handling": "Fixed metadata only; no document replay, production write/upload, mailbox or approval change.",
  "limitation_acceptance": "Actual correction still awaits complete-context recovery. DP and Training stopped for maintenance.",
  "exact_next_start": "Refresh affected source registration, then run one reserved contract-6 recovery of the existing blocked correction case using cached OCR and complete local-model context. Preserve human controls, comments, review snapshot and row/document until fresh correction approval. Verify requested filename evidence and concise proposal, then prove unchanged-cycle idempotency. Do not blindly repeat a failed replay. Resume authorized DP polling after exclusive maintenance; Training remains stopped until needed."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## 2026-09-10 - Complete-input source registration and enforced acceptance boundary

Source fix committed/pushed as 8fee328cb52025dfc5b19796583e4653b4dd7261;
local/remote divergence 0/0 and clean tree. All four existing Prefect registrations
refreshed using the repo CLI. Readback reports version 8fee328c (the CLI's shortened
commit form), empty schedules/parameters, and concurrency 1/CANCEL_NEW on manual,
live and Training deployments. Status confirms zero fresh workers and active runs,
DP/Training stopped and PostgreSQL/control room reachable. No flow invoked.

The scoped recovery helper first stopped before model/case access because its
version check expected a full SHA. Correcting it to the verified CLI representation
passed registration checks. The next preflight stopped at the existing frozen
Training-capability gate; the helper was aligned with the wrapper's protected
configuration fingerprint without changing that configuration. Both stops were
pre-inference and pre-recovery reservation. Windows PowerShell status initially
needed its repo-supported process-only ExecutionPolicy argument; no global policy
changed. A wildcard text search was corrected by reading the known wrapper.

Automatic safety review then denied the actual scoped recovery command because
earlier trusted task instructions prohibited live production operations. The denial
was not bypassed. Explicit approval is needed for local cached-document inference
and proposal-only publication; actual correction/upload still requires fresh human
approval. No protected model replay, proposal write or source/row/document change
occurred. The read-only owner-context state check confirms one matching case:
blocked, generation 2, preparation contract 5, no plan, no reserved new recovery,
no Training-operation lock. Sandbox-context decryption could not read the sealed
state; owner-context read-only execution succeeded without network calls or writes.

Final checkpoint: tracker Updated 1, Unchanged 37, Not Found 0, Failed 0;
continuity migration and tracker reconciliation reruns passed. Completed temporary
inspection/probe/test helpers were removed; the value-free scoped recovery helper
remains outside Git for the explicit approval boundary. Retained encrypted evidence
was preserved. This continuity-only checkpoint does not change registered executable
source. Diff checks and reviewed file scope passed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-10",
  "work_summary": "Committed the complete-input Ollama fix and refreshed all four Prefect registrations.",
  "key_result": "Registered source 8fee328; no worker/run conflicts. Existing blocked case and human state preserved; no recovery consumed.",
  "tests": "273 synthetic/mock checks passed; local synthetic context probes passed. Registration and read-only durable-state checks passed.",
  "phi_handling": "No protected replay, production correction/upload, mailbox access or human-state mutation. Tracker only received safe metadata.",
  "limitation_acceptance": "Automatic safety review denied live recovery under earlier prohibitions. Explicit scoped approval required; DP/Training stopped.",
  "exact_next_start": "Obtain explicit approval for one scoped cached-document/local-Ollama recovery and verified proposal-only Smartsheet publication after the automatic safety-review denial. Then run the reserved contract-6 recovery on the same existing case, preserving human controls, comments, review snapshot and row/document until fresh correction approval. Verify filename evidence, concise proposal and unchanged-cycle idempotency. Do not blindly repeat a failed replay. DP and Training remain stopped during this acceptance boundary."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->

## 2026-09-10 - Approved full-context same-case recovery and unchanged-cycle proof

Operator explicitly approved one cached-document/local-Ollama recovery and verified
proposal-only publication while preserving document fields, attachment, comments
and human controls. Read-only preflight confirmed current executable registrations,
concurrency, no active flow conflicts and zero fresh workers. No DP/Training worker
or deployment was started. Runtime capability settings matched protected config;
no Codex/cloud inference was invoked.

The temporary runner initially required explicit false approval values. The sheet
uses null for untouched boxes; production normalize_checkbox intentionally preserves
null and the workflow treats it as unchecked. Runner guard was aligned, without
changing production code or controls. This first stop preceded the contract-6
reservation and all inference. The diagnostic receipt was preserved, not deleted.
Unchanged blocked contract-5 state plus absent candidates/results proved prepare
never began; preflight resumption was separately audited before the one real cycle.

One real same-case recovery reserved contract 6/generation 3. Original cached OCR
was used, with no fresh OCR or Graph/mailbox access. Local model requests: category
classification 2912 input/114 output tokens, 102.45 seconds; extraction attempt 1
4074/1359 tokens, 392.80 seconds; extraction attempt 2 4426/1383 tokens, 358.45
seconds. All returned done=true/reason=stop. Runtime readback confirmed context
8192. Retry no longer evaluated the truncated 2050-token input. Model completion
does not establish field correctness. Candidates and selected validated document
remain DPAPI-sealed for diagnosis without repeated inference; values were not output.

Outcome remains completed_with_failures, blocked, correction_unrelated_field_change,
no verified plan and no correction applied. Two out-of-scope GOVERNING VALUE
differences (Hours, Days Per Week), not confidence-only drift, correctly remain
protected. Payer/start/end scalar evidence validates at .95; authoritative payer
lookup succeeds and dates are ready. Service token lookup remains unresolved.
Both retained candidates contain two service lines. The final line code/date/status
evidence is unsupported and modifier shape invalid despite model line confidence
1.0; that confidence was not used as deterministic support proof.
Subtype remains unsupported despite .95 candidate confidence; one candidate's
subtype state requires explicit/external context. Filename result partial_business,
two unresolved service/subtype placeholders. No placeholder was guessed away.

No document-field write or attachment upload occurred. Human controls, comments,
production row context and review snapshot remained unchanged. Only the existing
workflow-owned blocked-result publication/reconciliation path was permitted; no
verified correction proposal is ready for approval. A fresh-process unchanged
same-case cycle explicitly disabled analysis, processing and application: zero
model calls, zero workflow writes, zero correction applications, same generation
3. A separate verify-result receipt preserves the first recovery metrics. No
automatic retry, duplicate case or new document submission is authorized.

Added a synthetic untouched-null approval regression. Its first fixture lacked
the requested attachment plan and correctly failed verification; the synthetic
fixture was completed, not the production guard weakened. Modified test compiled;
context recovery 6, label recovery 5, local correction 51, review snapshot 13,
AI Correction 10: 85 synthetic/mock checks passed, zero failed. Existing executable
source remains 8fee328; this checkpoint changes tests/continuity only. DP and
Training remain stopped. Correction readiness is NOT established.

Final gates: 11 continuity and 3 tracker-reconciliation checks also passed,
bringing this turn's synthetic/mock count to 99. Tracker Updated 1, Unchanged 37,
Not Found 0, Failed 0. Protected-path ignore and diff checks passed. Sealed audit
identity uses complete-context-acceptance plus existing case identity, with
candidate:1, candidate:2, validated, result and verify-result suffixes. Those
records remain retained; completed temporary runners/inspectors are removed.

<!-- PROJECT_SMARTSHEET_CHECKPOINT_START
{
  "date": "2026-09-10",
  "work_summary": "Ran the explicitly approved full-context same-case recovery and verified unchanged-cycle idempotency.",
  "key_result": "Full retry input processed, but Hours/Days Per Week drift and unresolved service/subtype evidence still block correction. No plan applied.",
  "tests": "85 synthetic/mock checks passed; one cached/local replay completed. Fresh-process unchanged cycle: zero model calls/writes, same generation.",
  "phi_handling": "Evidence retained encrypted locally. Human controls/comments, row fields and attachment unchanged; no mailbox or fresh OCR access.",
  "limitation_acceptance": "Blocked generation 3/contract 6 remains consumed. No verified proposal ready. DP/Training stopped; no blind retry.",
  "exact_next_start": "Use the retained encrypted full-context candidates and final diagnostics to fix service-section evidence/subtype support and investigate out-of-scope Hours/Days Per Week value changes. Prove the correction synthetically before any further replay or rearm. Preserve blocked generation 3, review snapshot, comments, approvals, existing row/document and idempotency; do not resend the document or request approval of an unverified proposal. DP and Training remain stopped during exclusive maintenance."
}
PROJECT_SMARTSHEET_CHECKPOINT_END -->
