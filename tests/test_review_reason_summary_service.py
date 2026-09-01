from src.services.review_reason_summary_service import ReviewReasonSummaryService


def test_summary_groups_duplicate_technical_reasons_without_mutation():
    reasons = [
        "Service code evidence is unsupported.",
        "Service code confidence is below configured reliability.",
        "Modifier requires verification.",
        "Modifier evidence is unsupported.",
    ]
    original = list(reasons)

    summary = ReviewReasonSummaryService().summarize(reasons)

    assert reasons == original
    assert summary == (
        "service_codes_unclear_source_support; "
        "service_codes_low_confidence; "
        "modifiers_unclear_source_support"
    )


def test_summary_excludes_patient_values_source_text_and_internal_wording():
    marker = "SYNTHETIC-PERSON-VALUE"
    summary = ReviewReasonSummaryService().summarize(
        [
            f"Authorization quantity {marker} source_text requires verification.",
            "Checkbox verification failed for authorization status.",
        ]
    )

    assert marker not in summary
    assert "source_text" not in summary
    assert "checkbox" not in summary.lower()
    assert "quantity_unclear_source_support" in summary
    assert "authorization_status_unclear_source_support" in summary


def test_mapper_uses_summary_but_preserves_review_output():
    from src.services.review_output_service import ReviewOutput
    from src.services.smartsheet_review_row_mapping_service import (
        SmartsheetReviewRowMappingService,
    )

    output = ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="unknown",
        review_status="Human Review Required",
        needs_human_review=True,
        review_reasons=[
            "Service code evidence is unsupported.",
            "Service code confidence is below configured reliability.",
        ],
    )
    original = list(output.review_reasons)

    result = SmartsheetReviewRowMappingService().map(
        review_output=output,
        policies=[],
        run_type="Synthetic review summary",
    )

    assert output.review_reasons == original
    assert result.values["AI Review Reasons"] == (
        "service_codes_unclear_source_support; service_codes_low_confidence"
    )
    assert result.values["AI Review Required"] is True


def test_known_business_rule_maps_to_exact_phi_safe_code():
    assert ReviewReasonSummaryService().summarize(
        ["Authorization quantity requires verification"]
    ) == "authorization_quantity_requires_verification"


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic markers only; no protected data accessed")
