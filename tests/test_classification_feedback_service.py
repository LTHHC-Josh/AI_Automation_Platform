from dataclasses import fields

from src.services.classification_feedback_service import (
    ClassificationFeedback,
    ClassificationFeedbackService,
)


passed = 0
failed = 0

FINGERPRINT = "a" * 64
TIMESTAMP = "2026-08-06T15:00:00Z"


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


def build_feedback(
    **overrides,
):
    values = {
        "document_fingerprint": FINGERPRINT,
        "predicted_category": "authorization",
        "predicted_subtype": "initial",
        "confirmed_category": "authorization",
        "confirmed_subtype": "initial",
        "classification_confidence": 0.91,
        "reviewer_confirmation_status": "confirmed",
        "created_at": TIMESTAMP,
    }

    values.update(
        overrides
    )

    return ClassificationFeedbackService().build(
        **values
    )


def test_confirmed_result_is_ready():
    result = build_feedback()

    assert result.ready_for_storage is True
    assert result.errors == ()
    assert result.feedback is not None
    assert result.feedback.correction_required is False


def test_corrected_result_is_ready():
    result = build_feedback(
        predicted_subtype="unknown",
        confirmed_subtype="renewal",
        reviewer_confirmation_status="corrected",
    )

    assert result.ready_for_storage is True
    assert result.feedback.correction_required is True


def test_category_correction_is_detected():
    result = build_feedback(
        predicted_category="unknown",
        predicted_subtype="unknown",
        confirmed_category="referral",
        confirmed_subtype="unknown",
        reviewer_confirmation_status="corrected",
    )

    assert result.ready_for_storage is True
    assert result.feedback.correction_required is True


def test_invalid_hash_is_rejected():
    result = build_feedback(
        document_fingerprint="not-a-hash",
    )

    assert result.ready_for_storage is False
    assert result.feedback is None


def test_incompatible_subtype_is_rejected():
    result = build_feedback(
        confirmed_category="referral",
        confirmed_subtype="initial",
        reviewer_confirmation_status="corrected",
    )

    assert result.ready_for_storage is False


def test_termination_subtype_is_supported():
    result = build_feedback(
        predicted_category="termination",
        predicted_subtype="unknown",
        confirmed_category="termination",
        confirmed_subtype="service_termination",
        reviewer_confirmation_status="corrected",
    )

    assert result.ready_for_storage is True


def test_status_must_match_correction():
    result = build_feedback(
        confirmed_subtype="renewal",
        reviewer_confirmation_status="confirmed",
    )

    assert result.ready_for_storage is False


def test_naive_timestamp_is_rejected():
    result = build_feedback(
        created_at="2026-08-06T15:00:00",
    )

    assert result.ready_for_storage is False


def test_confidence_is_normalized():
    result = build_feedback(
        classification_confidence=91,
    )

    assert result.feedback.classification_confidence == 0.91


def test_contract_excludes_phi_fields():
    field_names = {
        item.name
        for item in fields(
            ClassificationFeedback
        )
    }

    prohibited_fields = {
        "raw_text",
        "source_text",
        "file_path",
        "file_name",
        "patient_name",
        "member_id",
        "authorization_number",
        "email_subject",
        "email_sender",
        "document_bytes",
        "extracted_data",
    }

    assert field_names.isdisjoint(
        prohibited_fields
    )


def test_service_does_not_accept_document_path():
    parameters = (
        ClassificationFeedbackService.build
        .__annotations__
    )

    assert "file_path" not in parameters
    assert "raw_text" not in parameters
    assert "source_text" not in parameters


print("=" * 60)
print("Testing Classification Feedback Contract")
print("=" * 60)

run_test(
    "confirmed result is ready",
    test_confirmed_result_is_ready,
)
run_test(
    "corrected result is ready",
    test_corrected_result_is_ready,
)
run_test(
    "category correction is detected",
    test_category_correction_is_detected,
)
run_test(
    "invalid hash is rejected",
    test_invalid_hash_is_rejected,
)
run_test(
    "incompatible subtype is rejected",
    test_incompatible_subtype_is_rejected,
)
run_test(
    "termination subtype is supported",
    test_termination_subtype_is_supported,
)
run_test(
    "status must match correction",
    test_status_must_match_correction,
)
run_test(
    "naive timestamp is rejected",
    test_naive_timestamp_is_rejected,
)
run_test(
    "confidence is normalized",
    test_confidence_is_normalized,
)
run_test(
    "contract excludes PHI fields",
    test_contract_excludes_phi_fields,
)
run_test(
    "service excludes document content inputs",
    test_service_does_not_accept_document_path,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic test")
print("External integration: Not called")
print("PHI handling: Contract excludes document and patient content")

if failed:
    raise SystemExit(1)
