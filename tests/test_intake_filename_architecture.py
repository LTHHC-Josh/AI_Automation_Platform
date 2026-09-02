from pathlib import Path
import tempfile

from src.models.document import AuthorizationServiceLine, Document
from src.services.filename_policy_service import FilenamePolicyRequest, FilenamePolicyService
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.intake_document_naming_service import IntakeDocumentNamingVocabulary
from src.services.production_filename_assembly_service import ProductionFilenameAssemblyService
from src.services.reference_table_service import (
    LookupResult,
    PayorReferenceTable,
    ReferenceTables,
    ServiceReferenceTable,
)
from src.services.review_decision_service import ReviewDecisionService
from src.services.review_output_service import ReviewOutputService
from src.services.review_reason_summary_service import ReviewReasonSummaryService
from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService


def evidence(value, confidence=0.95, source=None):
    return {
        "value": value,
        "confidence": confidence,
        "source_text": source if source is not None else f"Supported {value}",
    }


def tables(*, payer=True, service=True):
    return ReferenceTables(
        PayorReferenceTable(
            {("SYNTHETIC PLAN", ""): "PLAN"} if payer else {}
        ),
        ServiceReferenceTable(
            {("T0000", "", ""): {"SERVICE"}} if service else {}
        ),
    )


def authorization(*, subtype="NO CHANGE", date="2026-09-01"):
    subject = Document(
        file_path=Path("synthetic.pdf"),
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_reason="Synthetic supported classification",
        confidence=0.90,
        classification_support_status="supported",
        subtype_support_status="supported",
    )
    subject.field_evidence = {
        "person_last": evidence("EXAMPLE"),
        "person_first": evidence("SYNTHETIC"),
        "payer": evidence("SYNTHETIC PLAN"),
        "start_date": evidence(date) if date else evidence(None, None, ""),
        "intake_document_subtype": evidence(subtype) if subtype else evidence(None, None, ""),
    }
    subject.extracted_data = {
        key: item["value"] for key, item in subject.field_evidence.items()
    }
    subject.field_confidences = {
        key: item["confidence"] for key, item in subject.field_evidence.items()
        if item["value"] is not None
    }
    IntakeDocumentNamingVocabulary.apply(subject)
    return subject


def assemble(subject, *, reference_tables=None, extension=".pdf"):
    return ProductionFilenameAssemblyService(
        tables_provider=lambda: reference_tables if reference_tables is not None else tables()
    ).evaluate(document=subject, source_extension=extension)


def test_complete_intake_filename_uses_exact_pattern_and_optional_omission():
    subject = authorization()
    subject.service_lines = [AuthorizationServiceLine(
        service_code="T0000", start_date="2026-09-01", end_date="2026-09-30",
        confidence=0.95,
    )]
    result = assemble(subject)
    assert result.policy_result.filename == (
        "EXAMPLE, SYNTHETIC_PLAN_SERVICE_AUTH NO CHANGE_090126-093026.PDF"
    )
    assert result.policy_result.filename_result == "complete_business"
    assert result.policy_result.placeholder_categories == ()


def test_unknown_auth_subtype_uses_one_fixed_placeholder():
    subject = authorization(subtype=None)
    result = assemble(subject)
    assert "AUTH [SUBTYPE]" in result.policy_result.filename
    assert result.policy_result.filename_result == "partial_business"
    assert result.policy_result.placeholder_categories == ("document_subtype",)


def test_init_requires_authoritative_external_context():
    subject = authorization(subtype="INITIAL")
    unresolved = IntakeDocumentNamingVocabulary.resolve(subject)
    resolved = IntakeDocumentNamingVocabulary.resolve(
        subject,
        authoritative_subtype=LookupResult(True, "INIT", "resolved"),
    )
    assert unresolved.document_type_segment == "AUTH [SUBTYPE]"
    assert unresolved.subtype_source_category == "external_context_required"
    assert resolved.document_type_segment == "AUTH INIT"
    assert resolved.subtype_source_category == "authoritative_context"


def test_intake_subtype_validation_canonicalizes_supported_evidence_and_blocks_init():
    supported = authorization(subtype="INBOUND AUTH")
    EvidenceValidationService().validate(supported)
    IntakeDocumentNamingVocabulary.apply(supported)
    assert supported.field_evidence["intake_document_subtype"]["value"] == "inbound"
    assert IntakeDocumentNamingVocabulary.resolve(
        supported
    ).document_type_segment == "AUTH INBOUND"

    external_only = authorization(subtype="INIT")
    EvidenceValidationService().validate(external_only)
    IntakeDocumentNamingVocabulary.apply(external_only)
    assert external_only.field_evidence["intake_document_subtype"]["value"] is None
    assert IntakeDocumentNamingVocabulary.resolve(
        external_only
    ).document_type_segment == "AUTH [SUBTYPE]"


def test_inbound_auth_alias_normalizes_without_other_legacy_guesses():
    subject = authorization(subtype="INBOUND AUTH")
    inbound = IntakeDocumentNamingVocabulary.resolve(subject)
    subject = authorization(subtype="RENEW AUTH")
    renewal = IntakeDocumentNamingVocabulary.resolve(subject)
    assert inbound.document_type_segment == "AUTH INBOUND"
    assert renewal.document_type_segment == "AUTH [SUBTYPE]"


def test_canonical_authorization_filename_vocabulary_is_complete_and_exact():
    expected = {
        "init": "INIT",
        "no_change": "NO CHANGE",
        "increase": "INCREASE",
        "decrease": "DECREASE",
        "term": "TERM",
        "stub": "STUB",
        "inbound": "INBOUND",
        "gap_fill": "GAP FILL",
        "new_services": "NEW SVS",
        "modification_change": "MOD CHANGE",
        "rpm": "RPM",
        "readmit": "READMIT",
        "tasks_added": "TASKS ADDED",
        "resume_services": "RESUME SVS",
    }
    assert {
        definition.key: definition.token
        for definition in IntakeDocumentNamingVocabulary.AUTHORIZATION_SUBTYPES
    } == expected


def test_canonical_top_level_filename_vocabulary_is_complete_and_exact():
    assert IntakeDocumentNamingVocabulary.TOP_LEVEL_TOKENS == {
        "authorization": "AUTH",
        "2067": "2067",
        "plan_of_care": "POC",
        "verification_of_employment": "VOE",
        "referral": "REFERRAL",
        "assessment": "ASSESSMENT",
        "approval_letter": "APPROVAL LETTER",
        "adverse_determination_letter": "ADVERSE DETERMINATION LETTER",
        "acknowledgment": "ACK",
        "3052": "3052",
        "provider_news": "PROVIDER NEWS",
        "clinical_practice_guidelines": "CLINICAL PRACTICE GUIDELINES",
        "bad_fax": "BAD FAX",
        "spam": "SPAM",
    }


def test_supported_authorization_termination_uses_auth_term_without_merging_other_termination():
    authorization_term = authorization()
    authorization_term.document_category = "termination"
    authorization_term.document_subtype = "authorization_termination"
    authorization_term.subtype_support_status = "supported"
    service_term = authorization()
    service_term.document_category = "termination"
    service_term.document_subtype = "service_termination"
    service_term.subtype_support_status = "supported"
    assert IntakeDocumentNamingVocabulary.resolve(
        authorization_term
    ).document_type_segment == "AUTH TERM"
    assert IntakeDocumentNamingVocabulary.resolve(
        service_term
    ).document_type_segment == "[DOCUMENT TYPE]"


def test_payer_service_and_date_placeholders_are_partial_not_technical():
    subject = authorization(date=None)
    subject.field_evidence["payer"] = evidence("UNMAPPED")
    subject.extracted_data["payer"] = "UNMAPPED"
    subject.service_lines = [AuthorizationServiceLine(
        service_code="T9999", confidence=0.95,
        candidate_evidence={"service_code": "T9999", "confidence": 0.95},
    )]
    result = assemble(subject, reference_tables=tables(payer=False, service=False))
    assert "_[PAYER]_[SERVICE]_" in result.policy_result.filename
    assert result.policy_result.filename.endswith("_[DATE].PDF")
    assert result.policy_result.filename_result == "partial_business"
    assert result.policy_result.placeholder_categories == ("payer", "service", "date")
    assert result.required_component_failure_count == 0


def test_unknown_top_level_uses_document_type_placeholder():
    subject = authorization()
    subject.document_category = "unknown"
    subject.classification_support_status = "unknown"
    result = assemble(subject)
    assert "_[DOCUMENT TYPE]_" in result.policy_result.filename
    assert result.policy_result.placeholder_categories == ("document_type",)


def test_optional_middle_end_and_nonapplicable_service_are_omitted():
    result = assemble(authorization())
    assert result.policy_result.filename == (
        "EXAMPLE, SYNTHETIC_PLAN_AUTH NO CHANGE_090126.PDF"
    )
    assert "[SERVICE]" not in result.policy_result.filename
    assert result.policy_result.optional_omission_count == 3


def test_only_core_identity_failures_use_technical_fallback():
    missing_person = authorization()
    missing_person.field_evidence["person_first"]["value"] = None
    missing_person.extracted_data["person_first"] = None
    person_result = assemble(missing_person)
    extension_result = assemble(authorization(), extension=".doc")
    assert person_result.policy_result.filename_result == "technical_fallback"
    assert person_result.status == "person_name_unresolved"
    assert extension_result.policy_result.filename_result == "technical_fallback"
    assert extension_result.status == "source_extension_unsupported"


def test_technical_fallback_reasons_are_fixed_operator_categories():
    missing_person = authorization()
    missing_person.field_evidence["person_first"]["value"] = None
    missing_person.extracted_data["person_first"] = None
    missing_person.filename_assembly_result = assemble(missing_person)
    missing_person_reason = ReviewReasonSummaryService().summarize(
        ReviewDecisionService().evaluate(missing_person).reasons
    )
    unsupported_extension = authorization()
    unsupported_extension.filename_assembly_result = assemble(
        unsupported_extension,
        extension=".doc",
    )
    extension_reason = ReviewReasonSummaryService().summarize(
        ReviewDecisionService().evaluate(unsupported_extension).reasons
    )
    assert "Filename Person Components: Unknown" in missing_person_reason
    assert "Attachment File Type: Unsupported for business naming" in extension_reason


def test_placeholder_subtype_review_is_exact_and_smartsheet_uses_intake_value():
    subject = authorization(subtype=None)
    subject.filename_assembly_result = assemble(subject)
    decision = ReviewDecisionService().evaluate(subject)
    subject.needs_human_review = decision.needs_human_review
    subject.review_status = decision.review_status
    subject.review_reasons = decision.reasons
    output = ReviewOutputService().build(subject)
    mapping = SmartsheetReviewRowMappingService()
    mapped = mapping.map(
        review_output=output,
        policies=[],
        run_type="Synthetic intake filename architecture",
    )
    assert decision.reasons.count("Authorization subtype could not be determined.") == 1
    assert output.intake_document_subtype == "unknown"
    assert mapping.DOCUMENT_SUBTYPE_COLUMN == "AI Document Subtype"
    assert mapped.values["AI Document Subtype"] == "unknown"
    assert mapped.values["AI Review Reasons"] == "AI Document Subtype: Unknown"


def test_non_authorization_smartsheet_subtype_remains_classifier_owned():
    subject = authorization()
    subject.document_type = "2067"
    subject.document_category = "2067"
    subject.document_subtype = "utl"
    subject.subtype_support_status = "supported"
    IntakeDocumentNamingVocabulary.apply(subject)
    output = ReviewOutputService().build(subject)
    mapped = SmartsheetReviewRowMappingService().map(
        review_output=output,
        policies=[],
        run_type="Synthetic non-authorization subtype ownership",
    )
    assert output.intake_subtype_evaluated is False
    assert mapped.values["AI Document Subtype"] == "utl"


def test_result_repr_does_not_expose_the_business_filename():
    result = assemble(authorization())
    assert "EXAMPLE" not in repr(result)
    assert "SYNTHETIC" not in repr(result)


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("External integrations: not called")
    print("PHI handling: synthetic values only; filename values are not printed")
