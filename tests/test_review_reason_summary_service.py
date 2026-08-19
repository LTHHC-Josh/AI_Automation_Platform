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
        "Manual review needed for service codes and modifiers due to "
        "low confidence or unclear source support."
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
    assert "quantity" in summary
    assert "authorization status" in summary


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
        "Manual review needed for service codes due to low confidence or "
        "unclear source support."
    )
    assert result.values["AI Review Required"] is True


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic markers only; no protected data accessed")
