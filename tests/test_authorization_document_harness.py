from typing import Callable

from scripts.test_authorization_document import (
    EXPECTED_MODIFIER,
    EXPECTED_QUANTITIES,
    EXPECTED_SERVICE_CODE,
    validate_flat_fields,
    validate_retry_metadata,
    validate_review_decision,
    validate_service_lines,
)
from src.models.document import AuthorizationServiceLine
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)


def build_safe_flat_fields(
    authorization_status=None,
) -> dict:
    return {
        "authorization_status": authorization_status,
        "service_code": EXPECTED_SERVICE_CODE,
        "service_codes": [EXPECTED_SERVICE_CODE],
        "authorized_units": sorted(
            EXPECTED_QUANTITIES
        ),
        "modifier": EXPECTED_MODIFIER,
        "request_type": None,
        "approved_visits": None,
        "start_date": "2025-01-01",
        "end_date": "2025-01-02",
    }


def build_safe_service_lines(
    include_modifier: bool = True,
) -> list[AuthorizationServiceLine]:
    quantities = sorted(
        EXPECTED_QUANTITIES
    )

    return [
        AuthorizationServiceLine(
            service_code=EXPECTED_SERVICE_CODE,
            modifier=(
                EXPECTED_MODIFIER
                if include_modifier and line_number == 1
                else None
            ),
            quantity=quantity,
            start_date=None,
            end_date=None,
            status=None,
            confidence=0.50,
            source_text=(
                f"{EXPECTED_SERVICE_CODE} "
                f"{EXPECTED_MODIFIER if include_modifier and line_number == 1 else ''} "
                f"{quantity}"
            ),
        )
        for line_number, quantity in enumerate(
            quantities,
            start=1,
        )
    ]


def service_line_clear_actions() -> list[str]:
    actions: list[str] = []

    for line_number in range(
        1,
        3,
    ):
        for field_name in (
            "start date",
            "end date",
            "status",
        ):
            actions.append(
                f"Service line {line_number} {field_name} "
                "is not supported by its source evidence"
            )

    return actions


def test_cleared_authorization_status_requires_action() -> None:
    actions = [
        "Authorization status is not directly supported "
        "by its source evidence",
    ]

    assert validate_flat_fields(
        extracted_data=build_safe_flat_fields(),
        field_evidence={
            "authorization_status": {
                "source_text": "Synthetic decision evidence",
            },
        },
        validation_actions=actions,
    ) == []


def test_supported_authorization_status_requires_direct_evidence() -> None:
    assert validate_flat_fields(
        extracted_data=build_safe_flat_fields(
            authorization_status="Approved"
        ),
        field_evidence={
            "authorization_status": {
                "source_text": "Authorization Status Approved",
            },
        },
        validation_actions=[],
    ) == []

    failures = validate_flat_fields(
        extracted_data=build_safe_flat_fields(
            authorization_status="Approved"
        ),
        field_evidence={
            "authorization_status": {
                "source_text": "Synthetic unsupported decision",
            },
        },
        validation_actions=[],
    )

    assert failures


def test_cleared_service_line_fields_require_actions() -> None:
    assert validate_service_lines(
        service_lines=build_safe_service_lines(),
        validation_actions=service_line_clear_actions(),
    ) == []

    incomplete_actions = service_line_clear_actions()
    incomplete_actions.pop()

    assert validate_service_lines(
        service_lines=build_safe_service_lines(),
        validation_actions=incomplete_actions,
    )


def test_modifier_relationship_action_matches_validated_rows() -> None:
    other_action = "Synthetic evidence requires review"

    assert validate_review_decision(
        needs_human_review=True,
        validation_actions=[other_action],
        review_reasons=[other_action],
        extracted_data={
            "modifier": EXPECTED_MODIFIER,
        },
        service_lines=build_safe_service_lines(
            include_modifier=True
        ),
    ) == []

    relationship_action = (
        EvidenceValidationService
        .SERVICE_LINE_MODIFIER_RELATIONSHIP_ACTION
    )

    assert validate_review_decision(
        needs_human_review=True,
        validation_actions=[relationship_action],
        review_reasons=[relationship_action],
        extracted_data={
            "modifier": EXPECTED_MODIFIER,
        },
        service_lines=build_safe_service_lines(
            include_modifier=False
        ),
    ) == []


def test_retry_metadata_matches_controlled_checkpoint() -> None:
    assert validate_retry_metadata(
        {
            "extraction_attempt_count": 2,
            "extraction_raw_retry_required": False,
            "extraction_validated_retry_required": True,
            "extraction_retry_triggered": True,
            "extraction_selected_attempt": 2,
        }
    ) == []


def run_test(
    test_name: str,
    test_function: Callable[[], None],
) -> bool:
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
    tests = [
        (
            "cleared authorization status requires action",
            test_cleared_authorization_status_requires_action,
        ),
        (
            "supported authorization status requires evidence",
            test_supported_authorization_status_requires_direct_evidence,
        ),
        (
            "cleared service-line fields require actions",
            test_cleared_service_line_fields_require_actions,
        ),
        (
            "modifier relationship action matches rows",
            test_modifier_relationship_action_matches_validated_rows,
        ),
        (
            "retry metadata matches controlled checkpoint",
            test_retry_metadata_matches_controlled_checkpoint,
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

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()
