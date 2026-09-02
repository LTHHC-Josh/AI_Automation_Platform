from pathlib import Path
from typing import Callable

from src.business_rules.rules.authorization_rule import (
    AuthorizationRule,
)
from src.models.document import (
    AuthorizationServiceLine,
    Document,
)


QUANTITY_REVIEW_ACTION = (
    "Authorization quantity requires verification"
)

MISSING_QUANTITY_ACTION = (
    "Missing authorization quantity"
)


def build_document(
    approved_visits=None,
    authorized_units=None,
    service_lines=None,
) -> Document:
    """
    Build a complete synthetic authorization containing no PHI.
    """

    document = Document(
        file_path=Path(
            "synthetic-authorization.pdf"
        )
    )

    document.extracted_data = {
        "patient_name": "Synthetic Patient",
        "authorization_number": "SYNTH-AUTH-1",
        "payer": "Synthetic Payer",
        "member_id": "SYNTH123",
        "authorization_status": "Approved",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "approved_visits": approved_visits,
        "authorized_units": authorized_units,
    }

    document.service_lines = (
        service_lines
        if service_lines is not None
        else []
    )

    return document


def execute_rule(
    document: Document,
) -> list[str]:
    return AuthorizationRule().execute(
        document
    )


def test_approved_visits_do_not_require_unit_verification() -> None:
    actions = execute_rule(
        build_document(
            approved_visits=6
        )
    )

    assert QUANTITY_REVIEW_ACTION not in actions
    assert MISSING_QUANTITY_ACTION not in actions


def test_authorized_units_do_not_require_unit_verification() -> None:
    actions = execute_rule(
        build_document(
            authorized_units=[
                "6",
                "1",
            ]
        )
    )

    assert QUANTITY_REVIEW_ACTION not in actions
    assert MISSING_QUANTITY_ACTION not in actions


def test_service_line_quantity_counts_as_present() -> None:
    document = build_document(
        service_lines=[
            AuthorizationServiceLine(
                service_code="SYNTH1",
                quantity="6",
                confidence=0.95,
                source_text="SYNTH1 quantity 6",
            ),
        ]
    )

    actions = execute_rule(
        document
    )

    assert QUANTITY_REVIEW_ACTION not in actions
    assert MISSING_QUANTITY_ACTION not in actions


def test_multiple_service_line_quantities_are_not_classified() -> None:
    document = build_document(
        service_lines=[
            AuthorizationServiceLine(
                service_code="SYNTH1",
                quantity="1",
                confidence=0.95,
                source_text="SYNTH1 quantity 1",
            ),
            AuthorizationServiceLine(
                service_code="SYNTH1",
                quantity="6",
                confidence=0.95,
                source_text="SYNTH1 quantity 6",
            ),
        ]
    )

    actions = execute_rule(
        document
    )

    assert QUANTITY_REVIEW_ACTION not in actions

    assert MISSING_QUANTITY_ACTION not in actions
    assert "Authorization validated successfully" in actions


def test_zero_service_line_quantity_is_not_valid() -> None:
    document = build_document(
        service_lines=[
            AuthorizationServiceLine(
                service_code="SYNTH1",
                quantity=0,
                confidence=0.95,
                source_text="SYNTH1 quantity 0",
            ),
        ]
    )

    actions = execute_rule(
        document
    )

    assert MISSING_QUANTITY_ACTION in actions
    assert QUANTITY_REVIEW_ACTION not in actions


def test_invalid_service_line_quantity_is_not_valid() -> None:
    document = build_document(
        service_lines=[
            AuthorizationServiceLine(
                service_code="SYNTH1",
                quantity="unknown",
                confidence=0.50,
                source_text="SYNTH1 quantity unknown",
            ),
        ]
    )

    actions = execute_rule(
        document
    )

    assert MISSING_QUANTITY_ACTION in actions
    assert QUANTITY_REVIEW_ACTION not in actions


def test_missing_all_quantities_is_reported() -> None:
    actions = execute_rule(
        build_document()
    )

    assert MISSING_QUANTITY_ACTION in actions
    assert QUANTITY_REVIEW_ACTION not in actions


def test_flat_and_service_line_quantity_add_one_action() -> None:
    document = build_document(
        authorized_units=["6"],
        service_lines=[
            AuthorizationServiceLine(
                service_code="SYNTH1",
                quantity="6",
                confidence=0.95,
                source_text="SYNTH1 quantity 6",
            ),
        ],
    )

    actions = execute_rule(
        document
    )

    assert QUANTITY_REVIEW_ACTION not in actions

    assert MISSING_QUANTITY_ACTION not in actions


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
    print("Testing Authorization Quantity Rules")
    print("=" * 60)

    tests = [
        (
            "approved visits do not require unit verification",
            test_approved_visits_do_not_require_unit_verification,
        ),
        (
            "authorized units do not require unit verification",
            test_authorized_units_do_not_require_unit_verification,
        ),
        (
            "service-line quantity counts as present",
            test_service_line_quantity_counts_as_present,
        ),
        (
            "multiple service-line quantities are not classified",
            test_multiple_service_line_quantities_are_not_classified,
        ),
        (
            "zero service-line quantity is not valid",
            test_zero_service_line_quantity_is_not_valid,
        ),
        (
            "invalid service-line quantity is not valid",
            test_invalid_service_line_quantity_is_not_valid,
        ),
        (
            "missing all quantities is reported",
            test_missing_all_quantities_is_reported,
        ),
        (
            "flat and service-line quantity add one action",
            test_flat_and_service_line_quantity_add_one_action,
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
