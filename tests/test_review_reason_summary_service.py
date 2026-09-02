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
        "Service Code: Could not be verified; "
        "Service Code: Below confidence threshold; "
        "Modifier: Could not be verified"
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
    assert "Authorized Units: Could not be verified" in summary
    assert "Authorization Status: Could not be verified" in summary


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
        "Service Code: Could not be verified; "
        "Service Code: Below confidence threshold"
    )
    assert result.values["AI Review Required"] is True


def test_known_business_rule_maps_to_exact_phi_safe_code():
    assert ReviewReasonSummaryService().summarize(
        ["Authorization quantity requires verification"]
    ) == "Authorization quantity meaning requires verification"


def test_service_line_reasons_preserve_scope_and_do_not_become_document_details():
    summary = ReviewReasonSummaryService().summarize([
        "Service line 1 modifier is not supported by its source evidence",
        "Service line 1 quantity is not supported by its source evidence",
        "Service line 1 start date is not supported by its source evidence",
        "Service line 1 status is not supported by its source evidence",
        "Service line 1 confidence requires verification",
        "Service-line modifier relationship requires verification",
    ])
    assert summary == (
        "Service-line Modifier: Could not be verified; "
        "Service-line Quantity: Could not be verified; "
        "Service-line Date: Could not be verified; "
        "Service-line Status: Could not be verified; "
        "Service-line: Below confidence threshold; "
        "Modifier: Could not be assigned"
    )
    assert "Document details" not in summary


def test_internal_codes_remain_available_for_phi_safe_diagnostics():
    codes = ReviewReasonSummaryService().summarize_codes([
        "Service line 1 quantity is not supported by its source evidence"
    ])
    assert codes == "service_line_quantity_unclear_source_support"


def test_unknown_subtype_uses_operator_column_terminology_once():
    service = ReviewReasonSummaryService()
    reasons = [
        "2067 subtype could not be deterministically determined.",
        "Authorization subtype could not be determined.",
        "Authorization subtype requires verification",
    ]
    assert service.summarize_codes(reasons) == "document_subtype_unknown"
    assert service.summarize(reasons) == "AI Document Subtype: Unknown"


def test_internal_request_type_does_not_reach_operator_summary():
    service = ReviewReasonSummaryService()
    assert service.summarize_codes([
        "Request type requires checkbox or selection verification"
    ]) == ""
    assert service.summarize([
        "Request type requires checkbox or selection verification"
    ]) == ""


def test_filename_placeholder_diagnostics_do_not_reach_operator_review():
    service = ReviewReasonSummaryService()
    reasons = [
        "Filename payer could not be resolved.",
        "Filename service could not be resolved.",
        "Filename document type could not be resolved.",
        "Filename date could not be determined.",
        "Authorization subtype could not be determined.",
    ]
    assert service.summarize(reasons) == "AI Document Subtype: Unknown"


def test_filename_placeholder_diagnostics_do_not_duplicate_required_field_reasons():
    service = ReviewReasonSummaryService()
    assert service.summarize([
        "Document category could not be determined.",
        "Filename document type could not be resolved.",
        "Missing payer",
        "Filename payer could not be resolved.",
        "Missing authorization start date",
        "Filename date could not be determined.",
    ]) == (
        "Document category could not be determined; "
        "Payer: Missing; "
        "Authorization Start Date: Missing"
    )


def test_date_validation_reasons_use_exact_operator_field_terminology():
    service = ReviewReasonSummaryService()
    assert service.summarize([
        "start_date could not be normalized",
        "Missing authorization start date",
    ]) == "Authorization Start Date: Invalid"


def test_quantity_validation_reasons_are_scoped_and_actionable():
    service = ReviewReasonSummaryService()
    assert service.summarize([
        "authorized_units is not supported by its source evidence",
        "Missing authorization quantity",
        "Service line 1 quantity is not supported by its source evidence",
    ]) == "Service-line Quantity: Could not be verified"


def test_missing_field_confidence_is_not_mislabeled_as_below_threshold():
    assert ReviewReasonSummaryService().summarize([
        "Service code confidence is unavailable"
    ]) == "Service Code: Confidence unavailable"


def test_2067_unknown_subtype_maps_to_exact_smartsheet_reason():
    from src.services.review_output_service import ReviewOutput
    from src.services.smartsheet_review_row_mapping_service import (
        SmartsheetReviewRowMappingService,
    )

    output = ReviewOutput(
        document_type="2067",
        document_category="2067",
        document_subtype="unknown",
        review_status="Human Review Required",
        needs_human_review=True,
        review_reasons=[
            "2067 subtype could not be deterministically determined."
        ],
    )
    result = SmartsheetReviewRowMappingService().map(
        review_output=output,
        policies=[],
        run_type="Synthetic 2067 subtype presentation",
    )
    assert result.values["AI Review Reasons"] == (
        "AI Document Subtype: Unknown"
    )


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic markers only; no protected data accessed")
