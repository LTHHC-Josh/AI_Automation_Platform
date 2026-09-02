from pathlib import Path

from src.business_rules.rules.authorization_rule import (
    AuthorizationRenewalRule,
    AuthorizationRule,
)
from src.models.document import Document
from src.models.smartsheet_mapping import SmartsheetColumnPolicy
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.field_validation_diagnostic_service import (
    FieldValidationDiagnosticService, FinalValidationSummary,
)
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetService,
)
from src.services.review_decision_service import ReviewDecisionService
from src.services.review_output_service import ReviewOutputService
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)
from src.services.review_reason_summary_service import ReviewReasonSummaryService


def evidence(value, confidence=0.95, source=None):
    return {
        "value": value,
        "confidence": confidence,
        "source_text": source if source is not None else f"Supported {value}",
    }


def validate(document):
    document.validation_actions = EvidenceValidationService().validate(document)
    return document


def decision(document):
    document.document_type = "authorization_renewal"
    document.document_category = "authorization"
    document.document_subtype = "renewal"
    document.classification_reason = "Synthetic supported classification"
    document.confidence = 1.0
    document.rule_actions = AuthorizationRenewalRule().execute(document)
    result = ReviewDecisionService().evaluate(document)
    document.needs_human_review = result.needs_human_review
    document.review_status = result.review_status
    document.review_reasons = list(result.reasons)
    document.minimum_field_confidence = result.minimum_field_confidence
    return result


def test_accepted_service_code_and_status_are_cross_layer_consistent():
    document = Document(file_path=Path("synthetic.pdf"))
    document.field_evidence = {
        "service_codes": evidence(["T0000"], source="T0000"),
        "authorization_status": evidence("Approved", source="Approved"),
    }
    validate(document)
    document.rule_actions = []
    result = ReviewDecisionService().evaluate(document)
    output = ReviewOutputService().build(document)
    mapping = SmartsheetReviewRowMappingService().map(
        review_output=output,
        policies=[
            SmartsheetColumnPolicy(
                "service_codes", "Service Codes", confidence_column_name="Service Codes Conf."
            ),
            SmartsheetColumnPolicy("authorization_status", "Authorization Status"),
        ],
        run_type="Synthetic consistency",
    )
    assert mapping.values["Service Codes Conf."] == 0.95
    assert "Service Codes" in mapping.values
    assert "Authorization Status" in mapping.values
    assert not any("service code" in reason.lower() for reason in result.reasons)
    assert not any("authorization status" in reason.lower() for reason in result.reasons)


def test_redundant_singular_service_code_noise_cannot_contradict_accepted_plural():
    document = Document(file_path=Path("synthetic.pdf"))
    document.field_evidence = {
        "service_code": evidence("T9999", source="T9999"),
        "service_codes": evidence(["T0000"], source="T0000"),
    }
    validate(document)
    document.rule_actions = []
    result = ReviewDecisionService().evaluate(document)
    assert document.extracted_data["service_codes"] == ["T0000"]
    assert document.field_confidences["service_codes"] == 0.95
    assert result.minimum_field_confidence == 0.95
    assert not any("service code" in reason.lower() for reason in result.reasons)


def test_unsupported_high_confidence_candidate_is_blank_with_specific_review():
    document = Document(file_path=Path("synthetic.pdf"))
    document.field_evidence = {
        "service_codes": evidence(["T0000"], source="Different evidence"),
    }
    validate(document)
    document.rule_actions = []
    result = ReviewDecisionService().evaluate(document)
    output = ReviewOutputService().build(document)
    mapping = SmartsheetReviewRowMappingService().map(
        review_output=output,
        policies=[SmartsheetColumnPolicy(
            "service_codes", "Service Codes", confidence_column_name="Service Codes Conf."
        )],
        run_type="Synthetic consistency",
    )
    field = next(item for item in output.fields if item.name == "service_codes")
    assert field.value is None and field.candidate_value == ["T0000"]
    assert field.candidate_confidence == 0.95
    assert "Service Codes" not in mapping.values
    assert "Service Codes Conf." not in mapping.values
    assert any("source evidence" in reason for reason in result.reasons)


def test_optional_absence_is_blank_without_confidence_or_review():
    document = Document(file_path=Path("synthetic.pdf"), document_category="authorization")
    document.field_evidence = {
        "modifier": {"value": None, "confidence": None, "source_text": ""},
        "service_codes": evidence(["T0000"], source="T0000"),
    }
    validate(document)
    document.rule_actions = []
    result = ReviewDecisionService().evaluate(document)
    diagnostic = FieldValidationDiagnosticService().build(document, "modifier")
    assert diagnostic.field_state == "not_present"
    assert "modifier" not in document.field_confidences
    assert result.minimum_field_confidence == 0.95
    assert not any("modifier" in reason.lower() for reason in result.reasons)


def test_quantity_without_explicit_unit_defaults_to_hours_without_review():
    document = Document(file_path=Path("synthetic.pdf"))
    document.field_evidence = {
        "authorized_units": evidence(["6"], source="Authorized quantity 6"),
    }
    validate(document)
    assert document.extracted_data["authorization_unit"] == "Hours"
    assert document.field_evidence["authorization_unit"]["provenance"] == "business_default_hours"
    output = ReviewOutputService().build(document)
    mapping = SmartsheetReviewRowMappingService().map(
        review_output=output,
        policies=[SmartsheetColumnPolicy(
            "authorized_units", "Authorized Units", confidence_column_name="Authorized Units Conf."
        )],
        run_type="Synthetic consistency",
    )
    assert mapping.values["Authorized Units"] == "6 Hours"
    assert mapping.values["Authorized Units Conf."] == 0.95
    assert output.unit_source_category == "business_default_hours"
    assert "Authorization quantity requires verification" not in AuthorizationRule().execute(document)


def test_explicit_supported_unit_overrides_default_and_ambiguous_unit_fails_closed():
    explicit = Document(file_path=Path("synthetic.pdf"))
    explicit.field_evidence = {
        "authorized_units": evidence(["6"], source="Authorized quantity 6 visits"),
        "authorization_unit": evidence("Visits", source="Authorized quantity 6 visits"),
    }
    validate(explicit)
    assert explicit.extracted_data["authorization_unit"] == "Visits"
    assert explicit.field_evidence["authorization_unit"]["provenance"] == "explicit_document_evidence"
    explicit_output = ReviewOutputService().build(explicit)
    explicit_mapping = SmartsheetReviewRowMappingService().map(
        review_output=explicit_output,
        policies=[SmartsheetColumnPolicy("authorized_units", "Authorized Units")],
        run_type="Synthetic consistency",
    )
    assert explicit_mapping.values["Authorized Units"] == "6 Visits"

    ambiguous = Document(file_path=Path("synthetic.pdf"))
    ambiguous.field_evidence = {
        "authorized_units": evidence(["6"], source="Authorized quantity 6"),
        "authorization_unit": evidence(["Hours", "Visits"], source="Hours Visits"),
    }
    validate(ambiguous)
    assert ambiguous.extracted_data["authorization_unit"] is None
    assert any("ambiguous or conflicting" in action for action in ambiguous.validation_actions)

    unsupported = Document(file_path=Path("synthetic.pdf"))
    unsupported.field_evidence = {
        "authorized_units": evidence(["6"], source="Authorized quantity 6 weeks"),
        "authorization_unit": evidence("Weeks", source="Authorized quantity 6 weeks"),
    }
    validate(unsupported)
    assert unsupported.extracted_data["authorization_unit"] is None
    assert any("not supported" in action for action in unsupported.validation_actions)


def test_renewal_workflow_is_deterministic_and_not_a_review_reason():
    document = Document(file_path=Path("synthetic.pdf"))
    document.extracted_data = {
        "patient_name": "Synthetic",
        "authorization_number": "A",
        "payer": "P",
        "member_id": "M",
        "authorization_status": "Approved",
        "start_date": "2026-01-01",
        "end_date": "2026-02-01",
        "authorized_units": ["6"],
        "authorization_unit": "Hours",
    }
    document.field_evidence = {
        "authorization_unit": {
            "value": "Hours", "confidence": 0.95, "source_text": "",
            "provenance": "business_default_hours",
        }
    }
    actions = AuthorizationRenewalRule().execute(document)
    assert "Authorization subtype requires verification" not in actions
    assert "Authorization quantity requires verification" not in actions


def test_safe_validation_summary_uses_final_states_only():
    document = Document(file_path=Path("synthetic.pdf"), document_category="authorization")
    document.field_evidence = {
        "authorization_status": evidence("Approved", source="Approved"),
        "modifier": {"value": None, "confidence": None, "source_text": ""},
        "authorized_units": evidence(["6"], source="Authorized quantity 6"),
    }
    validate(document)
    summary = FieldValidationDiagnosticService().summarize(document)
    assert summary.accepted_field_count >= 2
    assert summary.optional_absent_field_count >= 1
    assert summary.low_confidence_count == 0
    assert summary.quantity_present is True
    assert summary.unit_source_category == "business_default_hours"


def test_review_summary_is_specific_deduplicated_and_drops_generic_noise():
    summary = ReviewReasonSummaryService().summarize([
        "Missing authorization status",
        "Missing authorization status",
        "A processing detail requires verification",
    ])
    assert summary == "Required authorization status was not found"
    low = ReviewReasonSummaryService().summarize([
        "Service codes confidence is below the acceptance threshold"
    ])
    assert low == "Service code confidence is below the required threshold"


def test_required_missing_is_specific_while_optional_missing_is_silent():
    document = Document(
        file_path=Path("synthetic.pdf"),
        document_category="authorization",
    )
    document.field_evidence = {
        "authorization_status": {"value": None, "confidence": None, "source_text": ""},
        "modifier": {"value": None, "confidence": None, "source_text": ""},
    }
    validate(document)
    document.extracted_data.update({
        "patient_name": "Synthetic", "authorization_number": "A",
        "payer": "P", "member_id": "M", "start_date": "2026-01-01",
        "end_date": "2026-02-01", "authorized_units": ["6"],
        "authorization_unit": "Hours",
    })
    document.field_evidence["authorization_unit"] = {
        "value": "Hours", "confidence": 0.95, "source_text": "",
        "provenance": "business_default_hours",
    }
    actions = AuthorizationRule().execute(document)
    assert "Missing authorization status" in actions
    summary = ReviewReasonSummaryService().summarize(actions)
    assert "Required authorization status was not found" in summary
    assert "Modifier" not in summary


def test_workflow_validation_summary_aggregates_only_safe_counts_and_categories():
    summary = MailboxCompleteReviewSmartsheetService._aggregate_validation_summaries([
        FinalValidationSummary(
            accepted_field_count=3,
            optional_absent_field_count=2,
            quantity_present=True,
            unit_source_category="business_default_hours",
        ),
        FinalValidationSummary(
            missing_required_count=1,
            unsupported_count=1,
            unit_source_category="business_default_hours",
        ),
    ])
    assert summary.accepted_field_count == 3
    assert summary.optional_absent_field_count == 2
    assert summary.missing_required_count == 1
    assert summary.unsupported_count == 1
    assert summary.quantity_present is True
    assert summary.unit_source_category == "business_default_hours"


def test_optional_authorization_end_date_is_blank_and_silent_across_layers():
    document = Document(
        file_path=Path("synthetic.pdf"),
        document_type="authorization",
        document_category="authorization",
        document_subtype="initial",
    )
    document.field_evidence = {
        "end_date": {"value": None, "confidence": None, "source_text": ""},
    }
    validate(document)
    document.extracted_data.update({
        "patient_name": "Synthetic", "authorization_number": "A",
        "payer": "P", "member_id": "M", "authorization_status": "Approved",
        "start_date": "2026-01-01", "authorized_units": ["6"],
    })
    document.rule_actions = AuthorizationRule().execute(document)
    assert "Missing authorization end date" not in document.rule_actions
    assert FieldValidationDiagnosticService().build(
        document, "end_date"
    ).field_state == "not_present"
    result = ReviewDecisionService().evaluate(document)
    document.needs_human_review = result.needs_human_review
    document.review_status = result.review_status
    document.review_reasons = result.reasons
    output = ReviewOutputService().build(document)
    mapping = SmartsheetReviewRowMappingService().map(
        review_output=output,
        policies=[SmartsheetColumnPolicy(
            "end_date", "End Date", confidence_column_name="End Date Conf.",
            confidence_column_supports_text=True,
        )],
        run_type="Synthetic optional end date",
    )
    assert "End Date" not in mapping.values
    assert "End Date Conf." not in mapping.values
    assert "Missing/Not extracted" not in mapping.values.values()
    assert not any("end date" in reason.lower() for reason in result.reasons)


def test_authorization_unknown_subtype_recommends_one_specific_review_reason():
    document = Document(
        file_path=Path("synthetic.pdf"),
        document_type="authorization",
        document_category="authorization",
        document_subtype="unknown",
        classification_reason="Synthetic supported authorization category",
        confidence=1.0,
        classification_support_status="supported",
        subtype_support_status="missing",
    )
    document.extracted_data = {"authorization_status": "Approved"}
    document.field_confidences = {"authorization_status": 0.95}
    document.rule_actions = ["Authorization validated successfully"]
    result = ReviewDecisionService().evaluate(document)
    assert result.classification_confidence == 1.0
    assert result.needs_human_review is True
    assert result.review_status == "Human Review Recommended"
    assert result.reasons == ["Authorization subtype could not be determined."]
    assert ReviewReasonSummaryService().summarize(result.reasons) == (
        "AI Document Subtype: Unknown"
    )


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic values only; external systems not called")
