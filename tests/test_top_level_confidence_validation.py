from pathlib import Path
from typing import Callable

from src.models.document import Document
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)


def build_document(
    field_evidence: dict,
) -> Document:
    document = Document(
        file_path=Path(
            "synthetic-confidence-test.pdf"
        )
    )

    document.field_evidence = field_evidence

    return document


def test_full_model_confidence_is_capped() -> None:
    document = build_document(
        {
            "authorization_number": {
                "value": "AUTH123",
                "confidence": 1.0,
                "source_text": "Authorization Number: AUTH123",
            },
        }
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert (
        document.extracted_data["authorization_number"]
        == "AUTH123"
    )
    assert (
        document.field_confidences["authorization_number"]
        == 0.95
    )
    assert actions == []


def test_percentage_model_confidence_is_capped() -> None:
    document = build_document(
        {
            "service_code": {
                "value": "SYNTH1",
                "confidence": 100,
                "source_text": "Service Code: SYNTH1",
            },
        }
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.extracted_data["service_code"] == "SYNTH1"
    assert document.field_confidences["service_code"] == 0.95
    assert actions == []


def test_lower_confidence_is_preserved() -> None:
    document = build_document(
        {
            "member_id": {
                "value": "ABC123",
                "confidence": 0.91,
                "source_text": "Member ID: ABC123",
            },
        }
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.field_confidences["member_id"] == 0.91
    assert actions == []


def test_empty_value_has_no_validated_confidence() -> None:
    document = build_document(
        {
            "approved_visits": {
                "value": None,
                "confidence": 1.0,
                "source_text": "",
            },
        }
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.extracted_data["approved_visits"] is None
    assert "approved_visits" not in document.field_confidences
    assert document.field_evidence["approved_visits"]["confidence"] is None
    assert actions == []


def test_unsupported_value_is_still_invalidated() -> None:
    document = build_document(
        {
            "authorization_number": {
                "value": "WRONG999",
                "confidence": 1.0,
                "source_text": "Authorization Number: AUTH123",
            },
        }
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.extracted_data["authorization_number"] is None
    assert "authorization_number" not in document.field_confidences

    assert (
        "authorization_number is not supported "
        "by its source evidence"
        in actions
    )


def test_conflict_can_downgrade_below_cap() -> None:
    document = build_document(
        {
            "service_code": {
                "value": "SYNTH1",
                "confidence": 1.0,
                "source_text": "Service Code: SYNTH1",
            },
            "service_codes": {
                "value": ["SYNTH2"],
                "confidence": 1.0,
                "source_text": "Service Code: SYNTH2",
            },
        }
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.field_confidences["service_code"] == 0.50
    assert document.field_confidences["service_codes"] == 0.95
    assert "Service code fields conflict" in actions


def run_test(
    test_name: str,
    test_function: Callable[[], None],
) -> None:
    try:
        test_function()
    except AssertionError:
        print(
            f"FAILED: {test_name}"
        )
        raise

    print(
        f"PASSED: {test_name}"
    )


def main() -> None:
    print("=" * 60)
    print("Testing Top-Level Confidence Validation")
    print("=" * 60)

    tests = [
        (
            "full model confidence is capped",
            test_full_model_confidence_is_capped,
        ),
        (
            "percentage model confidence is capped",
            test_percentage_model_confidence_is_capped,
        ),
        (
            "lower confidence is preserved",
            test_lower_confidence_is_preserved,
        ),
        (
            "empty value has no validated confidence",
            test_empty_value_has_no_validated_confidence,
        ),
        (
            "unsupported value is still invalidated",
            test_unsupported_value_is_still_invalidated,
        ),
        (
            "conflict can downgrade below cap",
            test_conflict_can_downgrade_below_cap,
        ),
    ]

    passed = 0
    failed = 0

    for test_name, test_function in tests:
        try:
            run_test(
                test_name,
                test_function,
            )
            passed += 1
        except AssertionError:
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
