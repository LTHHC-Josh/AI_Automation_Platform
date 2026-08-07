from dataclasses import fields

from src.services.complete_review_approval_service import (
    CompleteReviewApprovalResult,
    CompleteReviewApprovalService,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
    ReviewServiceLine,
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


def build_review_output(
    *,
    needs_human_review=False,
):
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
        service_lines=[
            ReviewServiceLine(
                service_code="SYNTHETIC-CODE",
                quantity=1,
                confidence=0.95,
                source_text=(
                    "Synthetic row evidence"
                ),
            ),
        ],
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
                "Synthetic unresolved reason"
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


def test_explicit_approval_succeeds():
    service = (
        CompleteReviewApprovalService()
    )

    result = service.decide(
        review_output=build_review_output(),
        reviewer_decision="approved",
    )

    assert result == CompleteReviewApprovalResult(
        approved=True,
        success=True,
        status="approved",
    )


def test_approval_is_normalized():
    service = (
        CompleteReviewApprovalService()
    )

    result = service.decide(
        review_output=build_review_output(),
        reviewer_decision="  APPROVED  ",
    )

    assert result.approved is True
    assert result.success is True
    assert result.status == "approved"


def test_explicit_rejection_succeeds_without_approval():
    service = (
        CompleteReviewApprovalService()
    )

    result = service.decide(
        review_output=build_review_output(),
        reviewer_decision="rejected",
    )

    assert result == CompleteReviewApprovalResult(
        approved=False,
        success=True,
        status="rejected",
    )


def test_unresolved_review_blocks_approval():
    service = (
        CompleteReviewApprovalService()
    )

    result = service.decide(
        review_output=build_review_output(
            needs_human_review=True
        ),
        reviewer_decision="approved",
    )

    assert result.approved is False
    assert result.success is False
    assert (
        result.status
        == "review_still_required"
    )


def test_unresolved_review_can_be_rejected():
    service = (
        CompleteReviewApprovalService()
    )

    result = service.decide(
        review_output=build_review_output(
            needs_human_review=True
        ),
        reviewer_decision="rejected",
    )

    assert result.approved is False
    assert result.success is True
    assert result.status == "rejected"


def test_non_explicit_decision_is_blocked():
    service = (
        CompleteReviewApprovalService()
    )

    for decision in (
        None,
        "",
        "confirm",
        "yes",
        "automatic",
        True,
    ):
        result = service.decide(
            review_output=build_review_output(),
            reviewer_decision=decision,
        )

        assert result.approved is False
        assert result.success is False
        assert (
            result.status
            == "decision_not_explicit"
        )


def test_invalid_review_output_is_blocked():
    service = (
        CompleteReviewApprovalService()
    )

    result = service.decide(
        review_output=None,
        reviewer_decision="approved",
    )

    assert result.approved is False
    assert result.success is False
    assert (
        result.status
        == "invalid_review_output"
    )


def test_service_does_not_mutate_review_output():
    service = (
        CompleteReviewApprovalService()
    )

    review_output = build_review_output()

    original_field_value = (
        review_output.fields[0].value
    )

    original_source_text = (
        review_output.fields[0].source_text
    )

    original_service_line_value = (
        review_output.service_lines[0]
        .service_code
    )

    result = service.decide(
        review_output=review_output,
        reviewer_decision="approved",
    )

    assert result.approved is True

    assert (
        review_output.fields[0].value
        == original_field_value
    )

    assert (
        review_output.fields[0].source_text
        == original_source_text
    )

    assert (
        review_output.service_lines[0]
        .service_code
        == original_service_line_value
    )


def test_result_contract_is_phi_safe():
    result_field_names = {
        item.name
        for item in fields(
            CompleteReviewApprovalResult
        )
    }

    assert result_field_names == {
        "approved",
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
        "fingerprint",
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
    "Testing Complete Review Approval Boundary"
)
print(
    "=" * 60
)

run_test(
    "explicit approval succeeds",
    test_explicit_approval_succeeds,
)

run_test(
    "approval decision is normalized",
    test_approval_is_normalized,
)

run_test(
    "explicit rejection succeeds",
    test_explicit_rejection_succeeds_without_approval,
)

run_test(
    "unresolved review blocks approval",
    test_unresolved_review_blocks_approval,
)

run_test(
    "unresolved review can be rejected",
    test_unresolved_review_can_be_rejected,
)

run_test(
    "non-explicit decision is blocked",
    test_non_explicit_decision_is_blocked,
)

run_test(
    "invalid review output is blocked",
    test_invalid_review_output_is_blocked,
)

run_test(
    "review output is not mutated",
    test_service_does_not_mutate_review_output,
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
    "Smartsheet: Not called"
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
    "review payload not printed"
)

if failed:
    raise SystemExit(1)
