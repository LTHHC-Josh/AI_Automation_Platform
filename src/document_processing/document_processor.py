from pathlib import Path
from time import perf_counter
from typing import Any

from src.ai.llm.llm_service import LLMService
from src.ai.ocr.ocr_service import OCRService
from src.business_rules.rule_service import RuleService
from src.models.document import (
    AuthorizationServiceLine,
    Document,
)
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)
from src.services.review_decision_service import (
    ReviewDecisionService,
)
from src.services.review_output_service import (
    ReviewOutputService,
)


class DocumentProcessor:
    """
    Coordinates the complete local document-processing pipeline.

    Pipeline:

        File
          -> OCR
          -> Classification
          -> Structured Extraction Attempt 1
          -> Independent Deterministic Validation
          -> Raw and Validated Completeness Checks
          -> Optional Controlled Extraction Attempt 2
          -> Independent Deterministic Validation
          -> Deterministic Candidate Selection
          -> Business Rules
          -> Human Review Decision
          -> Document

    Extraction candidates are never merged. When a retry occurs, each
    candidate is validated independently and the stronger supported
    candidate is selected as one complete result.
    """

    SERVICE_LINE_FIELDS = (
        "service_code",
        "modifier",
        "quantity",
        "start_date",
        "end_date",
        "status",
    )

    RETRY_CONTEXT_FIELDS = (
        "modifier",
        "start_date",
        "end_date",
        "status",
    )

    SCORE_TOP_LEVEL_FIELDS = (
        "authorization_status",
        "service_code",
        "service_codes",
        "modifier",
        "authorized_units",
        "approved_visits",
        "start_date",
        "end_date",
    )

    AUTHORIZATION_DOCUMENT_TYPES = {
        "authorization",
        "authorization_renewal",
    }

    def __init__(self) -> None:
        self.ocr = OCRService()
        self.llm = LLMService()
        self.evidence_validation = EvidenceValidationService()
        self.rules = RuleService()
        self.review_decisions = ReviewDecisionService()
        self.review_outputs = ReviewOutputService()

    def process(
        self,
        file_path: str | Path,
        *,
        ocr_cache_only: bool = False,
    ) -> Document:
        """
        Process a document through the complete local pipeline.
        """

        total_started_at = perf_counter()

        normalized_path = Path(
            file_path
        )

        if not normalized_path.exists():
            raise FileNotFoundError(
                "Document file was not found: "
                f"{normalized_path}"
            )

        if not normalized_path.is_file():
            raise ValueError(
                "Document path is not a file: "
                f"{normalized_path}"
            )

        document = Document(
            file_path=normalized_path
        )

        ocr_started_at = perf_counter()

        if ocr_cache_only:
            document.raw_text = self.ocr.extract_text(
                normalized_path,
                cache_only=True,
            )
        else:
            document.raw_text = self.ocr.extract_text(
                normalized_path
            )

        document.processing_metrics[
            "ocr_wall_seconds"
        ] = (
            perf_counter()
            - ocr_started_at
        )

        classification_started_at = perf_counter()

        classification = self.llm.classify(
            document.raw_text
        )

        document.processing_metrics[
            "classification_wall_seconds"
        ] = (
            perf_counter()
            - classification_started_at
        )

        document.processing_metrics[
            "classification_ollama"
        ] = self._get_last_llm_metrics()

        if not isinstance(
            classification,
            dict,
        ):
            classification = {}

        document.document_category = self._normalize_classification_label(
            classification.get(
                "document_category",
                "unknown",
            )
        )

        document.document_subtype = self._normalize_classification_label(
            classification.get(
                "document_subtype",
                "unknown",
            )
        )

        document.classification_reason = str(
            classification.get(
                "reason",
                "",
            )
            or ""
        ).strip()

        document.document_type = self._normalize_classification_label(
            classification.get(
                "document_type",
                document.document_category,
            )
        )

        document.confidence = self._normalize_confidence(
            classification.get(
                "confidence",
                0.0,
            )
        )

        (
            first_result,
            first_wall_seconds,
            first_metrics,
        ) = self._run_extraction_attempt(
            text=document.raw_text,
            document_type=document.document_type,
            attempt=1,
        )

        first_candidate = self._build_validated_candidate(
            template_document=document,
            extraction_result=first_result,
        )

        extraction_attempts: list[dict[str, Any]] = [
            {
                "attempt": 1,
                "wall_seconds": first_wall_seconds,
                "validation_wall_seconds": (
                    first_candidate.processing_metrics.get(
                        "validation_wall_seconds",
                        0.0,
                    )
                ),
                "ollama": first_metrics,
            },
        ]

        raw_retry_required = self._should_retry_extraction(
            extraction_result=first_result,
            document_type=document.document_type,
        )

        validated_retry_required = (
            self._should_retry_validated_candidate(
                candidate=first_candidate,
                document_type=document.document_type,
            )
        )

        retry_required = (
            raw_retry_required
            or validated_retry_required
        )

        second_candidate: Document | None = None

        if retry_required:
            (
                second_result,
                second_wall_seconds,
                second_metrics,
            ) = self._run_extraction_attempt(
                text=document.raw_text,
                document_type=document.document_type,
                attempt=2,
            )

            second_candidate = self._build_validated_candidate(
                template_document=document,
                extraction_result=second_result,
            )

            extraction_attempts.append(
                {
                    "attempt": 2,
                    "wall_seconds": second_wall_seconds,
                    "validation_wall_seconds": (
                        second_candidate.processing_metrics.get(
                            "validation_wall_seconds",
                            0.0,
                        )
                    ),
                    "ollama": second_metrics,
                }
            )

        (
            selected_candidate,
            selected_attempt,
        ) = self._select_validated_candidate(
            first_candidate=first_candidate,
            second_candidate=second_candidate,
        )

        document.field_evidence = dict(
            selected_candidate.field_evidence
        )

        document.service_lines = list(
            selected_candidate.service_lines
        )

        document.extracted_data = dict(
            selected_candidate.extracted_data
        )

        document.field_confidences = dict(
            selected_candidate.field_confidences
        )

        document.validation_actions = list(
            selected_candidate.validation_actions
        )

        selected_validation_wall_seconds = float(
            selected_candidate.processing_metrics.get(
                "validation_wall_seconds",
                0.0,
            )
        )

        total_validation_wall_seconds = sum(
            float(
                attempt.get(
                    "validation_wall_seconds",
                    0.0,
                )
            )
            for attempt in extraction_attempts
        )

        document.processing_metrics[
            "validation_wall_seconds"
        ] = total_validation_wall_seconds

        document.processing_metrics[
            "selected_validation_wall_seconds"
        ] = selected_validation_wall_seconds

        document.processing_metrics[
            "extraction_attempt_count"
        ] = len(
            extraction_attempts
        )

        document.processing_metrics[
            "extraction_retry_triggered"
        ] = retry_required

        document.processing_metrics[
            "extraction_raw_retry_required"
        ] = raw_retry_required

        document.processing_metrics[
            "extraction_validated_retry_required"
        ] = validated_retry_required

        document.processing_metrics[
            "extraction_selected_attempt"
        ] = selected_attempt

        document.processing_metrics[
            "extraction_attempts"
        ] = extraction_attempts

        document.processing_metrics[
            "extraction_wall_seconds"
        ] = sum(
            float(
                attempt.get(
                    "wall_seconds",
                    0.0,
                )
            )
            for attempt in extraction_attempts
        )

        selected_attempt_metrics = extraction_attempts[
            selected_attempt - 1
        ].get(
            "ollama",
            {},
        )

        if isinstance(
            selected_attempt_metrics,
            dict,
        ):
            document.processing_metrics[
                "extraction_ollama"
            ] = dict(
                selected_attempt_metrics
            )
        else:
            document.processing_metrics[
                "extraction_ollama"
            ] = {}

        rules_started_at = perf_counter()

        document.rule_actions = self.rules.execute(
            document
        )

        document.processing_metrics[
            "business_rules_wall_seconds"
        ] = (
            perf_counter()
            - rules_started_at
        )

        review_started_at = perf_counter()

        review_decision = self.review_decisions.evaluate(
            document
        )

        document.processing_metrics[
            "human_review_wall_seconds"
        ] = (
            perf_counter()
            - review_started_at
        )

        document.needs_human_review = (
            review_decision.needs_human_review
        )

        document.review_status = (
            review_decision.review_status
        )

        document.review_reasons = list(
            review_decision.reasons
        )

        document.minimum_field_confidence = (
            review_decision.minimum_field_confidence
        )

        document.processing_metrics[
            "total_wall_seconds"
        ] = (
            perf_counter()
            - total_started_at
        )

        self._attach_review_output(
            document
        )

        return document

    def _attach_review_output(
        self,
        document: Document,
    ) -> None:
        """
        Attach the local structured human-review handoff.

        This packages the completed document state. It does not rerun
        extraction, validation, business rules, or review decisions.
        """

        document.review_output = self.review_outputs.build(
            document
        )

    def _run_extraction_attempt(
        self,
        text: str,
        document_type: str,
        attempt: int,
    ) -> tuple[
        dict[str, Any],
        float,
        dict[str, Any],
    ]:
        """
        Run one local extraction request and capture PHI-safe metrics.
        """

        started_at = perf_counter()

        extraction_result = self.llm.extract(
            text,
            document_type,
            attempt=attempt,
        )

        wall_seconds = (
            perf_counter()
            - started_at
        )

        if isinstance(
            extraction_result,
            dict,
        ):
            normalized_result = extraction_result
        else:
            normalized_result = {}

        return (
            normalized_result,
            wall_seconds,
            self._get_last_llm_metrics(),
        )

    def _should_retry_extraction(
        self,
        extraction_result: Any,
        document_type: str,
    ) -> bool:
        """
        Check raw extraction structure before deterministic validation.

        Retry checks apply only to authorization documents. They do not
        infer payer-specific or service-code meaning.

        Model token count alone never triggers a retry.
        """

        if not self._is_authorization_document_type(
            document_type
        ):
            return False

        if not isinstance(
            extraction_result,
            dict,
        ):
            return True

        fields = extraction_result.get(
            "fields"
        )

        if not isinstance(
            fields,
            dict,
        ):
            return True

        service_lines = extraction_result.get(
            "service_lines"
        )

        if not isinstance(
            service_lines,
            list,
        ):
            return True

        top_level_service_code = (
            self._get_extracted_field_value(
                fields=fields,
                field_name="service_code",
            )
        )

        top_level_service_codes = (
            self._get_extracted_field_value(
                fields=fields,
                field_name="service_codes",
            )
        )

        if (
            not self._is_empty_value(
                top_level_service_code
            )
            and self._is_empty_value(
                top_level_service_codes
            )
        ):
            return True

        non_empty_rows = [
            row
            for row in service_lines
            if isinstance(
                row,
                dict,
            )
            and self._service_line_mapping_has_value(
                row
            )
        ]

        if not non_empty_rows:
            return True

        for row in non_empty_rows:
            service_code = row.get(
                "service_code"
            )

            quantity = row.get(
                "quantity"
            )

            has_context = any(
                not self._is_empty_value(
                    row.get(
                        field_name
                    )
                )
                for field_name in self.RETRY_CONTEXT_FIELDS
            )

            if (
                has_context
                and self._is_empty_value(
                    service_code
                )
                and self._is_empty_value(
                    quantity
                )
            ):
                return True

        if len(
            non_empty_rows
        ) > 1:
            for row in non_empty_rows:
                if (
                    self._is_empty_value(
                        row.get(
                            "service_code"
                        )
                    )
                    or self._is_empty_value(
                        row.get(
                            "quantity"
                        )
                    )
                ):
                    return True

        return False

    def _should_retry_validated_candidate(
        self,
        candidate: Document,
        document_type: str,
    ) -> bool:
        """
        Check supported structure after deterministic validation.

        This catches raw values that appeared complete but were cleared
        because their source evidence did not support them.
        """

        if not self._is_authorization_document_type(
            document_type
        ):
            return False

        top_level_service_code = candidate.extracted_data.get(
            "service_code"
        )

        top_level_service_codes = candidate.extracted_data.get(
            "service_codes"
        )

        if (
            not self._is_empty_value(
                top_level_service_code
            )
            and self._is_empty_value(
                top_level_service_codes
            )
        ):
            return True

        non_empty_rows = [
            service_line
            for service_line in candidate.service_lines
            if self._validated_service_line_has_value(
                service_line
            )
        ]

        if not non_empty_rows:
            return True

        for service_line in non_empty_rows:
            has_service_code = (
                not self._is_empty_value(
                    service_line.service_code
                )
            )

            has_quantity = (
                not self._is_empty_value(
                    service_line.quantity
                )
            )

            has_context = any(
                not self._is_empty_value(
                    value
                )
                for value in (
                    service_line.modifier,
                    service_line.start_date,
                    service_line.end_date,
                    service_line.status,
                )
            )

            if (
                has_context
                and not has_service_code
                and not has_quantity
            ):
                return True

        if len(
            non_empty_rows
        ) > 1:
            for service_line in non_empty_rows:
                if (
                    self._is_empty_value(
                        service_line.service_code
                    )
                    or self._is_empty_value(
                        service_line.quantity
                    )
                ):
                    return True

        return False

    def _select_extraction_candidate(
        self,
        template_document: Document,
        first_result: dict[str, Any],
        second_result: dict[str, Any] | None,
    ) -> tuple[Document, int]:
        """
        Build, independently validate, and select extraction candidates.

        This method remains available for deterministic unit tests and
        other existing callers.
        """

        first_candidate = self._build_validated_candidate(
            template_document=template_document,
            extraction_result=first_result,
        )

        second_candidate: Document | None = None

        if second_result is not None:
            second_candidate = self._build_validated_candidate(
                template_document=template_document,
                extraction_result=second_result,
            )

        return self._select_validated_candidate(
            first_candidate=first_candidate,
            second_candidate=second_candidate,
        )

    def _select_validated_candidate(
        self,
        first_candidate: Document,
        second_candidate: Document | None,
    ) -> tuple[Document, int]:
        """
        Select between independently validated candidates.

        Values from separate attempts are never merged. If both
        candidates receive the same deterministic score, the first
        attempt is retained.
        """

        if second_candidate is None:
            return first_candidate, 1

        first_score = self._score_validated_candidate(
            first_candidate
        )

        second_score = self._score_validated_candidate(
            second_candidate
        )

        if second_score > first_score:
            return second_candidate, 2

        return first_candidate, 1

    def _build_validated_candidate(
        self,
        template_document: Document,
        extraction_result: dict[str, Any],
    ) -> Document:
        """
        Build and deterministically validate one extraction candidate.
        """

        candidate = Document(
            file_path=template_document.file_path,
            document_type=template_document.document_type,
            confidence=template_document.confidence,
            raw_text=template_document.raw_text,
        )

        candidate.field_evidence = self._get_field_evidence(
            extraction_result
        )

        candidate.service_lines = self._get_service_lines(
            extraction_result
        )

        self._synchronize_flat_fields(
            candidate
        )

        validation_started_at = perf_counter()

        candidate.validation_actions = (
            self.evidence_validation.validate(
                candidate
            )
        )

        candidate.processing_metrics[
            "validation_wall_seconds"
        ] = (
            perf_counter()
            - validation_started_at
        )

        return candidate

    def _score_validated_candidate(
        self,
        candidate: Document,
    ) -> tuple[int, int, int, int, int]:
        """
        Score deterministically supported extraction structure.

        The score does not interpret payer meaning and does not use
        generation length or model confidence as proof of correctness.
        """

        complete_core_rows = 0
        rows_with_service_code = 0
        rows_with_quantity = 0
        supported_row_values = 0

        for service_line in candidate.service_lines:
            has_service_code = (
                not self._is_empty_value(
                    service_line.service_code
                )
            )

            has_quantity = (
                not self._is_empty_value(
                    service_line.quantity
                )
            )

            if has_service_code:
                rows_with_service_code += 1

            if has_quantity:
                rows_with_quantity += 1

            if (
                has_service_code
                and has_quantity
            ):
                complete_core_rows += 1

            supported_row_values += sum(
                not self._is_empty_value(
                    value
                )
                for value in (
                    service_line.service_code,
                    service_line.modifier,
                    service_line.quantity,
                    service_line.start_date,
                    service_line.end_date,
                    service_line.status,
                )
            )

        supported_top_level_values = sum(
            not self._is_empty_value(
                candidate.extracted_data.get(
                    field_name
                )
            )
            for field_name in self.SCORE_TOP_LEVEL_FIELDS
        )

        return (
            complete_core_rows,
            rows_with_service_code,
            rows_with_quantity,
            supported_row_values,
            supported_top_level_values,
        )

    def _is_authorization_document_type(
        self,
        document_type: str,
    ) -> bool:
        """
        Determine whether authorization retry rules apply.
        """

        normalized_document_type = str(
            document_type or ""
        ).strip().lower()

        return (
            normalized_document_type
            in self.AUTHORIZATION_DOCUMENT_TYPES
        )

    def _get_extracted_field_value(
        self,
        fields: dict[str, Any],
        field_name: str,
    ) -> Any:
        """
        Return one raw extracted top-level field value.
        """

        field_result = fields.get(
            field_name
        )

        if isinstance(
            field_result,
            dict,
        ):
            return field_result.get(
                "value"
            )

        return field_result

    def _service_line_mapping_has_value(
        self,
        service_line: dict[str, Any],
    ) -> bool:
        """
        Determine whether a raw service-line mapping contains data.
        """

        return any(
            not self._is_empty_value(
                service_line.get(
                    field_name
                )
            )
            for field_name in self.SERVICE_LINE_FIELDS
        )

    def _validated_service_line_has_value(
        self,
        service_line: AuthorizationServiceLine,
    ) -> bool:
        """
        Determine whether a validated service line still contains data.
        """

        return any(
            not self._is_empty_value(
                value
            )
            for value in (
                service_line.service_code,
                service_line.modifier,
                service_line.quantity,
                service_line.start_date,
                service_line.end_date,
                service_line.status,
            )
        )

    def _get_last_llm_metrics(
        self,
    ) -> dict[str, Any]:
        """
        Read PHI-safe metrics from the configured local LLM provider.

        Providers that do not expose metrics return an empty dictionary.
        Existing provider interfaces remain backward compatible.
        """

        provider = getattr(
            self.llm,
            "provider",
            None,
        )

        getter = getattr(
            provider,
            "get_last_request_metrics",
            None,
        )

        if not callable(
            getter
        ):
            return {}

        try:
            metrics = getter()
        except Exception:
            return {}

        if not isinstance(
            metrics,
            dict,
        ):
            return {}

        return dict(
            metrics
        )

    def _get_field_evidence(
        self,
        extraction_result: Any,
    ) -> dict[str, dict[str, Any]]:
        """
        Preserve normalized field-level extraction evidence.
        """

        if not isinstance(
            extraction_result,
            dict,
        ):
            return {}

        fields = extraction_result.get(
            "fields"
        )

        if not isinstance(
            fields,
            dict,
        ):
            return self._convert_legacy_extraction(
                extraction_result
            )

        field_evidence: dict[str, dict[str, Any]] = {}

        for field_name, field_result in fields.items():
            normalized_field_name = str(
                field_name
            ).strip()

            if not normalized_field_name:
                continue

            if isinstance(
                field_result,
                dict,
            ):
                value = field_result.get(
                    "value"
                )

                confidence = self._normalize_confidence(
                    field_result.get(
                        "confidence",
                        0.0,
                    )
                )

                source_text = str(
                    field_result.get(
                        "source_text",
                        "",
                    )
                    or ""
                ).strip()
            else:
                value = field_result
                confidence = 0.0
                source_text = ""

            if self._is_empty_value(
                value
            ):
                value = None
                confidence = 0.0
                source_text = ""

            field_evidence[normalized_field_name] = {
                "value": value,
                "confidence": confidence,
                "source_text": source_text,
            }

        return field_evidence

    def _get_service_lines(
        self,
        extraction_result: Any,
    ) -> list[AuthorizationServiceLine]:
        """
        Preserve optional row-level authorization service data.

        The provider may return service-line rows in addition to the
        existing flat extraction fields.
        """

        if not isinstance(
            extraction_result,
            dict,
        ):
            return []

        raw_service_lines = extraction_result.get(
            "service_lines"
        )

        if not isinstance(
            raw_service_lines,
            list,
        ):
            return []

        service_lines: list[AuthorizationServiceLine] = []

        for raw_service_line in raw_service_lines:
            if not isinstance(
                raw_service_line,
                dict,
            ):
                continue

            normalized_values = {
                field_name: self._normalize_optional_value(
                    raw_service_line.get(
                        field_name
                    )
                )
                for field_name in self.SERVICE_LINE_FIELDS
            }

            has_service_data = any(
                not self._is_empty_value(
                    normalized_values[field_name]
                )
                for field_name in self.SERVICE_LINE_FIELDS
            )

            if not has_service_data:
                continue

            confidence = self._normalize_confidence(
                raw_service_line.get(
                    "confidence",
                    0.0,
                )
            )

            source_text = str(
                raw_service_line.get(
                    "source_text",
                    "",
                )
                or ""
            ).strip()

            service_lines.append(
                AuthorizationServiceLine(
                    service_code=normalized_values[
                        "service_code"
                    ],
                    modifier=normalized_values[
                        "modifier"
                    ],
                    quantity=normalized_values[
                        "quantity"
                    ],
                    start_date=normalized_values[
                        "start_date"
                    ],
                    end_date=normalized_values[
                        "end_date"
                    ],
                    status=normalized_values[
                        "status"
                    ],
                    confidence=confidence,
                    source_text=source_text,
                )
            )

        return service_lines

    def _convert_legacy_extraction(
        self,
        extraction_result: dict,
    ) -> dict[str, dict[str, Any]]:
        """
        Convert a legacy flat extraction result into evidence records.
        """

        field_evidence: dict[str, dict[str, Any]] = {}

        for field_name, value in extraction_result.items():
            if field_name == "service_lines":
                continue

            normalized_field_name = str(
                field_name
            ).strip()

            if not normalized_field_name:
                continue

            if self._is_empty_value(
                value
            ):
                value = None

            field_evidence[normalized_field_name] = {
                "value": value,
                "confidence": 0.0,
                "source_text": "",
            }

        return field_evidence

    def _synchronize_flat_fields(
        self,
        document: Document,
    ) -> None:
        """
        Preserve existing flat-field behavior for business rules.
        """

        document.extracted_data = {
            field_name: evidence.get(
                "value"
            )
            for field_name, evidence
            in document.field_evidence.items()
        }

        document.field_confidences = {
            field_name: self._normalize_confidence(
                evidence.get(
                    "confidence",
                    0.0,
                )
            )
            for field_name, evidence
            in document.field_evidence.items()
        }

    def _normalize_optional_value(
        self,
        value: Any,
    ) -> Any:
        """
        Normalize surrounding whitespace without interpreting meaning.
        """

        if isinstance(
            value,
            str,
        ):
            normalized_value = value.strip()

            if not normalized_value:
                return None

            return normalized_value

        return value

    def _normalize_classification_label(
        self,
        value: Any,
    ) -> str:
        """
        Normalize classification labels without inventing a category.
        """

        normalized = str(
            value
            or ""
        ).strip().lower()

        if not normalized:
            return "unknown"

        return normalized

    def _normalize_confidence(
        self,
        value: Any,
    ) -> float:
        """
        Normalize a confidence value into the range 0.0 through 1.0.
        """

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
        """
        Determine whether an extracted value is empty.
        """

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
            return len(
                value
            ) == 0

        return False
