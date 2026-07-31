from pathlib import Path
from typing import Any

from src.ai.llm.llm_service import LLMService
from src.ai.ocr.ocr_service import OCRService
from src.business_rules.rule_service import RuleService
from src.models.document import Document
from src.services.review_decision_service import (
    ReviewDecisionService,
)


class DocumentProcessor:
    """
    Coordinates the complete AI document-processing pipeline.

    Pipeline:

        File
          |
          v
        OCR
          |
          v
        Classification
          |
          v
        Structured Extraction
          |
          v
        Business Rules
          |
          v
        Human Review Decision
          |
          v
        Document
    """

    def __init__(self) -> None:
        self.ocr = OCRService()
        self.llm = LLMService()
        self.rules = RuleService()
        self.review_decisions = ReviewDecisionService()

    def process(
        self,
        file_path: str | Path,
    ) -> Document:
        """
        Process a document through the complete AI pipeline.

        Args:
            file_path: Path to the local document.

        Returns:
            Fully processed Document object.
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

        document.confidence = (
            self._normalize_confidence(
                classification.get(
                    "confidence",
                    0.0,
                )
            )
        )

        extraction_result = self.llm.extract(
            document.raw_text,
            document.document_type,
        )

        document.extracted_data = (
            self._get_extracted_data(
                extraction_result
            )
        )

        document.field_confidences = (
            self._get_field_confidences(
                extraction_result
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

    def _get_extracted_data(
        self,
        extraction_result: Any,
    ) -> dict:
        """
        Convert confidence-aware extraction output into flat data.
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
            return extraction_result

        extracted_data: dict = {}

        for field_name, field_result in fields.items():
            if isinstance(
                field_result,
                dict,
            ):
                extracted_data[field_name] = (
                    field_result.get(
                        "value"
                    )
                )
            else:
                extracted_data[field_name] = (
                    field_result
                )

        return extracted_data

    def _get_field_confidences(
        self,
        extraction_result: Any,
    ) -> dict[str, float]:
        """
        Read and normalize field-level confidence values.
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
            return {}

        field_confidences: dict[str, float] = {}

        for field_name, field_result in fields.items():
            if not isinstance(
                field_result,
                dict,
            ):
                continue

            confidence = field_result.get(
                "confidence"
            )

            if confidence is None:
                continue

            field_confidences[field_name] = (
                self._normalize_confidence(
                    confidence
                )
            )

        return field_confidences

    def _normalize_confidence(
        self,
        value: Any,
    ) -> float:
        """
        Normalize confidence into the range 0 through 1.
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