"""Synchronize concise PROJECT_SMARTSHEET task state."""

from pathlib import Path

from src.services.project_smartsheet_service import (
    bound_project_smartsheet_comment,
    load_project_smartsheet,
    write_project_smartsheet_snapshot,
)
from src.services.project_status_service import ProjectStatusService


PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_HISTORY_PATH = PROJECT_ROOT / "PROJECT_HISTORY.md"

# Non-authoritative task presentation. Full pre-migration comments are preserved
# verbatim in PROJECT_HISTORY.md.
PROJECT_SMARTSHEET_TASKS = [

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
            "remains authoritative. Minimal-comment proposal-write and unchanged-cycle "
            "idempotency acceptance passed. A later approved dispatch failed with "
            "unavailable historical cause; safe diagnostics and failed-cycle reporting "
            "are now synthetic-tested. An isolated CLI probe reproduced result-schema "
            "uniqueItems rejection; the corrected API schema and local uniqueness "
            "enforcement passed the real PHI-free protocol check. Training is stopped, dispatch disabled, and "
            "the consumed approval is not retried. Live DP now "
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
            "local-only Ollama boundary. Resolution-authorized code candidates are "
            "restricted to existing pure-method scopes, tested in an offline Windows "
            "Sandbox and promoted with crash quarantine and exact rollback. "
            "Broader platform security design and full live acceptance continue."
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
            "run; broader system scenarios and remaining integrations continue. "
            "Approved AUTH DECREASE filename correction passed 153 synthetic/mock "
            "checks; date ownership and shared context v2 are covered. Real document "
            "retest remains pending."
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
            "guidance. Bounded value-free raw-model and adapter-shape diagnostics "
            "now distinguish malformed service-line containers and deterministic "
            "subtype support independently for each extraction attempt. No extra "
            "model request or attempt merging is introduced."
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
            "reconciliation supersedes its earlier top-level candidate failure. "
            "Nested service-line objects are preserved internally and rejected "
            "before production mapping rather than coerced to strings. Correction "
            "scope failures now retain exact approved-field difference diagnostics "
            "without values. A scoped row patch preserves unrelated scalar confidence "
            "only for the same independently accepted value with both scores in the "
            "existing accepted range. Displayed minimum and exact readback follow the "
            "projected row, without merging candidates. Retained diagnostic replay "
            "proves five confidence-only blockers are resolved; requested filename "
            "evidence remains unresolved and the consumed case is not rearmed."
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

]


def project_smartsheet_updates(project_smartsheet):
    """Return bounded task updates, using the derived project summary at the root."""
    rendered = []
    for task_name, status, comment in PROJECT_SMARTSHEET_TASKS:
        summary = (
            project_smartsheet.summary
            if task_name == "LTHHC AI Platform"
            else bound_project_smartsheet_comment(comment)
        )
        rendered.append((task_name, status, summary))
    return tuple(rendered)


def print_project_history_status() -> None:
    history = PROJECT_HISTORY_PATH.read_text(encoding="utf-8-sig")
    print("PROJECT_HISTORY.md preserved: Yes")
    print(f"PROJECT_HISTORY characters: {len(history)}")


def synchronize_project_smartsheet() -> None:
    # Local authoritative files are loaded and the non-authoritative snapshot is
    # written before any external client is initialized.
    project_smartsheet = load_project_smartsheet()
    write_project_smartsheet_snapshot(project_smartsheet)
    updates = project_smartsheet_updates(project_smartsheet)
    service = ProjectStatusService()
    tasks = service.tasks

    print()
    print("=" * 60)
    print("Synchronizing PROJECT_SMARTSHEET")
    print("=" * 60)
    print()

    updated = 0
    unchanged = 0
    not_found = 0
    failed = 0

    for task_name, status, comment in updates:
        try:
            task = tasks.find_task(task_name)
            if task is None:
                print(f"Task not found: {task_name}")
                not_found += 1
                continue
            changed = tasks.sync_task(task=task, status=status, comment=comment)
            if changed:
                updated += 1
                print(f"Updated: {task_name}")
            else:
                unchanged += 1
                print(f"No change: {task_name}")
        except Exception as error:
            failed += 1
            print(f"Failed: {task_name}")
            print(f"  {type(error).__name__}")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Updated   : {updated}")
    print(f"Unchanged : {unchanged}")
    print(f"Not Found : {not_found}")
    print(f"Failed    : {failed}")
    print("=" * 60)


if __name__ == "__main__":
    print_project_history_status()
    synchronize_project_smartsheet()
