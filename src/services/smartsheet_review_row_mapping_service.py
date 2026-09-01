from typing import Any

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
    SmartsheetRowMappingResult,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)
from src.services.review_reason_summary_service import (
    ReviewReasonSummaryService,
)
from src.services.review_decision_service import ReviewDecisionService


class SmartsheetReviewRowMappingService:
    """
    Maps structured review output into an explicitly configured Smartsheet
    row contract.

    This service:
    - does not connect to Smartsheet;
    - does not create SDK Cell objects;
    - does not log mapped values;
    - does not map source_text because no destination is configured;
    - does not infer missing values;
    - does not reinterpret quantities, visits, units, or approval.
    """

    PROHIBITED_SOURCE_FIELDS = {
        "raw_text",
        "file_path",
        "processing_metrics",
        "source_text",
    }

    REVIEW_STATUS_COLUMN = "AI Review Status"
    REVIEW_REQUIRED_COLUMN = "AI Review Required"
    AI_CORRECTION_COLUMN = "AI Correction"
    DOCUMENT_CATEGORY_COLUMN = (
        "AI Document Category"
    )
    DOCUMENT_SUBTYPE_COLUMN = (
        "AI Document Subtype"
    )
    REVIEW_REASONS_COLUMN = (
        "AI Review Reasons"
    )
    RUN_TYPE_COLUMN = "Run Type"
    CLASSIFICATION_CONFIDENCE_COLUMN = (
        "AI Classification Confidence"
    )
    MINIMUM_CONFIDENCE_COLUMN = (
        "AI Minimum Field Confidence"
    )
    SELECTED_ATTEMPT_COLUMN = (
        "AI Selected Extraction Attempt"
    )
    RETRY_TRIGGERED_COLUMN = (
        "AI Extraction Retry Triggered"
    )
    RECONCILIATION_COLUMN = (
        "AI Authorized Units Reconciled"
    )
    OPERATIONAL_METADATA_COLUMNS = (
        REVIEW_STATUS_COLUMN,
        REVIEW_REQUIRED_COLUMN,
        AI_CORRECTION_COLUMN,
        DOCUMENT_CATEGORY_COLUMN,
        DOCUMENT_SUBTYPE_COLUMN,
        REVIEW_REASONS_COLUMN,
        RUN_TYPE_COLUMN,
        CLASSIFICATION_CONFIDENCE_COLUMN,
        MINIMUM_CONFIDENCE_COLUMN,
        SELECTED_ATTEMPT_COLUMN,
        RETRY_TRIGGERED_COLUMN,
        RECONCILIATION_COLUMN,
    )

    def __init__(self, *, review_reason_summary_service=None) -> None:
        self.review_reason_summary_service = (
            review_reason_summary_service or ReviewReasonSummaryService()
        )

    def map(
        self,
        review_output: ReviewOutput,
        policies: list[SmartsheetColumnPolicy],
        run_type: str = "",
    ) -> SmartsheetRowMappingResult:
        """
        Build a deterministic mapping from explicit column policies.

        A result is ready for automatic writing only when:
        - the review output is valid;
        - required approved values are populated;
        - no prohibited source field was requested.

        Human-review state is mapped as downstream exception metadata
        and does not gate automatic row population.
        """

        result = SmartsheetRowMappingResult()

        normalized_run_type = self._normalize_run_type(
            run_type
        )

        if normalized_run_type is None:
            result.warnings.append(
                "Run type is unavailable or invalid."
            )
            return result

        if not isinstance(
            review_output,
            ReviewOutput,
        ):
            result.warnings.append(
                "Structured review output is unavailable or invalid."
            )
            return result

        normalized_policies = self._normalize_policies(
            policies
        )

        fields_by_name = {
            field.name: field
            for field in review_output.fields
            if isinstance(
                field,
                ReviewField,
            )
        }

        displayed_confidences: list[float] = []

        for policy in normalized_policies:
            if policy.source_field in self.PROHIBITED_SOURCE_FIELDS:
                result.prohibited_fields.append(
                    policy.source_field
                )
                continue

            review_field = fields_by_name.get(
                policy.source_field
            )

            if review_field is None:
                self._record_missing_required(
                    policy=policy,
                    result=result,
                )
                self._map_unavailable_confidence(
                    policy=policy,
                    review_field=None,
                    review_output=review_output,
                    result=result,
                    displayed_confidences=displayed_confidences,
                )
                continue

            if self._is_empty_value(
                review_field.value
            ):
                self._record_missing_required(
                    policy=policy,
                    result=result,
                )
                self._map_unavailable_confidence(
                    policy=policy,
                    review_field=review_field,
                    review_output=review_output,
                    result=result,
                    displayed_confidences=displayed_confidences,
                )
                continue

            if not self._is_reliably_supported(
                review_field=review_field,
                review_output=review_output,
            ):
                self._record_missing_required(
                    policy=policy,
                    result=result,
                )
                self._map_unavailable_confidence(
                    policy=policy,
                    review_field=review_field,
                    review_output=review_output,
                    result=result,
                    displayed_confidences=displayed_confidences,
                )
                continue

            result.values[
                policy.column_name
            ] = self._serialize_value(
                review_field.value
            )

            if (
                policy.confidence_column_name
                and review_field.confidence_available
            ):
                result.values[
                    policy.confidence_column_name
                ] = review_field.confidence

                if (
                    isinstance(
                        review_field.confidence,
                        (int, float),
                    )
                    and not isinstance(
                        review_field.confidence,
                        bool,
                    )
                ):
                    displayed_confidences.append(
                        float(
                            review_field.confidence
                        )
                    )

            if policy.review_only:
                result.review_only_columns.append(
                    policy.column_name
                )

        self._append_review_metadata(
            review_output=review_output,
            result=result,
            displayed_confidences=displayed_confidences,
            run_type=normalized_run_type,
        )

        result.missing_required_columns = self._deduplicate(
            result.missing_required_columns
        )
        result.review_only_columns = self._deduplicate(
            result.review_only_columns
        )
        result.prohibited_fields = self._deduplicate(
            result.prohibited_fields
        )
        result.warnings = self._deduplicate(
            result.warnings
        )

        result.ready_for_write = (
            not result.missing_required_columns
            and not result.prohibited_fields
        )

        return result

    def _is_reliably_supported(
        self,
        *,
        review_field: ReviewField,
        review_output: ReviewOutput,
    ) -> bool:
        if not review_field.confidence_available:
            return False
        confidence = review_field.confidence
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
        ):
            return False
        if (
            float(confidence)
            < ReviewDecisionService.FIELD_CONFIDENCE_THRESHOLD
        ):
            return False
        return True

    def _map_unavailable_confidence(
        self,
        *,
        policy: SmartsheetColumnPolicy,
        review_field: ReviewField | None,
        review_output: ReviewOutput,
        result: SmartsheetRowMappingResult,
        displayed_confidences: list[float],
    ) -> None:
        column_name = policy.confidence_column_name
        if not column_name:
            return

        status = self._confidence_status(
            field_name=policy.source_field,
            reasons=(
                list(review_output.review_reasons)
                + list(review_output.validation_actions)
                + list(review_output.rule_actions)
            ),
        )

        if status and policy.confidence_column_supports_text:
            result.values[column_name] = status
            return

        if status:
            result.warnings.append(
                "confidence_status_destination_constraint"
            )

        # Numeric confidence columns describe accepted production values only.
        # Candidate confidence remains in the protected review payload and must
        # not appear as though an unavailable value passed validation.

    @staticmethod
    def _confidence_status(*, field_name: str, reasons: list[str]) -> str | None:
        normalized_field = field_name.replace("_", " ").strip().lower()
        aliases = {normalized_field}
        if normalized_field.endswith("s"):
            aliases.add(normalized_field[:-1])
        else:
            aliases.add(f"{normalized_field}s")

        matching = []
        for reason in reasons:
            text = str(reason or "").strip().lower()
            if text.startswith("service line "):
                continue
            if text and any(alias in text for alias in aliases):
                matching.append(text)

        if any(
            signal in reason
            for reason in matching
            for signal in ("unsupported", "cleared", "invalid", "conflict")
        ):
            return "Unsupported/Cleared"

        if any(
            signal in reason
            for reason in matching
            for signal in (
                "not extracted",
                "missing",
                "could not be determined",
                "unavailable",
            )
        ):
            return "Missing/Not extracted"

        return None

    def _append_review_metadata(
        self,
        review_output: ReviewOutput,
        result: SmartsheetRowMappingResult,
        displayed_confidences: list[float],
        run_type: str,
    ) -> None:
        """
        Add PHI-safe workflow metadata under stable logical names.
        """

        result.values[
            self.REVIEW_STATUS_COLUMN
        ] = review_output.review_status

        result.values[
            self.REVIEW_REQUIRED_COLUMN
        ] = review_output.needs_human_review

        # Human-owned feedback boundary: initialize a brand-new row to an
        # unchecked checkbox. Reconciliation never remaps or updates an
        # existing row, so a reviewer-owned value is preserved thereafter.
        result.values[
            self.AI_CORRECTION_COLUMN
        ] = False

        result.values[
            self.DOCUMENT_CATEGORY_COLUMN
        ] = review_output.document_category

        result.values[
            self.DOCUMENT_SUBTYPE_COLUMN
        ] = review_output.document_subtype

        result.values[
            self.REVIEW_REASONS_COLUMN
        ] = self.review_reason_summary_service.summarize(
            review_output.review_reasons
        )

        result.values[
            self.RUN_TYPE_COLUMN
        ] = run_type

        result.values[
            self.CLASSIFICATION_CONFIDENCE_COLUMN
        ] = review_output.classification_confidence

        result.values[
            self.MINIMUM_CONFIDENCE_COLUMN
        ] = (
            min(
                displayed_confidences
            )
            if displayed_confidences
            else None
        )

        result.values[
            self.SELECTED_ATTEMPT_COLUMN
        ] = review_output.extraction_selected_attempt

        result.values[
            self.RETRY_TRIGGERED_COLUMN
        ] = review_output.extraction_retry_triggered

        result.values[
            self.RECONCILIATION_COLUMN
        ] = review_output.authorized_units_reconciled

        if review_output.needs_human_review:
            result.warnings.append(
                "Downstream human review is required after automatic row writing."
            )

    def _normalize_run_type(
        self,
        value: Any,
    ) -> str | None:
        """
        Accept explicit PHI-safe test-purpose text.

        Run Type identifies the change or behavior under test for the
        current execution. It must never be inferred from OCR,
        extracted values, filenames, or document content.
        """

        normalized = str(
            value
            or ""
        ).strip()

        if not normalized:
            return None

        if len(normalized) > 120:
            return None

        if "\n" in normalized or "\r" in normalized:
            return None

        return normalized

    def _record_missing_required(
        self,
        policy: SmartsheetColumnPolicy,
        result: SmartsheetRowMappingResult,
    ) -> None:
        """
        Record a missing required destination without inventing a value.
        """

        if policy.required:
            result.missing_required_columns.append(
                policy.column_name
            )

    def _normalize_policies(
        self,
        policies: Any,
    ) -> list[SmartsheetColumnPolicy]:
        """
        Retain valid policies and reject duplicate destination columns.
        """

        if not isinstance(
            policies,
            list,
        ):
            return []

        normalized: list[SmartsheetColumnPolicy] = []
        seen_columns: set[str] = set()

        for policy in policies:
            if not isinstance(
                policy,
                SmartsheetColumnPolicy,
            ):
                continue

            source_field = str(
                policy.source_field
            ).strip()
            column_name = str(
                policy.column_name
            ).strip()

            confidence_column_name = (
                str(
                    policy.confidence_column_name
                ).strip()
                if policy.confidence_column_name
                is not None
                else ""
            )

            if not source_field or not column_name:
                continue

            if column_name in seen_columns:
                continue

            if (
                confidence_column_name
                and confidence_column_name in seen_columns
            ):
                continue

            seen_columns.add(
                column_name
            )

            if confidence_column_name:
                seen_columns.add(
                    confidence_column_name
                )

            normalized.append(
                SmartsheetColumnPolicy(
                    source_field=source_field,
                    column_name=column_name,
                    required=bool(
                        policy.required
                    ),
                    review_only=bool(
                        policy.review_only
                    ),
                    confidence_column_name=(
                        confidence_column_name
                        or None
                    ),
                    confidence_column_supports_text=bool(
                        policy.confidence_column_supports_text
                    ),
                )
            )

        return normalized

    def _serialize_value(
        self,
        value: Any,
    ) -> Any:
        """
        Serialize collections deterministically for a single logical cell.

        Scalars are preserved. Lists and tuples preserve extraction order.
        Sets use sorted order because sets have no stable source order.
        """

        if isinstance(
            value,
            set,
        ):
            serialized_items = sorted(
                self._normalize_collection_items(
                    value
                )
            )
            return " | ".join(
                serialized_items
            )

        if isinstance(
            value,
            (list, tuple),
        ):
            return " | ".join(
                self._normalize_collection_items(
                    value
                )
            )

        return value

    def _normalize_collection_items(
        self,
        values: Any,
    ) -> list[str]:
        """
        Convert populated collection items to text without interpreting
        their business meaning.
        """

        normalized_items: list[str] = []

        for value in values:
            if value is None:
                continue

            normalized_value = str(
                value
            ).strip()

            if not normalized_value:
                continue

            normalized_items.append(
                normalized_value
            )

        return normalized_items

    def _is_empty_value(
        self,
        value: Any,
    ) -> bool:
        """
        Treat None and empty containers/text as missing.

        Numeric zero and boolean false remain populated values.
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
            (list, tuple, set, dict),
        ):
            return len(
                value
            ) == 0

        return False

    def _deduplicate(
        self,
        values: list[str],
    ) -> list[str]:
        """
        Deduplicate text while preserving first occurrence order.
        """

        seen: set[str] = set()
        deduplicated: list[str] = []

        for value in values:
            if value in seen:
                continue

            seen.add(
                value
            )
            deduplicated.append(
                value
            )

        return deduplicated
