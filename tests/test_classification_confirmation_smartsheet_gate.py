import inspect

from src.services.classification_feedback_workflow_service import (
    ClassificationFeedbackWorkflowResult,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionService,
)


def build_classification_result(*, success=True, status="submitted"):
    return ClassificationFeedbackWorkflowResult(
        fingerprint=None,
        byte_count=0,
        success=success,
        status=status,
    )


def test_submission_has_no_classification_credential_parameter():
    parameters = inspect.signature(
        SmartsheetReviewSubmissionService.submit
    ).parameters

    assert "approval_result" not in parameters
    assert "classification_result" not in parameters
    assert "classification_confirmation" not in parameters


def test_classification_success_is_feedback_only():
    result = build_classification_result(success=True)

    assert result.success is True
    assert not hasattr(result, "ready_for_write")
    assert not hasattr(result, "destination_ready")


def test_classification_status_cannot_define_write_readiness():
    result = build_classification_result(
        success=True,
        status="approved",
    )

    assert result.status == "approved"
    assert not hasattr(result, "written")
    assert not hasattr(result, "mapping")


TESTS = [
    (
        "submission has no classification credential parameter",
        test_submission_has_no_classification_credential_parameter,
    ),
    (
        "classification success remains feedback only",
        test_classification_success_is_feedback_only,
    ),
    (
        "classification status cannot define write readiness",
        test_classification_status_cannot_define_write_readiness,
    ),
]


passed = 0
failed = 0

print("=" * 60)
print("Testing Classification and Smartsheet Separation")
print("=" * 60)

for name, test in TESTS:
    try:
        test()
        passed += 1
        print(f"PASSED: {name}")
    except Exception as exception:
        failed += 1
        print(f"FAILED: {name}: {type(exception).__name__}")

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic")
print("Classification feedback storage: Not called")
print("Smartsheet external API: Not called")
print("Microsoft Graph: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("PHI handling: No document or payload values used")

if failed:
    raise SystemExit(1)
