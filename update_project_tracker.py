from src.services.project_status_service import ProjectStatusService


PROJECT_JOURNAL = """
============================================================
LTHHC AI AUTOMATION PLATFORM - DEVELOPMENT JOURNAL
============================================================

Last updated: 2026-08-05

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
  -> Controlled extraction retry when structurally incomplete
  -> Independent deterministic candidate validation
  -> Stronger supported candidate selection
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
  -> Human-review decision
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

Passed: 9
Failed: 0

Real or mock:

Synthetic deterministic test

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
- The generic retry verification prompt has not yet been observed during
  a real incomplete-first-attempt event.
- A stronger second candidate has not yet been selected during a real
  retry event.

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

- PHI-safe Ollama timing metadata
- PHI-safe Ollama token-count metadata
- PHI-safe request type, attempt, seed, and retry-prompt metadata
- Stage-level processing timing
- Configurable deterministic attempt seed routing
- Attempt 1 base seed and attempt 2 alternate seed
- Confirmation that changing the seed alone does not ensure recovery
- Generic controlled-retry verification prompt
- Structural authorization extraction retry detection
- One controlled retry maximum
- Independent deterministic candidate validation
- Deterministic stronger-candidate selection
- First-candidate preservation on score ties
- No merging between extraction attempts
- Per-attempt PHI-safe metrics
- Real complete-first-attempt path
- Real incomplete-first-attempt retry detection path
- Synthetic incomplete-first-attempt retry path
- Synthetic attempt-routing path
- Synthetic generic retry-prompt path
- Existing deterministic validation
- Existing business-rule separation
- Existing human-review routing

The real complete-first-attempt Molina regression passed.

A real retry event was observed. Both attempts remained incomplete, the
candidates tied, the first attempt was retained, semantic regression
failed, and human review remained active.

The synthetic retry, attempt-routing, retry-prompt, and
candidate-selection tests passed.

This does not prove that the second extraction attempt will always be
complete.

This does not prove that the retry mechanism is stable across all
authorization formats.

This does not remove the need for human review.

------------------------------------------------------------
EXACT NEXT DEVELOPMENT STEP
------------------------------------------------------------

Observe and validate the new generic retry verification prompt during
a real incomplete-first-attempt local Ollama run without weakening
deterministic validation.

Start with:

1. Run the known Molina semantic regression a reasonable limited number
   of times.
2. Stop when an incomplete first extraction triggers the controlled
   retry.
3. Record only PHI-safe attempt metrics.
4. Confirm extraction_attempt_count is 2.
5. Confirm extraction_retry_triggered is True.
6. Confirm attempt 1 reports retry_prompt_applied as False.
7. Confirm attempt 2 reports retry_prompt_applied as True.
8. Confirm attempt 1 uses seed 42 and attempt 2 uses seed 43.
9. Compare independently validated candidate scores.
10. Confirm which attempt is selected.
11. Confirm candidates were not merged.
12. Confirm the semantic regression result.
13. Confirm human review remains active when evidence is unresolved.
14. Do not print raw OCR text or raw source_text.
15. Do not add payer-specific reconstruction logic.
16. Do not use token count alone to choose a candidate.

After the real retry prompt is observed and evaluated, add a separate
regression profile for a second authorization document.

Do not apply Molina-specific expected values to every PDF in
data/incoming.

The unattended worker, production Smartsheet mapping, review Smartsheet
workflow, confirmed business rules, and final production routing remain
incomplete.

------------------------------------------------------------
NEXT SESSION START COMMANDS
------------------------------------------------------------

git status --short
git diff --stat
git diff --check

Then inspect:

scripts/test_molina_document.py
src/ai/llm/providers/ollama_provider.py
src/document_processing/document_processor.py
src/models/document.py
tests/test_document_processor.py
update_project_tracker.py

Run:

python -m tests.test_document_processor
python -m tests.test_ollama_service_lines
python -m tests.test_llm_attempt_routing
python -m tests.test_evidence_validation_service
python -m tests.test_review_decision_service
python -m scripts.test_molina_document

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
            "Graph, local PaddleOCR, local Ollama, field-level evidence, "
            "authorization service-line extraction, deterministic candidate "
            "validation, controlled retry, business rules, human review, and "
            "Smartsheet."
        ),
    ),
    (
        "Define Integration Architecture",
        "Completed",
        (
            "Completed integration architecture for Microsoft Graph mailbox "
            "ingestion followed by local OCR, separate local LLM requests, "
            "structured extraction, controlled retry, evidence validation, "
            "human review, and Smartsheet."
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
            "business rules, and human review."
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
            "reuse, privacy-safe logging, sanitized exceptions, and legacy "
            "cache migration."
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
            "cache reuse, and PHI-safe cache logging."
        ),
    ),
    (
        "Create Prompt Templates",
        "In Progress",
        (
            "Implemented separate local Ollama classification and extraction "
            "prompts with field-level evidence and service-line records. "
            "Repeated extraction can still vary, so controlled retry and human "
            "review remain active."
        ),
    ),
    (
        "Implement Classification",
        "In Progress",
        (
            "Implemented local Ollama classification with structured JSON and "
            "PHI-safe request metrics. Generic authorization classification "
            "works, while subtype and workflow classification remain "
            "untrained."
        ),
    ),
    (
        "Implement Data Extraction",
        "In Progress",
        (
            "Implemented field-level extraction, neutral service-line "
            "extraction, PHI-safe generation metrics, deterministic attempt "
            "routing, and one controlled retry with a generic verification "
            "prompt. A real retry event was observed, but recovery with the "
            "new retry prompt has not yet been observed in a real run."
        ),
    ),
    (
        "Validate AI Output",
        "In Progress",
        (
            "Implemented independent deterministic validation and scoring of "
            "extraction candidates. Candidates are never merged; the stronger "
            "supported candidate is selected and ambiguity remains routed to "
            "human review."
        ),
    ),
    (
        "Apply Business Rules",
        "In Progress",
        (
            "Authorization rules remain conservative and separate from "
            "evidence validation. Quantity and modifier relationships require "
            "human verification until confirmed requirements are available."
        ),
    ),
    (
        "Unit Test Rules",
        "In Progress",
        (
            "Real authorization testing confirms that unresolved quantity and "
            "modifier relationships route to human review. Synthetic retry, "
            "candidate-selection, validator, and review tests pass, while final "
            "business rules remain pending management confirmation."
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
            "is verified; real recovery with the new retry prompt and "
            "production Smartsheet routing remain incomplete."
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
        "In Progress",
        (
            "Normal Microsoft Graph authentication is implemented and tested. "
            "Dedicated tests for invalid credentials, expired secrets, missing "
            "permissions, Graph authorization failures, and sanitized error "
            "logging remain incomplete."
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
            task = tasks.find_task(
                task_name
            )

            if task is None:
                print(
                    f"Task not found: {task_name}"
                )
                not_found += 1
                continue

            changed = tasks.sync_task(
                task=task,
                status=status,
                comment=comment,
            )

            if changed:
                updated += 1
                print(
                    f"Updated: {task_name}"
                )
            else:
                unchanged += 1
                print(
                    f"No change: {task_name}"
                )

        except Exception as ex:
            failed += 1
            print(
                f"Failed: {task_name}"
            )
            print(
                f"  {ex}"
            )

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