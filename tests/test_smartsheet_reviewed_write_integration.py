from pathlib import Path

from src.models.document import Document
from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.review_output_service import (
    ReviewOutputService,
)
from src.services.smartsheet_destination_validation_service import (
    SmartsheetDestinationValidationService,
)
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)
from src.services.smartsheet_reviewed_write_service import (
    SmartsheetReviewedWriteService,
)


passed = 0
failed = 0


class RecordingSmartsheetClient:
    def __init__(self):
        self.add_calls = []

    def add_row(
        self,
        cells,
    ):
        self.add_calls.append(
            cells
        )
        return type("SyntheticRow", (), {"id": 7001})()


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

    document.extracted_data = {
        "authorization_status": (
            "Synthetic approved status"
        ),
        "service_codes": [
            "SYNTHETIC-A",
            "SYNTHETIC-B",
        ],
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
    }

    document.field_confidences = {
        "authorization_status": 0.95,
        "service_codes": 0.95,
        "start_date": 0.95,
        "end_date": 0.95,
    }

    document.field_evidence = {
        "authorization_status": {
            "value": (
                "Synthetic approved status"
            ),
            "confidence": 0.95,
            "source_text": (
                "Synthetic source evidence."
            ),
        },
        "service_codes": {
            "value": [
                "SYNTHETIC-A",
                "SYNTHETIC-B",
            ],
            "confidence": 0.95,
            "source_text": (
                "Synthetic source evidence."
            ),
        },
        "start_date": {
            "value": "2026-01-01",
            "confidence": 0.95,
            "source_text": (
                "Synthetic source evidence."
            ),
        },
        "end_date": {
            "value": "2026-06-30",
            "confidence": 0.95,
            "source_text": (
                "Synthetic source evidence."
            ),
        },
    }

    document.needs_human_review = (
        needs_human_review
    )

    document.review_status = (
        "Human Review Recommended"
        if needs_human_review
        else "Verified by AI"
    )

    document.review_reasons = (
        [
            "Synthetic review reason"
        ]
        if needs_human_review
        else []
    )

    document.minimum_field_confidence = 0.95

    return document


def build_policies():
    return [
        SmartsheetColumnPolicy(
            source_field=(
                "authorization_status"
            ),
            column_name=(
                "Authorization Status"
            ),
            required=True,
        ),
        SmartsheetColumnPolicy(
            source_field="service_codes",
            column_name="Service Codes",
            required=True,
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


def build_available_columns(
    mapping,
):
    return {
        column_name: (
            1000 + index
        )
        for index, column_name in enumerate(
            mapping.values.keys(),
            start=1,
        )
    }


def build_pipeline(
    *,
    needs_human_review=False,
):
    document = build_document(
        needs_human_review=(
            needs_human_review
        )
    )

    review_output = (
        ReviewOutputService()
        .build(
            document
        )
    )

    mapping = (
        SmartsheetReviewRowMappingService()
        .map(
            review_output=review_output,
            policies=build_policies(),
            run_type="Reviewed write integration",
        )
    )

    available_columns = (
        build_available_columns(
            mapping
        )
    )

    validation = (
        SmartsheetDestinationValidationService()
        .validate(
            mapping=mapping,
            available_columns=(
                available_columns
            ),
        )
    )

    return (
        document,
        review_output,
        mapping,
        validation,
    )


def test_verified_document_reaches_write():
    (
        _,
        _,
        mapping,
        validation,
    ) = build_pipeline(
        needs_human_review=False
    )

    client = RecordingSmartsheetClient()

    result = (
        SmartsheetReviewedWriteService(
            client=client
        )
        .write(
            mapping=mapping,
            destination_validation=(
                validation
            ),
        )
    )

    assert mapping.ready_for_write is True
    assert validation.ready_for_write is True

    assert result.success is True
    assert result.written is True
    assert result.column_count == len(
        mapping.values
    )

    assert len(
        client.add_calls
    ) == 1


def test_human_review_reaches_write_with_review_metadata():
    (
        _,
        review_output,
        mapping,
        validation,
    ) = build_pipeline(
        needs_human_review=True
    )

    client = RecordingSmartsheetClient()

    result = (
        SmartsheetReviewedWriteService(
            client=client
        )
        .write(
            mapping=mapping,
            destination_validation=(
                validation
            ),
        )
    )

    assert (
        review_output.needs_human_review
        is True
    )

    assert mapping.ready_for_write is True
    assert validation.ready_for_write is True

    assert result.success is True
    assert result.written is True
    assert len(client.add_calls) == 1
    assert mapping.values["AI Review Required"] is True
    assert mapping.values["AI Review Reasons"]


def test_source_evidence_never_enters_cells():
    (
        _,
        review_output,
        mapping,
        validation,
    ) = build_pipeline(
        needs_human_review=False
    )

    client = RecordingSmartsheetClient()

    result = (
        SmartsheetReviewedWriteService(
            client=client
        )
        .write(
            mapping=mapping,
            destination_validation=(
                validation
            ),
        )
    )

    assert result.success is True

    written_values = [
        cell.value
        for cell in client.add_calls[0]
    ]

    source_text_values = {
        field.source_text
        for field in review_output.fields
        if field.source_text
    }

    for source_text in source_text_values:
        assert source_text not in written_values


def test_write_result_excludes_payload():
    (
        _,
        _,
        mapping,
        validation,
    ) = build_pipeline(
        needs_human_review=False
    )

    client = RecordingSmartsheetClient()

    result = (
        SmartsheetReviewedWriteService(
            client=client
        )
        .write(
            mapping=mapping,
            destination_validation=(
                validation
            ),
        )
    )

    assert not hasattr(
        result,
        "values"
    )

    assert not hasattr(
        result,
        "payload"
    )

    assert not hasattr(
        result,
        "cells"
    )

    assert not hasattr(
        result,
        "row"
    )


print(
    "=" * 60
)
print(
    "Testing Reviewed Smartsheet Write Integration"
)
print(
    "=" * 60
)

run_test(
    "verified document reaches write",
    test_verified_document_reaches_write,
)

run_test(
    "human review reaches write with review metadata",
    test_human_review_reaches_write_with_review_metadata,
)

run_test(
    "source evidence never enters cells",
    test_source_evidence_never_enters_cells,
)

run_test(
    "write result excludes payload",
    test_write_result_excludes_payload,
)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Synthetic deterministic "
    "integration with mocked Smartsheet client"
)
print(
    "Smartsheet external API: Not called"
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
    "source evidence was not written or printed"
)

if failed:
    raise SystemExit(
        1
    )
