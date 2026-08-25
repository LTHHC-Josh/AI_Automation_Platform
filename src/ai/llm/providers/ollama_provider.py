import json
import os
from copy import deepcopy
from typing import Any

import requests

from src.ai import config
from src.ai.llm.llm_provider import LLMProvider
from src.ai.llm.provider_registration import register_llm_provider
from src.models.document_taxonomy import DocumentTaxonomyRegistry


@register_llm_provider("ollama")
class OllamaProvider(LLMProvider):
    """
    Local Ollama provider for healthcare document processing.

    Classification and extraction are intentionally separate model
    requests. Testing showed that a combined request caused substantial
    extraction and classification regressions without a meaningful
    performance improvement.

    OCR text is sent only to the locally configured Ollama server.
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_SEED = 42
    RETRY_SEED_OFFSET = 1
    CHAT_ENDPOINT = "/api/chat"

    DOCUMENT_CATEGORIES = list(DocumentTaxonomyRegistry.families())

    DOCUMENT_SUBTYPES = list(DocumentTaxonomyRegistry.subtypes())

    AUTHORIZATION_SUBTYPES = set(
        DocumentTaxonomyRegistry.definition("authorization").subtypes
    )

    TERMINATION_SUBTYPES = set(
        DocumentTaxonomyRegistry.definition("termination").subtypes
    )

    FIELD_NAMES = [
        "patient_name",
        "member_id",
        "payer",
        "authorization_number",
        "authorization_status",
        "request_type",
        "service_code",
        "service_codes",
        "service_description",
        "modifier",
        "authorized_units",
        "approved_visits",
        "start_date",
        "end_date",
        "posted_date",
        "renewal_qualifier",
        "member_dob",
        "provider_name",
        "provider_npi",
        "diagnosis_code",
        "diagnosis_description",
        "hours",
        "days_per_week",
    ]

    SERVICE_LINE_FIELD_NAMES = [
        "service_code",
        "modifier",
        "quantity",
        "start_date",
        "end_date",
        "status",
        "confidence",
        "source_text",
    ]

    SAFE_METRIC_FIELDS = (
        "done",
        "done_reason",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    )

    CONFIDENCE_FIELD_SCHEMA = {
        "type": "object",
        "properties": {
            "value": {
                "type": [
                    "string",
                    "number",
                    "integer",
                    "array",
                    "null",
                ],
                "items": {
                    "type": [
                        "string",
                        "number",
                        "integer",
                    ],
                },
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "source_text": {
                "type": "string",
            },
        },
        "required": [
            "value",
            "confidence",
            "source_text",
        ],
        "additionalProperties": False,
    }

    SERVICE_LINE_SCHEMA = {
        "type": "object",
        "properties": {
            "service_code": {
                "type": [
                    "string",
                    "null",
                ],
            },
            "modifier": {
                "type": [
                    "string",
                    "null",
                ],
            },
            "quantity": {
                "type": [
                    "string",
                    "number",
                    "integer",
                    "null",
                ],
            },
            "start_date": {
                "type": [
                    "string",
                    "null",
                ],
            },
            "end_date": {
                "type": [
                    "string",
                    "null",
                ],
            },
            "status": {
                "type": [
                    "string",
                    "null",
                ],
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "source_text": {
                "type": "string",
            },
        },
        "required": SERVICE_LINE_FIELD_NAMES,
        "additionalProperties": False,
    }

    CLASSIFICATION_SCHEMA = {
        "type": "object",
        "properties": {
            "document_category": {
                "type": "string",
                "enum": DOCUMENT_CATEGORIES,
            },
            "document_subtype": {
                "type": "string",
                "enum": DOCUMENT_SUBTYPES,
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "reason": {
                "type": "string",
            },
        },
        "required": [
            "document_category",
            "document_subtype",
            "confidence",
            "reason",
        ],
        "additionalProperties": False,
    }

    EXTRACTION_SCHEMA = {
        "type": "object",
        "properties": {
            "fields": {
                "type": "object",
                "properties": {
                    field_name: {
                        "$ref": "#/$defs/confidenceField"
                    }
                    for field_name in FIELD_NAMES
                },
                "required": FIELD_NAMES,
                "additionalProperties": False,
            },
            "service_lines": {
                "type": "array",
                "items": {
                    "$ref": "#/$defs/serviceLine"
                },
            },
        },
        "required": [
            "fields",
            "service_lines",
        ],
        "additionalProperties": False,
        "$defs": {
            "confidenceField": CONFIDENCE_FIELD_SCHEMA,
            "serviceLine": SERVICE_LINE_SCHEMA,
        },
    }

    LEARNING_ANALYSIS_SCHEMA = {
        "type": "object",
        "properties": {
            "document_structure": {
                "type": "object",
                "properties": {
                    "document_form_type": {"type": "string"},
                    "document_category": {
                        "type": "string",
                        "enum": [
                            "authorization", "referral", "termination",
                            "denial", "assessment", "plan_of_care", "claim",
                            "communication", "form", "2067", "other", "unknown",
                        ],
                    },
                    "document_subtype": {"type": "string"},
                    "purpose_concepts": {"type": "array", "items": {"type": "string"}},
                    "direction_context": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "document_form_type", "document_category", "document_subtype",
                    "purpose_concepts", "direction_context",
                ],
                "additionalProperties": False,
            },
            "date_fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field_name": {"type": "string"},
                        "semantic_role": {
                            "type": "string",
                            "enum": [
                                "posted", "effective", "start", "end",
                                "request", "approval", "service",
                                "communication", "unknown",
                            ],
                        },
                        "evidence_status": {
                            "type": "string",
                            "enum": [
                                "supported", "unsupported", "conflicting",
                                "ambiguous", "tentative", "missing", "unknown",
                            ],
                        },
                    },
                    "required": ["field_name", "semantic_role", "evidence_status"],
                    "additionalProperties": False,
                },
            },
            "authorization_service_structure": {
                "type": "object",
                "properties": {
                    name: {"type": "boolean"}
                    for name in (
                        "authorization_concepts_present",
                        "quantity_concepts_present", "units_concepts_present",
                        "visits_concepts_present", "approval_concepts_present",
                        "request_concepts_present",
                    )
                },
                "required": [
                    "authorization_concepts_present",
                    "quantity_concepts_present", "units_concepts_present",
                    "visits_concepts_present", "approval_concepts_present",
                    "request_concepts_present",
                ],
                "additionalProperties": False,
            },
            "business_concepts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "concept_label": {"type": "string"},
                        "explicitly_supported": {"type": "boolean"},
                        "evidence_status": {
                            "type": "string",
                            "enum": [
                                "supported", "unsupported", "conflicting",
                                "ambiguous", "tentative", "missing", "unknown",
                            ],
                        },
                        "current_modeled_field": {"type": "boolean"},
                    },
                    "required": [
                        "concept_label", "explicitly_supported",
                        "evidence_status", "current_modeled_field",
                    ],
                    "additionalProperties": False,
                },
            },
            "schema_gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "candidate_name": {"type": "string"},
                        "structural_type": {
                            "type": "string",
                            "enum": [
                                "date", "identifier", "status", "checkbox",
                                "quantity", "code", "name", "text",
                                "selection", "table", "other",
                            ],
                        },
                        "evidence_status": {
                            "type": "string",
                            "enum": [
                                "supported", "unsupported", "conflicting",
                                "ambiguous", "tentative", "missing", "unknown",
                            ],
                        },
                    },
                    "required": ["candidate_name", "structural_type", "evidence_status"],
                    "additionalProperties": False,
                },
            },
            "coverage": {
                "type": "object",
                "properties": {
                    "analyzed_page_refs": {"type": "array", "items": {"type": "integer"}},
                    "complete_document_analyzed": {"type": "boolean"},
                },
                "required": ["analyzed_page_refs", "complete_document_analyzed"],
                "additionalProperties": False,
            },
            "observations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "observation_id": {"type": "string"},
                        "observation_kind": {"type": "string", "enum": [
                            "document_family", "form_identifier", "modeled_field",
                            "date_role", "service_structure", "business_concept",
                            "free_text_concept", "schema_gap", "review_reason",
                        ]},
                        "normalized_label": {"type": "string"},
                        "proposed_category": {"type": "string", "enum": [
                            "business", "date", "document", "field", "form",
                            "service", "workflow", "free_text", "other",
                        ]},
                        "evidence_refs": {"type": "array", "items": {"type": "string"}},
                        "evidence_status": {"type": "string", "enum": [
                            "supported", "unsupported", "conflicting", "ambiguous",
                            "tentative", "missing", "unknown",
                        ]},
                        "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                        "repetition_count": {"type": "integer", "minimum": 0},
                        "current_modeled_field": {"type": ["string", "null"]},
                        "production_rule_status": {"type": "string", "enum": ["not_applicable", "not_mapped"]},
                        "deterministically_validated": {"type": "boolean"},
                    },
                    "required": [
                        "observation_id", "observation_kind", "normalized_label",
                        "proposed_category", "evidence_refs", "evidence_status",
                        "confidence", "repetition_count", "current_modeled_field",
                        "production_rule_status", "deterministically_validated",
                    ],
                    "additionalProperties": False,
                },
            },
            "contradictions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "contradiction_type": {"type": "string"},
                        "evidence_refs": {"type": "array", "items": {"type": "string"}},
                        "evidence_status": {"type": "string", "enum": ["conflicting", "ambiguous"]},
                    },
                    "required": ["contradiction_type", "evidence_refs", "evidence_status"],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "document_structure", "date_fields",
            "authorization_service_structure", "business_concepts",
            "schema_gaps", "coverage", "observations", "contradictions",
        ],
        "additionalProperties": False,
    }

    def __init__(self) -> None:
        self.base_url = os.getenv(
            "OLLAMA_BASE_URL",
            self.DEFAULT_BASE_URL,
        ).rstrip("/")

        self.model = os.getenv(
            "OLLAMA_MODEL",
            getattr(
                config,
                "LLM_MODEL",
                "llama3.1:8b",
            ),
        ).strip()

        self.timeout = self._load_timeout()
        self.seed = self._load_seed()
        self._last_request_metrics: dict[str, Any] = {}

        if not self.model:
            raise RuntimeError(
                "No Ollama model is configured."
            )

    def classify(
        self,
        text: str,
    ) -> dict:
        """
        Classify OCR text using one local Ollama request.
        """

        cleaned_text = self._validate_text(
            text
        )

        result = self._chat(
            system_prompt=self._classification_prompt(),
            user_prompt=(
                "Classify the following OCR text.\n\n"
                "DOCUMENT TEXT\n"
                "=============\n"
                f"{cleaned_text}"
            ),
            schema=self.CLASSIFICATION_SCHEMA,
            seed=self.seed,
        )

        self._last_request_metrics[
            "request_type"
        ] = "classification"

        self._last_request_metrics[
            "seed"
        ] = self.seed

        return self._normalize_classification(
            result
        )

    def extract(
        self,
        text: str,
        prompt: str,
        attempt: int = 1,
    ) -> dict:
        """
        Extract structured fields using a separate local request.

        Args:
            text: OCR text.
            prompt: Confirmed classification from the first request.
        """

        cleaned_text = self._validate_text(
            text
        )

        document_type = str(
            prompt or "unknown"
        ).strip().lower()

        normalized_attempt = self._normalize_attempt(
            attempt
        )

        request_seed = self._seed_for_attempt(
            normalized_attempt
        )

        result = self._chat(
            system_prompt=self._extraction_prompt_for_attempt(
                normalized_attempt
            ),
            user_prompt=(
                "The document was classified as: "
                f"{document_type}\n\n"
                "Extract structured fields from the following OCR "
                "text.\n\n"
                "DOCUMENT TEXT\n"
                "=============\n"
                f"{cleaned_text}"
            ),
            schema=self.EXTRACTION_SCHEMA,
            seed=request_seed,
        )

        self._last_request_metrics[
            "request_type"
        ] = "extraction"

        self._last_request_metrics[
            "attempt"
        ] = normalized_attempt

        self._last_request_metrics[
            "seed"
        ] = request_seed

        self._last_request_metrics[
            "retry_prompt_applied"
        ] = (
            normalized_attempt > 1
        )

        return {
            "fields": self._normalize_fields(
                result.get(
                    "fields",
                    {},
                )
            ),
            "service_lines": self._normalize_service_lines(
                result.get(
                    "service_lines",
                    [],
                )
            ),
        }

    def get_last_request_metrics(
        self,
    ) -> dict[str, Any]:
        """
        Return PHI-safe metadata from the most recent Ollama request.

        The returned values contain only timing, token-count, and
        completion information. Prompt text, response content, OCR text,
        extracted values, and source evidence are excluded.
        """

        return dict(
            self._last_request_metrics
        )

    def analyze_learning_structure(self, evidence) -> dict:
        """Return structured concepts without returning document values."""

        from src.models.learning_document_evidence import LearningDocumentEvidence

        prompt_text = (
            evidence.to_local_prompt()
            if isinstance(evidence, LearningDocumentEvidence)
            else str(evidence or "")
        )
        cleaned_text = self._validate_text(prompt_text)
        result = self._chat(
            system_prompt=self._learning_analysis_prompt(),
            user_prompt=(
                "Analyze the complete document evidence envelope. Do not reproduce "
                "any document value or narrative text.\n\nDOCUMENT EVIDENCE\n"
                "=============\n" + cleaned_text
            ),
            schema=self._learning_schema(evidence),
            seed=self.seed,
        )
        self._last_request_metrics["request_type"] = "learning_analysis"
        self._last_request_metrics["seed"] = self.seed
        return result

    def _learning_schema(self, evidence) -> dict:
        """Bind model references to aliases supplied in this one request."""

        from src.models.learning_document_evidence import LearningDocumentEvidence

        schema = deepcopy(self.LEARNING_ANALYSIS_SCHEMA)
        if not isinstance(evidence, LearningDocumentEvidence):
            return schema
        reference_schema = {
            "type": "string",
            "enum": list(evidence.model_references),
        }
        for section in ("observations", "contradictions"):
            schema["properties"][section]["items"]["properties"][
                "evidence_refs"
            ]["items"] = reference_schema
        schema["properties"]["coverage"]["properties"][
            "analyzed_page_refs"
        ]["items"] = {
            "type": "integer",
            "enum": list(evidence.page_references),
        }
        return schema

    def test_connection(self) -> dict:
        """
        Verify the local Ollama server and configured model.
        """

        endpoint = (
            f"{self.base_url}/api/tags"
        )

        try:
            response = requests.get(
                endpoint,
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as ex:
            raise RuntimeError(
                "Unable to connect to the local Ollama server at "
                f"{self.base_url}."
            ) from ex

        payload = response.json()

        models = payload.get(
            "models",
            [],
        )

        installed_models = {
            str(
                model.get(
                    "name",
                    "",
                )
            ).strip()
            for model in models
            if isinstance(
                model,
                dict,
            )
        }

        model_available = (
            self.model in installed_models
            or any(
                installed_model.split(":")[0]
                == self.model.split(":")[0]
                for installed_model in installed_models
            )
        )

        return {
            "server": self.base_url,
            "configured_model": self.model,
            "model_available": model_available,
            "installed_models": sorted(
                installed_models
            ),
        }

    def _learning_analysis_prompt(self) -> str:
        return """
You are a local structural document-learning service for a healthcare
automation platform. Analyze the entire OCR text, including labeled fields,
tables, checkboxes, headings, comments, and narrative business concepts.

Inspect every page and block. Return every analyzed page ordinal in coverage.
Layout, page, region, coordinates, and header/footer status are optional hints,
never fixed requirements. Use labels, nearby values, reading order, repetition,
and cross-page relationships. Preserve repeated agreement; conflicting or
ambiguous candidates remain unresolved and must not be guessed.

Return structural metadata only. Never return, quote, paraphrase, summarize,
or embed patient/member/provider names, identifiers, codes, actual dates,
field values, comments, narrative phrases, sender details, paths, filenames,
credentials, or tokens.

Use short generic snake_case labels that describe field or business meaning,
not document values. Identify business concepts only when explicitly supported
by the document. The examples unable_to_locate, annual_past_due, no_change,
renewal, initial, and inbound_authorization are illustrative, not a fixed list.
Do not infer a concept from document type, sender, filename, or template.

For schema gaps, identify labeled fields or useful structural concepts absent
from the current modeled field set, but return only a generic semantic label,
structural type, and evidence status. Do not propose production decisions.

Every observation and contradiction must reference compact block aliases from
the supplied envelope exactly. Literal evidence stays in the envelope; return generic semantic labels
and references only. Keep literal evidence, normalized meaning, and production
fields or rules separate. Confidence is nullable and never correctness proof.
Set deterministically_validated false for every observation. Learning cannot
change production rules. Contact failure does not mean UTL. Requested services
are not approved services, units are not visits, and quantity, codes, dates, or
generic status do not establish approval.
""".strip()

    def _classification_prompt(self) -> str:
        return """
You are a local healthcare document classification service for a home
healthcare automation platform.

Classify the OCR text using exactly one document_category and one
document_subtype.

DOCUMENT CATEGORIES

- authorization
- referral
- termination
- denial
- assessment
- plan_of_care
- claim
- 2067
- other
- unknown

DOCUMENT SUBTYPES

For authorization:

- initial
- renewal
- extension
- continuation
- amendment
- partial_approval
- unknown

For termination:

- authorization_termination
- service_termination
- unknown

For 2067:

- utl
- unknown

For every other category, use subtype unknown.

Use 2067 only when the document itself supports that form family. Use utl only
as a candidate when the complete document supports inability to locate or
contact the member. Deterministic application validation makes the final UTL
decision; 2067, annual wording, Posted Date, or a literal UTL token alone is
insufficient.

GENERAL RULES

Use only evidence directly supported by the OCR text.

Documents may arrive in nonstandard formats from many service
coordinators. Classify by supported document purpose and content, not by
layout, sender, logo, filename, or one known template.

Use unknown when the category cannot be supported.

Use subtype unknown when the category is supported but the subtype is
missing, conflicting, ambiguous, or dependent on an unreadable
checkbox.

Do not automatically assign 1.0 confidence.

AUTHORIZATION

Use authorization when the document clearly communicates an approval,
authorization decision, authorization number, approved service lines,
authorized dates, units, visits, sessions, equipment, or service codes.

Do not assume whether an authorization is initial, renewal, extension,
continuation, amendment, or partial approval.

Forms may contain labels for every checkbox option even when OCR cannot
determine which option is selected. A visible option label does not
prove selection.

Use initial only when reliable evidence explicitly supports an initial
authorization or initial approval.

Use renewal, extension, continuation, or amendment only when reliable
evidence explicitly supports that subtype.

Use partial_approval only when the document clearly approves less than
the full requested service, quantity, duration, or scope.

REFERRAL

Use referral when the primary purpose is to refer a patient for
services, evaluation, intake, consultation, or provider follow-up and
the document does not itself communicate an authorization decision.

A request for authorization is not automatically a referral.

TERMINATION

Use termination only when an authorization or an authorized service is
being terminated, discontinued, revoked, ended, closed, or stopped.

Use authorization_termination when the document ends or revokes the
authorization as a whole.

Use service_termination when the document ends or discontinues a
specific authorized service while the broader authorization may remain.

Do not use termination for employee, provider, vendor, contract,
administrative, or other non-patient authorization/service termination.

DENIAL

Use denial when the document communicates that requested authorization
or service was denied, not approved, or refused.

OTHER

Use other only when the document purpose is supported but does not fit
another listed category.

Return a short reason describing the classification evidence without
inventing unsupported facts.

Return only JSON matching the required schema.
""".strip()

    def _extraction_prompt(self) -> str:
        return """
You are a local healthcare structured-data extraction service for a
home healthcare automation platform.

Extract only information directly supported by the OCR text.

Never invent, infer, estimate, or complete a missing value.

Return null when a value cannot be reliably determined.

Each top-level field must include:

- value
- confidence
- source_text

source_text must be a short exact phrase from the OCR text supporting
the extracted value.

When a top-level value is null:

- confidence must be 0
- source_text must be an empty string

CONFIDENCE RULES

Confidence must reflect the evidence for each individual field.

Do not automatically assign 1.0.

High confidence requires:

- a clear label-value relationship,
- readable OCR text,
- no conflicting values,
- no unsupported interpretation.

Lower confidence when:

- OCR is unclear,
- multiple values compete,
- a checkbox selection is uncertain,
- the value requires interpretation,
- the relationship between a label and value is weak.

IDENTIFIERS

Do not confuse:

- member IDs,
- authorization numbers,
- fax message numbers,
- phone numbers,
- provider NPIs,
- claim numbers.

Authorization documents may use labels such as:

- "Health Plan ID" for a member identifier,
- "Member or Medicaid ID #" for a member identifier,
- "Reference#" for an authorization or reference identifier.

Use the surrounding label-value relationship and document evidence.
Do not infer identifier meaning from payer, sender, filename, or template.

AUTHORIZATION STATUS

authorization_status represents only the actual authorization decision
or authorization state supported by the document.

Do not combine request language with authorization decision language.

Examples:

- clear approval evidence may support Approved
- clear denial evidence may support Denied
- clear pending or review-state evidence may support that stated status

A request for services, visits, hours, units, or authorization does not by
itself prove approval.

Do not return blended or synthesized statuses such as:

- Approved Requested
- Requested Approved
- Approved Request

When the authorization decision is missing, conflicting, or ambiguous,
return null with confidence 0.

REQUEST TYPE

A form may contain both:

- Initial Request
- Extension/Renewal/Amendment

OCR may read both labels even when it cannot identify the selected
checkbox.

Do not return a request type unless the selected option is reliably
supported.

When selection is unclear, return null with confidence 0.

SERVICE CODES AND MODIFIERS

Extract service codes such as S9110 as service codes.

Do not treat ordinary words or service-description text as modifiers.

A modifier must be a clear code associated with a service line, such as
U1.

Return service_code as a single string when one unique service code is
present.

Return service_codes as a deduplicated list of service codes.

Do not duplicate the same service code merely because it appears on
multiple service lines.

SERVICE DESCRIPTION

Return one concise service description as a string.

Do not return a list unless the document contains genuinely distinct
services that cannot be represented accurately by one description.

QUANTITIES

Authorization documents may contain:

- visits,
- sessions,
- units,
- recurring monthly quantities,
- equipment quantities,
- multiple service-line quantities.

Keep approved_visits and authorized_units separate.

Do not treat a requested quantity as approved unless it appears in a
clear approval or authorized-service context.

When multiple approved service lines contain units, return
authorized_units as an array preserving the service-line quantities.

Do not total multiple quantities unless the document explicitly shows
a total.

Do not decide whether units or visits satisfy LTHHC business rules.
Extract only what the document supports.

SERVICE LINES

Return service_lines as an array.

Each service-line item must contain:

- service_code
- modifier
- quantity
- start_date
- end_date
- status
- confidence
- source_text

Create one service-line item for each distinct row that can be reliably
supported by the OCR text.

Preserve relationships within each row. Do not combine a quantity from
one row with a modifier, date, status, or service code from another row.

Use null for a service-line field when that value is not clearly shown
for that row.

When a service-line row itself cannot be reliably reconstructed, do not
guess. Omit that row.

Return an empty service_lines array when no reliable row-level service
data can be reconstructed.

A service-line source_text value must contain the shortest available OCR
text that directly supports every non-null field in that service line and
the relationship among those row values.

Before returning any non-null service-line field, verify it against that
same service-line source_text:

- service_code must appear in the row evidence,
- modifier must appear in the row evidence,
- quantity must appear in the row evidence,
- start_date and end_date must each be directly supported by a date in
  the row evidence,
- status must appear in the row evidence.

If that same row evidence does not support a field, return null for that
field. Do not preserve a value merely because it appears elsewhere in the
document.

Service-line confidence must reflect confidence in the whole row, not
only the service code.

Do not interpret the operational or billing meaning of a service code,
modifier, quantity, or row.

DATES

Normalize reliably supported dates to YYYY-MM-DD.

Return start_date and end_date as single strings, not arrays.

Prefer dates associated with approved authorization service lines.

Do not use fax dates, submission dates, review dates, printed dates, or
request dates as authorization start or end dates unless the document
clearly identifies them as the authorized service period.

POSTED DATE AND RENEWAL QUALIFIER

Return posted_date only when the source explicitly labels that exact value
as Posted Date. Do not infer it from received, signed, generated,
authorization start/end, or other dates, document position, or filename.

Return renewal_qualifier only when the source explicitly labels a renewal
qualifier and directly supports the returned value. Do not infer NO CHANGE
from matching quantities, unchanged-looking hours, filenames, or generic
wording. A qualifier does not establish that the document is a renewal.

HOURS AND DAYS PER WEEK

Extract hours only when the document directly states an hours value in a
clear service or authorization context.

Extract days_per_week only when the document directly states the number
of days per week in a clear service or authorization context.

Do not derive hours or days_per_week from:

- authorized units,
- requested units,
- visits,
- sessions,
- service codes,
- date ranges,
- arithmetic,
- assumptions about service duration or frequency.

If the value is not directly supported, return null with confidence 0.

PROVIDER NPI

Extract provider_npi only when a clear 10-digit NPI is associated with
the provider.

DIAGNOSIS

Preserve diagnosis codes exactly.

Return one diagnosis code as a string.

Return multiple distinct diagnosis codes as a deduplicated array.

Do not add codes that are not present in the OCR text.

Return only JSON matching the required schema.
""".strip()

    def _extraction_prompt_for_attempt(
        self,
        attempt: Any,
    ) -> str:
        """
        Return the extraction prompt for one controlled attempt.

        Attempt 1 uses the established extraction prompt unchanged.
        Later attempts append a generic verification section intended
        to encourage a fresh row-by-row reconstruction.

        The retry instructions do not introduce payer-specific,
        service-code-specific, or document-specific conclusions.
        """

        normalized_attempt = self._normalize_attempt(
            attempt
        )

        base_prompt = self._extraction_prompt()

        if normalized_attempt == 1:
            return base_prompt

        return (
            f"{base_prompt}\n\n"
            f"{self._retry_prompt_addendum()}"
        )

    def _retry_prompt_addendum(
        self,
    ) -> str:
        """
        Return generic verification instructions for a retry request.

        These instructions strengthen evidence checking without
        supplying missing values, interpreting business meaning, or
        referring to a specific payer or document.
        """

        return """
CONTROLLED RETRY VERIFICATION

This is a fresh verification pass.

Reread the entire OCR text from the beginning. Do not copy assumptions
from an earlier extraction.

Reconstruct every service line independently and in document order.

For each proposed service line:

- identify the shortest row-level source_text that directly supports
  every non-null field in that row,
- confirm that service_code appears in that same row evidence,
- confirm that modifier appears in that same row evidence when non-null,
- confirm that quantity appears in that same row evidence when non-null,
- confirm that each non-null start_date and end_date is directly supported
  by a date in that same row evidence,
- confirm that status appears in that same row evidence when non-null,
- use null for any field not supported by that same row evidence,
- do not preserve a row value merely because it appears elsewhere in the
  document,
- omit the row when a reliable row relationship cannot be reconstructed.

Do not combine a service code from one row with a quantity, modifier,
date, or status from another row.

After reconstructing service_lines, verify the top-level fields:

- service_code must agree with the supported service lines,
- service_codes must contain only deduplicated supported row codes,
- authorized_units must preserve only supported row quantities,
- approved_visits must remain separate from authorized_units,
- requested quantities must not become approved quantities without
  clear approval evidence.

Do not infer payer-specific meaning.

Do not infer the operational meaning of units, visits, sessions,
equipment quantities, modifiers, or service codes.

Do not fill a missing value merely to make the output complete.

Return null or omit an unsupported row rather than guessing.

Return only JSON matching the required schema.
""".strip()

    def _normalize_classification(
        self,
        value: Any,
    ) -> dict:
        """
        Normalize the two-level classification contract.

        document_type remains a backward-compatible routing value.
        """

        if not isinstance(
            value,
            dict,
        ):
            value = {}

        category = str(
            value.get(
                "document_category",
                "unknown",
            )
        ).strip().lower()

        subtype = str(
            value.get(
                "document_subtype",
                "unknown",
            )
        ).strip().lower()

        category = DocumentTaxonomyRegistry.normalize_family(category)
        subtype = DocumentTaxonomyRegistry.normalize_subtype(category, subtype)

        return {
            "document_category": category,
            "document_subtype": subtype,
            "document_type": self._legacy_document_type(
                category=category,
                subtype=subtype,
            ),
            "confidence": self._normalize_confidence(
                value.get(
                    "confidence"
                )
            ),
            "reason": str(
                value.get(
                    "reason",
                    "",
                )
            ).strip(),
        }

    def _normalize_subtype_for_category(
        self,
        category: str,
        subtype: str,
    ) -> str:
        """
        Reject subtypes that are incompatible with the category.
        """

        return DocumentTaxonomyRegistry.normalize_subtype(category, subtype)

    def _legacy_document_type(
        self,
        category: str,
        subtype: str,
    ) -> str:
        """
        Preserve existing authorization retry and extraction routing.

        Renewal-like authorization subtypes continue to use the legacy
        authorization_renewal routing value.
        """

        return DocumentTaxonomyRegistry.legacy_route(category, subtype)

    def _normalize_fields(
        self,
        fields: Any,
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(
            fields,
            dict,
        ):
            fields = {}

        normalized_fields: dict[str, dict[str, Any]] = {}

        for field_name in self.FIELD_NAMES:
            field_result = fields.get(
                field_name,
                {},
            )

            if not isinstance(
                field_result,
                dict,
            ):
                field_result = {}

            value = field_result.get(
                "value"
            )

            confidence = self._normalize_confidence(
                field_result.get(
                    "confidence"
                )
            )

            source_text = str(
                field_result.get(
                    "source_text",
                    "",
                )
                or ""
            ).strip()

            value = self._normalize_field_value(
                field_name=field_name,
                value=value,
            )

            if self._is_empty_value(
                value
            ):
                value = None
                confidence = 0.0
                source_text = ""

            normalized_fields[field_name] = {
                "value": value,
                "confidence": confidence,
                "source_text": source_text,
            }

        return normalized_fields

    def _normalize_service_lines(
        self,
        service_lines: Any,
    ) -> list[dict[str, Any]]:
        """
        Normalize optional row-level authorization service data.

        This method performs structural normalization only. It does not
        interpret service codes, modifiers, quantities, or approval.
        """

        if not isinstance(
            service_lines,
            list,
        ):
            return []

        normalized_service_lines: list[dict[str, Any]] = []

        for service_line in service_lines:
            if not isinstance(
                service_line,
                dict,
            ):
                continue

            normalized_line = {
                "service_code": self._normalize_optional_string(
                    service_line.get(
                        "service_code"
                    )
                ),
                "modifier": self._normalize_optional_string(
                    service_line.get(
                        "modifier"
                    )
                ),
                "quantity": self._normalize_optional_value(
                    service_line.get(
                        "quantity"
                    )
                ),
                "start_date": self._normalize_optional_string(
                    service_line.get(
                        "start_date"
                    )
                ),
                "end_date": self._normalize_optional_string(
                    service_line.get(
                        "end_date"
                    )
                ),
                "status": self._normalize_optional_string(
                    service_line.get(
                        "status"
                    )
                ),
                "confidence": self._normalize_confidence(
                    service_line.get(
                        "confidence"
                    )
                ),
                "source_text": str(
                    service_line.get(
                        "source_text",
                        "",
                    )
                    or ""
                ).strip(),
            }

            has_row_value = any(
                normalized_line[field_name] is not None
                for field_name in (
                    "service_code",
                    "modifier",
                    "quantity",
                    "start_date",
                    "end_date",
                    "status",
                )
            )

            if not has_row_value:
                continue

            normalized_service_lines.append(
                normalized_line
            )

        return normalized_service_lines

    def _normalize_field_value(
        self,
        field_name: str,
        value: Any,
    ) -> Any:
        """
        Apply safe structural normalization without interpreting
        healthcare business meaning.
        """

        if field_name in {
            "service_codes",
            "authorized_units",
        }:
            return self._deduplicate_list(
                value
            )

        if field_name == "diagnosis_code":
            normalized = self._deduplicate_list(
                value
            )

            if normalized is None:
                return None

            if len(normalized) == 1:
                return normalized[0]

            return normalized

        if field_name in {
            "service_code",
            "service_description",
            "modifier",
            "start_date",
            "end_date",
            "posted_date",
            "renewal_qualifier",
            "member_dob",
            "request_type",
            "approved_visits",
        }:
            if isinstance(
                value,
                list,
            ):
                normalized_values = self._deduplicate_list(
                    value
                )

                if (
                    normalized_values is not None
                    and len(normalized_values) == 1
                ):
                    return normalized_values[0]

            return value

        return value

    def _deduplicate_list(
        self,
        value: Any,
    ) -> list[Any] | None:
        if value is None:
            return None

        values = (
            value
            if isinstance(
                value,
                list,
            )
            else [value]
        )

        normalized_values: list[Any] = []

        for item in values:
            if isinstance(
                item,
                str,
            ):
                item = item.strip()

            if self._is_empty_value(
                item
            ):
                continue

            if item not in normalized_values:
                normalized_values.append(
                    item
                )

        if not normalized_values:
            return None

        return normalized_values

    def _normalize_optional_string(
        self,
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = str(
            value
        ).strip()

        if not normalized_value:
            return None

        return normalized_value

    def _normalize_optional_value(
        self,
        value: Any,
    ) -> Any:
        if isinstance(
            value,
            str,
        ):
            normalized_value = value.strip()

            if not normalized_value:
                return None

            return normalized_value

        return value

    def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        seed: int,
    ) -> dict:
        endpoint = (
            f"{self.base_url}"
            f"{self.CHAT_ENDPOINT}"
        )

        self._last_request_metrics = {}

        payload = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "options": {
                "temperature": 0,
                "seed": seed,
            },
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.ConnectionError as ex:
            raise RuntimeError(
                "Unable to connect to the local Ollama server at "
                f"{self.base_url}."
            ) from ex

        except requests.Timeout as ex:
            raise RuntimeError(
                "The local Ollama request timed out after "
                f"{self.timeout} seconds."
            ) from ex

        except requests.HTTPError as ex:
            detail = self._get_error_detail(
                response
            )

            raise RuntimeError(
                "Ollama returned an HTTP error: "
                f"{response.status_code}. {detail}"
            ) from ex

        except requests.RequestException as ex:
            raise RuntimeError(
                f"Ollama request failed: {ex}"
            ) from ex

        try:
            response_payload = response.json()
        except ValueError as ex:
            raise RuntimeError(
                "Ollama returned a response that was not valid JSON."
            ) from ex

        if not isinstance(
            response_payload,
            dict,
        ):
            raise RuntimeError(
                "Ollama response payload must be a JSON object."
            )

        self._last_request_metrics = self._extract_safe_metrics(
            response_payload
        )

        message = response_payload.get(
            "message"
        )

        if not isinstance(
            message,
            dict,
        ):
            raise RuntimeError(
                "Ollama response did not contain a message object."
            )

        content = message.get(
            "content"
        )

        if (
            not isinstance(
                content,
                str,
            )
            or not content.strip()
        ):
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        try:
            parsed_content = json.loads(
                content
            )
        except json.JSONDecodeError as ex:
            raise RuntimeError(
                "Ollama returned content that was not valid "
                "structured JSON."
            ) from ex

        if not isinstance(
            parsed_content,
            dict,
        ):
            raise RuntimeError(
                "Ollama structured output must be a JSON object."
            )

        return parsed_content

    def _extract_safe_metrics(
        self,
        response_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract only PHI-safe timing and generation metadata.
        """

        metrics: dict[str, Any] = {}

        for field_name in self.SAFE_METRIC_FIELDS:
            value = response_payload.get(
                field_name
            )

            if isinstance(
                value,
                (
                    bool,
                    int,
                    float,
                    str,
                ),
            ):
                metrics[field_name] = value

        for duration_field in (
            "total_duration",
            "load_duration",
            "prompt_eval_duration",
            "eval_duration",
        ):
            duration_value = metrics.get(
                duration_field
            )

            if isinstance(
                duration_value,
                (
                    int,
                    float,
                ),
            ):
                metrics[
                    f"{duration_field}_seconds"
                ] = (
                    float(
                        duration_value
                    )
                    / 1_000_000_000
                )

        eval_count = metrics.get(
            "eval_count"
        )

        eval_duration_seconds = metrics.get(
            "eval_duration_seconds"
        )

        if (
            isinstance(
                eval_count,
                int,
            )
            and eval_count >= 0
            and isinstance(
                eval_duration_seconds,
                float,
            )
            and eval_duration_seconds > 0
        ):
            metrics[
                "generation_tokens_per_second"
            ] = (
                eval_count
                / eval_duration_seconds
            )

        return metrics

    def _validate_text(
        self,
        text: str,
    ) -> str:
        cleaned_text = str(
            text or ""
        ).strip()

        if not cleaned_text:
            raise ValueError(
                "OCR text is required for Ollama processing."
            )

        return cleaned_text

    def _normalize_confidence(
        self,
        value: Any,
    ) -> float:
        try:
            confidence = float(
                value
            )
        except (TypeError, ValueError):
            return 0.0

        if confidence > 1:
            confidence = (
                confidence / 100
            )

        return max(
            0.0,
            min(
                confidence,
                1.0,
            ),
        )

    def _is_empty_value(
        self,
        value: Any,
    ) -> bool:
        if value is None:
            return True

        if isinstance(
            value,
            str,
        ):
            return not value.strip()

        if isinstance(
            value,
            list,
        ):
            return len(value) == 0

        return False

    def _normalize_attempt(
        self,
        attempt: Any,
    ) -> int:
        """
        Normalize an extraction attempt into a positive integer.

        Invalid, boolean, zero, and negative values default to attempt 1.
        """

        if isinstance(
            attempt,
            bool,
        ):
            return 1

        try:
            normalized_attempt = int(
                attempt
            )
        except (TypeError, ValueError):
            return 1

        if normalized_attempt < 1:
            return 1

        return normalized_attempt

    def _seed_for_attempt(
        self,
        attempt: Any,
    ) -> int:
        """
        Return the deterministic seed for an extraction attempt.

        Attempt 1 uses the configured base seed. Later attempts use a
        stable offset while temperature remains zero.
        """

        normalized_attempt = self._normalize_attempt(
            attempt
        )

        return (
            self.seed
            + (
                normalized_attempt - 1
            )
            * self.RETRY_SEED_OFFSET
        )

    def _load_timeout(self) -> int:
        raw_timeout = os.getenv(
            "OLLAMA_TIMEOUT_SECONDS",
            "600",
        )

        try:
            timeout = int(
                raw_timeout
            )
        except ValueError:
            timeout = 600

        return max(
            timeout,
            30,
        )

    def _load_seed(self) -> int:
        """
        Load a fixed Ollama generation seed.

        A fixed seed improves repeatability while remaining configurable
        for controlled local testing.
        """

        raw_seed = os.getenv(
            "OLLAMA_SEED",
            str(
                self.DEFAULT_SEED
            ),
        )

        try:
            return int(
                raw_seed
            )
        except ValueError:
            return self.DEFAULT_SEED

    def _get_error_detail(
        self,
        response: requests.Response,
    ) -> str:
        try:
            payload = response.json()

            if isinstance(
                payload,
                dict,
            ):
                error_message = payload.get(
                    "error"
                )

                if error_message:
                    return str(
                        error_message
                    )
        except ValueError:
            pass

        return response.text.strip()
