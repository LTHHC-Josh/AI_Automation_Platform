from dataclasses import fields

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.complete_review_approval_service import (
    CompleteReviewApprovalResult,
)
from src.services.complete_review_smartsheet_workflow_service import (
    CompleteReviewSmartsheetWorkflowResult,
    CompleteReviewSmartsheetWorkflowService,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionResult,
)


passed = 0
failed = 0


class RecordingReviewInteraction:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.calls = []

    def run(
        self,
        *,
        review_output,
    ):
        self.calls.append(
            review_output
        )

        return self.result


class RecordingSubmissionService:
    def __init__(
        self,
        *,
        result=None,
    ):
        self.calls = []

        self.result = (
            result
            or SmartsheetReviewSubmissionResult(
                written=True,
                success=True,
                status="written",
            )
        )

    def submit(
        self,
        *,
        review_output,
        approval_result,
        policies,
        available_columns,
    ):
        self.calls.append(
            {
                "review_output": review_output,
                "approval_result": approval_result,
                "policy_count": len(
                    policies
                ),
                "column_count": len(
                    available_columns
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


def build_review_output():
    return ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_reason=(
            "PRIVATE-SYNTHETIC-REASON"
        ),
        classification_confidence=0.95,
        fields=[
            ReviewField(
                name="authorization_status",
                value="PRIVATE-SYNTHETIC-STATUS",
                confidence=0.95,
                source_text=(
                    "PRIVATE-SYNTHETIC-EVIDENCE"
                ),
            ),
        ],
        service_lines=[],
        validation_actions=[],
        rule_actions=[],
        needs_human_review=False,
        review_status="Verified by AI",
        review_reasons=[],
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


def test_approved_review_reaches_submission_once():
    interaction = RecordingReviewInteraction(
        approved_result()
    )

    submission = RecordingSubmissionService()

    service = (
        CompleteReviewSmartsheetWorkflowService(
            review_interaction=interaction,
            submission_service=submission,
        )
    )

    review_output = build_review_output()

    result = service.run(
        review_output=review_output,
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result == (
        CompleteReviewSmartsheetWorkflowResult(
            approved=True,
            written=True,
            success=True,
            status="written",
        )
    )

    assert interaction.calls == [
        review_output
    ]

    assert len(
        submission.calls
    ) == 1

    assert (
        submission.calls[0][
            "approval_result"
        ].approved
        is True
    )


def test_rejection_never_reaches_submission():
    interaction = RecordingReviewInteraction(
        CompleteReviewApprovalResult(
            approved=False,
            success=True,
            status="rejected",
        )
    )

    submission = RecordingSubmissionService()

    service = (
        CompleteReviewSmartsheetWorkflowService(
            review_interaction=interaction,
            submission_service=submission,
        )
    )

    result = service.run(
        review_output=build_review_output(),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.approved is False
    assert result.written is False
    assert result.success is True
    assert result.status == "rejected"

    assert submission.calls == []


def test_cancellation_never_reaches_submission():
    interaction = RecordingReviewInteraction(
        CompleteReviewApprovalResult(
            approved=False,
            success=False,
            status="cancelled",
        )
    )

    submission = RecordingSubmissionService()

    service = (
        CompleteReviewSmartsheetWorkflowService(
            review_interaction=interaction,
            submission_service=submission,
        )
    )

    result = service.run(
        review_output=build_review_output(),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.approved is False
    assert result.written is False
    assert result.status == "cancelled"

    assert submission.calls == []


def test_unresolved_review_never_reaches_submission():
    interaction = RecordingReviewInteraction(
        CompleteReviewApprovalResult(
            approved=False,
            success=False,
            status="review_still_required",
        )
    )

    submission = RecordingSubmissionService()

    service = (
        CompleteReviewSmartsheetWorkflowService(
            review_interaction=interaction,
            submission_service=submission,
        )
    )

    result = service.run(
        review_output=build_review_output(),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.approved is False
    assert result.written is False
    assert result.success is False

    assert (
        result.status
        == "review_still_required"
    )

    assert submission.calls == []


def test_submission_failure_is_preserved():
    interaction = RecordingReviewInteraction(
        approved_result()
    )

    submission = RecordingSubmissionService(
        result=SmartsheetReviewSubmissionResult(
            written=False,
            success=False,
            status="destination_not_ready",
        )
    )

    service = (
        CompleteReviewSmartsheetWorkflowService(
            review_interaction=interaction,
            submission_service=submission,
        )
    )

    result = service.run(
        review_output=build_review_output(),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.approved is True
    assert result.written is False
    assert result.success is False

    assert (
        result.status
        == "destination_not_ready"
    )

    assert len(
        submission.calls
    ) == 1


def test_invalid_review_output_calls_nothing():
    interaction = RecordingReviewInteraction(
        approved_result()
    )

    submission = RecordingSubmissionService()

    service = (
        CompleteReviewSmartsheetWorkflowService(
            review_interaction=interaction,
            submission_service=submission,
        )
    )

    result = service.run(
        review_output=None,
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.approved is False
    assert result.written is False
    assert result.success is False

    assert (
        result.status
        == "invalid_review_output"
    )

    assert interaction.calls == []
    assert submission.calls == []


def test_same_review_output_is_forwarded():
    interaction = RecordingReviewInteraction(
        approved_result()
    )

    submission = RecordingSubmissionService()

    service = (
        CompleteReviewSmartsheetWorkflowService(
            review_interaction=interaction,
            submission_service=submission,
        )
    )

    review_output = build_review_output()

    service.run(
        review_output=review_output,
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert (
        submission.calls[0][
            "review_output"
        ]
        is review_output
    )


def test_result_contract_is_phi_safe():
    field_names = {
        field.name
        for field in fields(
            CompleteReviewSmartsheetWorkflowResult
        )
    }

    assert field_names == {
        "approved",
        "written",
        "success",
        "status",
    }

    prohibited_names = {
        "values",
        "value",
        "source_text",
        "raw_text",
        "file_path",
        "filename",
        "fields",
        "service_lines",
        "payload",
        "row_id",
        "column_ids",
        "fingerprint",
    }

    assert field_names.isdisjoint(
        prohibited_names
    )


print(
    "=" * 60
)
print(
    "Testing Complete Review to Smartsheet Workflow"
)
print(
    "=" * 60
)

run_test(
    "approved review reaches submission once",
    test_approved_review_reaches_submission_once,
)

run_test(
    "rejection blocks submission",
    test_rejection_never_reaches_submission,
)

run_test(
    "cancellation blocks submission",
    test_cancellation_never_reaches_submission,
)

run_test(
    "unresolved review blocks submission",
    test_unresolved_review_never_reaches_submission,
)

run_test(
    "submission failure is preserved",
    test_submission_failure_is_preserved,
)

run_test(
    "invalid review output calls nothing",
    test_invalid_review_output_calls_nothing,
)

run_test(
    "same review output is forwarded",
    test_same_review_output_is_forwarded,
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
    "Real or mock: Synthetic deterministic/mock coordinator test"
)
print(
    "Complete-review interaction: Mocked"
)
print(
    "Smartsheet submission service: Mocked"
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
    "review and mapped payloads not printed"
)

if failed:
    raise SystemExit(1)
