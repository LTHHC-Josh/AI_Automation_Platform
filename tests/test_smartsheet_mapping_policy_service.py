from dataclasses import fields

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.smartsheet_mapping_policy_service import (
    SmartsheetMappingPolicyResult,
    SmartsheetMappingPolicyService,
)


passed = 0
failed = 0


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
    return [
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
    ]


def test_configured_policy_is_returned():
    service = SmartsheetMappingPolicyService(
        policies_by_document_type={
            "authorization": build_policies(),
        }
    )

    result = service.get(
        document_type="authorization"
    )

    assert result.success is True
    assert result.status == "ready"
    assert result.policy_count == 2
    assert len(result.policies) == 2


def test_document_type_is_normalized():
    service = SmartsheetMappingPolicyService(
        policies_by_document_type={
            "authorization": build_policies(),
        }
    )

    result = service.get(
        document_type=" Authorization "
    )

    assert result.success is True
    assert result.policy_count == 2


def test_unknown_document_type_is_blocked():
    service = SmartsheetMappingPolicyService(
        policies_by_document_type={
            "authorization": build_policies(),
        }
    )

    result = service.get(
        document_type="unknown"
    )

    assert result.success is False

    assert (
        result.status
        == "policy_not_configured"
    )


def test_blank_document_type_is_blocked():
    service = SmartsheetMappingPolicyService()

    result = service.get(
        document_type="   "
    )

    assert result.success is False

    assert (
        result.status
        == "invalid_document_type"
    )


def test_no_default_production_policy_exists():
    service = SmartsheetMappingPolicyService()

    result = service.get(
        document_type="authorization"
    )

    assert result.success is False

    assert (
        result.status
        == "policy_not_configured"
    )


def test_empty_policy_is_blocked():
    service = SmartsheetMappingPolicyService(
        policies_by_document_type={
            "authorization": [],
        }
    )

    result = service.get(
        document_type="authorization"
    )

    assert result.success is False
    assert result.status == "empty_policy"


def test_invalid_policy_entry_is_rejected():
    try:
        SmartsheetMappingPolicyService(
            policies_by_document_type={
                "authorization": [
                    {},
                ],
            }
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid policy entry was accepted."
    )


def test_duplicate_source_field_is_rejected():
    policies = [
        SmartsheetColumnPolicy(
            source_field="status",
            column_name="Status A",
        ),
        SmartsheetColumnPolicy(
            source_field="status",
            column_name="Status B",
        ),
    ]

    try:
        SmartsheetMappingPolicyService(
            policies_by_document_type={
                "authorization": policies,
            }
        )
    except ValueError:
        return

    raise AssertionError(
        "Duplicate source field was accepted."
    )


def test_duplicate_column_name_is_rejected():
    policies = [
        SmartsheetColumnPolicy(
            source_field="status",
            column_name="Status",
        ),
        SmartsheetColumnPolicy(
            source_field="start_date",
            column_name="Status",
        ),
    ]

    try:
        SmartsheetMappingPolicyService(
            policies_by_document_type={
                "authorization": policies,
            }
        )
    except ValueError:
        return

    raise AssertionError(
        "Duplicate destination column was accepted."
    )


def test_result_contract_is_phi_safe():
    field_names = {
        field.name
        for field in fields(
            SmartsheetMappingPolicyResult
        )
    }

    assert field_names == {
        "policy_count",
        "policies",
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
        "row_values",
        "payload",
    }

    assert field_names.isdisjoint(
        prohibited_names
    )


print(
    "=" * 60
)
print(
    "Testing Smartsheet Mapping Policy Registry"
)
print(
    "=" * 60
)

run_test(
    "configured policy is returned",
    test_configured_policy_is_returned,
)

run_test(
    "document type is normalized",
    test_document_type_is_normalized,
)

run_test(
    "unknown document type is blocked",
    test_unknown_document_type_is_blocked,
)

run_test(
    "blank document type is blocked",
    test_blank_document_type_is_blocked,
)

run_test(
    "no default production policy exists",
    test_no_default_production_policy_exists,
)

run_test(
    "empty policy is blocked",
    test_empty_policy_is_blocked,
)

run_test(
    "invalid policy entry is rejected",
    test_invalid_policy_entry_is_rejected,
)

run_test(
    "duplicate source field is rejected",
    test_duplicate_source_field_is_rejected,
)

run_test(
    "duplicate destination column is rejected",
    test_duplicate_column_name_is_rejected,
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
    "Real or mock: Synthetic deterministic"
)
print(
    "Smartsheet external API: Not called"
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
    "PHI handling: Policy field names and column titles only"
)

if failed:
    raise SystemExit(1)
