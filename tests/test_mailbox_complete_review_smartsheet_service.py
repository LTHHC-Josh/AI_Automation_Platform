from dataclasses import fields
from pathlib import Path

from src.graph.mailbox_processor import MessageProcessingResult
from src.models.document import Document
from src.models.smartsheet_mapping import SmartsheetColumnPolicy
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetResult,
    MailboxCompleteReviewSmartsheetService,
)
from src.services.review_output_service import ReviewField, ReviewOutput
from src.services.smartsheet_review_configuration_service import (
    SmartsheetReviewConfigurationResult,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionResult,
)


class RecordingConfigurationService:
    def __init__(self, *, success=True):
        self.success = success
        self.calls = []

    def resolve(self, *, document_type):
        self.calls.append(document_type)
        if not self.success:
            return SmartsheetReviewConfigurationResult(
                policy_count=0,
                column_count=0,
                policies=(),
                available_columns={},
                success=False,
                status="policy_not_configured",
            )
        policy = SmartsheetColumnPolicy(
            source_field="authorization_number",
            column_name="Authorization #",
        )
        return SmartsheetReviewConfigurationResult(
            policy_count=1,
            column_count=1,
            policies=(policy,),
            available_columns={"Authorization #": 1},
            success=True,
            status="ready",
        )


class RecordingSubmissionService:
    def __init__(self, *, success=True, raise_error=False):
        self.success = success
        self.raise_error = raise_error
        self.calls = []

    def submit(
        self,
        *,
        review_output,
        policies,
        available_columns,
        attachment_source_path=None,
        run_type="",
    ):
        if self.raise_error:
            raise RuntimeError("synthetic provider detail")
        self.calls.append(
            {
                "review_output": review_output,
                "policy_count": len(policies),
                "column_count": len(available_columns),
                "attachment_supplied": attachment_source_path is not None,
                "run_type": run_type,
            }
        )
        return SmartsheetReviewSubmissionResult(
            written=self.success,
            success=self.success,
            status=("written" if self.success else "destination_not_ready"),
        )


def build_message(*, needs_human_review=False, include_review=True):
    document = Document(file_path=Path("synthetic-document.bin"))
    if include_review:
        document.review_output = ReviewOutput(
            document_type="authorization",
            document_category="authorization",
            document_subtype="renewal",
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
                ["Synthetic review reason."]
                if needs_human_review
                else []
            ),
        )
    return MessageProcessingResult(
        message_id="synthetic-message",
        subject="synthetic-subject",
        processed_documents=[document],
    )


def build_service(*, config_success=True, submit_success=True, raise_error=False):
    configuration = RecordingConfigurationService(success=config_success)
    submission = RecordingSubmissionService(
        success=submit_success,
        raise_error=raise_error,
    )
    service = MailboxCompleteReviewSmartsheetService(
        submission_service=submission,
        configuration_service=configuration,
    )
    return service, configuration, submission


def test_document_type_resolves_configuration():
    service, configuration, _ = build_service()
    result = service.run(
        message_results=[build_message()],
        run_type="Synthetic Mailbox Submission",
    )
    assert result.success is True
    assert configuration.calls == ["authorization"]


def test_configuration_and_attachment_reach_submission():
    service, _, submission = build_service()
    result = service.run(
        message_results=[build_message()],
        run_type="Synthetic Mailbox Submission",
    )
    assert result.written_count == 1
    assert submission.calls[0]["policy_count"] == 1
    assert submission.calls[0]["column_count"] == 1
    assert submission.calls[0]["attachment_supplied"] is True
    assert submission.calls[0]["run_type"] == "Synthetic Mailbox Submission"


def test_review_required_document_is_written_automatically():
    service, _, submission = build_service()
    result = service.run(
        message_results=[build_message(needs_human_review=True)],
        run_type="Synthetic Mailbox Submission",
    )
    assert result.success is True
    assert result.written_count == 1
    assert submission.calls[0]["review_output"].needs_human_review is True


def test_configuration_failure_blocks_submission():
    service, _, submission = build_service(config_success=False)
    result = service.run(
        message_results=[build_message()],
        run_type="Synthetic Mailbox Submission",
    )
    assert result.success is False
    assert result.failed_count == 1
    assert submission.calls == []


def test_submission_failure_is_counted():
    service, _, _ = build_service(submit_success=False)
    result = service.run(
        message_results=[build_message()],
        run_type="Synthetic Mailbox Submission",
    )
    assert result.success is False
    assert result.failed_count == 1
    assert result.written_count == 0


def test_missing_review_output_blocks_downstream_calls():
    service, configuration, submission = build_service()
    result = service.run(
        message_results=[build_message(include_review=False)],
        run_type="Synthetic Mailbox Submission",
    )
    assert result.failed_count == 1
    assert configuration.calls == []
    assert submission.calls == []


def test_submission_exception_is_sanitized():
    service, _, _ = build_service(raise_error=True)
    result = service.run(
        message_results=[build_message()],
        run_type="Synthetic Mailbox Submission",
    )
    assert result.success is False
    assert result.status == "completed_with_failures"


def test_no_documents_is_successful_noop():
    service, configuration, submission = build_service()
    result = service.run(message_results=[], run_type="Synthetic Mailbox Submission")
    assert result.success is True
    assert result.status == "no_documents"
    assert configuration.calls == []
    assert submission.calls == []


def test_invalid_collection_is_blocked():
    service, _, _ = build_service()
    result = service.run(message_results=None, run_type="Synthetic Mailbox Submission")
    assert result.success is False
    assert result.status == "invalid_message_results"


def test_result_contract_remains_phi_safe():
    result_fields = {item.name for item in fields(MailboxCompleteReviewSmartsheetResult)}
    forbidden = {"payload", "row_id", "source_text", "raw_text", "file_path"}
    assert result_fields.isdisjoint(forbidden)


TESTS = [
    ("document type resolves configuration", test_document_type_resolves_configuration),
    ("configuration and attachment reach submission", test_configuration_and_attachment_reach_submission),
    ("review-required document writes automatically", test_review_required_document_is_written_automatically),
    ("configuration failure blocks submission", test_configuration_failure_blocks_submission),
    ("submission failure is counted", test_submission_failure_is_counted),
    ("missing review output blocks downstream calls", test_missing_review_output_blocks_downstream_calls),
    ("submission exception is sanitized", test_submission_exception_is_sanitized),
    ("no documents is successful no-op", test_no_documents_is_successful_noop),
    ("invalid collection is blocked", test_invalid_collection_is_blocked),
    ("result contract remains PHI-safe", test_result_contract_remains_phi_safe),
]


passed = 0
failed = 0

print("=" * 60)
print("Testing Automatic Mailbox Smartsheet Submission")
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
print("Real or mock: Synthetic deterministic/mock coordinator")
print("Mailbox processing: Not called")
print("Smartsheet external API: Not called")
print("Microsoft Graph: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("PHI handling: Counts, booleans, and statuses only")

if failed:
    raise SystemExit(1)
