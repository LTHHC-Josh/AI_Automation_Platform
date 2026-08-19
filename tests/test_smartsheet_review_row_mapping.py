from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)


passed = 0
failed = 0

TEST_RUN_TYPE = "Synthetic mapping regression"


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


def build_review_output(
    *,
    needs_human_review=False,
    review_status=None,
    review_reasons=None,
):
    return ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_confidence=0.90,
        fields=[
            ReviewField(
                name="authorization_status",
                value="Approved",
                confidence=0.95,
                source_text="PHI-bearing evidence",
            ),
            ReviewField(
                name="service_codes",
                value=[
                    "CODE-A",
                    "CODE-B",
                ],
                confidence=0.95,
                source_text="PHI-bearing evidence",
            ),
            ReviewField(
                name="authorized_units",
                value=[
                    "6",
                    "1",
                ],
                confidence=0.50,
                source_text="PHI-bearing evidence",
            ),
            ReviewField(
                name="approved_visits",
                value=None,
                confidence=0.0,
                source_text="",
            ),
            ReviewField(
                name="numeric_zero",
                value=0,
                confidence=0.95,
                source_text="PHI-bearing evidence",
            ),
            ReviewField(
                name="boolean_false",
                value=False,
                confidence=0.95,
                source_text="PHI-bearing evidence",
            ),
        ],
        needs_human_review=needs_human_review,
        review_status=(
            review_status
            if review_status is not None
            else (
                "Human Review Recommended"
                if needs_human_review
                else "Verified by AI"
            )
        ),
        review_reasons=(
            list(review_reasons)
            if review_reasons is not None
            else []
        ),
        minimum_field_confidence=0.50,
        extraction_attempt_count=2,
        extraction_retry_triggered=True,
        extraction_selected_attempt=2,
        authorized_units_reconciled=True,
    )


def test_approved_fields_are_mapped():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="authorization_status",
                column_name="Authorization Status",
                required=True,
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "Authorization Status"
        ]
        == "Approved"
    )


def test_field_confidence_is_mapped_without_threshold_override():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="authorized_units",
                column_name="Authorized Units",
                confidence_column_name="Authorized Units Conf.",
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "Authorized Units Conf."
        ]
        == 0.50
    )


def test_sheet_minimum_confidence_uses_only_displayed_confidences():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="service_codes",
                column_name="Service Codes",
                confidence_column_name="Service Codes Conf.",
            ),
            SmartsheetColumnPolicy(
                source_field="authorization_status",
                column_name="Authorization Status",
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "Service Codes Conf."
        ]
        == 0.95
    )

    assert (
        result.values[
            "AI Minimum Field Confidence"
        ]
        == 0.95
    )


def test_sheet_minimum_confidence_tracks_lowest_displayed_confidence():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="service_codes",
                column_name="Service Codes",
                confidence_column_name="Service Codes Conf.",
            ),
            SmartsheetColumnPolicy(
                source_field="authorized_units",
                column_name="Authorized Units",
                confidence_column_name="Authorized Units Conf.",
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "AI Minimum Field Confidence"
        ]
        == 0.50
    )


def test_sheet_minimum_confidence_is_empty_without_displayed_confidences():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="authorization_status",
                column_name="Authorization Status",
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "AI Minimum Field Confidence"
        ]
        is None
    )


def test_list_order_is_preserved():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="authorized_units",
                column_name="Authorized Units",
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "Authorized Units"
        ]
        == "6 | 1"
    )


def test_missing_required_value_blocks_write():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="approved_visits",
                column_name="Approved Visits",
                required=True,
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.missing_required_columns
        == [
            "Approved Visits"
        ]
    )
    assert result.ready_for_write is False


def test_human_review_is_ready_for_automatic_write():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(
            needs_human_review=True
        ),
        policies=[],
        run_type=TEST_RUN_TYPE,
    )

    assert result.ready_for_write is True
    assert len(
        result.warnings
    ) == 1


def test_recommended_review_is_ready_without_approval():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(
            needs_human_review=True,
            review_status="Human Review Recommended",
        ),
        policies=[],
        run_type=TEST_RUN_TYPE,
    )

    assert result.ready_for_write is True
    assert (
        result.values[
            "AI Review Status"
        ]
        == "Human Review Recommended"
    )
    assert (
        result.values[
            "AI Review Required"
        ]
        is True
    )


def test_required_review_is_ready_without_approval():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(
            needs_human_review=True,
            review_status="Human Review Required",
        ),
        policies=[],
        run_type=TEST_RUN_TYPE,
    )

    assert result.ready_for_write is True


def test_source_text_is_not_mapped():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="source_text",
                column_name="Source Text",
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert "Source Text" not in result.values
    assert result.prohibited_fields == [
        "source_text"
    ]
    assert result.ready_for_write is False


def test_raw_text_and_file_path_are_prohibited():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="raw_text",
                column_name="Raw Text",
            ),
            SmartsheetColumnPolicy(
                source_field="file_path",
                column_name="File Path",
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert result.prohibited_fields == [
        "raw_text",
        "file_path",
    ]


def test_zero_and_false_are_preserved():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="numeric_zero",
                column_name="Numeric Zero",
                required=True,
            ),
            SmartsheetColumnPolicy(
                source_field="boolean_false",
                column_name="Boolean False",
                required=True,
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert result.values[
        "Numeric Zero"
    ] == 0
    assert result.values[
        "Boolean False"
    ] is False
    assert not result.missing_required_columns


def test_duplicate_destination_column_is_ignored():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="authorization_status",
                column_name="Shared Column",
            ),
            SmartsheetColumnPolicy(
                source_field="service_codes",
                column_name="Shared Column",
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert result.values[
        "Shared Column"
    ] == "Approved"


def test_review_only_column_is_identified():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="authorized_units",
                column_name="Quantity for Review",
                review_only=True,
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert result.review_only_columns == [
        "Quantity for Review"
    ]


def test_review_metadata_is_preserved():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "AI Review Status"
        ]
        == "Verified by AI"
    )
    assert (
        result.values[
            "AI Selected Extraction Attempt"
        ]
        == 2
    )
    assert (
        result.values[
            "AI Extraction Retry Triggered"
        ]
        is True
    )
    assert (
        result.values[
            "AI Authorized Units Reconciled"
        ]
        is True
    )


def test_classification_labels_are_mapped_as_review_metadata():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "AI Document Category"
        ]
        == "authorization"
    )

    assert (
        result.values[
            "AI Document Subtype"
        ]
        == "renewal"
    )


def test_review_reasons_are_mapped_without_values_or_source_text():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(
            needs_human_review=True,
            review_reasons=[
                "Authorization quantity requires verification",
                "Authorization subtype requires verification",
            ],
        ),
        policies=[],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "AI Review Reasons"
        ]
        == (
            "Manual review needed for quantity and request type due to "
            "unclear source support."
        )
    )

    assert "PHI-bearing evidence" not in str(
        result.values[
            "AI Review Reasons"
        ]
    )


def test_empty_review_reasons_map_to_empty_text():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[],
        run_type=TEST_RUN_TYPE,
    )

    assert (
        result.values[
            "AI Review Reasons"
        ]
        == ""
    )


def test_run_type_is_mapped_as_workflow_metadata():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[],
        run_type="Review reason visibility",
    )

    assert (
        result.values[
            "Run Type"
        ]
        == "Review reason visibility"
    )


def test_blank_run_type_blocks_mapping():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[],
        run_type="",
    )

    assert result.ready_for_write is False
    assert result.values == {}

    assert (
        "Run type is unavailable or invalid."
        in result.warnings
    )


def test_free_text_run_type_is_preserved():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[],
        run_type="Classification and review reason columns",
    )

    assert (
        result.values["Run Type"]
        == "Classification and review reason columns"
    )


def test_complete_verified_mapping_is_ready():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="authorization_status",
                column_name="Authorization Status",
                required=True,
            ),
        ],
        run_type=TEST_RUN_TYPE,
    )

    assert result.ready_for_write is True


def test_invalid_review_output_is_rejected():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=None,
        policies=[],
        run_type=TEST_RUN_TYPE,
    )

    assert result.ready_for_write is False
    assert len(
        result.warnings
    ) == 1
    assert result.values == {}


print(
    "=" * 60
)
print(
    "Testing Smartsheet Review Row Mapping"
)
print(
    "=" * 60
)

run_test(
    "approved fields are mapped",
    test_approved_fields_are_mapped,
)
run_test(
    "field confidence is mapped without threshold override",
    test_field_confidence_is_mapped_without_threshold_override,
)
run_test(
    "sheet minimum confidence uses only displayed confidences",
    test_sheet_minimum_confidence_uses_only_displayed_confidences,
)
run_test(
    "sheet minimum confidence tracks lowest displayed confidence",
    test_sheet_minimum_confidence_tracks_lowest_displayed_confidence,
)
run_test(
    "sheet minimum confidence is empty without displayed confidences",
    test_sheet_minimum_confidence_is_empty_without_displayed_confidences,
)
run_test(
    "list order is preserved",
    test_list_order_is_preserved,
)
run_test(
    "missing required value blocks write",
    test_missing_required_value_blocks_write,
)
run_test(
    "human review remains ready for automatic write",
    test_human_review_is_ready_for_automatic_write,
)
run_test(
    "recommended review proceeds without approval",
    test_recommended_review_is_ready_without_approval,
)
run_test(
    "required review proceeds without approval",
    test_required_review_is_ready_without_approval,
)
run_test(
    "source_text is not mapped",
    test_source_text_is_not_mapped,
)
run_test(
    "raw text and file path are prohibited",
    test_raw_text_and_file_path_are_prohibited,
)
run_test(
    "zero and false are preserved",
    test_zero_and_false_are_preserved,
)
run_test(
    "duplicate destination column is ignored",
    test_duplicate_destination_column_is_ignored,
)
run_test(
    "review-only column is identified",
    test_review_only_column_is_identified,
)
run_test(
    "review metadata is preserved",
    test_review_metadata_is_preserved,
)
run_test(
    "classification labels are mapped as review metadata",
    test_classification_labels_are_mapped_as_review_metadata,
)
run_test(
    "review reasons are mapped without values or source text",
    test_review_reasons_are_mapped_without_values_or_source_text,
)
run_test(
    "empty review reasons map to empty text",
    test_empty_review_reasons_map_to_empty_text,
)
run_test(
    "run type is mapped as workflow metadata",
    test_run_type_is_mapped_as_workflow_metadata,
)
run_test(
    "blank run type blocks mapping",
    test_blank_run_type_blocks_mapping,
)

run_test(
    "free-text run type is preserved",
    test_free_text_run_type_is_preserved,
)
run_test(
    "complete verified mapping is ready",
    test_complete_verified_mapping_is_ready,
)
run_test(
    "invalid review output is rejected",
    test_invalid_review_output_is_rejected,
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
    "PHI handling: Values were not printed"
)

if failed:
    raise SystemExit(
        1
    )
