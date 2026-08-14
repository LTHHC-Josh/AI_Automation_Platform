from src.services.project_status_service import ProjectStatusService


PROJECT_JOURNAL = """
============================================================
LTHHC AI AUTOMATION PLATFORM - DEVELOPMENT JOURNAL
============================================================

Last updated: 2026-08-10

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

Temporary helper scripts and project-tracker update scripts must be
delivered as one complete PowerShell block. The block must use a
single-quoted here-string piped to Set-Content at the exact file path,
include the complete script contents, run the script and related
commands, and remove the temporary script when appropriate.

Do not ask the user to create temporary files manually, choose their
paths, paste partial script contents into an editor, or assemble a
script from separate snippets.

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
  -> Automatic Smartsheet row population
  -> Conditional downstream human-review exception workflow

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
  -> Automatic intentionally mapped Smartsheet row population
  -> Conditional downstream human-review exception workflow
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
TOP-LEVEL CONFIDENCE NORMALIZATION STATUS
------------------------------------------------------------

Deterministic top-level confidence normalization is implemented.

Populated top-level extraction fields with model-reported confidence of
1.0 or 100 percent are capped at 0.95 before field-specific validation.

This prevents raw model certainty from being treated as deterministic
verification.

Current behavior:

- Populated values are capped at no more than 0.95.
- Existing confidence below 0.95 is preserved.
- Empty values receive confidence 0.0.
- Invalidated values receive confidence 0.0.
- Unsupported or conflicting evidence can be downgraded below 0.95.
- The confidence cap alone does not create a review action.
- Specific validation and business-rule failures still require review.
- Empty optional fields are excluded from minimum-field-confidence
  calculations.
- Numeric zero and boolean false remain meaningful populated values.

Files changed:

- src/services/evidence_validation_service.py
- src/services/review_decision_service.py
- tests/test_evidence_validation_service.py
- tests/test_review_decision_service.py
- tests/test_top_level_confidence_validation.py

Synthetic deterministic tests:

- Top-level confidence validation: 6 passed, 0 failed
- Evidence validation: 27 passed, 0 failed
- Review decision: 18 passed, 0 failed
- Document processor: 16 passed, 0 failed

Synthetic total:

Passed: 67
Failed: 0

Real Molina regression:

- Real cached PaddleOCR text
- Real local Ollama classification and extraction
- Supported populated top-level fields capped at 95 percent
- Empty or invalidated fields remained at 0 percent
- Minimum populated field confidence was 95 percent
- Human review remained active for legitimate validation and
  business-rule reasons
- PHI output remained suppressed

Real result:

Passed: 1
Failed: 0

Latest real performance:

- Total processing time: approximately 461.73 seconds
- OCR wall time: approximately 0.00 seconds using cached OCR
- Classification wall time: approximately 75.25 seconds
- Extraction wall time: approximately 386.48 seconds
- Extraction attempt count: 1
- Retry triggered: False
- Selected extraction attempt: 1

Limitations:

- A confidence of 0.95 means strongly supported model output, not final
  human verification.
- The unresolved top-level modifier-to-service-line relationship still
  requires review.
- Authorization quantity meaning still requires confirmation.
- A successful real retry where attempt 2 produces a stronger candidate
  has not yet been observed.

Exact next starting point:

Review business-rule handling for authorization quantities and determine
whether supported service-line quantities can be classified safely
without treating units, visits, sessions, or equipment quantities as
equivalent.


------------------------------------------------------------
AUTHORIZATION RULE REGISTRY CLEANUP STATUS
------------------------------------------------------------

The active authorization business-rule implementation was confirmed as:

src/business_rules/rules/authorization_rule.py

The obsolete parallel implementation was removed:

src/business_rules/authorization_rule.py

RuleFactory continues to load plugins from:

src.business_rules.rules

Registry verification confirmed:

- authorization resolves to AuthorizationRule
- authorization_renewal resolves to AuthorizationRenewalRule
- both classes come from src.business_rules.rules.authorization_rule
- no root-level authorization rule is registered
- no duplicate registry implementation remains active

Files changed:

- Deleted src/business_rules/authorization_rule.py
- Added tests/test_authorization_rule_registry.py

Synthetic deterministic registry test:

Passed: 5
Failed: 0

------------------------------------------------------------
AUTHORIZATION QUANTITY RULE STATUS
------------------------------------------------------------

The active authorization rule now recognizes positive quantities from:

- approved_visits
- authorized_units
- validated authorization service-line quantities

A supported quantity is treated only as evidence that a quantity exists.

The rule does not automatically interpret a quantity as:

- visits
- sessions
- units
- equipment quantities
- recurring services
- sufficient approval

When no positive quantity exists, the rule returns:

Missing authorization quantity

When a positive quantity exists but its meaning has not been confirmed,
the rule returns:

Authorization quantity requires verification

The action is emitted only once even when both flat fields and service
lines contain quantities.

Files changed:

- src/business_rules/rules/authorization_rule.py
- tests/test_authorization_quantity_rule.py

Synthetic deterministic quantity tests:

Passed: 8
Failed: 0

Related regression tests:

- Authorization registry: 5 passed, 0 failed
- Review decision: 18 passed, 0 failed
- Document processor: 16 passed, 0 failed

Related synthetic total:

Passed: 47
Failed: 0

------------------------------------------------------------
LATEST REAL QUANTITY REGRESSION
------------------------------------------------------------

The known Molina authorization regression was processed using:

- Real cached local PaddleOCR text
- Real local Ollama classification
- Real local Ollama extraction
- Deterministic evidence validation
- Updated authorization quantity business rules
- Human-review decision
- PHI-safe diagnostics

Verified real behavior:

- Two validated service-line records were preserved
- Positive quantities 1 and 6 were preserved
- Top-level authorized_units contained 6 and 1
- Missing authorization quantity was not returned
- Authorization quantity requires verification was returned
- Quantity meaning was not guessed
- Human verification remained required
- PHI output remained suppressed

Real result:

Passed: 1
Failed: 0

Real or mock:

Real cached OCR and local Ollama processing

Latest real performance:

- Total processing time: approximately 369.27 seconds
- OCR wall time: approximately 0.00 seconds using cached OCR
- Classification wall time: approximately 67.83 seconds
- Extraction wall time: approximately 301.43 seconds
- Extraction attempt count: 1
- Retry triggered: False
- Selected extraction attempt: 1
- Classification generation rate: approximately 6.46 tokens/second
- Extraction generation rate: approximately 5.56 tokens/second

Limitations:

- Quantity type remains unresolved without explicit supporting evidence.
- Units are not treated as visits.
- A positive quantity is not automatically treated as sufficient
  approval.
- The unresolved modifier-to-service-line relationship still requires
  review.
- A real retry where attempt 2 produces a stronger validated candidate
  has not yet been observed.

Exact next starting point:

Inspect the human-review output model and downstream document result
interfaces to determine how unresolved quantity type, modifier
relationships, and validation reasons should be presented to a reviewer
before mailbox-to-Smartsheet automation may proceed.


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

Passed: 18
Failed: 0

Real or mock:

Synthetic deterministic test

------------------------------------------------------------
AUTHORIZED-UNIT RECONCILIATION STATUS
------------------------------------------------------------

A deterministic same-candidate reconciliation check is implemented for
authorized_units and supported authorization service-line quantities.

The reconciliation is deliberately limited:

- It runs only when authorized_units already contains a populated
  extracted value.
- It compares that existing flat value with independently validated
  service-line quantities from the same extraction candidate.
- It may restore a supported quantity omitted from the flat list when
  the same candidate preserved that quantity on a validated service
  line.
- It never combines values from separate Ollama attempts.
- It never creates authorized_units when the flat field is missing or
  empty.
- It never interprets quantities as visits, sessions, equipment,
  recurring services, or sufficient approval.
- It preserves source_text.
- It uses the lowest supporting confidence.
- It emits a human-review validation action when reconciliation occurs.

Validation action:

Authorized units were reconciled from supported service-line evidence

Synthetic reconciliation result:

Passed: 7
Failed: 0

Synthetic regression results:

- Evidence validation: 27 passed, 0 failed
- Document processor: 16 passed, 0 failed
- Authorization quantity rules: 8 passed, 0 failed
- Review decision: 18 passed, 0 failed

Combined synthetic result:

Passed: 76
Failed: 0

------------------------------------------------------------
LATEST REAL RECONCILIATION REGRESSION
------------------------------------------------------------

The known Molina authorization regression was rerun after implementing
same-candidate authorized-unit reconciliation.

Real result:

Passed: 1
Failed: 0

Real or mock:

Real cached PaddleOCR text and real local Ollama processing

Verified output:

- Document type remained authorization.
- Classification confidence remained 90 percent.
- Exactly two service-line records were preserved.
- Service-line quantities 1 and 6 were preserved.
- Top-level authorized_units preserved both 6 and 1.
- Semantic regression passed.
- Human verification remained required.
- Authorization quantity still required verification.
- PHI output remained suppressed.
- Extraction attempt count was 1.
- Retry was not triggered.
- Attempt 1 was selected.

Latest timing:

- Total processing time: approximately 369.83 seconds
- Classification wall time: approximately 66.24 seconds
- Extraction wall time: approximately 303.59 seconds
- Extraction eval count: 1201
- Extraction generation rate: approximately 5.51 tokens per second

Repeatability status:

Completed successfully.

Three consecutive real cached-OCR and local-Ollama executions passed.
Each run triggered validated retry, selected the stronger second
candidate, preserved quantities 1 and 6, reconciled authorized_units
from same-candidate service-line evidence, retained human review, and
suppressed PHI output.


------------------------------------------------------------
THREE-RUN REAL REPEATABILITY RESULT
------------------------------------------------------------

The known Molina authorization regression completed three consecutive
successful real runs after same-candidate authorized-unit reconciliation
was implemented.

Final result:

Successful consecutive runs: 3 of 3

REPEATABILITY RESULT:

PASSED

Real or mock:

Real cached PaddleOCR text and real local Ollama processing

All three runs confirmed:

- Document type remained authorization.
- Classification confidence remained 90 percent.
- Attempt 1 produced the known incomplete 1080-token extraction pattern.
- Deterministic validation identified incomplete supported structure.
- Raw retry required remained False.
- Validated retry required remained True.
- Controlled extraction retry was triggered.
- Attempt 1 used seed 42.
- Attempt 2 used seed 43.
- Attempt 2 produced the stronger 1198-token extraction pattern.
- Attempt 2 was selected by deterministic candidate scoring.
- Candidates were independently validated.
- Candidates were never merged.
- Both service-line records preserved service code S9110.
- Service-line quantities 1 and 6 were preserved.
- Top-level authorized_units preserved both quantities after
  same-candidate deterministic reconciliation.
- Reconciled authorized_units confidence was reduced to 50 percent using
  the lowest supporting confidence.
- Human verification remained required.
- Authorization quantity interpretation remained unresolved.
- Modifier-to-service-line ownership remained unresolved.
- PHI output remained suppressed.
- Semantic regression passed.

Run results:

Run 1:

- Passed: 1
- Failed: 0
- Total time: approximately 579.08 seconds
- Extraction attempts: 2
- Selected attempt: 2
- Attempt 1 eval count: 1080
- Attempt 2 eval count: 1198

Run 2:

- Passed: 1
- Failed: 0
- Total time: approximately 624.75 seconds
- Extraction attempts: 2
- Selected attempt: 2
- Attempt 1 eval count: 1080
- Attempt 2 eval count: 1198

Run 3:

- Passed: 1
- Failed: 0
- Total time: approximately 474.30 seconds
- Extraction attempts: 2
- Selected attempt: 2
- Attempt 1 eval count: 1080
- Attempt 2 eval count: 1198

Conclusion:

The controlled retry, independent validation, deterministic candidate
selection, same-candidate quantity reconciliation, and human-review
safeguards successfully handled the known variable extraction pattern
in three consecutive real executions.

The repeatability investigation for this regression fixture is complete.

This result does not prove universal model determinism. Repeated local
Ollama output still varied between incomplete attempt 1 and stronger
attempt 2 patterns. Reliability was achieved through controlled retry
and deterministic safeguards rather than reliance on model consistency.


------------------------------------------------------------
STRUCTURED HUMAN-REVIEW OUTPUT STATUS
------------------------------------------------------------

A neutral structured human-review output contract is implemented.

Files:

- src/services/review_output_service.py
- tests/test_review_output_service.py
- tests/test_review_output_integration.py

Document model integration:

- src/models/document.py now contains review_output.
- src/document_processing/document_processor.py attaches review_output
  only after extraction, validation, business rules, review decisions,
  and PHI-safe processing metrics are complete.
- The review-output service does not rerun or reinterpret extraction,
  validation, business rules, quantities, approval, modifiers, or
  review decisions.

The review output preserves:

- document type
- classification confidence
- extracted field value
- extracted field confidence
- extracted field source_text
- authorization service-line relationships
- service-line confidence
- service-line source_text
- validation actions
- business-rule actions
- human-review status
- human-review reasons
- minimum populated field confidence
- extraction attempt count
- extraction retry status
- selected extraction attempt
- authorized-unit reconciliation status

The review output deliberately excludes:

- raw OCR text
- local document file path

The exclusion applies to the neutral review handoff contract and
diagnostic output. It does not remove validated PHI-bearing field values
or source evidence required for authorized local review and future
approved Smartsheet mapping.

PHI handling:

- OCR and Ollama processing remain local and in-house.
- Structured PHI remains available in memory for approved operational
  workflows.
- Console output, processing metrics, test results, tracker content,
  temporary scripts, and Git history remain PHI-safe.
- Future Smartsheet writes may include approved PHI fields only through
  the approved LTHHC Smartsheet workspace and confirmed column mapping.
- Failed Smartsheet writes must never log or print the row payload.
- source_text must not be written to Smartsheet unless an approved
  destination and operational requirement are confirmed.

Synthetic deterministic results:

Review-output service:

Passed: 8
Failed: 0

Review-output integration:

Passed: 7
Failed: 0

Related regression results:

Review-decision service:

Passed: 18
Failed: 0

DocumentProcessor:

Passed: 16
Failed: 0

Combined synthetic result:

Passed: 49
Failed: 0

Latest real Molina review-output regression:

Passed: 1
Failed: 0

Real or mock:

Real cached PaddleOCR text and real local Ollama processing

Verified real behavior:

- Review output was attached to the completed Document.
- Nineteen field review records were retained.
- Two authorization service-line records were retained.
- Field value, confidence, and source_text structures were available.
- Human-review status matched the processed Document.
- Human-review reasons matched the processed Document.
- Validation actions were preserved.
- Business-rule actions were preserved.
- Extraction attempt count was preserved.
- Retry status was preserved.
- Selected extraction attempt was preserved.
- Raw OCR text was not exposed by the review-output contract.
- The local document path was not exposed by the review-output contract.
- Semantic regression passed.
- PHI output remained suppressed.

Latest real execution:

- Total processing time: approximately 383.60 seconds
- OCR wall time: approximately 0.00 seconds using cached OCR
- Classification wall time: approximately 73.59 seconds
- Extraction wall time: approximately 310.00 seconds
- Extraction attempt count: 1
- Retry triggered: False
- Selected extraction attempt: 1
- Review-output field count: 19
- Review-output service-line count: 2

Current limitations:

- Review output is an in-memory contract and is not yet serialized for
  an external system.
- Smartsheet column mappings are not yet defined or tested.
- No automatic Smartsheet row creation is enabled.
- Quantity meaning remains unresolved.
- Units are not automatically interpreted as visits, sessions,
  equipment, recurring services, or sufficient approval.
- Modifier-to-service-line ownership remains unresolved.
- source_text may contain PHI and must remain restricted to approved
  systems and workflows.
- The known Molina authorization remains a regression fixture and not a
  universal payer or service-code rule.

Exact next starting point:

Define a deterministic Smartsheet row-mapping contract from the
structured review output using synthetic data. Confirm required,
optional, review-only, and prohibited columns before enabling any
Smartsheet write. Preserve PHI-bearing operational values while keeping
logs, errors, metrics, tests, and Git history PHI-safe.


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
- The generic retry verification prompt was observed in three consecutive
  real incomplete-first-attempt events and produced a stronger second
  candidate each time.
- A stronger independently validated second candidate was selected in
  three consecutive real retry events.

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

- Conservative authorization quantity business rules
- Removal of the obsolete duplicate authorization-rule implementation
- Top-level confidence normalization
- Empty optional fields excluded from minimum-confidence calculation
- Populated fields without confidence remain conservatively scored
- Same-candidate authorized-unit reconciliation
- Preservation of value, confidence, and source_text
- Controlled authorization extraction retry
- Independent deterministic candidate validation
- Stronger-candidate selection without candidate merging
- Human-review routing for unsupported or ambiguous evidence
- PHI-safe real regression diagnostics

Focused synthetic results:

- Service-line quantity reconciliation: 7 passed, 0 failed
- Evidence validation: 27 passed, 0 failed
- Top-level confidence validation: 6 passed, 0 failed
- Document processor: 16 passed, 0 failed
- Authorization quantity rule: 8 passed, 0 failed
- Authorization rule registry: 5 passed, 0 failed
- Review decision: 18 passed, 0 failed

Combined focused result:

Passed: 87
Failed: 0

Real repeatability result:

- Three consecutive runs passed.
- Each run used real cached PaddleOCR text and real local Ollama.
- Each run produced an incomplete first candidate.
- Validated incompleteness triggered controlled retry.
- Each stronger second candidate was selected.
- Candidates were never merged.
- Quantities 1 and 6 were preserved.
- authorized_units was reconciled using evidence from the selected
  candidate only.
- Human review remained required.
- PHI output remained suppressed.

This proves the safeguards handle the known Molina regression fixture
repeatedly. It does not prove universal model determinism or remove the
need for human review.

------------------------------------------------------------
EXACT NEXT DEVELOPMENT STEP
------------------------------------------------------------

Define and test the structured human-review output and downstream
handoff contract before mailbox-to-Smartsheet automation proceeds.

The review payload must preserve and clearly expose:

- Extracted value
- Confidence
- source_text reference without printing PHI in logs
- Validation actions
- Business-rule actions
- Review status
- Review reasons
- Selected extraction attempt
- Whether retry occurred
- Whether authorized_units was reconciled
- Low-confidence service-line evidence
- Unresolved authorization quantity meaning
- Unresolved modifier-to-service-line ownership

Start by inspecting:

src/models/document.py
src/services/review_decision_service.py
src/document_processing/document_processor.py
tests/test_review_decision_service.py

Then define the smallest neutral review-output model or serialization
contract that uses existing validated data without duplicating
validation or business-rule logic.

Do not send PHI to external services.
Do not enable automatic Smartsheet routing until the human-review
contract and confirmed field mappings are tested.

------------------------------------------------------------
NEXT SESSION START COMMANDS
------------------------------------------------------------

git status --short
git diff --stat
git diff --check
git --no-pager diff --cached --name-status
git --no-pager diff --cached --check

Then inspect:

src/models/document.py
src/services/review_decision_service.py
src/document_processing/document_processor.py
tests/test_review_decision_service.py
update_project_tracker.py

Run the focused deterministic tests before changing the review-output
contract.

============================================================

------------------------------------------------------------
SMARTSHEET DOCUMENT ROW MAPPING STATUS
------------------------------------------------------------

The future operational Smartsheet destination will use one row per
processed document.

The original source document will be attached to that row after the
operational sheet, attachment workflow, access controls, and PHI-safe
error handling are approved.

The currently connected Smartsheet is the project tracker only.

The project tracker sheet, sheet ID, columns, and rows must not be used
for authorization or patient-document records.

The future operational sheet has not yet been created.

Implemented local boundaries:

- Policy-driven structured review-output field mapping
- One logical row mapping per document
- Required destination-column detection
- Review-only column identification
- Prohibited raw OCR, file-path, processing-metric, and source_text
  mappings
- Deterministic collection serialization
- Preservation of numeric zero and boolean false
- Human-review gating before automatic write readiness
- Destination-column name and positive-ID validation
- Missing destination-column detection
- Invalid and duplicate destination-ID detection
- PHI-safe destination-validation output containing names and IDs only

No Smartsheet SDK cells were created.

No Smartsheet row was created or updated.

No operational Smartsheet connection was attempted.

Files changed:

- src/models/smartsheet_mapping.py
- src/models/smartsheet_destination_validation.py
- src/services/smartsheet_review_row_mapping_service.py
- src/services/smartsheet_destination_validation_service.py
- tests/test_smartsheet_review_row_mapping.py
- tests/test_smartsheet_review_mapping_integration.py
- tests/test_smartsheet_destination_validation.py

Synthetic deterministic tests:

- Smartsheet destination validation: 12 passed, 0 failed
- Document-to-Smartsheet mapping integration: 9 passed, 0 failed
- Smartsheet review-row mapping: 12 passed, 0 failed
- Review-output service regression: 8 passed, 0 failed
- Review-output integration regression: 7 passed, 0 failed

Synthetic total:

Passed: 48
Failed: 0

Real or mock status:

- Synthetic deterministic only
- No mock external write
- No real external integration
- No operational destination sheet exists yet

PHI handling:

- Test values and source evidence were not printed
- Raw OCR text was excluded from the mapping contract
- Local file paths were excluded from the mapping contract
- source_text was preserved in local review output but prohibited from
  Smartsheet mapping
- Destination validation retained column names and IDs only
- No Smartsheet payload was logged

Limitations:

- The operational one-row-per-document sheet has not been created
- The final operational column list has not been approved
- The original-document attachment workflow is not implemented
- The current Smartsheet credentials and sheet ID belong only to the
  project tracker
- No authorization-document row may be written using the tracker sheet
- Service-line values remain represented within the document-level
  review contract and require an approved one-row serialization policy

Document-classification requirement:

Document identification is a first-class platform result because source
documents arrive in nonstandard formats from multiple service
coordinators.

The classification contract must be expanded before operational inbox
training begins.

Termination classification is restricted to termination or
discontinuation of an authorization or authorized service.

Employee, provider, vendor, and other administrative terminations must
not be classified as authorization or service termination.

Exact next starting point:

Implement and test a two-level document classification contract with
document category and subtype while preserving conservative unknown
handling and the existing separate local classification and extraction
requests.


------------------------------------------------------------
TWO-LEVEL DOCUMENT CLASSIFICATION STATUS
------------------------------------------------------------

Document identification is now represented as a two-level local
classification contract.

Classification fields:

- document_category
- document_subtype
- document_type
- confidence
- classification_reason

document_type remains a backward-compatible routing value for existing
extraction and authorization-retry behavior.

Current document categories:

- authorization
- referral
- termination
- denial
- assessment
- plan_of_care
- claim
- other
- unknown

Current authorization subtypes:

- initial
- renewal
- extension
- continuation
- amendment
- partial_approval
- unknown

Current termination subtypes:

- authorization_termination
- service_termination
- unknown

Termination scope is restricted to an authorization or authorized
service being terminated, discontinued, revoked, ended, closed, or
stopped.

Employee, provider, vendor, contract, and administrative terminations
must not be classified as authorization or service termination.

Classification and extraction remain separate local Ollama requests.

The classifier uses supported document purpose and content rather than
assuming a standard template, sender, logo, filename, payer, or service
coordinator format.

Unknown, missing, conflicting, invalid, or incompatible classification
values remain unknown or require human review.

The classifier does not infer a subtype from the presence of unselected
checkbox labels.

Legacy routing behavior:

- authorization initial and unknown subtype route as authorization
- authorization renewal, extension, continuation, and amendment route
  as authorization_renewal
- other categories route using their category value

A neutral business rule is implemented for recognized categories that
do not yet have category-specific business rules.

The neutral rule produces no business-rule actions.

No rule actions does not mean the document is verified. Classification
review, deterministic validation, field confidence, and human-review
decisions remain separate.

Unsupported internal document-routing values still raise an error.

Classification review gating now requires or recommends human review
when:

- document category is unknown
- document category is unsupported
- classification confidence is below configured thresholds
- authorization subtype is unknown
- termination subtype is unknown
- category and subtype are incompatible
- category is other
- classification reason is missing

Unknown termination subtype requires human review because the platform
must distinguish termination of the authorization as a whole from
termination of a specific authorized service.

Unknown authorization subtype currently recommends review rather than
inventing initial, renewal, extension, continuation, amendment, or
partial approval.

Files changed:

- src/ai/llm/providers/mock_provider.py
- src/ai/llm/providers/ollama_provider.py
- src/business_rules/rule_factory.py
- src/business_rules/rules/neutral_rule.py
- src/document_processing/document_processor.py
- src/models/document.py
- src/services/review_decision_service.py
- src/services/review_output_service.py
- tests/test_classification_review_gating.py
- tests/test_document_classification_contract.py
- tests/test_neutral_business_rule.py
- tests/test_processor_classification_integration.py
- tests/test_review_decision_service.py

Synthetic deterministic and provider-routing tests:

- Classification review gating: 11 passed, 0 failed
- Review decision service: 18 passed, 0 failed
- Processor classification integration: 10 passed, 0 failed
- Neutral business-rule routing: 6 passed, 0 failed
- Document classification contract: 15 passed, 0 failed
- Document processor regressions: 16 passed, 0 failed
- Review-output service regressions: 8 passed, 0 failed
- Review-output integration regressions: 7 passed, 0 failed
- LLM extraction-attempt routing: 2 passed, 0 failed

Synthetic total:

Passed: 93
Failed: 0

Real or mock status:

- Synthetic deterministic tests
- Synthetic provider-routing tests
- No PaddleOCR prediction
- No local Ollama request
- No Microsoft Graph call
- No Smartsheet call
- No external integration

PHI handling:

- No OCR text was printed
- No extracted document values were printed
- No patient documents were used
- No patient-identifying paths were used
- Classification metrics retained PHI-safe metadata only
- Review output continues to exclude raw OCR text and local file paths
- No source_text or Smartsheet payload was logged

Limitations:

- The taxonomy is an approved initial classification contract and will
  require expansion from human-confirmed inbox examples
- No real local Ollama classification has yet been run against examples
  of referral, initial authorization, renewal, authorization
  termination, or service termination
- No approved training-example storage contract exists yet
- PHI-bearing documents and OCR text must remain local
- Human corrections must be captured without committing patient data,
  OCR text, source evidence, or identifying document paths
- The operational Smartsheet destination sheet does not yet exist
- The original-document attachment workflow is not implemented
- Category-specific business rules for non-authorization documents have
  not yet been defined

Exact next starting point:

Design a PHI-safe classification feedback and regression-fixture
contract that records human-confirmed category and subtype labels without
committing patient documents, OCR text, identifying paths, or extracted
PHI.


------------------------------------------------------------
PHI-SAFE CLASSIFICATION FEEDBACK AND FINGERPRINT STATUS
------------------------------------------------------------

A PHI-safe feedback contract records human-confirmed document
classification labels without retaining document content or patient
information.

Feedback fields:

- document_fingerprint
- predicted_category
- predicted_subtype
- confirmed_category
- confirmed_subtype
- classification_confidence
- correction_required
- reviewer_confirmation_status
- created_at

A reusable local DocumentFingerprintService now calculates lowercase
SHA-256 fingerprints by reading source files in one-megabyte chunks.

Fingerprint results contain exactly:

- fingerprint
- byte_count
- success
- status

Fingerprint results never contain:

- source paths
- filenames
- document content
- OCR text
- source_text
- extracted values
- patient identifiers
- exception messages

Failure results use PHI-safe statuses and return no fingerprint. Failed
or incomplete reads return a deterministic byte count of zero.

PaddleOCR now uses DocumentFingerprintService for OCR-cache identity.
The former private PaddleOCR file-hashing implementation and direct
hashlib dependency were removed. Existing cache filenames continue to
use only the lowercase SHA-256 fingerprint.

A local ClassificationFeedbackWorkflowService now coordinates:

1. local document fingerprinting;
2. validated feedback construction from ReviewOutput classification
   metadata;
3. local allowlisted JSONL storage.

The workflow source path is supplied only to the local fingerprint
service. It is not copied into feedback, storage, logs, or results.

Workflow results contain exactly:

- fingerprint
- byte_count
- success
- status

The feedback review adapter reads only category, subtype, and
classification confidence from ReviewOutput. It does not mutate the
review output or copy fields, service lines, source evidence, review
reasons, validation actions, business-rule actions, or other
PHI-bearing values.

Reviewer confirmation status remains deterministic:

- unchanged labels require confirmed
- changed labels require corrected

Validated feedback records are stored locally as JSON Lines under:

data/classification_feedback/classification_feedback.jsonl

The entire data/classification_feedback directory remains ignored by
Git.

The storage service accepts only ClassificationFeedback objects and
serializes an exact allowlist of feedback keys.

Duplicate detection and append execution remain inside an atomic local
lock-directory boundary. Repeated workflow submission for the same
fingerprint is idempotent: the initial submission is stored and later
submissions return duplicate_fingerprint without writing another record.

Files changed:

- src/ai/ocr/providers/paddle_ocr_provider.py
- src/services/document_fingerprint_service.py
- src/services/classification_feedback_workflow_service.py
- tests/test_document_fingerprint_service.py
- tests/test_paddle_ocr_fingerprint_integration.py
- tests/test_classification_feedback_workflow_service.py

Affected regressions also verified:

- src/services/classification_feedback_service.py
- src/services/classification_feedback_review_service.py
- src/services/classification_feedback_storage_service.py
- tests/test_classification_feedback_service.py
- tests/test_classification_feedback_review_integration.py
- tests/test_classification_feedback_storage_service.py
- tests/test_classification_feedback_storage_locking.py

Tests:

- Document fingerprint service: 10 passed, 0 failed
- PaddleOCR fingerprint integration: 3 passed, 0 failed
- Classification feedback workflow: 7 passed, 0 failed
- Classification feedback contract: 11 passed, 0 failed
- Feedback-to-review integration: 11 passed, 0 failed
- Local feedback storage: 11 passed, 0 failed
- Concurrent storage locking: 4 passed, 0 failed

Affected regression total:

Passed: 57
Failed: 0

Real or mock status:

- Synthetic deterministic local-file tests
- Synthetic deterministic integration tests
- Synthetic deterministic local workflow tests
- Synthetic concurrent local-storage tests
- PaddleOCR prediction was not called
- Local Ollama was not called
- Microsoft Graph was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- Only synthetic document bytes were used
- No patient documents were used
- No OCR text was printed or stored by these tests
- No source_text was copied into feedback storage
- No extracted document values were stored
- No identifying source paths or filenames were returned
- No email content was used
- Feedback storage contained only allowlisted classification metadata
- Test files and feedback stores used temporary local directories
- The ignored production feedback directory was not read or printed

Limitations:

- The production human-review submission path does not yet invoke
  ClassificationFeedbackWorkflowService
- No user interface currently submits reviewer confirmation
- The workflow has not been tested with a real PHI-bearing document
- PaddleOCR integration was tested with a synthetic cache hit; no fresh
  PaddleOCR prediction was performed
- The JSONL store does not provide administrative retention, export,
  migration, or recovery tooling
- Lock timeout behavior has not been tested with separate
  operating-system processes
- Feedback records are not yet converted into committed synthetic
  regression fixtures
- Document mutation during fingerprint calculation is not explicitly
  detected
- Human-confirmed labels do not authorize retaining or committing source
  documents, OCR text, source evidence, or extracted PHI

------------------------------------------------------------
EXPLICIT REVIEW CONFIRMATION SUBMISSION STATUS
------------------------------------------------------------

A production-facing ReviewConfirmationSubmissionService now provides
the explicit boundary between a completed local human review and the
classification feedback workflow.

The service accepts:

- one already-processed Document
- the Document's existing attached ReviewOutput
- reviewer-confirmed document category
- reviewer-confirmed document subtype
- explicit reviewer confirmation status
- optional PHI-safe timestamp

Accepted confirmation statuses:

- confirmed
- corrected

Any blank, pending, unsupported, or implicit confirmation status is
rejected before the feedback workflow is called.

The service does not rerun:

- OCR
- classification
- extraction
- deterministic validation
- candidate selection
- business rules
- review decisions
- review-output construction

The existing ReviewOutput object is passed unchanged to the feedback
workflow. The processed Document and its review snapshot are not
mutated.

The source document path is used only as the local input to the existing
fingerprint workflow. It is not returned, logged, copied into feedback,
or included in storage.

Submission results contain exactly:

- fingerprint
- byte_count
- success
- status

Submission results exclude:

- source paths
- filenames
- OCR text
- raw document text
- extracted values
- field evidence
- source_text
- review fields
- service lines
- patient identifiers
- storage payloads

Files changed:

- src/services/review_confirmation_submission_service.py
- tests/test_review_confirmation_submission_service.py

Focused and affected tests:

- Review confirmation submission boundary: 12 passed, 0 failed
- Classification feedback workflow: 7 passed, 0 failed
- Classification feedback review integration: 11 passed, 0 failed

Test total:

Passed: 30
Failed: 0

Real or mock status:

- Synthetic deterministic boundary tests
- Synthetic deterministic workflow tests
- Synthetic deterministic review integration tests
- OCR was not called
- Ollama was not called
- Extraction was not called
- Deterministic validation was not called
- Business rules were not called
- Microsoft Graph was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No OCR text was printed or stored
- No extracted values were returned
- No source_text was copied into feedback
- No source paths were returned or printed
- Existing review output was passed unchanged
- Only synthetic local objects were used
- Feedback storage was not inspected or printed

Limitations:

- No end-user interface currently invokes this service
- No mailbox or Smartsheet workflow invokes this service
- Reviewer identity and authorization are not yet represented
- The service does not persist a separate review-submission audit event
- A real human correction has not yet been submitted
- The service assumes Document.file_path remains locally available when
  the reviewer submits feedback
- Explicit confirmation improves the classification feedback dataset
  but does not automatically retrain or modify Ollama model weights

------------------------------------------------------------
LOCAL CLASSIFICATION REVIEW INTERACTION STATUS
------------------------------------------------------------

A reusable local ClassificationReviewInteraction now provides the
smallest reviewer-facing interaction for confirming or correcting one
completed document classification.

The interaction receives one already-processed Document with an
attached ReviewOutput.

It displays only:

- predicted document category
- predicted document subtype
- classification confidence
- PHI-safe submission status

It does not display:

- source path
- filename
- OCR text
- raw document text
- classification reason
- extracted field values
- field evidence
- source_text
- service lines
- patient identifiers
- feedback-storage payloads

Reviewer actions:

- Confirm the predicted category and subtype
- Correct the category and subtype
- Cancel without submitting feedback

A confirmation uses the existing predicted labels and submits status
confirmed.

A correction requires both category and subtype and submits status
corrected.

Blank corrections, invalid selections, missing review output, and
invalid document objects are rejected before the submission service is
called.

The interaction calls ReviewConfirmationSubmissionService only after
an explicit reviewer choice.

The interaction does not rerun:

- document processing
- OCR
- classification
- extraction
- deterministic validation
- candidate selection
- business rules
- review decisions
- review-output construction

The processed Document and existing ReviewOutput are not mutated.

Files changed:

- src/ui/classification_review_interaction.py
- tests/test_classification_review_interaction.py

Focused and affected tests:

- Classification review interaction: 12 passed, 0 failed
- Review confirmation submission: 12 passed, 0 failed
- Classification feedback workflow: 7 passed, 0 failed

Test total:

Passed: 31
Failed: 0

Real or mock status:

- Synthetic deterministic UI-boundary tests
- Synthetic deterministic submission-boundary tests
- Synthetic deterministic workflow tests
- Document processing was not called
- OCR was not called
- Ollama was not called
- Microsoft Graph was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No OCR text was displayed
- No source paths were displayed
- No extracted values were displayed
- No source_text was displayed
- No classification reason was displayed
- Entered correction labels were not echoed
- No feedback-storage payload was displayed
- Only category, subtype, confidence, and status were displayed
- All test data was synthetic

Limitations:

- The interaction is reusable but is not yet attached to the general
  application menu
- The interaction is not yet attached to MailboxProcessor
- No persistent review queue currently exists
- Processed Document objects must remain available in memory
- Reviewer identity and authorization are not represented
- A real human reviewer has not yet submitted feedback
- The interaction improves the feedback workflow but does not retrain
  or modify Ollama model weights

------------------------------------------------------------
MAILBOX REVIEW SESSION COORDINATOR STATUS
------------------------------------------------------------

A local MailboxReviewSessionService now coordinates explicit review of
already-processed mailbox documents without modifying mailbox ingestion.

The service receives existing MessageProcessingResult objects and
invokes ClassificationReviewInteraction once for each processed
Document, in the original message and document order.

The coordinator does not:

- fetch mailbox messages
- download attachments
- process documents
- run OCR
- call Ollama
- perform classification
- perform extraction
- run deterministic validation
- apply business rules
- mark messages as read
- write to Smartsheet
- automatically submit feedback

Each document still requires an explicit reviewer action through the
existing ClassificationReviewInteraction.

The coordinator tracks only PHI-safe session metadata:

- message_count
- document_count
- submitted_count
- cancelled_count
- failed_count
- success
- status

Session results exclude:

- message identifiers
- email subjects
- source paths
- filenames
- OCR text
- raw document text
- extracted values
- source evidence
- source_text
- review content
- correction labels
- fingerprints
- storage payloads
- patient identifiers

Session statuses:

- completed
- completed_with_cancellations
- completed_with_failures
- no_documents
- invalid_message_results
- invalid_message_result

A cancelled review is counted separately and does not make the session
fail.

A failed submission is counted and causes the session result to report
completed_with_failures.

An empty message collection or a collection containing no processed
documents is treated as a successful no-op with status no_documents.

Existing MessageProcessingResult objects and their processed_documents
lists are not mutated.

Files changed:

- src/services/mailbox_review_session_service.py
- tests/test_mailbox_review_session_service.py

Focused and affected tests:

- Mailbox review session coordinator: 13 passed, 0 failed
- Classification review interaction: 12 passed, 0 failed
- Review confirmation submission: 12 passed, 0 failed

Test total:

Passed: 37
Failed: 0

Real or mock status:

- Synthetic deterministic coordinator tests
- Synthetic deterministic UI-boundary tests
- Synthetic deterministic submission-boundary tests
- Mailbox ingestion was not called
- Attachment download was not called
- Document processing was not called
- OCR was not called
- Ollama was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No mailbox message identifiers were returned
- No email subjects were returned
- No source paths were returned
- No filenames were returned
- No OCR text was returned
- No extracted values were returned
- No source_text was returned
- No review content was returned
- No correction labels were returned
- No fingerprints were returned
- No storage payloads were returned
- Only counts, booleans, and status were returned
- All test data was synthetic

Limitations:

- The coordinator is not yet connected to MailboxProcessor
- The coordinator is not yet invoked by a production command or menu
- Processed Document objects must remain available in memory
- No persistent review queue exists
- Reviewer identity and authorization are not represented
- No resume or recovery mechanism exists for interrupted review sessions
- No real mailbox messages or patient documents were used
- The existing scripts/test_mailbox_processor.py remains PHI-unsafe for
  real documents because it prints paths, OCR text, and extracted values

------------------------------------------------------------
MAILBOX REVIEW ORCHESTRATION STATUS
------------------------------------------------------------

A separate MailboxReviewOrchestrationService now connects mailbox
processing to the explicit local review session without merging their
responsibilities.

The orchestration service:

- calls MailboxProcessor.process_unread_messages exactly once
- validates and normalizes the requested unread-message limit
- passes the returned in-memory MessageProcessingResult collection
  directly to MailboxReviewSessionService
- forwards the optional created_at value
- preserves review-session counts and status
- sanitizes mailbox and review exceptions into fixed status values

The orchestration service does not inspect, print, log, copy, or return:

- message identifiers
- email subjects
- attachment paths
- filenames
- OCR text
- raw document text
- extracted values
- field evidence
- source_text
- review content
- reviewer correction labels
- fingerprints
- storage payloads
- patient identifiers

Orchestration results contain exactly:

- message_count
- document_count
- submitted_count
- cancelled_count
- failed_count
- success
- status

Supported orchestration statuses include:

- completed
- completed_with_cancellations
- completed_with_failures
- no_documents
- invalid_top
- mailbox_processing_failed
- review_session_failed

Mailbox ingestion remains owned by MailboxProcessor.

Explicit human review remains owned by MailboxReviewSessionService and
ClassificationReviewInteraction.

Files added:

- src/services/mailbox_review_orchestration_service.py
- tests/test_mailbox_review_orchestration_service.py

Focused orchestration tests:

Passed: 11
Failed: 0

Real or mock status:

- Mock orchestration test
- MailboxProcessor was mocked
- MailboxReviewSessionService was mocked
- Microsoft Graph was not called
- Attachment download was not called
- Document processing was not called
- OCR was not called
- Ollama was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No message identifiers were returned
- No email subjects were returned
- No source paths were returned
- No filenames were returned
- No OCR text was returned
- No extracted values were returned
- No source_text was returned
- No review content was returned
- No fingerprints were returned
- No storage payloads were returned
- Only counts, booleans, and status were returned
- All test data was synthetic

------------------------------------------------------------
PHI-SAFE MAILBOX REVIEW COMMAND STATUS
------------------------------------------------------------

A separate opt-in MailboxReviewCommand now provides a PHI-safe local
command boundary for the mailbox-review orchestration workflow.

The command runs only when explicitly invoked.

It is not attached to an automatic startup path or general application
menu.

The command:

- calls MailboxReviewOrchestrationService exactly once
- accepts an optional unread-message limit
- accepts an optional created_at value
- returns the orchestration result unchanged
- prints only PHI-safe summary fields

Displayed fields:

- message_count
- document_count
- submitted_count
- cancelled_count
- failed_count
- success
- status

The command does not print:

- message identifiers
- email subjects
- attachment paths
- filenames
- created_at
- OCR text
- raw document text
- extracted values
- source evidence
- source_text
- review content
- correction labels
- fingerprints
- storage payloads
- patient identifiers
- exception details

Files added:

- src/ui/mailbox_review_command.py
- tests/test_mailbox_review_command.py

Focused command tests:

Passed: 8
Failed: 0

Affected regression results:

- Mailbox review orchestration: 11 passed, 0 failed
- Mailbox review session: 13 passed, 0 failed

Combined tested result:

Passed: 32
Failed: 0

Real or mock status:

- Mailbox review command test used a mocked orchestration service
- Mailbox review orchestration test used mocked mailbox and review
  services
- Mailbox review session test was synthetic deterministic
- Microsoft Graph was not called
- Attachment download was not called
- Document processing was not called
- OCR was not called
- Ollama was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No mailbox data was displayed
- No source paths were displayed
- No filenames were displayed
- No OCR text was displayed
- No extracted values were displayed
- No source_text was displayed
- No review evidence was displayed
- No correction labels were displayed
- No fingerprint was displayed
- Only counts, success, and status were displayed
- All test data was synthetic

Limitations:

- The real opt-in command has not yet been executed against Microsoft
  Graph
- No real mailbox messages or patient documents were used
- No persistent review queue exists
- Processed Document objects remain in memory only
- Reviewer identity and authorization are not represented
- No resume or recovery exists for interrupted review sessions
- The command is not attached to a general application menu
- The existing scripts/test_mailbox_processor.py remains PHI-unsafe for
  real documents because it prints paths, OCR text, and extracted values
- Smartsheet submission is not enabled by this command

------------------------------------------------------------
REAL MAILBOX REVIEW EXECUTION STATUS
------------------------------------------------------------

The PHI-safe opt-in mailbox review command completed its first real
Graph-backed execution successfully.

Execution command:

python -m src.ui.mailbox_review_command --top 1

Real result:

- message_count: 1
- document_count: 1
- submitted_count: 1
- cancelled_count: 0
- failed_count: 0
- success: True
- status: completed

Real or mock status:

- Microsoft Graph mailbox access was real
- Attachment handling was real
- OCR used real cached OCR text
- Fresh PaddleOCR prediction was not performed
- Local Ollama classification and extraction were real
- Human review interaction was real
- Reviewer confirmation was explicit
- Classification feedback was stored locally
- Smartsheet was not called
- No external AI service was called

PHI handling:

- No message identifier was printed by the PHI-safe command
- No email subject was printed by the PHI-safe command
- No attachment path was printed by the PHI-safe command
- No filename was printed by the PHI-safe command
- No OCR text was printed by the PHI-safe command
- No extracted values were printed by the PHI-safe command
- No source_text was printed by the PHI-safe command
- No review evidence was printed by the PHI-safe command
- No feedback-storage payload was printed
- The final summary contained only counts, success, and status

Important limitation:

This was a real cached-OCR integration run, not a fresh OCR prediction.
The known document bytes matched an existing local OCR cache entry.

The existing PaddleOCR initialization behavior still created or loaded
local model objects before cached OCR text was reused.

The successful run confirms the current integration path:

Microsoft Graph
  -> attachment handling
  -> cached local OCR text
  -> real local Ollama
  -> structured processing
  -> explicit classification review
  -> local classification feedback storage
  -> PHI-safe command summary

Smartsheet submission remains disabled.

------------------------------------------------------------
CLASSIFICATION REVIEW WORDING STATUS
------------------------------------------------------------

The reviewer-facing menu wording was revised from:

Correct classification

to:

Revise classification

The change avoids implying that an alternate reviewer entry is
necessarily objectively correct. The underlying workflow remains
unchanged:

- Confirm classification keeps the predicted category and subtype
- Revise classification accepts reviewer-entered category and subtype
- Cancel submits no feedback

No extraction, validation, business-rule, review-output, fingerprint, or
feedback-storage behavior changed.

Affected test results:

- Classification review interaction: 12 passed, 0 failed
- Mailbox review session: 13 passed, 0 failed
- Mailbox review command: 8 passed, 0 failed

Combined result:

Passed: 33
Failed: 0

Test classification:

- Synthetic deterministic UI-boundary tests
- Synthetic deterministic coordinator tests
- Mock command-boundary tests

During these regression tests:

- Microsoft Graph was not called
- Attachment download was not called
- Document processing was not called
- OCR was not called
- Ollama was not called
- Smartsheet was not called
- No external integration was called

PHI handling:

- No patient documents were used
- No OCR text was displayed
- No source paths were displayed
- No extracted values were displayed
- No source_text was displayed
- No review evidence was displayed
- Only approved PHI-safe review metadata and status were displayed

Current limitations:

- The real integration used cached OCR rather than fresh OCR
- Only one real mailbox message and one document were processed
- The known document was used rather than a new document format
- No persistent review queue exists
- Processed Document objects remain in memory only
- Reviewer identity and authorization are not represented
- No interrupted-session resume or recovery exists
- Smartsheet submission is not enabled
- The model-reported confidence value is not deterministic proof of
  classification correctness
- The existing scripts/test_mailbox_processor.py remains PHI-unsafe for
  real documents because it prints paths, OCR text, and extracted values

Exact next starting point:

Run the complete end-of-day Git safety review. Confirm the classification
review wording change and this tracker update are the only intended
changes. Verify protected paths remain ignored, review the complete
noninteractive diff, confirm no PHI, OCR text, patient documents,
identifying paths, credentials, secrets, tokens, cache files, model
files, or temporary scripts are present, then stage only reviewed safe
files, commit, push, verify branch synchronization, and confirm a clean
working tree.


------------------------------------------------------------
FRESH OCR MAILBOX AND MAILBOX HANDLING STATUS
------------------------------------------------------------

A real Microsoft Graph-backed mailbox review run completed successfully
using a new document that did not have an existing OCR cache entry.

Execution command:

python -m src.ui.mailbox_review_command --top 1

Verified real processing path:

- Microsoft Graph mailbox access was real
- One unread inbox message was selected
- Attachment handling was real
- No OCR cache entry was found for the document
- A fresh local PaddleOCR prediction was performed
- OCR text was stored in the secured local OCR cache
- Local Ollama classification and extraction were real
- Explicit human classification review was performed
- The reviewer confirmed the predicted classification
- Classification feedback was stored locally
- Smartsheet was not called
- No external AI service was called

PHI-safe command result:

- message_count: 1
- document_count: 1
- submitted_count: 1
- cancelled_count: 0
- failed_count: 0
- success: True
- status: completed

This closes the previously outstanding fresh-OCR mailbox integration
gap. The earlier real mailbox test used cached OCR; this later run
verified the fresh local PaddleOCR path.

Mailbox unread-state diagnostic:

Microsoft Graph initially reported the visible test message as read even
though the Outlook client displayed it as unread. After explicitly
marking the message read and then unread in Outlook, Graph reported one
unread inbox message and the mailbox command processed it successfully.

This confirms that the unread-message Graph query itself behaved as
implemented. It also demonstrates that Read/Unread state is not a
sufficient long-term processing-state or idempotency mechanism.

Mailbox handling was then improved so successfully inspected messages
without a processable document do not remain indefinitely in the unread
queue.

New mailbox behavior:

- A message with no attachments is marked read after successful
  inspection.
- A message containing only unsupported attachments is marked read
  after successful inspection.
- A message whose attachment service returns no downloadable files is
  marked read after successful inspection.
- A message with a successfully processed supported document is marked
  read.
- Attachment-download failures remain unread for retry.
- Supported-document processing failures remain unread for retry.
- Mixed document success and processing failure remains unread for
  retry.
- Missing message IDs are not marked read.
- Mark-read failures remain explicit failures.
- Raw attachment-download exception details are not propagated.
- Raw document-processing exception details are not propagated.
- Identifying filenames are not embedded in mailbox-processing error
  strings.

MessageProcessingResult.succeeded continues to represent successful
document processing and is not redefined to mean that a message was
merely inspected or intentionally skipped.

Files changed:

- src/graph/mailbox_processor.py
- tests/test_mailbox_handling.py
- update_project_tracker.py

Focused mailbox-handling test:

Passed: 9
Failed: 0

Real or mock:

Mock mailbox-boundary test

Affected regression tests:

- Mailbox review orchestration: 11 passed, 0 failed
- Mailbox review session: 13 passed, 0 failed
- Mailbox review command: 8 passed, 0 failed

Combined tested result:

Passed: 41
Failed: 0

Test classification:

- Mailbox handling: mock boundary test
- Mailbox review orchestration: mock
- Mailbox review session: synthetic deterministic
- Mailbox review command: mock command-boundary
- Fresh mailbox integration: real Microsoft Graph
- Fresh OCR: real local PaddleOCR
- Classification and extraction: real local Ollama
- Human review: real explicit confirmation
- Classification feedback storage: real local storage
- Smartsheet: not called
- External AI: not called

PHI handling:

- No patient document was committed
- No OCR text was added to the tracker
- No patient identifiers were added to the tracker
- No source_text was added to the tracker
- No identifying document path or filename was added to the tracker
- No feedback payload was printed
- Mailbox command output contained only approved review metadata and
  PHI-safe counts, success, and status
- New mailbox error strings suppress raw exception details and
  identifying filenames
- data/incoming remains local-only
- data/ocr_cache remains local-only
- data/classification_feedback remains local-only

Current limitations:

- Read/Unread state is still the current mailbox selection mechanism
- A durable explicit processing-state or idempotency mechanism is not
  yet implemented
- Reviewer identity and authorization are not represented
- No interrupted-review resume or persistent review queue exists
- Smartsheet review submission is not enabled
- Final operational document taxonomy is still pending the confirmed
  list of possible document types
- A model-reported confidence value is not deterministic proof of
  correctness

Exact next starting point:

Complete Git safety review for the mailbox-handling implementation and
tracker update. Verify protected local data paths remain ignored, review
the complete noninteractive diff, confirm no PHI, OCR text, patient
documents, identifying paths, credentials, secrets, tokens, cache files,
model files, or temporary scripts are present, then stage only the
reviewed safe files, commit, push, verify synchronization, and confirm a
clean working tree.

After this change is safely committed, design the smallest durable
mailbox processing-state and idempotency boundary so production
processing does not rely solely on Outlook Read/Unread state.


------------------------------------------------------------
DURABLE MAILBOX MESSAGE IDEMPOTENCY STATUS
------------------------------------------------------------

Mailbox ingestion now has durable local message-level handled state.

Purpose:

Prevent a successfully handled Graph message from repeating attachment
download, document processing, OCR, Ollama processing, and human review
if the same message later appears unread again.

Implementation:

- Graph message IDs are normalized locally.
- Raw Graph message IDs are never persisted.
- SHA-256 of the message ID is used as the handled-marker filename.
- Marker content is the constant text handled.
- Durable state is stored under:
  data/mailbox_processing_state/
- The state directory is ignored by Git.
- MailboxProcessor checks durable state before attachment download.
- Already-handled messages skip attachment and document processing.
- Already-handled messages retry only the Graph mark-read operation.
- Successfully handled messages are recorded before mark-read.
- A mark-read failure preserves the handled marker so expensive
  document processing is not repeated.
- Attachment-download failures are not recorded as handled.
- Document-processing failures are not recorded as handled.
- Mixed document success and failure is not recorded as handled.
- State-check failures block processing.
- State-storage failures leave messages unread.
- Missing or invalid message IDs are not recorded.

State result contract:

- handled
- stored
- duplicate
- success
- status

The contract excludes:

- Graph message IDs
- message subjects
- senders
- email content
- attachment names
- local document paths
- OCR text
- extracted values
- source_text
- patient identifiers

Files changed:

- .gitignore
- src/graph/mailbox_processor.py
- src/services/mailbox_processing_state_service.py
- tests/test_mailbox_handling.py
- tests/test_mailbox_processing_state_service.py
- tests/test_mailbox_persistent_idempotency.py
- update_project_tracker.py

Focused processing-state tests:

Passed: 9
Failed: 0

Test type:

Synthetic deterministic local-state

Mailbox handling regression:

Passed: 12
Failed: 0

Test type:

Mock mailbox boundary

Mailbox review orchestration regression:

Passed: 11
Failed: 0

Test type:

Mock orchestration

Mailbox review session regression:

Passed: 13
Failed: 0

Test type:

Synthetic deterministic coordinator

Mailbox review command regression:

Passed: 8
Failed: 0

Test type:

Mock command boundary

Persistent state across separate MailboxProcessor instances:

Passed: 1
Failed: 0

Test type:

Synthetic deterministic local-state integration

Combined automated result:

Passed: 54
Failed: 0

Real external verification:

A previously processed Graph message was marked unread again and the
mailbox review command was rerun.

Observed second-run result:

- Messages: 1
- Documents: 0
- Submitted: 0
- Cancelled: 0
- Failed: 0
- Success: True
- Status: no_documents

This confirmed that the real Graph message was recognized as already
handled and did not re-enter document review.

Real or mock:

- Microsoft Graph: Real
- Durable mailbox state: Real local state
- Attachment processing on repeat run: Skipped
- OCR on repeat run: Not rerun
- Ollama on repeat run: Not rerun
- Human review on repeat run: Not rerun
- Smartsheet: Not called

PHI handling:

- No raw Graph message ID is stored in durable state.
- Durable filenames contain only SHA-256-derived identifiers.
- Marker content contains only the constant handled status.
- No email body, subject, sender, attachment name, document path,
  OCR text, extracted value, or source_text is stored in processing
  state.
- Tests use synthetic identifiers.
- Console verification used only PHI-safe counts, booleans, and status.
- data/mailbox_processing_state/ is ignored by Git.

Limitations:

- State is message-level, not document-level across different emails.
- Identical attachment bytes arriving in a different Graph message are
  treated as a new mailbox event.
- Concurrent processing claims are not implemented.
- Interrupted-run lease recovery is not implemented.
- Marker cleanup and retention policy is not yet defined.
- State is local to this installation.
- The current durable marker represents successful mailbox ingestion,
  not a persistent end-to-end human-review queue.

Exact next starting point:

Complete Git safety review, stage only the reviewed mailbox-idempotency
files and tracker update, commit, push, verify branch synchronization,
and confirm a clean worktree.

Atomic claims and interrupted-run recovery remain future production
hardening work and are not required before continuing higher-value
workflow development.


------------------------------------------------------------
REVIEWED SMARTSHEET WRITE BOUNDARY STATUS
------------------------------------------------------------

A controlled reviewed-write boundary is now implemented between the
existing logical Smartsheet mapping/destination-validation services and
the existing Smartsheet client.

Purpose:

Prevent unreviewed, unmapped, stale, mismatched, or invalid data from
reaching the Smartsheet row-write client.

Implementation:

- SmartsheetReviewedWriteService accepts only:
  - SmartsheetRowMappingResult
  - SmartsheetDestinationValidationResult
- The service refuses writes when the logical mapping is not ready.
- The service refuses writes when destination validation is not ready.
- The mapping column names must exactly match the validated destination
  column names.
- Every destination column ID is rechecked immediately before write.
- Boolean, zero, negative, missing, and invalid column IDs are rejected.
- One Smartsheet row is created only after all boundaries pass.
- The service invokes the existing SmartsheetClient.add_row method.
- The write-result contract contains only:
  - written
  - column_count
  - success
  - status
- The write result excludes:
  - mapped values
  - Smartsheet cell payloads
  - row payloads
  - row IDs
  - OCR text
  - source_text
  - filenames
  - local document paths
  - patient data

The existing logical mapping boundary continues to prohibit source_text,
raw OCR text, file paths, and processing metrics from Smartsheet
mapping.

The existing destination validator continues to resolve approved logical
column names to real positive Smartsheet column IDs before writing.

Files added:

- src/services/smartsheet_reviewed_write_service.py
- tests/test_smartsheet_reviewed_write_service.py
- tests/test_smartsheet_reviewed_write_integration.py

Focused reviewed-write tests:

Passed: 13
Failed: 0

Test type:

Mock Smartsheet write-boundary test

Existing document-to-Smartsheet mapping regression:

Passed: 9
Failed: 0

Test type:

Synthetic deterministic

Existing Smartsheet destination validation regression:

Passed: 12
Failed: 0

Test type:

Synthetic deterministic

Reviewed-write integration test:

Passed: 4
Failed: 0

Test type:

Synthetic deterministic integration with mocked Smartsheet client

Combined automated result:

Passed: 38
Failed: 0

Real Smartsheet destination-schema validation:

- Real Smartsheet API called
- Read-only sheet schema retrieval succeeded
- Rows read: 0
- Rows written: 0
- Required reviewed-write logical columns were present
- Missing mapped columns: 0
- Invalid column IDs: 0
- No document or row values were accessed

Real synthetic Smartsheet write:

- Real Smartsheet API called
- Mapping ready: True
- Destination ready: True
- Write ready: True
- Mapped columns: 12
- Missing columns: 0
- Invalid columns: 0
- Write attempted: True
- Write success: True
- Rows written: 1
- Column count: 12
- Status: written
- Microsoft Graph was not called
- PaddleOCR was not called
- Ollama was not called
- No patient data was used
- Only synthetic test values were written
- The Smartsheet row payload was not printed or logged

PHI handling:

- No real patient information was used in the external-write test.
- No OCR text was sent to or printed for Smartsheet.
- No source_text was mapped or written.
- No source document path or filename was mapped or written.
- No Smartsheet payload was printed or logged.
- No Smartsheet write result contains mapped values.
- .env remained Git-ignored.
- Smartsheet credentials were not printed.
- The configured destination sheet was validated using column titles and
  IDs only before the first write.

Limitations:

- The current reviewed-write service is not yet wired into the mailbox
  human-review session automatically.
- Classification confirmation alone does not authorize a Smartsheet
  write.
- The service requires an already-approved complete ReviewOutput mapping.
- A production policy/configuration for all document types is not yet
  centralized.
- The current mapping is focused on the existing authorization workflow.
- Service-line records are not written as independent Smartsheet rows.
- No real patient-bearing Smartsheet write has been performed.
- The synthetic integration-test row may remain in the test destination
  until intentionally removed.
- Real write retry/idempotency semantics for Smartsheet are not yet
  implemented.


------------------------------------------------------------
SMARTSHEET SHEET ROUTING CORRECTION
------------------------------------------------------------

The project tracker and reviewed AI-output destination now use separate
Smartsheet configuration boundaries.

Cause found during real integration testing:

SMARTSHEET_SHEET_ID had temporarily been changed from the project-tracker
sheet to the new AI reviewed-output destination. Existing tracker
services correctly continued using SMARTSHEET_SHEET_ID, which caused
update_project_tracker.py to search the AI destination for project task
names.

Correction:

- SMARTSHEET_SHEET_ID again identifies the project-tracker sheet.
- SMARTSHEET_PROJECT_TRACKER_SHEET_ID records the explicit local
  project-tracker destination.
- SMARTSHEET_AI_DESTINATION_SHEET_ID identifies the reviewed AI-output
  destination.
- SmartsheetClient now accepts a sheet-ID environment-variable name.
- Existing SmartsheetClient() callers preserve their original
  SMARTSHEET_SHEET_ID behavior.
- SmartsheetReviewedWriteService explicitly selects
  SMARTSHEET_AI_DESTINATION_SHEET_ID when no client is injected.
- No duplicate Smartsheet client or tracker service was created.

Files changed or added:

- src/clients/smartsheet_client.py
- src/services/smartsheet_reviewed_write_service.py
- tests/test_smartsheet_reviewed_write_service.py
- tests/test_smartsheet_reviewed_write_integration.py
- tests/test_smartsheet_sheet_routing.py
- update_project_tracker.py

Routing-focused tests:

Passed: 5
Failed: 0
Real or mock: Synthetic deterministic/mock
External integration: Not called

Affected reviewed-write, mapping, and destination regressions:

Passed: 38
Failed: 0
Real or mock: Synthetic deterministic/mock

Combined automated Smartsheet result:

Passed: 43
Failed: 0

Real external routing verification:

- Project-tracker connection succeeded.
- Project-tracker expected schema was present.
- AI-destination connection succeeded.
- AI-destination expected schema was present.
- Routing verification was read-only.
- Rows read: 0
- Rows written: 0
- Only column metadata was inspected.

Prior real synthetic Smartsheet write:

- Real Smartsheet API called.
- Mapping ready: True.
- Destination ready: True.
- Write ready: True.
- One synthetic row was written successfully.
- No patient data was used.
- Microsoft Graph was not called.
- PaddleOCR was not called.
- Ollama was not called.
- The row payload was not printed or logged.

PHI handling:

- No patient information was used in routing tests.
- No Smartsheet row values were read during routing verification.
- No OCR text or source_text was printed or logged.
- No patient document path or filename was printed or written.
- Smartsheet credentials and .env values were not printed.
- .env remained Git-ignored.
- Only PHI-safe schema metadata was inspected.

Limitations:

- Classification confirmation alone does not authorize a Smartsheet
  write.
- Reviewed writing is not yet automatically connected to the complete
  mailbox human-review workflow.
- Production mapping policy for all document types is not yet
  centralized.
- Service-line records are not yet written as independent rows.
- No real patient-bearing Smartsheet write has been performed.
- Smartsheet write retry/idempotency semantics are not yet implemented.

Exact next starting point after this commit:

Design the explicit workflow connection from a completely reviewed
ReviewOutput through logical mapping, destination validation, and
controlled Smartsheet writing.

Human review must remain the authority that decides whether automation
may proceed. Classification confirmation alone must not authorize the
write.

Exact next starting point:

Complete Git safety review and commit the reviewed Smartsheet write
boundary.

After that commit, design the explicit workflow connection that allows a
complete reviewed ReviewOutput to proceed through mapping, destination
validation, and Smartsheet writing.

Do not authorize Smartsheet writing merely because classification was
confirmed. The complete review/write-readiness boundary must remain
separate.


------------------------------------------------------------
COMPLETE REVIEW TO SMARTSHEET WORKFLOW STATUS
------------------------------------------------------------

Implemented and tested the explicit human-review authority boundary
required before reviewed AI output can proceed to Smartsheet.

Architecture completed:

ReviewOutput
-> explicit complete-review approval
-> logical Smartsheet mapping
-> destination validation
-> controlled reviewed write

Classification confirmation remains a separate feedback workflow and
cannot authorize Smartsheet writing.

Implementation:

- CompleteReviewApprovalService requires an explicit complete-review
  decision.
- Approval and rejection are separate explicit reviewer decisions.
- A ReviewOutput with unresolved human-review requirements cannot be
  approved for downstream automation.
- CompleteReviewApprovalResult contains only:
  - approved
  - success
  - status
- CompleteReviewApprovalInteraction provides a separate local final
  approval interaction.
- The interaction displays only PHI-safe workflow metadata:
  - field count
  - service-line count
  - whether review remains required
  - review-reason count
  - approval status
- Field values, service-line values, source_text, OCR text, patient data,
  classification reason, filenames, and paths are not displayed.
- MailboxCompleteReviewSessionService coordinates complete-review
  decisions separately from the existing classification-feedback
  mailbox session.
- SmartsheetReviewSubmissionService requires a valid successful
  CompleteReviewApprovalResult before mapping, destination validation,
  or controlled writing can proceed.
- A successful classification-feedback result cannot satisfy the
  complete-review approval contract.
- CompleteReviewSmartsheetWorkflowService coordinates:
  - explicit complete-review interaction
  - complete-review approval result
  - approval-gated Smartsheet submission
- Rejection, cancellation, unresolved review, invalid review output,
  mapping failure, and destination failure prevent writing.
- Existing SmartsheetReviewedWriteService remains the final narrow
  mapped-and-validated write boundary.

Files added:

- src/services/complete_review_approval_service.py
- src/services/complete_review_smartsheet_workflow_service.py
- src/services/mailbox_complete_review_session_service.py
- src/services/smartsheet_review_submission_service.py
- src/ui/complete_review_approval_interaction.py
- tests/test_classification_confirmation_smartsheet_gate.py
- tests/test_complete_review_approval_interaction.py
- tests/test_complete_review_approval_service.py
- tests/test_complete_review_smartsheet_workflow_service.py
- tests/test_mailbox_complete_review_session_service.py
- tests/test_smartsheet_review_submission_service.py

Focused and affected automated tests:

Passed: 120
Failed: 0

Test types:

- Synthetic deterministic
- Synthetic deterministic UI-boundary
- Synthetic deterministic coordinator
- Mock Smartsheet write-boundary
- Synthetic deterministic integration with mocked Smartsheet client
- Synthetic deterministic/mock coordinator

External systems:

- Real Smartsheet write: Not called
- Microsoft Graph: Not called
- PaddleOCR: Not called
- Ollama: Not called
- Classification feedback storage: Not called during the new safety-gate
  test

Safety behavior proven:

- Explicit complete-review approval is required before submission.
- Classification confirmation alone cannot authorize writing.
- Classification success=True cannot authorize writing.
- Classification status text "approved" cannot impersonate complete
  approval.
- Rejected complete reviews do not reach Smartsheet submission.
- Cancelled complete reviews do not reach Smartsheet submission.
- Unresolved human-review requirements do not reach submission.
- Invalid review output does not reach submission.
- Mapping and destination readiness remain independent required gates.
- Review output is not re-extracted, reinterpreted, or mutated by the
  approval workflow.

PHI handling:

- Automated tests used synthetic values only.
- No patient documents were used.
- No OCR text was printed or transmitted.
- No field or service-line source_text was printed or transmitted.
- No patient-bearing local path or filename was printed.
- No Smartsheet row payload was printed.
- PHI-safe workflow result contracts contain only booleans, counts, and
  statuses where applicable.
- No real patient-bearing Smartsheet write was performed.
- .env and protected local data locations remain outside the intended
  commit.

Limitations:

- The complete-review workflow is not yet connected to the live mailbox
  command/orchestration path.
- Available Smartsheet columns and mapping policies still need an
  explicit production orchestration source.
- Production mapping policy for all document types is not centralized.
- Service-line records are not yet written as independent Smartsheet
  rows.
- Real Smartsheet write retry/idempotency semantics remain future work.
- No real patient-bearing end-to-end write has been performed.

Exact next starting point after this commit:

Inspect the existing mailbox command/orchestration callers and design the
smallest explicit connection that invokes the separate complete-review
workflow after document processing while preserving classification
feedback as a separate step.

Do not allow classification confirmation to authorize Smartsheet
writing. Preserve human complete-review approval as the authority that
decides whether automation may proceed.



------------------------------------------------------------
FULL MAILBOX REVIEW / SMARTSHEET ORCHESTRATION - 2026-08-07
------------------------------------------------------------

Feature completed:

Added an explicit opt-in mailbox workflow that preserves
classification review as a separate step and requires separate
complete-review approval before any Smartsheet write may proceed.

Implemented production boundaries:

- Mailbox complete-review Smartsheet coordinator
- PHI-safe Smartsheet destination schema reader
- Explicit document-type Smartsheet mapping-policy registry
- Smartsheet reviewed-write configuration resolver
- Full mailbox review orchestration service
- Separate explicit full mailbox review command

Files changed:

src/services/mailbox_complete_review_smartsheet_service.py
src/services/smartsheet_destination_schema_service.py
src/services/smartsheet_mapping_policy_service.py
src/services/smartsheet_review_configuration_service.py
src/services/mailbox_full_review_orchestration_service.py
src/ui/mailbox_full_review_command.py
tests/test_mailbox_complete_review_smartsheet_service.py
tests/test_smartsheet_destination_schema_service.py
tests/test_smartsheet_mapping_policy_service.py
tests/test_smartsheet_review_configuration_service.py
tests/test_mailbox_full_review_orchestration_service.py
tests/test_mailbox_full_review_command.py

Focused tests:

Mailbox complete-review Smartsheet boundary:
13 passed, 0 failed.
Synthetic deterministic/mock.

Smartsheet destination schema reader:
10 passed, 0 failed.
Synthetic deterministic/mock.

Smartsheet mapping policy registry:
10 passed, 0 failed.
Synthetic deterministic.

Smartsheet review configuration resolver:
6 passed, 0 failed.
Synthetic deterministic/mock.

Full mailbox review orchestration:
10 passed, 0 failed.
Mock.

Full mailbox review command:
8 passed, 0 failed.
Mock.

Affected regression:

196 passed, 0 failed.

Test classification:

Synthetic deterministic and mock.

No real Smartsheet write occurred during the affected regression.
Microsoft Graph was not called during the affected regression.
OCR was not called during the affected regression.
Ollama was not called during the affected regression.

PHI handling:

Only synthetic values, counts, booleans, statuses, mapping metadata,
and destination column metadata were used or displayed.

No OCR text, source_text, patient data, filenames, identifying paths,
Smartsheet payload values, row IDs, credentials, or tokens were
printed or committed by these tests.

Safety behavior:

Classification confirmation remains separate from complete-review
approval.

Classification confirmation cannot authorize Smartsheet writing.

Complete-review rejection or cancellation prevents writing.

Missing or unconfigured mapping policy fails closed.

Missing destination columns fail closed.

The existing classification-only mailbox command remains separate.

Limitations:

Production Smartsheet mapping policies are intentionally not
hard-coded yet.

No payer-, service-code-, modifier-, subtype-, or fixture-specific
mapping policy was inferred.

The full mailbox command therefore cannot perform a production write
until explicitly approved production mapping policies are supplied.

Real Smartsheet retry/idempotency remains future work.

Independent service-line row writing remains future work.

No real patient-bearing end-to-end Smartsheet write was performed.

Exact next starting point:

Define and approve the production SmartsheetColumnPolicy mappings for
each supported document type, then connect those approved policies to
the SmartsheetMappingPolicyService used by the explicit full mailbox
review command.

Do not invent payer-, service-code-, modifier-, or document-specific
mapping decisions.

Do not allow classification confirmation to authorize Smartsheet
writing.

Preserve complete-review approval as the authority that decides
whether automation may proceed.

------------------------------------------------------------
SMARTSHEET DEMO SCHEMA AND APPROVED AUTHORIZATION POLICY - 2026-08-07
------------------------------------------------------------

Feature:
Prepared the reviewed Smartsheet path for the live authorization demo.

Files changed:

- src/services/smartsheet_destination_schema_service.py
- tests/test_smartsheet_destination_schema_service.py
- src/services/smartsheet_mapping_policy_service.py
- tests/test_smartsheet_mapping_policy_service.py
- src/services/smartsheet_review_configuration_service.py
- tests/test_smartsheet_review_configuration_service.py

Changes:

- Real Smartsheet SDK column collections are accepted as iterables instead
  of requiring a plain Python list.
- Destination column capitalization is preserved in mapping policies.
- Document-type and source-field keys remain normalized.
- Explicitly approved authorization mappings are registered:
  authorization_status -> Authorization Status
  service_codes -> Service Codes
  authorized_units -> Authorized Units
  start_date -> Start Date
  end_date -> End Date
- No payer-, service-code-, modifier-, or document-specific business
  conclusions were added.
- Complete human-review approval remains required before writing.

Focused tests:

- Smartsheet destination schema reader: 11 passed, 0 failed
- Smartsheet mapping policy registry: 10 passed, 0 failed
- Smartsheet review configuration resolver: 7 passed, 0 failed

Affected regression execution:

- 8 affected regression scripts completed successfully
- Script failures: 0
- Final full-mailbox orchestration group: 10 passed, 0 failed
- Synthetic deterministic/mock only

Real external read-only validation:

- AI destination schema read succeeded
- Destination column count: 13
- Approved authorization policy count: 5
- Configuration resolution status: ready
- Smartsheet rows read: 0
- Smartsheet rows written: 0

PHI handling:

- Only column metadata, field names, counts, booleans, and statuses were
  displayed.
- No OCR text, patient data, source_text, filenames, document paths,
  row values, or Smartsheet payload values were printed or committed.

Limitations:

- No real authorization document has yet been processed through this
  newly approved configuration.
- No real Smartsheet row has been written during this work.
- Service-line rows remain review-output data and are not independently
  written as multiple Smartsheet rows.
- Human approval remains required before a reviewed result may write.

Exact next starting point:

Run the live boss demo from a new unread authorization-type mailbox
attachment through Graph, local PaddleOCR, local Ollama, deterministic
validation, business rules, classification review, complete human review,
and the approved AI-destination Smartsheet write. Keep PHI-bearing values,
OCR text, filenames, paths, source_text, and payload values out of
terminal/chat output.


------------------------------------------------------------
DEMO-ONLY CLASSIFICATION REVIEW BYPASS - 2026-08-07
------------------------------------------------------------

Feature:
Added an explicit demo-only option allowing the AI classification and
extraction result to proceed without classification confirmation.

Files changed:

- src/services/mailbox_full_review_orchestration_service.py
- src/ui/mailbox_full_review_command.py
- tests/test_mailbox_full_review_orchestration_service.py
- tests/test_mailbox_full_review_command.py

Behavior:

- Normal production behavior remains unchanged by default.
- --demo-skip-classification-review bypasses only the classification
  review/feedback interaction.
- The existing AI classification and extraction result is preserved.
- Deterministic validation and business rules remain active.
- Complete human-review approval remains mandatory before Smartsheet
  writing.
- Classification bypass does not itself grant write authority.
- Demo output remains PHI-safe.

Focused tests:

- Full mailbox orchestration: 11 passed, 0 failed
- Full mailbox review command: 9 passed, 0 failed
- Synthetic deterministic/mock only

Affected regressions:

- 5 affected regression scripts completed successfully
- Script failures: 0
- Final command group: 9 passed, 0 failed
- Synthetic deterministic/mock only

External systems:

- Microsoft Graph: Not called
- Attachment download: Not called
- OCR: Not called
- Ollama: Not called
- Smartsheet external API: Not called
- Smartsheet rows written: 0

PHI handling:

- Only counts, booleans, statuses, and demo-mode metadata were displayed.
- No OCR text, patient data, extracted values, source_text, filenames,
  local document paths, Smartsheet payloads, or row values were printed
  or committed.

Limitations:

- Demo bypass has not yet been exercised against a fresh real mailbox
  authorization attachment.
- Final complete-review approval is intentionally still required before
  any real Smartsheet write.
- The bypass is for demonstration only and is not presented as trained
  production classification behavior.

Exact next starting point:

Run the live boss demo using a new unread authorization-type attachment
with --demo-skip-classification-review. Allow local PaddleOCR and Ollama
to classify and extract independently, preserve deterministic validation
and business rules, and stop at the final complete-review decision before
any Smartsheet write. Keep PHI-bearing values, OCR text, filenames, paths,
source_text, and Smartsheet payload values out of terminal/chat output.


------------------------------------------------------------
AUTHORIZATION RENEWAL SMARTSHEET POLICY - 2026-08-07
------------------------------------------------------------

Feature:
Extended the explicitly approved authorization Smartsheet mapping policy
to authorization_renewal after a real demo document was independently
classified by Ollama as authorization_renewal.

Files changed:

- src/services/smartsheet_review_configuration_service.py
- tests/test_smartsheet_review_configuration_service.py

Approved mapping for authorization_renewal:

- authorization_status -> Authorization Status
- service_codes -> Service Codes
- authorized_units -> Authorized Units
- start_date -> Start Date
- end_date -> End Date

Behavior:

- authorization and authorization_renewal now use the same explicitly
  approved five-column mapping.
- No payer-, code-, modifier-, quantity-, or document-specific business
  meaning was inferred.
- Deterministic validation and business rules remain unchanged.
- Complete human-review approval remains mandatory before Smartsheet
  writing.
- Classification alone still cannot authorize a write.

Focused test:

- Smartsheet review configuration resolver: 8 passed, 0 failed
- Synthetic deterministic/mock

Affected regressions:

- 5 affected regression scripts completed successfully
- Script failures: 0
- Final full mailbox command group: 9 passed, 0 failed
- Synthetic deterministic/mock only

Real external validation:

- authorization_renewal configuration resolved successfully against the
  real AI destination Smartsheet schema.
- Approved policy count: 5
- Destination column count: 13
- Read-only metadata validation
- Smartsheet rows written: 0

Real demo diagnostic:

- One real document was processed.
- Ollama document type: authorization_renewal
- Review output present: True
- Human review required: True
- Initial Smartsheet configuration failed safely with
  policy_not_configured before this approval was added.
- Cached OCR was used during the diagnostic run.

PHI handling:

- No OCR text, patient data, extracted values, source_text, filenames,
  document paths, Smartsheet payloads, or row values were displayed or
  committed.
- Diagnostics were limited to document type, counts, booleans, statuses,
  and configuration metadata.

Limitations:

- The newly approved authorization_renewal mapping has not yet completed
  a real Smartsheet write.
- The real document still requires final complete-review approval before
  writing.
- Cached OCR diagnostic execution is not described as fresh OCR.

Exact next starting point:

Rerun the live boss demo using the existing demo-only classification
review bypass. Allow the real document to proceed through the approved
authorization_renewal mapping, deterministic validation, business rules,
and final complete-review approval. Write to the AI destination
Smartsheet only after explicit complete-review approval. Keep PHI-bearing
values, OCR text, filenames, paths, source_text, and Smartsheet payload
values out of terminal/chat output.


------------------------------------------------------------
COMPLETE REVIEW RECOMMENDATION APPROVAL GATE - 2026-08-07
------------------------------------------------------------

Feature:
Corrected the complete-review approval and Smartsheet submission gates so
that an explicitly approved Human Review Recommended result may proceed,
while Human Review Required remains blocked.

Files changed:

- src/services/complete_review_approval_service.py
- src/services/smartsheet_review_row_mapping_service.py
- src/services/smartsheet_review_submission_service.py
- tests/test_complete_review_approval_service.py
- tests/test_smartsheet_review_row_mapping.py
- tests/test_smartsheet_review_submission_service.py

Behavior:

- Human Review Recommended may proceed only after explicit complete-review
  approval.
- Human Review Required remains blocked.
- Automatic mapping without explicit complete-review approval remains
  blocked when needs_human_review is true.
- Existing review metadata is preserved.
- Classification confirmation remains insufficient write authority.
- No deterministic validation or business-rule conclusions were weakened.

Focused tests:

- Complete review approval service: 10 passed, 0 failed
- Smartsheet review row mapping: 14 passed, 0 failed
- Approval-gated Smartsheet submission: 11 passed, 0 failed
- Synthetic deterministic/mock only

Affected regressions:

- Complete review approval interaction: 8 passed, 0 failed
- Complete review Smartsheet workflow: 8 passed, 0 failed
- Smartsheet review mapping integration: 9 passed, 0 failed
- Smartsheet reviewed write integration: 4 passed, 0 failed
- Mailbox complete review Smartsheet service: 13 passed, 0 failed
- Mailbox full review orchestration: 11 passed, 0 failed
- Mailbox full review command: 9 passed, 0 failed

Real demo finding:

- Real local document classified as authorization_renewal.
- Classification confidence: 0.90.
- Minimum field confidence: 0.95.
- Review status: Human Review Recommended.
- Review reason count: 7.
- Explicit approval was previously blocked by review_still_required.
- No Smartsheet row was written during the failed demo attempt.

PHI handling:

- No OCR text, patient data, extracted values, filenames, paths,
  source_text, or Smartsheet payload values were printed or committed.
- Diagnostics were limited to counts, confidence values, statuses,
  document classification labels, and booleans.

Limitations:

- The corrected recommended-review approval path has not yet completed a
  real Smartsheet write.
- Required-review cases remain intentionally blocked.
- Real local diagnostic reused cached OCR text.

Exact next starting point:

Retry the same real boss demo after resetting only the durable handled
marker for the unread demo message. Allow the authorization_renewal
document to proceed through final complete-review approval. If the result
remains Human Review Recommended and the reviewer explicitly approves it,
verify that one row is written to the approved AI-destination Smartsheet.
Keep all PHI-bearing values and payload contents out of terminal/chat
output.


------------------------------------------------------------
REAL BOSS DEMO SMARTSHEET WRITE SUCCESS - 2026-08-07
------------------------------------------------------------

Feature:
Completed the real boss-demo workflow through one successful reviewed
Smartsheet row write.

Real external integration result:

- Messages processed: 1
- Documents processed: 1
- Demo classification review skipped: true
- Final complete-review approval: approved
- Approved documents: 1
- Smartsheet rows written: 1
- Rejected documents: 0
- Failed documents: 0
- Workflow success: true
- Workflow status: completed

Review state:

- Fields present: 19
- Service lines present: 1
- Review reason count: 7
- Review was Human Review Recommended.
- Explicit complete-review approval authorized the reviewed submission.
- Human Review Required behavior remains blocked by deterministic tests.

Test classification:

- Real Microsoft Graph mailbox integration
- Real attachment processing
- Real local OCR/Ollama workflow
- Real complete-review interaction
- Real external Smartsheet write
- Demo-only classification-review bypass enabled

PHI handling:

- No patient data, OCR text, extracted values, filenames, local paths,
  source_text, message identifiers, or Smartsheet payload values were
  copied into chat or tracker output.
- Only counts, booleans, confidence/review metadata, and workflow statuses
  were reported.

Limitations:

- The live run used the latest supported local demo attachment and may
  reuse locally cached OCR text when the OCR cache is available.
- The demo bypass skips classification review only.
- Production automation still requires the existing explicit mappings,
  validation, business-rule, review, and approval boundaries.

Exact next starting point:

Preserve this successful boss-demo baseline. Next development should start
from the clean synchronized repository and should not broaden Smartsheet
mappings or bypass Human Review Required without a separately confirmed
business requirement.


------------------------------------------------------------
ENHANCED AUTHORIZATION DEMO FIELD MAPPING - 2026-08-10
------------------------------------------------------------

Feature:

Expanded the approved authorization and authorization-renewal review
mapping for the enhanced boss demo while preserving deterministic
validation, explicit mapping policy, human-review authority, and PHI-safe
diagnostics.

Implementation:

- Authorization Status now represents only an actual authorization
  decision or supported authorization state.
- Request wording is not treated as an authorization decision.
- Blended status text such as Approved Requested is deterministically
  rejected rather than written as a final status.
- Authorization status must retain direct source evidence.
- Added hours to the structured Ollama extraction contract.
- Added days_per_week to the structured Ollama extraction contract.
- Hours and days_per_week may be extracted only from direct document
  evidence.
- Hours and days_per_week must not be derived from units, visits,
  sessions, service codes, date ranges, or arithmetic.
- SmartsheetColumnPolicy now supports an explicitly approved optional
  confidence destination column.
- Review-field confidence is mapped directly from the existing
  ReviewField confidence value.
- Low confidence is preserved and is not increased to satisfy a
  threshold.
- source_text is still not mapped to Smartsheet.
- DOB remains unmapped.
- Authorization and authorization_renewal use the same explicitly
  approved mapping policy.

Approved value mappings:

- authorization_status -> Authorization Status
- authorization_number -> Authorization #
- service_codes -> Service Codes
- diagnosis_code -> Diagnosis Codes
- start_date -> Start Date
- end_date -> End Date
- authorized_units -> Authorized Units
- hours -> Hours
- days_per_week -> Days Per Week

Approved confidence mappings:

- authorization_number -> Authorization # Conf.
- service_codes -> Service Codes Conf.
- diagnosis_code -> Diagnosis Codes Conf.
- authorized_units -> Authorized Units Conf.
- hours -> Hours Conf.
- days_per_week -> Days Per Week Conf.

Files changed:

- src/ai/llm/providers/ollama_provider.py
- src/models/smartsheet_mapping.py
- src/services/evidence_validation_service.py
- src/services/smartsheet_mapping_policy_service.py
- src/services/smartsheet_review_configuration_service.py
- src/services/smartsheet_review_row_mapping_service.py
- tests/test_evidence_validation_service.py
- tests/test_ollama_service_lines.py
- tests/test_smartsheet_review_configuration_service.py
- tests/test_smartsheet_review_row_mapping.py

Focused tests:

- Evidence validation: 29 passed, 0 failed
- Smartsheet mapping policy registry: 10 passed, 0 failed
- Smartsheet review configuration resolver: 8 passed, 0 failed
- Smartsheet review row mapping: 15 passed, 0 failed
- Ollama service-line schema and prompt: 17 passed, 0 failed

Focused total:

Passed: 79
Failed: 0

Affected regressions:

- Review output service: 8 passed, 0 failed
- Smartsheet destination schema reader: 11 passed, 0 failed
- Smartsheet reviewed write boundary: 13 passed, 0 failed
- Authorization quantity rules: 8 passed, 0 failed
- Authorization rule registry: 5 passed, 0 failed

Affected regression total:

Passed: 45
Failed: 0

Combined automated result:

Passed: 124
Failed: 0

Test classification:

- Synthetic deterministic
- Synthetic deterministic/mock
- Mock Smartsheet write-boundary
- No real OCR prediction was called
- No real Ollama generation was called
- Microsoft Graph was not called
- No real Smartsheet row write occurred

Real external read-only Smartsheet validation:

- Real AI-destination Smartsheet API called
- Configuration success: True
- Configuration status: ready
- Approved policy count: 9
- Destination column count: 23
- Rows read: 0
- Rows written: 0
- Only column metadata was accessed

PHI handling:

- No patient data was printed or copied into tests or tracker output.
- No OCR text was printed.
- No source_text was printed or written to Smartsheet.
- No patient document filename or identifying local path was printed.
- No Smartsheet row payload values were printed.
- No credentials, tokens, or .env contents were printed.
- Real Smartsheet verification used only PHI-safe schema metadata.
- Synthetic tests used synthetic values only.

Limitations:

- Hours and days_per_week have not yet been exercised through a real
  local Ollama extraction run.
- The enhanced nine-field policy has not yet performed a real reviewed
  Smartsheet row write.
- The original document is not yet attached to the Smartsheet row.
- Document renaming for the enhanced demo is not yet implemented.
- A non-interactive explicit complete-review approval command option is
  not yet implemented.
- Human Review Required remains intentionally blocked.
- Authorization quantity meaning remains governed by the existing
  deterministic business-rule and review boundaries.
- No payer-, service-code-, modifier-, or fixture-specific conclusion
  was introduced.

Exact next starting point:

Preserve this tested mapping baseline. Next inspect the existing full
mailbox review command, complete-review approval interaction, reviewed
Smartsheet write service, and Smartsheet client attachment capabilities.

Implement the smallest explicit non-interactive complete-review approval
option without weakening Human Review Required, then implement the
reviewed-row attachment boundary and deterministic document-renaming
behavior.

After focused and affected tests pass, run the real local
OCR/Ollama/review workflow and perform a real Smartsheet write only after
explicit complete-review approval. Keep patient data, OCR text,
filenames, paths, source_text, and Smartsheet payload values out of
terminal and chat output.


------------------------------------------------------------
NON-INTERACTIVE COMPLETE REVIEW AND SMARTSHEET ROW ATTACHMENT STATUS
------------------------------------------------------------

Implemented explicit non-interactive complete-review approval.

CLI flag:

--approve-complete-review

The flag does not bypass the complete-review approval service.

It sends the explicit approved decision through the same
CompleteReviewApprovalService boundary used by interactive approval.

Current safety behavior remains:

- Human Review Recommended may proceed only after explicit complete
  review approval.
- Human Review Required remains blocked.
- Classification confirmation does not authorize Smartsheet writing.
- Existing interactive approval remains available when the explicit
  flag is not supplied.

Implemented Smartsheet row attachment support.

Current flow:

approved complete review
  -> deterministic Smartsheet mapping
  -> destination validation
  -> create reviewed Smartsheet row
  -> prepare temporary locally renamed document copy
  -> attach temporary copy to the newly created row
  -> remove temporary copy

The original local document is not renamed or modified.

Temporary test naming convention:

LTHHC_AUTH_TEST_<12-character SHA-256 fingerprint prefix>.<extension>

This is a temporary test policy only. The final LTHHC document naming
convention has not yet been defined.

The existing local DocumentFingerprintService supplies the SHA-256
fingerprint. Patient data, OCR text, source_text, authorization values,
original filename, and original path are not used in the test filename.

Smartsheet Python SDK support was confirmed locally:

attach_file_to_row(sheet_id, row_id, _file)

The installed SDK accepts a string path or file stream for _file.

SmartsheetReviewedWriteResult now preserves only PHI-safe write state:

- written
- column_count
- attachment_written
- success
- status

It does not return the Smartsheet row ID, filename, local path,
fingerprint, mapped payload, OCR text, source_text, or patient data.

If row creation succeeds but attachment preparation or attachment fails,
the result reports the partial state safely. The already-created
Smartsheet row is not automatically deleted.

Files added:

- src/services/document_attachment_naming_service.py
- tests/test_document_attachment_naming_service.py

Files changed include:

- src/clients/smartsheet_client.py
- src/services/smartsheet_reviewed_write_service.py
- src/services/smartsheet_review_submission_service.py
- src/services/complete_review_smartsheet_workflow_service.py
- src/services/mailbox_complete_review_smartsheet_service.py
- src/services/mailbox_full_review_orchestration_service.py
- src/ui/complete_review_approval_interaction.py
- src/ui/mailbox_full_review_command.py
- related focused and regression tests

Non-interactive approval testing completed before attachment work:

Focused:
54 passed
0 failed

Affected regressions:
52 passed
0 failed

Total for that tested checkpoint:
106 passed
0 failed

All were synthetic deterministic or mock tests.
No external Smartsheet, Microsoft Graph, OCR, or Ollama calls occurred.

Attachment and forwarding tests completed:

Document attachment naming:
2 passed
0 failed
Synthetic deterministic local-file test

Smartsheet reviewed write:
17 passed
0 failed
Mock Smartsheet write-boundary test

Approval-gated Smartsheet submission:
11 passed
0 failed
Synthetic deterministic/mock

Complete-review Smartsheet workflow:
9 passed
0 failed
Synthetic deterministic/mock

Mailbox complete-review Smartsheet boundary:
14 passed
0 failed
Synthetic deterministic/mock

Full mailbox review orchestration:
12 passed
0 failed
Mock

Full mailbox review command:
10 passed
0 failed
Mock

PHI handling:

- Synthetic values and synthetic files only were used in these tests.
- No real patient document was read during attachment tests.
- No Smartsheet external API write occurred.
- No Microsoft Graph call occurred.
- No OCR call occurred.
- No Ollama call occurred.
- No mapped Smartsheet payload was printed.
- No real filename, local patient path, OCR text, source_text, or patient
  data was printed.

Limitations:

- The attachment filename convention is temporary.
- A real Smartsheet row attachment has not yet been performed.
- If row creation succeeds and attachment later fails, the row can
  remain in Smartsheet and the result reports the failure safely.
- Automatic rollback of a successfully created row is not implemented.
- Final production naming requirements remain unresolved.
- Real OCR/Ollama/review/Smartsheet execution still requires explicit
  complete-review approval before writing.

Exact next starting point:

Perform the real boss-demo preflight using the latest supported local
attachment already used for testing. Keep patient data, OCR text,
source_text, filenames, local paths, fingerprints, row IDs, and
Smartsheet payload values out of terminal and chat output. Run real local
OCR/Ollama/review, require explicit complete-review approval, then write
the reviewed row and attach the temporary renamed copy to Smartsheet.

------------------------------------------------------------
SMARTSHEET ATTACHMENT STREAM AND VISIBLE CONFIDENCE FIX - 2026-08-10
------------------------------------------------------------

Feature:

Corrected the Smartsheet attachment upload boundary and aligned the
Smartsheet-facing minimum-field-confidence value with the confidence
columns actually displayed on the destination row.

Attachment correction:

- Installed Smartsheet Python SDK version 4.3.0 was inspected locally.
- Its attach_file_to_row multipart operation places the supplied object
  directly into files["file"].
- The prior implementation supplied a local path string.
- The real external test showed that Smartsheet accepted that string as
  a generic file attachment rather than uploading the document bytes.
- The attachment appeared as a generic file named file and could not be
  opened after download.
- SmartsheetClient now opens the prepared temporary document in binary
  mode and passes the real file stream to the SDK.
- The stream retains the temporary renamed attachment filename.
- The stream is closed immediately after the SDK call returns.
- The existing temporary attachment preparation and cleanup boundary is
  preserved.
- The original local source document remains unchanged.

Smartsheet minimum confidence correction:

- Internal ReviewOutput.minimum_field_confidence remains unchanged.
- Human-review decisions continue to use the full populated extraction
  field set.
- Smartsheet AI Minimum Field Confidence now represents the minimum only
  among populated fields that have explicit displayed confidence
  destination columns in the approved mapping policy.
- Hidden internal extraction fields no longer create a Smartsheet
  minimum that cannot be reconciled with the confidence cells visible
  to a reviewer.
- Individual mapped confidence values remain unchanged.
- Confidence values below the 0.85 review threshold remain preserved
  without being increased or normalized upward.

Files changed:

- src/clients/smartsheet_client.py
- src/services/smartsheet_review_row_mapping_service.py
- tests/test_smartsheet_client.py
- tests/test_smartsheet_review_row_mapping.py

Focused tests:

- Smartsheet client attachment boundary: 1 passed, 0 failed
- Smartsheet review row mapping: 18 passed, 0 failed

Focused total:

Passed: 19
Failed: 0

Affected regressions:

- Smartsheet reviewed write boundary: 17 passed, 0 failed
- Approval-gated Smartsheet submission: 11 passed, 0 failed
- Complete-review Smartsheet workflow: 9 passed, 0 failed
- Mailbox complete-review Smartsheet boundary: 14 passed, 0 failed
- Full mailbox review orchestration: 12 passed, 0 failed
- Full mailbox review command: 10 passed, 0 failed
- Classification-to-Smartsheet safety gate: 3 passed, 0 failed

Affected regression total:

Passed: 76
Failed: 0

Combined automated result:

Passed: 95
Failed: 0

Test classification:

- Synthetic deterministic tests
- Mock Smartsheet SDK attachment boundary
- Mock reviewed-write and workflow boundaries
- No real Smartsheet external API call during the fix tests
- No Microsoft Graph call
- No PaddleOCR call
- No local Ollama request

PHI handling:

- Synthetic values and synthetic attachment bytes only were used.
- No real patient document was read by the attachment boundary test.
- No OCR text was printed.
- No source_text was printed.
- No patient values were printed.
- No Smartsheet payload was printed.
- No row ID was printed.
- No real patient filename or local path was printed.

Limitations:

- The corrected binary-stream attachment path has not yet been verified
  with a new real Smartsheet attachment.
- The temporary attachment naming convention remains a test convention.
- Automatic rollback of a created row after a later attachment failure
  is not implemented.
- The internal human-review minimum confidence intentionally continues
  to evaluate all populated extracted fields and may differ from the
  Smartsheet-facing minimum used for reviewer display.

Exact next starting point:

After this fix is committed and synchronized, run one controlled real
Smartsheet attachment verification through the existing complete-review
approval boundary. Verify only PHI-safe attachment metadata and success
status. Do not print document values, OCR text, source_text, filenames,
local paths, fingerprints, row IDs, or Smartsheet payload values.

------------------------------------------------------------
SMARTSHEET REVIEW VISIBILITY AND RUN TYPE - 2026-08-10
------------------------------------------------------------

Feature:

Expanded the reviewed AI-destination row metadata so reviewers can see
the AI document classification, the reasons a document requires or
recommends review, and an explicit PHI-safe operational Run Type.

Smartsheet review visibility:

New mapped review metadata columns:

- AI Document Category
- AI Document Subtype
- AI Review Reasons

AI Review Reasons uses the authoritative ReviewOutput.review_reasons
collection and serializes reasons deterministically in preserved order.

The mapping does not rerun extraction, reinterpret values, or expose
source_text.

Run Type:

Added the existing Smartsheet column:

- Run Type

Run Type is explicit workflow metadata and is not extracted or inferred
from OCR, Ollama, filenames, document content, or patient data.

Allowed values:

- Production
- Boss Demo
- Attachment Verification
- Classification Metadata Test
- End-to-End Test

Production is the default.

Invalid or unavailable Run Type values fail the logical mapping closed.

Run Type is propagated through:

MailboxFullReviewCommand
-> MailboxFullReviewOrchestrationService
-> MailboxCompleteReviewSmartsheetService
-> CompleteReviewSmartsheetWorkflowService
-> SmartsheetReviewSubmissionService
-> SmartsheetReviewRowMappingService

Classification confirmation remains separate from complete-review
approval and does not authorize a Smartsheet write.

Files changed:

- src/services/complete_review_smartsheet_workflow_service.py
- src/services/mailbox_complete_review_smartsheet_service.py
- src/services/mailbox_full_review_orchestration_service.py
- src/services/smartsheet_review_row_mapping_service.py
- src/services/smartsheet_review_submission_service.py
- src/ui/mailbox_full_review_command.py
- tests/test_complete_review_smartsheet_workflow_service.py
- tests/test_mailbox_complete_review_smartsheet_service.py
- tests/test_mailbox_full_review_command.py
- tests/test_mailbox_full_review_orchestration_service.py
- tests/test_smartsheet_review_row_mapping.py
- tests/test_smartsheet_review_submission_service.py

Final tested results:

Smartsheet review-row mapping:
23 passed, 0 failed.
Synthetic deterministic.

Approval-gated Smartsheet submission:
11 passed, 0 failed.
Synthetic deterministic/mock.

Full mailbox review command:
11 passed, 0 failed.
Mock command boundary.

Complete-review Smartsheet workflow:
10 passed, 0 failed.
Synthetic deterministic/mock.

Mailbox complete-review Smartsheet boundary:
15 passed, 0 failed.
Synthetic deterministic/mock.

Full mailbox review orchestration:
13 passed, 0 failed.
Mock full-orchestration.

Document-to-Smartsheet mapping integration:
9 passed, 0 failed.
Synthetic deterministic.

Smartsheet reviewed-write boundary:
17 passed, 0 failed.
Mock Smartsheet write boundary.

Combined final current-feature result:

Passed: 109
Failed: 0

External systems during automated tests:

- Microsoft Graph: Not called
- PaddleOCR: Not called
- Ollama: Not called
- Smartsheet external write: Not called

Real Smartsheet metadata-only verification:

- Schema read success: True
- Schema status: ready
- Destination column count: 27
- Required new column count: 4
- Required new columns found: 4
- Missing new column count: 0
- Rows read: 0
- Rows written: 0

Verified destination columns:

- AI Document Category
- AI Document Subtype
- AI Review Reasons
- Run Type

Corrected real attachment verification:

The previously corrected binary-stream Smartsheet attachment path was
subsequently exercised through the real external boundary and manually
confirmed successful.

No document filename, patient value, OCR text, source_text, local path,
row ID, or Smartsheet payload value was included in tracker or chat
output.

PHI handling:

- Automated tests used synthetic values only.
- Review-reason tests did not print mapped values or source evidence.
- Raw OCR text is not mapped.
- source_text remains prohibited from Smartsheet mapping.
- Local patient-document paths are not mapped.
- Run Type accepts only approved PHI-safe operational labels.
- Smartsheet payload values were not printed or logged.
- Real schema verification used column metadata only.

Limitations:

- AI Review Reasons currently reflects the authoritative combined review
  reasons, which can include classification, deterministic validation,
  and business-rule reasons.
- A new real patient-bearing row has not yet been written with the new
  classification/review-reason/Run Type metadata.
- A fresh complete-review approval is required for any new real row.
- Automatic rollback after a successful row write followed by attachment
  failure is still not implemented.
- Smartsheet retry/idempotency remains future production hardening.

Exact next starting point:

Before the next real write, audit all deterministic validation-action and
business-rule-action producers used by AI Review Reasons to confirm that
the sheet-visible reason strings contain only generic PHI-safe reason
text and never interpolate extracted values or source_text.

Then run the controlled real boss-demo path using the latest supported
local attachment, explicit Run Type "Boss Demo", real local OCR/Ollama,
deterministic validation, business rules, and complete human review.

Write only after a fresh explicit complete-review approval.

Keep patient data, OCR text, extracted values, source_text, filenames,
local paths, fingerprints, row IDs, and Smartsheet payload values out of
terminal and chat output.


------------------------------------------------------------
RUN TYPE TEST PURPOSE AND DATE CONFIDENCE - 2026-08-11
------------------------------------------------------------

Feature:

Changed Smartsheet Run Type from fixed environment/demo labels to
explicit PHI-safe operator-supplied text describing why the execution
was performed.

Run Type behavior:

- No automatic Production fallback.
- No Boss Demo or other fixed environment/demo choices.
- Test runs require explicit nonblank Run Type text.
- Run Type is never inferred from OCR, extracted values, filenames,
  local paths, patient data, or document content.
- Mapper rejects blank values, values over 120 characters, and values
  containing carriage returns or line feeds.
- CLI requires --run-type.
- Run Type remains workflow metadata and not extracted document data.

Date confidence mapping:

Added existing Smartsheet confidence columns:

- Start Date Conf.
- End Date Conf.

Mappings:

- start_date -> Start Date / Start Date Conf.
- end_date -> End Date / End Date Conf.

The existing generic confidence-column mapping is used. These displayed
confidence values participate in the existing AI Minimum Field
Confidence calculation.

AI Review Reasons PHI-safety audit:

Reviewed review-decision, deterministic evidence-validation, review
output, document-processing, and authorization business-rule reason
producers.

Observed sheet-visible reason producers use generic fixed reason text,
controlled field names, confidence thresholds, and service-line
numbers. No reviewed producer interpolated extracted document values or
source_text into review reasons.

Added a synthetic deterministic regression proving document values,
source_text, and classification-reason text do not enter
ReviewDecisionService review reasons through the normal reviewed path.

Focused and affected regression results:

- Smartsheet review configuration: 8 passed, 0 failed
- Smartsheet review row mapping: 24 passed, 0 failed
- Mailbox full-review command: 11 passed, 0 failed
- Complete-review Smartsheet workflow: 10 passed, 0 failed
- Mailbox complete-review Smartsheet service: 15 passed, 0 failed
- Mailbox full-review orchestration: 13 passed, 0 failed
- Smartsheet review submission: 11 passed, 0 failed
- Smartsheet review mapping integration: 9 passed, 0 failed
- Review decision: 19 passed, 0 failed
- Reviewed Smartsheet write integration: 4 passed, 0 failed

Total listed regression passes:

124 passed
0 failed

Test classification:

Synthetic deterministic and mock only for this change set.

External boundaries:

- Microsoft Graph not called.
- Fresh PaddleOCR not called.
- Ollama not called.
- Smartsheet external write API not called.
- No new real Smartsheet row was written.

PHI handling:

- Synthetic test values only.
- OCR text and source_text were not printed.
- Smartsheet payload values were not printed.
- Review-reason regression verifies synthetic document values and
  source evidence are excluded from review reasons.
- Stale fixed Run Type label audit returned no matches.

Limitations:

Operator-supplied Run Type cannot be semantically guaranteed PHI-free
by current validation. CLI/help and project policy prohibit patient
information, document values, filenames, paths, and source_text.
Mapper validation checks structure, not general PHI detection.

No fresh real OCR/Ollama execution was performed for this change set.

Exact next starting point:

Run the controlled real local OCR/Ollama/review path with explicit
PHI-safe Run Type:

Review reason visibility and date confidence columns

Keep patient data, OCR text, extracted values, source_text, filenames,
local paths, payload values, and row IDs out of terminal/chat output.

A fresh explicit complete-review approval is required before any new
real Smartsheet row is written.


------------------------------------------------------------
CLASSIFICATION CORRECTION PROPAGATION AND WRITE SUMMARY - 2026-08-12
------------------------------------------------------------

Feature:

Fixed two defects discovered during a controlled real mailbox review and
Smartsheet write.

Classification correction propagation:

Human-confirmed classification corrections were previously stored as
classification feedback but the existing in-memory Document and
ReviewOutput retained the original predicted classification.

That allowed a later explicitly approved Smartsheet write to use the
original predicted subtype instead of the human-confirmed subtype.

After successful classification-feedback storage, the confirmed category
and subtype now update both:

- Document classification state
- Existing ReviewOutput classification state

The change does not rerun classification, OCR, Ollama, extraction,
validation, business rules, or review-output construction.

A failed feedback-storage result does not mutate classification state.

Smartsheet write-summary correction:

A successful reviewed row with an attachment returns:

written=True
success=True
status=written_with_attachment

MailboxCompleteReviewSmartsheetService previously counted a successful
write only when status was exactly written.

The coordinator now treats success=True plus written=True as the
successful-write contract, so successful rows with attachments are
counted as written instead of failures.

Files changed:

- src/services/review_confirmation_submission_service.py
- src/services/mailbox_complete_review_smartsheet_service.py
- tests/test_review_confirmation_submission_service.py
- tests/test_mailbox_complete_review_smartsheet_service.py

Real test that exposed the defects:

- Real mailbox processing was used.
- Cached local OCR text was used.
- Local Ollama classification/extraction path ran.
- Explicit local classification review was performed.
- Classification feedback was stored.
- Explicit complete-review approval was given.
- A real Smartsheet row and attachment were observed.
- The human-confirmed subtype did not reach the written row.
- The final summary reported the successful attached write as a failure.

No row values, patient data, OCR text, source_text, identifying filenames,
local document paths, Smartsheet payload values, or row IDs were copied
into tracker or chat output.

Focused and affected regression results after the fixes:

- Review confirmation submission: 12 passed, 0 failed
- Mailbox complete-review Smartsheet service: 16 passed, 0 failed
- Classification review interaction: 12 passed, 0 failed
- Mailbox review session: 13 passed, 0 failed
- Mailbox full-review orchestration: 13 passed, 0 failed
- Complete-review Smartsheet workflow: 10 passed, 0 failed
- Approval-gated Smartsheet submission: 11 passed, 0 failed

Total:

87 passed
0 failed

Test classification:

Synthetic deterministic and mock for post-fix verification.

External boundaries during post-fix regression tests:

- Microsoft Graph not called.
- OCR not called.
- Ollama not called.
- Smartsheet external API not called.
- No additional real row was written during post-fix regression testing.

PHI handling:

- Synthetic test values only.
- OCR text and source_text were not printed.
- Smartsheet payload values were not printed.
- Failure results remain PHI-safe.
- Classification correction tests use classification labels only.
- No external integration was invoked by the regression suites.

Limitations:

The two defects are covered by synthetic deterministic/mock regressions
but have not yet been reverified with a second real external Smartsheet
write after the fixes.

Exact next starting point:

After this tested change is committed and pushed, run one controlled real
full mailbox review with a brand-new unread supported attachment and the
PHI-safe Run Type:

Classification correction propagation and attachment write summary

If classification requires correction, confirm only a locally verified
supported category/subtype.

A fresh explicit complete-review approval is required before the next
real Smartsheet row is written.

Verify only PHI-safe outcomes such as classification labels, counts,
booleans, write success, attachment presence, and final status. Keep
patient data, OCR text, extracted values, source_text, filenames, local
document paths, payload values, and row IDs out of terminal/chat output.


------------------------------------------------------------
SERVICE-LINE CONFIDENCE REVIEW NOISE CLEANUP - 2026-08-12
------------------------------------------------------------

Feature:

Removed a redundant service-line review reason created solely when raw
model confidence of 1.0 was conservatively capped to 0.95.

The deterministic 1.0 to 0.95 confidence cap remains unchanged.

The cap itself no longer emits:

Service line N confidence requires deterministic verification

A service line still emits a low-confidence review action when its final
validated confidence is below the existing 0.85 threshold.

Unsupported or invalid service-line evidence continues to generate
targeted review reasons. No authorization safety rule was weakened.

Files changed:

- src/services/evidence_validation_service.py
- tests/test_evidence_validation_service.py

Focused test:

- Evidence validation: 29 passed, 0 failed

Affected regressions:

- Review decision: 19 passed, 0 failed
- Review output service: 8 passed, 0 failed
- Review output integration: 7 passed, 0 failed
- Document-to-Smartsheet mapping integration: 9 passed, 0 failed

Combined automated result:

Passed: 72
Failed: 0

Test classification:

Synthetic deterministic only.

External boundaries during this change:

- Microsoft Graph not called.
- PaddleOCR not called.
- Ollama not called.
- Smartsheet external API not called.
- No new row was written.

PHI handling:

- Synthetic test values only.
- No OCR text or source_text was printed.
- No patient values, filenames, local paths, Smartsheet payloads, or row
  IDs were printed.
- Review-reason behavior remains generic and PHI-safe.

Related controlled real verification completed before this cleanup:

- One real mailbox document completed successfully.
- Human-confirmed classification correction was submitted.
- Complete-review approval was explicitly given.
- Approved: 1
- Written: 1
- Failed: 0
- Success: True
- Status: completed
- The written row was manually confirmed to use the human-confirmed
  renewal subtype.
- The row attachment was manually confirmed present.
- No row values, patient data, OCR text, source_text, filename, path,
  payload value, or row ID was copied into tracker output.

Limitation:

The remaining service-line review reasons have not yet been changed.
Unsupported date, status, modifier, low-confidence, and unresolved
authorization-quantity conditions remain active where deterministic
evidence does not support them.

Exact next starting point:

Inspect the current service-line date, status, modifier, and source_text
validation contracts together with the Ollama service-line extraction
prompt and tests.

Determine whether the remaining review reasons reflect genuinely
unsupported evidence or whether service-line source evidence is too
narrow to support otherwise valid extracted values.

Do not weaken evidence requirements, infer modifier ownership, or
interpret authorization quantity meaning without deterministic support.


------------------------------------------------------------
SOURCE-AGNOSTIC AUTHORIZATION AND SERVICE-LINE EVIDENCE - 2026-08-12
------------------------------------------------------------

Feature:

Completed the source-agnostic authorization naming cleanup and strengthened
the Ollama service-line extraction evidence contract.

Authorization naming cleanup:

- Removed payer-specific identifier guidance from the production Ollama
  extraction prompt.
- Authorization identifier labels are interpreted using surrounding
  label-value relationships and document evidence.
- Identifier meaning must not be inferred from payer, sender, filename,
  or template.
- Renamed the single-document authorization test runners from
  payer-specific names to document-purpose names.
- Production provider and renamed authorization runners contain no
  payer-specific Molina references.
- Remaining Molina references in the focused prompt test are intentional
  negative assertions verifying payer-specific prompt language is absent.

Service-line extraction guidance:

- Every non-null service-line field must be directly supported by the
  same service-line source evidence.
- service_code, modifier, quantity, dates, and status must each be
  supported by that row's evidence before being returned.
- A value appearing elsewhere in the document is not sufficient evidence
  for a service-line field.
- The stronger prompt guidance remains aligned with the existing
  deterministic evidence-validation contract.
- No service-line values from separate Ollama attempts are merged.

Files changed:

- AGENTS.md
- scripts/test_molina_document.py removed
- scripts/test_molina_timing.py removed
- scripts/test_authorization_document.py added
- scripts/test_authorization_timing.py added
- src/ai/llm/providers/ollama_provider.py
- tests/test_ollama_service_lines.py
- update_project_tracker.py

Compilation:

Modified provider, focused test, and renamed authorization runners compiled
successfully.

Focused Ollama service-line regression:

Passed: 19
Failed: 0

Affected evidence-validation regression:

Passed: 29
Failed: 0

Affected document-processor regression:

Passed: 16
Failed: 0

Combined automated result:

Passed: 64
Failed: 0

Test classification:

Synthetic deterministic.

The renamed real-document authorization runners were compiled but were not
executed during this checkpoint.

External boundaries during these regression tests:

- Microsoft Graph not called.
- PaddleOCR not called.
- Ollama not called.
- Smartsheet external API not called.
- No real Smartsheet row was written.

PHI handling:

- Synthetic deterministic test data only.
- No OCR text was printed or copied into tracker output.
- No patient data or extracted patient values were printed.
- No source_text containing PHI was printed.
- No identifying protected filename or local patient path was printed.
- No Smartsheet payload values or row IDs were printed.
- Rename verification used only safe source-code paths and reference
  counts.

Limitations:

- The strengthened service-line prompt has not yet been exercised through
  a new real local Ollama extraction run.
- The renamed authorization runners have not yet been executed after the
  naming cleanup.
- Real cached OCR behavior has not yet been reverified against the stronger
  same-row evidence prompt.
- Quantity meaning and modifier ownership remain conservative and require
  deterministic support or human review.
- No new real Smartsheet write was performed or authorized during this
  checkpoint.

Exact next starting point:

Run one controlled local authorization test through the renamed
single-document harness using real cached OCR and real local Ollama.

Keep OCR text, patient data, extracted values, source_text, protected
filenames, local patient paths, credentials, payload values, and row IDs
out of terminal and chat output.

Verify only PHI-safe counts, booleans, attempts, confidence metadata,
review status/reason counts, selected attempt, reconciliation state, and
success/failure.

Do not perform a real Smartsheet write without a fresh explicit
complete-review approval.


------------------------------------------------------------
PROJECT MEMORY AND BEGIN/END DAY CONTINUITY - 2026-08-13
------------------------------------------------------------

Feature:

Implemented a durable project continuity layer so work can resume from a
compact, committed project memory rather than relying on conversation
history alone.

Project memory:

Added `PROJECT_MEMORY.md` as the current-state continuity source.

The file records:

- source-of-truth ordering
- platform goal
- current architecture
- safety invariants
- implemented capabilities
- recent tested baseline
- known limitations and open questions
- Begin Day procedure
- End of Day procedure
- exactly one authoritative CURRENT NEXT START

The file explicitly prohibits PHI, OCR text, patient/member data,
source_text, protected filenames and paths, credentials, secrets, tokens,
Smartsheet payload values, and Smartsheet row IDs.

AGENTS continuity:

Replaced the volatile Current Work section in `AGENTS.md` with durable
Project Continuity rules.

`AGENTS.md` now defines:

- `PROJECT_MEMORY.md` as the current continuity layer
- Begin Day behavior
- End of Day behavior
- preservation and reconciliation of uncommitted work
- Git/local-state verification before continuing
- prohibition on automatically executing PHI-sensitive operations during
  Begin Day

Source-of-truth responsibilities are now separated:

- Git committed state: authoritative committed code
- confirmed local uncommitted state: work not yet committed
- AGENTS.md: durable repository and execution rules
- PROJECT_MEMORY.md: current project state and next start
- update_project_tracker.py: detailed historical checkpoints and project
  task synchronization

Continuity validation:

Passed: 14
Failed: 0

Validated behavior:

- AGENTS contains Project Continuity
- stale Current Work section removed
- AGENTS references PROJECT_MEMORY
- Begin Day procedure present
- End of Day procedure present
- PROJECT_MEMORY purpose present
- source-of-truth order present
- tested baseline present
- limitations section present
- Begin Day procedure present in memory
- End of Day procedure present in memory
- exactly one CURRENT NEXT START exists
- current 19/29/16 regression baseline preserved
- fresh explicit complete-review approval requirement preserved

Test classification:

Synthetic deterministic repository-text validation.

External boundaries:

- Microsoft Graph not called.
- PaddleOCR not called.
- Ollama not called.
- Smartsheet external API not called.
- No real patient document was accessed.
- No real Smartsheet row was written.

PHI handling:

- No patient data was used.
- No OCR text was used.
- No source_text was used.
- No protected patient filename or local patient path was used.
- No credentials, secrets, tokens, payload values, or row IDs were used.
- Validation inspected repository instruction and continuity text only.

Files changed:

- AGENTS.md
- PROJECT_MEMORY.md
- update_project_tracker.py

Limitations:

- PROJECT_MEMORY.md must be maintained whenever current project state,
  tested baseline, limitations, or CURRENT NEXT START changes.
- Begin Day still requires inspection of actual Git and local state rather
  than trusting the memory file blindly.
- Git remains authoritative for committed code.
- The project tracker remains the detailed historical record.
- The continuity system does not itself execute local-only commands or
  PHI-sensitive operations.

Exact next starting point:

Use the new Begin Day procedure to rehydrate project state, then run one
controlled local authorization test through the renamed single-document
authorization harness.

Use real cached OCR and real local Ollama while keeping PHI-bearing data
local.

Report only PHI-safe counts, booleans, attempts, confidence metadata,
review status and reason counts, selected attempt, reconciliation state,
and success/failure.

Do not perform a real Smartsheet write without a fresh explicit
complete-review approval.


------------------------------------------------------------
CODEX / WORK WEEKLY CAPACITY CONTINUITY - 2026-08-13
------------------------------------------------------------

Feature:

Added Codex/Work weekly-capacity planning to durable project memory.

Behavior:

- Codex and Work share the weekly usage limit.
- The exact reset timestamp shown in Codex and Work Analytics is
  authoritative when known.
- The currently known reset is August 18, 2026 at 1:26 PM local time.
- The known timestamp is current-cycle information and must be replaced
  after reset when a new authoritative timestamp is observed.
- Begin Day considers both remaining useful capacity and time until reset.
- Appropriate Codex work includes workspace inspection, complex
  multi-file edits, debugging, refactoring, caller/reference analysis,
  and architecture review.
- Worthwhile capacity should be used before expiration when it materially
  improves the work.
- Codex must never be used merely to consume credits.
- Codex must preserve uncommitted work, follow AGENTS.md, remain PHI-safe,
  and respect local PHI/OCR/Ollama boundaries.

Files changed:

- PROJECT_MEMORY.md
- update_project_tracker.py

Test classification:

Synthetic deterministic repository-text validation.

External boundaries:

- Microsoft Graph not called.
- PaddleOCR not called.
- Ollama not called.
- Smartsheet not called.
- No patient document accessed.

PHI handling:

No PHI, OCR text, source_text, protected patient filename/path,
credentials, secrets, tokens, payload values, or row IDs were used.

Limitations:

- Usage balance and reset timestamp are not continuously monitored.
- A new reset timestamp must be observed from Codex and Work Analytics
  after the current reset cycle.
- Codex selection remains task-driven rather than automatic.

Exact next starting point:

Continue from the authoritative CURRENT NEXT START in PROJECT_MEMORY.md.

During Begin Day, also consider worthwhile Codex work against the current
known reset timestamp.


------------------------------------------------------------
CONTROLLED AUTHORIZATION RETRY AND HARNESS CONTRACT - 2026-08-14
------------------------------------------------------------

Run Type:

Controlled Authorization Regression

Retry fix:

- Authorization raw and validated completeness checks now request the
  existing single controlled retry when no supported service-line rows
  remain, even when top-level service-code fields are also empty.
- Authorization-only scope, independent candidate validation, no candidate
  merging, deterministic selection, and attempt-1 tie behavior remain
  unchanged.
- No payer, service code, modifier, quantity, date, filename, or source
  conclusion was added to production retry logic.

Synthetic validation:

- Authorization harness contract: 5 passed, 0 failed.
- Document processor: 17 passed, 0 failed.
- Evidence validation: 29 passed, 0 failed.
- Ollama service lines: 19 passed, 0 failed.
- Review-output service: 8 passed, 0 failed.
- Review-output integration: 7 passed, 0 failed.
- Combined synthetic result: 85 passed, 0 failed.
- All modified Python files compiled successfully.

Real cached-OCR/local-Ollama verification:

- Classification: authorization.
- Extraction attempt count: 2.
- Raw retry required: False.
- Validated retry required: True.
- Retry triggered: True.
- Selected attempt: 2.
- Final service-line count: 2.
- Supported service-code and quantity evidence remained on both rows.
- A modifier remained only where row evidence supported it.
- Unsupported row dates and statuses were cleared.
- Unsupported authorization status was cleared.
- Human review required: True.
- Review output remained attached and preserved final review state.
- Microsoft Graph and Smartsheet were not called.
- No external AI was used.

Semantic harness correction:

The previous harness required authorization status and service-line dates
and statuses to remain populated even when deterministic evidence did not
support them. It also always required the modifier-relationship action.

The corrected contract now verifies that supported values remain supported,
unsupported values are cleared with validation actions, modifier-relationship
review is required only when a supported top-level modifier remains unresolved
across validated rows, human review remains required, review output preserves
final state, and retry metadata matches the controlled checkpoint.

PHI handling:

- Real processing remained local and PHI output was suppressed.
- No OCR text, source_text, patient values, protected filenames or paths,
  credentials, tokens, Smartsheet payload values, or row IDs were recorded.
- All harness-correction tests used synthetic deterministic data only.

Codex / Work Analytics:

- Weekly usage remaining observed: 99%.
- Authoritative reset: August 20, 2026 at 9:53 AM local time.
- Source: Codex and Work Analytics.
- This observation supersedes the prior August 18 reset value.
- The reason for the platform timestamp change is unknown and was not
  inferred.

Limitations:

- The corrected semantic harness has not yet been rerun against the
  controlled real cached-OCR/local-Ollama regression.
- Quantity meaning remains conservative and requires deterministic support
  or human review.
- No real Smartsheet write was performed or authorized.

Exact next starting point:

Run one controlled local authorization test through the corrected
single-document harness. Verify only PHI-safe retry metadata, supported-value
presence, cleared-value evidence flags, review state, reason counts, selected
attempt, service-line count, and semantic success/failure.

Do not expose PHI-bearing data and do not perform a real Smartsheet write
without fresh explicit complete-review approval.


------------------------------------------------------------
CONTROLLED AUTHORIZATION REGRESSION FINAL PASS - 2026-08-14
------------------------------------------------------------

Run Type:

Controlled Authorization Regression

Verified real result:

- Semantic regression: PASSED.
- Passed: 1.
- Failed: 0.
- Real cached OCR and real local Ollama were used locally.
- Extraction attempt count: 2.
- Retry triggered: True.
- Raw retry required: False.
- Validated retry required: True.
- Selected attempt: 2.
- Final service-line count: 2.
- Supported service-code and quantity structure remained preserved.
- Unsupported authorization and service-line values remained cleared with
  validation and review reasons.
- Human review required: True.
- Review output remained attached and preserved final state.
- Raw OCR text and the local document path were excluded from review output.

External boundaries:

- Microsoft Graph was not called.
- Smartsheet was not called and no row was written.
- No external AI was used.
- PHI output remained suppressed.

Continuity:

- The retry fix is verified in real cached-OCR/local-Ollama execution.
- The corrected authorization harness is verified in the same controlled
  real execution.
- Weekly usage remaining remains the observed 99%.
- The authoritative Codex and Work Analytics reset remains August 20, 2026
  at 9:53 AM local time.
- This newer observation supersedes the historical August 18 value; the
  reason for the timestamp change is unknown and was not guessed.

Limitations:

- Authorization quantity meaning remains intentionally conservative when
  deterministic evidence is insufficient.
- Modifier ownership remains unresolved without row evidence.
- No real Smartsheet write was performed or authorized.

Exact next starting point:

Inspect the existing authorization service-line quantity-reconciliation
boundary, callers, and synthetic tests. Confirm supported quantities are
preserved only within one independently validated candidate and are never
interpreted as visits, sessions, equipment, approval, or sufficient
authorization.

Make a code change only if inspection demonstrates a concrete gap. Do not
invent quantity meaning without confirmed business requirements.


------------------------------------------------------------
AUTHORIZATION QUANTITY RECONCILIATION SAFETY CHECKPOINT - 2026-08-14
------------------------------------------------------------

Feature:

Inspected the authorization service-line quantity-reconciliation boundary
end to end across deterministic validation, independent extraction-candidate
selection, authorization business rules, review output, and reviewed
Smartsheet mapping.

Verified behavior:

- Reconciliation uses only supported quantities from one independently
  validated candidate.
- Separate extraction attempts are never merged and ties retain attempt 1.
- Missing or null top-level authorized units are not inferred.
- Unsupported row quantities are cleared and excluded from reconciliation.
- Supported quantities remain eligible when another row field is unresolved;
  conservative confidence and review actions are preserved.
- Approved visits remain separate and unchanged.
- Quantity is not interpreted as visits, sessions, equipment, recurring
  services, approval, or sufficient authorization.
- Authorization business rules continue to require human verification.
- Review output preserves validated quantity state, confidence, evidence, and
  review metadata without reinterpretation.
- Smartsheet mapping performs no quantity conversion or reinterpretation.
- No production code change was required.

Files changed:

- tests/test_document_processor.py
- tests/test_service_line_quantity_reconciliation.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Synthetic deterministic and mock validation:

- Service-line quantity reconciliation: 10 passed, 0 failed.
- Document processor: 18 passed, 0 failed.
- Evidence validation: 29 passed, 0 failed.
- Authorization quantity rules: 8 passed, 0 failed.
- Review-output service: 8 passed, 0 failed.
- Smartsheet review-mapping integration: 9 passed, 0 failed.
- Ollama prompt and schema guardrails: 19 passed, 0 failed.
- Combined: 101 passed, 0 failed.
- All modified Python test files compiled successfully.

External and PHI boundaries:

- No patient document or protected data was accessed.
- Microsoft Graph, PaddleOCR, Ollama, the reviewed-document Smartsheet
  workflow, and external AI were not called during inspection or regression
  testing.
- No OCR text, patient values, source evidence, protected filenames or paths,
  credentials, secrets, tokens, payload values, or row IDs were exposed.

Limitations:

- Quantity business meaning and final approval remain human-review decisions.
- Modifier ownership remains unresolved without row evidence.
- No real Smartsheet write was performed or authorized.

Codex / Work Analytics continuity:

- Weekly usage remaining remains the observed 99%.
- The authoritative reset remains August 20, 2026 at 9:53 AM local time.
- The reason for the reset timestamp change remains unknown and was not
  guessed.

Exact next starting point:

Inspect the existing Microsoft Graph authentication-error boundary in
src/graph/auth.py, its configuration, callers, and current synthetic tests.
Add dedicated mock regression coverage for invalid credentials, expired
secrets, missing permissions, Graph authorization failures, and sanitized
error handling. Make a production change only if a failing synthetic
regression demonstrates a concrete gap. Do not make a live Graph request or
use real credentials or tokens.


------------------------------------------------------------
MICROSOFT GRAPH SANITIZED FAILURE BOUNDARY - 2026-08-14
------------------------------------------------------------

Feature:

Inspected and corrected the Microsoft Graph configuration, authentication,
request, authorization, caller, and diagnostic-entry-point failure boundary.

Confirmed pre-fix gap:

- MSAL/provider authentication descriptions were included in raised errors.
- Raw MSAL construction and token-acquisition exceptions could escape.
- Raw Graph 401/403, request, and response-decoding exceptions could escape.
- Uncaught diagnostic entry points could display those raw exceptions.

Implemented behavior:

- Added application-owned sanitized categories: configuration_error,
  authentication_failed, authorization_failed, and graph_request_failed.
- Missing configuration reports missing environment-variable names only and
  never reports values.
- Provider descriptions, response bodies, credentials, secrets, tokens, and
  authorization headers are not included in sanitized error output.
- Blank or failed token acquisition stops before any Graph request.
- HTTP 401 and 403 responses map to authorization_failed.
- Other request and response-decoding failures map to graph_request_failed.
- Successful token acquisition still returns the token internally without
  printing or logging it.
- Sanitized failures retain no provider exception cause or context.
- Existing RuntimeError compatibility is preserved through subclasses.

Files changed:

- src/graph/auth.py
- src/graph/client.py
- src/graph/config.py
- src/graph/errors.py
- tests/test_graph_security_boundary.py
- PROJECT_MEMORY.md
- update_project_tracker.py

Synthetic deterministic and mock validation:

- Initial red regression: 1 passed, 11 failed.
- Final Graph security boundary: 17 passed, 0 failed.
- Ten affected mailbox suites: 108 passed, 0 failed.
- Combined final result: 125 passed, 0 failed.
- All five modified Graph/security Python files compiled successfully.

External and PHI boundaries:

- Microsoft Graph and MSAL were mocked only.
- No real credentials or .env values were read or printed.
- No live Graph, patient-document, PaddleOCR, Ollama, reviewed-document
  Smartsheet, or external-AI operation occurred.
- No protected data, provider detail, credential, secret, token, response
  payload, OCR text, protected filename/path, or row ID was exposed.

Limitations:

- Verification is mock-only; no live negative authentication or authorization
  request was performed.
- Legacy Graph/mailbox diagnostic scripts still contain direct output of
  message metadata, identifiers, paths, OCR text, or extracted values and must
  not be run against live data before their output boundary is corrected.

Codex / Work Analytics continuity:

- Weekly usage remaining remains the observed 99%.
- The authoritative reset remains August 20, 2026 at 9:53 AM local time.
- The reason for the reset timestamp change remains unknown and was not
  guessed.

Exact next starting point:

Inspect scripts/test_graph_connection.py, scripts/test_graph_attachments.py,
scripts/check_graph_read_status.py, and scripts/test_mailbox_processor.py.
Add mocked stdout regressions for their current message metadata, identifier,
path, OCR-text, and extracted-value exposure, then make the smallest changes
needed to restrict output to PHI-safe counts, booleans, timings, confidence
metadata, and sanitized statuses. Do not run a live mailbox or real document.


------------------------------------------------------------
AUTOMATIC SMARTSHEET PRODUCTION FLOW CLARIFICATION - 2026-08-14
------------------------------------------------------------

Authoritative business requirement:

- Normal production processing automatically creates or populates the
  intentionally mapped Smartsheet row after deterministic validation and
  business rules.
- Human review is a downstream exception workflow and is not a write gate.
- Review-required rows must preserve supported values, keep unsupported or
  unreliable values null/unknown, and carry review status and reasons.
- The existing configured review thresholds remain unchanged; no new
  threshold was invented.
- Smartsheet is an approved production destination for intentionally mapped
  PHI and full document content.
- PHI or document content may reach Smartsheet only through an explicit
  production mapping/write path. Internal diagnostics, credentials, tokens,
  local paths, cache metadata, and unrelated internal fields remain excluded.

Durable continuity changes:

- AGENTS.md now defines automatic Smartsheet population before conditional
  downstream human review.
- PROJECT_MEMORY.md records the clarified architecture and implementation
  gap and contains one authoritative next start.
- Earlier tracker entries describing complete-review approval as write
  authority remain historical; this checkpoint supersedes that architecture
  decision.

Inspected implementation gap:

- SmartsheetReviewSubmissionService requires a successful explicit approval
  result before mapping or writing.
- CompleteReviewSmartsheetWorkflowService invokes an approval interaction
  before submission.
- Mailbox and full-review orchestration propagate explicit approval state.
- SmartsheetReviewRowMappingService blocks review-required rows unless a
  narrow approval exception applies and currently prohibits source_text.
- Existing focused tests encode these approval-gated assumptions.
- Correcting this coherently spans several active interfaces, so no broad
  production refactor was made during the durable-rule reconciliation.

External and PHI boundaries:

- Eleven focused Smartsheet/review-boundary suites passed: 120 passed,
  0 failed.
- Tests used synthetic deterministic or mocked data only and documented the
  current approval-gated contracts that are now obsolete.
- update_project_tracker.py compiled successfully.
- No real Smartsheet write is performed for this checkpoint.
- Microsoft Graph, PaddleOCR, Ollama, patient documents, and external AI are
  not called.
- No protected data, payload values, credentials, tokens, filenames, paths,
  OCR text, or source evidence is exposed.

Exact next starting point:

Add focused synthetic red regressions for automatic Smartsheet population of
both verified and review-required null-safe rows, then reconcile row mapping,
submission, complete-review workflow, mailbox orchestration, command options,
and callers as the smallest coherent interface change. Preserve review
status/reasons, configured thresholds, deterministic validation, explicit
destination mapping, and all no-inference rules. Use mocked Smartsheet only.
After this production boundary is green, resume the deferred legacy
Graph/mailbox diagnostic-output hardening task.


------------------------------------------------------------
AUTOMATIC SMARTSHEET WRITE BOUNDARY IMPLEMENTED - 2026-08-14
------------------------------------------------------------

Implemented production boundary:

- Deterministic validation and business rules continue to precede submission.
- Normal mailbox processing now automatically submits the intentionally
  mapped row without a complete-review approval result or approval flag.
- Review-required rows still write with review status and reasons; human
  review is downstream exception handling.
- Missing and unsupported values remain null or omitted under the existing
  mapping rules.
- Required missing destination data and destination-validation failures still
  prevent the writer call.
- Classification confirmation remains downstream feedback, not a write
  credential.
- The command path no longer requires an approval option.
- The full document continues through the existing explicit attachment-upload
  path.
- OCR text and source_text have no explicit Smartsheet destination and remain
  unmapped.
- No new columns or mappings were introduced, and document/review/internal
  objects are not serialized wholesale.

Regression evidence:

- Focused red result for obsolete approval gating: 5 passed, 8 failed.
- Final affected regression baseline: 286 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- No PHI or protected data was accessed.
- No real Microsoft Graph, PaddleOCR, Ollama, patient-document, Smartsheet
  production-write, or external-AI operation occurred.

Exact next starting point:

Resume the deferred legacy Graph/mailbox diagnostic stdout hardening for
scripts/test_graph_connection.py, scripts/test_graph_attachments.py,
scripts/check_graph_read_status.py, and scripts/test_mailbox_processor.py.
Use synthetic/mock stdout regressions first. Remove protected subjects, sender
addresses, message IDs, paths, raw OCR, extracted values, and raw error text.
Retain only PHI-safe counts, booleans, confidence/status/timing metadata. Do
not change mailbox or document-processing behavior. Do not run live Graph,
mailbox, or documents.


------------------------------------------------------------
LEGACY GRAPH/MAILBOX DIAGNOSTIC STDOUT HARDENED - 2026-08-14
------------------------------------------------------------

Work completed:

- Hardened scripts/test_graph_connection.py,
  scripts/test_graph_attachments.py, scripts/check_graph_read_status.py,
  and scripts/test_mailbox_processor.py.
- Added tests/test_legacy_graph_mailbox_diagnostic_stdout.py with synthetic
  marker-based stdout and sanitized-failure coverage.
- Removed subjects, sender addresses, received identifying metadata, message
  IDs, filenames, paths, raw OCR/document text, extracted values, raw mailbox
  errors, and raw provider diagnostics from covered script output.
- Confirmed source_text and field-evidence values remain excluded.
- Retained PHI-safe counts, booleans, safe sequence numbers, document/review
  status, confidence metadata, action/reason counts, and application-owned
  sanitized failure categories.
- No EmailService, AttachmentService, MailboxProcessor, mark-as-read,
  idempotency, document-processing, validation/business-rule, review, or
  automatic-Smartsheet behavior changed.

Regression evidence:

- Initial focused red result: 2 passed, 16 failed.
- Final focused stdout regression: 22 passed, 0 failed.
- Affected Graph/mailbox regressions: 121 passed, 0 failed.
- Combined: 143 passed, 0 failed.
- Compilation: 5 passed, 0 failed.
- Test classification: synthetic deterministic and mock.
- No protected stdout exposure remains in the covered paths.
- No PHI or protected data was accessed.
- No live Microsoft Graph, mailbox, attachment, PaddleOCR, Ollama,
  patient-document, production-Smartsheet, or external-AI operation occurred.

Limitation:

- Verification is mock-only; the hardened diagnostics were not run against a
  live mailbox.

Exact next starting point:

Inspect the existing automatic Smartsheet row-write and attachment-upload
boundary for the previously tracked partial-success and retry/idempotency
limitation. Use focused mocked red regressions first for a successful row
creation followed by attachment failure and for a subsequent retry. Determine
the smallest safe correction that prevents duplicate rows or explicitly
preserves partial-success state without changing deterministic validation,
business rules, automatic writing, downstream review, or explicit destination
mappings. Do not run a real Smartsheet write, Graph, OCR, Ollama, mailbox, or
patient document.

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
            "prompt. A controlled real authorization run triggered validated "
            "retry, selected attempt 2, and recovered supported service-line "
            "structure while unsupported values remained cleared."
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
            "or attempt merging."
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
            "candidate-selection, quantity-reconciliation, validator, review, "
            "and mapping tests pass, while quantity meaning, final approval, "
            "and final business rules remain pending human confirmation."
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
            "failure categories. Smartsheet attachment partial-success and "
            "retry/idempotency behavior remains future production hardening."
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
