from pathlib import Path

from src.models.document import Document
from src.services.review_decision_service import (
    ReviewDecisionService,
)


LOW_CONFIDENCE_REASON = (
    "One or more extracted fields have confidence below 85%."
)

NO_STRUCTURED_DATA_REASON = (
    "No structured data was extracted from the document."
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
    document.document_category = "authorization"
    document.document_subtype = "initial"
    document.classification_reason = (
        "Synthetic supported classification reason."
    )
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


def test_low_populated_field_confidence_triggers_review() -> None:
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
    assert "Authorization number confidence is below the acceptance threshold" in decision.reasons


def test_field_at_confidence_threshold_does_not_trigger_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.field_confidences[
        "authorization_number"
    ] = 0.85

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is False
    assert decision.review_status == "Verified by AI"
    assert decision.minimum_field_confidence == 0.85
    assert LOW_CONFIDENCE_REASON not in decision.reasons


def test_none_optional_field_confidence_is_ignored() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data[
        "approved_visits"
    ] = None

    document.field_confidences[
        "approved_visits"
    ] = 0.0

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is False
    assert decision.review_status == "Verified by AI"
    assert decision.minimum_field_confidence == 0.95
    assert LOW_CONFIDENCE_REASON not in decision.reasons


def test_empty_string_field_confidence_is_ignored() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data[
        "modifier"
    ] = "   "

    document.field_confidences[
        "modifier"
    ] = 0.0

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is False
    assert decision.review_status == "Verified by AI"
    assert decision.minimum_field_confidence == 0.95
    assert LOW_CONFIDENCE_REASON not in decision.reasons


def test_empty_list_field_confidence_is_ignored() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data[
        "service_codes"
    ] = []

    document.field_confidences[
        "service_codes"
    ] = 0.0

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is False
    assert decision.review_status == "Verified by AI"
    assert decision.minimum_field_confidence == 0.95
    assert LOW_CONFIDENCE_REASON not in decision.reasons


def test_populated_field_without_confidence_triggers_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data[
        "service_code"
    ] = "SYNTH1"

    document.field_confidences.pop(
        "service_code",
        None,
    )

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.minimum_field_confidence == 0.95
    assert "Service code confidence is unavailable" in decision.reasons


def test_invalidated_field_uses_validation_action_for_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    validation_reason = (
        "approved_visits is not supported by its source evidence"
    )

    document.extracted_data[
        "approved_visits"
    ] = None

    document.field_confidences[
        "approved_visits"
    ] = 0.0

    document.validation_actions = [
        validation_reason
    ]

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"
    assert decision.minimum_field_confidence == 0.95
    assert validation_reason in decision.reasons
    assert LOW_CONFIDENCE_REASON not in decision.reasons


def test_numeric_zero_is_treated_as_populated() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data[
        "authorized_units"
    ] = 0

    document.field_confidences[
        "authorized_units"
    ] = 0.80

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.minimum_field_confidence == 0.80
    assert "Authorized units confidence is below the acceptance threshold" in decision.reasons


def test_false_boolean_is_treated_as_populated() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data[
        "is_renewal"
    ] = False

    document.field_confidences[
        "is_renewal"
    ] = 0.80

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.minimum_field_confidence == 0.80
    assert "Is renewal confidence is below the acceptance threshold" in decision.reasons


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


def test_successful_reconciliation_action_does_not_trigger_review() -> None:
    service = ReviewDecisionService()
    document = build_document()
    document.validation_actions = [
        "Authorized units were reconciled from supported service-line evidence"
    ]

    decision = service.evaluate(document)

    assert decision.needs_human_review is False
    assert decision.review_status == "Verified by AI"
    assert decision.reasons == []


def test_retry_and_second_attempt_do_not_trigger_review_or_conflate_confidence() -> None:
    service = ReviewDecisionService()
    document = build_document()
    document.confidence = 1.0
    document.processing_metrics = {
        "extraction_attempt_count": 2,
        "extraction_retry_triggered": True,
        "extraction_selected_attempt": 2,
    }

    decision = service.evaluate(document)

    assert decision.needs_human_review is False
    assert decision.classification_confidence == 1.0
    assert decision.minimum_field_confidence == 0.95
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


def test_review_reasons_exclude_document_values_and_source_text() -> None:
    service = ReviewDecisionService()
    document = build_document()

    synthetic_value = "SYNTHETIC_VALUE_MUST_NOT_APPEAR"
    synthetic_source = "SYNTHETIC_SOURCE_MUST_NOT_APPEAR"
    synthetic_classification = (
        "SYNTHETIC_CLASSIFICATION_TEXT_MUST_NOT_APPEAR"
    )

    document.extracted_data[
        "authorization_number"
    ] = synthetic_value

    document.field_evidence = {
        "authorization_number": {
            "value": synthetic_value,
            "confidence": 0.95,
            "source_text": synthetic_source,
        },
    }

    document.classification_reason = (
        synthetic_classification
    )

    document.validation_actions = [
        "Authorization status requires verification",
    ]

    document.rule_actions = [
        "Authorization quantity requires verification",
    ]

    decision = service.evaluate(
        document
    )

    joined_reasons = " | ".join(
        decision.reasons
    )

    assert synthetic_value not in joined_reasons
    assert synthetic_source not in joined_reasons
    assert synthetic_classification not in joined_reasons


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


def test_empty_structured_mapping_triggers_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data = {}
    document.field_confidences = {}

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"
    assert decision.minimum_field_confidence is None
    assert NO_STRUCTURED_DATA_REASON in decision.reasons


def test_only_empty_structured_values_trigger_review() -> None:
    service = ReviewDecisionService()
    document = build_document()

    document.extracted_data = {
        "approved_visits": None,
        "modifier": "",
        "service_codes": [],
    }

    document.field_confidences = {
        "approved_visits": 0.0,
        "modifier": 0.0,
        "service_codes": 0.0,
    }

    decision = service.evaluate(
        document
    )

    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Recommended"
    assert decision.minimum_field_confidence is None
    assert NO_STRUCTURED_DATA_REASON in decision.reasons
    assert LOW_CONFIDENCE_REASON not in decision.reasons


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
            "low populated field confidence triggers review",
            test_low_populated_field_confidence_triggers_review,
        ),
        (
            "field at confidence threshold does not trigger review",
            test_field_at_confidence_threshold_does_not_trigger_review,
        ),
        (
            "none optional field confidence is ignored",
            test_none_optional_field_confidence_is_ignored,
        ),
        (
            "empty string field confidence is ignored",
            test_empty_string_field_confidence_is_ignored,
        ),
        (
            "empty list field confidence is ignored",
            test_empty_list_field_confidence_is_ignored,
        ),
        (
            "populated field without confidence triggers review",
            test_populated_field_without_confidence_triggers_review,
        ),
        (
            "invalidated field uses validation action for review",
            test_invalidated_field_uses_validation_action_for_review,
        ),
        (
            "numeric zero is treated as populated",
            test_numeric_zero_is_treated_as_populated,
        ),
        (
            "false boolean is treated as populated",
            test_false_boolean_is_treated_as_populated,
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
            "successful reconciliation does not trigger review",
            test_successful_reconciliation_action_does_not_trigger_review,
        ),
        (
            "retry and second attempt do not trigger review",
            test_retry_and_second_attempt_do_not_trigger_review_or_conflate_confidence,
        ),
        (
            "business rule failure triggers review",
            test_business_rule_failure_triggers_review,
        ),
        (
            "review reasons exclude document values and source text",
            test_review_reasons_exclude_document_values_and_source_text,
        ),
        (
            "duplicate reasons are removed",
            test_duplicate_reasons_are_removed,
        ),
        (
            "empty structured mapping triggers review",
            test_empty_structured_mapping_triggers_review,
        ),
        (
            "only empty structured values trigger review",
            test_only_empty_structured_values_trigger_review,
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
