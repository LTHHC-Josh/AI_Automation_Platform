from types import SimpleNamespace

import smartsheet

from src.clients.smartsheet_client import _DefaultTimeoutSession
from src.models.smartsheet_destination_validation import (
    SmartsheetDestinationValidationResult,
)
from src.models.smartsheet_mapping import SmartsheetRowMappingResult
from src.services.smartsheet_reviewed_write_service import (
    SmartsheetReviewedWriteService,
)


class RecordingSession:
    def __init__(self):
        self.calls = []

    def send(self, request, **kwargs):
        self.calls.append((request, kwargs))
        return "synthetic-response"


class RaisingClient:
    def __init__(self, exception_factory):
        self.exception_factory = exception_factory

    def add_row(self, cells):
        raise self.exception_factory()


def mapping():
    return SmartsheetRowMappingResult(
        values={"Synthetic Column": "synthetic"}, ready_for_write=True
    )


def validation():
    return SmartsheetDestinationValidationResult(
        column_ids={"Synthetic Column": 101}, mapping_ready=True,
        destination_ready=True, ready_for_write=True,
        column_types={"Synthetic Column": "TEXT_NUMBER"},
        mapping_validation_passed=True,
        schema_validation_passed=True,
        type_validation_passed=True,
    )


def test_timeout_session_adds_default_without_overriding_explicit_timeout():
    delegate = RecordingSession()
    session = _DefaultTimeoutSession(delegate, 30.0)

    assert session.send("first") == "synthetic-response"
    session.send("second", timeout=7)

    assert delegate.calls[0][1]["timeout"] == 30.0
    assert delegate.calls[1][1]["timeout"] == 7


def test_nonretryable_api_rejection_is_definite():
    service = SmartsheetReviewedWriteService(
        client=RaisingClient(
            lambda: smartsheet.exceptions.ApiError(
                SimpleNamespace(), "SYNTHETIC_SECRET_DETAIL", False
            )
        )
    )

    result = service.create_row(
        mapping=mapping(), destination_validation=validation()
    )

    assert not result.success and result.outcome_proven
    assert result.request_attempted
    assert result.status == "row_write_api_rejected"
    assert "SYNTHETIC_SECRET_DETAIL" not in repr(result)


def test_transport_exception_is_uncertain_and_sanitized():
    service = SmartsheetReviewedWriteService(
        client=RaisingClient(lambda: RuntimeError("SYNTHETIC_SECRET_DETAIL"))
    )

    result = service.create_row(
        mapping=mapping(), destination_validation=validation()
    )

    assert not result.success and not result.outcome_proven
    assert result.request_attempted
    assert result.status == "row_write_outcome_unknown"
    assert "SYNTHETIC_SECRET_DETAIL" not in repr(result)


def test_api_rejection_retains_only_safe_numeric_metadata():
    provider_result = SimpleNamespace(
        code=1013,
        status_code=400,
        message="SYNTHETIC_SECRET_DETAIL",
        ref_id="SYNTHETIC_SECRET_REFERENCE",
    )
    service = SmartsheetReviewedWriteService(
        client=RaisingClient(
            lambda: smartsheet.exceptions.ApiError(
                SimpleNamespace(result=provider_result),
                "SYNTHETIC_SECRET_DETAIL",
                True,
            )
        )
    )

    result = service.create_row(
        mapping=mapping(), destination_validation=validation()
    )

    assert result.outcome_proven
    assert result.api_error_code == 1013
    assert result.api_status_class == "4xx"
    assert result.rejection_safe_category == "row_write_api_cell_invalid"
    assert "SYNTHETIC_SECRET" not in repr(result)


def test_sdk_timeout_has_fixed_uncertain_timeout_category():
    service = SmartsheetReviewedWriteService(
        client=RaisingClient(
            lambda: smartsheet.exceptions.ServerTimeoutExceededError(
                RuntimeError("SYNTHETIC_SECRET_DETAIL"),
                "SYNTHETIC_SECRET_DETAIL",
            )
        )
    )

    result = service.create_row(
        mapping=mapping(), destination_validation=validation()
    )

    assert not result.success and not result.outcome_proven
    assert result.request_attempted
    assert result.status == "row_write_timeout"
    assert "SYNTHETIC_SECRET_DETAIL" not in repr(result)


def test_success_response_without_row_identity_is_uncertain():
    service = SmartsheetReviewedWriteService(
        client=SimpleNamespace(add_row=lambda cells: SimpleNamespace(id=None))
    )

    result = service.create_row(
        mapping=mapping(), destination_validation=validation()
    )

    assert not result.success and not result.outcome_proven
    assert result.request_attempted
    assert result.status == "row_write_response_invalid"


TESTS = (
    test_timeout_session_adds_default_without_overriding_explicit_timeout,
    test_nonretryable_api_rejection_is_definite,
    test_transport_exception_is_uncertain_and_sanitized,
    test_api_rejection_retains_only_safe_numeric_metadata,
    test_sdk_timeout_has_fixed_uncertain_timeout_category,
    test_success_response_without_row_identity_is_uncertain,
)


if __name__ == "__main__":
    passed = 0
    for test in TESTS:
        test()
        passed += 1
    print(f"Passed: {passed}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/mock transport boundary")
    print("External integrations: not called")
    print("PHI handling: fixed categories and synthetic values only")
