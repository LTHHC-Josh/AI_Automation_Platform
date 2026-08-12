from dataclasses import fields
from pathlib import Path

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.models.document import Document
from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.complete_review_smartsheet_workflow_service import (
    CompleteReviewSmartsheetWorkflowResult,
)
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetResult,
    MailboxCompleteReviewSmartsheetService,
)
from src.services.review_output_service import (
    ReviewOutput,
)
from src.services.smartsheet_review_configuration_service import (
    SmartsheetReviewConfigurationResult,
)


passed = 0
failed = 0


class RecordingWorkflowService:
    def __init__(
        self,
        results,
    ):
        self.results = list(
            results
        )
        self.calls = []

    def run(
        self,
        *,
        review_output,
        policies,
        available_columns,
        approve_complete_review=False,
        attachment_source_path=None,
        run_type="",
    ):
        self.calls.append(
            {
                "review_output": review_output,
                "policies": policies,
                "available_columns": available_columns,
                "approve_complete_review": (
                    approve_complete_review
                ),
                "attachment_source_path": (
                    attachment_source_path
                ),
                "run_type": run_type,
            }
        )

        if not self.results:
            raise AssertionError(
                "Unexpected workflow call."
            )

        return self.results.pop(
            0
        )


class RecordingConfigurationService:
    def __init__(
        self,
        results,
    ):
        self.results = list(
            results
        )
        self.document_types = []

    def resolve(
        self,
        *,
        document_type,
    ):
        self.document_types.append(
            document_type
        )

        if not self.results:
            raise AssertionError(
                "Unexpected configuration call."
            )

        return self.results.pop(
            0
        )


class FailingWorkflowService:
    def run(
        self,
        *,
        review_output,
        policies,
        available_columns,
        approve_complete_review=False,
        attachment_source_path=None,
        run_type="",
    ):
        raise RuntimeError(
            "PRIVATE-SYNTHETIC-FAILURE"
        )


def run_test(
    name,
    test,
):
    global passed
    global failed

    try:
        test()
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


def build_document(
    suffix,
    *,
    with_review_output=True,
    document_type="authorization",
):
    document = Document(
        file_path=Path(
            f"PRIVATE-SYNTHETIC-{suffix}.pdf"
        )
    )

    document.raw_text = (
        f"PRIVATE-SYNTHETIC-OCR-{suffix}"
    )

    document.extracted_data = {
        "patient_name": (
            f"PRIVATE-SYNTHETIC-PATIENT-{suffix}"
        ),
    }

    if with_review_output:
        document.review_output = ReviewOutput(
            document_type=document_type,
            document_category="authorization",
            document_subtype="renewal",
            classification_reason=(
                f"PRIVATE-SYNTHETIC-REASON-{suffix}"
            ),
            classification_confidence=0.95,
            needs_human_review=False,
            review_status="Verified by AI",
        )

    return document


def build_message_result(
    documents,
):
    return MessageProcessingResult(
        message_id="PRIVATE-SYNTHETIC-ID",
        subject="PRIVATE-SYNTHETIC-SUBJECT",
        processed_documents=list(
            documents
        ),
    )


def ready_configuration():
    policies = (
        SmartsheetColumnPolicy(
            source_field="authorization_status",
            column_name="Authorization Status",
            required=True,
        ),
    )

    return SmartsheetReviewConfigurationResult(
        policy_count=1,
        column_count=1,
        policies=policies,
        available_columns={
            "Authorization Status": 1001,
        },
        success=True,
        status="ready",
    )


def failed_configuration(
    status="policy_not_configured",
):
    return SmartsheetReviewConfigurationResult(
        policy_count=0,
        column_count=0,
        policies=(),
        available_columns={},
        success=False,
        status=status,
    )


def written_result():
    return CompleteReviewSmartsheetWorkflowResult(
        approved=True,
        written=True,
        success=True,
        status="written",
    )


def written_with_attachment_result():
    return CompleteReviewSmartsheetWorkflowResult(
        approved=True,
        written=True,
        success=True,
        status="written_with_attachment",
    )


def rejected_result():
    return CompleteReviewSmartsheetWorkflowResult(
        approved=False,
        written=False,
        success=True,
        status="rejected",
    )


def cancelled_result():
    return CompleteReviewSmartsheetWorkflowResult(
        approved=False,
        written=False,
        success=False,
        status="cancelled",
    )


def failed_result():
    return CompleteReviewSmartsheetWorkflowResult(
        approved=True,
        written=False,
        success=False,
        status="destination_not_ready",
    )


def test_document_type_resolves_configuration():
    document = build_document(
        "one",
        document_type="authorization",
    )

    configuration = (
        RecordingConfigurationService(
            [
                ready_configuration(),
            ]
        )
    )

    workflow = RecordingWorkflowService(
        [
            written_result(),
        ]
    )

    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=workflow,
            configuration_service=configuration,
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [document]
            )
        ]
    )

    assert result.success is True
    assert result.written_count == 1

    assert configuration.document_types == [
        "authorization"
    ]


def test_resolved_config_is_forwarded():
    document = build_document(
        "one"
    )

    configuration_result = (
        ready_configuration()
    )

    configuration = (
        RecordingConfigurationService(
            [
                configuration_result,
            ]
        )
    )

    workflow = RecordingWorkflowService(
        [
            written_result(),
        ]
    )

    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=workflow,
            configuration_service=configuration,
        )
    )

    service.run(
        message_results=[
            build_message_result(
                [document]
            )
        ]
    )

    assert (
        workflow.calls[0][
            "review_output"
        ]
        is document.review_output
    )

    assert (
        workflow.calls[0][
            "policies"
        ]
        == list(
            configuration_result.policies
        )
    )

    assert (
        workflow.calls[0][
            "available_columns"
        ]
        == configuration_result.available_columns
    )

    assert (
        workflow.calls[0][
            "attachment_source_path"
        ]
        == document.file_path
    )


def test_explicit_approval_flag_reaches_workflow():
    document = build_document(
        "one"
    )

    workflow = RecordingWorkflowService(
        [
            written_result(),
        ]
    )

    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=workflow,
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [document]
            )
        ],
        approve_complete_review=True,
    )

    assert result.success is True

    assert (
        workflow.calls[0][
            "approve_complete_review"
        ]
        is True
    )


def test_run_type_reaches_workflow():
    document = build_document(
        "one"
    )

    workflow = RecordingWorkflowService(
        [
            written_result(),
        ]
    )

    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=workflow,
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [document]
            )
        ],
        run_type="Mailbox Run Type forwarding",
    )

    assert result.success is True

    assert (
        workflow.calls[0][
            "run_type"
        ]
        == "Mailbox Run Type forwarding"
    )


def test_configuration_failure_blocks_workflow():
    configuration = (
        RecordingConfigurationService(
            [
                failed_configuration(),
            ]
        )
    )

    workflow = RecordingWorkflowService(
        []
    )

    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=workflow,
            configuration_service=configuration,
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "one"
                    )
                ]
            )
        ]
    )

    assert result.document_count == 1
    assert result.written_count == 0
    assert result.failed_count == 1
    assert result.success is False
    assert workflow.calls == []


def test_written_document_is_counted():
    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=(
                RecordingWorkflowService(
                    [
                        written_result(),
                    ]
                )
            ),
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "one"
                    )
                ]
            )
        ]
    )

    assert result.message_count == 1
    assert result.document_count == 1
    assert result.approved_count == 1
    assert result.written_count == 1
    assert result.failed_count == 0
    assert result.success is True
    assert result.status == "completed"


def test_written_with_attachment_is_counted():
    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=(
                RecordingWorkflowService(
                    [
                        written_with_attachment_result(),
                    ]
                )
            ),
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "attachment"
                    )
                ]
            )
        ]
    )

    assert result.approved_count == 1
    assert result.written_count == 1
    assert result.failed_count == 0
    assert result.success is True
    assert result.status == "completed"


def test_rejection_is_not_written():
    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=(
                RecordingWorkflowService(
                    [
                        rejected_result(),
                    ]
                )
            ),
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "one"
                    )
                ]
            )
        ]
    )

    assert result.approved_count == 0
    assert result.written_count == 0
    assert result.rejected_count == 1
    assert result.failed_count == 0
    assert result.success is True

    assert (
        result.status
        == "completed_with_rejections"
    )


def test_cancellation_is_not_written():
    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=(
                RecordingWorkflowService(
                    [
                        cancelled_result(),
                    ]
                )
            ),
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "one"
                    )
                ]
            )
        ]
    )

    assert result.written_count == 0
    assert result.cancelled_count == 1
    assert result.failed_count == 0
    assert result.success is True


def test_failed_write_is_failure():
    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=(
                RecordingWorkflowService(
                    [
                        failed_result(),
                    ]
                )
            ),
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "one"
                    )
                ]
            )
        ]
    )

    assert result.approved_count == 1
    assert result.written_count == 0
    assert result.failed_count == 1
    assert result.success is False


def test_missing_review_output_blocks_config_and_workflow():
    configuration = (
        RecordingConfigurationService(
            []
        )
    )

    workflow = RecordingWorkflowService(
        []
    )

    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=workflow,
            configuration_service=configuration,
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "one",
                        with_review_output=False,
                    )
                ]
            )
        ]
    )

    assert result.failed_count == 1
    assert configuration.document_types == []
    assert workflow.calls == []


def test_workflow_exception_is_sanitized():
    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=(
                FailingWorkflowService()
            ),
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "one"
                    )
                ]
            )
        ]
    )

    assert result.failed_count == 1
    assert result.success is False

    assert (
        "PRIVATE-SYNTHETIC-FAILURE"
        not in repr(
            result
        )
    )


def test_mixed_outcomes_are_counted():
    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=(
                RecordingWorkflowService(
                    [
                        written_result(),
                        rejected_result(),
                        cancelled_result(),
                        failed_result(),
                    ]
                )
            ),
            configuration_service=(
                RecordingConfigurationService(
                    [
                        ready_configuration(),
                        ready_configuration(),
                        ready_configuration(),
                        ready_configuration(),
                    ]
                )
            ),
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document("one"),
                    build_document("two"),
                    build_document("three"),
                    build_document("four"),
                ]
            )
        ]
    )

    assert result.document_count == 4
    assert result.approved_count == 2
    assert result.written_count == 1
    assert result.rejected_count == 1
    assert result.cancelled_count == 1
    assert result.failed_count == 1
    assert result.success is False


def test_no_documents_is_successful_noop():
    configuration = (
        RecordingConfigurationService(
            []
        )
    )

    workflow = RecordingWorkflowService(
        []
    )

    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=workflow,
            configuration_service=configuration,
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                []
            )
        ]
    )

    assert result.message_count == 1
    assert result.document_count == 0
    assert result.success is True
    assert result.status == "no_documents"
    assert configuration.document_types == []
    assert workflow.calls == []


def test_invalid_collection_is_blocked():
    configuration = (
        RecordingConfigurationService(
            []
        )
    )

    workflow = RecordingWorkflowService(
        []
    )

    service = (
        MailboxCompleteReviewSmartsheetService(
            workflow_service=workflow,
            configuration_service=configuration,
        )
    )

    result = service.run(
        message_results=None
    )

    assert result.success is False

    assert (
        result.status
        == "invalid_message_results"
    )

    assert configuration.document_types == []
    assert workflow.calls == []


def test_result_contract_is_phi_safe():
    field_names = {
        field.name
        for field in fields(
            MailboxCompleteReviewSmartsheetResult
        )
    }

    assert field_names == {
        "message_count",
        "document_count",
        "approved_count",
        "written_count",
        "rejected_count",
        "cancelled_count",
        "failed_count",
        "success",
        "status",
    }

    prohibited_names = {
        "message_id",
        "subject",
        "filename",
        "file_path",
        "raw_text",
        "ocr_text",
        "source_text",
        "review_output",
        "values",
        "payload",
        "row_id",
        "patient",
        "policies",
        "available_columns",
    }

    assert field_names.isdisjoint(
        prohibited_names
    )


print(
    "=" * 60
)
print(
    "Testing Configured Mailbox Complete Review Smartsheet Boundary"
)
print(
    "=" * 60
)

run_test(
    "document type resolves configuration",
    test_document_type_resolves_configuration,
)

run_test(
    "resolved configuration is forwarded",
    test_resolved_config_is_forwarded,
)

run_test(
    "explicit approval flag reaches workflow",
    test_explicit_approval_flag_reaches_workflow,
)

run_test(
    "run type reaches workflow",
    test_run_type_reaches_workflow,
)

run_test(
    "configuration failure blocks workflow",
    test_configuration_failure_blocks_workflow,
)

run_test(
    "written document is counted",
    test_written_document_is_counted,
)

run_test(
    "written with attachment is counted",
    test_written_with_attachment_is_counted,
)

run_test(
    "rejection is not written",
    test_rejection_is_not_written,
)

run_test(
    "cancellation is not written",
    test_cancellation_is_not_written,
)

run_test(
    "failed write is counted",
    test_failed_write_is_failure,
)

run_test(
    "missing review output blocks config and workflow",
    test_missing_review_output_blocks_config_and_workflow,
)

run_test(
    "workflow exception is sanitized",
    test_workflow_exception_is_sanitized,
)

run_test(
    "mixed outcomes are counted",
    test_mixed_outcomes_are_counted,
)

run_test(
    "no documents is successful no-op",
    test_no_documents_is_successful_noop,
)

run_test(
    "invalid collection is blocked",
    test_invalid_collection_is_blocked,
)

run_test(
    "result contract is PHI-safe",
    test_result_contract_is_phi_safe,
)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Synthetic deterministic/mock coordinator test"
)
print(
    "Mailbox processing: Not called"
)
print(
    "Classification feedback: Not called"
)
print(
    "Configuration resolver: Mocked"
)
print(
    "Complete-review workflow: Mocked"
)
print(
    "Smartsheet external API: Not called"
)
print(
    "Microsoft Graph: Not called"
)
print(
    "OCR: Not called"
)
print(
    "Ollama: Not called"
)
print(
    "PHI handling: Synthetic values only; "
    "review and Smartsheet payloads not printed"
)

if failed:
    raise SystemExit(1)
