from dataclasses import fields

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.complete_review_approval_service import (
    CompleteReviewApprovalResult,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionResult,
    SmartsheetReviewSubmissionService,
)
from src.services.smartsheet_reviewed_write_service import (
    SmartsheetReviewedWriteResult,
)


passed = 0
failed = 0


class RecordingWriteService:
    def __init__(
        self,
        *,
        result=None,
    ):
        self.calls = []
        self.result = (
            result
            or SmartsheetReviewedWriteResult(
                written=True,
                column_count=8,
                success=True,
                status="written",
            )
        )

    def write(
        self,
        *,
        mapping,
        destination_validation,
    ):
        self.calls.append(
            {
                "mapping_ready": (
                    mapping.ready_for_write
                ),
                "destination_ready": (
                    destination_validation
                    .ready_for_write
                ),
            }
        )

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


def build_review_output(
    *,
    needs_human_review=False,
):
    return ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="initial",
        classification_reason="Synthetic reason",
        classification_confidence=0.95,
        fields=[
            ReviewField(
                name="authorization_status",
                value="Synthetic status",
                confidence=0.95,
                source_text="Synthetic evidence",
            ),
        ],
        service_lines=[],
        validation_actions=[],
        rule_actions=[],
        needs_human_review=(
            needs_human_review
        ),
        review_status=(
            "Human Review Recommended"
            if needs_human_review
            else "Verified by AI"
        ),
        review_reasons=(
            [
                "Synthetic review reason"
            ]
            if needs_human_review
            else []
        ),
        minimum_field_confidence=0.95,
        extraction_attempt_count=1,
        extraction_retry_triggered=False,
        extraction_selected_attempt=1,
        authorized_units_reconciled=False,
    )


def build_policies():
    return [
        SmartsheetColumnPolicy(
            source_field="authorization_status",
            column_name="Authorization Status",
            required=True,
        ),
    ]


def build_columns():
    return {
        "Authorization Status": 1001,
        "AI Review Status": 1002,
        "AI Review Required": 1003,
        "AI Classification Confidence": 1004,
        "AI Minimum Field Confidence": 1005,
        "AI Selected Extraction Attempt": 1006,
        "AI Extraction Retry Triggered": 1007,
        "AI Authorized Units Reconciled": 1008,
    }


def approved_result():
    return CompleteReviewApprovalResult(
        approved=True,
        success=True,
        status="approved",
    )


def test_approved_review_reaches_writer_once():
    writer = RecordingWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=build_review_output(),
        approval_result=approved_result(),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result == SmartsheetReviewSubmissionResult(
        written=True,
        success=True,
        status="written",
    )

    assert len(
        writer.calls
    ) == 1

    assert (
        writer.calls[0]["mapping_ready"]
        is True
    )

    assert (
        writer.calls[0]["destination_ready"]
        is True
    )


def test_rejected_review_never_reaches_writer():
    writer = RecordingWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=build_review_output(),
        approval_result=(
            CompleteReviewApprovalResult(
                approved=False,
                success=True,
                status="rejected",
            )
        ),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.written is False
    assert result.success is False
    assert (
        result.status
        == "complete_review_not_approved"
    )

    assert writer.calls == []


def test_failed_approval_never_reaches_writer():
    writer = RecordingWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=build_review_output(),
        approval_result=(
            CompleteReviewApprovalResult(
                approved=False,
                success=False,
                status="review_still_required",
            )
        ),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.written is False
    assert result.success is False
    assert (
        result.status
        == "complete_review_not_approved"
    )

    assert writer.calls == []


def test_forged_success_without_approved_status_is_blocked():
    writer = RecordingWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=build_review_output(),
        approval_result=(
            CompleteReviewApprovalResult(
                approved=True,
                success=True,
                status="confirmed",
            )
        ),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.written is False
    assert result.success is False
    assert (
        result.status
        == "complete_review_not_approved"
    )

    assert writer.calls == []


def test_review_requirement_still_blocks_mapping():
    writer = RecordingWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=build_review_output(
            needs_human_review=True
        ),
        approval_result=approved_result(),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.written is False
    assert result.success is False
    assert result.status == "mapping_not_ready"

    assert writer.calls == []


def test_missing_destination_blocks_writer():
    writer = RecordingWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    columns = build_columns()

    del columns[
        "Authorization Status"
    ]

    result = service.submit(
        review_output=build_review_output(),
        approval_result=approved_result(),
        policies=build_policies(),
        available_columns=columns,
    )

    assert result.written is False
    assert result.success is False
    assert (
        result.status
        == "destination_not_ready"
    )

    assert writer.calls == []


def test_writer_failure_is_preserved_safely():
    writer = RecordingWriteService(
        result=SmartsheetReviewedWriteResult(
            written=False,
            column_count=0,
            success=False,
            status="smartsheet_write_failed",
        )
    )

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=build_review_output(),
        approval_result=approved_result(),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.written is False
    assert result.success is False
    assert (
        result.status
        == "smartsheet_write_failed"
    )

    assert len(
        writer.calls
    ) == 1


def test_invalid_approval_contract_is_blocked():
    writer = RecordingWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=build_review_output(),
        approval_result=None,
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.written is False
    assert result.success is False
    assert (
        result.status
        == "invalid_approval_result"
    )

    assert writer.calls == []


def test_invalid_review_output_is_blocked():
    writer = RecordingWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=None,
        approval_result=approved_result(),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.written is False
    assert result.success is False
    assert (
        result.status
        == "invalid_review_output"
    )

    assert writer.calls == []


def test_result_contract_is_phi_safe():
    result_field_names = {
        item.name
        for item in fields(
            SmartsheetReviewSubmissionResult
        )
    }

    assert result_field_names == {
        "written",
        "success",
        "status",
    }

    prohibited_names = {
        "value",
        "values",
        "source_text",
        "raw_text",
        "file_path",
        "filename",
        "fields",
        "service_lines",
        "payload",
        "row_id",
        "column_ids",
    }

    assert (
        result_field_names
        .isdisjoint(
            prohibited_names
        )
    )


print(
    "=" * 60
)
print(
    "Testing Approval-Gated Smartsheet Submission"
)
print(
    "=" * 60
)

run_test(
    "approved review reaches writer once",
    test_approved_review_reaches_writer_once,
)

run_test(
    "rejected review blocks writer",
    test_rejected_review_never_reaches_writer,
)

run_test(
    "failed approval blocks writer",
    test_failed_approval_never_reaches_writer,
)

run_test(
    "non-approved status blocks writer",
    test_forged_success_without_approved_status_is_blocked,
)

run_test(
    "remaining review requirement blocks mapping",
    test_review_requirement_still_blocks_mapping,
)

run_test(
    "missing destination blocks writer",
    test_missing_destination_blocks_writer,
)

run_test(
    "writer failure remains PHI-safe",
    test_writer_failure_is_preserved_safely,
)

run_test(
    "invalid approval contract is blocked",
    test_invalid_approval_contract_is_blocked,
)

run_test(
    "invalid review output is blocked",
    test_invalid_review_output_is_blocked,
)

run_test(
    "submission result is PHI-safe",
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
    "Microsoft Graph: Not called"
)
print(
    "OCR: Not called"
)
print(
    "Ollama: Not called"
)
print(
    "PHI handling: Synthetic values only; "
    "mapped payload not printed"
)

if failed:
    raise SystemExit(1)
