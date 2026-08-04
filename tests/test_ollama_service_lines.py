from src.ai.llm.providers.ollama_provider import (
    OllamaProvider,
)


def build_provider_without_connection() -> OllamaProvider:
    """
    Build the provider without reading environment configuration or
    contacting the local Ollama server.
    """

    return OllamaProvider.__new__(
        OllamaProvider
    )


def test_schema_requires_service_lines() -> None:
    required_fields = (
        OllamaProvider.EXTRACTION_SCHEMA[
            "required"
        ]
    )

    assert "fields" in required_fields
    assert "service_lines" in required_fields


def test_empty_service_lines_are_preserved() -> None:
    provider = build_provider_without_connection()

    normalized = provider._normalize_service_lines(
        []
    )

    assert normalized == []


def test_non_list_service_lines_return_empty_list() -> None:
    provider = build_provider_without_connection()

    normalized = provider._normalize_service_lines(
        {
            "service_code": "SYNTH1",
        }
    )

    assert normalized == []


def test_service_line_relationships_are_preserved() -> None:
    provider = build_provider_without_connection()

    normalized = provider._normalize_service_lines(
        [
            {
                "service_code": " SYNTH1 ",
                "modifier": None,
                "quantity": 6,
                "start_date": " 2025-11-25 ",
                "end_date": " 2026-05-23 ",
                "status": " Approved ",
                "confidence": 0.94,
                "source_text": (
                    "SYNTH1 6 2025-11-25 "
                    "2026-05-23 Approved"
                ),
            },
            {
                "service_code": "SYNTH1",
                "modifier": " U1 ",
                "quantity": 1,
                "start_date": "2025-11-25",
                "end_date": "2026-05-23",
                "status": "Approved",
                "confidence": 0.91,
                "source_text": (
                    "SYNTH1 U1 1 2025-11-25 "
                    "2026-05-23 Approved"
                ),
            },
        ]
    )

    assert len(
        normalized
    ) == 2

    assert normalized[0] == {
        "service_code": "SYNTH1",
        "modifier": None,
        "quantity": 6,
        "start_date": "2025-11-25",
        "end_date": "2026-05-23",
        "status": "Approved",
        "confidence": 0.94,
        "source_text": (
            "SYNTH1 6 2025-11-25 "
            "2026-05-23 Approved"
        ),
    }

    assert normalized[1] == {
        "service_code": "SYNTH1",
        "modifier": "U1",
        "quantity": 1,
        "start_date": "2025-11-25",
        "end_date": "2026-05-23",
        "status": "Approved",
        "confidence": 0.91,
        "source_text": (
            "SYNTH1 U1 1 2025-11-25 "
            "2026-05-23 Approved"
        ),
    }


def test_confidence_is_normalized() -> None:
    provider = build_provider_without_connection()

    normalized = provider._normalize_service_lines(
        [
            {
                "service_code": "SYNTH1",
                "modifier": None,
                "quantity": 1,
                "start_date": None,
                "end_date": None,
                "status": None,
                "confidence": 95,
                "source_text": "SYNTH1 quantity 1",
            },
        ]
    )

    assert normalized[0]["confidence"] == 0.95


def test_empty_rows_are_removed() -> None:
    provider = build_provider_without_connection()

    normalized = provider._normalize_service_lines(
        [
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
        ]
    )

    assert normalized == []


def test_invalid_items_are_removed() -> None:
    provider = build_provider_without_connection()

    normalized = provider._normalize_service_lines(
        [
            None,
            "invalid",
            7,
            {
                "service_code": "SYNTH1",
                "modifier": None,
                "quantity": 2,
                "start_date": None,
                "end_date": None,
                "status": None,
                "confidence": 0.90,
                "source_text": "SYNTH1 quantity 2",
            },
        ]
    )

    assert len(
        normalized
    ) == 1

    assert normalized[0]["quantity"] == 2


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
    print("Testing Ollama Service-Line Schema")
    print("=" * 60)

    tests = [
        (
            "schema requires service lines",
            test_schema_requires_service_lines,
        ),
        (
            "empty service lines are preserved",
            test_empty_service_lines_are_preserved,
        ),
        (
            "non-list service lines return empty list",
            test_non_list_service_lines_return_empty_list,
        ),
        (
            "service-line relationships are preserved",
            test_service_line_relationships_are_preserved,
        ),
        (
            "confidence is normalized",
            test_confidence_is_normalized,
        ),
        (
            "empty rows are removed",
            test_empty_rows_are_removed,
        ),
        (
            "invalid items are removed",
            test_invalid_items_are_removed,
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