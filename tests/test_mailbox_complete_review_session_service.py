from dataclasses import fields
from pathlib import Path

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.models.document import Document
from src.services.complete_review_approval_service import (
    CompleteReviewApprovalResult,
)
from src.services.mailbox_complete_review_session_service import (
    MailboxCompleteReviewSessionResult,
    MailboxCompleteReviewSessionService,
)
from src.services.review_output_service import (
    ReviewOutput,
)


passed = 0
failed = 0


class RecordingCompleteReviewInteraction:
    def __init__(
        self,
        results,
    ):
        self.results = list(
            results
        )
        self.review_outputs = []

    def run(
        self,
        *,
        review_output,
    ):
        self.review_outputs.append(
            review_output
        )

        if not self.results:
            raise AssertionError(
                "Unexpected complete-review interaction call."
            )

        return self.results.pop(
            0
        )


def approved_result():
    return CompleteReviewApprovalResult(
        approved=True,
        success=True,
        status="approved",
    )


def rejected_result():
    return CompleteReviewApprovalResult(
        approved=False,
        success=True,
        status="rejected",
    )


def cancelled_result():
    return CompleteReviewApprovalResult(
        approved=False,
        success=False,
        status="cancelled",
    )


def failed_result():
    return CompleteReviewApprovalResult(
        approved=False,
        success=False,
        status="review_still_required",
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
):
    document = Document(
        file_path=Path(
            f"sensitive-{suffix}.pdf"
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
            document_type="authorization",
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
        message_id="synthetic-message-id",
        subject="PRIVATE-SYNTHETIC-SUBJECT",
        processed_documents=list(
            documents
        ),
    )


def test_reviews_each_document_once():
    first = build_document(
        "one"
    )

    second = build_document(
        "two"
    )

    interaction = (
        RecordingCompleteReviewInteraction(
            [
                approved_result(),
                approved_result(),
            ]
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    first,
                    second,
                ]
            )
        ]
    )

    assert interaction.review_outputs == [
        first.review_output,
        second.review_output,
    ]

    assert result.message_count == 1
    assert result.document_count == 2
    assert result.approved_count == 2
    assert result.rejected_count == 0
    assert result.cancelled_count == 0
    assert result.failed_count == 0
    assert result.success is True
    assert result.status == "completed"


def test_reviews_documents_across_messages():
    first = build_document(
        "one"
    )

    second = build_document(
        "two"
    )

    interaction = (
        RecordingCompleteReviewInteraction(
            [
                approved_result(),
                approved_result(),
            ]
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
        )
    )

    result = service.run(
        message_results=[
            build_message_result(
                [first]
            ),
            build_message_result(
                [second]
            ),
        ]
    )

    assert result.message_count == 2
    assert result.document_count == 2

    assert interaction.review_outputs == [
        first.review_output,
        second.review_output,
    ]


def test_rejection_is_counted_safely():
    interaction = (
        RecordingCompleteReviewInteraction(
            [
                rejected_result(),
            ]
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
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
    assert result.rejected_count == 1
    assert result.cancelled_count == 0
    assert result.failed_count == 0
    assert result.success is True

    assert (
        result.status
        == "completed_with_rejections"
    )


def test_cancellation_is_counted_safely():
    interaction = (
        RecordingCompleteReviewInteraction(
            [
                cancelled_result(),
            ]
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
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
    assert result.rejected_count == 0
    assert result.cancelled_count == 1
    assert result.failed_count == 0
    assert result.success is True

    assert (
        result.status
        == "completed_with_cancellations"
    )


def test_failed_approval_is_counted():
    interaction = (
        RecordingCompleteReviewInteraction(
            [
                failed_result(),
            ]
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
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
    assert result.failed_count == 1
    assert result.success is False

    assert (
        result.status
        == "completed_with_failures"
    )


def test_missing_review_output_is_failure():
    interaction = (
        RecordingCompleteReviewInteraction(
            []
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
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

    assert result.document_count == 1
    assert result.failed_count == 1
    assert result.success is False

    assert (
        result.status
        == "completed_with_failures"
    )

    assert interaction.review_outputs == []


def test_mixed_results_are_counted():
    interaction = (
        RecordingCompleteReviewInteraction(
            [
                approved_result(),
                rejected_result(),
                cancelled_result(),
                failed_result(),
            ]
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
        )
    )

    documents = [
        build_document(
            "one"
        ),
        build_document(
            "two"
        ),
        build_document(
            "three"
        ),
        build_document(
            "four"
        ),
    ]

    result = service.run(
        message_results=[
            build_message_result(
                documents
            )
        ]
    )

    assert result.document_count == 4
    assert result.approved_count == 1
    assert result.rejected_count == 1
    assert result.cancelled_count == 1
    assert result.failed_count == 1
    assert result.success is False

    assert (
        result.status
        == "completed_with_failures"
    )


def test_no_documents_is_successful_noop():
    interaction = (
        RecordingCompleteReviewInteraction(
            []
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
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
    assert result.approved_count == 0
    assert result.success is True
    assert result.status == "no_documents"

    assert interaction.review_outputs == []


def test_empty_message_list_is_successful_noop():
    interaction = (
        RecordingCompleteReviewInteraction(
            []
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
        )
    )

    result = service.run(
        message_results=[]
    )

    assert result.message_count == 0
    assert result.document_count == 0
    assert result.success is True
    assert result.status == "no_documents"


def test_invalid_collection_is_rejected():
    interaction = (
        RecordingCompleteReviewInteraction(
            []
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
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

    assert interaction.review_outputs == []


def test_invalid_message_result_is_rejected():
    interaction = (
        RecordingCompleteReviewInteraction(
            []
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
        )
    )

    result = service.run(
        message_results=[
            {},
        ]
    )

    assert result.success is False

    assert (
        result.status
        == "invalid_message_result"
    )

    assert interaction.review_outputs == []


def test_message_results_are_not_mutated():
    document = build_document(
        "one"
    )

    message_result = build_message_result(
        [document]
    )

    original_documents = list(
        message_result.processed_documents
    )

    interaction = (
        RecordingCompleteReviewInteraction(
            [
                approved_result(),
            ]
        )
    )

    service = (
        MailboxCompleteReviewSessionService(
            review_interaction=interaction
        )
    )

    service.run(
        message_results=[
            message_result
        ]
    )

    assert (
        message_result.processed_documents
        == original_documents
    )

    assert (
        message_result.processed_documents[0]
        is document
    )


def test_result_contract_is_phi_safe():
    field_names = {
        field.name
        for field in fields(
            MailboxCompleteReviewSessionResult
        )
    }

    assert field_names == {
        "message_count",
        "document_count",
        "approved_count",
        "rejected_count",
        "cancelled_count",
        "failed_count",
        "success",
        "status",
    }


def test_result_excludes_sensitive_terms():
    result = (
        MailboxCompleteReviewSessionResult(
            message_count=1,
            document_count=1,
            approved_count=1,
            rejected_count=0,
            cancelled_count=0,
            failed_count=0,
            success=True,
            status="completed",
        )
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
        "payload",
        "row_id",
        "fingerprint",
    }

    assert all(
        term not in rendered
        for term in prohibited_terms
    )


print(
    "=" * 60
)
print(
    "Testing Mailbox Complete Review Session"
)
print(
    "=" * 60
)

run_test(
    "documents are completely reviewed once",
    test_reviews_each_document_once,
)

run_test(
    "documents across messages are reviewed",
    test_reviews_documents_across_messages,
)

run_test(
    "rejection is counted safely",
    test_rejection_is_counted_safely,
)

run_test(
    "cancellation is counted safely",
    test_cancellation_is_counted_safely,
)

run_test(
    "failed approval is counted",
    test_failed_approval_is_counted,
)

run_test(
    "missing review output is failure",
    test_missing_review_output_is_failure,
)

run_test(
    "mixed outcomes are counted",
    test_mixed_results_are_counted,
)

run_test(
    "no documents is successful no-op",
    test_no_documents_is_successful_noop,
)

run_test(
    "empty message list is successful no-op",
    test_empty_message_list_is_successful_noop,
)

run_test(
    "invalid collection is rejected",
    test_invalid_collection_is_rejected,
)

run_test(
    "invalid message result is rejected",
    test_invalid_message_result_is_rejected,
)

run_test(
    "message results are not mutated",
    test_message_results_are_not_mutated,
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
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Synthetic deterministic coordinator test"
)
print(
    "Complete-review interaction: Mocked"
)
print(
    "Mailbox ingestion: Not called"
)
print(
    "Attachment download: Not called"
)
print(
    "Document processing: Not called"
)
print(
    "Classification feedback: Not called"
)
print(
    "OCR: Not called"
)
print(
    "Ollama: Not called"
)
print(
    "Smartsheet: Not called"
)
print(
    "External integration: Not called"
)
print(
    "PHI handling: Result contains counts, boolean, "
    "and status only"
)

if failed:
    raise SystemExit(1)
