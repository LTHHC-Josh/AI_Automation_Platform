from typing import Any

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
    SmartsheetRowMappingResult,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)


class SmartsheetReviewRowMappingService:
    """
    Maps structured review output into an approved logical Smartsheet
    row contract.

    This service:
    - does not connect to Smartsheet;
    - does not create SDK Cell objects;
    - does not log mapped values;
    - does not map source_text;
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
    ALLOWED_RUN_TYPES = {
        "Production",
        "Boss Demo",
        "Attachment Verification",
        "Classification Metadata Test",
        "End-to-End Test",
    }
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

    def map(
        self,
        review_output: ReviewOutput,
        policies: list[SmartsheetColumnPolicy],
        complete_review_approved: bool = False,
        run_type: str = "Production",
    ) -> SmartsheetRowMappingResult:
        """
        Build a deterministic mapping from explicit column policies.

        A result is ready for automatic writing only when:
        - the review output is valid;
        - required approved values are populated;
        - no prohibited source field was requested;
        - human review is not required.
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
                continue

            if self._is_empty_value(
                review_field.value
            ):
                self._record_missing_required(
                    policy=policy,
                    result=result,
                )
                continue

            result.values[
                policy.column_name
            ] = self._serialize_value(
                review_field.value
            )

            if policy.confidence_column_name:
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

        recommended_review_approved = (
            complete_review_approved is True
            and str(
                review_output.review_status
                or ""
            ).strip().lower()
            == "human review recommended"
        )

        result.ready_for_write = (
            not result.missing_required_columns
            and not result.prohibited_fields
            and (
                not review_output.needs_human_review
                or recommended_review_approved
            )
        )

        return result

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

        result.values[
            self.DOCUMENT_CATEGORY_COLUMN
        ] = review_output.document_category

        result.values[
            self.DOCUMENT_SUBTYPE_COLUMN
        ] = review_output.document_subtype

        result.values[
            self.REVIEW_REASONS_COLUMN
        ] = self._serialize_value(
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
                "Human review is required before automatic row writing."
            )

    def _normalize_run_type(
        self,
        value: Any,
    ) -> str | None:
        """
        Accept only explicitly approved PHI-safe workflow labels.

        Run Type is operational metadata. It must never be inferred
        from OCR, extracted values, filenames, or document content.
        """

        normalized = str(
            value
            or ""
        ).strip()

        if normalized not in self.ALLOWED_RUN_TYPES:
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
