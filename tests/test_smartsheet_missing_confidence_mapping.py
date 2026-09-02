from src.models.smartsheet_mapping import SmartsheetColumnPolicy
from src.services.review_output_service import ReviewField, ReviewOutput
from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService


def output(field, reasons):
    return ReviewOutput(
        document_type="authorization",
        fields=[field],
        needs_human_review=True,
        review_status="Human Review Required",
        review_reasons=reasons,
    )


def policy(*, supports_text):
    return SmartsheetColumnPolicy(
        source_field="service_codes",
        column_name="Service Codes",
        confidence_column_name="Service Codes Conf.",
        confidence_column_supports_text=supports_text,
    )


def map_output(review_output, *, supports_text):
    return SmartsheetReviewRowMappingService().map(
        review_output=review_output,
        policies=[policy(supports_text=supports_text)],
        run_type="Synthetic confidence status",
    )


def test_supported_value_maps_actual_confidence():
    result = map_output(
        output(ReviewField("service_codes", ["SYNTHETIC-CODE"], 0.85, "Synthetic evidence"), []),
        supports_text=False,
    )
    assert result.values["Service Codes Conf."] == 0.85


def test_explicit_missing_reason_keeps_value_and_confidence_blank():
    field = ReviewField("service_codes", None, 0.0, "", confidence_available=False)
    reasons = ["Service codes were not extracted from the document."]
    text_result = map_output(output(field, reasons), supports_text=True)
    numeric_result = map_output(output(field, reasons), supports_text=False)
    assert "Service Codes Conf." not in text_result.values
    assert "Service Codes Conf." not in numeric_result.values
    assert "Missing/Not extracted" not in text_result.values.values()


def test_explicit_cleared_reason_keeps_production_confidence_blank():
    field = ReviewField("service_codes", None, 0.0, "", confidence_available=True)
    review_output = output(field, ["Unsupported service code evidence was cleared."])
    result = map_output(review_output, supports_text=True)
    assert "Service Codes Conf." not in result.values
    assert review_output.fields[0].confidence == 0.0
    assert review_output.fields[0].confidence_available is True


def test_numeric_only_cleared_field_leaves_production_confidence_blank():
    field = ReviewField("service_codes", None, 0.0, "", confidence_available=True)
    result = map_output(
        output(field, ["Unsupported service code evidence was cleared."]),
        supports_text=False,
    )
    assert "Service Codes Conf." not in result.values
    assert "Unsupported/Cleared" not in result.values.values()
    assert "confidence_status_destination_constraint" not in result.warnings


def test_below_threshold_candidate_confidence_is_not_a_production_confidence():
    result = map_output(
        output(ReviewField("service_codes", ["SYNTHETIC-CODE"], 0.84, "Synthetic evidence"), []),
        supports_text=False,
    )
    assert "Service Codes" not in result.values
    assert "Service Codes Conf." not in result.values


def test_blank_field_with_unrelated_reason_does_not_infer_cause_or_zero():
    field = ReviewField("service_codes", None, 0.0, "", confidence_available=False)
    result = map_output(
        output(field, ["Authorization status requires verification."]),
        supports_text=True,
    )
    assert "Service Codes Conf." not in result.values


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic values only")
