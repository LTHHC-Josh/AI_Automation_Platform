import io
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import fields
from pathlib import Path

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.models.document import Document
from src.models.smartsheet_destination_validation import (
    SmartsheetDestinationValidationResult,
)
from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.document_attachment_naming_service import (
    DocumentAttachmentPreparationResult,
)
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetResult,
    MailboxCompleteReviewSmartsheetService,
)
from src.services.mailbox_full_review_orchestration_service import (
    MailboxFullReviewOrchestrationService,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)
from src.services.smartsheet_review_configuration_service import (
    SmartsheetReviewConfigurationResult,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionResult,
    SmartsheetReviewSubmissionService,
)
from src.services.smartsheet_reviewed_write_service import (
    SmartsheetReviewedWriteService,
)


SYNTHETIC_EXTERNAL_REFERENCE = 73001
SYNTHETIC_PAYLOAD_MARKER = (
    "SYNTHETIC_PAYLOAD_VALUE_DO_NOT_EXPOSE"
)
ATTACHMENT_PATH = Path(
    "synthetic-attachment.bin"
)
TEMPORARY_PATH = Path(
    "synthetic-temporary-attachment.bin"
)


class SyntheticRow:
    def __init__(self):
        self.id = SYNTHETIC_EXTERNAL_REFERENCE


class RecordingClient:
    def __init__(
        self,
        *,
        row_failure=False,
        attachment_failure=False,
    ):
        self.row_failure = row_failure
        self.attachment_failure = (
            attachment_failure
        )
        self.add_count = 0
        self.attachment_count = 0

    def add_row(self, cells):
        self.add_count += 1

        if self.row_failure:
            raise RuntimeError(
                "SYNTHETIC_ROW_PROVIDER_DETAIL"
            )

        return SyntheticRow()

    def attach_file_to_row(
        self,
        row_id,
        file_path,
    ):
        self.attachment_count += 1

        if self.attachment_failure:
            raise RuntimeError(
                "SYNTHETIC_ATTACHMENT_PROVIDER_DETAIL"
            )

        return object()


class FixedAttachmentNamingService:
    def __init__(self):
        self.prepare_count = 0
        self.cleanup_count = 0

    def prepare(self, *, source_path):
        self.prepare_count += 1
        return DocumentAttachmentPreparationResult(
            prepared=True,
            temporary_path=TEMPORARY_PATH,
            success=True,
            status="prepared",
        )

    def cleanup(self, temporary_path):
        self.cleanup_count += 1
        return True


class FixedDestinationValidationService:
    def __init__(self, *, ready=True):
        self.ready = ready
        self.call_count = 0

    def validate(
        self,
        *,
        mapping,
        available_columns,
        available_column_types=None,
        available_system_column_types=None,
    ):
        self.call_count += 1
        column_ids = (
            {
                name: index + 1
                for index, name in enumerate(
                    mapping.values
                )
            }
            if self.ready
            else {}
        )

        return SmartsheetDestinationValidationResult(
            column_ids=column_ids,
            column_types={
                name: (
                    "CHECKBOX"
                    if name == "AI Correction"
                    else "DATE"
                    if name in {"Start Date", "End Date"}
                    else "TEXT_NUMBER"
                )
                for name in mapping.values
            },
            mapping_ready=mapping.ready_for_write,
            destination_ready=self.ready,
            ready_for_write=(
                mapping.ready_for_write
                and self.ready
            ),
            mapping_validation_passed=mapping.ready_for_write,
            schema_validation_passed=self.ready,
            type_validation_passed=self.ready,
        )


class FixedConfigurationService:
    def resolve(
        self,
        *,
        document_type=None,
        document_family=None,
        document_subtype=None,
    ):
        return SmartsheetReviewConfigurationResult(
            policy_count=1,
            column_count=1,
            policies=tuple(
                policies()
            ),
            available_columns={
                "Authorization #": 1,
            },
            success=True,
            status="ready",
        )


class FixedPartialSubmissionService:
    def __init__(self):
        self.call_count = 0

    def submit(self, **kwargs):
        self.call_count += 1
        return SmartsheetReviewSubmissionResult(
            written=True,
            success=False,
            status="smartsheet_attachment_failed",
        )


class FixedMailboxProcessor:
    def __init__(self, message):
        self.message = message
        self.call_count = 0

    def process_unread_messages(self, *, top):
        self.call_count += 1
        return [
            self.message,
        ]


class FixedPartialMailboxSubmissionService:
    def __init__(self):
        self.call_count = 0

    def run(self, *, message_results, run_type):
        self.call_count += 1
        return MailboxCompleteReviewSmartsheetResult(
            message_count=1,
            document_count=1,
            approved_count=0,
            written_count=1,
            rejected_count=0,
            cancelled_count=0,
            failed_count=1,
            success=False,
            status="completed_with_partial_success",
        )


class ForbiddenClassificationReviewService:
    def __init__(self):
        self.call_count = 0

    def run(self, **kwargs):
        self.call_count += 1
        raise AssertionError(
            "Classification review must not run after submission failure."
        )


def policies():
    return [
        SmartsheetColumnPolicy(
            source_field="authorization_number",
            column_name="Authorization #",
        )
    ]


def review_output(
    *,
    needs_human_review=False,
):
    return ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_confidence=0.92,
        fields=[
            ReviewField(
                name="authorization_number",
                value=SYNTHETIC_PAYLOAD_MARKER,
                confidence=0.91,
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
            ["Synthetic review reason"]
            if needs_human_review
            else []
        ),
    )


def build_submission(
    *,
    row_failure=False,
    attachment_failure=False,
    destination_ready=True,
):
    client = RecordingClient(
        row_failure=row_failure,
        attachment_failure=attachment_failure,
    )
    naming = FixedAttachmentNamingService()
    writer = SmartsheetReviewedWriteService(
        client=client,
        attachment_naming_service=naming,
    )
    destination = FixedDestinationValidationService(
        ready=destination_ready
    )
    service = SmartsheetReviewSubmissionService(
        destination_validation_service=destination,
        write_service=writer,
    )
    return service, client, naming, destination


def submit(
    service,
    *,
    output=None,
    attachment=True,
):
    return service.submit(
        review_output=(
            output
            or review_output()
        ),
        policies=policies(),
        available_columns={
            "Authorization #": 1,
        },
        attachment_source_path=(
            ATTACHMENT_PATH
            if attachment
            else None
        ),
        run_type="Synthetic Partial Success",
    )


def test_first_attempt_full_success_is_unchanged():
    service, client, _, _ = build_submission()
    result = submit(service)

    assert result.written is True
    assert result.success is True
    assert result.status == "written_with_attachment"
    assert client.add_count == 1
    assert client.attachment_count == 1


def test_row_failure_performs_no_attachment_upload():
    service, client, _, _ = build_submission(
        row_failure=True
    )
    result = submit(service)

    assert result.written is False
    assert result.success is False
    assert result.status == "row_write_outcome_unknown"
    assert client.add_count == 1
    assert client.attachment_count == 0


def test_destination_failure_performs_no_row_creation():
    service, client, _, destination = build_submission(
        destination_ready=False
    )
    result = submit(service)

    assert result.written is False
    assert result.status == "destination_not_ready"
    assert destination.call_count == 1
    assert client.add_count == 0
    assert client.attachment_count == 0


def test_attachment_absence_is_valid():
    service, client, naming, _ = build_submission()
    result = submit(
        service,
        attachment=False,
    )

    assert result.written is True
    assert result.success is True
    assert result.status == "written"
    assert client.add_count == 1
    assert client.attachment_count == 0
    assert naming.prepare_count == 0


def test_attachment_failure_is_explicit_partial_success():
    service, client, naming, _ = build_submission(
        attachment_failure=True
    )
    result = submit(service)

    assert result.written is True
    assert result.success is False
    assert result.status == "smartsheet_attachment_failed"
    assert client.add_count == 1
    assert client.attachment_count == 1
    assert naming.cleanup_count == 1


def test_result_states_are_unambiguous():
    failed_service, _, _, _ = build_submission(
        row_failure=True
    )
    full_service, _, _, _ = build_submission()
    partial_service, _, _, _ = build_submission(
        attachment_failure=True
    )

    row_failed = submit(failed_service)
    full = submit(full_service)
    partial = submit(partial_service)

    assert (
        row_failed.written,
        row_failed.success,
    ) == (False, False)
    assert (
        full.written,
        full.success,
    ) == (True, True)
    assert (
        partial.written,
        partial.success,
    ) == (True, False)


def test_retry_after_partial_success_blocks_duplicate_row():
    service, client, _, _ = build_submission(
        attachment_failure=True
    )
    first = submit(service)

    retry = service.retry(
        previous_result=first,
        review_output=review_output(),
        policies=policies(),
        available_columns={
            "Authorization #": 1,
        },
        attachment_source_path=ATTACHMENT_PATH,
        run_type="Synthetic Partial Success Retry",
    )

    assert first.written is True
    assert retry.written is True
    assert retry.success is False
    assert retry.status == "retry_blocked_existing_row"
    assert client.add_count == 1
    assert client.attachment_count == 1


def test_retry_after_uncertain_row_failure_is_blocked():
    service, client, _, _ = build_submission(
        row_failure=True
    )
    first = submit(service)
    client.row_failure = False

    retry = service.retry(
        previous_result=first,
        review_output=review_output(),
        policies=policies(),
        available_columns={
            "Authorization #": 1,
        },
        attachment_source_path=ATTACHMENT_PATH,
        run_type="Synthetic Row Retry",
    )

    assert first.written is False
    assert retry.written is False
    assert retry.success is False
    assert retry.status == "retry_blocked_uncertain_row"
    assert client.add_count == 1
    assert client.attachment_count == 0


def test_review_required_row_keeps_automatic_write():
    service, client, _, _ = build_submission()
    result = submit(
        service,
        output=review_output(
            needs_human_review=True
        ),
    )

    assert result.written is True
    assert result.success is True
    assert client.add_count == 1
    assert client.attachment_count == 1


def test_mailbox_summary_preserves_partial_row_count():
    output = review_output()
    document = Document(
        file_path=ATTACHMENT_PATH,
        review_output=output,
    )
    message = MessageProcessingResult(
        message_id="synthetic-message",
        subject="synthetic-subject",
        processed_documents=[
            document,
        ],
    )
    submission = FixedPartialSubmissionService()

    result = MailboxCompleteReviewSmartsheetService(
        submission_service=submission,
        configuration_service=(
            FixedConfigurationService()
        ),
    ).run(
        message_results=[
            message,
        ],
        run_type="Synthetic Partial Mailbox",
    )

    assert submission.call_count == 1
    assert result.written_count == 1
    assert result.failed_count == 1
    assert result.success is False
    assert result.status == "completed_with_partial_success"


def test_results_exclude_external_reference_and_payload():
    service, _, _, _ = build_submission(
        attachment_failure=True
    )
    stdout = io.StringIO()
    stderr = io.StringIO()

    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = submit(service)

    rendered = (
        repr(result)
        + result.status
        + stdout.getvalue()
        + stderr.getvalue()
    )

    assert str(
        SYNTHETIC_EXTERNAL_REFERENCE
    ) not in rendered
    assert SYNTHETIC_PAYLOAD_MARKER not in rendered
    assert {
        item.name
        for item in fields(
            SmartsheetReviewSubmissionResult
        )
    } == {
        "written",
        "success",
        "status",
    }


def test_full_orchestration_preserves_partial_state():
    message = MessageProcessingResult(
        message_id="synthetic-message",
        subject="synthetic-subject",
        processed_documents=[
            Document(
                file_path=ATTACHMENT_PATH,
                review_output=review_output(),
            )
        ],
    )
    mailbox = FixedMailboxProcessor(
        message
    )
    submission = FixedPartialMailboxSubmissionService()
    classification = ForbiddenClassificationReviewService()

    result = MailboxFullReviewOrchestrationService(
        mailbox_processor=mailbox,
        complete_review_smartsheet_service=submission,
        classification_review_session=classification,
    ).run(
        run_type="Synthetic Partial Orchestration",
    )

    assert mailbox.call_count == 1
    assert submission.call_count == 1
    assert classification.call_count == 0
    assert result.written_count == 1
    assert result.failed_count == 1
    assert result.success is False
    assert result.status == "completed_with_partial_success"


TESTS = [
    ("full success unchanged", test_first_attempt_full_success_is_unchanged),
    ("row failure blocks attachment", test_row_failure_performs_no_attachment_upload),
    ("destination failure blocks row", test_destination_failure_performs_no_row_creation),
    ("optional attachment remains valid", test_attachment_absence_is_valid),
    ("attachment failure is partial", test_attachment_failure_is_explicit_partial_success),
    ("result states are unambiguous", test_result_states_are_unambiguous),
    ("partial retry blocks duplicate", test_retry_after_partial_success_blocks_duplicate_row),
    ("uncertain row failure retry is blocked", test_retry_after_uncertain_row_failure_is_blocked),
    ("review-required row writes", test_review_required_row_keeps_automatic_write),
    ("mailbox preserves partial count", test_mailbox_summary_preserves_partial_row_count),
    ("full orchestration preserves partial state", test_full_orchestration_preserves_partial_state),
    ("result suppresses external state", test_results_exclude_external_reference_and_payload),
]


def main():
    passed = 0
    failed = 0

    print("=" * 60)
    print("Testing Smartsheet Partial Success and Retry")
    print("=" * 60)

    for name, operation in TESTS:
        try:
            operation()
            passed += 1
            print(
                f"PASSED: {name}"
            )
        except Exception as error:
            failed += 1
            print(
                f"FAILED: {name}: "
                f"{type(error).__name__}"
            )

    print()
    print(
        f"Passed: {passed}"
    )
    print(
        f"Failed: {failed}"
    )
    print(
        "Classification: synthetic deterministic/mock"
    )
    print(
        "Smartsheet external API: not called"
    )
    print(
        "PHI/protected-data access: no"
    )

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()
