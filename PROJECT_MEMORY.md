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
- Capability modes default to metadata-only `schema_only`. Production proposal
  writes and Codex dispatch each remain behind separate disabled protected-local
  gates pending controlled acceptance. Synthetic/mock/local-safe tests passed;
  no live flagged row/comment, protected OCR/Ollama, production correction write,
  mailbox operation, deployment run, or worker start occurred.

## CURRENT NEXT START

Perform a metadata/read-only live acceptance of DP Training first: verify
document-processor-training deployment readiness, command mappings, seven-column
schema, zero schedules/automations, no active worker/conflicts, and read-only
detection contract without reading comment content. Then separately authorize
one controlled flagged-row/comment acceptance and one proposal write before
enabling approval-gated Codex dispatch in production.
