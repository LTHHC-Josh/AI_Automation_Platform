from pathlib import Path
from typing import Callable

from src.models.document import Document
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)


def build_document(
    field_evidence: dict,
) -> Document:
    """
    Build a synthetic document containing no PHI.
    """

    document = Document(
        file_path=Path(
            "synthetic-evidence-test.pdf"
        )
    )

    document.field_evidence = field_evidence

    return document


def test_missing_source_text_clears_protected_field() -> None:
    document = build_document(
        {
            "authorization_number": {
                "value": "AUTH123",
                "confidence": 1.0,
                "source_text": "",
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.field_evidence[
            "authorization_number"
        ]["value"]
        is None
    )

    assert (
        document.field_evidence[
            "authorization_number"
        ]["confidence"]
        == 0.0
    )

    assert (
        document.extracted_data[
            "authorization_number"
        ]
        is None
    )

    assert (
        document.field_confidences[
            "authorization_number"
        ]
        == 0.0
    )

    assert (
        "authorization_number has no source evidence"
        in actions
    )


def test_supported_identifier_is_preserved() -> None:
    document = build_document(
        {
            "member_id": {
                "value": "ABC-12345",
                "confidence": 0.96,
                "source_text": "Health Plan ID: ABC12345",
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["member_id"]
        == "ABC-12345"
    )

    assert (
        document.field_confidences["member_id"]
        == 0.96
    )

    assert actions == []


def test_unsupported_identifier_is_cleared() -> None:
    source_text = "Reference Number: AUTH123"

    document = build_document(
        {
            "authorization_number": {
                "value": "WRONG999",
                "confidence": 1.0,
                "source_text": source_text,
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data[
            "authorization_number"
        ]
        is None
    )

    assert (
        document.field_confidences[
            "authorization_number"
        ]
        == 0.0
    )

    assert (
        document.field_evidence[
            "authorization_number"
        ]["source_text"]
        == source_text
    )

    assert (
        "authorization_number is not supported "
        "by its source evidence"
        in actions
    )


def test_supported_date_is_normalized() -> None:
    document = build_document(
        {
            "start_date": {
                "value": "11/25/2025",
                "confidence": 0.97,
                "source_text": "Start Date: 11/25/2025",
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["start_date"]
        == "2025-11-25"
    )

    assert (
        document.field_confidences["start_date"]
        == 0.97
    )

    assert actions == []


def test_unsupported_date_evidence_is_cleared() -> None:
    source_text = "Start Date: 11/26/2025"

    document = build_document(
        {
            "start_date": {
                "value": "11/25/2025",
                "confidence": 1.0,
                "source_text": source_text,
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["start_date"]
        is None
    )

    assert (
        document.field_confidences["start_date"]
        == 0.0
    )

    assert (
        document.field_evidence[
            "start_date"
        ]["source_text"]
        == source_text
    )

    assert (
        "start_date is not supported "
        "by its source evidence"
        in actions
    )


def test_duplicate_service_codes_are_removed() -> None:
    document = build_document(
        {
            "service_codes": {
                "value": [
                    "S9110",
                    "S9110",
                    " S9110 ",
                ],
                "confidence": 0.95,
                "source_text": (
                    "Approved service code S9110"
                ),
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["service_codes"]
        == ["S9110"]
    )

    assert (
        document.field_confidences["service_codes"]
        == 0.95
    )

    assert actions == []


def test_service_code_conflict_downgrades_confidence() -> None:
    document = build_document(
        {
            "service_code": {
                "value": "S9110",
                "confidence": 1.0,
                "source_text": "Service Code: S9110",
            },
            "service_codes": {
                "value": [
                    "S9123",
                ],
                "confidence": 1.0,
                "source_text": "Service Code: S9123",
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["service_code"]
        == "S9110"
    )

    assert (
        document.extracted_data["service_codes"]
        == ["S9123"]
    )

    assert (
        document.field_confidences["service_code"]
        == 0.50
    )

    assert (
        "Service code fields conflict"
        in actions
    )


def test_invalid_modifier_structure_is_cleared() -> None:
    source_text = "Modifier: U11"

    document = build_document(
        {
            "modifier": {
                "value": "U11",
                "confidence": 1.0,
                "source_text": source_text,
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["modifier"]
        is None
    )

    assert (
        document.field_confidences["modifier"]
        == 0.0
    )

    assert (
        document.field_evidence[
            "modifier"
        ]["source_text"]
        == source_text
    )

    assert (
        "Modifier evidence is structurally invalid"
        in actions
    )


def test_selected_request_type_is_preserved() -> None:
    document = build_document(
        {
            "request_type": {
                "value": "Initial Request",
                "confidence": 0.92,
                "source_text": (
                    "Request Type: [x] Initial Request"
                ),
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["request_type"]
        == "Initial Request"
    )

    assert (
        document.field_confidences["request_type"]
        == 0.92
    )

    assert actions == []


def test_ambiguous_request_type_is_cleared() -> None:
    source_text = "Request Type: Initial Request"

    document = build_document(
        {
            "request_type": {
                "value": "Initial Request",
                "confidence": 1.0,
                "source_text": source_text,
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["request_type"]
        is None
    )

    assert (
        document.field_confidences["request_type"]
        == 0.0
    )

    assert (
        document.field_evidence[
            "request_type"
        ]["source_text"]
        == source_text
    )

    assert (
        "Request type requires checkbox "
        "or selection verification"
        in actions
    )


def test_requested_visits_are_not_approved_visits() -> None:
    source_text = "Number of Visits: 7"

    document = build_document(
        {
            "approved_visits": {
                "value": 7,
                "confidence": 1.0,
                "source_text": source_text,
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["approved_visits"]
        is None
    )

    assert (
        document.field_confidences["approved_visits"]
        == 0.0
    )

    assert (
        document.field_evidence[
            "approved_visits"
        ]["source_text"]
        == source_text
    )

    assert (
        "Approved visits are not supported "
        "by clear approval evidence"
        in actions
    )


def test_clear_approval_context_preserves_visits() -> None:
    document = build_document(
        {
            "approved_visits": {
                "value": 7,
                "confidence": 0.90,
                "source_text": (
                    "Approved Visits: 7"
                ),
            },
        }
    )

    service = EvidenceValidationService()

    actions = service.validate(
        document
    )

    assert (
        document.extracted_data["approved_visits"]
        == 7
    )

    assert (
        document.field_confidences["approved_visits"]
        == 0.90
    )

    assert actions == []


def test_flat_fields_are_synchronized() -> None:
    document = build_document(
        {
            "provider_npi": {
                "value": "1234567890",
                "confidence": 95,
                "source_text": (
                    "Provider NPI: 1234567890"
                ),
            },
            "diagnosis_code": {
                "value": "I10",
                "confidence": 88,
                "source_text": (
                    "Diagnosis Code: I10"
                ),
            },
        }
    )

    service = EvidenceValidationService()

    service.validate(
        document
    )

    assert document.extracted_data == {
        "provider_npi": "1234567890",
        "diagnosis_code": "I10",
    }

    assert document.field_confidences == {
        "provider_npi": 0.95,
        "diagnosis_code": 0.88,
    }


def test_validation_actions_are_deduplicated() -> None:
    service = EvidenceValidationService()

    actions = service._remove_duplicates(
        [
            "Evidence requires verification",
            "Evidence requires verification",
            "Another validation action",
        ]
    )

    assert actions == [
        "Evidence requires verification",
        "Another validation action",
    ]


def run_test(
    test_name: str,
    test_function: Callable[[], None],
) -> bool:
    """
    Run one synthetic test and print its result.
    """

    try:
        test_function()
    except AssertionError:
        print(
            f"FAILED: {test_name}"
        )
        return False

    print(
        f"PASSED: {test_name}"
    )

    return True


def main() -> None:
    print("=" * 60)
    print("Testing Evidence Validation Service")
    print("=" * 60)

    tests: list[
        tuple[
            str,
            Callable[[], None],
        ]
    ] = [
        (
            "missing source text clears protected field",
            test_missing_source_text_clears_protected_field,
        ),
        (
            "supported identifier is preserved",
            test_supported_identifier_is_preserved,
        ),
        (
            "unsupported identifier is cleared",
            test_unsupported_identifier_is_cleared,
        ),
        (
            "supported date is normalized",
            test_supported_date_is_normalized,
        ),
        (
            "unsupported date evidence is cleared",
            test_unsupported_date_evidence_is_cleared,
        ),
        (
            "duplicate service codes are removed",
            test_duplicate_service_codes_are_removed,
        ),
        (
            "service-code conflict downgrades confidence",
            test_service_code_conflict_downgrades_confidence,
        ),
        (
            "invalid modifier structure is cleared",
            test_invalid_modifier_structure_is_cleared,
        ),
        (
            "selected request type is preserved",
            test_selected_request_type_is_preserved,
        ),
        (
            "ambiguous request type is cleared",
            test_ambiguous_request_type_is_cleared,
        ),
        (
            "requested visits are not approved visits",
            test_requested_visits_are_not_approved_visits,
        ),
        (
            "clear approval context preserves visits",
            test_clear_approval_context_preserves_visits,
        ),
        (
            "flat fields are synchronized",
            test_flat_fields_are_synchronized,
        ),
        (
            "validation actions are deduplicated",
            test_validation_actions_are_deduplicated,
        ),
    ]

    passed = 0
    failed = 0

    for test_name, test_function in tests:
        if run_test(
            test_name,
            test_function,
        ):
            passed += 1
        else:
            failed += 1

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
    print("=" * 60)

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()