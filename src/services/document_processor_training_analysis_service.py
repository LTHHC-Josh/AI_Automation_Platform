"""Local correction analysis and PHI-safe implementation-task assembly."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from src.ai.llm.providers.ollama_provider import OllamaProvider
from src.services.document_processor_training_contracts import (
    AFFECTED_FIELDS,
    CORRECTION_TYPES,
    IMPLEMENTATION_LAYERS,
    CorrectionAnalysis,
    local_analysis_schema,
    safe_behavior_for_code,
    validate_analysis,
)


@dataclass(frozen=True, repr=False)
class PhiSafeImplementationTask:
    schema_version: int
    task_id: str
    proposal_generation: int
    correction_type: str
    affected_fields: tuple[str, ...]
    desired_behavior: str
    likely_layers: tuple[str, ...]
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
            analysis = CorrectionAnalysis(
                correction_type=result.get("correction_type"),
                affected_fields=tuple(result.get("affected_fields", ())),
                behavior_code=result.get("behavior_code"),
                desired_behavior=result.get("desired_behavior"),
                likely_layers=tuple(result.get("likely_layers", ())),
                information_sufficient=result.get("information_sufficient"),
            )
            return validate_analysis(analysis)
        except Exception:
            return CorrectionAnalysis(
                correction_type="Needs Investigation",
                affected_fields=(),
                behavior_code="needs_investigation",
                desired_behavior=(
                    "More reviewer information or local investigation is required "
                    "before a safe correction can be proposed."
                ),
                likely_layers=("Needs Investigation",),
                information_sufficient=False,
            )


class PhiSafeImplementationTaskService:
    """Build a Codex task only from controlled, non-free-text structures."""

    SCHEMA_VERSION = 1

    def build(
        self,
        *,
        opaque_case_id: str,
        proposal_generation: int,
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
        desired = safe_behavior_for_code(validated.behavior_code)
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
            correction_type=validated.correction_type,
            affected_fields=fields,
            desired_behavior=desired,
            likely_layers=validated.likely_layers,
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
        if not isinstance(task, PhiSafeImplementationTask) or task.schema_version != 1:
            raise ValueError("implementation_task_invalid")
        if task.correction_type not in CORRECTION_TYPES:
            raise ValueError("implementation_task_correction_type_invalid")
        if any(field not in AFFECTED_FIELDS for field in task.affected_fields):
            raise ValueError("implementation_task_field_invalid")
        if any(layer not in IMPLEMENTATION_LAYERS for layer in task.likely_layers):
            raise ValueError("implementation_task_layer_invalid")
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
