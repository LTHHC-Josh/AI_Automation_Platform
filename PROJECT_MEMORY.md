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
-> human review
-> approved external destinations such as Smartsheet

The architecture must remain reusable for future document types,
healthcare sources, EHR/API integrations, cross-source validation,
workflow automation, and internal AI task completion.

## Current Architecture

Classification, extraction, deterministic validation, business rules,
human review, and external writes are separate boundaries.

MCO, payer, sender, source, filename, logo, and template are context or
metadata and must not determine document meaning.

Extraction preserves `value`, `confidence`, and `source_text`.

Separate Ollama attempts are independently validated and are never merged.

The strongest deterministically supported candidate is selected. Ties keep
attempt 1.

Unsupported, conflicting, ambiguous, guessed, invalid, or insufficiently
evidenced values remain null/unknown and route to review.

Real Smartsheet writes require explicit complete-review approval.

## Important Safety Invariants

- Requested visits are not approved visits.
- Units are not automatically visits, sessions, equipment, or sufficient
  approval.
- Approval must not be inferred from quantity, service code, dates,
  service lines, or generic status.
- Modifier ownership requires row evidence.
- Service-line values must be supported by evidence from the same service
  line.
- `source_text` is not written to Smartsheet without explicit approval.
- PHI remains local.
- Run Type is explicit PHI-safe operator text and is never inferred from
  document data.
- Human Review Required cannot be bypassed by complete-review approval.
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
- Complete-review approval boundary.
- Reviewed Smartsheet row mapping and writes.
- Smartsheet document attachment support.
- Explicit PHI-safe Run Type.
- Human-confirmed classification propagation.
- Source-agnostic authorization identifier prompt guidance.
- Source-agnostic authorization document/timing harness naming.
- Same-row service-line evidence guidance.
- Application-owned sanitized Microsoft Graph failure categories.

## Recent Tested Baseline

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
- Every new real Smartsheet write requires fresh explicit complete-review
  approval.

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

Inspect the legacy Graph/mailbox diagnostic entry points and their current
output contracts:

- `scripts/test_graph_connection.py`
- `scripts/test_graph_attachments.py`
- `scripts/check_graph_read_status.py`
- `scripts/test_mailbox_processor.py`

Test classification:

- synthetic deterministic
- mocked mailbox, Graph, attachment, and document results only

Add PHI-safe stdout regressions reproducing the current exposure of message
metadata, identifiers, attachment/document paths, OCR text, and extracted
document values without using any real protected value. Confirm both success
and failure output contracts.

Then make the smallest changes needed so these diagnostics report only safe
counts, booleans, timings, confidence metadata, and sanitized statuses while
remaining operationally useful. Do not change mailbox-processing behavior or
core document-processing interfaces.

Report only PHI-safe metadata:

- test counts and classification
- diagnostic output field categories
- whether protected output exposure was detected before and after correction
- exact safe files affected

Do not run these scripts against a live mailbox or real documents. Do not
expose provider diagnostics, credentials, secrets, tokens, OCR text, patient
data, extracted values, `source_text`, protected filenames or paths,
Smartsheet payload values, or row IDs.

Do not perform a real Smartsheet write without a fresh explicit
complete-review approval.
