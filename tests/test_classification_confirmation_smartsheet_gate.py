from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.review_confirmation_submission_service import (
    ReviewConfirmationSubmissionResult,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionService,
)


passed = 0
failed = 0


class FailIfCalledWriteService:
    def __init__(self):
        self.call_count = 0

    def write(
        self,
        *,
        mapping,
        destination_validation,
    ):
        self.call_count += 1

        raise AssertionError(
            "Smartsheet writer must not be called."
        )


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
        document_subtype="initial",
        classification_reason=(
            "Synthetic classification reason"
        ),
        classification_confidence=0.95,
        fields=[
            ReviewField(
                name="authorization_status",
                value="Synthetic status",
                confidence=0.95,
                source_text=(
                    "Synthetic source evidence"
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


def build_successful_classification_confirmation():
    return ReviewConfirmationSubmissionResult(
        fingerprint="a" * 64,
        byte_count=25,
        success=True,
        status="stored",
    )


def test_classification_confirmation_is_not_approval():
    writer = FailIfCalledWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    result = service.submit(
        review_output=build_review_output(),
        approval_result=(
            build_successful_classification_confirmation()
        ),
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.written is False
    assert result.success is False

    assert (
        result.status
        == "invalid_approval_result"
    )

    assert writer.call_count == 0


def test_classification_success_flag_is_not_authorization():
    writer = FailIfCalledWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    classification_result = (
        build_successful_classification_confirmation()
    )

    assert classification_result.success is True

    result = service.submit(
        review_output=build_review_output(),
        approval_result=classification_result,
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.success is False
    assert result.written is False
    assert writer.call_count == 0


def test_classification_status_is_not_approval_status():
    writer = FailIfCalledWriteService()

    service = (
        SmartsheetReviewSubmissionService(
            write_service=writer
        )
    )

    classification_result = (
        ReviewConfirmationSubmissionResult(
            fingerprint="b" * 64,
            byte_count=25,
            success=True,
            status="approved",
        )
    )

    result = service.submit(
        review_output=build_review_output(),
        approval_result=classification_result,
        policies=build_policies(),
        available_columns=build_columns(),
    )

    assert result.success is False
    assert result.written is False

    assert (
        result.status
        == "invalid_approval_result"
    )

    assert writer.call_count == 0


print(
    "=" * 60
)
print(
    "Testing Classification-to-Smartsheet Safety Gate"
)
print(
    "=" * 60
)

run_test(
    "classification confirmation is not complete approval",
    test_classification_confirmation_is_not_approval,
)

run_test(
    "classification success does not authorize writing",
    test_classification_success_flag_is_not_authorization,
)

run_test(
    "classification status text cannot impersonate approval",
    test_classification_status_is_not_approval_status,
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
    "Classification feedback storage: Not called"
)
print(
    "Smartsheet external API: Not called"
)
print(
    "Smartsheet writer calls: 0 expected"
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
