from src.document_processing.document_processor import (
    DocumentProcessor,
)


def build_processor_without_providers() -> DocumentProcessor:
    """
    Build a processor instance without initializing OCR or Ollama.

    These tests exercise deterministic conversion helpers only.
    """

    return DocumentProcessor.__new__(
        DocumentProcessor
    )


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

    first_line = service_lines[0]
    second_line = service_lines[1]

    assert first_line.service_code == "SYNTH1"
    assert first_line.modifier is None
    assert first_line.quantity == 6
    assert first_line.status == "Approved"
    assert first_line.confidence == 0.94

    assert second_line.service_code == "SYNTH1"
    assert second_line.modifier == "U1"
    assert second_line.quantity == 1
    assert second_line.status == "Approved"
    assert second_line.confidence == 0.91


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
                "source_text": (
                    "Service quantities 6 and 1"
                ),
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


def run_test(
    test_name: str,
    test_function,
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
    print("=" * 60)
    print("Testing Document Processor Service-Line Conversion")
    print("=" * 60)

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
    print("=" * 60)

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()