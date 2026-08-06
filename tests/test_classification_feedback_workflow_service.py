from dataclasses import fields
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.classification_feedback_storage_service import (
    ClassificationFeedbackStorageService,
)
from src.services.classification_feedback_workflow_service import (
    ClassificationFeedbackWorkflowResult,
    ClassificationFeedbackWorkflowService,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
    ReviewServiceLine,
)


passed = 0
failed = 0

TIMESTAMP = "2026-08-06T17:00:00Z"


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


def build_review_output():
    return ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="unknown",
        classification_reason=(
            "Synthetic classification reason."
        ),
        classification_confidence=0.88,
        fields=[
            ReviewField(
                name="patient_name",
                value="Synthetic Patient",
                confidence=0.95,
                source_text="Synthetic patient evidence",
            ),
            ReviewField(
                name="authorization_number",
                value="SYNTHETIC-AUTH",
                confidence=0.95,
                source_text=(
                    "Synthetic authorization evidence"
                ),
            ),
        ],
        service_lines=[
            ReviewServiceLine(
                service_code="SYNTH1",
                quantity=6,
                confidence=0.90,
                source_text=(
                    "Synthetic service-line evidence"
                ),
            )
        ],
        validation_actions=[
            "Synthetic validation action"
        ],
        rule_actions=[
            "Synthetic rule action"
        ],
        needs_human_review=True,
        review_status="Human Review Recommended",
        review_reasons=[
            "Synthetic review reason"
        ],
    )


def build_workflow(storage_path):
    return ClassificationFeedbackWorkflowService(
        storage_service=(
            ClassificationFeedbackStorageService(
                storage_path
            )
        )
    )


def submit(workflow, source_path):
    return workflow.submit(
        source_path=source_path,
        review_output=build_review_output(),
        confirmed_category="authorization",
        confirmed_subtype="renewal",
        reviewer_confirmation_status="corrected",
        created_at=TIMESTAMP,
    )


def test_valid_submission_is_stored():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.bin"
        source_content = b"synthetic-document"
        source_path.write_bytes(source_content)

        storage_path = root / "feedback.jsonl"
        workflow = build_workflow(storage_path)

        result = submit(
            workflow,
            source_path,
        )

        assert result.success is True
        assert result.status == "stored"
        assert result.fingerprint is not None
        assert len(result.fingerprint) == 64
        assert result.byte_count == len(source_content)
        assert storage_path.exists()


def test_duplicate_submission_is_idempotent():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.bin"
        source_path.write_bytes(b"same-document")

        workflow = build_workflow(
            root / "feedback.jsonl"
        )

        first = submit(
            workflow,
            source_path,
        )
        second = submit(
            workflow,
            source_path,
        )

        assert first.success is True
        assert first.status == "stored"
        assert second.success is True
        assert second.status == "duplicate_fingerprint"
        assert first.fingerprint == second.fingerprint


def test_invalid_feedback_is_not_stored():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.bin"
        source_path.write_bytes(b"synthetic")

        storage_path = root / "feedback.jsonl"
        workflow = build_workflow(storage_path)

        result = workflow.submit(
            source_path=source_path,
            review_output=build_review_output(),
            confirmed_category="authorization",
            confirmed_subtype="renewal",
            reviewer_confirmation_status="confirmed",
            created_at=TIMESTAMP,
        )

        assert result.success is False
        assert result.status == "feedback_invalid"
        assert result.fingerprint is not None
        assert not storage_path.exists()


def test_missing_document_result_is_phi_safe():
    with TemporaryDirectory() as directory:
        root = Path(directory)

        source_path = (
            root
            / "sensitive-patient-name.pdf"
        )

        workflow = build_workflow(
            root / "feedback.jsonl"
        )

        result = submit(
            workflow,
            source_path,
        )

        rendered = repr(result)

        assert result.success is False
        assert result.status == "not_found"
        assert result.fingerprint is None
        assert result.byte_count == 0
        assert "sensitive-patient-name" not in rendered
        assert str(source_path) not in rendered


def test_storage_excludes_review_phi():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source_path = root / "synthetic.bin"
        source_path.write_bytes(b"synthetic")

        storage_path = root / "feedback.jsonl"
        workflow = build_workflow(storage_path)

        result = submit(
            workflow,
            source_path,
        )

        assert result.success is True

        stored_text = storage_path.read_text(
            encoding="utf-8"
        )

        payload = json.loads(
            stored_text.strip()
        )

        prohibited_values = {
            "Synthetic Patient",
            "SYNTHETIC-AUTH",
            "Synthetic patient evidence",
            "Synthetic authorization evidence",
            "Synthetic service-line evidence",
            "SYNTH1",
            "Synthetic validation action",
            "Synthetic rule action",
            "Synthetic review reason",
            "Synthetic classification reason.",
        }

        assert all(
            value not in stored_text
            for value in prohibited_values
        )

        assert set(payload) == (
            ClassificationFeedbackStorageService.ALLOWED_KEYS
        )


def test_result_contract_has_only_four_safe_fields():
    field_names = {
        field.name
        for field in fields(
            ClassificationFeedbackWorkflowResult
        )
    }

    assert field_names == {
        "fingerprint",
        "byte_count",
        "success",
        "status",
    }


def test_result_excludes_path_and_content():
    result = ClassificationFeedbackWorkflowResult(
        fingerprint="a" * 64,
        byte_count=10,
        success=True,
        status="stored",
    )

    rendered = repr(result).lower()

    prohibited_terms = {
        "source_path",
        "filename",
        "document_content",
        "ocr_text",
        "source_text",
        "patient",
        "member_id",
        "authorization_number",
        "review_output",
        "storage_payload",
    }

    assert all(
        term not in rendered
        for term in prohibited_terms
    )


print("=" * 60)
print("Testing Classification Feedback Workflow")
print("=" * 60)

run_test(
    "valid submission is stored",
    test_valid_submission_is_stored,
)
run_test(
    "duplicate submission is idempotent",
    test_duplicate_submission_is_idempotent,
)
run_test(
    "invalid feedback is not stored",
    test_invalid_feedback_is_not_stored,
)
run_test(
    "missing document result is PHI-safe",
    test_missing_document_result_is_phi_safe,
)
run_test(
    "storage excludes review PHI",
    test_storage_excludes_review_phi,
)
run_test(
    "result contains only four safe fields",
    test_result_contract_has_only_four_safe_fields,
)
run_test(
    "result excludes path and content",
    test_result_excludes_path_and_content,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic local workflow test")
print("External integration: Not called")
print(
    "PHI handling: Synthetic content remained local and "
    "was excluded from feedback storage and results"
)

if failed:
    raise SystemExit(1)
