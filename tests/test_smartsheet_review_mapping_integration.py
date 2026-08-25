from pathlib import Path

from src.models.document import (
    AuthorizationServiceLine,
    Document,
)
from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.review_output_service import (
    ReviewOutputService,
)
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
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
    needs_human_review=False,
):
    document = Document(
        file_path=Path(
            "synthetic_document.pdf"
        )
    )

    document.document_type = "authorization"
    document.confidence = 0.90

    document.raw_text = (
        "Synthetic PHI-bearing OCR text that must not be mapped."
    )

    document.extracted_data = {
        "authorization_status": "Approved",
        "service_codes": [
            "CODE-A",
            "CODE-B",
        ],
        "authorized_units": [
            "6",
            "1",
        ],
        "approved_visits": None,
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
    }

    document.field_confidences = {
        "authorization_status": 0.95,
        "service_codes": 0.95,
        "authorized_units": 0.90,
        "approved_visits": 0.0,
        "start_date": 0.95,
        "end_date": 0.95,
    }

    document.field_evidence = {
        "authorization_status": {
            "value": "Approved",
            "confidence": 0.95,
            "source_text": "Synthetic PHI-bearing source evidence.",
        },
        "service_codes": {
            "value": [
                "CODE-A",
                "CODE-B",
            ],
            "confidence": 0.95,
            "source_text": "Synthetic PHI-bearing source evidence.",
        },
        "authorized_units": {
            "value": [
                "6",
                "1",
            ],
            "confidence": 0.90,
            "source_text": "Synthetic PHI-bearing source evidence.",
        },
        "approved_visits": {
            "value": None,
            "confidence": 0.0,
            "source_text": "",
        },
        "start_date": {
            "value": "2026-01-01",
            "confidence": 0.95,
            "source_text": "Synthetic PHI-bearing source evidence.",
        },
        "end_date": {
            "value": "2026-06-30",
            "confidence": 0.95,
            "source_text": "Synthetic PHI-bearing source evidence.",
        },
    }

    document.service_lines = [
        AuthorizationServiceLine(
            service_code="CODE-A",
            modifier=None,
            quantity="1",
            start_date="2026-01-01",
            end_date="2026-06-30",
            status="Approved",
            confidence=0.50,
            source_text=(
                "Synthetic PHI-bearing service-line evidence."
            ),
        ),
        AuthorizationServiceLine(
            service_code="CODE-B",
            modifier=None,
            quantity="6",
            start_date="2026-01-01",
            end_date="2026-06-30",
            status="Approved",
            confidence=0.95,
            source_text=(
                "Synthetic PHI-bearing service-line evidence."
            ),
        ),
    ]

    document.processing_metrics = {
        "extraction_attempt_count": 2,
        "extraction_retry_triggered": True,
        "extraction_selected_attempt": 2,
    }

    document.validation_actions = [
        (
            "Authorized units were reconciled from supported "
            "service-line evidence"
        )
    ]

    document.rule_actions = (
        [
            "Authorization quantity requires verification"
        ]
        if needs_human_review
        else []
    )

    document.needs_human_review = needs_human_review
    document.review_status = (
        "Human Review Recommended"
        if needs_human_review
        else "Verified by AI"
    )

    document.review_reasons = (
        [
            "Authorization quantity requires verification"
        ]
        if needs_human_review
        else []
    )

    document.minimum_field_confidence = 0.90

    return document


def build_policies():
    return [
        SmartsheetColumnPolicy(
            source_field="authorization_status",
            column_name="Authorization Status",
            required=True,
        ),
        SmartsheetColumnPolicy(
            source_field="service_codes",
            column_name="Service Codes",
            required=True,
        ),
        SmartsheetColumnPolicy(
            source_field="authorized_units",
            column_name="Authorized Units",
            review_only=True,
        ),
        SmartsheetColumnPolicy(
            source_field="start_date",
            column_name="Start Date",
            required=True,
        ),
        SmartsheetColumnPolicy(
            source_field="end_date",
            column_name="End Date",
            required=True,
        ),
    ]


def build_mapping(
    *,
    needs_human_review=False,
):
    document = build_document(
        needs_human_review=needs_human_review
    )

    review_output = ReviewOutputService().build(
        document
    )

    mapping = SmartsheetReviewRowMappingService().map(
        review_output=review_output,
        policies=build_policies(),
        run_type="Document mapping integration",
    )

    return (
        document,
        review_output,
        mapping,
    )


def test_document_flows_to_mapping():
    (
        document,
        review_output,
        mapping,
    ) = build_mapping()

    assert review_output.document_type == (
        document.document_type
    )
    assert mapping.values[
        "Authorization Status"
    ] == "Approved"


def test_field_values_are_preserved():
    (
        _,
        _,
        mapping,
    ) = build_mapping()

    assert mapping.values[
        "Service Codes"
    ] == "CODE-A | CODE-B"

    assert mapping.values[
        "Authorized Units"
    ] == "6 | 1"


def test_review_metadata_is_preserved():
    (
        _,
        review_output,
        mapping,
    ) = build_mapping()

    assert mapping.values[
        "AI Review Status"
    ] == review_output.review_status

    assert mapping.values[
        "AI Selected Extraction Attempt"
    ] == 2

    assert mapping.values[
        "AI Extraction Retry Triggered"
    ] is True

    assert mapping.values[
        "AI Authorized Units Reconciled"
    ] is True


def test_source_text_is_not_mapped():
    (
        _,
        review_output,
        mapping,
    ) = build_mapping()

    mapped_values = list(
        mapping.values.values()
    )

    source_text_values = {
        field.source_text
        for field in review_output.fields
        if field.source_text
    }

    for source_text in source_text_values:
        assert source_text not in mapped_values


def test_raw_text_and_file_path_are_not_mapped():
    (
        document,
        _,
        mapping,
    ) = build_mapping()

    mapped_values = list(
        mapping.values.values()
    )

    assert document.raw_text not in mapped_values
    assert str(
        document.file_path
    ) not in mapped_values


def test_review_only_quantity_is_identified():
    (
        _,
        _,
        mapping,
    ) = build_mapping()

    assert mapping.review_only_columns == [
        "Authorized Units"
    ]


def test_verified_document_can_be_ready():
    (
        _,
        _,
        mapping,
    ) = build_mapping(
        needs_human_review=False
    )

    assert not mapping.missing_required_columns
    assert not mapping.prohibited_fields
    assert mapping.ready_for_write is True


def test_human_review_preserves_metadata_and_allows_write():
    (
        _,
        review_output,
        mapping,
    ) = build_mapping(
        needs_human_review=True
    )

    assert review_output.needs_human_review is True
    assert mapping.ready_for_write is True
    assert mapping.values["AI Review Required"] is True
    assert mapping.values["AI Review Reasons"]
    assert len(
        mapping.warnings
    ) == 1


def test_service_lines_remain_in_review_output_only():
    (
        _,
        review_output,
        mapping,
    ) = build_mapping()

    assert len(
        review_output.service_lines
    ) == 2

    assert "service_lines" not in mapping.values
    assert "Service Lines" not in mapping.values


print(
    "=" * 60
)
print(
    "Testing Document to Smartsheet Mapping Integration"
)
print(
    "=" * 60
)

run_test(
    "document flows to mapping",
    test_document_flows_to_mapping,
)
run_test(
    "field values are preserved",
    test_field_values_are_preserved,
)
run_test(
    "review metadata is preserved",
    test_review_metadata_is_preserved,
)
run_test(
    "source_text is not mapped",
    test_source_text_is_not_mapped,
)
run_test(
    "raw text and file path are not mapped",
    test_raw_text_and_file_path_are_not_mapped,
)
run_test(
    "review-only quantity is identified",
    test_review_only_quantity_is_identified,
)
run_test(
    "verified document can be ready",
    test_verified_document_can_be_ready,
)
run_test(
    "human review preserves metadata and allows write",
    test_human_review_preserves_metadata_and_allows_write,
)
run_test(
    "service lines remain in review output only",
    test_service_lines_remain_in_review_output_only,
)

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
print(
    "External integration: Not called"
)
print(
    "PHI handling: Values and source evidence were not printed"
)

if failed:
    raise SystemExit(
        1
    )
