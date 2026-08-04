from src.services.project_status_service import ProjectStatusService


PROJECT_JOURNAL = """
============================================================
LTHHC AI AUTOMATION PLATFORM - DEVELOPMENT JOURNAL
============================================================

Last updated: 2026-08-04

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

------------------------------------------------------------
APPROVED ARCHITECTURE
------------------------------------------------------------

Microsoft 365 shared mailbox
  -> Microsoft Graph
  -> Attachment download
  -> Local PaddleOCR
  -> Local Ollama
  -> Structured extraction
  -> Field-level evidence preservation
  -> Deterministic evidence validation
  -> Business rules
  -> Human-review decision
  -> Smartsheet

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

Do not send documents, OCR text, patient information, member IDs,
authorization numbers, medical information, or credentials to external
AI services.

------------------------------------------------------------
CURRENT DOCUMENT-PROCESSING FLOW
------------------------------------------------------------

File
  -> OCR or cached OCR text
  -> Separate Ollama classification request
  -> Separate Ollama structured-extraction request
  -> Preserve field-level value, confidence, and source_text
  -> Deterministic evidence validation
  -> Synchronize corrected flat extraction values
  -> Deterministic business rules
  -> Human-review decision
  -> Document result

Classification and extraction intentionally remain separate.

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
- Reuses cached OCR text when the document has not changed
- Treats cached OCR text as PHI

The following paths must never be committed:

.env
data/incoming/
data/ocr_cache/
patient documents
OCR text containing PHI
local model files

Real scanned authorization OCR was completed successfully.

OCR cache reuse was tested successfully.

PaddleOCR model initialization still occurs when cached text is used,
but actual OCR prediction is skipped.

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

Current performance baseline for a cached three-page authorization:

Provider initialization:
Approximately 3.30 seconds

OCR cache lookup:
Effectively zero seconds

Classification:
Approximately 70.35 seconds

Extraction:
Approximately 191.37 seconds

Document processing total:
Approximately 261.73 seconds

Overall total:
Approximately 265.03 seconds

The principal performance bottleneck is local CPU Ollama inference.

Do not select production hardware until document volume, page count,
acceptable processing time, concurrency, model size, context length,
storage, and accuracy requirements are better established.

------------------------------------------------------------
FIELD-LEVEL EVIDENCE STATUS
------------------------------------------------------------

Field-level extraction evidence is now preserved on the Document model.

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

This feature was tested successfully with a real cached OCR document and
real local Ollama extraction.

------------------------------------------------------------
DETERMINISTIC EVIDENCE VALIDATION STATUS
------------------------------------------------------------

A deterministic evidence-validation service is implemented and active
between extraction and business rules.

Current non-business-specific checks include:

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

The validator does not currently apply payer-specific, service-line,
quantity, or authorization workflow conclusions.

------------------------------------------------------------
REAL DOCUMENT TEST STATUS
------------------------------------------------------------

A real scanned authorization document was processed using:

- Real local PaddleOCR cache
- Real local Ollama classification
- Real local Ollama extraction
- Real field-level evidence preservation
- Real deterministic evidence validation
- Real deterministic business rules
- Real human-review decision

Verified real behavior:

- Document classified as a generic authorization
- Classification confidence returned as 90 percent
- Member ID remained supported by source evidence
- Authorization number remained supported by source evidence
- Service code remained supported by source evidence
- Service-code list remained supported and deduplicated
- Modifier remained supported and structurally valid
- Provider NPI remained supported by source evidence
- Diagnosis code remained supported by source evidence
- Start date normalized to YYYY-MM-DD
- End date normalized to YYYY-MM-DD
- Member date of birth normalized to YYYY-MM-DD
- Ambiguous request type was cleared
- Unsupported approved visits value was cleared
- Invalidated fields were assigned 0.0 confidence
- Authorized unit values were preserved without automatic interpretation
- Source evidence remained available after correction
- Document was routed to human review

Real deterministic validation actions:

- Request type requires checkbox or selection verification
- Approved visits are not supported by clear approval evidence

Current business-rule action:

Authorization quantity requires verification

Current review status:

Human Review Recommended

Current review reasons include:

- One or more extracted fields have confidence below 85 percent
- Request type requires checkbox or selection verification
- Approved visits are not supported by clear approval evidence
- Authorization quantity requires verification

The real test output contained PHI and must remain local. No patient
values or OCR evidence should be added to source files, documentation,
the tracker, or GitHub.

------------------------------------------------------------
SYNTHETIC EVIDENCE-VALIDATION TEST STATUS
------------------------------------------------------------

Test file:

scripts/test_evidence_validation.py

Test type:

Synthetic deterministic test with no PHI and no external dependencies

Verified behavior:

- Matching identifiers were preserved
- Unsupported identifiers were cleared
- Unsupported identifier confidence was set to 0.0
- Ambiguous request type was cleared
- Unsupported approved visits were cleared
- Dates were normalized
- Duplicate service codes were removed
- Valid modifier evidence was preserved
- Validation actions were emitted

Result:

Passed
Failed: 0

This test does not call PaddleOCR, Ollama, Microsoft Graph, or
Smartsheet.

------------------------------------------------------------
SYNTHETIC REVIEW-DECISION TEST STATUS
------------------------------------------------------------

Test file:

tests/test_review_decision_service.py

Test type:

Synthetic deterministic test with no PHI and no external dependencies

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

Passed: 9
Failed: 0

This test does not call PaddleOCR, Ollama, Microsoft Graph, or
Smartsheet.

------------------------------------------------------------
KNOWN EXTRACTION AND VALIDATION LIMITATIONS
------------------------------------------------------------

The current llama3.1:8b extraction output is not approved for automatic
processing without human review.

Observed limitations:

- Ambiguous checkbox labels may be treated as selected by the model.
- Initial Request may be returned without reliable selection evidence.
- Requested visit quantities may be presented as approved values.
- The model may assign 1.0 confidence to ambiguous or weakly supported
  fields.
- Current deterministic validation clears known unsupported fields but
  does not yet provide full confidence calibration.
- Person names, payer names, provider names, descriptions, and status
  text are not yet deterministically compared with source evidence.
- Authorized-unit values are retained but their business meaning has not
  been confirmed.
- Multiple service-line rows are not yet modeled as separate structured
  service-line records.
- The current field structures may eventually need a dedicated model
  instead of nested dictionaries.
- Prompt instructions alone do not reliably enforce evidence rules.

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
- Do not infer initial, renewal, extension, continuation, amendment,
  denial, or partial approval without reliable evidence.
- Require human verification for authorization quantity interpretation.
- Require human verification when subtype evidence is ambiguous.

A tested example was confirmed by the user to be a telemonitoring
authorization associated with the Remote Patient Monitoring service
line.

That information is currently treated only as confirmed context for the
example. It has not been implemented as a universal service-code,
payer, service-line, or authorization-type rule.

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

The current work is focused on completing and stabilizing the technical
pipeline before formal business-rule training.

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

Current statuses:

Verified by AI
Human Review Recommended
Human Review Required

Duplicate review reasons are removed.

Human review is functioning as a safety control.

------------------------------------------------------------
TIMING TESTS
------------------------------------------------------------

scripts/test_molina_timing.py

Measures:

- Provider initialization
- OCR or cache lookup
- Classification
- Extraction
- Business-rule validation
- Human-review decision when separately detectable
- Pipeline overhead
- Total processing time

scripts/test_combined_ollama_timing.py

Purpose:

- Measure the rejected combined classification-and-extraction
  experiment
- Preserve evidence that the combined request was not a useful
  optimization

Combined-request result:

Combined Ollama analysis:
Approximately 255.70 seconds

Overall total:
Approximately 259.14 seconds

Performance gain:
Approximately 6 seconds or 2.3 percent

Accuracy result:
Failed

The combined request produced unsupported classification and extraction
results. The production pipeline was restored to separate requests.

------------------------------------------------------------
FILES CREATED OR MODIFIED
------------------------------------------------------------

Files created:

src/services/evidence_validation_service.py
scripts/test_evidence_validation.py
tests/test_review_decision_service.py

Files modified:

src/models/document.py
src/document_processing/document_processor.py
src/services/review_decision_service.py
scripts/test_molina_document.py
update_project_tracker.py

Previously implemented production and service files:

src/ai/config.py
src/ai/ocr/providers/paddle_ocr_provider.py
src/ai/llm/llm_provider.py
src/ai/llm/llm_service.py
src/ai/llm/providers/ollama_provider.py
src/business_rules/rules/authorization_rule.py

Previously implemented Graph files:

src/graph/config.py
src/graph/auth.py
src/graph/client.py
src/graph/email_service.py
src/graph/attachment_service.py
src/graph/mailbox_processor.py

------------------------------------------------------------
TESTS RUN
------------------------------------------------------------

Synthetic deterministic evidence-validation test:

python -m scripts.test_evidence_validation

Result:

Passed
Failed: 0

Real local document regression test:

python -m scripts.test_molina_document

Result:

Passed

Real or mock status:

Real cached PaddleOCR text
Real local Ollama classification
Real local Ollama extraction
Real deterministic evidence validation
Real business rules
Real human-review decision

Synthetic review-decision test:

python -m tests.test_review_decision_service

Result:

Passed: 9
Failed: 0

Real or mock status:

Synthetic deterministic test

Syntax checks were also run with Python compileall before selected
behavior tests. Syntax checks confirm that Python can parse the files,
but they do not replace behavioral tests.

------------------------------------------------------------
EXACT NEXT DEVELOPMENT STEP
------------------------------------------------------------

Add focused automated tests for EvidenceValidationService under the
project tests directory, then improve confidence handling without adding
unconfirmed business rules.

Start with:

1. tests/test_evidence_validation_service.py
2. src/services/evidence_validation_service.py
3. src/models/document.py
4. src/document_processing/document_processor.py

Initial test coverage should include:

- Missing source_text clears protected structured fields
- Supported alphanumeric identifiers remain intact
- Unsupported identifiers are cleared
- Supported date evidence normalizes correctly
- Unsupported date evidence is cleared
- Duplicate service codes are removed
- Conflicting service_code and service_codes trigger review
- Invalid modifier structures are cleared
- Validation actions remain deduplicated
- Original source_text remains preserved after invalidation
- Flat extracted_data and field_confidences remain synchronized

After automated evidence-validator coverage is complete, continue with
technical extraction structure for multiple authorization service lines.

Do not define payer-specific, RPM-specific, service-code, quantity, or
Smartsheet business mappings until the technical pipeline is stable and
the rules are confirmed.

------------------------------------------------------------
NEXT SESSION START COMMANDS
------------------------------------------------------------

git status --short
git diff --stat
git diff --check

Then inspect:

src/services/evidence_validation_service.py
tests/test_review_decision_service.py
scripts/test_evidence_validation.py
scripts/test_molina_document.py
src/models/document.py
src/document_processing/document_processor.py
src/services/review_decision_service.py

============================================================
"""


service = ProjectStatusService()
tasks = service.tasks


updates = [
    (
        "Design Solution Architecture",
        "Completed",
        (
            "Completed the approved local-first architecture using Microsoft "
            "Graph, local PaddleOCR, local Ollama, field-level evidence "
            "preservation, deterministic evidence validation, business rules, "
            "human review, and Smartsheet."
        ),
    ),
    (
        "Define Integration Architecture",
        "Completed",
        (
            "Completed integration architecture for Microsoft Graph mailbox "
            "ingestion followed by local OCR, local LLM processing, structured "
            "extraction, evidence validation, human review, and Smartsheet."
        ),
    ),
    (
        "Design AI Pipeline",
        "Completed",
        (
            "Implemented provider-based OCR and LLM architecture with "
            "registries, factories, field-level extraction evidence, "
            "deterministic evidence validation, business rules, and "
            "human-review decisions."
        ),
    ),
    (
        "Configure Branch Strategy",
        "Completed",
        (
            "Git repository is connected to GitHub and the development workflow "
            "has been validated. Secrets, PHI, incoming documents, and OCR cache "
            "must remain excluded from commits."
        ),
    ),
    (
        "Validate Development Environment",
        "Completed",
        (
            "Python virtual environment, PaddlePaddle, PaddleOCR, Ollama, "
            "llama3.1:8b, Microsoft Graph, Git, synthetic tests, and real local "
            "document processing were validated."
        ),
    ),
    (
        "Create OCR Service",
        "Completed",
        (
            "Implemented the production local PaddleOCR provider using the "
            "existing OCR provider framework. Added SHA-256 OCR caching under "
            "data/ocr_cache and verified cache reuse."
        ),
    ),
    (
        "Extract PDF Text",
        "Completed",
        (
            "Successfully extracted text from a real scanned image-only PDF "
            "using local PaddleOCR. Verified that unchanged documents reuse "
            "cached OCR text."
        ),
    ),
    (
        "Unit Test OCR",
        "Completed",
        (
            "Validated mock OCR, direct production PaddleOCR, real scanned PDF "
            "OCR, OCR cache creation, and cached OCR reuse."
        ),
    ),
    (
        "Create Prompt Templates",
        "In Progress",
        (
            "Implemented local Ollama classification and extraction prompts "
            "that request field-level value, confidence, and source_text. Real "
            "testing confirms that prompt instructions still require "
            "deterministic evidence validation."
        ),
    ),
    (
        "Implement Classification",
        "In Progress",
        (
            "Implemented local Ollama classification with structured JSON. A "
            "real authorization was classified as a generic authorization. "
            "Subtype and workflow classification remain untrained."
        ),
    ),
    (
        "Implement Data Extraction",
        "In Progress",
        (
            "Implemented local Ollama structured extraction and preserved "
            "field-level value, confidence, and source_text. Real testing "
            "confirmed key fields can be retained while unsupported request "
            "type and approved-visit values are cleared deterministically."
        ),
    ),
    (
        "Validate AI Output",
        "In Progress",
        (
            "Implemented deterministic evidence validation before business "
            "rules. Real testing confirmed identifier evidence checks, date "
            "normalization, service-code deduplication, unsupported-field "
            "clearing, confidence downgrading, and human-review routing."
        ),
    ),
    (
        "Implement Business Rules",
        "In Progress",
        (
            "Authorization rules remain conservative and separate from evidence "
            "validation. Authorization quantities still require human "
            "verification because formal business-rule training has not begun."
        ),
    ),
    (
        "Validate Business Rules",
        "In Progress",
        (
            "Real authorization testing confirms that evidence validation and "
            "quantity interpretation route the document to human review. Final "
            "business rules remain pending confirmed management requirements."
        ),
    ),
    (
        "Integration Testing",
        "In Progress",
        (
            "Tested Microsoft Graph mailbox processing, attachment download, "
            "local OCR, local Ollama, field-level evidence preservation, "
            "deterministic evidence validation, business rules, and human "
            "review. Final mappings and end-to-end Smartsheet behavior remain "
            "under development."
        ),
    ),
    (
        "Configure Microsoft Entra",
        "Completed",
        (
            "Created and tested the Microsoft Entra application registration, "
            "client secret, Graph application permissions, tenant consent, and "
            "client-credentials authentication."
        ),
    ),
    (
        "Create Shared Mailbox",
        "Completed",
        (
            "Created ai@lthhc.com as the shared mailbox for the AI Automation "
            "Platform."
        ),
    ),
    (
        "Configure Mailbox Security",
        "Completed",
        (
            "Configured the shared mailbox and application access for the "
            "approved Microsoft Graph workflow."
        ),
    ),
    (
        "Validate Email Delivery",
        "Completed",
        (
            "Successfully delivered test messages and attachments to "
            "ai@lthhc.com and retrieved them through Microsoft Graph."
        ),
    ),
    (
        "Design Office365 Connector",
        "Completed",
        (
            "Completed the Microsoft Graph connector architecture including "
            "configuration, authentication, Graph client, email service, "
            "attachment service, and mailbox processor."
        ),
    ),
    (
        "Authenticate Microsoft Graph",
        "Completed",
        (
            "Successfully authenticated using OAuth client credentials and "
            "confirmed access to the ai@lthhc.com shared mailbox."
        ),
    ),
    (
        "Implement Office365 Connector",
        "Completed",
        (
            "Implemented and tested unread-message retrieval, supported "
            "attachment downloading, inline-image filtering, document "
            "processing, mark-read-after-success behavior, retry preservation "
            "for failures, and duplicate prevention."
        ),
    ),
]


def print_project_journal() -> None:
    print(PROJECT_JOURNAL)


def synchronize_project_tracker() -> None:
    print()
    print("=" * 60)
    print("Synchronizing Project Tracker")
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

            changed = tasks.sync_task(
                task=task,
                status=status,
                comment=comment,
            )

            if changed:
                updated += 1
                print(f"Updated: {task_name}")
            else:
                unchanged += 1
                print(f"No change: {task_name}")

        except Exception as ex:
            failed += 1
            print(f"Failed: {task_name}")
            print(f"  {ex}")

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
    print_project_journal()
    synchronize_project_tracker()