"""Local correction analysis and PHI-safe implementation-task assembly."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from src.ai.llm.providers.ollama_provider import OllamaProvider
from src.services.document_processor_training_contracts import (
    ANALYSIS_CONTRACT_VERSION,
    AFFECTED_FIELDS,
    CORRECTION_TYPES,
    IMPLEMENTATION_LAYERS,
    CorrectionAnalysis,
    local_analysis_schema,
    validate_analysis,
)


@dataclass(frozen=True, repr=False)
class PhiSafeImplementationTask:
    schema_version: int
    task_id: str
    proposal_generation: int
    business_context_version: int
    analysis_contract_version: int
    primary_correction_type: str
    related_correction_types: tuple[str, ...]
    affected_fields: tuple[str, ...]
    desired_behavior: str
    behavior_code: str
    technical_disposition: str
    likely_layers: tuple[str, ...]
    generalized_business_concepts: tuple[str, ...]
    shared_context_assessment_required: bool
    synthetic_regression_requirements: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    phi_prohibitions: tuple[str, ...]


class LocalCorrectionAnalysisService:
    """Invoke only the approved local provider and validate its structure."""

    def __init__(self, *, provider: OllamaProvider | None = None) -> None:
        self.provider = provider or OllamaProvider()

    def analyze(self, *, protected_context: dict[str, Any]) -> CorrectionAnalysis:
        try:
            result = self.provider.analyze_correction_context(
                protected_context, schema=local_analysis_schema()
            )
        except Exception:
            return self._fallback("provider_failed")
        try:
            analysis = CorrectionAnalysis(
                primary_correction_type=result.get("primary_correction_type"),
                related_correction_types=tuple(
                    result.get("related_correction_types", ())
                ),
                affected_fields=tuple(result.get("affected_fields", ())),
                behavior_code=result.get("behavior_code"),
                desired_behavior="",
                likely_layers=tuple(result.get("likely_layers", ())),
                desired_behavior_sufficient=result.get("desired_behavior_sufficient"),
                technical_disposition=result.get("technical_disposition"),
                feedback_relationship=result.get("feedback_relationship"),
                observed_failure_type=result.get("observed_failure_type"),
                affected_document_category=result.get("affected_document_category"),
                desired_intake_subtype=result.get("desired_intake_subtype"),
                required_filename_components=tuple(
                    result.get("required_filename_components", ())
                ),
                excluded_filename_components=tuple(
                    result.get("excluded_filename_components", ())
                ),
            )
            return validate_analysis(analysis)
        except (TypeError, ValueError) as error:
            category = self._validation_category(error)
            return self._fallback(category)

    @staticmethod
    def _validation_category(error: Exception) -> str:
        safe = str(error)
        if "correction_type" in safe:
            return "taxonomy_invalid"
        if "field" in safe:
            return "field_invalid"
        if "layer" in safe or "technical_disposition" in safe:
            return "layer_invalid"
        return "schema_invalid"

    @staticmethod
    def _fallback(category: str) -> CorrectionAnalysis:
        return CorrectionAnalysis(
            primary_correction_type="Needs Investigation",
            related_correction_types=(),
            affected_fields=(),
            behavior_code="needs_investigation",
            desired_behavior="More reviewer information is required before a correction can be proposed.",
            likely_layers=("Needs Investigation",),
            desired_behavior_sufficient=False,
            technical_disposition="Needs Investigation",
            feedback_relationship="Insufficient",
            observed_failure_type="Other",
            affected_document_category="not_applicable",
            desired_intake_subtype="not_applicable",
            required_filename_components=(),
            excluded_filename_components=(),
            analysis_outcome_category=category,
        )


class PhiSafeImplementationTaskService:
    """Build a Codex task only from controlled, non-free-text structures."""

    SCHEMA_VERSION = 2

    def build(
        self,
        *,
        opaque_case_id: str,
        proposal_generation: int,
        business_context_version: int,
        analysis: CorrectionAnalysis,
    ) -> PhiSafeImplementationTask:
        validated = validate_analysis(analysis)
        if (
            not isinstance(opaque_case_id, str)
            or len(opaque_case_id) != 64
            or any(value not in "0123456789abcdef" for value in opaque_case_id)
            or isinstance(proposal_generation, bool)
            or not isinstance(proposal_generation, int)
            or proposal_generation <= 0
        ):
            raise ValueError("implementation_task_identity_invalid")
        desired = validated.desired_behavior
        task_id = hashlib.sha256(
            f"{opaque_case_id}:{proposal_generation}".encode("ascii")
        ).hexdigest()
        fields = validated.affected_fields
        regressions = (
            "Add synthetic deterministic coverage for the corrected structural behavior.",
            "Prove unsupported or absent evidence remains null-safe and review-safe.",
            "Run focused tests before affected integration and idempotency regressions.",
        )
        acceptance = (
            "The behavior matches the approved structural correction.",
            "No real patient document, value, comment, identifier, or filename enters tests or output.",
            "Compilation, focused tests, affected regressions, tracker, and Git safety checks pass.",
            "Commit and push occur only after every safety gate passes.",
        )
        task = PhiSafeImplementationTask(
            schema_version=self.SCHEMA_VERSION,
            task_id=task_id,
            proposal_generation=proposal_generation,
            business_context_version=business_context_version,
            analysis_contract_version=ANALYSIS_CONTRACT_VERSION,
            primary_correction_type=validated.primary_correction_type,
            related_correction_types=validated.related_correction_types,
            affected_fields=fields,
            desired_behavior=desired,
            behavior_code=validated.behavior_code,
            technical_disposition=validated.technical_disposition,
            likely_layers=validated.likely_layers,
            generalized_business_concepts=tuple(
                item for item in dict.fromkeys((
                    validated.affected_document_category,
                    validated.desired_intake_subtype,
                    *validated.required_filename_components,
                    *validated.excluded_filename_components,
                ))
                if item not in {"unknown", "not_applicable"}
            ),
            shared_context_assessment_required=True,
            synthetic_regression_requirements=regressions,
            acceptance_criteria=acceptance,
            phi_prohibitions=(
                "Do not access or expose Smartsheet rows, comments, documents, OCR text, or protected state.",
                "Do not include patient values, row IDs, filenames, payloads, credentials, or tokens.",
                "Do not run live mailbox, OCR, Ollama, Smartsheet, or document-processing operations.",
            ),
        )
        self.validate(task)
        return task

    @staticmethod
    def validate(task: Any) -> None:
        if not isinstance(task, PhiSafeImplementationTask) or task.schema_version != 2:
            raise ValueError("implementation_task_invalid")
        if task.primary_correction_type not in CORRECTION_TYPES:
            raise ValueError("implementation_task_correction_type_invalid")
        if any(value not in CORRECTION_TYPES for value in task.related_correction_types):
            raise ValueError("implementation_task_related_type_invalid")
        if (
            isinstance(task.business_context_version, bool)
            or not isinstance(task.business_context_version, int)
            or task.business_context_version <= 0
            or task.analysis_contract_version != ANALYSIS_CONTRACT_VERSION
        ):
            raise ValueError("implementation_task_version_invalid")
        if any(field not in AFFECTED_FIELDS for field in task.affected_fields):
            raise ValueError("implementation_task_field_invalid")
        if any(layer not in IMPLEMENTATION_LAYERS for layer in task.likely_layers):
            raise ValueError("implementation_task_layer_invalid")
        if task.shared_context_assessment_required is not True:
            raise ValueError("implementation_task_context_assessment_invalid")
        serialized = json.dumps(asdict(task), sort_keys=True, separators=(",", ":"))
        prohibited = (
            "row_id", "sheet_id", "comment_text", "source_text", "document_path",
            "attachment_name", "patient_value", "member_value", "request_payload",
        )
        if any(marker in serialized.lower() for marker in prohibited):
            raise ValueError("implementation_task_protected_field_detected")


def serialize_phi_safe_task(task: PhiSafeImplementationTask) -> str:
    PhiSafeImplementationTaskService.validate(task)
    return json.dumps(asdict(task), sort_keys=True, separators=(",", ":"))
