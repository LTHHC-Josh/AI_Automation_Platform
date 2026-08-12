# LTHHC A.I. Automation Platform — Codex Repository Instructions

## Business / Platform Context

LT Home Healthcare is a Texas Medicaid-certified long-term home healthcare agency serving Medicaid clients. Services include PAS/PCS and other Texas Medicaid home-care programs.

Client data/documents may come from MCOs, doctors/providers, HHS, EHRs, internal systems, eligibility files, and other healthcare/Medicaid sources.

MCO/payer/sender names are source context, not document types.

Current work is authorization-related; future document types and integrations will expand.

Long-term goal: a reusable company AI platform. The current document processor is subsystem one.

## Source of Truth / Continuity

- Git committed state is authoritative for committed code.
- Preserve existing uncommitted work.
- Never overwrite or discard uncommitted changes unless explicitly instructed.
- Before editing, inspect affected files, callers, usages, tests, interfaces, and current Git diff/status.
- Do not guess paths, symbols, signatures, anchors, defaults, callers, tests, command args, or config shape.

## Architecture

- Preserve architecture; extend, do not duplicate.
- Keep classification, extraction, validation, business rules, human review, and external writes separate.
- Treat MCO/payer/sender/source as metadata/context, not document meaning.
- Prefer evidence-driven, source-agnostic logic.
- Do not hard-code conclusions from one payer, fixture, template, service code, or modifier.
- Design reusable integration boundaries for future EHR/API and internal AI workflows.

## PHI / Security

PHI must remain local.

Never print, expose, log, upload, commit, or include in responses:

- OCR text
- patient/member data
- `source_text` containing PHI
- identifying filenames from protected data folders
- patient PDFs/documents
- credentials
- secrets
- tokens
- `.env` values
- model files
- Smartsheet payload values
- Smartsheet row IDs

Never commit:

- `.env`
- `data/incoming/`
- `data/ocr_cache/`
- `data/classification_feedback/`
- `data/mailbox_processing_state/`
- patient documents
- OCR data
- credentials/tokens/secrets
- model files

Use PHI-safe diagnostics only: counts, booleans, timings, attempts, confidence, field names, statuses, evidence-present flags, exit codes, and safe file paths outside protected data.

Never write `source_text` to Smartsheet unless explicitly approved.

## AI / Extraction

- Preserve `value`/`confidence`/`source_text` for each field and service line.
- Never auto-assign confidence `1.0`.
- Missing, unsupported, conflicting, invalid, low-confidence, guessed, or ambiguous values must become `null`/unknown plus review.
- Never invent or restore values unless deterministic evidence supports them within the same extraction candidate.
- Never merge separate Ollama attempts.
- Validate each candidate independently and choose the strongest deterministically supported candidate; ties keep attempt 1.
- Model confidence, token count, or generation length are not correctness proof.

## Authorization Safety

- Requested visits are not approved visits.
- Units are not automatically visits, sessions, equipment, or sufficient approval.
- Never infer approval from quantity, service code, dates, service lines, or generic status.
- Never assign a top-level modifier without row evidence.
- If quantity meaning or modifier ownership is unresolved, preserve supported values and require review.

## Validation / Review

- Keep deterministic validation, business rules, and human review separate.
- Review output must preserve values, confidence, `source_text`, actions, status/reasons, retry metadata, selected attempt, and reconciliation.
- Do not rerun or reinterpret extraction while constructing review output.
- Only explicit complete-review approval may permit a real Smartsheet write.

## Testing

Before tests, verify test paths and affected callers/expectations.

For tests importing `src`:

- preserve and restore `PYTHONPATH`
- set it to the repository root
- compile modified Python files first
- run focused tests before affected regressions

Classify test reporting as:

- synthetic deterministic
- mock
- real cached OCR
- real local Ollama
- real external integration

Report pass/fail, real/mock classification, PHI handling, limitations, and next step.

Reusable tests should be named by behavior/document purpose, not payer/MCO unless intentionally source-specific.

## Local Execution

This repository runs on Windows PowerShell.

Repository root:

`C:\Projects\LTHHC-AI-Automation-Platform`

For complex text edits, prefer a temporary Python script over fragile PowerShell replacement logic.

Read UTF-8/BOM safely.

Write UTF-8 with LF newlines.

Remove temporary scripts after use.

Do not expose protected local data while diagnosing failures.

## Failure Handling

If a command fails due to wrong path, stale anchor, parser error, wrong module, missing file, or stale caller:

1. Acknowledge the cause.
2. State what actually ran.
3. Inspect the current state.
4. Make the smallest correction.
5. Verify execution.

## Project Tracker

Tracker file: `update_project_tracker.py`

After meaningful tested work:

- inspect its current structure and insertion boundary
- record feature, files, tests, results, real/mock classification, PHI handling, limitations, and exact next start
- run the tracker
- require `Not Found : 0` and `Failed : 0`

Do not commit before tracker success.

## Git Safety

Before staging:

- run `git diff --check`
- verify protected paths remain ignored
- inspect Git status
- inspect the full reviewed diff
- confirm no PHI/OCR/PDF/secrets/tokens/cache/model/temp files are included
- stage only reviewed safe files

After commit:

- push
- verify local/remote sync
- confirm clean tree

## Current Work

Current uncommitted work includes:

- PHI-safe single-document authorization harness changes
- generic authorization identifier prompt cleanup
- stronger service-line same-row evidence guidance
- focused Ollama prompt tests

Do not revert or overwrite those existing changes.

## Communication / Execution

During implementation/testing/recovery, perform the work directly when safe instead of asking the operator to manually execute routine commands.

Stop only for:

- unresolved business/architecture decision
- PHI/credential boundary
- explicit approval requirement
- genuinely unavailable local-only fact
- destructive/risky action requiring approval
