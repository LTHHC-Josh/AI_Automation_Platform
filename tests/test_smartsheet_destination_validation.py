from src.models.smartsheet_mapping import (
    SmartsheetRowMappingResult,
)
from src.services.smartsheet_destination_validation_service import (
    SmartsheetDestinationValidationService,
)
from datetime import date
from decimal import Decimal


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


def build_mapping(
    *,
    ready_for_write=True,
):
    return SmartsheetRowMappingResult(
        values={
            "Authorization Status": "Synthetic value",
            "Service Codes": "Synthetic value",
            "AI Review Status": "Verified by AI",
            "AI Review Required": "No",
        },
        ready_for_write=ready_for_write,
    )


def build_columns():
    return {
        "Authorization Status": 101,
        "Service Codes": 102,
        "AI Review Status": 103,
        "AI Review Required": 104,
    }


def build_column_types():
    return {
        column_name: "TEXT_NUMBER"
        for column_name in build_columns()
    }


def build_system_column_types():
    return {
        column_name: "none"
        for column_name in build_columns()
    }


def test_complete_schema_is_ready():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=build_mapping(),
        available_columns=build_columns(),
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.mapping_ready is True
    assert result.destination_ready is True
    assert result.ready_for_write is True


def test_column_ids_are_resolved():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=build_mapping(),
        available_columns=build_columns(),
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.column_ids == {
        "Authorization Status": 101,
        "Service Codes": 102,
        "AI Review Status": 103,
        "AI Review Required": 104,
    }


def test_missing_column_blocks_write():
    service = SmartsheetDestinationValidationService()

    columns = build_columns()
    del columns[
        "Service Codes"
    ]

    result = service.validate(
        mapping=build_mapping(),
        available_columns=columns,
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.missing_columns == [
        "Service Codes"
    ]
    assert result.destination_ready is False
    assert result.ready_for_write is False


def test_invalid_column_id_blocks_write():
    service = SmartsheetDestinationValidationService()

    columns = build_columns()
    columns[
        "Service Codes"
    ] = 0

    result = service.validate(
        mapping=build_mapping(),
        available_columns=columns,
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.invalid_columns == [
        "Service Codes"
    ]
    assert result.ready_for_write is False


def test_boolean_column_id_is_rejected():
    service = SmartsheetDestinationValidationService()

    columns = build_columns()
    columns[
        "Service Codes"
    ] = True

    result = service.validate(
        mapping=build_mapping(),
        available_columns=columns,
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.invalid_columns == [
        "Service Codes"
    ]


def test_coercible_non_integer_id_is_rejected():
    service = SmartsheetDestinationValidationService()

    for unsupported_id in ("102", 102.5):
        columns = build_columns()
        columns["Service Codes"] = unsupported_id
        result = service.validate(
            mapping=build_mapping(),
            available_columns=columns,
            available_column_types=build_column_types(),
            available_system_column_types=build_system_column_types(),
        )
        assert "Service Codes" in result.invalid_columns
        assert result.ready_for_write is False


def test_duplicate_column_id_blocks_write():
    service = SmartsheetDestinationValidationService()

    columns = build_columns()
    columns[
        "Service Codes"
    ] = 101

    result = service.validate(
        mapping=build_mapping(),
        available_columns=columns,
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.duplicate_column_ids == [
        101
    ]
    assert result.ready_for_write is False


def test_upstream_mapping_block_is_preserved():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=build_mapping(
            ready_for_write=False
        ),
        available_columns=build_columns(),
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.destination_ready is True
    assert result.mapping_ready is False
    assert result.ready_for_write is False


def test_invalid_mapping_is_rejected():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=None,
        available_columns=build_columns(),
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.ready_for_write is False
    assert len(
        result.warnings
    ) == 1


def test_invalid_schema_is_rejected():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=build_mapping(),
        available_columns=None,
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.destination_ready is False
    assert result.ready_for_write is False


def test_empty_mapping_is_not_destination_ready():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=SmartsheetRowMappingResult(
            values={},
            ready_for_write=True,
        ),
        available_columns=build_columns(),
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert result.destination_ready is False
    assert result.ready_for_write is False


def test_result_does_not_preserve_payload_values():
    service = SmartsheetDestinationValidationService()

    mapping = build_mapping()

    result = service.validate(
        mapping=mapping,
        available_columns=build_columns(),
        available_column_types=build_column_types(),
        available_system_column_types=build_system_column_types(),
    )

    assert not hasattr(
        result,
        "values"
    )
    assert not hasattr(
        result,
        "payload"
    )
    assert not hasattr(
        result,
        "cells"
    )


def validate_single(value, column_type, *, system_type="none"):
    return SmartsheetDestinationValidationService().validate(
        mapping=SmartsheetRowMappingResult(
            values={"Synthetic Column": value},
            ready_for_write=True,
        ),
        available_columns={"Synthetic Column": 101},
        available_column_types={"Synthetic Column": column_type},
        available_system_column_types={"Synthetic Column": system_type},
    )


def test_supported_typed_scalars_are_ready():
    for value, column_type in (
        (False, "CHECKBOX"),
        ("2026-09-03", "DATE"),
        ("Synthetic text", "TEXT_NUMBER"),
        (0, "TEXT_NUMBER"),
        (0.5, "TEXT_NUMBER"),
    ):
        result = validate_single(value, column_type)
        assert result.ready_for_write
        assert result.type_validation_passed


def test_checkbox_requires_literal_boolean():
    result = validate_single("False", "CHECKBOX")
    assert not result.ready_for_write
    assert result.rejection_safe_category == "row_mapping_invalid_checkbox_value"


def test_date_requires_normalized_iso_text():
    for value in (date(2026, 9, 3), "09/03/2026", "2026-9-3"):
        result = validate_single(value, "DATE")
        assert not result.ready_for_write
        assert result.rejection_safe_category == "row_mapping_invalid_date_value"


def test_text_number_rejects_unsupported_values():
    unsupported = (
        True,
        Decimal("1.5"),
        date(2026, 9, 3),
        {"value": "synthetic"},
        ["synthetic"],
        float("inf"),
        float("nan"),
        object(),
    )
    for value in unsupported:
        result = validate_single(value, "TEXT_NUMBER")
        assert not result.ready_for_write


def test_unproven_or_system_writable_state_blocks_write():
    missing = SmartsheetDestinationValidationService().validate(
        mapping=SmartsheetRowMappingResult(
            values={"Synthetic Column": "synthetic"},
            ready_for_write=True,
        ),
        available_columns={"Synthetic Column": 101},
        available_column_types={"Synthetic Column": "TEXT_NUMBER"},
        available_system_column_types={},
    )
    system = validate_single(
        "synthetic", "TEXT_NUMBER", system_type="AUTO_NUMBER"
    )
    assert not missing.ready_for_write
    assert missing.rejection_safe_category == (
        "row_mapping_writable_state_unavailable"
    )
    assert not system.ready_for_write
    assert system.rejection_safe_category == (
        "row_mapping_system_column_not_writable"
    )


def test_none_and_duplicate_destination_contracts_block_write():
    none_result = validate_single(None, "TEXT_NUMBER")
    duplicate_result = SmartsheetDestinationValidationService().validate(
        mapping=SmartsheetRowMappingResult(
            values={"Synthetic Column": "synthetic"},
            ready_for_write=False,
            duplicate_destination_columns=["Synthetic Column"],
        ),
        available_columns={"Synthetic Column": 101},
        available_column_types={"Synthetic Column": "TEXT_NUMBER"},
        available_system_column_types={"Synthetic Column": "none"},
    )
    assert none_result.rejection_safe_category == "row_mapping_value_missing"
    assert not duplicate_result.ready_for_write
    assert "row_mapping_duplicate_destination" in (
        duplicate_result.rejected_field_categories
    )


print(
    "=" * 60
)
print(
    "Testing Smartsheet Destination Validation"
)
print(
    "=" * 60
)

run_test(
    "complete schema is ready",
    test_complete_schema_is_ready,
)
run_test(
    "column IDs are resolved",
    test_column_ids_are_resolved,
)
run_test(
    "missing column blocks write",
    test_missing_column_blocks_write,
)
run_test(
    "invalid column ID blocks write",
    test_invalid_column_id_blocks_write,
)
run_test(
    "boolean column ID is rejected",
    test_boolean_column_id_is_rejected,
)
run_test(
    "coercible non-integer ID is rejected",
    test_coercible_non_integer_id_is_rejected,
)
run_test(
    "duplicate column ID blocks write",
    test_duplicate_column_id_blocks_write,
)
run_test(
    "upstream mapping block is preserved",
    test_upstream_mapping_block_is_preserved,
)
run_test(
    "invalid mapping is rejected",
    test_invalid_mapping_is_rejected,
)
run_test(
    "invalid schema is rejected",
    test_invalid_schema_is_rejected,
)
run_test(
    "empty mapping is not destination ready",
    test_empty_mapping_is_not_destination_ready,
)
run_test(
    "result excludes payload values",
    test_result_does_not_preserve_payload_values,
)
run_test("supported typed scalars are ready", test_supported_typed_scalars_are_ready)
run_test("checkbox requires boolean", test_checkbox_requires_literal_boolean)
run_test("date requires normalized ISO text", test_date_requires_normalized_iso_text)
run_test("TEXT_NUMBER rejects unsupported values", test_text_number_rejects_unsupported_values)
run_test("writable state must be proven", test_unproven_or_system_writable_state_blocks_write)
run_test("None and duplicate destinations block", test_none_and_duplicate_destination_contracts_block_write)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Synthetic deterministic test"
)
print(
    "External integration: Not called"
)
print(
    "PHI handling: Column names and IDs only"
)

if failed:
    raise SystemExit(
        1
    )
