from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from src.models.document import Document
from src.services.reference_table_service import LookupResult


@dataclass(frozen=True)
class AuthorizationNamingSubtypeDefinition:
    key: str
    token: str
    aliases: tuple[str, ...]
    requires_external_context: bool = False


@dataclass(frozen=True)
class IntakeDocumentTypeResolution:
    document_type_segment: str
    document_type_status: str
    subtype_key: str = "unknown"
    subtype_display: str = ""
    subtype_status: str = "Omitted"
    subtype_source_category: str = "not_applicable"


class IntakeDocumentNamingVocabulary:
    """Canonical intake filename vocabulary; values never contain document PHI."""

    DOCUMENT_TYPE_PLACEHOLDER = "[DOCUMENT TYPE]"
    SUBTYPE_PLACEHOLDER = "[SUBTYPE]"

    TOP_LEVEL_TOKENS = {
        "authorization": "AUTH",
        "2067": "2067",
        "plan_of_care": "POC",
        "verification_of_employment": "VOE",
        "referral": "REFERRAL",
        "assessment": "ASSESSMENT",
        "approval_letter": "APPROVAL LETTER",
        "adverse_determination_letter": "ADVERSE DETERMINATION LETTER",
        "acknowledgment": "ACK",
        "3052": "3052",
        "provider_news": "PROVIDER NEWS",
        "clinical_practice_guidelines": "CLINICAL PRACTICE GUIDELINES",
        "bad_fax": "BAD FAX",
        "spam": "SPAM",
    }

    AUTHORIZATION_SUBTYPES = (
        AuthorizationNamingSubtypeDefinition(
            "init", "INIT", ("INIT", "INITIAL"), True
        ),
        AuthorizationNamingSubtypeDefinition(
            "no_change", "NO CHANGE", ("NO CHANGE",)
        ),
        AuthorizationNamingSubtypeDefinition(
            "increase", "INCREASE", ("INCREASE",)
        ),
        AuthorizationNamingSubtypeDefinition(
            "decrease", "DECREASE", ("DECREASE",)
        ),
        AuthorizationNamingSubtypeDefinition(
            "term", "TERM", ("TERM", "TERMINATION")
        ),
        AuthorizationNamingSubtypeDefinition(
            "stub", "STUB", ("STUB",)
        ),
        AuthorizationNamingSubtypeDefinition(
            "inbound", "INBOUND", ("INBOUND", "INBOUND AUTH")
        ),
        AuthorizationNamingSubtypeDefinition(
            "gap_fill", "GAP FILL", ("GAP FILL",)
        ),
        AuthorizationNamingSubtypeDefinition(
            "new_services", "NEW SVS", ("NEW SVS", "NEW SERVICES")
        ),
        AuthorizationNamingSubtypeDefinition(
            "modification_change",
            "MOD CHANGE",
            ("MOD CHANGE", "MODIFICATION CHANGE"),
        ),
        AuthorizationNamingSubtypeDefinition(
            "rpm", "RPM", ("RPM", "REMOTE PATIENT MONITORING")
        ),
        AuthorizationNamingSubtypeDefinition(
            "readmit", "READMIT", ("READMIT",)
        ),
        AuthorizationNamingSubtypeDefinition(
            "tasks_added", "TASKS ADDED", ("TASKS ADDED",)
        ),
        AuthorizationNamingSubtypeDefinition(
            "resume_services", "RESUME SVS", ("RESUME SVS", "RESUME SERVICES")
        ),
    )

    _AUTH_BY_KEY = {item.key: item for item in AUTHORIZATION_SUBTYPES}
    _AUTH_BY_ALIAS = {
        alias: item
        for item in AUTHORIZATION_SUBTYPES
        for alias in {
            item.token,
            *item.aliases,
            *(f"AUTH {value}" for value in (item.token, *item.aliases)),
            *(f"AUTHORIZATION {value}" for value in (item.token, *item.aliases)),
        }
    }

    @classmethod
    def resolve(
        cls,
        document: Any,
        *,
        authoritative_subtype: LookupResult | None = None,
        minimum_confidence: float = 0.85,
    ) -> IntakeDocumentTypeResolution:
        if not isinstance(document, Document):
            return IntakeDocumentTypeResolution(
                cls.DOCUMENT_TYPE_PLACEHOLDER, "Placeholder"
            )

        category = cls._category(document.document_category)
        if (
            document.classification_support_status == "supported"
            and category == "termination"
        ):
            if (
                document.subtype_support_status == "supported"
                and cls._category(document.document_subtype)
                == "authorization_termination"
            ):
                return IntakeDocumentTypeResolution(
                    "AUTH TERM",
                    "Ready",
                    subtype_key="term",
                    subtype_display="TERM",
                    subtype_status="Ready",
                    subtype_source_category="final_validated_classification",
                )
            return IntakeDocumentTypeResolution(
                cls.DOCUMENT_TYPE_PLACEHOLDER,
                "Placeholder",
            )
        category_supported = (
            document.classification_support_status == "supported"
            and category in cls.TOP_LEVEL_TOKENS
        )
        if not category_supported:
            return IntakeDocumentTypeResolution(
                cls.DOCUMENT_TYPE_PLACEHOLDER, "Placeholder"
            )

        category_token = cls.TOP_LEVEL_TOKENS[category]
        if category != "authorization":
            return IntakeDocumentTypeResolution(
                category_token, "Ready", subtype_status="Omitted"
            )

        stored = cls._stored_resolution(document)
        if stored is not None:
            return cls._authorization_resolution(stored, "final_validated_state")

        external = cls._definition_from_lookup(authoritative_subtype)
        if external is not None:
            return cls._authorization_resolution(external, "authoritative_context")

        evidence = document.field_evidence.get("intake_document_subtype")
        definition = cls._definition_from_evidence(
            evidence,
            minimum_confidence=minimum_confidence,
        )
        if definition is not None and not definition.requires_external_context:
            return cls._authorization_resolution(definition, "explicit_document_evidence")

        return IntakeDocumentTypeResolution(
            f"{category_token} {cls.SUBTYPE_PLACEHOLDER}",
            "Ready",
            subtype_key="unknown",
            subtype_display="unknown",
            subtype_status="Placeholder",
            subtype_source_category=(
                "external_context_required"
                if definition is not None and definition.requires_external_context
                else "unresolved"
            ),
        )

    @classmethod
    def apply(
        cls,
        document: Document,
        *,
        authoritative_subtype: LookupResult | None = None,
    ) -> IntakeDocumentTypeResolution:
        resolution = cls.resolve(
            document,
            authoritative_subtype=authoritative_subtype,
        )
        applies_to_authorization = (
            cls._category(document.document_category) == "authorization"
        )
        document.intake_document_subtype = resolution.subtype_key
        document.intake_subtype_support_status = (
            "supported" if resolution.subtype_status == "Ready" else (
                "not_applicable" if resolution.subtype_status == "Omitted" else "unknown"
            )
        )
        document.intake_subtype_source_category = resolution.subtype_source_category
        document.intake_subtype_evaluated = applies_to_authorization
        evidence = document.field_evidence.get("intake_document_subtype")
        confidence = evidence.get("confidence") if isinstance(evidence, dict) else None
        document.intake_subtype_confidence = cls._confidence(confidence)
        return resolution

    @classmethod
    def canonical_authorization_subtype(
        cls, value: Any
    ) -> AuthorizationNamingSubtypeDefinition | None:
        normalized = cls._token(value)
        return cls._AUTH_BY_KEY.get(normalized.lower()) or cls._AUTH_BY_ALIAS.get(
            normalized
        )

    @classmethod
    def validate_document_evidence(
        cls, evidence: Any, *, minimum_confidence: float = 0.85
    ) -> tuple[AuthorizationNamingSubtypeDefinition | None, str]:
        if not isinstance(evidence, dict) or evidence.get("value") in (None, ""):
            return None, "not_present"
        confidence = cls._confidence(evidence.get("confidence"))
        if confidence is None or confidence < minimum_confidence:
            return None, "low_confidence"
        definition = cls._definition_from_evidence(
            evidence, minimum_confidence=minimum_confidence
        )
        if definition is None:
            return None, "unsupported"
        if definition.requires_external_context:
            return definition, "external_context_required"
        return definition, "resolved"

    @classmethod
    def _stored_resolution(
        cls, document: Document
    ) -> AuthorizationNamingSubtypeDefinition | None:
        if document.intake_subtype_support_status != "supported":
            return None
        return cls.canonical_authorization_subtype(document.intake_document_subtype)

    @classmethod
    def _definition_from_lookup(
        cls, lookup: Any
    ) -> AuthorizationNamingSubtypeDefinition | None:
        if not isinstance(lookup, LookupResult) or not lookup.resolved:
            return None
        return cls.canonical_authorization_subtype(lookup.value)

    @classmethod
    def _definition_from_evidence(
        cls, evidence: Any, *, minimum_confidence: float
    ) -> AuthorizationNamingSubtypeDefinition | None:
        if not isinstance(evidence, dict):
            return None
        confidence = cls._confidence(evidence.get("confidence"))
        if confidence is None or confidence < minimum_confidence:
            return None
        definition = cls.canonical_authorization_subtype(evidence.get("value"))
        if definition is None:
            return None
        source = cls._token(evidence.get("source_text"))
        aliases = {
            cls._token(value)
            for value in (
                definition.token,
                *definition.aliases,
                *(f"AUTH {value}" for value in (definition.token, *definition.aliases)),
                *(f"AUTHORIZATION {value}" for value in (definition.token, *definition.aliases)),
            )
        }
        if not any(re.search(rf"\b{re.escape(alias)}\b", source) for alias in aliases):
            return None
        return definition

    @staticmethod
    def _authorization_resolution(
        definition: AuthorizationNamingSubtypeDefinition,
        source_category: str,
    ) -> IntakeDocumentTypeResolution:
        return IntakeDocumentTypeResolution(
            f"AUTH {definition.token}",
            "Ready",
            subtype_key=definition.key,
            subtype_display=definition.token,
            subtype_status="Ready",
            subtype_source_category=source_category,
        )

    @staticmethod
    def _category(value: Any) -> str:
        return str(value or "unknown").strip().lower().replace(" ", "_")

    @staticmethod
    def _token(value: Any) -> str:
        return " ".join(
            str(value or "").strip().upper().replace("_", " ").replace("-", " ").split()
        )

    @staticmethod
    def _confidence(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        if result > 1:
            result /= 100
        return result if 0 <= result <= 1 else None
