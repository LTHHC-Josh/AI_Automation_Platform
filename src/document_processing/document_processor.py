from pathlib import Path
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


class DocumentProcessor:
    """
    Coordinates the complete local document-processing pipeline.

    Pipeline:

        File
          -> OCR
          -> Classification
          -> Structured Extraction
          -> Preserve Field Evidence
          -> Preserve Optional Service Lines
          -> Deterministic Evidence Validation
          -> Business Rules
          -> Human Review Decision
          -> Document
    """

    SERVICE_LINE_FIELDS = (
        "service_code",
        "modifier",
        "quantity",
        "start_date",
        "end_date",
        "status",
    )

    def __init__(self) -> None:
        self.ocr = OCRService()
        self.llm = LLMService()
        self.evidence_validation = EvidenceValidationService()
        self.rules = RuleService()
        self.review_decisions = ReviewDecisionService()

    def process(
        self,
        file_path: str | Path,
    ) -> Document:
        """
        Process a document through the complete local pipeline.
        """

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

        document.raw_text = self.ocr.extract_text(
            normalized_path
        )

        classification = self.llm.classify(
            document.raw_text
        )

        if not isinstance(
            classification,
            dict,
        ):
            classification = {}

        document.document_type = str(
            classification.get(
                "document_type",
                "unknown",
            )
        ).strip()

        document.confidence = self._normalize_confidence(
            classification.get(
                "confidence",
                0.0,
            )
        )

        extraction_result = self.llm.extract(
            document.raw_text,
            document.document_type,
        )

        document.field_evidence = self._get_field_evidence(
            extraction_result
        )

        document.service_lines = self._get_service_lines(
            extraction_result
        )

        self._synchronize_flat_fields(
            document
        )

        document.validation_actions = (
            self.evidence_validation.validate(
                document
            )
        )

        document.rule_actions = self.rules.execute(
            document
        )

        review_decision = self.review_decisions.evaluate(
            document
        )

        document.needs_human_review = (
            review_decision.needs_human_review
        )

        document.review_status = (
            review_decision.review_status
        )

        document.review_reasons = (
            review_decision.reasons
        )

        document.minimum_field_confidence = (
            review_decision.minimum_field_confidence
        )

        return document

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

        Current Ollama output does not yet include service_lines. This
        method allows the structure to be tested independently before
        the provider schema and prompt are changed.
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
            confidence = confidence / 100

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