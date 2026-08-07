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
):
    return ReviewOutput(
        document_type="authorization",
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
    )

    assert (
        result.values[
            "Authorization Status"
        ]
        == "Approved"
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
    )

    assert (
        result.missing_required_columns
        == [
            "Approved Visits"
        ]
    )
    assert result.ready_for_write is False


def test_human_review_blocks_automatic_write():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(
            needs_human_review=True
        ),
        policies=[],
    )

    assert result.ready_for_write is False
    assert len(
        result.warnings
    ) == 1


def test_recommended_review_is_ready_after_complete_approval():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(
            needs_human_review=True,
            review_status="Human Review Recommended",
        ),
        policies=[],
        complete_review_approved=True,
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


def test_required_review_stays_blocked_after_approval_flag():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(
            needs_human_review=True,
            review_status="Human Review Required",
        ),
        policies=[],
        complete_review_approved=True,
    )

    assert result.ready_for_write is False


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
    )

    assert result.review_only_columns == [
        "Quantity for Review"
    ]


def test_review_metadata_is_preserved():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=build_review_output(),
        policies=[],
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
    )

    assert result.ready_for_write is True


def test_invalid_review_output_is_rejected():
    service = SmartsheetReviewRowMappingService()

    result = service.map(
        review_output=None,
        policies=[],
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
    "list order is preserved",
    test_list_order_is_preserved,
)
run_test(
    "missing required value blocks write",
    test_missing_required_value_blocks_write,
)
run_test(
    "human review blocks automatic write",
    test_human_review_blocks_automatic_write,
)
run_test(
    "recommended review proceeds after complete approval",
    test_recommended_review_is_ready_after_complete_approval,
)
run_test(
    "required review remains blocked after approval flag",
    test_required_review_stays_blocked_after_approval_flag,
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
