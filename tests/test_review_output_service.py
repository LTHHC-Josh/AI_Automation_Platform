from pathlib import Path

from src.models.document import (
    AuthorizationServiceLine,
    Document,
)
from src.services.review_output_service import (
    ReviewOutputService,
)


RECONCILIATION_ACTION = (
    "Authorized units were reconciled from supported "
    "service-line evidence"
)


def build_document() -> Document:
    """
    Build a synthetic processed document containing no real PHI.
    """

    document = Document(
        file_path=Path(
            "synthetic-local-review.pdf"
        )
    )

    document.document_type = "authorization"
    document.confidence = 0.90
    document.raw_text = "Synthetic OCR text that must not be exported."

    document.extracted_data = {
        "authorization_status": "Approved",
        "authorized_units": ["6", "1"],
        "request_type": None,
    }

    document.field_confidences = {
        "authorization_status": 0.95,
        "authorized_units": 0.50,
        "request_type": 0.0,
    }

    document.field_evidence = {
        "authorization_status": {
            "value": "Approved",
            "confidence": 0.95,
            "source_text": "Synthetic approved status evidence",
        },
        "authorized_units": {
            "value": ["6", "1"],
            "confidence": 0.50,
            "source_text": "Synthetic quantity evidence",
        },
        "request_type": {
            "value": None,
            "confidence": 0.0,
            "source_text": "Synthetic ambiguous checkbox evidence",
        },
    }

    document.service_lines = [
        AuthorizationServiceLine(
            service_code="SYNTH1",
            modifier=None,
            quantity=6,
            start_date="2026-01-01",
            end_date="2026-02-01",
            status="Approved",
            confidence=0.50,
            source_text="Synthetic service-line evidence",
        )
    ]

    document.validation_actions = [
        RECONCILIATION_ACTION,
        "Request type requires checkbox verification",
    ]

    document.rule_actions = [
        "Authorization quantity requires verification"
    ]

    document.needs_human_review = True
    document.review_status = "Human Review Recommended"
    document.review_reasons = [
        "One or more extracted fields have confidence below 85%.",
        RECONCILIATION_ACTION,
        "Authorization quantity requires verification",
    ]
    document.minimum_field_confidence = 0.50

    document.processing_metrics = {
        "extraction_attempt_count": 2,
        "extraction_retry_triggered": True,
        "extraction_selected_attempt": 2,
    }

    return document


def get_field(
    output,
    field_name: str,
):
    """
    Return one named field from a review output.
    """

    matches = [
        field
        for field in output.fields
        if field.name == field_name
    ]

    assert len(
        matches
    ) == 1

    return matches[0]


def test_build_preserves_field_evidence() -> None:
    service = ReviewOutputService()
    document = build_document()

    output = service.build(
        document
    )

    units = get_field(
        output,
        "authorized_units",
    )

    assert units.value == ["6", "1"]
    assert units.confidence == 0.50
    assert units.source_text == "Synthetic quantity evidence"


def test_build_preserves_empty_ambiguous_field() -> None:
    service = ReviewOutputService()
    document = build_document()

    output = service.build(
        document
    )

    request_type = get_field(
        output,
        "request_type",
    )

    assert request_type.value is None
    assert request_type.confidence == 0.0
    assert (
        request_type.source_text
        == "Synthetic ambiguous checkbox evidence"
    )


def test_build_preserves_service_line_relationship() -> None:
    service = ReviewOutputService()
    document = build_document()

    output = service.build(
        document
    )

    assert len(
        output.service_lines
    ) == 1

    service_line = output.service_lines[0]

    assert service_line.service_code == "SYNTH1"
    assert service_line.modifier is None
    assert service_line.quantity == 6
    assert service_line.start_date == "2026-01-01"
    assert service_line.end_date == "2026-02-01"
    assert service_line.status == "Approved"
    assert service_line.confidence == 0.50
    assert (
        service_line.source_text
        == "Synthetic service-line evidence"
    )


def test_build_preserves_review_and_retry_metadata() -> None:
    service = ReviewOutputService()
    document = build_document()

    output = service.build(
        document
    )

    assert output.needs_human_review is True
    assert output.review_status == "Human Review Recommended"
    assert output.minimum_field_confidence == 0.50
    assert output.extraction_attempt_count == 2
    assert output.extraction_retry_triggered is True
    assert output.extraction_selected_attempt == 2


def test_build_identifies_authorized_units_reconciliation() -> None:
    service = ReviewOutputService()
    document = build_document()

    output = service.build(
        document
    )

    assert output.authorized_units_reconciled is True

    document.validation_actions.remove(
        RECONCILIATION_ACTION
    )

    output_without_action = service.build(
        document
    )

    assert (
        output_without_action.authorized_units_reconciled
        is False
    )


def test_build_does_not_expose_raw_text_or_file_path() -> None:
    service = ReviewOutputService()
    document = build_document()

    output = service.build(
        document
    )

    assert not hasattr(
        output,
        "raw_text",
    )
    assert not hasattr(
        output,
        "file_path",
    )


def test_build_returns_independent_mutable_values() -> None:
    service = ReviewOutputService()
    document = build_document()

    output = service.build(
        document
    )

    units = get_field(
        output,
        "authorized_units",
    )

    units.value.append(
        "999"
    )

    assert document.field_evidence[
        "authorized_units"
    ]["value"] == ["6", "1"]


def test_flat_field_fallback_preserves_missing_confidence_as_zero() -> None:
    service = ReviewOutputService()
    document = build_document()

    document.extracted_data[
        "service_description"
    ] = "Synthetic service"

    document.field_confidences.pop(
        "service_description",
        None,
    )

    output = service.build(
        document
    )

    description = get_field(
        output,
        "service_description",
    )

    assert description.value == "Synthetic service"
    assert description.confidence == 0.0
    assert description.source_text == ""


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
    print("Testing Review Output Service")
    print("=" * 60)

    tests = [
        (
            "field evidence is preserved",
            test_build_preserves_field_evidence,
        ),
        (
            "ambiguous empty field is preserved",
            test_build_preserves_empty_ambiguous_field,
        ),
        (
            "service-line relationship is preserved",
            test_build_preserves_service_line_relationship,
        ),
        (
            "review and retry metadata are preserved",
            test_build_preserves_review_and_retry_metadata,
        ),
        (
            "quantity reconciliation is identified",
            test_build_identifies_authorized_units_reconciliation,
        ),
        (
            "raw text and file path are excluded",
            test_build_does_not_expose_raw_text_or_file_path,
        ),
        (
            "mutable values are copied",
            test_build_returns_independent_mutable_values,
        ),
        (
            "flat fallback uses conservative confidence",
            test_flat_field_fallback_preserves_missing_confidence_as_zero,
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
