from pathlib import Path

from src.models.document import Document
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)


def build_test_document() -> Document:
    """
    Build a synthetic document with no PHI or external dependencies.
    """

    document = Document(
        file_path=Path(
            "synthetic-test.pdf"
        )
    )

    document.field_evidence = {
        "member_id": {
            "value": "ABC12345",
            "confidence": 1.0,
            "source_text": "Member ID: ABC12345",
        },
        "authorization_number": {
            "value": "WRONG999",
            "confidence": 1.0,
            "source_text": "Reference#: AUTH123",
        },
        "request_type": {
            "value": "Initial Request",
            "confidence": 1.0,
            "source_text": "Request Type: Initial Request",
        },
        "service_code": {
            "value": "S9110",
            "confidence": 1.0,
            "source_text": "Service Code S9110 U1",
        },
        "service_codes": {
            "value": [
                "S9110",
                "S9110",
            ],
            "confidence": 1.0,
            "source_text": "Service Code S9110 U1",
        },
        "modifier": {
            "value": "U1",
            "confidence": 1.0,
            "source_text": "Service Code S9110 U1",
        },
        "approved_visits": {
            "value": 7,
            "confidence": 1.0,
            "source_text": "Number of Visits: 7",
        },
        "start_date": {
            "value": "11/25/2025",
            "confidence": 1.0,
            "source_text": "Start Date 11/25/2025",
        },
        "end_date": {
            "value": "05/23/2026",
            "confidence": 1.0,
            "source_text": "End Date 05/23/2026",
        },
        "member_dob": {
            "value": "06/08/1994",
            "confidence": 1.0,
            "source_text": "Member DOB: 06/08/1994",
        },
        "provider_npi": {
            "value": "1003213190",
            "confidence": 1.0,
            "source_text": "NPI #: 1003213190",
        },
        "diagnosis_code": {
            "value": "I10",
            "confidence": 1.0,
            "source_text": "Diagnosis: I10",
        },
    }

    return document


def main() -> None:
    print("=" * 60)
    print("Testing Deterministic Evidence Validation")
    print("=" * 60)

    document = build_test_document()
    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["member_id"]
        == "ABC12345"
    )

    assert (
        document.extracted_data["authorization_number"]
        is None
    )

    assert (
        document.field_confidences["authorization_number"]
        == 0.0
    )

    assert (
        document.extracted_data["request_type"]
        is None
    )

    assert (
        document.extracted_data["approved_visits"]
        is None
    )

    assert (
        document.extracted_data["start_date"]
        == "2025-11-25"
    )

    assert (
        document.extracted_data["end_date"]
        == "2026-05-23"
    )

    assert (
        document.extracted_data["member_dob"]
        == "1994-06-08"
    )

    assert (
        document.extracted_data["service_codes"]
        == ["S9110"]
    )

    assert (
        document.extracted_data["modifier"]
        == "U1"
    )

    assert (
        "authorization_number is not supported "
        "by its source evidence"
        in actions
    )

    assert (
        "Request type requires checkbox or "
        "selection verification"
        in actions
    )

    assert (
        "Approved visits are not supported by "
        "clear approval evidence"
        in actions
    )

    print("Passed: matching identifiers were preserved")
    print("Passed: unsupported identifiers were cleared")
    print("Passed: ambiguous request type was cleared")
    print("Passed: unsupported approved visits were cleared")
    print("Passed: dates were normalized")
    print("Passed: duplicate service codes were removed")
    print("Passed: valid modifier evidence was preserved")
    print()
    print("Validation actions:")

    for action in actions:
        print(
            f"  - {action}"
        )

    print()
    print("Real or mock: Synthetic deterministic test")
    print("Failed: 0")
    print("=" * 60)


if __name__ == "__main__":
    main()