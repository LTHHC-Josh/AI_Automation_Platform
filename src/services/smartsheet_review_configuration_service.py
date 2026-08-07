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


APPROVED_AUTHORIZATION_POLICIES = (
    SmartsheetColumnPolicy(
        source_field="authorization_status",
        column_name="Authorization Status",
    ),
    SmartsheetColumnPolicy(
        source_field="service_codes",
        column_name="Service Codes",
    ),
    SmartsheetColumnPolicy(
        source_field="authorized_units",
        column_name="Authorized Units",
    ),
    SmartsheetColumnPolicy(
        source_field="start_date",
        column_name="Start Date",
    ),
    SmartsheetColumnPolicy(
        source_field="end_date",
        column_name="End Date",
    ),
)


APPROVED_POLICIES_BY_DOCUMENT_TYPE = {
    "authorization": APPROVED_AUTHORIZATION_POLICIES,
    "authorization_renewal": APPROVED_AUTHORIZATION_POLICIES,
}


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
                )
            )
        )

        self.schema_service = (
            schema_service
            or SmartsheetDestinationSchemaService()
        )

    def resolve(
        self,
        *,
        document_type,
    ) -> SmartsheetReviewConfigurationResult:
        policy_result = (
            self.policy_service.get(
                document_type=document_type
            )
        )

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

        return SmartsheetReviewConfigurationResult(
            policy_count=(
                policy_result.policy_count
            ),
            column_count=(
                schema_result.column_count
            ),
            policies=(
                policy_result.policies
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
