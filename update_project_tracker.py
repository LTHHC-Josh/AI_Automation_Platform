from src.services.project_status_service import ProjectStatusService


PROJECT_JOURNAL = """
============================================================
LTHHC AI AUTOMATION PLATFORM - DEVELOPMENT JOURNAL
============================================================

Last updated: 2026-07-31

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
5. Run real or clearly identified mock tests.
6. Update this project tracker.
7. Verify that secrets and PHI are excluded.
8. Commit and push tested work.

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
  -> Deterministic validation
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
REAL DOCUMENT TEST STATUS
------------------------------------------------------------

A real scanned authorization document was processed using:

- Real local PaddleOCR cache
- Real local Ollama classification
- Real local Ollama extraction
- Real deterministic business rules
- Real human-review decision

Verified reliable behavior:

- Document classified as a generic authorization
- Service code extraction works
- Multiple authorized-unit values can be retained
- Modifier extraction can work
- Authorization quantity is not automatically approved
- Document is routed to human review

Current business-rule action:

Authorization quantity requires verification

Current review status:

Human Review Recommended

------------------------------------------------------------
KNOWN EXTRACTION LIMITATIONS
------------------------------------------------------------

The current llama3.1:8b extraction output is not approved for automatic
processing.

Observed limitations:

- Ambiguous checkbox labels may be treated as selected.
- Initial Request may be returned without reliable checkbox evidence.
- A requested visit quantity may be treated as approved.
- Dates are not consistently normalized to YYYY-MM-DD.
- The model may assign 1.0 confidence to ambiguous fields.
- Minimum field confidence can therefore appear artificially high.
- Prompt instructions alone do not reliably enforce evidence rules.

The business-rule and human-review layers prevented automatic approval,
but extraction accuracy still requires deterministic validation.

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

Required, optional, and conditionally required fields still need to be
confirmed with management.

------------------------------------------------------------
HUMAN-REVIEW STATUS
------------------------------------------------------------

The ReviewDecisionService is implemented and active.

Human review is required when:

- Classification confidence is below threshold
- Required evidence is missing
- A field has low confidence
- Values conflict
- Dates are invalid
- Status is unclear
- Document type is ambiguous
- Business rules fail
- The model appears to guess

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

Production and service files:

src/ai/config.py
src/ai/ocr/providers/paddle_ocr_provider.py
src/ai/llm/llm_provider.py
src/ai/llm/llm_service.py
src/ai/llm/providers/ollama_provider.py
src/document_processing/document_processor.py
src/business_rules/rules/authorization_rule.py
src/services/review_decision_service.py
src/models/document.py

Test files:

scripts/test_ollama_connection.py
scripts/test_molina_document.py
scripts/test_molina_timing.py
scripts/test_combined_ollama_timing.py

Graph files already implemented:

src/graph/config.py
src/graph/auth.py
src/graph/client.py
src/graph/email_service.py
src/graph/attachment_service.py
src/graph/mailbox_processor.py

------------------------------------------------------------
EXACT NEXT DEVELOPMENT STEP
------------------------------------------------------------

Retain field-level extraction evidence.

Start with:

1. src/models/document.py
2. src/document_processing/document_processor.py
3. scripts/test_molina_document.py

Add a field-evidence structure that preserves:

- extracted value
- confidence
- source_text

Then implement deterministic evidence validation before business rules.

Target flow:

Ollama extraction
  -> Preserve value, confidence, and source_text
  -> Deterministic evidence validation
  -> Clear or downgrade unsupported values
  -> Business rules
  -> Human-review decision

Initial deterministic checks should focus on:

- request_type checkbox ambiguity
- requested versus approved quantities
- date normalization
- service-code deduplication
- modifier validation
- confidence downgrading when source evidence is insufficient

Do not add payer-specific conclusions that have not been confirmed.

------------------------------------------------------------
NEXT SESSION START COMMANDS
------------------------------------------------------------

git status
git diff --stat
git diff --check

Then inspect:

src/models/document.py
src/document_processing/document_processor.py
scripts/test_molina_document.py
src/ai/llm/providers/ollama_provider.py

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
            "Graph, local PaddleOCR, local Ollama, structured extraction, "
            "deterministic business rules, human review, and Smartsheet."
        ),
    ),
    (
        "Define Integration Architecture",
        "Completed",
        (
            "Completed integration architecture for Microsoft Graph mailbox "
            "ingestion followed by local OCR, local LLM processing, "
            "deterministic validation, human review, and Smartsheet."
        ),
    ),
    (
        "Design AI Pipeline",
        "Completed",
        (
            "Implemented provider-based OCR and LLM architecture with "
            "registries, factories, provider discovery, deterministic business "
            "rules, and human-review decisions."
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
            "Python 3.13 virtual environment, PaddlePaddle, PaddleOCR, Ollama, "
            "llama3.1:8b, Microsoft Graph, Git, and test execution were "
            "validated locally."
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
            "Implemented local Ollama classification and extraction prompts. "
            "Real testing showed that prompt instructions alone do not reliably "
            "control checkbox interpretation, approval quantities, date "
            "normalization, or confidence calibration. Deterministic evidence "
            "validation is the next step."
        ),
    ),
    (
        "Implement Classification",
        "In Progress",
        (
            "Implemented local Ollama classification with structured JSON. A "
            "real authorization was classified as authorization, but subtype "
            "classification remains unapproved when evidence is ambiguous."
        ),
    ),
    (
        "Implement Data Extraction",
        "In Progress",
        (
            "Implemented local Ollama structured extraction with field-level "
            "confidence and source_text in the provider response. Real testing "
            "extracts key authorization fields, but unsupported checkbox and "
            "quantity interpretations still require deterministic correction."
        ),
    ),
    (
        "Validate AI Output",
        "In Progress",
        (
            "Validated real local PaddleOCR and Ollama output. Human review "
            "correctly blocks automatic processing, but llama3.1:8b currently "
            "returns unsupported values and unrealistically high confidence for "
            "some fields. Field evidence must be preserved and validated."
        ),
    ),
    (
        "Implement Business Rules",
        "In Progress",
        (
            "Authorization rules now use conservative structural validation and "
            "require verification of authorization quantities and ambiguous "
            "subtypes. Unconfirmed business interpretations are not "
            "automatically approved."
        ),
    ),
    (
        "Validate Business Rules",
        "In Progress",
        (
            "Real authorization testing confirms that quantity interpretation "
            "is routed to human verification. Final validation rules remain "
            "pending management confirmation of required fields, optional "
            "fields, units, visits, sessions, and subtype semantics."
        ),
    ),
    (
        "Integration Testing",
        "In Progress",
        (
            "Microsoft Graph mailbox processing, attachment download, local OCR, "
            "local Ollama processing, business rules, and human review have been "
            "tested. Extraction accuracy and final Smartsheet mappings remain "
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