from src.models.smartsheet_mapping import (
    SmartsheetRowMappingResult,
)
from src.services.smartsheet_destination_validation_service import (
    SmartsheetDestinationValidationService,
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


def build_mapping(
    *,
    ready_for_write=True,
):
    return SmartsheetRowMappingResult(
        values={
            "Authorization Status": "Synthetic value",
            "Service Codes": "Synthetic value",
            "AI Review Status": "Verified by AI",
            "AI Review Required": False,
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


def test_complete_schema_is_ready():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=build_mapping(),
        available_columns=build_columns(),
    )

    assert result.mapping_ready is True
    assert result.destination_ready is True
    assert result.ready_for_write is True


def test_column_ids_are_resolved():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=build_mapping(),
        available_columns=build_columns(),
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
    )

    assert result.invalid_columns == [
        "Service Codes"
    ]


def test_numeric_string_id_is_normalized():
    service = SmartsheetDestinationValidationService()

    columns = build_columns()
    columns[
        "Service Codes"
    ] = "102"

    result = service.validate(
        mapping=build_mapping(),
        available_columns=columns,
    )

    assert result.column_ids[
        "Service Codes"
    ] == 102
    assert result.ready_for_write is True


def test_duplicate_column_id_blocks_write():
    service = SmartsheetDestinationValidationService()

    columns = build_columns()
    columns[
        "Service Codes"
    ] = 101

    result = service.validate(
        mapping=build_mapping(),
        available_columns=columns,
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
    )

    assert result.destination_ready is True
    assert result.mapping_ready is False
    assert result.ready_for_write is False


def test_invalid_mapping_is_rejected():
    service = SmartsheetDestinationValidationService()

    result = service.validate(
        mapping=None,
        available_columns=build_columns(),
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
    )

    assert result.destination_ready is False
    assert result.ready_for_write is False


def test_result_does_not_preserve_payload_values():
    service = SmartsheetDestinationValidationService()

    mapping = build_mapping()

    result = service.validate(
        mapping=mapping,
        available_columns=build_columns(),
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
    "numeric string ID is normalized",
    test_numeric_string_id_is_normalized,
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
