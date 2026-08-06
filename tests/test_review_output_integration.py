from pathlib import Path

from src.document_processing.document_processor import (
    DocumentProcessor,
)
from src.models.document import (
    AuthorizationServiceLine,
    Document,
)
from src.services.review_output_service import (
    ReviewOutput,
    ReviewOutputService,
)


RECONCILIATION_ACTION = (
    "Authorized units were reconciled from supported "
    "service-line evidence"
)


def build_processed_document() -> Document:
    """
    Build a synthetic document representing completed pipeline output.
    """

    document = Document(
        file_path=Path(
            "synthetic-review-integration.pdf"
        )
    )

    document.document_type = "authorization"
    document.confidence = 0.90

    document.raw_text = (
        "Synthetic OCR text that must not appear in review output."
    )

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
            "source_text": "Synthetic approval evidence",
        },
        "authorized_units": {
            "value": ["6", "1"],
            "confidence": 0.50,
            "source_text": "Synthetic quantity evidence",
        },
        "request_type": {
            "value": None,
            "confidence": 0.0,
            "source_text": "Synthetic ambiguous selection evidence",
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
        "total_wall_seconds": 10.0,
    }

    return document


def build_processor_without_provider_initialization() -> (
    DocumentProcessor
):
    """
    Build only the processor portion required by this unit test.
    """

    processor = DocumentProcessor.__new__(
        DocumentProcessor
    )

    processor.review_outputs = ReviewOutputService()

    return processor


def test_document_defaults_to_no_review_output() -> None:
    document = Document(
        file_path=Path(
            "synthetic-empty-review-output.pdf"
        )
    )

    assert document.review_output is None


def test_processor_attaches_review_output() -> None:
    processor = build_processor_without_provider_initialization()
    document = build_processed_document()

    processor._attach_review_output(
        document
    )

    assert isinstance(
        document.review_output,
        ReviewOutput,
    )


def test_attached_output_preserves_review_decision() -> None:
    processor = build_processor_without_provider_initialization()
    document = build_processed_document()

    processor._attach_review_output(
        document
    )

    output = document.review_output

    assert output.needs_human_review is True
    assert output.review_status == "Human Review Recommended"
    assert output.minimum_field_confidence == 0.50
    assert (
        "Authorization quantity requires verification"
        in output.review_reasons
    )


def test_attached_output_preserves_retry_metadata() -> None:
    processor = build_processor_without_provider_initialization()
    document = build_processed_document()

    processor._attach_review_output(
        document
    )

    output = document.review_output

    assert output.extraction_attempt_count == 2
    assert output.extraction_retry_triggered is True
    assert output.extraction_selected_attempt == 2
    assert output.authorized_units_reconciled is True


def test_attached_output_preserves_evidence() -> None:
    processor = build_processor_without_provider_initialization()
    document = build_processed_document()

    processor._attach_review_output(
        document
    )

    fields = {
        field.name: field
        for field in document.review_output.fields
    }

    assert fields[
        "authorized_units"
    ].value == ["6", "1"]

    assert fields[
        "authorized_units"
    ].confidence == 0.50

    assert fields[
        "authorized_units"
    ].source_text == "Synthetic quantity evidence"


def test_attached_output_excludes_raw_text_and_file_path() -> None:
    processor = build_processor_without_provider_initialization()
    document = build_processed_document()

    processor._attach_review_output(
        document
    )

    output = document.review_output

    assert not hasattr(
        output,
        "raw_text",
    )

    assert not hasattr(
        output,
        "file_path",
    )


def test_attached_output_is_independent_snapshot() -> None:
    processor = build_processor_without_provider_initialization()
    document = build_processed_document()

    processor._attach_review_output(
        document
    )

    units_field = next(
        field
        for field in document.review_output.fields
        if field.name == "authorized_units"
    )

    units_field.value.append(
        "999"
    )

    assert document.field_evidence[
        "authorized_units"
    ]["value"] == ["6", "1"]


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
    print("Testing Review Output Integration")
    print("=" * 60)

    tests = [
        (
            "document defaults to no review output",
            test_document_defaults_to_no_review_output,
        ),
        (
            "processor attaches review output",
            test_processor_attaches_review_output,
        ),
        (
            "review decision is preserved",
            test_attached_output_preserves_review_decision,
        ),
        (
            "retry metadata is preserved",
            test_attached_output_preserves_retry_metadata,
        ),
        (
            "field evidence is preserved",
            test_attached_output_preserves_evidence,
        ),
        (
            "raw text and file path are excluded",
            test_attached_output_excludes_raw_text_and_file_path,
        ),
        (
            "review output is an independent snapshot",
            test_attached_output_is_independent_snapshot,
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
