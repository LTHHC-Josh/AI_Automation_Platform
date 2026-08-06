from dataclasses import fields
from pathlib import Path

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.models.document import Document
from src.services.mailbox_review_session_service import (
    MailboxReviewSessionResult,
    MailboxReviewSessionService,
)
from src.services.review_confirmation_submission_service import (
    ReviewConfirmationSubmissionResult,
)
from src.services.review_output_service import ReviewOutput


passed = 0
failed = 0

TIMESTAMP = "2026-08-06T20:00:00Z"


class RecordingReviewInteraction:
    def __init__(
        self,
        results,
    ):
        self.results = list(
            results
        )
        self.documents = []
        self.created_at_values = []

    def run(
        self,
        *,
        document,
        created_at=None,
    ):
        self.documents.append(
            document
        )
        self.created_at_values.append(
            created_at
        )

        if not self.results:
            raise AssertionError(
                "Unexpected review interaction call."
            )

        return self.results.pop(
            0
        )


def successful_result():
    return ReviewConfirmationSubmissionResult(
        fingerprint="a" * 64,
        byte_count=20,
        success=True,
        status="stored",
    )


def cancelled_result():
    return ReviewConfirmationSubmissionResult(
        fingerprint=None,
        byte_count=0,
        success=False,
        status="cancelled",
    )


def failed_result():
    return ReviewConfirmationSubmissionResult(
        fingerprint=None,
        byte_count=0,
        success=False,
        status="feedback_invalid",
    )


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


def build_document(
    suffix,
):
    document = Document(
        file_path=Path(
            f"sensitive-patient-{suffix}.pdf"
        )
    )

    document.raw_text = (
        f"Synthetic OCR text {suffix}"
    )

    document.extracted_data = {
        "patient_name": (
            f"Synthetic Patient {suffix}"
        ),
    }

    document.review_output = ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_reason=(
            f"Synthetic reason {suffix}"
        ),
        classification_confidence=0.88,
        needs_human_review=True,
        review_status=(
            "Human Review Recommended"
        ),
    )

    return document


def build_message_result(
    documents,
):
    return MessageProcessingResult(
        message_id="synthetic-message-id",
        subject="Synthetic private subject",
        processed_documents=list(
            documents
        ),
    )


def test_reviews_each_document_once_in_order():
    first = build_document(
        "one"
    )
    second = build_document(
        "two"
    )

    interaction = RecordingReviewInteraction(
        [
            successful_result(),
            successful_result(),
        ]
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
    )

    result = service.run(
        message_results=[
            build_message_result(
                [first, second]
            )
        ],
        created_at=TIMESTAMP,
    )

    assert interaction.documents == [
        first,
        second,
    ]

    assert result.message_count == 1
    assert result.document_count == 2
    assert result.submitted_count == 2
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

    interaction = RecordingReviewInteraction(
        [
            successful_result(),
            successful_result(),
        ]
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
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
    assert interaction.documents == [
        first,
        second,
    ]


def test_created_at_is_forwarded():
    document = build_document(
        "one"
    )

    interaction = RecordingReviewInteraction(
        [
            successful_result(),
        ]
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
    )

    service.run(
        message_results=[
            build_message_result(
                [document]
            )
        ],
        created_at=TIMESTAMP,
    )

    assert interaction.created_at_values == [
        TIMESTAMP
    ]


def test_cancellation_is_counted_without_failure():
    interaction = RecordingReviewInteraction(
        [
            cancelled_result(),
        ]
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
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

    assert result.submitted_count == 0
    assert result.cancelled_count == 1
    assert result.failed_count == 0
    assert result.success is True

    assert (
        result.status
        == "completed_with_cancellations"
    )


def test_failed_submission_is_counted():
    interaction = RecordingReviewInteraction(
        [
            failed_result(),
        ]
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
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

    assert result.submitted_count == 0
    assert result.cancelled_count == 0
    assert result.failed_count == 1
    assert result.success is False

    assert (
        result.status
        == "completed_with_failures"
    )


def test_mixed_results_are_counted():
    interaction = RecordingReviewInteraction(
        [
            successful_result(),
            cancelled_result(),
            failed_result(),
        ]
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
    )

    result = service.run(
        message_results=[
            build_message_result(
                [
                    build_document(
                        "one"
                    ),
                    build_document(
                        "two"
                    ),
                    build_document(
                        "three"
                    ),
                ]
            )
        ]
    )

    assert result.document_count == 3
    assert result.submitted_count == 1
    assert result.cancelled_count == 1
    assert result.failed_count == 1
    assert result.success is False

    assert (
        result.status
        == "completed_with_failures"
    )


def test_no_documents_is_successful_noop():
    interaction = RecordingReviewInteraction(
        []
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
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
    assert result.submitted_count == 0
    assert result.success is True
    assert result.status == "no_documents"
    assert interaction.documents == []


def test_empty_message_list_is_successful_noop():
    interaction = RecordingReviewInteraction(
        []
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
    )

    result = service.run(
        message_results=[]
    )

    assert result.message_count == 0
    assert result.document_count == 0
    assert result.success is True
    assert result.status == "no_documents"


def test_invalid_collection_is_rejected():
    interaction = RecordingReviewInteraction(
        []
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
    )

    result = service.run(
        message_results=None
    )

    assert result.success is False

    assert (
        result.status
        == "invalid_message_results"
    )

    assert interaction.documents == []


def test_invalid_result_is_rejected():
    interaction = RecordingReviewInteraction(
        []
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
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

    assert interaction.documents == []


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

    interaction = RecordingReviewInteraction(
        [
            successful_result(),
        ]
    )

    service = MailboxReviewSessionService(
        review_interaction=interaction
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
            MailboxReviewSessionResult
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
    result = MailboxReviewSessionResult(
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
        "storage_payload",
    }

    assert all(
        term not in rendered
        for term in prohibited_terms
    )


print("=" * 60)
print("Testing Mailbox Review Session")
print("=" * 60)

run_test(
    "documents are reviewed once in order",
    test_reviews_each_document_once_in_order,
)
run_test(
    "documents across messages are reviewed",
    test_reviews_documents_across_messages,
)
run_test(
    "created timestamp is forwarded",
    test_created_at_is_forwarded,
)
run_test(
    "cancellation is counted safely",
    test_cancellation_is_counted_without_failure,
)
run_test(
    "failed submission is counted",
    test_failed_submission_is_counted,
)
run_test(
    "mixed results are counted",
    test_mixed_results_are_counted,
)
run_test(
    "no documents is a successful no-op",
    test_no_documents_is_successful_noop,
)
run_test(
    "empty message list is a successful no-op",
    test_empty_message_list_is_successful_noop,
)
run_test(
    "invalid collection is rejected",
    test_invalid_collection_is_rejected,
)
run_test(
    "invalid message result is rejected",
    test_invalid_result_is_rejected,
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
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic coordinator test")
print("Mailbox ingestion: Not called")
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
