from src.services.complete_review_approval_service import (
    CompleteReviewApprovalResult,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
    ReviewServiceLine,
)
from src.ui.complete_review_approval_interaction import (
    CompleteReviewApprovalInteraction,
)


passed = 0
failed = 0


class InputSequence:
    def __init__(
        self,
        values,
    ):
        self.values = list(
            values
        )
        self.prompts = []

    def __call__(
        self,
        prompt,
    ):
        self.prompts.append(
            prompt
        )

        if not self.values:
            raise AssertionError(
                "Unexpected input request."
            )

        return self.values.pop(
            0
        )


class OutputRecorder:
    def __init__(self):
        self.lines = []

    def __call__(
        self,
        value,
    ):
        self.lines.append(
            str(
                value
            )
        )


class RecordingApprovalService:
    def __init__(
        self,
        *,
        result=None,
    ):
        self.calls = []

        self.result = (
            result
            or CompleteReviewApprovalResult(
                approved=True,
                success=True,
                status="approved",
            )
        )

    def decide(
        self,
        *,
        review_output,
        reviewer_decision,
    ):
        self.calls.append(
            {
                "review_output": review_output,
                "reviewer_decision": (
                    reviewer_decision
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
        document_subtype="renewal",
        classification_reason=(
            "PRIVATE-SYNTHETIC-CLASSIFICATION-REASON"
        ),
        classification_confidence=0.91,
        fields=[
            ReviewField(
                name="patient_name",
                value="PRIVATE-SYNTHETIC-PATIENT",
                confidence=0.95,
                source_text=(
                    "PRIVATE-SYNTHETIC-FIELD-EVIDENCE"
                ),
            ),
            ReviewField(
                name="authorization_status",
                value="PRIVATE-SYNTHETIC-STATUS",
                confidence=0.95,
                source_text=(
                    "PRIVATE-SYNTHETIC-STATUS-EVIDENCE"
                ),
            ),
        ],
        service_lines=[
            ReviewServiceLine(
                service_code=(
                    "PRIVATE-SYNTHETIC-CODE"
                ),
                quantity=1,
                confidence=0.95,
                source_text=(
                    "PRIVATE-SYNTHETIC-ROW-EVIDENCE"
                ),
            ),
        ],
        validation_actions=[
            "Synthetic validation action"
        ],
        rule_actions=[
            "Synthetic rule action"
        ],
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
                "PRIVATE-SYNTHETIC-REVIEW-REASON"
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


def build_interaction(
    inputs,
    approval_service=None,
):
    input_reader = InputSequence(
        inputs
    )

    output_writer = OutputRecorder()

    interaction = (
        CompleteReviewApprovalInteraction(
            approval_service=(
                approval_service
                or RecordingApprovalService()
            ),
            input_reader=input_reader,
            output_writer=output_writer,
        )
    )

    return (
        interaction,
        input_reader,
        output_writer,
    )


def test_approve_submits_explicit_approved_decision():
    approval_service = (
        RecordingApprovalService()
    )

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["1"],
        approval_service,
    )

    review_output = build_review_output()

    result = interaction.run(
        review_output=review_output
    )

    assert result.approved is True
    assert result.success is True

    assert len(
        approval_service.calls
    ) == 1

    assert (
        approval_service.calls[0][
            "review_output"
        ]
        is review_output
    )

    assert (
        approval_service.calls[0][
            "reviewer_decision"
        ]
        == "approved"
    )


def test_explicit_approval_skips_terminal_prompt():
    approval_service = (
        RecordingApprovalService()
    )

    (
        interaction,
        input_reader,
        output,
    ) = build_interaction(
        [],
        approval_service,
    )

    review_output = build_review_output()

    result = interaction.run(
        review_output=review_output,
        approve_without_prompt=True,
    )

    assert result.approved is True
    assert result.success is True
    assert input_reader.prompts == []

    assert approval_service.calls == [
        {
            "review_output": review_output,
            "reviewer_decision": "approved",
        }
    ]

    assert (
        "Approval status: approved"
        in output.lines
    )


def test_reject_submits_explicit_rejected_decision():
    approval_service = (
        RecordingApprovalService(
            result=CompleteReviewApprovalResult(
                approved=False,
                success=True,
                status="rejected",
            )
        )
    )

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["2"],
        approval_service,
    )

    result = interaction.run(
        review_output=build_review_output()
    )

    assert result.approved is False
    assert result.success is True
    assert result.status == "rejected"

    assert (
        approval_service.calls[0][
            "reviewer_decision"
        ]
        == "rejected"
    )


def test_cancel_does_not_call_approval_service():
    approval_service = (
        RecordingApprovalService()
    )

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["0"],
        approval_service,
    )

    result = interaction.run(
        review_output=build_review_output()
    )

    assert result.approved is False
    assert result.success is False
    assert result.status == "cancelled"

    assert approval_service.calls == []


def test_invalid_selection_does_not_call_service():
    approval_service = (
        RecordingApprovalService()
    )

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["9"],
        approval_service,
    )

    result = interaction.run(
        review_output=build_review_output()
    )

    assert result.approved is False
    assert result.success is False
    assert (
        result.status
        == "invalid_selection"
    )

    assert approval_service.calls == []


def test_invalid_review_output_is_rejected():
    approval_service = (
        RecordingApprovalService()
    )

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        [],
        approval_service,
    )

    result = interaction.run(
        review_output=None
    )

    assert result.approved is False
    assert result.success is False

    assert (
        result.status
        == "invalid_review_output"
    )

    assert approval_service.calls == []


def test_unresolved_review_status_is_preserved():
    approval_service = (
        RecordingApprovalService(
            result=CompleteReviewApprovalResult(
                approved=False,
                success=False,
                status="review_still_required",
            )
        )
    )

    (
        interaction,
        _,
        output,
    ) = build_interaction(
        ["1"],
        approval_service,
    )

    result = interaction.run(
        review_output=build_review_output(
            needs_human_review=True
        )
    )

    assert result.approved is False
    assert result.success is False

    assert (
        result.status
        == "review_still_required"
    )

    assert (
        "Approval status: review_still_required"
        in output.lines
    )


def test_output_contains_only_phi_safe_metadata():
    approval_service = (
        RecordingApprovalService()
    )

    (
        interaction,
        _,
        output,
    ) = build_interaction(
        ["1"],
        approval_service,
    )

    review_output = build_review_output(
        needs_human_review=True
    )

    interaction.run(
        review_output=review_output
    )

    rendered = "\n".join(
        output.lines
    )

    assert "Fields present       : 2" in rendered

    assert (
        "Service lines present: 1"
        in rendered
    )

    assert (
        "Review still required: True"
        in rendered
    )

    assert (
        "Review reason count  : 1"
        in rendered
    )

    prohibited_values = {
        review_output.classification_reason,
        review_output.fields[0].value,
        review_output.fields[0].source_text,
        review_output.fields[1].value,
        review_output.fields[1].source_text,
        review_output.service_lines[0].service_code,
        review_output.service_lines[0].source_text,
        review_output.review_reasons[0],
    }

    assert all(
        value not in rendered
        for value in prohibited_values
    )


def test_interaction_does_not_mutate_review_output():
    approval_service = (
        RecordingApprovalService()
    )

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["1"],
        approval_service,
    )

    review_output = build_review_output()

    original_fields = list(
        review_output.fields
    )

    original_service_lines = list(
        review_output.service_lines
    )

    original_review_reasons = list(
        review_output.review_reasons
    )

    interaction.run(
        review_output=review_output
    )

    assert (
        review_output.fields
        == original_fields
    )

    assert (
        review_output.service_lines
        == original_service_lines
    )

    assert (
        review_output.review_reasons
        == original_review_reasons
    )


print(
    "=" * 60
)
print(
    "Testing Complete Review Approval Interaction"
)
print(
    "=" * 60
)

run_test(
    "approve submits explicit approved decision",
    test_approve_submits_explicit_approved_decision,
)

run_test(
    "explicit approval skips terminal prompt",
    test_explicit_approval_skips_terminal_prompt,
)

run_test(
    "reject submits explicit rejected decision",
    test_reject_submits_explicit_rejected_decision,
)

run_test(
    "cancel does not call approval service",
    test_cancel_does_not_call_approval_service,
)

run_test(
    "invalid selection does not call approval service",
    test_invalid_selection_does_not_call_service,
)

run_test(
    "invalid review output is rejected",
    test_invalid_review_output_is_rejected,
)

run_test(
    "unresolved review status is preserved",
    test_unresolved_review_status_is_preserved,
)

run_test(
    "output contains only PHI-safe metadata",
    test_output_contains_only_phi_safe_metadata,
)

run_test(
    "review output is not mutated",
    test_interaction_does_not_mutate_review_output,
)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Synthetic deterministic UI-boundary test"
)
print(
    "Complete approval service: Mocked"
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
    "External integration: Not called"
)
print(
    "PHI handling: Counts, boolean review state, "
    "and PHI-safe status only"
)

if failed:
    raise SystemExit(1)
