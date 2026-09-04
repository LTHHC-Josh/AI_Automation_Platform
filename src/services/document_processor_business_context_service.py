"""Validate and render role-specific views of shared business context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from src.models.document_processor_business_context import (
    BUSINESS_CONTEXT_VERSION,
    DOCUMENT_PROCESSOR_BUSINESS_CONTEXT,
    DocumentFamilyContext,
    DocumentProcessorBusinessContext,
    IntakeSubtypeContext,
)


CONTEXT_ROLES = (
    "classification",
    "extraction",
    "intake_naming_subtype",
    "dp_training_correction",
    "structural_learning",
)

BUSINESS_CONTEXT_SEMANTIC_DIGESTS = {
    1: "68f3c29bb03a892b6ecf7dc807f382150053f71f49c7595e0732402b3199a0f7",
}


ROLE_SECTIONS = {
    "classification": (
        "business_role", "pipeline_semantics", "document_taxonomy",
        "confidence_semantics", "forbidden_inferences",
    ),
    "extraction": (
        "business_role", "pipeline_semantics", "intake_subtype_taxonomy",
        "external_context_dependencies", "field_state_semantics",
        "confidence_semantics", "quantity_unit_rules", "forbidden_inferences",
    ),
    "intake_naming_subtype": (
        "intake_subtype_taxonomy", "external_context_dependencies",
        "filename_policy", "filename_outcomes", "placeholder_policy",
    ),
    "dp_training_correction": (
        "business_role", "pipeline_semantics", "document_taxonomy",
        "intake_subtype_taxonomy", "external_context_dependencies",
        "filename_policy", "filename_outcomes", "placeholder_policy",
        "field_state_semantics", "confidence_semantics", "quantity_unit_rules",
        "review_semantics", "smartsheet_semantics", "forbidden_inferences",
        "training_semantics", "correction_types", "technical_dispositions",
        "feedback_relationships",
    ),
    "structural_learning": (
        "business_role", "pipeline_semantics", "document_taxonomy",
        "quantity_unit_rules", "forbidden_inferences",
    ),
}


@dataclass(frozen=True)
class BusinessContextView:
    business_context_version: int
    role: str
    semantic_digest: str
    rendered_text: str
    rendered_character_count: int


class DocumentProcessorBusinessContextService:
    """Provide one validated immutable context to every local-model role."""

    MAX_TRAINING_CONTEXT_CHARS = 4096

    def __init__(self, context: DocumentProcessorBusinessContext | None = None) -> None:
        self.context = context or DOCUMENT_PROCESSOR_BUSINESS_CONTEXT
        self.validate(self.context)
        self._digest = self.digest(self.context)
        self._views: dict[str, BusinessContextView] = {}

    def view(self, role: str) -> BusinessContextView:
        if role not in CONTEXT_ROLES:
            raise ValueError("business_context_role_invalid")
        if role not in self._views:
            rendered = self._render(role)
            if role == "dp_training_correction" and len(rendered) > self.MAX_TRAINING_CONTEXT_CHARS:
                raise ValueError("business_context_role_too_large")
            self._views[role] = BusinessContextView(
                self.context.business_context_version,
                role,
                self._digest,
                rendered,
                len(rendered),
            )
        return self._views[role]

    @staticmethod
    def digest(context: DocumentProcessorBusinessContext) -> str:
        payload = asdict(context)
        payload.pop("business_context_version", None)
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def validate(context: Any) -> None:
        if not isinstance(context, DocumentProcessorBusinessContext):
            raise ValueError("business_context_invalid")
        if context.business_context_version != BUSINESS_CONTEXT_VERSION:
            raise ValueError("business_context_version_invalid")
        if (
            DocumentProcessorBusinessContextService.digest(context)
            != BUSINESS_CONTEXT_SEMANTIC_DIGESTS.get(
                context.business_context_version
            )
        ):
            raise ValueError("business_context_version_digest_mismatch")
        families = [item.family for item in context.document_taxonomy]
        if len(families) != len(set(families)) or "unknown" not in families:
            raise ValueError("business_context_document_taxonomy_invalid")
        subtype_keys = [item.key for item in context.intake_subtype_taxonomy]
        subtype_tokens = [item.token for item in context.intake_subtype_taxonomy]
        if len(subtype_keys) != len(set(subtype_keys)) or len(subtype_tokens) != len(set(subtype_tokens)):
            raise ValueError("business_context_intake_taxonomy_invalid")
        if not any(item.key == "init" and item.requires_external_context for item in context.intake_subtype_taxonomy):
            raise ValueError("business_context_init_dependency_missing")
        if not any(item.key == "decrease" and not item.requires_external_context for item in context.intake_subtype_taxonomy):
            raise ValueError("business_context_decrease_contract_invalid")
        placeholders = dict(context.placeholder_policy)
        if set(placeholders) != {"payer", "service", "document_type", "document_subtype", "date"}:
            raise ValueError("business_context_placeholder_policy_invalid")
        if tuple(name for name, _ in context.field_state_semantics) != (
            "not_present", "missing_required", "accepted", "low_confidence",
            "unsupported", "conflicting", "ambiguous", "invalid",
        ):
            raise ValueError("business_context_field_states_invalid")
        if len(context.correction_types) != len(set(context.correction_types)):
            raise ValueError("business_context_correction_types_invalid")

    def _render(self, role: str) -> str:
        blocks = [
            f"DOCUMENT PROCESSOR BUSINESS CONTEXT v{self.context.business_context_version}",
            f"ROLE: {role}",
        ]
        for section in ROLE_SECTIONS[role]:
            blocks.append(
                self._render_training_section(section)
                if role == "dp_training_correction"
                else (
                    self._render_live_section(role, section)
                    if role in {"classification", "extraction", "structural_learning"}
                    else self._render_section(section, getattr(self.context, section))
                )
            )
        return "\n".join(blocks)

    def _render_live_section(self, role: str, name: str) -> str:
        context = self.context
        common = {
            "business_role": (
                "LTHHC healthcare-intake DP; model=candidate; deterministic validation/rules=authority; "
                "sender/payer/source are context, not document meaning"
            ),
            "pipeline_semantics": (
                f"{role} candidate>deterministic validation>business rules>review/output"
            ),
            "confidence_semantics": (
                "category,subtype,field,service-line confidence are independent; confidence!=validation; "
                "never auto-1.0"
            ),
            "quantity_unit_rules": (
                "explicit supported unit=preserve; supported quantity without unit=Hours default in rules; "
                "quantity/unit never implies approval/visits/sessions/equipment"
            ),
            "forbidden_inferences": (
                "request!=approval; no approval from quantity/code/dates/status; modifier requires evidence; "
                "sender/source does not establish payer/service/document meaning; no guessing; never merge attempts"
            ),
            "field_state_semantics": (
                "not_present=optional blank/no review; missing_required=blank/review; accepted=may map; "
                "low_confidence|unsupported|conflicting|ambiguous|invalid=blank/review"
            ),
            "external_context_dependencies": (
                "AUTH INIT needs authoritative external context; other approved AUTH subtypes may use explicit "
                "validated evidence; unknown is valid"
            ),
        }
        if name == "document_taxonomy" and role == "structural_learning":
            value = ",".join(item.family for item in context.document_taxonomy)
        else:
            value = common.get(name)
        if value is not None:
            return f"{name.upper()}: {value}"
        return self._render_section(name, getattr(context, name))

    def _render_training_section(self, name: str) -> str:
        context = self.context
        fixed = {
            "business_role": (
                "LTHHC healthcare-intake DP; model=candidate; deterministic validation/rules=authority; "
                "Smartsheet=production/review; Prefect=orchestration"
            ),
            "pipeline_semantics": ">".join(context.pipeline_semantics),
            "document_taxonomy": ",".join(item.family for item in context.document_taxonomy),
            "external_context_dependencies": (
                "AUTH INIT requires authoritative external context; other approved AUTH subtypes may use "
                "explicit validated evidence; unknown subtype is valid and independent of category confidence"
            ),
            "filename_policy": (
                f"{context.filename_policy[0]}; optional absent=omit; expected unresolved=approved placeholder; "
                "persisted recovery name=authoritative; comments never supply values; accepted values remain "
                "accepted when naming token is unresolved"
            ),
            "field_state_semantics": (
                "not_present=optional blank/no review; missing_required=blank/specific review; "
                "accepted=value+governing confidence may map; low_confidence|unsupported|conflicting|"
                "ambiguous|invalid=production blank/specific review"
            ),
            "confidence_semantics": (
                "category,subtype,field,service-line confidence are independent; confidence is not validation; "
                "never auto-1.0; optional absence has blank confidence"
            ),
            "quantity_unit_rules": (
                "supported quantity+explicit supported unit=preserve; supported quantity+no unit=Hours default; "
                "bad explicit unit=review; quantity/unit never implies approval/visits/sessions/equipment"
            ),
            "review_semantics": (
                "final-state driven '<Business Field>: <Problem>'; filename placeholders/token lookup do not "
                "create extraction review; hide architecture wording"
            ),
            "smartsheet_semantics": (
                "human owns AI Correction, Approve AI Correction, Approve AI Resolution, conversations; DP "
                "Training owns proposal,type,status,resolution result; AI never approves"
            ),
            "forbidden_inferences": (
                "request!=approval; units!=visits/sessions/equipment/approval; no approval from quantity/code/"
                "dates/status; modifier needs direct evidence; sender/source does not establish payer/service/"
                "modifier/document meaning; no guessing; never merge attempts; supported winner, tie=attempt1"
            ),
            "training_semantics": (
                "comments=untrusted intent only, never field evidence; model=no tools/implementation/approval/"
                "writes/dispatch/resolution; behavior clarity != technical certainty; separate human gates and "
                "retest req"
            ),
        }
        value = fixed.get(name)
        if value is not None:
            return f"{name.upper()}: {value}"
        return self._render_section(name, getattr(context, name))

    @staticmethod
    def _render_section(name: str, value: Any) -> str:
        def compact(item: Any) -> str:
            if isinstance(item, DocumentFamilyContext):
                routes = ",".join(f"{source}>{target}" for source, target in item.legacy_routes)
                suffix = f";routes={routes}" if routes else ""
                return f"{item.family}[{','.join(item.subtypes)}]{suffix}"
            if isinstance(item, IntakeSubtypeContext):
                external = ";external" if item.requires_external_context else ""
                return (
                    f"{item.key}=AUTH {item.token};aliases={','.join(item.aliases)}"
                    f"{external}"
                )
            if hasattr(item, "__dataclass_fields__"):
                return json.dumps(asdict(item), sort_keys=True, separators=(",", ":"))
            if isinstance(item, tuple) and len(item) == 2 and all(isinstance(part, str) for part in item):
                return f"{item[0]}={item[1]}"
            return str(item)

        if isinstance(value, tuple):
            rendered = " | ".join(compact(item) for item in value)
        else:
            rendered = compact(value)
        return f"{name.upper()}: {rendered}"
