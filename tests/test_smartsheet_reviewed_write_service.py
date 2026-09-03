from dataclasses import fields
from pathlib import Path

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


class SyntheticRow:
    def __init__(
        self,
        row_id=4242,
    ):
        self.id = row_id


class RecordingAttachmentNamingService:
    def __init__(
        self,
        *,
        cleanup_result=True,
        preparation_status="prepared",
    ):
        self.cleanup_result = cleanup_result
        self.preparation_status = preparation_status
        self.prepare_calls = []
        self.cleanup_calls = []

    def prepare(
        self,
        *,
        source_path,
        filename_policy_result=None,
    ):
        from src.services.document_attachment_naming_service import (
            DocumentAttachmentPreparationResult,
        )

        self.prepare_calls.append((source_path, filename_policy_result))

        return DocumentAttachmentPreparationResult(
            prepared=True,
            temporary_path=Path(
                "SYNTHETIC_TEMP.pdf"
            ),
            success=True,
            status=self.preparation_status,
        )

    def cleanup(
        self,
        temporary_path,
    ):
        self.cleanup_calls.append(
            temporary_path
        )

        return self.cleanup_result


class RecordingSmartsheetClient:
    def __init__(
        self,
        *,
        fail=False,
        row_id=4242,
        attachment_fail=False,
    ):
        self.fail = fail
        self.row_id = row_id
        self.attachment_fail = attachment_fail
        self.add_calls = []
        self.attachment_calls = []

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

        return SyntheticRow(
            self.row_id
        )

    def attach_file_to_row(
        self,
        row_id,
        file_path,
    ):
        self.attachment_calls.append(
            {
                "row_id": row_id,
                "file_path": file_path,
            }
        )

        if self.attachment_fail:
            raise RuntimeError(
                "PRIVATE-SYNTHETIC-ATTACHMENT-FAILURE"
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


def test_attachment_uses_created_row_and_cleans_temp():
    client = RecordingSmartsheetClient(
        row_id=9876
    )

    naming = RecordingAttachmentNamingService()

    service = SmartsheetReviewedWriteService(
        client=client,
        attachment_naming_service=naming,
    )

    source_path = Path(
        "PRIVATE-SYNTHETIC-SOURCE.pdf"
    )

    result = service.write(
        mapping=build_mapping(),
        destination_validation=build_validation(),
        attachment_source_path=source_path,
    )

    assert result.written is True
    assert result.attachment_written is True
    assert result.success is True

    assert (
        result.status
        == "written_with_attachment"
    )

    assert naming.prepare_calls == [(source_path, None)]

    assert client.attachment_calls == [
        {
            "row_id": 9876,
            "file_path": Path(
                "SYNTHETIC_TEMP.pdf"
            ),
        }
    ]

    assert naming.cleanup_calls == [
        Path(
            "SYNTHETIC_TEMP.pdf"
        )
    ]


def test_attachment_failure_is_sanitized_and_cleaned():
    client = RecordingSmartsheetClient(
        attachment_fail=True
    )

    naming = RecordingAttachmentNamingService()

    service = SmartsheetReviewedWriteService(
        client=client,
        attachment_naming_service=naming,
    )

    result = service.write(
        mapping=build_mapping(),
        destination_validation=build_validation(),
        attachment_source_path=Path(
            "PRIVATE-SYNTHETIC-SOURCE.pdf"
        ),
    )

    assert result.written is True
    assert result.attachment_written is False
    assert result.success is False

    assert (
        result.status
        == "smartsheet_attachment_failed"
    )

    assert (
        "PRIVATE-SYNTHETIC-ATTACHMENT-FAILURE"
        not in repr(result)
    )

    assert naming.cleanup_calls == [
        Path(
            "SYNTHETIC_TEMP.pdf"
        )
    ]


def test_invalid_created_row_blocks_attachment():
    client = RecordingSmartsheetClient(
        row_id=None
    )

    naming = RecordingAttachmentNamingService()

    service = SmartsheetReviewedWriteService(
        client=client,
        attachment_naming_service=naming,
    )

    result = service.write(
        mapping=build_mapping(),
        destination_validation=build_validation(),
        attachment_source_path=Path(
            "PRIVATE-SYNTHETIC-SOURCE.pdf"
        ),
    )

    assert result.written is False
    assert result.attachment_written is False
    assert result.success is False

    assert (
        result.status
        == "row_write_response_invalid"
    )

    assert client.attachment_calls == []

    assert naming.cleanup_calls == []


def test_no_attachment_preserves_legacy_write():
    client = RecordingSmartsheetClient()
    naming = RecordingAttachmentNamingService()

    service = SmartsheetReviewedWriteService(
        client=client,
        attachment_naming_service=naming,
    )

    result = service.write(
        mapping=build_mapping(),
        destination_validation=build_validation(),
    )

    assert result.written is True
    assert result.attachment_written is False
    assert result.success is True
    assert result.status == "written"

    assert client.attachment_calls == []
    assert naming.prepare_calls == []
    assert naming.cleanup_calls == []


def test_unresolved_filename_policy_uses_attachment_fallback_and_safe_review_status():
    from src.services.filename_policy_service import FilenamePolicyResult

    client = RecordingSmartsheetClient()
    naming = RecordingAttachmentNamingService(
        preparation_status="prepared_naming_fallback_review"
    )
    policy = FilenamePolicyResult(
        complete=False,
        filename=None,
        review_required=True,
        status="workflow_token_unresolved",
    )
    result = SmartsheetReviewedWriteService(
        client=client,
        attachment_naming_service=naming,
    ).write(
        mapping=build_mapping(),
        destination_validation=build_validation(),
        attachment_source_path=Path("PRIVATE-SYNTHETIC-SOURCE.pdf"),
        filename_policy_result=policy,
    )
    assert result.success is True
    assert result.status == "written_with_attachment_naming_review"
    assert naming.prepare_calls == [
        (Path("PRIVATE-SYNTHETIC-SOURCE.pdf"), policy)
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
        "row_write_outcome_unknown"
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
        "attachment_written",
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
    "attachment uses created row and cleans temp",
    test_attachment_uses_created_row_and_cleans_temp,
)

run_test(
    "attachment failure is sanitized and cleaned",
    test_attachment_failure_is_sanitized_and_cleaned,
)

run_test(
    "invalid created row blocks attachment",
    test_invalid_created_row_blocks_attachment,
)

run_test(
    "no attachment preserves legacy write",
    test_no_attachment_preserves_legacy_write,
)
run_test(
    "unresolved filename policy preserves fallback",
    test_unresolved_filename_policy_uses_attachment_fallback_and_safe_review_status,
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
