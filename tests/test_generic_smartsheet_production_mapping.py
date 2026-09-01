from src.models.smartsheet_mapping import SmartsheetColumnPolicy
from src.services.review_output_service import ReviewField, ReviewOutput
from src.services.smartsheet_destination_schema_service import (
    SmartsheetDestinationSchemaResult,
)
from src.services.smartsheet_mapping_policy_service import (
    SmartsheetMappingPolicyService,
)
from src.services.smartsheet_review_configuration_service import (
    APPROVED_DOCUMENT_FIELD_POLICIES,
    SmartsheetReviewConfigurationService,
)
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)


class StaticSchemaService:
    def __init__(self, *, missing_column=None):
        column_names = {
            policy.column_name
            for policy in APPROVED_DOCUMENT_FIELD_POLICIES
        }
        column_names.update(
            policy.confidence_column_name
            for policy in APPROVED_DOCUMENT_FIELD_POLICIES
            if policy.confidence_column_name
        )
        column_names.update(
            SmartsheetReviewRowMappingService.OPERATIONAL_METADATA_COLUMNS
        )
        if missing_column is not None:
            column_names.discard(missing_column)
        self.columns = {
            name: ordinal
            for ordinal, name in enumerate(sorted(column_names), start=1)
        }

    def read(self):
        column_types = {name: "TEXT_NUMBER" for name in self.columns}
        if SmartsheetReviewRowMappingService.AI_CORRECTION_COLUMN in column_types:
            column_types[
                SmartsheetReviewRowMappingService.AI_CORRECTION_COLUMN
            ] = "CHECKBOX"
        return SmartsheetDestinationSchemaResult(
            column_count=len(self.columns),
            columns=dict(self.columns),
            column_types=column_types,
            success=True,
            status="ready",
        )


def review_output(*, family="2067", subtype="utl", needs_review=False):
    return ReviewOutput(
        document_type=family,
        document_category=family,
        document_subtype=subtype,
        classification_confidence=0.94,
        fields=[
            ReviewField(
                name="authorization_number",
                value="SYNTHETIC-SUPPORTED",
                confidence=0.92,
                source_text="Synthetic supporting evidence",
            ),
            ReviewField(
                name="service_codes",
                value="SYNTHETIC-LOW",
                confidence=0.60,
                source_text="Synthetic supporting evidence",
            ),
            ReviewField(
                name="posted_date",
                value="2099-01-01",
                confidence=0.94,
                source_text="Synthetic Posted Date evidence",
            ),
        ],
        needs_human_review=needs_review,
        review_status=(
            "Human Review Required" if needs_review else "Verified by AI"
        ),
        review_reasons=(
            ["Document subtype could not be determined."]
            if needs_review
            else []
        ),
    )


def test_2067_utl_uses_shared_approved_mapping():
    result = SmartsheetReviewConfigurationService(
        schema_service=StaticSchemaService()
    ).resolve(
        document_type="2067",
        document_family="2067",
        document_subtype="utl",
    )
    assert result.success is True
    assert result.policy_count == len(APPROVED_DOCUMENT_FIELD_POLICIES)


def test_unknown_taxonomy_uses_generic_production_mapping():
    result = SmartsheetReviewConfigurationService(
        schema_service=StaticSchemaService()
    ).resolve(
        document_type="unknown",
        document_family="unknown",
        document_subtype="unknown",
    )
    assert result.success is True


def test_family_subtype_policy_precedes_family_and_default():
    exact = SmartsheetColumnPolicy("exact", "Exact")
    family = SmartsheetColumnPolicy("family", "Family")
    default = SmartsheetColumnPolicy("default", "Default")
    service = SmartsheetMappingPolicyService(
        policies_by_document_type={
            "2067/utl": (exact,),
            "2067": (family,),
        },
        default_policies=(default,),
    )
    result = service.get(
        document_type="legacy",
        document_family="2067",
        document_subtype="utl",
    )
    assert result.policies[0].source_field == "exact"


def test_supported_value_maps_and_low_confidence_value_stays_blank():
    mapped = SmartsheetReviewRowMappingService().map(
        review_output=review_output(),
        policies=list(APPROVED_DOCUMENT_FIELD_POLICIES),
        run_type="Synthetic generic production mapping",
    )
    assert "Authorization #" in mapped.values
    assert "Service Codes" not in mapped.values
    assert "Posted Date" not in mapped.values
    assert mapped.values["AI Document Category"] == "2067"
    assert mapped.values["AI Document Subtype"] == "utl"
    assert mapped.ready_for_write is True


def test_unknown_review_required_metadata_only_row_is_writeable():
    subject = review_output(
        family="unknown",
        subtype="unknown",
        needs_review=True,
    )
    subject.fields = []
    mapped = SmartsheetReviewRowMappingService().map(
        review_output=subject,
        policies=list(APPROVED_DOCUMENT_FIELD_POLICIES),
        run_type="Synthetic generic production mapping",
    )
    assert mapped.ready_for_write is True
    assert mapped.values["AI Document Category"] == "unknown"
    assert mapped.values["AI Document Subtype"] == "unknown"
    assert mapped.values["AI Review Required"] is True


def test_missing_universal_metadata_column_fails_configuration():
    result = SmartsheetReviewConfigurationService(
        schema_service=StaticSchemaService(
            missing_column="AI Document Subtype"
        )
    ).resolve(
        document_type="2067",
        document_family="2067",
        document_subtype="utl",
    )
    assert result.success is False
    assert result.status == "policy_columns_missing"


TESTS = (
    test_2067_utl_uses_shared_approved_mapping,
    test_unknown_taxonomy_uses_generic_production_mapping,
    test_family_subtype_policy_precedes_family_and_default,
    test_supported_value_maps_and_low_confidence_value_stays_blank,
    test_unknown_review_required_metadata_only_row_is_writeable,
    test_missing_universal_metadata_column_fails_configuration,
)

passed = 0
failed = 0
for test in TESTS:
    try:
        test()
        passed += 1
        print(f"PASSED: {test.__name__}")
    except Exception as error:
        failed += 1
        print(f"FAILED: {test.__name__}: {type(error).__name__}")

print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic/mock")
print("External integrations: Not called")
print("PHI handling: Synthetic values only")

if failed:
    raise SystemExit(1)
