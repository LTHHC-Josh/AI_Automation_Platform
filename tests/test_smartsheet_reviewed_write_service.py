from dataclasses import fields

from src.models.smartsheet_destination_validation import (
    SmartsheetDestinationValidationResult,
)
from src.models.smartsheet_mapping import (
    SmartsheetRowMappingResult,
)
from src.services.smartsheet_reviewed_write_service import (
    SmartsheetReviewedWriteResult,
    SmartsheetReviewedWriteService,
)


passed = 0
failed = 0


class RecordingSmartsheetClient:
    def __init__(
        self,
        *,
        fail=False,
    ):
        self.fail = fail
        self.add_calls = []

    def add_row(
        self,
        cells,
    ):
        self.add_calls.append(
            cells
        )

        if self.fail:
            raise RuntimeError(
                "Synthetic Smartsheet failure"
            )

        return object()


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
    ready=True,
):
    return SmartsheetRowMappingResult(
        values={
            "Authorization Status": (
                "Synthetic status"
            ),
            "Service Codes": (
                "SYNTHETIC-A | SYNTHETIC-B"
            ),
            "AI Review Required": False,
        },
        ready_for_write=ready,
    )


def build_validation(
    *,
    ready=True,
):
    return SmartsheetDestinationValidationResult(
        column_ids={
            "Authorization Status": 101,
            "Service Codes": 102,
            "AI Review Required": 103,
        },
        mapping_ready=ready,
        destination_ready=ready,
        ready_for_write=ready,
    )


def test_ready_mapping_is_written_once():
    client = RecordingSmartsheetClient()

    service = SmartsheetReviewedWriteService(
        client=client
    )

    result = service.write(
        mapping=build_mapping(),
        destination_validation=(
            build_validation()
        ),
    )

    assert result.success is True
    assert result.written is True
    assert result.column_count == 3
    assert result.status == "written"

    assert len(
        client.add_calls
    ) == 1

    assert len(
        client.add_calls[0]
    ) == 3


def test_cells_use_validated_column_ids():
    client = RecordingSmartsheetClient()

    service = SmartsheetReviewedWriteService(
        client=client
    )

    result = service.write(
        mapping=build_mapping(),
        destination_validation=(
            build_validation()
        ),
    )

    assert result.success is True

    cells = client.add_calls[0]

    assert [
        cell.column_id
        for cell in cells
    ] == [
        101,
        102,
        103,
    ]


def test_mapping_not_ready_blocks_write():
    client = RecordingSmartsheetClient()

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=build_mapping(
            ready=False
        ),
        destination_validation=(
            build_validation()
        ),
    )

    assert result.success is False
    assert result.written is False
    assert result.status == (
        "mapping_not_ready"
    )
    assert client.add_calls == []


def test_destination_not_ready_blocks_write():
    client = RecordingSmartsheetClient()

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=build_mapping(),
        destination_validation=(
            build_validation(
                ready=False
            )
        ),
    )

    assert result.success is False
    assert result.status == (
        "destination_not_ready"
    )
    assert client.add_calls == []


def test_destination_mismatch_blocks_write():
    client = RecordingSmartsheetClient()

    validation = build_validation()

    del validation.column_ids[
        "Service Codes"
    ]

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=build_mapping(),
        destination_validation=validation,
    )

    assert result.success is False
    assert result.status == (
        "destination_mismatch"
    )
    assert client.add_calls == []


def test_extra_validated_column_blocks_write():
    client = RecordingSmartsheetClient()

    validation = build_validation()

    validation.column_ids[
        "Unexpected Column"
    ] = 104

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=build_mapping(),
        destination_validation=validation,
    )

    assert result.success is False
    assert result.status == (
        "destination_mismatch"
    )
    assert client.add_calls == []


def test_invalid_column_id_blocks_write():
    client = RecordingSmartsheetClient()

    validation = build_validation()

    validation.column_ids[
        "Service Codes"
    ] = 0

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=build_mapping(),
        destination_validation=validation,
    )

    assert result.success is False
    assert result.status == (
        "invalid_column_id"
    )
    assert client.add_calls == []


def test_boolean_column_id_blocks_write():
    client = RecordingSmartsheetClient()

    validation = build_validation()

    validation.column_ids[
        "Service Codes"
    ] = True

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=build_mapping(),
        destination_validation=validation,
    )

    assert result.success is False
    assert result.status == (
        "invalid_column_id"
    )
    assert client.add_calls == []


def test_write_failure_is_sanitized():
    client = RecordingSmartsheetClient(
        fail=True
    )

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=build_mapping(),
        destination_validation=(
            build_validation()
        ),
    )

    assert result.success is False
    assert result.written is False
    assert result.column_count == 0
    assert result.status == (
        "smartsheet_write_failed"
    )

    result_text = repr(
        result
    )

    assert "Synthetic status" not in result_text
    assert "SYNTHETIC-A" not in result_text


def test_invalid_mapping_is_rejected():
    client = RecordingSmartsheetClient()

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=None,
        destination_validation=(
            build_validation()
        ),
    )

    assert result.success is False
    assert result.status == (
        "invalid_mapping"
    )
    assert client.add_calls == []


def test_invalid_validation_is_rejected():
    client = RecordingSmartsheetClient()

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=build_mapping(),
        destination_validation=None,
    )

    assert result.success is False
    assert result.status == (
        "invalid_destination_validation"
    )
    assert client.add_calls == []


def test_empty_mapping_is_rejected():
    client = RecordingSmartsheetClient()

    mapping = SmartsheetRowMappingResult(
        values={},
        ready_for_write=True,
    )

    validation = (
        SmartsheetDestinationValidationResult(
            column_ids={},
            mapping_ready=True,
            destination_ready=True,
            ready_for_write=True,
        )
    )

    result = SmartsheetReviewedWriteService(
        client=client
    ).write(
        mapping=mapping,
        destination_validation=validation,
    )

    assert result.success is False
    assert result.status == (
        "empty_mapping"
    )
    assert client.add_calls == []


def test_result_contract_is_phi_safe():
    result_fields = {
        field.name
        for field in fields(
            SmartsheetReviewedWriteResult
        )
    }

    assert result_fields == {
        "written",
        "column_count",
        "success",
        "status",
    }


print(
    "=" * 60
)
print(
    "Testing Smartsheet Reviewed Write"
)
print(
    "=" * 60
)

run_test(
    "ready mapping is written once",
    test_ready_mapping_is_written_once,
)
run_test(
    "cells use validated column IDs",
    test_cells_use_validated_column_ids,
)
run_test(
    "mapping not ready blocks write",
    test_mapping_not_ready_blocks_write,
)
run_test(
    "destination not ready blocks write",
    test_destination_not_ready_blocks_write,
)
run_test(
    "destination mismatch blocks write",
    test_destination_mismatch_blocks_write,
)
run_test(
    "extra validated column blocks write",
    test_extra_validated_column_blocks_write,
)
run_test(
    "invalid column ID blocks write",
    test_invalid_column_id_blocks_write,
)
run_test(
    "boolean column ID blocks write",
    test_boolean_column_id_blocks_write,
)
run_test(
    "write failure is sanitized",
    test_write_failure_is_sanitized,
)
run_test(
    "invalid mapping is rejected",
    test_invalid_mapping_is_rejected,
)
run_test(
    "invalid validation is rejected",
    test_invalid_validation_is_rejected,
)
run_test(
    "empty mapping is rejected",
    test_empty_mapping_is_rejected,
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
    "Real or mock: Mock Smartsheet write-boundary test"
)
print(
    "Smartsheet external API: Not called"
)
print(
    "OCR: Not called"
)
print(
    "Ollama: Not called"
)
print(
    "Microsoft Graph: Not called"
)
print(
    "PHI handling: Synthetic values only; "
    "write result excludes payload values"
)

if failed:
    raise SystemExit(
        1
    )
