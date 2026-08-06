from pathlib import Path

from src.models.document import Document
from src.services.review_decision_service import (
    ReviewDecisionService,
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


def build_document(
    *,
    category="authorization",
    subtype="initial",
    confidence=0.95,
    reason="Synthetic supported classification reason.",
):
    document = Document(
        file_path=Path(
            "synthetic-classification-review.pdf"
        ),
        document_type="authorization",
        document_category=category,
        document_subtype=subtype,
        classification_reason=reason,
        confidence=confidence,
    )

    document.extracted_data = {
        "authorization_number": "SYNTHETIC",
    }

    document.field_confidences = {
        "authorization_number": 0.95,
    }

    document.rule_actions = [
        "Authorization validated successfully",
    ]

    return document


def test_supported_initial_authorization_can_be_verified():
    decision = ReviewDecisionService().evaluate(
        build_document()
    )

    assert decision.needs_human_review is False
    assert decision.review_status == "Verified by AI"


def test_unknown_category_requires_review():
    document = build_document(
        category="unknown",
        subtype="unknown",
    )
    document.document_type = "unknown"

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Required"
    assert (
        ReviewDecisionService.UNKNOWN_CATEGORY_REASON
        in decision.reasons
    )


def test_unsupported_category_requires_review():
    document = build_document(
        category="unsupported_category",
        subtype="unknown",
    )

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.review_status == "Human Review Required"
    assert (
        ReviewDecisionService.UNSUPPORTED_CATEGORY_REASON
        in decision.reasons
    )


def test_unknown_authorization_subtype_recommends_review():
    document = build_document(
        category="authorization",
        subtype="unknown",
    )

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"
    assert (
        ReviewDecisionService.UNKNOWN_AUTHORIZATION_SUBTYPE_REASON
        in decision.reasons
    )


def test_unknown_termination_subtype_requires_review():
    document = build_document(
        category="termination",
        subtype="unknown",
    )
    document.document_type = "termination"

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.review_status == "Human Review Required"
    assert (
        ReviewDecisionService.UNKNOWN_TERMINATION_SUBTYPE_REASON
        in decision.reasons
    )


def test_supported_service_termination_is_compatible():
    document = build_document(
        category="termination",
        subtype="service_termination",
    )
    document.document_type = "termination"
    document.rule_actions = []

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert (
        ReviewDecisionService.INCOMPATIBLE_SUBTYPE_REASON
        not in decision.reasons
    )


def test_incompatible_termination_subtype_requires_review():
    document = build_document(
        category="termination",
        subtype="initial",
    )
    document.document_type = "termination"

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.review_status == "Human Review Required"
    assert (
        ReviewDecisionService.INCOMPATIBLE_SUBTYPE_REASON
        in decision.reasons
    )


def test_referral_must_use_unknown_subtype():
    document = build_document(
        category="referral",
        subtype="initial",
    )
    document.document_type = "referral"
    document.rule_actions = []

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.review_status == "Human Review Required"
    assert (
        ReviewDecisionService.INCOMPATIBLE_SUBTYPE_REASON
        in decision.reasons
    )


def test_other_category_recommends_confirmation():
    document = build_document(
        category="other",
        subtype="unknown",
    )
    document.document_type = "other"
    document.rule_actions = []

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.review_status == "Human Review Recommended"
    assert (
        ReviewDecisionService.OTHER_CATEGORY_REASON
        in decision.reasons
    )


def test_missing_reason_recommends_review():
    document = build_document(
        reason="",
    )

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.review_status == "Human Review Recommended"
    assert (
        ReviewDecisionService.MISSING_CLASSIFICATION_REASON
        in decision.reasons
    )


def test_low_confidence_still_requires_review():
    document = build_document(
        confidence=0.74,
    )

    decision = ReviewDecisionService().evaluate(
        document
    )

    assert decision.review_status == "Human Review Required"
    assert (
        "Document classification confidence is below 75%."
        in decision.reasons
    )


print("=" * 60)
print("Testing Classification Review Gating")
print("=" * 60)

run_test(
    "supported initial authorization can be verified",
    test_supported_initial_authorization_can_be_verified,
)
run_test(
    "unknown category requires review",
    test_unknown_category_requires_review,
)
run_test(
    "unsupported category requires review",
    test_unsupported_category_requires_review,
)
run_test(
    "unknown authorization subtype recommends review",
    test_unknown_authorization_subtype_recommends_review,
)
run_test(
    "unknown termination subtype requires review",
    test_unknown_termination_subtype_requires_review,
)
run_test(
    "supported service termination is compatible",
    test_supported_service_termination_is_compatible,
)
run_test(
    "incompatible termination subtype requires review",
    test_incompatible_termination_subtype_requires_review,
)
run_test(
    "referral must use unknown subtype",
    test_referral_must_use_unknown_subtype,
)
run_test(
    "other category recommends confirmation",
    test_other_category_recommends_confirmation,
)
run_test(
    "missing reason recommends review",
    test_missing_reason_recommends_review,
)
run_test(
    "low confidence still requires review",
    test_low_confidence_still_requires_review,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic test")
print("External integration: Not called")
print("PHI handling: No OCR or extracted values printed")

if failed:
    raise SystemExit(1)
