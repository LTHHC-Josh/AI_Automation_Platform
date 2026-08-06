from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from src.models.document import (
    AuthorizationServiceLine,
    Document,
)


@dataclass
class ReviewField:
    """
    Represents one extracted field in the local human-review payload.

    Values and source evidence may contain PHI and must remain inside
    approved LTHHC systems.
    """

    name: str
    value: Any = None
    confidence: float = 0.0
    source_text: str = ""


@dataclass
class ReviewServiceLine:
    """
    Represents one authorization service line for human review.

    The model preserves extracted relationships without interpreting
    the business meaning of quantity, status, modifier, or dates.
    """

    service_code: str | None = None
    modifier: str | None = None
    quantity: Any = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    confidence: float = 0.0
    source_text: str = ""


@dataclass
class ReviewOutput:
    """
    Represents the local structured human-review handoff contract.

    This output intentionally excludes raw OCR text and the local file
    path. Field and service-line source evidence is retained because it
    is required for authorized local review.
    """

    document_type: str = ""
    classification_confidence: float = 0.0
    fields: list[ReviewField] = field(
        default_factory=list
    )
    service_lines: list[ReviewServiceLine] = field(
        default_factory=list
    )
    validation_actions: list[str] = field(
        default_factory=list
    )
    rule_actions: list[str] = field(
        default_factory=list
    )
    needs_human_review: bool = False
    review_status: str = ""
    review_reasons: list[str] = field(
        default_factory=list
    )
    minimum_field_confidence: float | None = None
    extraction_attempt_count: int = 0
    extraction_retry_triggered: bool = False
    extraction_selected_attempt: int | None = None
    authorized_units_reconciled: bool = False


class ReviewOutputService:
    """
    Builds a neutral local human-review output from a processed document.

    The service does not rerun extraction, validation, business rules,
    or review-decision logic. It only packages the current processed
    document state.

    The returned object may contain PHI in field values and source_text.
    It must not be logged or transmitted outside approved LTHHC systems.
    """

    AUTHORIZED_UNITS_RECONCILIATION_ACTION = (
        "Authorized units were reconciled from supported "
        "service-line evidence"
    )

    def build(
        self,
        document: Document,
    ) -> ReviewOutput:
        """
        Build an independent review-output snapshot.

        Mutable extracted values are deep-copied so downstream review
        changes cannot mutate the processed Document.
        """

        return ReviewOutput(
            document_type=self._normalize_text(
                document.document_type
            ),
            classification_confidence=(
                self._normalize_confidence(
                    document.confidence
                )
            ),
            fields=self._build_fields(
                document
            ),
            service_lines=self._build_service_lines(
                document.service_lines
            ),
            validation_actions=self._copy_text_list(
                document.validation_actions
            ),
            rule_actions=self._copy_text_list(
                document.rule_actions
            ),
            needs_human_review=bool(
                document.needs_human_review
            ),
            review_status=self._normalize_text(
                document.review_status
            ),
            review_reasons=self._copy_text_list(
                document.review_reasons
            ),
            minimum_field_confidence=(
                self._normalize_optional_confidence(
                    document.minimum_field_confidence
                )
            ),
            extraction_attempt_count=(
                self._get_nonnegative_integer_metric(
                    document=document,
                    metric_name="extraction_attempt_count",
                )
            ),
            extraction_retry_triggered=(
                self._get_boolean_metric(
                    document=document,
                    metric_name="extraction_retry_triggered",
                )
            ),
            extraction_selected_attempt=(
                self._get_positive_integer_metric(
                    document=document,
                    metric_name="extraction_selected_attempt",
                )
            ),
            authorized_units_reconciled=(
                self.AUTHORIZED_UNITS_RECONCILIATION_ACTION
                in document.validation_actions
            ),
        )

    def _build_fields(
        self,
        document: Document,
    ) -> list[ReviewField]:
        """
        Build field review records from complete evidence when available.

        Flat extracted values remain available as a conservative fallback
        for fields that do not have a field_evidence record.
        """

        field_names: list[str] = []

        if isinstance(
            document.field_evidence,
            dict,
        ):
            field_names.extend(
                str(field_name)
                for field_name in document.field_evidence
            )

        if isinstance(
            document.extracted_data,
            dict,
        ):
            for field_name in document.extracted_data:
                normalized_name = str(
                    field_name
                )

                if normalized_name not in field_names:
                    field_names.append(
                        normalized_name
                    )

        fields: list[ReviewField] = []

        for field_name in field_names:
            evidence = document.field_evidence.get(
                field_name
            )

            if isinstance(
                evidence,
                dict,
            ):
                value = deepcopy(
                    evidence.get(
                        "value"
                    )
                )
                confidence = self._normalize_confidence(
                    evidence.get(
                        "confidence"
                    )
                )
                source_text = self._normalize_text(
                    evidence.get(
                        "source_text"
                    )
                )
            else:
                value = deepcopy(
                    document.extracted_data.get(
                        field_name
                    )
                )
                confidence = self._normalize_confidence(
                    document.field_confidences.get(
                        field_name
                    )
                )
                source_text = ""

            fields.append(
                ReviewField(
                    name=field_name,
                    value=value,
                    confidence=confidence,
                    source_text=source_text,
                )
            )

        return fields

    def _build_service_lines(
        self,
        service_lines: Any,
    ) -> list[ReviewServiceLine]:
        """
        Copy valid service-line models into the review contract.
        """

        if not isinstance(
            service_lines,
            list,
        ):
            return []

        review_lines: list[ReviewServiceLine] = []

        for service_line in service_lines:
            if not isinstance(
                service_line,
                AuthorizationServiceLine,
            ):
                continue

            review_lines.append(
                ReviewServiceLine(
                    service_code=self._normalize_optional_text(
                        service_line.service_code
                    ),
                    modifier=self._normalize_optional_text(
                        service_line.modifier
                    ),
                    quantity=deepcopy(
                        service_line.quantity
                    ),
                    start_date=self._normalize_optional_text(
                        service_line.start_date
                    ),
                    end_date=self._normalize_optional_text(
                        service_line.end_date
                    ),
                    status=self._normalize_optional_text(
                        service_line.status
                    ),
                    confidence=self._normalize_confidence(
                        service_line.confidence
                    ),
                    source_text=self._normalize_text(
                        service_line.source_text
                    ),
                )
            )

        return review_lines

    def _get_metric(
        self,
        document: Document,
        metric_name: str,
    ) -> Any:
        """
        Return one PHI-safe processing metric when available.
        """

        if not isinstance(
            document.processing_metrics,
            dict,
        ):
            return None

        return document.processing_metrics.get(
            metric_name
        )

    def _get_nonnegative_integer_metric(
        self,
        document: Document,
        metric_name: str,
    ) -> int:
        """
        Return a nonnegative integer metric or zero when unavailable.
        """

        value = self._get_metric(
            document=document,
            metric_name=metric_name,
        )

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

    def _get_positive_integer_metric(
        self,
        document: Document,
        metric_name: str,
    ) -> int | None:
        """
        Return a positive integer metric or None when unavailable.
        """

        value = self._get_metric(
            document=document,
            metric_name=metric_name,
        )

        try:
            normalized = int(
                value
            )
        except (TypeError, ValueError):
            return None

        if normalized < 1:
            return None

        return normalized

    def _get_boolean_metric(
        self,
        document: Document,
        metric_name: str,
    ) -> bool:
        """
        Return a boolean metric without treating arbitrary text as true.
        """

        value = self._get_metric(
            document=document,
            metric_name=metric_name,
        )

        if isinstance(
            value,
            bool,
        ):
            return value

        return False

    def _copy_text_list(
        self,
        values: Any,
    ) -> list[str]:
        """
        Copy text entries while preserving their existing order.
        """

        if not isinstance(
            values,
            list,
        ):
            return []

        return [
            str(
                value
            )
            for value in values
            if value is not None
        ]

    def _normalize_optional_confidence(
        self,
        value: Any,
    ) -> float | None:
        """
        Preserve an absent optional confidence as None.
        """

        if value is None:
            return None

        return self._normalize_confidence(
            value
        )

    def _normalize_confidence(
        self,
        value: Any,
    ) -> float:
        """
        Normalize confidence to the range 0.0 through 1.0.

        Missing or invalid confidence remains conservatively 0.0.
        """

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

    def _normalize_optional_text(
        self,
        value: Any,
    ) -> str | None:
        """
        Normalize optional text without inventing missing values.
        """

        if value is None:
            return None

        return str(
            value
        ).strip()

    def _normalize_text(
        self,
        value: Any,
    ) -> str:
        """
        Normalize required text fields to a string.
        """

        if value is None:
            return ""

        return str(
            value
        ).strip()
