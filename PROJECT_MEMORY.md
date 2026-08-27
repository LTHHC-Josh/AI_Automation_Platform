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

The accepted development topology is one localhost server/UI, the default
local SQLite database, one process work pool with concurrency one, one process
worker, and manual synthetic runs only. Prefect 3.8.4 emitted repeated
non-fatal SQLite database-lock errors from deployment-readiness updates during
worker polling even though both synthetic runs completed and UI/API/worker
health endpoints remained healthy. SQLite is therefore sufficient only for
this manual development checkpoint. Resolve the locking behavior or separately
review PostgreSQL before scheduling or always-on production use.

The application prerequisite boundary is now implemented but remains dormant:
an explicit downstream classification-review mode, PHI-safe durable job-batch
summary, and parameterless one-call Prefect adapter exist without a deployment.
The adapter uses the explicit PHI-safe operator-purpose Run Type `Prefect
bounded mailbox orchestration`; it is not registered in `prefect.yaml` and has
zero Prefect retries.

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
- Production filename wiring remains disabled unless separately approved.
  The current normal path retains the existing safe attachment filename.

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
- Validated business-reference workbook boundary and deterministic filename
  policy/input services. Production filename orchestration remains disabled.
- Prefect 3.8.4 pinned with a self-hosted localhost server/UI, native process
  work pool/worker, versioned synthetic deployment, PHI-safe flow/task, and
  copy/paste-verified Windows operator guide. A parameterless mailbox adapter
  is import/mock-tested but remains undeployed and has never invoked the live
  production workflow.

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
- Repeated non-fatal SQLite deployment-readiness lock errors prevent treating
  this as always-on or production-hosting acceptance. The worker and server
  were stopped cleanly after the bounded acceptance.

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
8. Resolve the Prefect Windows/SQLite deployment-readiness locking evidence or
   approve a PostgreSQL hosting plan, then register the already implemented
   dormant mailbox adapter only after a separate deployment review.
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
- The PHI-safe self-hosted Prefect development control room and dormant
  parameterless mailbox adapter are implemented, but no mailbox deployment is
  registered or executed. Repeated SQLite lock errors block deployment
  registration, automatic worker startup, scheduling, Prefect retries, and
  always-on operation until a clean supported SQLite soak or separately
  approved PostgreSQL hosting checkpoint passes.
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
- Production filename orchestration remains disabled. Posted Date,
  renewal-qualifier, workflow-context, and ambiguity-safe reference boundaries
  exist but are not wired into normal production naming.
- No approved runtime source supplies 2067 workflow context or supported
  renewal-qualifier reference values. INIT/renewal context must not be inferred
  from 2067.
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

## CURRENT NEXT START

Perform a PHI-free Prefect persistence decision checkpoint using the intended
single-server/single-worker production-shaped topology: either prove a clean
supported SQLite soak with zero lock errors or prepare a separate PostgreSQL
hosting plan for approval. Do not register or run the dormant mailbox adapter,
enable schedules/startup/Prefect retries, or permit unattended uncertain row or
attachment retries during that checkpoint.
