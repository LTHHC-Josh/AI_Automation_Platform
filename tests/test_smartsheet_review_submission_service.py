from dataclasses import fields

from src.models.smartsheet_destination_validation import (
    SmartsheetDestinationValidationResult,
)
from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionResult,
    SmartsheetReviewSubmissionService,
)
from src.services.smartsheet_reviewed_write_service import (
    SmartsheetReviewedWriteResult,
)


class RecordingDestinationValidationService:
    def __init__(self, *, ready=True):
        self.ready = ready
        self.calls = []

    def validate(self, *, mapping, available_columns):
        self.calls.append(mapping)
        return SmartsheetDestinationValidationResult(
            column_ids=(
                {
                    name: index + 1
                    for index, name in enumerate(mapping.values)
                }
                if self.ready
                else {}
            ),
            mapping_ready=mapping.ready_for_write,
            destination_ready=self.ready,
            ready_for_write=(mapping.ready_for_write and self.ready),
        )


class RecordingWriteService:
    def __init__(self, *, success=True):
        self.success = success
        self.calls = []

    def write(
        self,
        *,
        mapping,
        destination_validation,
        attachment_source_path=None,
    ):
        self.calls.append(
            {
                "mapping": mapping,
                "destination_validation": destination_validation,
                "attachment_supplied": attachment_source_path is not None,
            }
        )
        return SmartsheetReviewedWriteResult(
            written=self.success,
            column_count=(len(mapping.values) if self.success else 0),
            attachment_written=False,
            success=self.success,
            status=("written" if self.success else "synthetic_write_failed"),
        )


def build_review_output(*, needs_human_review=False):
    return ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_confidence=0.94,
        fields=[
            ReviewField(
                name="authorization_number",
                value="SYNTHETIC-AUTH",
                confidence=0.93,
                source_text="Synthetic evidence",
            )
        ],
        needs_human_review=needs_human_review,
        review_status=(
            "Human Review Required"
            if needs_human_review
            else "Verified by AI"
        ),
        review_reasons=(
            ["Synthetic unsupported value remained empty."]
            if needs_human_review
            else []
        ),
    )


def build_service(*, destination_ready=True, write_success=True):
    destination = RecordingDestinationValidationService(
        ready=destination_ready
    )
    writer = RecordingWriteService(success=write_success)
    service = SmartsheetReviewSubmissionService(
        destination_validation_service=destination,
        write_service=writer,
    )
    return service, destination, writer


POLICIES = [
    SmartsheetColumnPolicy(
        source_field="authorization_number",
        column_name="Authorization #",
    )
]


def submit(service, *, review_output=None, attachment_source_path=None):
    return service.submit(
        review_output=(review_output or build_review_output()),
        policies=POLICIES,
        available_columns={},
        attachment_source_path=attachment_source_path,
        run_type="Synthetic Submission Regression",
    )


def test_validated_review_reaches_writer_once():
    service, destination, writer = build_service()
    result = submit(service)
    assert result.success is True
    assert result.written is True
    assert len(destination.calls) == 1
    assert len(writer.calls) == 1


def test_review_required_output_reaches_writer():
    service, destination, writer = build_service()
    result = submit(
        service,
        review_output=build_review_output(needs_human_review=True),
    )
    assert result.success is True
    assert result.written is True
    mapping = destination.calls[0]
    assert mapping.values["AI Review Required"] is True
    assert mapping.values["AI Review Reasons"]
    assert len(writer.calls) == 1


def test_destination_failure_blocks_writer():
    service, destination, writer = build_service(
        destination_ready=False
    )
    result = submit(service)
    assert result.success is False
    assert result.status == "destination_not_ready"
    assert len(destination.calls) == 1
    assert writer.calls == []


def test_mapping_failure_blocks_destination_and_writer():
    service, destination, writer = build_service()
    result = service.submit(
        review_output=build_review_output(),
        policies=[
            SmartsheetColumnPolicy(
                source_field="missing_required",
                column_name="Missing Required",
                required=True,
            )
        ],
        available_columns={},
        run_type="Synthetic Submission Regression",
    )
    assert result.success is False
    assert result.status == "mapping_not_ready"
    assert destination.calls == []
    assert writer.calls == []


def test_writer_failure_is_preserved_safely():
    service, _, writer = build_service(write_success=False)
    result = submit(service)
    assert result.success is False
    assert result.status == "synthetic_write_failed"
    assert len(writer.calls) == 1


def test_attachment_path_is_forwarded_without_logging():
    service, _, writer = build_service()
    result = submit(
        service,
        attachment_source_path="synthetic-document.bin",
    )
    assert result.success is True
    assert writer.calls[0]["attachment_supplied"] is True


def test_invalid_review_output_is_blocked():
    service, destination, writer = build_service()
    result = service.submit(
        review_output=None,
        policies=POLICIES,
        available_columns={},
        run_type="Synthetic Submission Regression",
    )
    assert result.success is False
    assert result.status == "invalid_review_output"
    assert destination.calls == []
    assert writer.calls == []


def test_result_contract_is_phi_safe():
    assert {
        item.name
        for item in fields(SmartsheetReviewSubmissionResult)
    } == {"written", "success", "status"}


TESTS = [
    ("validated review reaches writer once", test_validated_review_reaches_writer_once),
    ("review-required output reaches writer", test_review_required_output_reaches_writer),
    ("destination failure blocks writer", test_destination_failure_blocks_writer),
    ("mapping failure blocks downstream calls", test_mapping_failure_blocks_destination_and_writer),
    ("writer failure remains PHI-safe", test_writer_failure_is_preserved_safely),
    ("attachment path is forwarded", test_attachment_path_is_forwarded_without_logging),
    ("invalid review output is blocked", test_invalid_review_output_is_blocked),
    ("submission result is PHI-safe", test_result_contract_is_phi_safe),
]


passed = 0
failed = 0

print("=" * 60)
print("Testing Automatic Smartsheet Submission")
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
print("Real or mock: Synthetic deterministic/mock")
print("Smartsheet external API: Not called")
print("Microsoft Graph: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("PHI handling: Synthetic values only; payload not printed")

if failed:
    raise SystemExit(1)
