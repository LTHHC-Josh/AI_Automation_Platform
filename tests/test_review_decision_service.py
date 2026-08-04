from pathlib import Path

from src.models.document import Document
from src.services.review_decision_service import (
    ReviewDecisionService,
)


def build_document() -> Document:
    """
    Build a synthetic document containing no PHI.
    """

    document = Document(
        file_path=Path(
            "synthetic-review-test.pdf"
        )
    )

    document.document_type = "authorization"
    document.confidence = 0.95

    document.extracted_data = {
        "patient_name": "Synthetic Patient",
        "authorization_number": "AUTH123",
    }

    document.field_confidences = {
        "patient_name": 0.95,
        "authorization_number": 0.95,
    }

    document.validation_actions = []
    document.rule_actions = [
        "Authorization validated successfully",
    ]

    return document


def test_clean_document_is_verified() -> None:
    service = ReviewDecisionService()
    document = build_document()

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is False
    assert decision.review_status == "Verified by AI"
    assert decision.reasons == []
    assert decision.classification_confidence == 0.95
    assert decision.minimum_field_confidence == 0.95


def test_validation_action_triggers_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.validation_actions = [
        "Request type requires checkbox or selection verification"
    ]

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"

    assert (
        "Request type requires checkbox or selection verification"
        in decision.reasons
    )


def test_low_field_confidence_triggers_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.field_confidences[
        "authorization_number"
    ] = 0.84

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"
    assert decision.minimum_field_confidence == 0.84

    assert (
        "One or more extracted fields have confidence below 85%."
        in decision.reasons
    )


def test_classification_below_auto_approve_threshold() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.confidence = 0.89

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"

    assert (
        "Document classification confidence is below 90%."
        in decision.reasons
    )


def test_classification_below_human_review_threshold() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.confidence = 0.74

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Required"

    assert (
        "Document classification confidence is below 75%."
        in decision.reasons
    )


def test_success_action_does_not_trigger_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.rule_actions = [
        "Authorization validated successfully"
    ]

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is False
    assert decision.review_status == "Verified by AI"
    assert decision.reasons == []


def test_business_rule_failure_triggers_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.rule_actions = [
        "Authorization quantity requires verification"
    ]

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"

    assert (
        "Authorization quantity requires verification"
        in decision.reasons
    )


def test_duplicate_reasons_are_removed() -> None:
    service = ReviewDecisionService()
    document = build_document()

    duplicate_reason = (
        "Authorization quantity requires verification"
    )

    document.validation_actions = [
        duplicate_reason
    ]

    document.rule_actions = [
        duplicate_reason
    ]

    decision = service.evaluate(
        document
    )

    assert decision.reasons.count(
        duplicate_reason
    ) == 1


def test_missing_structured_data_triggers_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data = {}

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"

    assert (
        "No structured data was extracted from the document."
        in decision.reasons
    )


def run_test(
    test_name: str,
    test_function,
) -> None:
    """
    Run one synthetic test and print a readable result.
    """

    try:
        test_function()
    except AssertionError:
        print(
            f"FAILED: {test_name}"
        )
        raise

    print(
        f"PASSED: {test_name}"
    )


def main() -> None:
    print("=" * 60)
    print("Testing Review Decision Service")
    print("=" * 60)

    tests = [
        (
            "clean document is verified",
            test_clean_document_is_verified,
        ),
        (
            "validation action triggers review",
            test_validation_action_triggers_review,
        ),
        (
            "low field confidence triggers review",
            test_low_field_confidence_triggers_review,
        ),
        (
            "classification below 90 percent",
            test_classification_below_auto_approve_threshold,
        ),
        (
            "classification below 75 percent",
            test_classification_below_human_review_threshold,
        ),
        (
            "success action does not trigger review",
            test_success_action_does_not_trigger_review,
        ),
        (
            "business rule failure triggers review",
            test_business_rule_failure_triggers_review,
        ),
        (
            "duplicate reasons are removed",
            test_duplicate_reasons_are_removed,
        ),
        (
            "missing structured data triggers review",
            test_missing_structured_data_triggers_review,
        ),
    ]

    passed = 0
    failed = 0

    for test_name, test_function in tests:
        try:
            run_test(
                test_name,
                test_function,
            )
            passed += 1
        except AssertionError:
            failed += 1

    print()
    print(
        f"Passed: {passed}"
    )
    print(
        f"Failed: {failed}"
    )
    print(
        "Real or mock: Synthetic deterministic test"
    )
    print("=" * 60)

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()