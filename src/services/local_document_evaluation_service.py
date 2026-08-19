from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from pathlib import Path
from re import fullmatch
from typing import Any, Callable, Protocol, TextIO

from src.ai import config
from src.ai.ocr.errors import OCRCacheOnlyMissError
from src.document_processing.document_processor import (
    DocumentProcessor,
)
from src.models.document import Document
from src.services.review_decision_service import (
    ReviewDecisionService,
)
from src.services.local_protected_review_errors import (
    ProtectedReviewUnavailableError,
)


class LocalEvaluationExecutionClassification(Enum):
    REAL_CACHED_OCR_LOCAL_OLLAMA = (
        "real cached OCR / real local Ollama"
    )
    SYNTHETIC_MOCK = "synthetic deterministic/mock"
    NOT_COMPLETED = "not completed"


class LocalProtectedReviewConsumer(Protocol):
    """
    Local-only in-memory handoff for an approved protected review UI.

    Implementations must not log, persist, or write protected content to
    stdout or stderr. The aggregate evaluation result never contains the
    supplied document.
    """

    def review(
        self,
        document: Document,
    ) -> None:
        ...


class _DiscardingTextStream(TextIO):
    """Discard nested output without retaining protected content."""

    def write(
        self,
        value: str,
    ) -> int:
        return len(
            value
        )

    def flush(self) -> None:
        return None


@dataclass(frozen=True)
class LocalDocumentEvaluationResult:
    run_type: str
    success: bool
    execution_status: str
    failure_category: str | None
    execution_classification: str
    document_category: str = "unknown"
    document_subtype: str = "unknown"
    classification_confidence: float = 0.0
    extraction_attempt_count: int = 0
    retry_triggered: bool = False
    selected_attempt: int = 0
    final_field_count: int = 0
    service_line_count: int = 0
    low_confidence_field_count: int = 0
    low_confidence_service_line_count: int = 0
    validation_action_count: int = 0
    business_rule_action_count: int = 0
    review_required: bool = False
    review_status: str = "unknown"
    review_reason_count: int = 0
    minimum_field_confidence: float = 0.0
    stage_timings: dict[str, float] = field(
        default_factory=dict
    )
    total_timing: float = 0.0
    known_contract_pass: bool | None = None
    cache_only_enforced: bool = True
    processing_stdout_suppressed: bool = True
    processing_stderr_suppressed: bool = True
    protected_values_suppressed: bool = True
    external_integrations_invoked: bool = False
    protected_review_requested: bool = False
    protected_review_handoff_completed: bool = False
    protected_review_status: str = "not_requested"

    def to_safe_dict(
        self,
    ) -> dict[str, Any]:
        """Return only the explicit aggregate-safe result contract."""

        return {
            "run_type": self.run_type,
            "success": self.success,
            "execution_status": self.execution_status,
            "failure_category": self.failure_category,
            "execution_classification": (
                self.execution_classification
            ),
            "document_category": self.document_category,
            "document_subtype": self.document_subtype,
            "classification_confidence": (
                self.classification_confidence
            ),
            "extraction_attempt_count": (
                self.extraction_attempt_count
            ),
            "retry_triggered": self.retry_triggered,
            "selected_attempt": self.selected_attempt,
            "final_field_count": self.final_field_count,
            "service_line_count": self.service_line_count,
            "low_confidence_field_count": (
                self.low_confidence_field_count
            ),
            "low_confidence_service_line_count": (
                self.low_confidence_service_line_count
            ),
            "validation_action_count": (
                self.validation_action_count
            ),
            "business_rule_action_count": (
                self.business_rule_action_count
            ),
            "review_required": self.review_required,
            "review_status": self.review_status,
            "review_reason_count": self.review_reason_count,
            "minimum_field_confidence": (
                self.minimum_field_confidence
            ),
            "stage_timings": dict(
                self.stage_timings
            ),
            "total_timing": self.total_timing,
            "known_contract_pass": self.known_contract_pass,
            "cache_only_enforced": self.cache_only_enforced,
            "processing_stdout_suppressed": (
                self.processing_stdout_suppressed
            ),
            "processing_stderr_suppressed": (
                self.processing_stderr_suppressed
            ),
            "protected_values_suppressed": (
                self.protected_values_suppressed
            ),
            "external_integrations_invoked": (
                self.external_integrations_invoked
            ),
            "protected_review_requested": (
                self.protected_review_requested
            ),
            "protected_review_handoff_completed": (
                self.protected_review_handoff_completed
            ),
            "protected_review_status": (
                self.protected_review_status
            ),
        }


class LocalDocumentEvaluationService:
    """
    Run one explicitly authorized local, cache-only evaluation.

    Document selection and protected processing remain local. The returned
    object contains aggregate metadata only and never contains the selected
    path, source document, OCR text, extracted values, evidence, or review
    object.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp",
    }

    RUN_TYPE_PATTERN = r"[A-Za-z0-9][A-Za-z0-9 _-]{0,79}"

    STAGE_TIMING_KEYS = {
        "ocr": "ocr_wall_seconds",
        "classification": "classification_wall_seconds",
        "extraction": "extraction_wall_seconds",
        "validation": "validation_wall_seconds",
        "business_rules": "business_rules_wall_seconds",
        "review": "human_review_wall_seconds",
    }

    REVIEW_STATUSES = {
        "Verified by AI",
        "Human Review Required",
        "Human Review Recommended",
    }

    def __init__(
        self,
        *,
        document_directory: str | Path = Path(
            "data/incoming"
        ),
        processor_factory: Callable[[], Any] | None = None,
        execution_classification: (
            LocalEvaluationExecutionClassification
        ) = (
            LocalEvaluationExecutionClassification
            .REAL_CACHED_OCR_LOCAL_OLLAMA
        ),
        protected_review_consumer: (
            LocalProtectedReviewConsumer | None
        ) = None,
    ) -> None:
        self._document_directory = Path(
            document_directory
        )
        self._processor_factory = (
            processor_factory
            if processor_factory is not None
            else DocumentProcessor
        )
        self._uses_default_processor = (
            processor_factory is None
        )
        self._execution_classification = (
            execution_classification
            if isinstance(
                execution_classification,
                LocalEvaluationExecutionClassification,
            )
            else LocalEvaluationExecutionClassification.SYNTHETIC_MOCK
        )
        self._protected_review_consumer = (
            protected_review_consumer
        )

    def evaluate(
        self,
        *,
        document_index: int | None,
        run_type: str,
        authorize_cached_ocr_access: bool,
        authorize_local_ollama: bool,
        known_contract_pass: bool | None = None,
    ) -> LocalDocumentEvaluationResult:
        normalized_run_type = self.normalize_run_type(
            run_type
        )

        if normalized_run_type is None:
            return self._failure(
                run_type="",
                category="invalid_run_type",
            )

        if (
            not isinstance(document_index, int)
            or isinstance(document_index, bool)
            or document_index < 1
        ):
            return self._failure(
                run_type=normalized_run_type,
                category="invalid_document_selector",
            )

        if authorize_cached_ocr_access is not True:
            return self._failure(
                run_type=normalized_run_type,
                category=(
                    "protected_document_access_not_authorized"
                ),
            )

        if authorize_local_ollama is not True:
            return self._failure(
                run_type=normalized_run_type,
                category="local_ollama_not_authorized",
            )

        if (
            self._uses_default_processor
            and (
                config.OCR_PROVIDER != "paddle"
                or config.LLM_PROVIDER != "ollama"
            )
        ):
            return self._failure(
                run_type=normalized_run_type,
                category="local_configuration_unavailable",
            )

        selected_path = self._select_document(
            document_index
        )

        if selected_path is None:
            return self._failure(
                run_type=normalized_run_type,
                category="document_selection_unavailable",
            )

        discard_stdout = _DiscardingTextStream()
        discard_stderr = _DiscardingTextStream()

        try:
            from contextlib import (
                redirect_stderr,
                redirect_stdout,
            )

            with redirect_stdout(
                discard_stdout
            ), redirect_stderr(
                discard_stderr
            ):
                processor = self._processor_factory()
                document = processor.process(
                    selected_path,
                    ocr_cache_only=True,
                )

        except OCRCacheOnlyMissError:
            return self._failure(
                run_type=normalized_run_type,
                category="ocr_cache_unavailable",
            )
        except Exception:
            return self._failure(
                run_type=normalized_run_type,
                category="local_processing_failed",
            )

        protected_review_requested = (
            self._protected_review_consumer is not None
        )
        protected_review_handoff_completed = False
        protected_review_status = "not_requested"

        if self._protected_review_consumer is not None:
            try:
                with redirect_stdout(
                    discard_stdout
                ), redirect_stderr(
                    discard_stderr
                ):
                    self._protected_review_consumer.review(
                        document
                    )
            except ProtectedReviewUnavailableError:
                return self._failure(
                    run_type=normalized_run_type,
                    category="protected_review_unavailable",
                    protected_review_requested=True,
                    protected_review_status="unavailable",
                )
            except Exception:
                return self._failure(
                    run_type=normalized_run_type,
                    category="protected_review_failed",
                    protected_review_requested=True,
                    protected_review_status="failed",
                )

            protected_review_handoff_completed = True
            protected_review_status = "completed"

        return self._build_success(
            run_type=normalized_run_type,
            document=document,
            known_contract_pass=known_contract_pass,
            protected_review_handoff_completed=(
                protected_review_handoff_completed
            ),
            protected_review_requested=(
                protected_review_requested
            ),
            protected_review_status=protected_review_status,
        )

    def _select_document(
        self,
        document_index: int,
    ) -> Path | None:
        try:
            candidates = sorted(
                path
                for path in self._document_directory.iterdir()
                if (
                    path.is_file()
                    and path.suffix.lower()
                    in self.SUPPORTED_EXTENSIONS
                )
            )
        except OSError:
            return None

        if document_index > len(
            candidates
        ):
            return None

        return candidates[
            document_index - 1
        ]

    def _build_success(
        self,
        *,
        run_type: str,
        document: Document,
        known_contract_pass: bool | None,
        protected_review_handoff_completed: bool,
        protected_review_requested: bool,
        protected_review_status: str,
    ) -> LocalDocumentEvaluationResult:
        extracted_data = (
            document.extracted_data
            if isinstance(document.extracted_data, dict)
            else {}
        )
        field_confidences = (
            document.field_confidences
            if isinstance(document.field_confidences, dict)
            else {}
        )
        service_lines = (
            document.service_lines
            if isinstance(document.service_lines, list)
            else []
        )
        processing_metrics = (
            document.processing_metrics
            if isinstance(document.processing_metrics, dict)
            else {}
        )

        populated_fields = [
            field_name
            for field_name, value in extracted_data.items()
            if self._is_present(
                value
            )
        ]

        low_confidence_field_count = sum(
            1
            for field_name in populated_fields
            if self._safe_confidence(
                field_confidences.get(
                    field_name,
                    0.0,
                )
            )
            < ReviewDecisionService.FIELD_CONFIDENCE_THRESHOLD
        )

        low_confidence_service_line_count = sum(
            1
            for service_line in service_lines
            if (
                self._service_line_has_value(
                    service_line
                )
                and self._safe_confidence(
                    getattr(
                        service_line,
                        "confidence",
                        0.0,
                    )
                )
                < ReviewDecisionService.FIELD_CONFIDENCE_THRESHOLD
            )
        )

        stage_timings = {
            safe_name: self._safe_timing(
                processing_metrics.get(
                    metric_name,
                    0.0,
                )
            )
            for safe_name, metric_name in (
                self.STAGE_TIMING_KEYS.items()
            )
        }

        return LocalDocumentEvaluationResult(
            run_type=run_type,
            success=True,
            execution_status="completed",
            failure_category=None,
            execution_classification=(
                self._execution_classification.value
            ),
            document_category=self._safe_category(
                document.document_category
            ),
            document_subtype=self._safe_subtype(
                document.document_subtype
            ),
            classification_confidence=(
                self._safe_confidence(
                    document.confidence
                )
            ),
            extraction_attempt_count=self._safe_integer(
                processing_metrics.get(
                    "extraction_attempt_count",
                    0,
                )
            ),
            retry_triggered=(
                processing_metrics.get(
                    "extraction_retry_triggered"
                )
                is True
            ),
            selected_attempt=self._safe_integer(
                processing_metrics.get(
                    "extraction_selected_attempt",
                    0,
                )
            ),
            final_field_count=len(
                populated_fields
            ),
            service_line_count=len(
                service_lines
            ),
            low_confidence_field_count=(
                low_confidence_field_count
            ),
            low_confidence_service_line_count=(
                low_confidence_service_line_count
            ),
            validation_action_count=self._safe_length(
                document.validation_actions
            ),
            business_rule_action_count=self._safe_length(
                document.rule_actions
            ),
            review_required=(
                document.needs_human_review is True
            ),
            review_status=self._safe_review_status(
                document.review_status
            ),
            review_reason_count=self._safe_length(
                document.review_reasons
            ),
            minimum_field_confidence=(
                self._safe_confidence(
                    document.minimum_field_confidence
                )
            ),
            stage_timings=stage_timings,
            total_timing=self._safe_timing(
                processing_metrics.get(
                    "total_wall_seconds",
                    0.0,
                )
            ),
            known_contract_pass=(
                known_contract_pass
                if isinstance(
                    known_contract_pass,
                    bool,
                )
                else None
            ),
            protected_review_handoff_completed=(
                protected_review_handoff_completed
            ),
            protected_review_requested=(
                protected_review_requested
            ),
            protected_review_status=protected_review_status,
        )

    def _failure(
        self,
        *,
        run_type: str,
        category: str,
        protected_review_requested: bool = False,
        protected_review_status: str = "not_requested",
    ) -> LocalDocumentEvaluationResult:
        return LocalDocumentEvaluationResult(
            run_type=run_type,
            success=False,
            execution_status="failed",
            failure_category=category,
            execution_classification=(
                LocalEvaluationExecutionClassification
                .NOT_COMPLETED.value
            ),
            protected_review_requested=(
                protected_review_requested
            ),
            protected_review_status=protected_review_status,
        )

    @classmethod
    def normalize_run_type(
        cls,
        value: Any,
    ) -> str | None:
        if not isinstance(
            value,
            str,
        ):
            return None

        normalized = value.strip()

        if not fullmatch(
            cls.RUN_TYPE_PATTERN,
            normalized,
        ):
            return None

        return normalized

    def _safe_category(
        self,
        value: Any,
    ) -> str:
        normalized = str(
            value
            or "unknown"
        ).strip().lower()

        if normalized not in ReviewDecisionService.DOCUMENT_CATEGORIES:
            return "unknown"

        return normalized

    def _safe_subtype(
        self,
        value: Any,
    ) -> str:
        normalized = str(
            value
            or "unknown"
        ).strip().lower()
        allowed_subtypes = (
            ReviewDecisionService.AUTHORIZATION_SUBTYPES
            | ReviewDecisionService.TERMINATION_SUBTYPES
            | {
                "unknown",
            }
        )

        if normalized not in allowed_subtypes:
            return "unknown"

        return normalized

    def _safe_review_status(
        self,
        value: Any,
    ) -> str:
        if value not in self.REVIEW_STATUSES:
            return "unknown"

        return value

    def _service_line_has_value(
        self,
        service_line: Any,
    ) -> bool:
        return any(
            self._is_present(
                getattr(
                    service_line,
                    field_name,
                    None,
                )
            )
            for field_name in (
                "service_code",
                "modifier",
                "quantity",
                "start_date",
                "end_date",
                "status",
            )
        )

    def _is_present(
        self,
        value: Any,
    ) -> bool:
        if value is None:
            return False

        if isinstance(
            value,
            str,
        ):
            return bool(
                value.strip()
            )

        if isinstance(
            value,
            (list, tuple, set, dict),
        ):
            return bool(
                value
            )

        return True

    def _safe_confidence(
        self,
        value: Any,
    ) -> float:
        try:
            normalized = float(
                value
            )
        except (TypeError, ValueError):
            return 0.0

        if not isfinite(
            normalized
        ):
            return 0.0

        return max(
            0.0,
            min(
                normalized,
                1.0,
            ),
        )

    def _safe_timing(
        self,
        value: Any,
    ) -> float:
        try:
            normalized = float(
                value
            )
        except (TypeError, ValueError):
            return 0.0

        if not isfinite(
            normalized
        ):
            return 0.0

        return max(
            normalized,
            0.0,
        )

    def _safe_integer(
        self,
        value: Any,
    ) -> int:
        if isinstance(
            value,
            bool,
        ):
            return 0

        try:
            normalized = int(
                value
            )
        except (TypeError, ValueError):
            return 0

        return max(
            normalized,
            0,
        )

    def _safe_length(
        self,
        value: Any,
    ) -> int:
        if not isinstance(
            value,
            (list, tuple, set),
        ):
            return 0

        return len(
            value
        )
