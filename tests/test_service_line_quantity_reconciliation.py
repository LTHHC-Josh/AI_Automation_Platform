from pathlib import Path
from typing import Callable

from src.models.document import (
    AuthorizationServiceLine,
    Document,
)
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)


RECONCILIATION_ACTION = (
    "Authorized units were reconciled from "
    "supported service-line evidence"
)


def build_document(
    authorized_units,
    service_lines,
    include_authorized_units: bool = True,
) -> Document:
    document = Document(
        file_path=Path(
            "synthetic-reconciliation.pdf"
        )
    )

    if include_authorized_units:
        document.field_evidence = {
            "authorized_units": {
                "value": authorized_units,
                "confidence": 0.95,
                "source_text": "Authorized quantity 6",
            },
        }
    else:
        document.field_evidence = {}

    document.service_lines = service_lines

    return document


def build_line(
    quantity,
    confidence=0.95,
) -> AuthorizationServiceLine:
    return AuthorizationServiceLine(
        service_code="SYNTH1",
        quantity=quantity,
        confidence=confidence,
        source_text=(
            f"SYNTH1 quantity {quantity}"
        ),
    )


def test_incomplete_flat_quantity_is_reconciled() -> None:
    document = build_document(
        authorized_units=[6],
        service_lines=[
            build_line(
                6,
                0.50,
            ),
            build_line(
                1,
                0.95,
            ),
        ],
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert {
        str(value)
        for value in document.extracted_data[
            "authorized_units"
        ]
    } == {
        "1",
        "6",
    }

    assert (
        document.field_confidences[
            "authorized_units"
        ]
        == 0.50
    )

    assert RECONCILIATION_ACTION in actions


def test_missing_flat_field_is_not_inferred() -> None:
    document = build_document(
        authorized_units=None,
        service_lines=[
            build_line(6),
            build_line(1),
        ],
        include_authorized_units=False,
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert (
        "authorized_units"
        not in document.extracted_data
    )

    assert (
        "authorized_units"
        not in document.field_confidences
    )

    assert RECONCILIATION_ACTION not in actions


def test_empty_flat_value_is_not_inferred() -> None:
    document = build_document(
        authorized_units=None,
        service_lines=[
            build_line(6),
            build_line(1),
        ],
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.extracted_data[
        "authorized_units"
    ] is None

    assert (
        document.field_confidences[
            "authorized_units"
        ]
        == 0.0
    )

    assert RECONCILIATION_ACTION not in actions


def test_matching_flat_quantities_are_not_changed() -> None:
    document = build_document(
        authorized_units=[
            6,
            1,
        ],
        service_lines=[
            build_line(6),
            build_line(1),
        ],
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.extracted_data[
        "authorized_units"
    ] == [
        6,
        1,
    ]

    assert RECONCILIATION_ACTION not in actions


def test_duplicate_row_quantities_are_deduplicated() -> None:
    document = build_document(
        authorized_units=[6],
        service_lines=[
            build_line(6),
            build_line(6),
        ],
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.extracted_data[
        "authorized_units"
    ] == [
        6,
    ]

    assert RECONCILIATION_ACTION not in actions


def test_empty_row_quantities_do_not_change_units() -> None:
    document = build_document(
        authorized_units=[6],
        service_lines=[
            AuthorizationServiceLine(
                service_code="SYNTH1",
                quantity=None,
                confidence=0.95,
                source_text="SYNTH1",
            ),
        ],
    )

    actions = EvidenceValidationService().validate(
        document
    )

    assert document.extracted_data[
        "authorized_units"
    ] == [
        6,
    ]

    assert RECONCILIATION_ACTION not in actions


def test_reconciliation_preserves_original_source() -> None:
    document = build_document(
        authorized_units=[6],
        service_lines=[
            build_line(6),
            build_line(1),
        ],
    )

    EvidenceValidationService().validate(
        document
    )

    source_text = document.field_evidence[
        "authorized_units"
    ][
        "source_text"
    ]

    assert "Authorized quantity 6" in source_text
    assert "SYNTH1 quantity 1" in source_text


def run_test(
    name: str,
    function: Callable[[], None],
) -> bool:
    try:
        function()
    except AssertionError:
        print(
            f"FAILED: {name}"
        )
        return False

    print(
        f"PASSED: {name}"
    )
    return True


def main() -> None:
    print("=" * 60)
    print("Testing Service-Line Quantity Reconciliation")
    print("=" * 60)

    tests = [
        (
            "incomplete flat quantity is reconciled",
            test_incomplete_flat_quantity_is_reconciled,
        ),
        (
            "missing flat field is not inferred",
            test_missing_flat_field_is_not_inferred,
        ),
        (
            "empty flat value is not inferred",
            test_empty_flat_value_is_not_inferred,
        ),
        (
            "matching flat quantities are unchanged",
            test_matching_flat_quantities_are_not_changed,
        ),
        (
            "duplicate row quantities are deduplicated",
            test_duplicate_row_quantities_are_deduplicated,
        ),
        (
            "empty row quantities do not change units",
            test_empty_row_quantities_do_not_change_units,
        ),
        (
            "original source evidence is preserved",
            test_reconciliation_preserves_original_source,
        ),
    ]

    passed = 0
    failed = 0

    for name, function in tests:
        if run_test(
            name,
            function,
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