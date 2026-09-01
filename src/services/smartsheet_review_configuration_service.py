from dataclasses import dataclass

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.smartsheet_destination_schema_service import (
    SmartsheetDestinationSchemaService,
)
from src.services.smartsheet_mapping_policy_service import (
    SmartsheetMappingPolicyService,
)
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)


APPROVED_DOCUMENT_FIELD_POLICIES = (
    SmartsheetColumnPolicy(
        source_field="authorization_status",
        column_name="Authorization Status",
    ),
    SmartsheetColumnPolicy(
        source_field="authorization_number",
        column_name="Authorization #",
        confidence_column_name="Authorization # Conf.",
    ),
    SmartsheetColumnPolicy(
        source_field="service_codes",
        column_name="Service Codes",
        confidence_column_name="Service Codes Conf.",
    ),
    SmartsheetColumnPolicy(
        source_field="diagnosis_code",
        column_name="Diagnosis Codes",
        confidence_column_name="Diagnosis Codes Conf.",
    ),
    SmartsheetColumnPolicy(
        source_field="start_date",
        column_name="Start Date",
        confidence_column_name="Start Date Conf.",
    ),
    SmartsheetColumnPolicy(
        source_field="end_date",
        column_name="End Date",
        confidence_column_name="End Date Conf.",
    ),
    SmartsheetColumnPolicy(
        source_field="authorized_units",
        column_name="Authorized Units",
        confidence_column_name="Authorized Units Conf.",
    ),
    SmartsheetColumnPolicy(
        source_field="hours",
        column_name="Hours",
        confidence_column_name="Hours Conf.",
    ),
    SmartsheetColumnPolicy(
        source_field="days_per_week",
        column_name="Days Per Week",
        confidence_column_name="Days Per Week Conf.",
    ),
)


APPROVED_POLICIES_BY_DOCUMENT_TYPE = {
    "authorization": APPROVED_DOCUMENT_FIELD_POLICIES,
    "authorization_renewal": APPROVED_DOCUMENT_FIELD_POLICIES,
    "2067": APPROVED_DOCUMENT_FIELD_POLICIES,
}

# Backward-compatible name retained for existing imports.
APPROVED_AUTHORIZATION_POLICIES = APPROVED_DOCUMENT_FIELD_POLICIES


@dataclass(frozen=True)
class SmartsheetReviewConfigurationResult:
    policy_count: int
    column_count: int
    policies: tuple[SmartsheetColumnPolicy, ...]
    available_columns: dict[str, int]
    success: bool
    status: str


class SmartsheetReviewConfigurationService:
    """
    Resolves explicitly approved mapping policy plus the real
    destination column schema required by reviewed Smartsheet writing.

    No document values, OCR text, source_text, filenames, paths,
    Smartsheet row values, or patient data are returned or logged.
    """

    def __init__(
        self,
        *,
        policy_service: (
            SmartsheetMappingPolicyService
            | None
        ) = None,
        schema_service: (
            SmartsheetDestinationSchemaService
            | None
        ) = None,
    ) -> None:
        self.policy_service = (
            policy_service
            or SmartsheetMappingPolicyService(
                policies_by_document_type=(
                    APPROVED_POLICIES_BY_DOCUMENT_TYPE
                ),
                default_policies=APPROVED_DOCUMENT_FIELD_POLICIES,
            )
        )

        self.schema_service = (
            schema_service
            or SmartsheetDestinationSchemaService()
        )

    def resolve(
        self,
        *,
        document_type=None,
        document_family=None,
        document_subtype=None,
    ) -> SmartsheetReviewConfigurationResult:
        policy_arguments = {
            "document_type": document_type,
        }
        if document_family is not None:
            policy_arguments["document_family"] = document_family
        if document_subtype is not None:
            policy_arguments["document_subtype"] = document_subtype

        policy_result = self.policy_service.get(**policy_arguments)

        if not policy_result.success:
            return self._failure(
                policy_result.status
            )

        schema_result = (
            self.schema_service.read()
        )

        if not schema_result.success:
            return self._failure(
                schema_result.status
            )

        policy_columns = {
            policy.column_name
            for policy in policy_result.policies
        }

        policy_columns.update(
            policy.confidence_column_name
            for policy in policy_result.policies
            if policy.confidence_column_name
        )

        policy_columns.update(
            SmartsheetReviewRowMappingService.OPERATIONAL_METADATA_COLUMNS
        )

        missing_columns = (
            policy_columns
            - set(
                schema_result.columns.keys()
            )
        )

        if missing_columns:
            return self._failure(
                "policy_columns_missing"
            )

        if schema_result.column_types.get(
            SmartsheetReviewRowMappingService.AI_CORRECTION_COLUMN,
            "",
        ) != "CHECKBOX":
            return self._failure(
                "ai_correction_column_invalid"
            )

        resolved_policies = tuple(
            SmartsheetColumnPolicy(
                source_field=policy.source_field,
                column_name=policy.column_name,
                required=policy.required,
                review_only=policy.review_only,
                confidence_column_name=policy.confidence_column_name,
                confidence_column_supports_text=(
                    bool(policy.confidence_column_name)
                    and schema_result.column_types.get(
                        policy.confidence_column_name, ""
                    ) == "TEXT_NUMBER"
                ),
            )
            for policy in policy_result.policies
        )

        return SmartsheetReviewConfigurationResult(
            policy_count=(
                policy_result.policy_count
            ),
            column_count=(
                schema_result.column_count
            ),
            policies=(
                resolved_policies
            ),
            available_columns=dict(
                schema_result.columns
            ),
            success=True,
            status="ready",
        )

    @staticmethod
    def _failure(
        status: str,
    ) -> SmartsheetReviewConfigurationResult:
        return SmartsheetReviewConfigurationResult(
            policy_count=0,
            column_count=0,
            policies=(),
            available_columns={},
            success=False,
            status=status,
        )
