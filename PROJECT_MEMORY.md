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

## Recent Tested Baseline

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
- Automatic rollback after a successful Smartsheet row write followed by an
  attachment-upload failure is not implemented, and Smartsheet retry/
  idempotency remains future production hardening.
- The full document currently reaches Smartsheet only through the existing
  explicit attachment-upload path.
- OCR text and `source_text` have no explicitly configured Smartsheet
  destination and therefore remain unmapped. Any future destination must be
  intentionally designed without serializing document/review objects
  wholesale.
- Review thresholds currently remain the configured values in
  `ReviewDecisionService`; this clarification does not change them.

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

Inspect the existing automatic Smartsheet row-write and attachment-upload
boundary for the tracked partial-success and retry/idempotency limitation.

Use focused mocked red regressions first for a successful row creation followed
by attachment failure and for a subsequent retry. Determine the smallest safe
correction that prevents duplicate rows or explicitly preserves partial-success
state without changing deterministic validation, business rules, automatic
write behavior, downstream review, or explicit destination mappings. Do not
run a real Smartsheet write, Graph, OCR, Ollama, mailbox, or patient document.
