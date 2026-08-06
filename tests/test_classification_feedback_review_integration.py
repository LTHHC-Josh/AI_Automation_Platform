from dataclasses import asdict

from src.services.classification_feedback_review_service import (
    ClassificationFeedbackReviewService,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
    ReviewServiceLine,
)


passed = 0
failed = 0

FINGERPRINT = "b" * 64
TIMESTAMP = "2026-08-06T16:00:00Z"


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
    category="authorization",
    subtype="unknown",
    confidence=0.88,
):
    return ReviewOutput(
        document_type="authorization",
        document_category=category,
        document_subtype=subtype,
        classification_reason=(
            "Synthetic classification reason."
        ),
        classification_confidence=confidence,
        fields=[
            ReviewField(
                name="patient_name",
                value="Synthetic Patient",
                confidence=0.95,
                source_text="Synthetic patient evidence",
            ),
            ReviewField(
                name="authorization_number",
                value="SYNTHETIC-AUTH",
                confidence=0.95,
                source_text="Synthetic authorization evidence",
            ),
        ],
        service_lines=[
            ReviewServiceLine(
                service_code="SYNTH1",
                quantity=6,
                confidence=0.90,
                source_text="Synthetic service-line evidence",
            )
        ],
        validation_actions=[
            "Synthetic validation action"
        ],
        rule_actions=[
            "Synthetic rule action"
        ],
        needs_human_review=True,
        review_status="Human Review Recommended",
        review_reasons=[
            "Synthetic review reason"
        ],
    )


def build_feedback(
    *,
    review_output=None,
    confirmed_category="authorization",
    confirmed_subtype="renewal",
    confirmation_status="corrected",
):
    if review_output is None:
        review_output = build_review_output()

    return ClassificationFeedbackReviewService().build(
        review_output=review_output,
        document_fingerprint=FINGERPRINT,
        confirmed_category=confirmed_category,
        confirmed_subtype=confirmed_subtype,
        reviewer_confirmation_status=confirmation_status,
        created_at=TIMESTAMP,
    )


def test_human_correction_builds_feedback():
    result = build_feedback()

    assert result.ready_for_storage is True
    assert result.feedback is not None
    assert result.feedback.predicted_category == "authorization"
    assert result.feedback.predicted_subtype == "unknown"
    assert result.feedback.confirmed_category == "authorization"
    assert result.feedback.confirmed_subtype == "renewal"
    assert result.feedback.correction_required is True


def test_confirmation_without_change_builds_feedback():
    review_output = build_review_output(
        category="referral",
        subtype="unknown",
        confidence=0.92,
    )

    result = build_feedback(
        review_output=review_output,
        confirmed_category="referral",
        confirmed_subtype="unknown",
        confirmation_status="confirmed",
    )

    assert result.ready_for_storage is True
    assert result.feedback.correction_required is False


def test_classification_confidence_is_preserved():
    review_output = build_review_output(
        confidence=0.87,
    )

    result = build_feedback(
        review_output=review_output,
    )

    assert result.feedback.classification_confidence == 0.87


def test_feedback_contains_no_review_fields():
    result = build_feedback()

    payload = asdict(
        result.feedback
    )

    prohibited_keys = {
        "fields",
        "service_lines",
        "source_text",
        "patient_name",
        "authorization_number",
        "extracted_data",
        "validation_actions",
        "rule_actions",
        "review_reasons",
    }

    assert set(
        payload
    ).isdisjoint(
        prohibited_keys
    )


def test_phi_values_are_not_copied():
    review_output = build_review_output()

    result = build_feedback(
        review_output=review_output,
    )

    payload_text = repr(
        asdict(
            result.feedback
        )
    )

    prohibited_values = {
        "Synthetic Patient",
        "SYNTHETIC-AUTH",
        "Synthetic patient evidence",
        "Synthetic authorization evidence",
        "Synthetic service-line evidence",
        "SYNTH1",
        "Synthetic validation action",
        "Synthetic rule action",
        "Synthetic review reason",
    }

    assert all(
        value not in payload_text
        for value in prohibited_values
    )


def test_classification_reason_is_not_copied():
    review_output = build_review_output()

    result = build_feedback(
        review_output=review_output,
    )

    payload = asdict(
        result.feedback
    )

    assert "classification_reason" not in payload

    assert (
        review_output.classification_reason
        not in repr(
            payload
        )
    )


def test_fingerprint_is_supplied_separately():
    review_output = build_review_output()

    result = ClassificationFeedbackReviewService().build(
        review_output=review_output,
        document_fingerprint=FINGERPRINT,
        confirmed_category="authorization",
        confirmed_subtype="renewal",
        reviewer_confirmation_status="corrected",
        created_at=TIMESTAMP,
    )

    assert result.feedback.document_fingerprint == FINGERPRINT

    assert not hasattr(
        review_output,
        "document_fingerprint",
    )


def test_invalid_fingerprint_is_rejected():
    result = ClassificationFeedbackReviewService().build(
        review_output=build_review_output(),
        document_fingerprint="invalid",
        confirmed_category="authorization",
        confirmed_subtype="renewal",
        reviewer_confirmation_status="corrected",
        created_at=TIMESTAMP,
    )

    assert result.ready_for_storage is False
    assert result.feedback is None


def test_invalid_review_output_is_rejected():
    result = ClassificationFeedbackReviewService().build(
        review_output={},
        document_fingerprint=FINGERPRINT,
        confirmed_category="authorization",
        confirmed_subtype="renewal",
        reviewer_confirmation_status="corrected",
        created_at=TIMESTAMP,
    )

    assert result.ready_for_storage is False
    assert result.feedback is None


def test_adapter_does_not_mutate_review_output():
    review_output = build_review_output()

    original_field_count = len(
        review_output.fields
    )
    original_line_count = len(
        review_output.service_lines
    )

    build_feedback(
        review_output=review_output,
    )

    assert len(
        review_output.fields
    ) == original_field_count

    assert len(
        review_output.service_lines
    ) == original_line_count


def test_termination_correction_is_supported():
    review_output = build_review_output(
        category="termination",
        subtype="unknown",
        confidence=0.84,
    )

    result = build_feedback(
        review_output=review_output,
        confirmed_category="termination",
        confirmed_subtype="service_termination",
        confirmation_status="corrected",
    )

    assert result.ready_for_storage is True
    assert result.feedback.confirmed_subtype == (
        "service_termination"
    )


print("=" * 60)
print("Testing Classification Feedback Review Integration")
print("=" * 60)

run_test(
    "human correction builds feedback",
    test_human_correction_builds_feedback,
)
run_test(
    "confirmation without change builds feedback",
    test_confirmation_without_change_builds_feedback,
)
run_test(
    "classification confidence is preserved",
    test_classification_confidence_is_preserved,
)
run_test(
    "feedback contains no review fields",
    test_feedback_contains_no_review_fields,
)
run_test(
    "PHI values are not copied",
    test_phi_values_are_not_copied,
)
run_test(
    "classification reason is not copied",
    test_classification_reason_is_not_copied,
)
run_test(
    "fingerprint is supplied separately",
    test_fingerprint_is_supplied_separately,
)
run_test(
    "invalid fingerprint is rejected",
    test_invalid_fingerprint_is_rejected,
)
run_test(
    "invalid review output is rejected",
    test_invalid_review_output_is_rejected,
)
run_test(
    "adapter does not mutate review output",
    test_adapter_does_not_mutate_review_output,
)
run_test(
    "termination correction is supported",
    test_termination_correction_is_supported,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(
    "Real or mock: Synthetic deterministic integration test"
)
print("External integration: Not called")
print(
    "PHI handling: Review fields and evidence were not copied"
)

if failed:
    raise SystemExit(1)
