from src.ai.llm.providers.ollama_provider import (
    OllamaProvider,
)


def build_provider_without_connection() -> OllamaProvider:
    """
    Build the provider without reading environment configuration or
    contacting the local Ollama server.
    """

    provider = OllamaProvider.__new__(
        OllamaProvider
    )

    provider.seed = 42
    provider._last_request_metrics = {}

    return provider


def test_enhanced_demo_fields_are_in_extraction_schema() -> None:
    field_properties = (
        OllamaProvider.EXTRACTION_SCHEMA[
            "properties"
        ][
            "fields"
        ][
            "properties"
        ]
    )

    assert "hours" in field_properties
    assert "days_per_week" in field_properties


def test_authorization_status_prompt_rejects_blended_request_status() -> None:
    provider = build_provider_without_connection()

    prompt = " ".join(
        provider._extraction_prompt()
        .lower()
        .split()
    )

    assert "approved requested" in prompt
    assert "request for services" in prompt
    assert "does not by itself prove approval" in prompt


def test_hours_and_days_prompt_forbids_quantity_inference() -> None:
    provider = build_provider_without_connection()

    prompt = provider._extraction_prompt().lower()

    assert "hours and days per week" in prompt
    assert "do not derive hours or days_per_week" in prompt
    assert "authorized units" in prompt


def test_identifier_prompt_is_payer_agnostic() -> None:
    provider = build_provider_without_connection()

    prompt = " ".join(
        provider._extraction_prompt()
        .lower()
        .split()
    )

    assert "for molina documents" not in prompt
    assert "authorization documents may use labels such as" in prompt
    assert "do not infer identifier meaning from payer" in prompt


def test_service_line_prompt_matches_deterministic_evidence_contract() -> None:
    provider = build_provider_without_connection()

    base_prompt = " ".join(
        provider._extraction_prompt()
        .lower()
        .split()
    )

    retry_prompt = " ".join(
        provider._retry_prompt_addendum()
        .lower()
        .split()
    )

    for prompt in (
        base_prompt,
        retry_prompt,
    ):
        assert "service_code" in prompt
        assert "modifier" in prompt
        assert "quantity" in prompt
        assert "start_date" in prompt
        assert "end_date" in prompt
        assert "status" in prompt
        assert "same row evidence" in prompt

    assert (
        "do not preserve a value merely because it appears elsewhere "
        "in the document"
        in base_prompt
    )

    assert (
        "do not preserve a row value merely because it appears elsewhere "
        "in the document"
        in retry_prompt
    )


def test_schema_requires_service_lines() -> None:
    required_fields = (
        OllamaProvider.EXTRACTION_SCHEMA[
            "required"
        ]
    )

    assert "fields" in required_fields
    assert "service_lines" in required_fields


def test_learning_schema_and_prompt_are_value_free_and_open_ended() -> None:
    provider = build_provider_without_connection()
    schema = OllamaProvider.LEARNING_ANALYSIS_SCHEMA
    prompt = " ".join(provider._learning_analysis_prompt().lower().split())

    assert set(schema["required"]) == {
        "document_structure",
        "date_fields",
        "authorization_service_structure",
        "business_concepts",
        "schema_gaps",
        "coverage",
        "observations",
        "contradictions",
    }
    assert "never return" in prompt
    assert "actual dates" in prompt
    assert "not a fixed list" in prompt
    assert "do not infer" in prompt
    assert "every page and block" in prompt
    assert "optional hints" in prompt
    assert "contact failure does not mean utl" in prompt


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


def test_first_attempt_uses_base_seed() -> None:
    provider = build_provider_without_connection()

    assert provider._seed_for_attempt(
        1
    ) == 42


def test_second_attempt_uses_alternate_seed() -> None:
    provider = build_provider_without_connection()

    assert provider._seed_for_attempt(
        2
    ) == 43


def test_retry_seed_is_deterministic() -> None:
    provider = build_provider_without_connection()

    first_value = provider._seed_for_attempt(
        2
    )

    second_value = provider._seed_for_attempt(
        2
    )

    assert first_value == second_value
    assert first_value == 43


def test_invalid_attempt_defaults_to_first_seed() -> None:
    provider = build_provider_without_connection()

    assert provider._seed_for_attempt(
        0
    ) == 42

    assert provider._seed_for_attempt(
        -1
    ) == 42

    assert provider._seed_for_attempt(
        "invalid"
    ) == 42

    assert provider._seed_for_attempt(
        True
    ) == 42


def test_first_attempt_uses_original_prompt() -> None:
    provider = build_provider_without_connection()

    base_prompt = provider._extraction_prompt()

    first_attempt_prompt = (
        provider._extraction_prompt_for_attempt(
            1
        )
    )

    assert first_attempt_prompt == base_prompt

    assert (
        "CONTROLLED RETRY VERIFICATION"
        not in first_attempt_prompt
    )


def test_second_attempt_adds_retry_verification_prompt() -> None:
    provider = build_provider_without_connection()

    base_prompt = provider._extraction_prompt()

    retry_prompt = (
        provider._extraction_prompt_for_attempt(
            2
        )
    )

    assert retry_prompt.startswith(
        base_prompt
    )

    assert (
        "CONTROLLED RETRY VERIFICATION"
        in retry_prompt
    )

    assert (
        "Reconstruct every service line independently"
        in retry_prompt
    )

    assert (
        "confirm that service_code appears"
        in retry_prompt
    )

    assert (
        "confirm that quantity appears"
        in retry_prompt
    )

    assert (
        "Do not combine a service code from one row"
        in retry_prompt
    )

    assert (
        "Return null or omit an unsupported row"
        in retry_prompt
    )


def test_retry_prompt_addendum_is_generic() -> None:
    provider = build_provider_without_connection()

    addendum = provider._retry_prompt_addendum()

    normalized_addendum = addendum.lower()

    assert "molina" not in normalized_addendum
    assert "humana" not in normalized_addendum
    assert "medicaid" not in normalized_addendum
    assert "s9110" not in normalized_addendum
    assert "u1" not in normalized_addendum

    assert (
        "do not infer payer-specific meaning"
        in normalized_addendum
    )

    assert (
        "do not fill a missing value"
        in normalized_addendum
    )

    assert (
        "approved_visits must remain separate "
        "from authorized_units"
        in normalized_addendum
    )


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
    print(
        "=" * 60
    )

    print(
        "Testing Ollama Service-Line Schema and Retry Prompt"
    )

    print(
        "=" * 60
    )

    tests = [
        (
            "enhanced demo fields are in extraction schema",
            test_enhanced_demo_fields_are_in_extraction_schema,
        ),
        (
            "authorization status prompt rejects blended request status",
            test_authorization_status_prompt_rejects_blended_request_status,
        ),
        (
            "hours and days prompt forbids quantity inference",
            test_hours_and_days_prompt_forbids_quantity_inference,
        ),
        (
            "identifier prompt is payer agnostic",
            test_identifier_prompt_is_payer_agnostic,
        ),
        (
            "service-line prompt matches deterministic evidence contract",
            test_service_line_prompt_matches_deterministic_evidence_contract,
        ),
        (
            "schema requires service lines",
            test_schema_requires_service_lines,
        ),
        (
            "learning schema and prompt are value free",
            test_learning_schema_and_prompt_are_value_free_and_open_ended,
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
        (
            "first attempt uses base seed",
            test_first_attempt_uses_base_seed,
        ),
        (
            "second attempt uses alternate seed",
            test_second_attempt_uses_alternate_seed,
        ),
        (
            "retry seed is deterministic",
            test_retry_seed_is_deterministic,
        ),
        (
            "invalid attempt defaults to first seed",
            test_invalid_attempt_defaults_to_first_seed,
        ),
        (
            "first attempt uses original prompt",
            test_first_attempt_uses_original_prompt,
        ),
        (
            "second attempt adds retry verification prompt",
            test_second_attempt_adds_retry_verification_prompt,
        ),
        (
            "retry prompt addendum is generic",
            test_retry_prompt_addendum_is_generic,
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
