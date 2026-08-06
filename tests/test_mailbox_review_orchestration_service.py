from dataclasses import fields

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.services.mailbox_review_orchestration_service import (
    MailboxReviewOrchestrationResult,
    MailboxReviewOrchestrationService,
)
from src.services.mailbox_review_session_service import (
    MailboxReviewSessionResult,
)


passed = 0
failed = 0

TIMESTAMP = "2026-08-06T20:30:00Z"


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
        self.call_count = 0
        self.top_values = []

    def process_unread_messages(
        self,
        top=10,
    ):
        self.call_count += 1
        self.top_values.append(
            top
        )

        if self.error is not None:
            raise self.error

        return self.results


class RecordingReviewSession:
    def __init__(
        self,
        *,
        result=None,
        error=None,
    ):
        self.result = (
            result
            or MailboxReviewSessionResult(
                message_count=0,
                document_count=0,
                submitted_count=0,
                cancelled_count=0,
                failed_count=0,
                success=True,
                status="no_documents",
            )
        )
        self.error = error
        self.call_count = 0
        self.message_results = None
        self.created_at_values = []

    def run(
        self,
        *,
        message_results,
        created_at=None,
    ):
        self.call_count += 1
        self.message_results = message_results
        self.created_at_values.append(
            created_at
        )

        if self.error is not None:
            raise self.error

        return self.result


def run_test(
    name,
    test_function,
):
    global passed
    global failed

    try:
        test_function()
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
            message_id="synthetic-message-id",
            subject="Synthetic private subject",
        )
    ]


def completed_review_result():
    return MailboxReviewSessionResult(
        message_count=2,
        document_count=3,
        submitted_count=3,
        cancelled_count=0,
        failed_count=0,
        success=True,
        status="completed",
    )


def test_mailbox_results_are_passed_to_review_session():
    message_results = build_message_results()

    mailbox = RecordingMailboxProcessor(
        results=message_results
    )

    review = RecordingReviewSession(
        result=completed_review_result()
    )

    service = MailboxReviewOrchestrationService(
        mailbox_processor=mailbox,
        review_session=review,
    )

    result = service.run(
        top=5,
        created_at=TIMESTAMP,
    )

    assert mailbox.call_count == 1
    assert mailbox.top_values == [5]
    assert review.call_count == 1
    assert review.message_results is message_results
    assert review.created_at_values == [TIMESTAMP]
    assert result.success is True
    assert result.status == "completed"


def test_completed_counts_are_preserved():
    service = MailboxReviewOrchestrationService(
        mailbox_processor=RecordingMailboxProcessor(
            results=build_message_results()
        ),
        review_session=RecordingReviewSession(
            result=completed_review_result()
        ),
    )

    result = service.run()

    assert result.message_count == 2
    assert result.document_count == 3
    assert result.submitted_count == 3
    assert result.cancelled_count == 0
    assert result.failed_count == 0


def test_cancellation_status_is_preserved():
    review_result = MailboxReviewSessionResult(
        message_count=1,
        document_count=2,
        submitted_count=1,
        cancelled_count=1,
        failed_count=0,
        success=True,
        status="completed_with_cancellations",
    )

    service = MailboxReviewOrchestrationService(
        mailbox_processor=RecordingMailboxProcessor(
            results=build_message_results()
        ),
        review_session=RecordingReviewSession(
            result=review_result
        ),
    )

    result = service.run()

    assert result.success is True

    assert (
        result.status
        == "completed_with_cancellations"
    )

    assert result.cancelled_count == 1


def test_review_failure_status_is_preserved():
    review_result = MailboxReviewSessionResult(
        message_count=1,
        document_count=1,
        submitted_count=0,
        cancelled_count=0,
        failed_count=1,
        success=False,
        status="completed_with_failures",
    )

    service = MailboxReviewOrchestrationService(
        mailbox_processor=RecordingMailboxProcessor(
            results=build_message_results()
        ),
        review_session=RecordingReviewSession(
            result=review_result
        ),
    )

    result = service.run()

    assert result.success is False

    assert (
        result.status
        == "completed_with_failures"
    )

    assert result.failed_count == 1


def test_no_documents_status_is_preserved():
    service = MailboxReviewOrchestrationService(
        mailbox_processor=RecordingMailboxProcessor(
            results=[]
        ),
        review_session=RecordingReviewSession(),
    )

    result = service.run()

    assert result.success is True
    assert result.status == "no_documents"
    assert result.message_count == 0
    assert result.document_count == 0


def test_mailbox_exception_is_sanitized():
    mailbox = RecordingMailboxProcessor(
        error=RuntimeError(
            "Synthetic private mailbox detail"
        )
    )

    review = RecordingReviewSession()

    service = MailboxReviewOrchestrationService(
        mailbox_processor=mailbox,
        review_session=review,
    )

    result = service.run()

    assert result.success is False

    assert (
        result.status
        == "mailbox_processing_failed"
    )

    assert review.call_count == 0

    assert (
        "Synthetic private mailbox detail"
        not in repr(result)
    )


def test_review_exception_is_sanitized():
    mailbox = RecordingMailboxProcessor(
        results=build_message_results()
    )

    review = RecordingReviewSession(
        error=RuntimeError(
            "Synthetic private review detail"
        )
    )

    service = MailboxReviewOrchestrationService(
        mailbox_processor=mailbox,
        review_session=review,
    )

    result = service.run()

    assert result.success is False

    assert (
        result.status
        == "review_session_failed"
    )

    assert (
        "Synthetic private review detail"
        not in repr(result)
    )


def test_invalid_top_is_rejected_before_calls():
    mailbox = RecordingMailboxProcessor()
    review = RecordingReviewSession()

    service = MailboxReviewOrchestrationService(
        mailbox_processor=mailbox,
        review_session=review,
    )

    invalid_values = [
        None,
        "",
        0,
        -1,
        False,
    ]

    for value in invalid_values:
        result = service.run(
            top=value
        )

        assert result.success is False
        assert result.status == "invalid_top"

    assert mailbox.call_count == 0
    assert review.call_count == 0


def test_numeric_text_top_is_normalized():
    mailbox = RecordingMailboxProcessor()
    review = RecordingReviewSession()

    service = MailboxReviewOrchestrationService(
        mailbox_processor=mailbox,
        review_session=review,
    )

    result = service.run(
        top="4"
    )

    assert result.success is True
    assert mailbox.top_values == [4]


def test_result_contract_is_phi_safe():
    field_names = {
        field.name
        for field in fields(
            MailboxReviewOrchestrationResult
        )
    }

    assert field_names == {
        "message_count",
        "document_count",
        "submitted_count",
        "cancelled_count",
        "failed_count",
        "success",
        "status",
    }


def test_result_excludes_sensitive_terms():
    result = MailboxReviewOrchestrationResult(
        message_count=1,
        document_count=1,
        submitted_count=1,
        cancelled_count=0,
        failed_count=0,
        success=True,
        status="completed",
    )

    rendered = repr(
        result
    ).lower()

    prohibited_terms = {
        "message_id",
        "subject",
        "source_path",
        "file_path",
        "filename",
        "raw_text",
        "ocr_text",
        "source_text",
        "extracted_data",
        "patient",
        "authorization_number",
        "review_output",
        "fingerprint",
        "correction",
        "storage_payload",
    }

    assert all(
        term not in rendered
        for term in prohibited_terms
    )


print("=" * 60)
print("Testing Mailbox Review Orchestration")
print("=" * 60)

run_test(
    "mailbox results pass to review session",
    test_mailbox_results_are_passed_to_review_session,
)
run_test(
    "completed counts are preserved",
    test_completed_counts_are_preserved,
)
run_test(
    "cancellation status is preserved",
    test_cancellation_status_is_preserved,
)
run_test(
    "review failure status is preserved",
    test_review_failure_status_is_preserved,
)
run_test(
    "no documents status is preserved",
    test_no_documents_status_is_preserved,
)
run_test(
    "mailbox exception is sanitized",
    test_mailbox_exception_is_sanitized,
)
run_test(
    "review exception is sanitized",
    test_review_exception_is_sanitized,
)
run_test(
    "invalid top is rejected before calls",
    test_invalid_top_is_rejected_before_calls,
)
run_test(
    "numeric text top is normalized",
    test_numeric_text_top_is_normalized,
)
run_test(
    "result contract is PHI-safe",
    test_result_contract_is_phi_safe,
)
run_test(
    "result excludes sensitive terms",
    test_result_excludes_sensitive_terms,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Mock orchestration test")
print("Mailbox processor: Mocked")
print("Review session: Mocked")
print("Microsoft Graph: Not called")
print("Attachment download: Not called")
print("Document processing: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("Smartsheet: Not called")
print("External integration: Not called")
print(
    "PHI handling: Results contain counts, booleans, "
    "and status only"
)

if failed:
    raise SystemExit(1)
