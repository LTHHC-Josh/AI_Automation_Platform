from dataclasses import fields

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetResult,
)
from src.services.mailbox_full_review_orchestration_service import (
    MailboxFullReviewOrchestrationResult,
    MailboxFullReviewOrchestrationService,
)
from src.services.mailbox_review_session_service import (
    MailboxReviewSessionResult,
)


passed = 0
failed = 0

TIMESTAMP = "2026-08-07T16:00:00Z"


class RecordingMailboxProcessor:
    def __init__(
        self,
        *,
        results=None,
        error=None,
    ):
        self.results = (
            results
            if results is not None
            else []
        )
        self.error = error
        self.calls = []

    def process_unread_messages(
        self,
        top=10,
    ):
        self.calls.append(
            top
        )

        if self.error is not None:
            raise self.error

        return self.results


class RecordingClassificationSession:
    def __init__(
        self,
        result,
        *,
        error=None,
    ):
        self.result = result
        self.error = error
        self.calls = []

    def run(
        self,
        *,
        message_results,
        created_at=None,
    ):
        self.calls.append(
            {
                "message_results": message_results,
                "created_at": created_at,
            }
        )

        if self.error is not None:
            raise self.error

        return self.result


class RecordingCompleteReviewService:
    def __init__(
        self,
        result,
        *,
        error=None,
    ):
        self.result = result
        self.error = error
        self.calls = []
        self.approval_flags = []

    def run(
        self,
        *,
        message_results,
        approve_complete_review=False,
    ):
        self.calls.append(
            message_results
        )

        self.approval_flags.append(
            approve_complete_review
        )

        if self.error is not None:
            raise self.error

        return self.result


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


def build_message_results():
    return [
        MessageProcessingResult(
            message_id="PRIVATE-SYNTHETIC-ID",
            subject="PRIVATE-SYNTHETIC-SUBJECT",
        )
    ]


def classification_completed():
    return MailboxReviewSessionResult(
        message_count=1,
        document_count=2,
        submitted_count=2,
        cancelled_count=0,
        failed_count=0,
        success=True,
        status="completed",
    )


def complete_written():
    return MailboxCompleteReviewSmartsheetResult(
        message_count=1,
        document_count=2,
        approved_count=2,
        written_count=2,
        rejected_count=0,
        cancelled_count=0,
        failed_count=0,
        success=True,
        status="completed",
    )


def test_same_mailbox_results_reach_both_review_stages():
    message_results = build_message_results()

    mailbox = RecordingMailboxProcessor(
        results=message_results
    )

    classification = (
        RecordingClassificationSession(
            classification_completed()
        )
    )

    complete = (
        RecordingCompleteReviewService(
            complete_written()
        )
    )

    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=mailbox,
            classification_review_session=classification,
            complete_review_smartsheet_service=complete,
        )
    )

    result = service.run(
        top=4,
        created_at=TIMESTAMP,
    )

    assert mailbox.calls == [4]

    assert (
        classification.calls[0][
            "message_results"
        ]
        is message_results
    )

    assert (
        classification.calls[0][
            "created_at"
        ]
        == TIMESTAMP
    )

    assert complete.calls == [
        message_results
    ]

    assert result.success is True
    assert result.written_count == 2


def test_demo_skip_bypasses_classification_review_only():
    message_results = build_message_results()

    message_results[0].processed_documents = [
        object()
    ]

    mailbox = RecordingMailboxProcessor(
        results=message_results
    )

    classification = RecordingClassificationSession(
        classification_completed()
    )

    complete = RecordingCompleteReviewService(
        MailboxCompleteReviewSmartsheetResult(
            message_count=1,
            document_count=1,
            approved_count=1,
            written_count=1,
            rejected_count=0,
            cancelled_count=0,
            failed_count=0,
            success=True,
            status="completed",
        )
    )

    service = MailboxFullReviewOrchestrationService(
        mailbox_processor=mailbox,
        classification_review_session=classification,
        complete_review_smartsheet_service=complete,
    )

    result = service.run(
        skip_classification_review=True
    )

    assert classification.calls == []

    assert complete.calls == [
        message_results
    ]

    assert result.document_count == 1
    assert result.classification_submitted_count == 0
    assert result.approved_count == 1
    assert result.written_count == 1
    assert result.success is True


def test_explicit_approval_flag_reaches_complete_review():
    message_results = build_message_results()

    complete = RecordingCompleteReviewService(
        complete_written()
    )

    service = MailboxFullReviewOrchestrationService(
        mailbox_processor=RecordingMailboxProcessor(
            results=message_results
        ),
        classification_review_session=(
            RecordingClassificationSession(
                classification_completed()
            )
        ),
        complete_review_smartsheet_service=complete,
    )

    result = service.run(
        approve_complete_review=True
    )

    assert result.success is True

    assert complete.approval_flags == [
        True
    ]


def test_classification_failure_blocks_complete_review():
    message_results = build_message_results()

    classification_result = (
        MailboxReviewSessionResult(
            message_count=1,
            document_count=1,
            submitted_count=0,
            cancelled_count=0,
            failed_count=1,
            success=False,
            status="completed_with_failures",
        )
    )

    complete = (
        RecordingCompleteReviewService(
            complete_written()
        )
    )

    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=(
                RecordingMailboxProcessor(
                    results=message_results
                )
            ),
            classification_review_session=(
                RecordingClassificationSession(
                    classification_result
                )
            ),
            complete_review_smartsheet_service=complete,
        )
    )

    result = service.run()

    assert result.success is False

    assert (
        result.status
        == "completed_with_failures"
    )

    assert complete.calls == []


def test_no_documents_skips_complete_review():
    complete = (
        RecordingCompleteReviewService(
            complete_written()
        )
    )

    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=(
                RecordingMailboxProcessor(
                    results=[]
                )
            ),
            classification_review_session=(
                RecordingClassificationSession(
                    MailboxReviewSessionResult(
                        message_count=0,
                        document_count=0,
                        submitted_count=0,
                        cancelled_count=0,
                        failed_count=0,
                        success=True,
                        status="no_documents",
                    )
                )
            ),
            complete_review_smartsheet_service=complete,
        )
    )

    result = service.run()

    assert result.success is True
    assert result.status == "no_documents"
    assert complete.calls == []


def test_rejected_complete_review_is_preserved():
    complete_result = (
        MailboxCompleteReviewSmartsheetResult(
            message_count=1,
            document_count=2,
            approved_count=1,
            written_count=1,
            rejected_count=1,
            cancelled_count=0,
            failed_count=0,
            success=True,
            status="completed_with_rejections",
        )
    )

    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=(
                RecordingMailboxProcessor(
                    results=build_message_results()
                )
            ),
            classification_review_session=(
                RecordingClassificationSession(
                    classification_completed()
                )
            ),
            complete_review_smartsheet_service=(
                RecordingCompleteReviewService(
                    complete_result
                )
            ),
        )
    )

    result = service.run()

    assert result.success is True
    assert result.rejected_count == 1
    assert result.written_count == 1

    assert (
        result.status
        == "completed_with_rejections"
    )


def test_complete_review_failure_is_preserved():
    complete_result = (
        MailboxCompleteReviewSmartsheetResult(
            message_count=1,
            document_count=2,
            approved_count=1,
            written_count=0,
            rejected_count=0,
            cancelled_count=0,
            failed_count=1,
            success=False,
            status="completed_with_failures",
        )
    )

    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=(
                RecordingMailboxProcessor(
                    results=build_message_results()
                )
            ),
            classification_review_session=(
                RecordingClassificationSession(
                    classification_completed()
                )
            ),
            complete_review_smartsheet_service=(
                RecordingCompleteReviewService(
                    complete_result
                )
            ),
        )
    )

    result = service.run()

    assert result.success is False
    assert result.failed_count == 1
    assert result.written_count == 0

    assert (
        result.status
        == "completed_with_failures"
    )


def test_mailbox_exception_is_sanitized():
    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=(
                RecordingMailboxProcessor(
                    error=RuntimeError(
                        "PRIVATE-SYNTHETIC-MAILBOX"
                    )
                )
            ),
            classification_review_session=(
                RecordingClassificationSession(
                    classification_completed()
                )
            ),
            complete_review_smartsheet_service=(
                RecordingCompleteReviewService(
                    complete_written()
                )
            ),
        )
    )

    result = service.run()

    assert result.success is False

    assert (
        result.status
        == "mailbox_processing_failed"
    )

    assert (
        "PRIVATE-SYNTHETIC-MAILBOX"
        not in repr(
            result
        )
    )


def test_classification_exception_is_sanitized():
    complete = (
        RecordingCompleteReviewService(
            complete_written()
        )
    )

    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=(
                RecordingMailboxProcessor(
                    results=build_message_results()
                )
            ),
            classification_review_session=(
                RecordingClassificationSession(
                    classification_completed(),
                    error=RuntimeError(
                        "PRIVATE-SYNTHETIC-CLASSIFICATION"
                    ),
                )
            ),
            complete_review_smartsheet_service=complete,
        )
    )

    result = service.run()

    assert result.success is False

    assert (
        result.status
        == "classification_review_failed"
    )

    assert complete.calls == []


def test_complete_review_exception_is_sanitized():
    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=(
                RecordingMailboxProcessor(
                    results=build_message_results()
                )
            ),
            classification_review_session=(
                RecordingClassificationSession(
                    classification_completed()
                )
            ),
            complete_review_smartsheet_service=(
                RecordingCompleteReviewService(
                    complete_written(),
                    error=RuntimeError(
                        "PRIVATE-SYNTHETIC-COMPLETE"
                    ),
                )
            ),
        )
    )

    result = service.run()

    assert result.success is False

    assert (
        result.status
        == "complete_review_failed"
    )

    assert (
        "PRIVATE-SYNTHETIC-COMPLETE"
        not in repr(
            result
        )
    )


def test_invalid_top_blocks_all_calls():
    mailbox = RecordingMailboxProcessor()

    classification = (
        RecordingClassificationSession(
            classification_completed()
        )
    )

    complete = (
        RecordingCompleteReviewService(
            complete_written()
        )
    )

    service = (
        MailboxFullReviewOrchestrationService(
            mailbox_processor=mailbox,
            classification_review_session=classification,
            complete_review_smartsheet_service=complete,
        )
    )

    for value in [
        None,
        "",
        0,
        -1,
        False,
    ]:
        result = service.run(
            top=value
        )

        assert result.success is False
        assert result.status == "invalid_top"

    assert mailbox.calls == []
    assert classification.calls == []
    assert complete.calls == []


def test_result_contract_is_phi_safe():
    field_names = {
        field.name
        for field in fields(
            MailboxFullReviewOrchestrationResult
        )
    }

    assert field_names == {
        "message_count",
        "document_count",
        "classification_submitted_count",
        "classification_cancelled_count",
        "approved_count",
        "written_count",
        "rejected_count",
        "complete_review_cancelled_count",
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
        "fingerprint",
    }

    assert field_names.isdisjoint(
        prohibited_names
    )


print(
    "=" * 60
)
print(
    "Testing Full Mailbox Review Orchestration"
)
print(
    "=" * 60
)

run_test(
    "same mailbox results reach both review stages",
    test_same_mailbox_results_reach_both_review_stages,
)

run_test(
    "demo skip bypasses classification review only",
    test_demo_skip_bypasses_classification_review_only,
)

run_test(
    "explicit approval reaches complete review",
    test_explicit_approval_flag_reaches_complete_review,
)

run_test(
    "classification failure blocks complete review",
    test_classification_failure_blocks_complete_review,
)

run_test(
    "no documents skips complete review",
    test_no_documents_skips_complete_review,
)

run_test(
    "rejected complete review is preserved",
    test_rejected_complete_review_is_preserved,
)

run_test(
    "complete review failure is preserved",
    test_complete_review_failure_is_preserved,
)

run_test(
    "mailbox exception is sanitized",
    test_mailbox_exception_is_sanitized,
)

run_test(
    "classification exception is sanitized",
    test_classification_exception_is_sanitized,
)

run_test(
    "complete review exception is sanitized",
    test_complete_review_exception_is_sanitized,
)

run_test(
    "invalid top blocks all calls",
    test_invalid_top_blocks_all_calls,
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
    "Real or mock: Mock full-orchestration test"
)
print(
    "Mailbox processor: Mocked"
)
print(
    "Classification review: Mocked"
)
print(
    "Complete-review Smartsheet stage: Mocked"
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
    "Smartsheet external API: Not called"
)
print(
    "PHI handling: Counts, booleans, and statuses only"
)

if failed:
    raise SystemExit(1)
