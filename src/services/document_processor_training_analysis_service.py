"""Local correction analysis and PHI-safe implementation-task assembly."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any

from src.ai.llm.providers.ollama_provider import OllamaProvider
from src.services.document_processor_training_contracts import (
    ANALYSIS_CONTRACT_VERSION,
    AFFECTED_FIELDS,
    CORRECTION_TYPES,
    EXCLUDED_FILENAME_COMPONENTS,
    FILENAME_COMPONENTS,
    IMPLEMENTATION_LAYERS,
    CorrectionAnalysis,
    local_analysis_schema,
    normalize_filename_components,
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
            result = self._merge_structural_feedback(
                result=result, protected_context=protected_context
            )
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

    @classmethod
    def _merge_structural_feedback(
        cls, *, result: Any, protected_context: dict[str, Any]
    ) -> Any:
        """Merge only controlled filename intent; never derive production values."""
        if not isinstance(result, dict) or not cls._is_filename_analysis(result):
            return result
        merged = dict(result)
        required = list(normalize_filename_components(
            merged.get("required_filename_components", ())
        ))
        excluded = list(merged.get("excluded_filename_components", ()))
        if any(item not in EXCLUDED_FILENAME_COMPONENTS for item in excluded):
            return result
        feedback = protected_context.get("prior_reviewer_feedback", ())
        entries = list(feedback) if isinstance(feedback, (tuple, list)) else []
        entries.append(protected_context.get("current_reviewer_feedback"))
        for entry in entries:
            text = entry.get("text") if isinstance(entry, dict) else None
            if not isinstance(text, str):
                continue
            for component, directive in cls._filename_component_directives(text).items():
                if directive and component not in required:
                    required.append(component)
                elif directive is False and component in required:
                    required.remove(component)
            if cls._excludes_unrelated_fields(text):
                marker = "Unrelated Extracted Fields"
                if marker not in excluded:
                    excluded.append(marker)
        merged["required_filename_components"] = [
            item for item in FILENAME_COMPONENTS if item in required
        ]
        merged["excluded_filename_components"] = excluded
        return merged

    @staticmethod
    def _is_filename_analysis(result: dict[str, Any]) -> bool:
        return (
            result.get("primary_correction_type") == "Filename"
            or result.get("observed_failure_type") in {
                "Filename Token", "Filename Missing Component",
                "Filename Unrelated Component",
            }
            or result.get("behavior_code") in {
                "correct_filename", "correct_authorization_filename_subtype",
            }
            or "Filename" in result.get("affected_fields", ())
        )

    @classmethod
    def _filename_component_directives(cls, text: str) -> dict[str, bool]:
        normalized = " ".join(text.casefold().split())
        terms = {
            "Canonical Document Type": r"(?:canonical|document\s+type|subtype|naming\s+token)",
            "Payer When Applicable": r"(?:payer|mco)",
            "Service When Applicable": r"service(?:s|\s+(?:line|code|description|name))?",
            "Supported Date Representation": r"(?:date(?:s|\s+range)?|start\s+date|end\s+date)",
        }
        positive = r"(?:include|use|using|consume|consuming|preserve|retain|add|apply|incorporate)"
        negative = r"(?:do\s+not|don't|must\s+not|should\s+not|exclude|omit|remove|never)"
        directives: dict[str, bool] = {}
        for component, term in terms.items():
            negative_patterns = (
                rf"{negative}[^.!?;]{{0,120}}\b{term}\b",
                rf"\b{term}\b[^.!?;]{{0,120}}{negative}",
            )
            negative_spans = [
                match.span()
                for pattern in negative_patterns
                for match in re.finditer(pattern, normalized)
            ]
            positive_source = list(normalized)
            for start, end in negative_spans:
                positive_source[start:end] = " " * (end - start)
            positive_text = "".join(positive_source)
            has_positive = bool(
                re.search(rf"{positive}[^.!?;]{{0,120}}\b{term}\b", positive_text)
                or re.search(rf"\b{term}\b[^.!?;]{{0,120}}{positive}", positive_text)
            )
            has_negative = bool(negative_spans)
            if has_positive:
                directives[component] = True
            elif has_negative:
                directives[component] = False
        return directives

    @staticmethod
    def _excludes_unrelated_fields(text: str) -> bool:
        normalized = " ".join(text.casefold().split())
        negative = r"(?:do\s+not|don't|must\s+not|should\s+not|exclude|omit|remove|never)"
        non_naming_field = r"(?:status|units?|days?|hours?|diagnos(?:is|es))"
        return bool(
            re.search(rf"{negative}[^.!?;]{{0,120}}\bunrelated\b", normalized)
            or re.search(rf"\bunrelated\b[^.!?;]{{0,120}}{negative}", normalized)
            or re.search(rf"{negative}[^.!?;]{{0,120}}\b{non_naming_field}\b", normalized)
            or re.search(rf"\b{non_naming_field}\b[^.!?;]{{0,120}}{negative}", normalized)
        )

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
