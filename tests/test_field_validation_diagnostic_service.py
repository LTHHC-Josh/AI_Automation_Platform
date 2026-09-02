from pathlib import Path

from src.models.document import AuthorizationServiceLine, Document
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.field_validation_diagnostic_service import FieldValidationDiagnosticService
from src.services.review_output_service import ReviewOutputService
from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService
from src.models.smartsheet_mapping import SmartsheetColumnPolicy


def candidate(*, value="SYNTHETIC", confidence=0.95, source="Supported SYNTHETIC"):
    document = Document(file_path=Path("synthetic.pdf"), document_type="authorization")
    document.field_evidence = {
        "authorization_status": {
            "value": value,
            "confidence": confidence,
            "source_text": source,
        }
    }
    return document


def test_exact_threshold_is_inclusive_and_below_threshold_fails():
    exact = candidate(confidence=0.95)
    below = candidate(confidence=0.949)
    service = FieldValidationDiagnosticService(threshold=0.95)
    assert service.build(exact, "authorization_status").threshold_passed is True
    assert service.build(below, "authorization_status").threshold_passed is False


def test_unsupported_high_confidence_candidate_becomes_validated_null_and_is_preserved_for_review():
    document = candidate(value="SYNTHETIC", confidence=0.95, source="Different evidence")
    document.validation_actions = EvidenceValidationService().validate(document)
    diagnostic = FieldValidationDiagnosticService(threshold=0.95).build(
        document, "authorization_status"
    )
    review_field = ReviewOutputService().build(document).fields[0]
    assert document.extracted_data["authorization_status"] is None
    assert "authorization_status" not in document.field_confidences
    assert document.field_evidence["authorization_status"]["candidate_confidence"] == 0.95
    assert review_field.value is None
    assert review_field.candidate_value == "SYNTHETIC"
    assert review_field.candidate_confidence == 0.95
    assert diagnostic.candidate_confidence == 0.95
    assert diagnostic.threshold_passed is True
    assert diagnostic.source_support_proven is False
    assert diagnostic.validated_value_present is False
    assert diagnostic.validation_passed is False
    assert diagnostic.review_triggered is True
    assert diagnostic.reason_code == "authorization_status_unclear_source_support"


def test_supported_high_confidence_candidate_maps_as_validated_value():
    document = candidate(confidence=0.95)
    document.validation_actions = EvidenceValidationService().validate(document)
    diagnostic = FieldValidationDiagnosticService(threshold=0.95).build(
        document, "authorization_status"
    )
    assert diagnostic.source_support_proven is True
    assert diagnostic.validated_value_present is True
    assert diagnostic.review_triggered is False


def test_unsupported_candidate_does_not_reach_production_value_or_confidence_columns():
    document = candidate(value="SYNTHETIC", confidence=0.95, source="Different evidence")
    document.validation_actions = EvidenceValidationService().validate(document)
    document.needs_human_review = True
    document.review_status = "Human Review Recommended"
    document.review_reasons = list(document.validation_actions)
    mapping = SmartsheetReviewRowMappingService().map(
        review_output=ReviewOutputService().build(document),
        policies=[SmartsheetColumnPolicy(
            source_field="authorization_status",
            column_name="Authorization Status",
            confidence_column_name="Authorization Status Confidence",
        )],
        run_type="Synthetic validated mapping",
    )
    assert "Authorization Status" not in mapping.values
    assert "Authorization Status Confidence" not in mapping.values
    assert mapping.values["AI Review Required"] is True
    assert "Authorization status could not be verified" in mapping.values["AI Review Reasons"]


def test_classification_confidence_cannot_replace_missing_field_confidence():
    document = candidate(confidence=0.0)
    document.confidence = 1.0
    document.validation_actions = EvidenceValidationService().validate(document)
    diagnostic = FieldValidationDiagnosticService().build(document, "authorization_status")
    assert diagnostic.candidate_confidence == 0.0
    assert diagnostic.threshold_passed is False


def test_service_line_candidate_is_preserved_when_modifier_support_fails():
    document = Document(file_path=Path("synthetic.pdf"))
    document.service_lines = [AuthorizationServiceLine(
        service_code="T0000",
        modifier="U1",
        confidence=0.95,
        source_text="T0000",
    )]
    document.validation_actions = EvidenceValidationService().validate(document)
    diagnostic = FieldValidationDiagnosticService(threshold=0.95).build_service_line(
        document, 0, "modifier"
    )
    line = document.service_lines[0]
    assert line.modifier is None
    assert line.candidate_evidence["modifier"] == "U1"
    assert line.candidate_evidence["confidence"] == 0.95
    assert diagnostic.threshold_passed is True
    assert diagnostic.source_support_proven is False
    assert diagnostic.validated_value_present is False
    assert diagnostic.reason_code == "service_line_modifier_unclear_source_support"


def test_classification_resolution_does_not_invent_full_confidence():
    from src.services.document_classification_resolution_service import (
        DocumentClassificationResolutionService,
    )

    resolved = DocumentClassificationResolutionService().resolve(
        {
            "document_category": "authorization",
            "document_subtype": "initial",
            "confidence": None,
        },
        (),
    )
    assert resolved["confidence"] is None
    assert resolved["family_evidence_confidence"] is None


def test_optional_absence_is_not_present_without_zero_confidence_or_review():
    document = Document(file_path=Path("synthetic.pdf"), document_category="authorization")
    document.field_evidence = {
        "modifier": {"value": None, "confidence": None, "source_text": ""}
    }
    document.validation_actions = EvidenceValidationService().validate(document)
    diagnostic = FieldValidationDiagnosticService().build(document, "modifier")
    assert diagnostic.field_state == "not_present"
    assert diagnostic.required is False
    assert diagnostic.candidate_confidence is None
    assert diagnostic.review_triggered is False
    assert "modifier" not in document.field_confidences


def test_required_absence_is_distinguished_from_optional_absence():
    document = Document(file_path=Path("synthetic.pdf"), document_category="authorization")
    document.field_evidence = {
        "authorization_status": {"value": None, "confidence": None, "source_text": ""}
    }
    diagnostic = FieldValidationDiagnosticService().build(
        document, "authorization_status")
    assert diagnostic.field_state == "missing_required"
    assert diagnostic.required is True


def test_authorization_end_date_absence_is_optional_not_present():
    document = Document(
        file_path=Path("synthetic.pdf"), document_category="authorization"
    )
    document.field_evidence = {
        "end_date": {"value": None, "confidence": None, "source_text": ""}
    }
    diagnostic = FieldValidationDiagnosticService().build(document, "end_date")
    assert diagnostic.field_state == "not_present"
    assert diagnostic.required is False
    assert diagnostic.review_triggered is False


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic markers only; actual values are not printed")
