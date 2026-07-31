import json
import os
from typing import Any

import requests

from src.ai import config
from src.ai.llm.llm_provider import LLMProvider
from src.ai.llm.provider_registration import register_llm_provider


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
    CHAT_ENDPOINT = "/api/chat"

    DOCUMENT_TYPES = [
        "authorization",
        "authorization_renewal",
        "denial",
        "assessment",
        "plan_of_care",
        "claim",
        "unknown",
    ]

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
        "member_dob",
        "provider_name",
        "provider_npi",
        "diagnosis_code",
        "diagnosis_description",
    ]

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

    CLASSIFICATION_SCHEMA = {
        "type": "object",
        "properties": {
            "document_type": {
                "type": "string",
                "enum": DOCUMENT_TYPES,
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
            "document_type",
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
        },
        "required": [
            "fields",
        ],
        "additionalProperties": False,
        "$defs": {
            "confidenceField": CONFIDENCE_FIELD_SCHEMA,
        },
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
        )

        return self._normalize_classification(
            result
        )

    def extract(
        self,
        text: str,
        prompt: str,
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

        result = self._chat(
            system_prompt=self._extraction_prompt(),
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
        )

        return {
            "fields": self._normalize_fields(
                result.get(
                    "fields",
                    {},
                )
            ),
        }

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

    def _classification_prompt(self) -> str:
        return """
You are a local healthcare document classification service for a home
healthcare automation platform.

Classify the OCR text into exactly one document type:

- authorization
- authorization_renewal
- denial
- assessment
- plan_of_care
- claim
- unknown

CLASSIFICATION RULES

Use authorization when the document clearly communicates an approval,
authorization number, approved service lines, authorized dates, units,
visits, sessions, equipment, or service codes.

Do not assume whether an authorization is initial, renewal, extension,
continuation, or amendment when the evidence is ambiguous.

Forms may contain text for every checkbox option even when OCR cannot
determine which checkbox is selected. The presence of labels such as
"Initial Request" or "Extension/Renewal/Amendment" does not prove that
either option was selected.

Use authorization_renewal only when reliable text explicitly confirms
a renewal, continuation, extension, or amendment.

When the document is clearly an authorization but the subtype is not
reliably confirmed, classify it as authorization.

Use unknown when the document type cannot be supported by the OCR text.

Confidence must reflect the strength of the actual evidence.

Do not automatically assign 1.0 confidence.

Return only JSON matching the required schema.
""".strip()

    def _extraction_prompt(self) -> str:
        return """
You are a local healthcare structured-data extraction service for a
home healthcare automation platform.

Extract only information directly supported by the OCR text.

Never invent, infer, estimate, or complete a missing value.

Return null when a value cannot be reliably determined.

Each field must include:

- value
- confidence
- source_text

source_text must be a short exact phrase from the OCR text supporting
the extracted value.

When a value is null:

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

For Molina documents:

- "Health Plan ID" may represent the member ID.
- "Member or Medicaid ID #" may represent the member ID.
- "Reference#" may represent the authorization number.

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

DATES

Normalize reliably supported dates to YYYY-MM-DD.

Return start_date and end_date as single strings, not arrays.

Prefer dates associated with approved authorization service lines.

Do not use fax dates, submission dates, review dates, printed dates, or
request dates as authorization start or end dates unless the document
clearly identifies them as the authorized service period.

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

    def _normalize_classification(
        self,
        value: Any,
    ) -> dict:
        if not isinstance(
            value,
            dict,
        ):
            value = {}

        document_type = str(
            value.get(
                "document_type",
                "unknown",
            )
        ).strip().lower()

        if document_type not in self.DOCUMENT_TYPES:
            document_type = "unknown"

        return {
            "document_type": document_type,
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

    def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
    ) -> dict:
        endpoint = (
            f"{self.base_url}"
            f"{self.CHAT_ENDPOINT}"
        )

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