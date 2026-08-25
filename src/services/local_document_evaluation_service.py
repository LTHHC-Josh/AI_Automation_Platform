from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from math import isfinite
import os
from pathlib import Path
from re import fullmatch
from typing import Any, Callable, Protocol, TextIO

from src.ai import config
from src.ai.ocr.errors import OCRCacheOnlyMissError
from src.document_processing.document_processor import (
    DocumentProcessor,
)
from src.models.document import Document
from src.models.learning_document_evidence import LearningDocumentEvidence
from src.models.ocr_document import OCRDocument
from src.services.review_decision_service import (
    ReviewDecisionService,
)
from src.services.local_protected_review_errors import (
    ProtectedReviewUnavailableError,
)
from src.services.local_document_learning_report_service import (
    LocalDocumentLearningReportService,
)
from src.services.learning_evidence_grounding_service import (
    LearningEvidenceGroundingService,
)
from src.services.document_fingerprint_service import (
    DocumentFingerprintService,
)
from src.services.local_document_source_recency_service import (
    LocalDocumentSourceRecencyService,
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


class LocalProtectedDocumentSelector(Protocol):
    """Local-only selector that must not emit or persist candidate paths."""

    def select(
        self,
        candidates: tuple[tuple[int, Path], ...],
    ) -> int | None:
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
class LocalDocumentListItem:
    index: int
    relative_order: str
    file_type: str
    cached_ocr_available: bool

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "relative_order": self.relative_order,
            "file_type": self.file_type,
            "cached_ocr_available": self.cached_ocr_available,
        }


@dataclass(frozen=True)
class LocalDocumentListResult:
    success: bool
    failure_category: str | None
    candidate_count: int
    documents: tuple[LocalDocumentListItem, ...] = ()

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "failure_category": self.failure_category,
            "candidate_count": self.candidate_count,
            "documents": [item.to_safe_dict() for item in self.documents],
        }


@dataclass(frozen=True)
class LocalDocumentSelectionResult:
    success: bool
    selection_status: str
    selected_index: int | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "selection_status": self.selection_status,
            "selected_index": self.selected_index,
        }


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
    ocr_diagnostics: dict[str, Any] = field(default_factory=dict)
    known_contract_pass: bool | None = None
    cache_only_enforced: bool = True
    processing_stdout_suppressed: bool = True
    processing_stderr_suppressed: bool = True
    protected_values_suppressed: bool = True
    external_integrations_invoked: bool = False
    protected_review_requested: bool = False
    protected_review_handoff_completed: bool = False
    protected_review_status: str = "not_requested"
    learning_report_requested: bool = False
    learning_report_status: str = "not_requested"
    learning_report: dict[str, Any] | None = None

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
            "ocr_diagnostics": dict(self.ocr_diagnostics),
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
            "learning_report_requested": self.learning_report_requested,
            "learning_report_status": self.learning_report_status,
            "learning_report": (
                dict(self.learning_report)
                if isinstance(self.learning_report, dict)
                else None
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

    DEFAULT_SELECTION_SNAPSHOT_PATH = Path(
        "data/ocr_cache/.local_document_selection_snapshot.json"
    )
    DEFAULT_OCR_CACHE_DIRECTORY = Path("data/ocr_cache")

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
        learning_analysis_factory: (
            Callable[[Document, Any], Any] | None
        ) = None,
        selection_snapshot_path: str | Path | None = (
            DEFAULT_SELECTION_SNAPSHOT_PATH
        ),
        ocr_cache_directory: str | Path = DEFAULT_OCR_CACHE_DIRECTORY,
        fingerprint_service: Any | None = None,
        source_recency_service: Any | None = None,
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
        self._learning_analysis_factory = learning_analysis_factory
        self._selection_snapshot_path = (
            Path(selection_snapshot_path)
            if selection_snapshot_path is not None
            else None
        )
        self._ocr_cache_directory = Path(ocr_cache_directory)
        self._fingerprint_service = (
            fingerprint_service
            if fingerprint_service is not None
            else DocumentFingerprintService()
        )
        self._source_recency_service = (
            source_recency_service
            if source_recency_service is not None
            else LocalDocumentSourceRecencyService()
        )

    def list_documents(self) -> LocalDocumentListResult:
        candidates = self._document_candidates()
        if candidates is None:
            return LocalDocumentListResult(
                success=False,
                failure_category="document_listing_unavailable",
                candidate_count=0,
            )

        snapshot_entries = self._snapshot_entries(candidates)
        if snapshot_entries is None or not self._write_selection_snapshot(
            snapshot_entries
        ):
            return LocalDocumentListResult(
                success=False,
                failure_category="document_listing_unavailable",
                candidate_count=0,
            )

        items = tuple(
            LocalDocumentListItem(
                index=index,
                relative_order=self._relative_order_label(
                    index
                ),
                file_type=path.suffix.lower().lstrip("."),
                cached_ocr_available=self._cache_exists(
                    path,
                    snapshot_entries[index - 1]["fingerprint"],
                ),
            )
            for index, path in enumerate(candidates, start=1)
        )

        return LocalDocumentListResult(
            success=True,
            failure_category=None,
            candidate_count=len(items),
            documents=items,
        )

    def select_document(
        self,
        selector: LocalProtectedDocumentSelector,
    ) -> LocalDocumentSelectionResult:
        candidates = self._document_candidates()
        if candidates is None:
            return LocalDocumentSelectionResult(
                success=False,
                selection_status="unavailable",
                selected_index=None,
            )

        snapshot_entries = self._snapshot_entries(candidates)
        if snapshot_entries is None or not self._write_selection_snapshot(
            snapshot_entries
        ):
            return LocalDocumentSelectionResult(
                success=False,
                selection_status="unavailable",
                selected_index=None,
            )

        try:
            selected_index = selector.select(
                tuple(
                    (index, path)
                    for index, path in enumerate(candidates, start=1)
                )
            )
        except Exception:
            return LocalDocumentSelectionResult(
                success=False,
                selection_status="unavailable",
                selected_index=None,
            )

        if selected_index is None:
            return LocalDocumentSelectionResult(
                success=False,
                selection_status="cancelled",
                selected_index=None,
            )

        valid_indexes = range(1, len(candidates) + 1)
        if (
            not isinstance(selected_index, int)
            or isinstance(selected_index, bool)
            or selected_index not in valid_indexes
        ):
            return LocalDocumentSelectionResult(
                success=False,
                selection_status="invalid_selection",
                selected_index=None,
            )

        if not self._write_selection_snapshot(
            snapshot_entries,
            selected_index=selected_index,
        ):
            return LocalDocumentSelectionResult(
                success=False,
                selection_status="unavailable",
                selected_index=None,
            )

        return LocalDocumentSelectionResult(
            success=True,
            selection_status="selected",
            selected_index=selected_index,
        )

    def evaluate(
        self,
        *,
        document_index: int | None,
        run_type: str,
        authorize_cached_ocr_access: bool,
        authorize_local_ollama: bool,
        authorize_local_ocr: bool = False,
        known_contract_pass: bool | None = None,
        include_learning_report: bool = False,
    ) -> LocalDocumentEvaluationResult:
        learning_report_requested = include_learning_report is True
        blocked_learning_status = (
            "blocked" if learning_report_requested else "not_requested"
        )
        cache_only_enforced = authorize_local_ocr is not True

        normalized_run_type = self.normalize_run_type(
            run_type
        )

        if normalized_run_type is None:
            return self._failure(
                run_type="",
                category="invalid_run_type",
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
            )

        if (
            not isinstance(document_index, int)
            or isinstance(document_index, bool)
            or document_index < 1
        ):
            return self._failure(
                run_type=normalized_run_type,
                category="invalid_document_selector",
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
            )

        if authorize_cached_ocr_access is not True:
            return self._failure(
                run_type=normalized_run_type,
                category=(
                    "protected_document_access_not_authorized"
                ),
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
            )

        if authorize_local_ollama is not True:
            return self._failure(
                run_type=normalized_run_type,
                category="local_ollama_not_authorized",
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
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
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
            )

        selected_path, selection_changed = self._select_document(
            document_index
        )

        if selection_changed:
            return self._failure(
                run_type=normalized_run_type,
                category="document_selection_changed",
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
            )

        if selected_path is None:
            return self._failure(
                run_type=normalized_run_type,
                category="document_selection_unavailable",
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
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
                    ocr_cache_only=cache_only_enforced,
                )

        except OCRCacheOnlyMissError:
            return self._failure(
                run_type=normalized_run_type,
                category="ocr_cache_unavailable",
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
            )
        except Exception:
            return self._failure(
                run_type=normalized_run_type,
                category="local_processing_failed",
                cache_only_enforced=cache_only_enforced,
                learning_report_requested=learning_report_requested,
                learning_report_status=blocked_learning_status,
            )

        learning_report = None
        learning_report_status = "not_requested"
        if include_learning_report is True:
            try:
                with redirect_stdout(discard_stdout), redirect_stderr(discard_stderr):
                    modeled_fields = getattr(
                        getattr(getattr(processor, "llm", None), "provider", None),
                        "FIELD_NAMES",
                        (),
                    )
                    if self._learning_analysis_factory is not None:
                        structural_analysis = self._learning_analysis_factory(
                            document,
                            processor,
                        )
                    else:
                        ocr_document = (
                            document.ocr_document
                            if isinstance(document.ocr_document, OCRDocument)
                            else OCRDocument.from_flat_text(document.raw_text)
                        )
                        learning_evidence = LearningDocumentEvidence.build(
                            ocr_document,
                            modeled_fields,
                        )
                        structural_analysis = processor.llm.analyze_learning_structure(
                            learning_evidence
                        )
                        structural_analysis = LearningEvidenceGroundingService().resolve(
                            structural_analysis,
                            learning_evidence,
                        ).analysis
                    learning_report = LocalDocumentLearningReportService().build(
                        document,
                        structural_analysis,
                        modeled_field_names=modeled_fields,
                    )
                learning_report_status = "completed"
            except Exception:
                return self._failure(
                    run_type=normalized_run_type,
                    category="learning_analysis_failed",
                    cache_only_enforced=cache_only_enforced,
                    learning_report_requested=True,
                    learning_report_status="failed",
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
                    cache_only_enforced=cache_only_enforced,
                    protected_review_requested=True,
                    protected_review_status="unavailable",
                )
            except Exception:
                return self._failure(
                    run_type=normalized_run_type,
                    category="protected_review_failed",
                    cache_only_enforced=cache_only_enforced,
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
            learning_report=learning_report,
            learning_report_requested=include_learning_report is True,
            learning_report_status=learning_report_status,
            cache_only_enforced=cache_only_enforced,
        )

    def _select_document(
        self,
        document_index: int,
    ) -> tuple[Path | None, bool]:
        candidates = self._document_candidates()
        if candidates is None:
            return None, False

        if not self._selection_snapshot_matches(
            candidates,
            document_index=document_index,
        ):
            return None, True

        if document_index > len(
            candidates
        ):
            return None, False

        return candidates[document_index - 1], False

    def _document_candidates(self) -> list[Path] | None:
        try:
            paths = [
                path
                for path in self._document_directory.iterdir()
                if (
                    path.is_file()
                    and path.suffix.lower() in self.SUPPORTED_EXTENSIONS
                )
            ]
        except OSError:
            return None
        ordered: list[tuple[tuple[Any, ...], Path]] = []
        for path in paths:
            result = self._fingerprint_service.calculate(path)
            if not result.success or result.fingerprint is None:
                return None
            fingerprint = result.fingerprint
            candidate_identity = (
                self._source_recency_service.candidate_identity(path)
            )
            if candidate_identity is None:
                return None
            recency_key = self._source_recency_service.ordering_key(
                path,
                fingerprint
            )
            key = (
                (0, *recency_key, candidate_identity)
                if recency_key is not None
                else (1, fingerprint, candidate_identity)
            )
            ordered.append((key, path))
        ordered.sort(key=lambda item: item[0])
        return [path for _, path in ordered]

    def _snapshot_entries(
        self,
        candidates: list[Path],
    ) -> list[dict[str, str]] | None:
        entries: list[dict[str, str]] = []
        for path in candidates:
            result = self._fingerprint_service.calculate(path)
            if not result.success or result.fingerprint is None:
                return None
            candidate_identity = (
                self._source_recency_service.candidate_identity(path)
            )
            if candidate_identity is None:
                return None
            entries.append(
                {
                    "candidate_identity": candidate_identity,
                    "fingerprint": result.fingerprint,
                    "file_type": path.suffix.lower().lstrip("."),
                }
            )
        return entries

    def _selection_snapshot_matches(
        self,
        candidates: list[Path],
        *,
        document_index: int,
    ) -> bool:
        if self._selection_snapshot_path is None:
            return True
        try:
            if not self._selection_snapshot_path.exists():
                return True
            stored = json.loads(
                self._selection_snapshot_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError, TypeError):
            return False
        current = self._snapshot_entries(candidates)
        if current is None or not isinstance(stored, dict):
            return False
        if stored.get("version") != 4 or stored.get("candidates") != current:
            return False
        selected_index = stored.get("selected_index")
        return selected_index is None or selected_index == document_index

    def _write_selection_snapshot(
        self,
        entries: list[dict[str, str]],
        *,
        selected_index: int | None = None,
    ) -> bool:
        if self._selection_snapshot_path is None:
            return True
        temporary_path = self._selection_snapshot_path.with_suffix(".tmp")
        try:
            self._selection_snapshot_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            temporary_path.write_text(
                json.dumps(
                    {
                        "version": 4,
                        "candidates": entries,
                        "selected_index": selected_index,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
                newline="\n",
            )
            os.replace(temporary_path, self._selection_snapshot_path)
        except OSError:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False
        return True

    def _cache_exists(self, path: Path, fingerprint: str) -> bool:
        current = self._ocr_cache_directory / f"{fingerprint}.txt"
        legacy = self._ocr_cache_directory / (
            f"{self._legacy_safe_stem(path.stem)}_{fingerprint[:16]}.txt"
        )
        try:
            return any(
                cache_path.is_file() and cache_path.stat().st_size > 0
                for cache_path in (current, legacy)
            )
        except OSError:
            return False

    @staticmethod
    def _legacy_safe_stem(value: str) -> str:
        normalized = "".join(
            character if character.isalnum() or character in "-_" else "_"
            for character in value
        ).strip("_")
        return normalized or "document"

    @staticmethod
    def _relative_order_label(position: int) -> str:
        if position == 1:
            return "newest"
        if 10 <= position % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(
                position % 10,
                "th",
            )
        return f"{position}{suffix} newest"

    def _build_success(
        self,
        *,
        run_type: str,
        document: Document,
        known_contract_pass: bool | None,
        protected_review_handoff_completed: bool,
        protected_review_requested: bool,
        protected_review_status: str,
        learning_report: dict[str, Any] | None,
        learning_report_requested: bool,
        learning_report_status: str,
        cache_only_enforced: bool,
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
            ocr_diagnostics=(
                dict(processing_metrics.get("ocr_diagnostics", {}))
                if isinstance(processing_metrics.get("ocr_diagnostics"), dict)
                else {}
            ),
            known_contract_pass=(
                known_contract_pass
                if isinstance(
                    known_contract_pass,
                    bool,
                )
                else None
            ),
            cache_only_enforced=cache_only_enforced,
            protected_review_handoff_completed=(
                protected_review_handoff_completed
            ),
            protected_review_requested=(
                protected_review_requested
            ),
            protected_review_status=protected_review_status,
            learning_report=learning_report,
            learning_report_requested=learning_report_requested,
            learning_report_status=learning_report_status,
        )

    def _failure(
        self,
        *,
        run_type: str,
        category: str,
        protected_review_requested: bool = False,
        protected_review_status: str = "not_requested",
        learning_report_requested: bool = False,
        learning_report_status: str = "not_requested",
        cache_only_enforced: bool = True,
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
            learning_report_requested=learning_report_requested,
            learning_report_status=learning_report_status,
            cache_only_enforced=cache_only_enforced,
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
            | ReviewDecisionService.FORM_2067_SUBTYPES
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
