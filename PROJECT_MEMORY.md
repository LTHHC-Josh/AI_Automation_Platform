# LTHHC A.I. Automation Platform - Project Memory

## Purpose

This file is the compact continuity layer for the LTHHC A.I. Automation
Platform.

It records current architecture decisions, implemented capabilities,
tested baselines, known limitations, and the exact next starting point.

It does not replace GitHub as the source of truth for committed code.
It does not replace `AGENTS.md` as the repository safety/execution rules.
It does not replace `update_project_tracker.py` as the detailed historical
project record.

Never store PHI, OCR text, patient/member data, `source_text`, protected
filenames, local patient-document paths, credentials, secrets, tokens,
Smartsheet payload values, or Smartsheet row IDs in this file.

## Source of Truth Order

1. Git committed state for committed code.
2. Confirmed local uncommitted state for work not yet committed.
3. `AGENTS.md` for durable repository safety and execution rules.
4. `PROJECT_MEMORY.md` for current project continuity.
5. `update_project_tracker.py` for detailed historical checkpoints and
   project-task synchronization.

If these disagree, inspect and reconcile rather than guessing.

## Platform Goal

Build a reusable company AI automation platform for LT Home Healthcare.

Current document-processing flow:

Microsoft 365 / Microsoft Graph
-> local PaddleOCR
-> local Ollama
-> structured extraction
-> deterministic evidence validation
-> business rules
-> automatic population of the intentionally mapped Smartsheet row
-> conditional downstream human-review exception workflow

The architecture must remain reusable for future document types,
healthcare sources, EHR/API integrations, cross-source validation,
workflow automation, and internal AI task completion.

## Current Architecture

Classification, extraction, deterministic validation, business rules,
external writes, and human review are separate boundaries.

MCO, payer, sender, source, filename, logo, and template are context or
metadata and must not determine document meaning.

Extraction preserves `value`, `confidence`, and `source_text`.

Separate Ollama attempts are independently validated and are never merged.

The strongest deterministically supported candidate is selected. Ties keep
attempt 1.

Unsupported, conflicting, ambiguous, guessed, invalid, or insufficiently
evidenced values remain null/unknown and flag the row for review as
appropriate.

After deterministic validation and business rules, the normal production
flow automatically creates or populates the intentionally mapped Smartsheet
row. Human review is a downstream exception workflow, not a write gate.

## Important Safety Invariants

- Requested visits are not approved visits.
- Units are not automatically visits, sessions, equipment, or sufficient
  approval.
- Approval must not be inferred from quantity, service code, dates,
  service lines, or generic status.
- Modifier ownership requires row evidence.
- Service-line values must be supported by evidence from the same service
  line.
- PHI, `source_text`, and full document content may reach Smartsheet only
  through an explicit, intentionally designed production mapping/write path.
- Internal diagnostics, credentials, tokens, local paths, cache metadata,
  and unrelated internal fields are never included merely because an object
  contains approved destination data.
- PHI remains within approved LTHHC systems and production integrations and
  is excluded from console output, logs, Git, continuity files, tests,
  diagnostics, screenshots, and Codex responses.
- Run Type is explicit PHI-safe operator text and is never inferred from
  document data.
- Review status and reasons accompany an automatically populated row when
  the configured accuracy/reliability rules require downstream review.
- Payer, sender, filename, and template must not imply document meaning or
  authorization conclusions.

## Current Implemented Capabilities

- Microsoft Graph mailbox access and attachment handling.
- Durable local mailbox message idempotency.
- Local PaddleOCR with protected local caching.
- Local Ollama classification and structured extraction.
- Field-level value/confidence/source evidence.
- Authorization service-line extraction.
- Controlled deterministic Ollama retry.
- Independent extraction-candidate validation and selection.
- Deterministic evidence validation.
- Authorization business-rule boundary.
- Human classification review and local feedback.
- Automatic Smartsheet row mapping and submission after deterministic
  validation and business rules, with review-required rows written with
  downstream review status and reasons.
- Smartsheet document attachment support.
- Explicit PHI-safe Run Type.
- Human-confirmed classification propagation.
- Source-agnostic authorization identifier prompt guidance.
- Source-agnostic authorization document/timing harness naming.
- Same-row service-line evidence guidance.
- Application-owned sanitized Microsoft Graph failure categories.
- PHI-safe legacy Graph/mailbox diagnostic stdout limited to aggregate
  counts, booleans, confidence/status metadata, and sanitized categories.
- PHI-safe Smartsheet partial-success propagation and explicit duplicate-
  blocking retry when a prior submission result confirms a row exists.
- Generic PHI-safe local document evaluation with explicit numeric selection,
  Run Type, protected-document/cache authorization, local-Ollama
  authorization, aggregate-only results, and sanitized failures.
- Opt-in cache-only OCR enforcement that cannot silently fall through to
  PaddleOCR while normal production OCR behavior remains unchanged.
- Opt-in synchronous Tkinter protected-review consumer that displays the
  source-document action, extracted fields and evidence, service lines, and
  validation/review context locally in memory while remaining excluded from
  evaluator serialization, output, logging, clipboard writes, and
  persistence.
- Deterministic staff-friendly Smartsheet review-reason summaries while full
  technical review reasons remain available in `ReviewOutput`.
- Confidence mapping that distinguishes unavailable confidence from actual
  numeric zero and uses missing/cleared text only for confirmed text-capable
  confidence destinations.
- Validated deterministic business-reference workbook loading for payer and
  service naming data, with optional future document-type data, exact lookups,
  an injectable Graph/SharePoint source boundary, and an ignored version-aware
  last-known-good cache.
- A deterministic filename policy for confirmed initial-authorization naming,
  with reference-derived payer/service tokens, separate optional form and
  workflow dimensions, supported single/range dates, no timestamp, and a
  guarded attachment boundary that remains inactive for normal production
  callers.
- Ambiguity-safe business service references keyed by HCPCS/bill code,
  modifier, and program. Multiple distinct naming results may coexist under
  one key, but lookup remains unresolved rather than using description or
  inferring an unsupported discriminator.

## Recent Tested Baseline

Latest live SharePoint reference-workbook checkpoint:

- The authoritative reference source is configured in the ignored local
  configuration boundary; identifiers and source details remain protected.
- Read-only Graph metadata lookup passed and returned a version token.
- Workbook download passed. `PAYOR LISTING` and `SERVICES LISTING` loaded and
  validated successfully; optional `DOCUMENT TYPES` is not present.
- Legitimate multiple service naming results under one three-part key were
  preserved and resolve as `ambiguous` with no selected value rather than
  invalidating the workbook.
- The ignored local cache refreshed, a second unchanged-version run reused the
  cache without another refresh download, and malformed-refresh simulation
  preserved the last-known-good cache.
- No sanitized failure occurred. No mailbox document, OCR, Ollama, Smartsheet
  write, production rename, or external AI operation occurred.
- Production filename orchestration remains disabled.

Latest ambiguity-safe service-reference checkpoint:

- `SERVICES LISTING` retains its existing schema and three-part normalized key:
  HCPCS/BILL CODE + MODIFIERS + PROGRAM. No PRIORITY column is required.
- Multiple rows and naming results under one key are accepted by the loader.
  One distinct naming result resolves; multiple distinct results return
  `ambiguous` with no selected value.
- `DESCRIPTION` remains informational free text and is never a discriminator.
  Priority is not inferred from description, code, modifier, program, or any
  other field.
- Focused synthetic deterministic/mock tests: 46 passed, 0 failed.
- Affected Smartsheet/mailbox regressions: 67 passed, 0 failed.
- Production filename orchestration remains disabled and unchanged.
- The configured live workbook can retain its legitimate conflicting rows and
  does not require structural correction for those distinctions.
- No mailbox document, OCR, Ollama, patient data, Smartsheet write, production
  rename, or external AI operation occurred.

Latest deterministic filename-policy checkpoint:

- Encoded LAST FIRST MIDDLE/INITIAL order, underscore-separated major
  components, optional service/form components, AUTH INIT, 2067 plus workflow
  coexistence, MMDDYY single dates, MMDDYY-MMDDYY supported ranges, no
  timestamp, and PDF extension preservation.
- Payer and applicable service tokens require unambiguous reference lookup.
  Unsupported/non-relevant service is omitted; relevant unresolved service,
  missing mandatory components, unresolved workflow tokens, and ambiguous date
  ownership block naming without guessing.
- Normal production orchestration does not construct or pass a policy and
  therefore retains the existing fingerprint attachment filename. An explicit
  incomplete policy uses the safe fallback with a naming-review status.
- Generated filenames and temporary paths are excluded from result
  representations and diagnostic output.
- The SharePoint configuration contract requires ignored local
  GRAPH_REFERENCE_DRIVE_ID and GRAPH_REFERENCE_ITEM_ID values. Version refresh
  prefers eTag and falls back to lastModifiedDateTime while protecting the
  last-known-good cache.
- Focused synthetic deterministic/mock tests: 43 passed, 0 failed.
- Affected Smartsheet/mailbox regressions: 67 passed, 0 failed.
- All 9 changed Python files compiled; git diff --check passed.
- No live Graph, mailbox, patient document, OCR, Ollama, Smartsheet, or external
  AI operation occurred during implementation verification.
- No PHI, protected filename/path, configured identifier, URL, credential,
  token, workbook content, payload, row identifier, cache, model, or patient
  file is included in this checkpoint.

Latest project-tracker WBS reconciliation checkpoint:

- Inspected all 75 actual project-tracker tasks and evaluated all 33 tasks
  currently Not Started or In Progress against committed source, tests,
  continuity, tracker history, and Git evidence.
- Advanced 16 evidence-supported statuses and intentionally left 17 unchanged
  where requirements, approval, accuracy benchmarking, user acceptance,
  go-live, or hypercare evidence was insufficient.
- Foundational installed/tested components and deterministic processing
  boundaries were marked Completed only where committed evidence was direct.
- Broader platform, security design, benchmarking, system testing, performance
  testing, and production deployment were marked In Progress where work has
  demonstrably started but is not complete.
- Added a durable rule requiring checkpoint history and affected WBS rows to be
  reconciled after meaningful tested work without inferring completion.
- Synthetic tracker reconciliation validation: 3 passed, 0 failed.
- No tracker row identifiers, payload values, credentials, tokens, PHI, or
  protected data are recorded here.

Latest review-summary, confidence, and reference-architecture checkpoint:

- Smartsheet receives a deterministic concise review summary while the full
  technical reason list remains unchanged in `ReviewOutput`.
- Missing and deterministically cleared confidence statuses are written only
  to confirmed text-capable confidence destinations. Unavailable confidence
  remains blank, and actual numeric zero remains numeric zero.
- Reference workbooks require validated PAYOR LISTING and SERVICES LISTING
  sheets; optional DOCUMENT TYPES support uses a separate schema.
- Duplicate, ambiguous, missing, malformed, and blank-result mappings fail
  safely without guessing.
- Version metadata controls refresh; malformed new data cannot replace the
  last-known-good ignored local cache.
- SharePoint/Graph access is behind an injectable metadata/download boundary.
  No live source configuration or workbook was accessed.
- The filename-component builder requires an explicit composition policy and
  all resolved components. It is not wired into production processing.
- Confidence-focused regression: 5 passed, 0 failed.
- Focused configuration, policy, review-output, and mapping regressions:
  61 passed, 0 failed.
- Affected processing, validation, review, Smartsheet, and mailbox
  regressions: 223 passed, 0 failed.
- All 20 modified Python files compiled; `git diff --check` passed.
- Classification: synthetic deterministic and mock. No live Graph, mailbox,
  patient document, OCR, Ollama, production Smartsheet write, or external AI
  operation occurred.
- No PHI, protected filename, source evidence, workbook content, payload,
  external identifier, credential, token, cache, model, or patient file is
  included in this checkpoint.

Latest first production end-to-end checkpoint:

- Exactly one intended mailbox message completed the production path.
- Microsoft Graph retrieval and attachment download passed.
- Real local OCR, classification, and local Ollama processing passed.
- Deterministic validation and business rules completed.
- Intentional Smartsheet mapping and destination validation passed.
- The Smartsheet row write and document attachment upload passed with no
  partial success.
- Mailbox handled/read state and the durable idempotency marker completed.
- Total elapsed time was 542.992 seconds.
- Test classification: real production integration using local AI; external
  AI was not used.
- No PHI, protected filename, extracted value, payload content, external row
  identifier, credential, or token is recorded here.

Latest Graph attachment-enumeration diagnostic checkpoint:

- The production `AttachmentService` attachment-listing GET path, method, and
  response handling were inspected and remain unchanged.
- The earlier `graph_request_failed` result was caused by incorrect PowerShell
  interpolation of the `$select` query key in a custom read-only probe, not by
  the production Graph endpoint or attachment service.
- Added allowlisted PHI-safe Graph diagnostic metadata for operation category,
  HTTP status, response presence, coarse content type, and failure kind without
  retaining raw provider errors, identifiers, request URLs, tokens, or response
  bodies.
- Initial focused synthetic result: 0 passed, 4 failed; expanded red result:
  2 passed, 2 failed; final focused result: 6 passed, 0 failed.
- Affected Graph security, attachment, mailbox, idempotency, and diagnostic-
  output regressions: 52 passed, 0 failed.
- Combined: 58 passed, 0 failed; all five changed Python files compiled.
- Test classification: synthetic deterministic/mock; no protected data was
  accessed by tests and no live processing integration was invoked by tests.
- The approved live read-only production-service preflight passed with exactly
  one unread candidate and exactly one processable attachment.
- The preflight did not download an attachment, process a document, invoke OCR
  or Ollama, write Smartsheet, mark the message read, or change durable
  idempotency state.

Latest local protected-review UI checkpoint:

- Initial synthetic red result: 0 passed, 8 failed.
- Final protected-review UI/evaluator regression: 27 passed, 0 failed.
- Affected cache-only OCR, document-processor, review-output, automatic-
  Smartsheet, and mailbox-Smartsheet regressions: 62 passed, 0 failed.
- Combined: 89 passed, 0 failed.
- All six modified Python files compiled successfully.
- Test classification: synthetic deterministic and mock.
- A real local Tkinter window was opened with synthetic non-PHI values only.
  The overview, extracted-field/evidence, service-line, and validation/review
  sections rendered; the injected source-document action, Done action, and
  normal close action completed successfully.
- The visual smoke test produced no protected stdout/stderr, clipboard write,
  persisted review output, screenshot, or extra file.
- The concrete consumer remains opt-in, synchronous, local-only, and in
  memory. It opens the existing selected source through the OS-default action
  without displaying or serializing the path.
- Aggregate evaluator output adds only protected-review requested/completed/
  status metadata and uses the sanitized `protected_review_unavailable` and
  `protected_review_failed` categories.
- Production DocumentProcessor/OCR behavior, validation, business rules,
  review decisions, extraction retry/candidate selection, Graph/mailbox,
  automatic Smartsheet submission, classification feedback, and the
  fixture-specific authorization harness remain unchanged.
- No PHI or protected data was accessed.
- No patient document, real PaddleOCR, local Ollama request, Microsoft Graph,
  mailbox, production Smartsheet workflow, or external AI ran.

Latest generic local-evaluator checkpoint:

- Initial focused red result: 1 passed, 18 failed.
- Final evaluator/cache-only regression: 21 passed, 0 failed.
- Affected processor, OCR, review, classification-feedback, authorization-
  harness, and automatic-Smartsheet regressions: 108 passed, 0 failed.
- Combined: 129 passed, 0 failed.
- All eight modified Python files compiled successfully.
- Test classification: synthetic deterministic and mock.
- The evaluator requires a positive numeric selector, explicit validated
  nonblank Run Type, explicit cached-OCR/protected-document access
  authorization, and explicit local-Ollama authorization.
- The evaluator invokes `DocumentProcessor.process()` directly and has no
  Graph, mailbox, or Smartsheet dependency.
- Cache-only evaluation stops with the sanitized `ocr_cache_unavailable`
  category on a cache miss; PaddleOCR prediction cannot run after that miss.
- Existing callers omit `ocr_cache_only`, so normal production OCR, mailbox
  processing, validation, retry/candidate selection, business rules, review,
  and automatic Smartsheet submission remain unchanged.
- External results contain aggregate allowlisted metadata only and exclude
  document paths, filenames, fingerprints, OCR/document text, extracted or
  service-line values, evidence, protected review objects, provider details,
  credentials, tokens, and destination payload identifiers.
- Nested protected-processing stdout and stderr are discarded without
  retaining captured content; raw exceptions become application-owned safe
  failure categories.
- `LocalProtectedReviewConsumer` is an optional synchronous local-only
  in-memory handoff. It is not serialized, logged, or persisted.
- One large in-process regression run encountered a Windows temporary-
  directory `PermissionError` in the existing concurrent classification-
  feedback locking suite. That suite passed 4/0 in isolation, and the other
  affected suites passed 104/0 separately; no concurrency test was weakened.
- No PHI or protected data was accessed.
- No real patient document, PaddleOCR prediction, Ollama request, Microsoft
  Graph, mailbox, Smartsheet production workflow, or external AI ran.

Latest Smartsheet partial-success/retry checkpoint:

- Initial focused red result: 6 passed, 5 failed.
- Final focused partial-success/retry regression: 12 passed, 0 failed.
- Affected Smartsheet/mailbox regressions: 123 passed, 0 failed.
- Combined: 135 passed, 0 failed.
- All three modified Python files compiled successfully.
- Test classification: synthetic deterministic and mock.
- A created row followed by attachment failure now remains
  `written=True, success=False` through submission, mailbox aggregation, and
  full orchestration.
- Mailbox aggregation reports `completed_with_partial_success` and preserves
  both the existing-row count and failure count.
- Explicit retry blocks a duplicate when the prior PHI-safe result confirms
  that a row exists and allows retry when the prior attempt created no row.
- No external row identifier is stored in or exposed by the retry contract.
- Normal first-attempt automatic writes, destination validation,
  review-required writes, optional attachments, mapping, deterministic
  validation, business rules, review thresholds, mailbox mark-as-read/
  idempotency, and no-inference protections remain unchanged.
- No result representation, status, stdout, or stderr exposed row identifiers,
  payload values, credentials, tokens, PHI, paths, or provider details.
- No real Smartsheet, Microsoft Graph, mailbox, PaddleOCR, Ollama,
  patient-document, or external-AI operation occurred.
- No protected data was accessed or exposed.

Latest legacy Graph/mailbox diagnostic-output checkpoint:

- Initial focused red result: 2 passed, 16 failed.
- Final focused stdout regression: 22 passed, 0 failed.
- Affected Graph/mailbox regressions: 121 passed, 0 failed.
- Combined: 143 passed, 0 failed.
- All five modified Python files compiled successfully.
- Test classification: synthetic deterministic and mock.
- Subjects, sender addresses, received identifying metadata, message IDs,
  filenames, paths, raw OCR/document text, extracted values, `source_text`,
  field-evidence values, raw mailbox errors, provider diagnostics, and
  credential/token-like values are excluded from covered diagnostic output.
- Output retains PHI-safe counts, booleans, safe sequence numbers,
  confidence/status metadata, and sanitized failure categories.
- No `EmailService`, `AttachmentService`, `MailboxProcessor`, mark-as-read,
  idempotency, document-processing, validation/business-rule, review, or
  automatic-Smartsheet behavior changed.
- No live Microsoft Graph, mailbox, attachment, PaddleOCR, Ollama,
  patient-document, production-Smartsheet, or external-AI operation occurred.
- No protected data was accessed or exposed.

Latest automatic-Smartsheet production-write checkpoint:

- Focused red result against the obsolete approval-gated contracts:
  5 passed, 8 failed.
- Final affected regression baseline: 286 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- Automatic intentionally mapped Smartsheet row population now follows
  deterministic validation and business rules without a complete-review
  approval gate.
- Review-required rows are written with review status and reasons; human
  review remains downstream exception handling.
- The existing configured review thresholds remain unchanged.
- Missing required destination data and destination-validation failures still
  block submission before the writer is called.
- The full document continues through the existing explicit attachment-upload
  path.
- OCR text and `source_text` have no explicit Smartsheet destination and are
  not mapped.
- No real Smartsheet write, Microsoft Graph, PaddleOCR, Ollama, patient
  document, or external-AI operation occurred during this checkpoint.
- No protected data was accessed or exposed.

Latest continuity-system validation:

- Project memory / Begin Day / End of Day validation: 14 passed, 0 failed.
- Test classification: synthetic deterministic repository-text validation.
- No Microsoft Graph, PaddleOCR, Ollama, or Smartsheet call occurred.

Latest Graph security checkpoint:

- Initial red security regression: 1 passed, 11 failed.
- Final Graph security boundary: 17 passed, 0 failed.
- Ten affected mailbox suites: 108 passed, 0 failed.
- Combined: 125 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- All five modified Graph/security Python files compiled successfully.
- Safe failure categories are `configuration_error`,
  `authentication_failed`, `authorization_failed`, and
  `graph_request_failed`.
- Missing configuration reports environment-variable names only.
- Provider/MSAL descriptions, raw MSAL exceptions, 401/403 details,
  request details, and response-decoding details are not propagated.
- Blank or failed token acquisition cannot proceed to a Graph request.
- Sanitized failures retain no provider exception cause or context.
- Microsoft Graph and MSAL were mocked; no live request occurred.
- No real credentials or `.env` values were read.
- No patient document or protected data was accessed.
- PaddleOCR, Ollama, Smartsheet, and external AI were not called.

Previous quantity-reconciliation checkpoint:

- Service-line quantity reconciliation: 10 passed, 0 failed.
- Document-processor regression: 18 passed, 0 failed.
- Evidence-validation regression: 29 passed, 0 failed.
- Authorization quantity-rule regression: 8 passed, 0 failed.
- Ollama service-line regression: 19 passed, 0 failed.
- Review-output service regression: 8 passed, 0 failed.
- Smartsheet review-mapping integration: 9 passed, 0 failed.
- Combined: 101 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- All modified Python files compiled successfully.
- Quantity reconciliation was verified end to end across validation,
  candidate selection, business rules, review output, and Smartsheet mapping.
- Reconciliation remains within one independently validated candidate;
  extraction attempts are never merged and ties keep attempt 1.
- Missing or null top-level `authorized_units` is not inferred, unsupported
  row quantities are excluded, and `approved_visits` remains separate.
- No production code change was required; only missing synthetic regression
  coverage was added.
- Microsoft Graph was not called.
- PaddleOCR was not called.
- Real Ollama generation was not called.
- Smartsheet external API was not called.
- No real Smartsheet row was written.

Latest controlled real authorization checkpoint:

- Run Type: Controlled Authorization Regression.
- Real cached OCR and real local Ollama were used locally.
- Classification remained authorization.
- Two extraction attempts occurred.
- Raw retry was not required; validated retry was required.
- The controlled retry triggered and attempt 2 was selected.
- The final validated candidate preserved two service lines.
- Supported row service-code and quantity evidence was preserved.
- A modifier remained only on the row with supporting row evidence.
- Unsupported row dates and statuses were cleared.
- Unsupported authorization status was cleared.
- Human review remained required.
- Review output was attached and preserved final review state.
- Raw OCR text and the local document path were excluded from review output.
- The corrected semantic harness passed: 1 passed, 0 failed.
- The retry fix and corrected harness contract are now verified with real
  cached OCR and real local Ollama.
- PHI output remained suppressed.
- Microsoft Graph and Smartsheet were not called.

Latest completed end-of-day state:

- Tracker synchronization returned `Not Found : 0` and `Failed : 0`.
- Changes were committed and pushed to `main`.
- Local and remote were synchronized.
- Working tree was clean.

Begin Day must verify current Git state again rather than assuming this
remains true.

## Known Limitations / Open Questions

- Authorization quantity meaning remains conservative where deterministic
  evidence is insufficient.
- Quantity business meaning and final approval remain human-review decisions.
- Modifier ownership remains unresolved without row evidence.
- Final production document taxonomy will expand beyond current
  authorization work.
- Production hardening and future integrations remain ongoing.
- Graph authentication and authorization failure verification is mock-only;
  no live negative authentication request was performed.
- Legacy Graph/mailbox diagnostic-output verification is mock-only; the
  hardened scripts have not been run against a live mailbox.
- Attachment upload cannot resume against an already-created Smartsheet row
  because no safe persisted row reference exists. Explicit retry is safe only
  while the prior PHI-safe submission result is available; after process-state
  loss, manual resubmission cannot be safely deduplicated and must not be
  attempted blindly.
- The full document currently reaches Smartsheet only through the existing
  explicit attachment-upload path.
- OCR text and `source_text` have no explicitly configured Smartsheet
  destination and therefore remain unmapped. Any future destination must be
  intentionally designed without serializing document/review objects
  wholesale.
- Review thresholds currently remain the configured values in
  `ReviewDecisionService`; this clarification does not change them.
- The protected-review UI has been rendered only with synthetic non-PHI data;
  the first operator-controlled protected comparison with a real local
  document has not yet run.
- The first true single-item production-path run completed successfully. No
  additional production item has been authorized for testing.
- The official `INBOUND RENEW` renewal token remains unresolved.
- Single-date ownership for state communications/notices remains unresolved
  when multiple supported document dates exist.
- The authoritative SharePoint reference source is configured only in the
  ignored local configuration boundary and passed its live read-only refresh.
- Production orchestration intentionally does not construct or pass filename
  policies until reference configuration and remaining business rules resolve.
- The legitimate service conflicts cannot resolve automatically until the
  owner defines a supported source-document discriminator. Description and
  other existing fields must not be used to infer priority.

## Weekly Codex / Work Capacity

Codex and Work share a weekly usage limit.

When the Codex and Work Analytics page provides an exact reset timestamp,
that timestamp is authoritative. Do not rely only on an assumed weekday.

Current Analytics observation:

- Weekly usage remaining: 99%.
- Authoritative reset timestamp: August 20, 2026 at 9:53 AM local time.
- Source: Codex and Work Analytics.
- This newer observation supersedes the prior August 18 reset value.
- The reason the platform changed the reset timestamp is unknown and must
  not be guessed.

Treat the known timestamp as current-cycle information. After the reset,
replace it when a new authoritative reset timestamp is observed.

Each week, identify work where VS Code Codex materially improves safety
or speed, including:

- workspace inspection
- complex multi-file edits
- debugging
- refactoring
- caller/reference analysis
- architecture review

On Begin Day, consider both remaining useful capacity and time until the
known reset. Prefer completing worthwhile Codex-suited work before unused
capacity expires, but never use Codex merely to consume credits.

Codex work must preserve uncommitted changes, follow `AGENTS.md`, remain
PHI-safe, and keep PHI/OCR/Ollama-sensitive data within approved local
boundaries.

## Begin Day Procedure

When the operator says `begin day`:

1. Read `AGENTS.md`.
2. Read this entire file.
3. Inspect the latest relevant checkpoint in
   `update_project_tracker.py`.
4. Inspect the current Git branch and status.
5. Verify local `HEAD` against the remote tracking branch.
6. Preserve and reconcile any uncommitted work before making changes.
7. Inspect files, callers, interfaces, and tests relevant to
   `CURRENT NEXT START`.
8. Check whether a known Codex/Work reset timestamp is approaching and
   identify worthwhile current/upcoming Codex-suited work.
9. Produce a concise Begin Day Brief containing:
   - repository state
   - last tested baseline
   - where work stopped
   - known limitations or blockers
   - today's exact objective
   - smallest safe first step
10. Continue from `CURRENT NEXT START` unless new evidence requires a
   different safe path.
11. Do not automatically run PHI-sensitive patient-document, OCR, Ollama,
    Graph, or Smartsheet operations.

## End of Day Procedure

When the operator says `end of day`:

1. Reach the smallest safe tested checkpoint.
2. Compile modified Python where applicable.
3. Run focused tests and affected regressions.
4. Update `update_project_tracker.py` with:
   - work completed
   - files changed
   - tests and results
   - real/mock classification
   - PHI handling
   - limitations
   - exact next starting point
5. Update this file so current capabilities, tested baseline, limitations,
   and `CURRENT NEXT START` are accurate.
6. Keep exactly one authoritative `CURRENT NEXT START`.
7. Run `update_project_tracker.py`.
8. Require `Not Found : 0` and `Failed : 0`.
9. Run Git safety checks.
10. Review the complete diff for PHI, OCR, protected files, credentials,
    secrets, tokens, caches, models, and temporary files.
11. Stage only reviewed safe files.
12. Commit and push.
13. Verify local and remote synchronization.
14. Confirm a clean working tree.
15. Report the completed checkpoint and next starting point.

## CURRENT NEXT START

Resolve the remaining filename business rules before production filename wiring,
specifically:

- official renewal workflow naming token
- deterministic ownership/source evidence for single-date state communication/notice naming

Do not guess either rule.
