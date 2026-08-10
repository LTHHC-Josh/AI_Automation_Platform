from dataclasses import fields

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.smartsheet_destination_schema_service import (
    SmartsheetDestinationSchemaResult,
)
from src.services.smartsheet_mapping_policy_service import (
    SmartsheetMappingPolicyResult,
)
from src.services.smartsheet_review_configuration_service import (
    SmartsheetReviewConfigurationResult,
    SmartsheetReviewConfigurationService,
)


passed = 0
failed = 0


class RecordingPolicyService:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.calls = []

    def get(
        self,
        *,
        document_type,
    ):
        self.calls.append(
            document_type
        )

        return self.result


class RecordingSchemaService:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.call_count = 0

    def read(
        self,
    ):
        self.call_count += 1

        return self.result


def run_test(
    name,
    test,
):
    global passed
    global failed

    try:
        test()
        passed += 1
        print(
            f"PASSED: {name}"
        )
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def build_policies():
    return (
        SmartsheetColumnPolicy(
            source_field="authorization_status",
            column_name="Authorization Status",
            required=True,
        ),
        SmartsheetColumnPolicy(
            source_field="start_date",
            column_name="Start Date",
            required=False,
        ),
    )


def successful_policy_result():
    policies = build_policies()

    return SmartsheetMappingPolicyResult(
        policy_count=len(
            policies
        ),
        policies=policies,
        success=True,
        status="ready",
    )


def successful_schema_result():
    columns = {
        "Authorization Status": 1001,
        "Start Date": 1002,
        "AI Review Status": 1003,
    }

    return SmartsheetDestinationSchemaResult(
        column_count=len(
            columns
        ),
        columns=columns,
        success=True,
        status="ready",
    )


def test_ready_configuration_is_returned():
    policy_service = RecordingPolicyService(
        successful_policy_result()
    )

    schema_service = RecordingSchemaService(
        successful_schema_result()
    )

    service = (
        SmartsheetReviewConfigurationService(
            policy_service=policy_service,
            schema_service=schema_service,
        )
    )

    result = service.resolve(
        document_type="authorization"
    )

    assert result.success is True
    assert result.status == "ready"
    assert result.policy_count == 2
    assert result.column_count == 3

    assert len(
        result.policies
    ) == 2

    assert result.available_columns == {
        "Authorization Status": 1001,
        "Start Date": 1002,
        "AI Review Status": 1003,
    }

    assert policy_service.calls == [
        "authorization"
    ]

    assert schema_service.call_count == 1


def test_default_authorization_policy_is_approved():
    columns = {
        "Authorization Status": 1001,
        "Authorization #": 1002,
        "Authorization # Conf.": 1003,
        "Service Codes": 1004,
        "Service Codes Conf.": 1005,
        "Diagnosis Codes": 1006,
        "Diagnosis Codes Conf.": 1007,
        "Start Date": 1008,
        "End Date": 1009,
        "Authorized Units": 1010,
        "Authorized Units Conf.": 1011,
        "Hours": 1012,
        "Hours Conf.": 1013,
        "Days Per Week": 1014,
        "Days Per Week Conf.": 1015,
    }

    schema_service = RecordingSchemaService(
        SmartsheetDestinationSchemaResult(
            column_count=len(
                columns
            ),
            columns=columns,
            success=True,
            status="ready",
        )
    )

    result = (
        SmartsheetReviewConfigurationService(
            schema_service=schema_service
        )
        .resolve(
            document_type="authorization"
        )
    )

    assert result.success is True
    assert result.status == "ready"
    assert result.policy_count == 9

    assert [
        (
            policy.source_field,
            policy.column_name,
            policy.confidence_column_name,
        )
        for policy in result.policies
    ] == [
        (
            "authorization_status",
            "Authorization Status",
            None,
        ),
        (
            "authorization_number",
            "Authorization #",
            "Authorization # Conf.",
        ),
        (
            "service_codes",
            "Service Codes",
            "Service Codes Conf.",
        ),
        (
            "diagnosis_code",
            "Diagnosis Codes",
            "Diagnosis Codes Conf.",
        ),
        (
            "start_date",
            "Start Date",
            None,
        ),
        (
            "end_date",
            "End Date",
            None,
        ),
        (
            "authorized_units",
            "Authorized Units",
            "Authorized Units Conf.",
        ),
        (
            "hours",
            "Hours",
            "Hours Conf.",
        ),
        (
            "days_per_week",
            "Days Per Week",
            "Days Per Week Conf.",
        ),
    ]

    assert schema_service.call_count == 1


def test_default_authorization_renewal_policy_is_approved():
    columns = {
        "Authorization Status": 1001,
        "Authorization #": 1002,
        "Authorization # Conf.": 1003,
        "Service Codes": 1004,
        "Service Codes Conf.": 1005,
        "Diagnosis Codes": 1006,
        "Diagnosis Codes Conf.": 1007,
        "Start Date": 1008,
        "End Date": 1009,
        "Authorized Units": 1010,
        "Authorized Units Conf.": 1011,
        "Hours": 1012,
        "Hours Conf.": 1013,
        "Days Per Week": 1014,
        "Days Per Week Conf.": 1015,
    }

    schema_service = RecordingSchemaService(
        SmartsheetDestinationSchemaResult(
            column_count=len(
                columns
            ),
            columns=columns,
            success=True,
            status="ready",
        )
    )

    result = (
        SmartsheetReviewConfigurationService(
            schema_service=schema_service
        )
        .resolve(
            document_type="authorization_renewal"
        )
    )

    assert result.success is True
    assert result.status == "ready"
    assert result.policy_count == 9

    assert [
        (
            policy.source_field,
            policy.column_name,
            policy.confidence_column_name,
        )
        for policy in result.policies
    ] == [
        (
            "authorization_status",
            "Authorization Status",
            None,
        ),
        (
            "authorization_number",
            "Authorization #",
            "Authorization # Conf.",
        ),
        (
            "service_codes",
            "Service Codes",
            "Service Codes Conf.",
        ),
        (
            "diagnosis_code",
            "Diagnosis Codes",
            "Diagnosis Codes Conf.",
        ),
        (
            "start_date",
            "Start Date",
            None,
        ),
        (
            "end_date",
            "End Date",
            None,
        ),
        (
            "authorized_units",
            "Authorized Units",
            "Authorized Units Conf.",
        ),
        (
            "hours",
            "Hours",
            "Hours Conf.",
        ),
        (
            "days_per_week",
            "Days Per Week",
            "Days Per Week Conf.",
        ),
    ]

    assert schema_service.call_count == 1


def test_policy_failure_blocks_schema_read():
    policy_service = RecordingPolicyService(
        SmartsheetMappingPolicyResult(
            policy_count=0,
            policies=(),
            success=False,
            status="policy_not_configured",
        )
    )

    schema_service = RecordingSchemaService(
        successful_schema_result()
    )

    result = (
        SmartsheetReviewConfigurationService(
            policy_service=policy_service,
            schema_service=schema_service,
        )
        .resolve(
            document_type="authorization"
        )
    )

    assert result.success is False

    assert (
        result.status
        == "policy_not_configured"
    )

    assert schema_service.call_count == 0


def test_schema_failure_is_preserved():
    policy_service = RecordingPolicyService(
        successful_policy_result()
    )

    schema_service = RecordingSchemaService(
        SmartsheetDestinationSchemaResult(
            column_count=0,
            columns={},
            success=False,
            status="schema_read_failed",
        )
    )

    result = (
        SmartsheetReviewConfigurationService(
            policy_service=policy_service,
            schema_service=schema_service,
        )
        .resolve(
            document_type="authorization"
        )
    )

    assert result.success is False

    assert (
        result.status
        == "schema_read_failed"
    )


def test_missing_policy_column_blocks_configuration():
    policy_service = RecordingPolicyService(
        successful_policy_result()
    )

    schema_service = RecordingSchemaService(
        SmartsheetDestinationSchemaResult(
            column_count=1,
            columns={
                "Authorization Status": 1001,
            },
            success=True,
            status="ready",
        )
    )

    result = (
        SmartsheetReviewConfigurationService(
            policy_service=policy_service,
            schema_service=schema_service,
        )
        .resolve(
            document_type="authorization"
        )
    )

    assert result.success is False

    assert (
        result.status
        == "policy_columns_missing"
    )


def test_extra_destination_columns_are_allowed():
    policy_service = RecordingPolicyService(
        successful_policy_result()
    )

    schema_service = RecordingSchemaService(
        SmartsheetDestinationSchemaResult(
            column_count=4,
            columns={
                "Authorization Status": 1001,
                "Start Date": 1002,
                "AI Review Status": 1003,
                "Unused Destination Column": 1004,
            },
            success=True,
            status="ready",
        )
    )

    result = (
        SmartsheetReviewConfigurationService(
            policy_service=policy_service,
            schema_service=schema_service,
        )
        .resolve(
            document_type="authorization"
        )
    )

    assert result.success is True
    assert result.column_count == 4


def test_result_contract_is_phi_safe():
    field_names = {
        field.name
        for field in fields(
            SmartsheetReviewConfigurationResult
        )
    }

    assert field_names == {
        "policy_count",
        "column_count",
        "policies",
        "available_columns",
        "success",
        "status",
    }

    prohibited_names = {
        "values",
        "source_text",
        "ocr_text",
        "file_path",
        "filename",
        "patient",
        "rows",
        "row_values",
        "payload",
        "review_output",
    }

    assert field_names.isdisjoint(
        prohibited_names
    )


print(
    "=" * 60
)
print(
    "Testing Smartsheet Review Configuration Resolver"
)
print(
    "=" * 60
)

run_test(
    "ready configuration is returned",
    test_ready_configuration_is_returned,
)

run_test(
    "default authorization policy is approved",
    test_default_authorization_policy_is_approved,
)

run_test(
    "default authorization renewal policy is approved",
    test_default_authorization_renewal_policy_is_approved,
)

run_test(
    "policy failure blocks schema read",
    test_policy_failure_blocks_schema_read,
)

run_test(
    "schema failure is preserved",
    test_schema_failure_is_preserved,
)

run_test(
    "missing policy column blocks configuration",
    test_missing_policy_column_blocks_configuration,
)

run_test(
    "extra destination columns are allowed",
    test_extra_destination_columns_are_allowed,
)

run_test(
    "result contract is PHI-safe",
    test_result_contract_is_phi_safe,
)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Synthetic deterministic/mock"
)
print(
    "Smartsheet external API: Not called"
)
print(
    "Smartsheet rows read: 0"
)
print(
    "Smartsheet rows written: 0"
)
print(
    "Microsoft Graph: Not called"
)
print(
    "OCR: Not called"
)
print(
    "Ollama: Not called"
)
print(
    "PHI handling: Policy metadata and column schema only"
)

if failed:
    raise SystemExit(1)
