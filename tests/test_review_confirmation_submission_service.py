from dataclasses import fields
from pathlib import Path

from src.models.document import Document
from src.services.classification_feedback_workflow_service import (
    ClassificationFeedbackWorkflowResult,
)
from src.services.review_confirmation_submission_service import (
    ReviewConfirmationSubmissionResult,
    ReviewConfirmationSubmissionService,
)
from src.services.review_output_service import ReviewOutput


passed = 0
failed = 0

TIMESTAMP = "2026-08-06T18:00:00Z"


class RecordingFeedbackWorkflow:
    def __init__(self):
        self.call_count = 0
        self.last_arguments = None

    def submit(
        self,
        *,
        source_path,
        review_output,
        confirmed_category,
        confirmed_subtype,
        reviewer_confirmation_status,
        created_at=None,
    ):
        self.call_count += 1

        self.last_arguments = {
            "source_path": source_path,
            "review_output": review_output,
            "confirmed_category": confirmed_category,
            "confirmed_subtype": confirmed_subtype,
            "reviewer_confirmation_status": (
                reviewer_confirmation_status
            ),
            "created_at": created_at,
        }

        return ClassificationFeedbackWorkflowResult(
            fingerprint="a" * 64,
            byte_count=25,
            success=True,
            status="stored",
        )


class FailingFeedbackWorkflow:
    def submit(
        self,
        *,
        source_path,
        review_output,
        confirmed_category,
        confirmed_subtype,
        reviewer_confirmation_status,
        created_at=None,
    ):
        return ClassificationFeedbackWorkflowResult(
            fingerprint="b" * 64,
            byte_count=30,
            success=False,
            status="feedback_invalid",
        )


def run_test(name, test_function):
    global passed
    global failed

    try:
        test_function()
        passed += 1
        print(f"PASSED: {name}")
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def build_document():
    document = Document(
        file_path=Path(
            "synthetic-local-document.pdf"
        )
    )

    document.review_output = ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="unknown",
        classification_reason=(
            "Synthetic classification reason."
        ),
        classification_confidence=0.88,
        needs_human_review=True,
        review_status="Human Review Recommended",
    )

    return document


def test_confirmed_submission_calls_workflow_once():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    document = build_document()

    result = service.submit(
        document=document,
        confirmed_category="authorization",
        confirmed_subtype="unknown",
        reviewer_confirmation_status="confirmed",
        created_at=TIMESTAMP,
    )

    assert result.success is True
    assert result.status == "stored"
    assert result.fingerprint == "a" * 64
    assert result.byte_count == 25
    assert workflow.call_count == 1


def test_corrected_submission_is_supported():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    document = build_document()

    result = service.submit(
        document=document,
        confirmed_category="authorization",
        confirmed_subtype="renewal",
        reviewer_confirmation_status="corrected",
        created_at=TIMESTAMP,
    )

    assert result.success is True

    assert (
        workflow.last_arguments[
            "reviewer_confirmation_status"
        ]
        == "corrected"
    )

    assert (
        workflow.last_arguments[
            "confirmed_subtype"
        ]
        == "renewal"
    )

    assert (
        document.document_category
        == "authorization"
    )
    assert (
        document.document_subtype
        == "renewal"
    )
    assert (
        document.review_output.document_category
        == "authorization"
    )
    assert (
        document.review_output.document_subtype
        == "renewal"
    )


def test_confirmation_status_is_normalized():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    result = service.submit(
        document=build_document(),
        confirmed_category="authorization",
        confirmed_subtype="unknown",
        reviewer_confirmation_status=" Confirmed ",
        created_at=TIMESTAMP,
    )

    assert result.success is True

    assert (
        workflow.last_arguments[
            "reviewer_confirmation_status"
        ]
        == "confirmed"
    )


def test_invalid_document_is_rejected_before_workflow():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    result = service.submit(
        document={},
        confirmed_category="authorization",
        confirmed_subtype="unknown",
        reviewer_confirmation_status="confirmed",
        created_at=TIMESTAMP,
    )

    assert result.success is False
    assert result.status == "invalid_document"
    assert workflow.call_count == 0


def test_missing_review_output_is_rejected():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    document = Document(
        file_path=Path(
            "synthetic-local-document.pdf"
        )
    )

    result = service.submit(
        document=document,
        confirmed_category="authorization",
        confirmed_subtype="unknown",
        reviewer_confirmation_status="confirmed",
        created_at=TIMESTAMP,
    )

    assert result.success is False
    assert result.status == "review_output_missing"
    assert workflow.call_count == 0


def test_nonexplicit_status_is_rejected():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    result = service.submit(
        document=build_document(),
        confirmed_category="authorization",
        confirmed_subtype="unknown",
        reviewer_confirmation_status="pending",
        created_at=TIMESTAMP,
    )

    assert result.success is False
    assert result.status == "confirmation_not_explicit"
    assert workflow.call_count == 0


def test_blank_status_is_rejected():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    result = service.submit(
        document=build_document(),
        confirmed_category="authorization",
        confirmed_subtype="unknown",
        reviewer_confirmation_status="",
        created_at=TIMESTAMP,
    )

    assert result.success is False
    assert result.status == "confirmation_not_explicit"
    assert workflow.call_count == 0


def test_existing_review_output_is_passed_unchanged():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    document = build_document()
    original_review_output = document.review_output

    service.submit(
        document=document,
        confirmed_category="authorization",
        confirmed_subtype="unknown",
        reviewer_confirmation_status="confirmed",
        created_at=TIMESTAMP,
    )

    assert document.review_output is original_review_output

    assert (
        workflow.last_arguments[
            "review_output"
        ]
        is original_review_output
    )


def test_document_path_is_used_only_for_workflow_call():
    workflow = RecordingFeedbackWorkflow()

    service = ReviewConfirmationSubmissionService(
        feedback_workflow=workflow
    )

    document = build_document()

    result = service.submit(
        document=document,
        confirmed_category="authorization",
        confirmed_subtype="unknown",
        reviewer_confirmation_status="confirmed",
        created_at=TIMESTAMP,
    )

    assert (
        workflow.last_arguments[
            "source_path"
        ]
        == document.file_path
    )

    assert str(
        document.file_path
    ) not in repr(
        result
    )


def test_workflow_failure_is_preserved_safely():
    service = ReviewConfirmationSubmissionService(
        feedback_workflow=(
            FailingFeedbackWorkflow()
        )
    )

    document = build_document()

    result = service.submit(
        document=document,
        confirmed_category="authorization",
        confirmed_subtype="renewal",
        reviewer_confirmation_status="corrected",
        created_at=TIMESTAMP,
    )

    assert result.success is False
    assert result.status == "feedback_invalid"
    assert result.fingerprint == "b" * 64
    assert result.byte_count == 30

    assert (
        document.document_subtype
        == "unknown"
    )
    assert (
        document.review_output.document_subtype
        == "unknown"
    )


def test_result_contract_has_only_safe_fields():
    field_names = {
        field.name
        for field in fields(
            ReviewConfirmationSubmissionResult
        )
    }

    assert field_names == {
        "fingerprint",
        "byte_count",
        "success",
        "status",
    }


def test_result_excludes_phi_bearing_terms():
    result = ReviewConfirmationSubmissionResult(
        fingerprint="a" * 64,
        byte_count=25,
        success=True,
        status="stored",
    )

    rendered = repr(result).lower()

    prohibited_terms = {
        "source_path",
        "file_path",
        "filename",
        "raw_text",
        "ocr_text",
        "source_text",
        "extracted_data",
        "fields",
        "service_lines",
        "patient",
        "member_id",
        "authorization_number",
        "review_output",
    }

    assert all(
        term not in rendered
        for term in prohibited_terms
    )


print("=" * 60)
print("Testing Review Confirmation Submission")
print("=" * 60)

run_test(
    "confirmed submission calls workflow once",
    test_confirmed_submission_calls_workflow_once,
)
run_test(
    "corrected submission is supported",
    test_corrected_submission_is_supported,
)
run_test(
    "confirmation status is normalized",
    test_confirmation_status_is_normalized,
)
run_test(
    "invalid document is rejected",
    test_invalid_document_is_rejected_before_workflow,
)
run_test(
    "missing review output is rejected",
    test_missing_review_output_is_rejected,
)
run_test(
    "nonexplicit status is rejected",
    test_nonexplicit_status_is_rejected,
)
run_test(
    "blank status is rejected",
    test_blank_status_is_rejected,
)
run_test(
    "review output is passed unchanged",
    test_existing_review_output_is_passed_unchanged,
)
run_test(
    "document path is not returned",
    test_document_path_is_used_only_for_workflow_call,
)
run_test(
    "workflow failure is preserved safely",
    test_workflow_failure_is_preserved_safely,
)
run_test(
    "result contains only safe fields",
    test_result_contract_has_only_safe_fields,
)
run_test(
    "result excludes PHI-bearing terms",
    test_result_excludes_phi_bearing_terms,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic boundary test")
print("OCR: Not called")
print("Ollama: Not called")
print("Extraction: Not called")
print("Validation: Not called")
print("Business rules: Not called")
print("External integration: Not called")
print(
    "PHI handling: No review fields, evidence, OCR text, "
    "or source paths were returned"
)

if failed:
    raise SystemExit(1)
