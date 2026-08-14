from pathlib import Path
from typing import Any, Callable

from src.document_processing.document_processor import (
    DocumentProcessor,
)
from src.models.document import Document
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)


def build_processor_without_providers() -> DocumentProcessor:
    """
    Build a processor without initializing OCR or Ollama.

    These tests exercise deterministic conversion, retry detection,
    candidate validation, and candidate selection only.
    """

    processor = DocumentProcessor.__new__(
        DocumentProcessor
    )

    processor.evidence_validation = EvidenceValidationService()

    return processor


def confidence_field(
    value: Any,
    source_text: str,
    confidence: float = 0.90,
) -> dict[str, Any]:
    """
    Build one synthetic field-evidence record.
    """

    return {
        "value": value,
        "confidence": confidence,
        "source_text": source_text,
    }


def build_template_document() -> Document:
    """
    Build a synthetic authorization document for candidate validation.
    """

    return Document(
        file_path=Path(
            "synthetic.pdf"
        ),
        document_type="authorization",
        confidence=0.90,
        raw_text="Synthetic local OCR text",
    )


def build_complete_extraction() -> dict[str, Any]:
    """
    Build a structurally complete synthetic authorization extraction.
    """

    return {
        "fields": {
            "authorization_status": confidence_field(
                "Approved",
                "Approved",
            ),
            "service_code": confidence_field(
                "SYNTH1",
                "SYNTH1",
            ),
            "service_codes": confidence_field(
                [
                    "SYNTH1",
                ],
                "SYNTH1",
            ),
            "modifier": confidence_field(
                None,
                "",
                0.0,
            ),
            "authorized_units": confidence_field(
                [
                    1,
                    6,
                ],
                "1 6",
            ),
            "start_date": confidence_field(
                "2025-11-25",
                "11/25/2025",
            ),
            "end_date": confidence_field(
                "2026-05-23",
                "05/23/2026",
            ),
        },
        "service_lines": [
            {
                "service_code": "SYNTH1",
                "modifier": None,
                "quantity": 1,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.90,
                "source_text": (
                    "SYNTH1 1 11/25/2025 "
                    "05/23/2026 Approved"
                ),
            },
            {
                "service_code": "SYNTH1",
                "modifier": None,
                "quantity": 6,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.90,
                "source_text": (
                    "SYNTH1 6 11/25/2025 "
                    "05/23/2026 Approved"
                ),
            },
        ],
    }


def build_raw_complete_but_unsupported_extraction() -> dict[str, Any]:
    """
    Reproduce the real failure pattern.

    The raw second row contains a service code and quantity, so the raw
    structural check considers it complete. Its source evidence does
    not support either value, so deterministic validation must clear
    them and the validated candidate must trigger retry.
    """

    return {
        "fields": {
            "authorization_status": confidence_field(
                "Approved",
                "Approved",
            ),
            "service_code": confidence_field(
                "SYNTH1",
                "SYNTH1",
            ),
            "service_codes": confidence_field(
                [
                    "SYNTH1",
                ],
                "SYNTH1",
            ),
            "modifier": confidence_field(
                "U1",
                "U1",
            ),
            "authorized_units": confidence_field(
                [
                    6,
                ],
                "6",
            ),
            "start_date": confidence_field(
                "2025-11-25",
                "11/25/2025",
            ),
            "end_date": confidence_field(
                "2026-05-23",
                "05/23/2026",
            ),
        },
        "service_lines": [
            {
                "service_code": "SYNTH1",
                "modifier": "U1",
                "quantity": 6,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.90,
                "source_text": (
                    "SYNTH1 U1 6 11/25/2025 "
                    "05/23/2026 Approved"
                ),
            },
            {
                "service_code": "SYNTH1",
                "modifier": None,
                "quantity": 1,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.90,
                "source_text": (
                    "11/25/2025 05/23/2026 Approved"
                ),
            },
        ],
    }


def build_incomplete_extraction() -> dict[str, Any]:
    """
    Build a structurally incomplete authorization extraction.
    """

    return {
        "fields": {
            "authorization_status": confidence_field(
                "Approved",
                "Approved",
            ),
            "service_code": confidence_field(
                "SYNTH1",
                "SYNTH1",
            ),
            "service_codes": confidence_field(
                None,
                "",
                0.0,
            ),
            "modifier": confidence_field(
                "U1",
                "U1",
            ),
            "authorized_units": confidence_field(
                [
                    6,
                ],
                "6",
            ),
            "start_date": confidence_field(
                "2025-11-25",
                "11/25/2025",
            ),
            "end_date": confidence_field(
                "2026-05-23",
                "05/23/2026",
            ),
        },
        "service_lines": [
            {
                "service_code": "SYNTH1",
                "modifier": "U1",
                "quantity": 6,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.90,
                "source_text": (
                    "SYNTH1 U1 6 11/25/2025 "
                    "05/23/2026 Approved"
                ),
            },
            {
                "service_code": None,
                "modifier": None,
                "quantity": None,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.50,
                "source_text": (
                    "11/25/2025 05/23/2026 Approved"
                ),
            },
        ],
    }


def build_structurally_empty_authorization_extraction() -> dict[str, Any]:
    """
    Build an authorization extraction with schema but no service data.
    """

    return {
        "fields": {
            "authorization_status": confidence_field(
                None,
                "",
                0.0,
            ),
            "service_code": confidence_field(
                None,
                "",
                0.0,
            ),
            "service_codes": confidence_field(
                [],
                "",
                0.0,
            ),
            "modifier": confidence_field(
                None,
                "",
                0.0,
            ),
            "authorized_units": confidence_field(
                None,
                "",
                0.0,
            ),
            "approved_visits": confidence_field(
                None,
                "",
                0.0,
            ),
            "start_date": confidence_field(
                None,
                "",
                0.0,
            ),
            "end_date": confidence_field(
                None,
                "",
                0.0,
            ),
        },
        "service_lines": [],
    }


def test_missing_service_lines_returns_empty_list() -> None:
    processor = build_processor_without_providers()

    service_lines = processor._get_service_lines(
        {
            "fields": {},
        }
    )

    assert service_lines == []


def test_non_list_service_lines_returns_empty_list() -> None:
    processor = build_processor_without_providers()

    service_lines = processor._get_service_lines(
        {
            "service_lines": {
                "service_code": "SYNTH1",
            },
        }
    )

    assert service_lines == []


def test_service_lines_preserve_row_relationships() -> None:
    processor = build_processor_without_providers()

    extraction_result = {
        "fields": {},
        "service_lines": [
            {
                "service_code": "SYNTH1",
                "modifier": None,
                "quantity": 6,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.94,
                "source_text": (
                    "SYNTH1 6 11/25/2025 "
                    "05/23/2026 Approved"
                ),
            },
            {
                "service_code": "SYNTH1",
                "modifier": "U1",
                "quantity": 1,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.91,
                "source_text": (
                    "SYNTH1 U1 1 11/25/2025 "
                    "05/23/2026 Approved"
                ),
            },
        ],
    }

    service_lines = processor._get_service_lines(
        extraction_result
    )

    assert len(
        service_lines
    ) == 2

    assert service_lines[0].service_code == "SYNTH1"
    assert service_lines[0].modifier is None
    assert service_lines[0].quantity == 6
    assert service_lines[0].status == "Approved"
    assert service_lines[0].confidence == 0.94

    assert service_lines[1].service_code == "SYNTH1"
    assert service_lines[1].modifier == "U1"
    assert service_lines[1].quantity == 1
    assert service_lines[1].status == "Approved"
    assert service_lines[1].confidence == 0.91


def test_service_line_confidence_is_normalized() -> None:
    processor = build_processor_without_providers()

    service_lines = processor._get_service_lines(
        {
            "service_lines": [
                {
                    "service_code": "SYNTH1",
                    "quantity": 1,
                    "confidence": 95,
                    "source_text": "SYNTH1 quantity 1",
                },
            ],
        }
    )

    assert len(
        service_lines
    ) == 1

    assert service_lines[0].confidence == 0.95


def test_empty_service_line_is_ignored() -> None:
    processor = build_processor_without_providers()

    service_lines = processor._get_service_lines(
        {
            "service_lines": [
                {
                    "service_code": " ",
                    "modifier": None,
                    "quantity": None,
                    "start_date": "",
                    "end_date": "",
                    "status": None,
                    "confidence": 1.0,
                    "source_text": "",
                },
            ],
        }
    )

    assert service_lines == []


def test_invalid_service_line_items_are_ignored() -> None:
    processor = build_processor_without_providers()

    service_lines = processor._get_service_lines(
        {
            "service_lines": [
                None,
                "not a service line",
                7,
                {
                    "service_code": "SYNTH1",
                    "quantity": 2,
                    "confidence": 0.90,
                    "source_text": "SYNTH1 quantity 2",
                },
            ],
        }
    )

    assert len(
        service_lines
    ) == 1

    assert service_lines[0].service_code == "SYNTH1"
    assert service_lines[0].quantity == 2


def test_flat_fields_remain_separate_from_service_lines() -> None:
    processor = build_processor_without_providers()

    extraction_result = {
        "fields": {
            "service_code": {
                "value": "SYNTH1",
                "confidence": 0.95,
                "source_text": "Service Code: SYNTH1",
            },
            "authorized_units": {
                "value": [
                    6,
                    1,
                ],
                "confidence": 0.90,
                "source_text": "Service quantities 6 and 1",
            },
        },
        "service_lines": [
            {
                "service_code": "SYNTH1",
                "modifier": None,
                "quantity": 6,
                "confidence": 0.90,
                "source_text": "SYNTH1 quantity 6",
            },
            {
                "service_code": "SYNTH1",
                "modifier": "U1",
                "quantity": 1,
                "confidence": 0.90,
                "source_text": "SYNTH1 U1 quantity 1",
            },
        ],
    }

    field_evidence = processor._get_field_evidence(
        extraction_result
    )

    service_lines = processor._get_service_lines(
        extraction_result
    )

    assert field_evidence[
        "service_code"
    ]["value"] == "SYNTH1"

    assert field_evidence[
        "authorized_units"
    ]["value"] == [6, 1]

    assert len(
        service_lines
    ) == 2

    assert service_lines[0].quantity == 6
    assert service_lines[1].quantity == 1


def test_complete_authorization_does_not_require_raw_retry() -> None:
    processor = build_processor_without_providers()

    assert not processor._should_retry_extraction(
        extraction_result=build_complete_extraction(),
        document_type="authorization",
    )


def test_complete_validated_authorization_does_not_require_retry() -> None:
    processor = build_processor_without_providers()

    candidate = processor._build_validated_candidate(
        template_document=build_template_document(),
        extraction_result=build_complete_extraction(),
    )

    assert not processor._should_retry_validated_candidate(
        candidate=candidate,
        document_type="authorization",
    )


def test_incomplete_service_line_requires_raw_retry() -> None:
    processor = build_processor_without_providers()

    assert processor._should_retry_extraction(
        extraction_result=build_incomplete_extraction(),
        document_type="authorization",
    )


def test_missing_service_codes_list_requires_raw_retry() -> None:
    processor = build_processor_without_providers()

    extraction_result = build_complete_extraction()

    extraction_result[
        "fields"
    ][
        "service_codes"
    ] = confidence_field(
        None,
        "",
        0.0,
    )

    assert processor._should_retry_extraction(
        extraction_result=extraction_result,
        document_type="authorization",
    )


def test_structurally_empty_authorization_requires_retry() -> None:
    processor = build_processor_without_providers()

    extraction_result = (
        build_structurally_empty_authorization_extraction()
    )

    raw_retry_required = processor._should_retry_extraction(
        extraction_result=extraction_result,
        document_type="authorization",
    )

    candidate = processor._build_validated_candidate(
        template_document=build_template_document(),
        extraction_result=extraction_result,
    )

    assert candidate.service_lines == []

    validated_retry_required = (
        processor._should_retry_validated_candidate(
            candidate=candidate,
            document_type="authorization",
        )
    )

    assert raw_retry_required
    assert validated_retry_required


def test_non_authorization_does_not_use_authorization_retry() -> None:
    processor = build_processor_without_providers()

    assert not processor._should_retry_extraction(
        extraction_result=build_incomplete_extraction(),
        document_type="assessment",
    )

    candidate = processor._build_validated_candidate(
        template_document=build_template_document(),
        extraction_result=build_incomplete_extraction(),
    )

    assert not processor._should_retry_validated_candidate(
        candidate=candidate,
        document_type="assessment",
    )


def test_validation_cleared_row_requires_retry() -> None:
    processor = build_processor_without_providers()

    extraction_result = (
        build_raw_complete_but_unsupported_extraction()
    )

    assert not processor._should_retry_extraction(
        extraction_result=extraction_result,
        document_type="authorization",
    )

    candidate = processor._build_validated_candidate(
        template_document=build_template_document(),
        extraction_result=extraction_result,
    )

    assert len(
        candidate.service_lines
    ) == 2

    assert candidate.service_lines[1].service_code is None
    assert candidate.service_lines[1].quantity is None
    assert candidate.service_lines[1].start_date is not None
    assert candidate.service_lines[1].end_date is not None
    assert candidate.service_lines[1].status == "Approved"

    assert processor._should_retry_validated_candidate(
        candidate=candidate,
        document_type="authorization",
    )


def test_stronger_validated_candidate_is_selected() -> None:
    processor = build_processor_without_providers()

    selected, selected_attempt = (
        processor._select_extraction_candidate(
            template_document=build_template_document(),
            first_result=build_incomplete_extraction(),
            second_result=build_complete_extraction(),
        )
    )

    assert selected_attempt == 2

    assert len(
        selected.service_lines
    ) == 2

    observed_quantities = {
        str(
            service_line.quantity
        )
        for service_line in selected.service_lines
    }

    assert observed_quantities == {
        "1",
        "6",
    }


def test_equal_candidates_preserve_first_attempt() -> None:
    processor = build_processor_without_providers()

    selected, selected_attempt = (
        processor._select_extraction_candidate(
            template_document=build_template_document(),
            first_result=build_complete_extraction(),
            second_result=build_complete_extraction(),
        )
    )

    assert selected_attempt == 1

    assert len(
        selected.service_lines
    ) == 2


def test_candidates_are_never_merged() -> None:
    processor = build_processor_without_providers()

    first_result = build_incomplete_extraction()
    second_result = build_complete_extraction()

    first_result[
        "fields"
    ][
        "modifier"
    ] = confidence_field(
        "U1",
        "U1",
    )

    second_result[
        "fields"
    ][
        "modifier"
    ] = confidence_field(
        None,
        "",
        0.0,
    )

    selected, selected_attempt = (
        processor._select_extraction_candidate(
            template_document=build_template_document(),
            first_result=first_result,
            second_result=second_result,
        )
    )

    assert selected_attempt == 2

    assert selected.extracted_data.get(
        "modifier"
    ) is None


def test_candidate_quantities_are_never_merged() -> None:
    processor = build_processor_without_providers()

    first_result = build_incomplete_extraction()
    second_result = build_complete_extraction()

    first_result[
        "fields"
    ][
        "authorized_units"
    ] = confidence_field(
        [9],
        "9",
    )
    first_result["service_lines"][0]["quantity"] = 9
    first_result["service_lines"][0]["source_text"] = (
        "SYNTH1 U1 9 11/25/2025 "
        "05/23/2026 Approved"
    )

    selected, selected_attempt = (
        processor._select_extraction_candidate(
            template_document=build_template_document(),
            first_result=first_result,
            second_result=second_result,
        )
    )

    assert selected_attempt == 2
    assert {
        str(quantity)
        for quantity in selected.extracted_data[
            "authorized_units"
        ]
    } == {"1", "6"}
    assert {
        str(service_line.quantity)
        for service_line in selected.service_lines
    } == {"1", "6"}


def run_test(
    test_name: str,
    test_function: Callable[[], None],
) -> bool:
    try:
        test_function()
    except AssertionError:
        print(
            f"FAILED: {test_name}"
        )

        return False

    print(
        f"PASSED: {test_name}"
    )

    return True


def main() -> None:
    print(
        "=" * 60
    )

    print(
        "Testing Document Processor Service-Line Conversion"
    )

    print(
        "=" * 60
    )

    tests = [
        (
            "missing service lines return empty list",
            test_missing_service_lines_returns_empty_list,
        ),
        (
            "non-list service lines return empty list",
            test_non_list_service_lines_returns_empty_list,
        ),
        (
            "service lines preserve row relationships",
            test_service_lines_preserve_row_relationships,
        ),
        (
            "service-line confidence is normalized",
            test_service_line_confidence_is_normalized,
        ),
        (
            "empty service line is ignored",
            test_empty_service_line_is_ignored,
        ),
        (
            "invalid service-line items are ignored",
            test_invalid_service_line_items_are_ignored,
        ),
        (
            "flat fields remain separate",
            test_flat_fields_remain_separate_from_service_lines,
        ),
        (
            "complete authorization does not require raw retry",
            test_complete_authorization_does_not_require_raw_retry,
        ),
        (
            "complete validated authorization does not retry",
            test_complete_validated_authorization_does_not_require_retry,
        ),
        (
            "incomplete service line requires raw retry",
            test_incomplete_service_line_requires_raw_retry,
        ),
        (
            "missing service_codes requires raw retry",
            test_missing_service_codes_list_requires_raw_retry,
        ),
        (
            "structurally empty authorization requires retry",
            test_structurally_empty_authorization_requires_retry,
        ),
        (
            "non-authorization does not use authorization retry",
            test_non_authorization_does_not_use_authorization_retry,
        ),
        (
            "validation-cleared row requires retry",
            test_validation_cleared_row_requires_retry,
        ),
        (
            "stronger validated candidate is selected",
            test_stronger_validated_candidate_is_selected,
        ),
        (
            "equal candidates preserve first attempt",
            test_equal_candidates_preserve_first_attempt,
        ),
        (
            "candidates are never merged",
            test_candidates_are_never_merged,
        ),
        (
            "candidate quantities are never merged",
            test_candidate_quantities_are_never_merged,
        ),
    ]

    passed = 0
    failed = 0

    for test_name, test_function in tests:
        if run_test(
            test_name,
            test_function,
        ):
            passed += 1
        else:
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

    print(
        "=" * 60
    )

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()
