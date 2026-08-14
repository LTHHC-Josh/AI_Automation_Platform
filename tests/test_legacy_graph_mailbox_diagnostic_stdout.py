import io
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import check_graph_read_status
from scripts import test_graph_attachments
from scripts import test_graph_connection
from scripts import test_mailbox_processor
from src.graph.errors import GraphRequestError
from src.graph.mailbox_processor import MessageProcessingResult
from src.models.document import Document


SUBJECT_MARKER = "SYNTHETIC_SUBJECT_DO_NOT_EXPOSE"
SENDER_MARKER = "synthetic.sender@example.invalid"
MESSAGE_ID_MARKER = "SYNTHETIC_MESSAGE_ID_DO_NOT_EXPOSE"
ATTACHMENT_PATH_MARKER = "SYNTHETIC_ATTACHMENT_PATH_DO_NOT_EXPOSE.pdf"
SKIPPED_PATH_MARKER = "SYNTHETIC_SKIPPED_PATH_DO_NOT_EXPOSE.exe"
PROCESSED_PATH_MARKER = "SYNTHETIC_PROCESSED_PATH_DO_NOT_EXPOSE.pdf"
OCR_MARKER = "SYNTHETIC_RAW_OCR_DO_NOT_EXPOSE"
EXTRACTED_MARKER = "SYNTHETIC_EXTRACTED_VALUE_DO_NOT_EXPOSE"
SOURCE_TEXT_MARKER = "SYNTHETIC_SOURCE_TEXT_DO_NOT_EXPOSE"
EVIDENCE_MARKER = "SYNTHETIC_FIELD_EVIDENCE_DO_NOT_EXPOSE"
MAILBOX_ERROR_MARKER = "SYNTHETIC_MAILBOX_ERROR_DO_NOT_EXPOSE"
PROVIDER_MARKER = "SYNTHETIC_PROVIDER_DIAGNOSTIC_DO_NOT_EXPOSE"
CREDENTIAL_MARKER = "SYNTHETIC_CREDENTIAL_TOKEN_DO_NOT_EXPOSE"
RECEIVED_MARKER = "SYNTHETIC_RECEIVED_METADATA_DO_NOT_EXPOSE"


class FixedEmailService:
    def __init__(
        self,
        *,
        unread_messages=None,
        recent_messages=None,
        error=None,
    ):
        self.unread_messages = list(
            unread_messages or []
        )
        self.recent_messages = list(
            recent_messages or []
        )
        self.error = error

    def get_unread_messages(self, top=10):
        if self.error is not None:
            raise self.error

        return list(
            self.unread_messages
        )

    def get_recent_messages(self, top=10):
        if self.error is not None:
            raise self.error

        return list(
            self.recent_messages
        )


class FixedAttachmentService:
    def __init__(
        self,
        *,
        downloaded_files=None,
        error=None,
    ):
        self.downloaded_files = list(
            downloaded_files or []
        )
        self.error = error

    def download_file_attachments(
        self,
        message_id,
    ):
        if self.error is not None:
            raise self.error

        return list(
            self.downloaded_files
        )


class FixedMailboxProcessor:
    def __init__(
        self,
        *,
        results=None,
        error=None,
    ):
        self.results = list(
            results or []
        )
        self.error = error

    def process_unread_messages(self, top=10):
        if self.error is not None:
            raise self.error

        return list(
            self.results
        )


def capture_main(
    operation,
):
    stdout = io.StringIO()
    stderr = io.StringIO()
    escaped = False

    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            operation()
        except Exception:
            escaped = True
            traceback.print_exc()

    return (
        stdout.getvalue() + stderr.getvalue(),
        escaped,
    )


def graph_connection_output():
    service = FixedEmailService(
        unread_messages=[
            {
                "id": MESSAGE_ID_MARKER,
                "subject": SUBJECT_MARKER,
                "from": {
                    "emailAddress": {
                        "address": SENDER_MARKER,
                    }
                },
                "receivedDateTime": RECEIVED_MARKER,
                "hasAttachments": True,
            }
        ]
    )

    with patch.object(
        test_graph_connection,
        "EmailService",
        return_value=service,
    ):
        return capture_main(
            test_graph_connection.main
        )


def graph_connection_failure_output(
    error,
):
    service = FixedEmailService(
        error=error
    )

    with patch.object(
        test_graph_connection,
        "EmailService",
        return_value=service,
    ):
        return capture_main(
            test_graph_connection.main
        )


def attachment_output():
    email_service = FixedEmailService(
        unread_messages=[
            {
                "id": MESSAGE_ID_MARKER,
                "subject": SUBJECT_MARKER,
                "hasAttachments": True,
            }
        ]
    )
    attachment_service = FixedAttachmentService(
        downloaded_files=[
            Path(
                ATTACHMENT_PATH_MARKER
            )
        ]
    )

    with (
        patch.object(
            test_graph_attachments,
            "EmailService",
            return_value=email_service,
        ),
        patch.object(
            test_graph_attachments,
            "AttachmentService",
            return_value=attachment_service,
        ),
    ):
        return capture_main(
            test_graph_attachments.main
        )


def attachment_failure_output():
    email_service = FixedEmailService(
        unread_messages=[
            {
                "id": MESSAGE_ID_MARKER,
                "hasAttachments": True,
            }
        ]
    )
    attachment_service = FixedAttachmentService(
        error=RuntimeError(
            PROVIDER_MARKER
        )
    )

    with (
        patch.object(
            test_graph_attachments,
            "EmailService",
            return_value=email_service,
        ),
        patch.object(
            test_graph_attachments,
            "AttachmentService",
            return_value=attachment_service,
        ),
    ):
        return capture_main(
            test_graph_attachments.main
        )


def read_status_output():
    service = FixedEmailService(
        recent_messages=[
            {
                "id": MESSAGE_ID_MARKER,
                "subject": SUBJECT_MARKER,
                "receivedDateTime": RECEIVED_MARKER,
                "isRead": False,
            },
            {
                "id": "SAFE_SYNTHETIC_SEQUENCE_ONLY",
                "subject": "SECOND_SYNTHETIC_SUBJECT",
                "receivedDateTime": "SECOND_SYNTHETIC_RECEIVED",
                "isRead": True,
            },
        ]
    )

    with patch.object(
        check_graph_read_status,
        "EmailService",
        return_value=service,
    ):
        return capture_main(
            check_graph_read_status.main
        )


def read_status_failure_output():
    service = FixedEmailService(
        error=RuntimeError(
            PROVIDER_MARKER
        )
    )

    with patch.object(
        check_graph_read_status,
        "EmailService",
        return_value=service,
    ):
        return capture_main(
            check_graph_read_status.main
        )


def mailbox_output():
    document = Document(
        file_path=Path(
            PROCESSED_PATH_MARKER
        ),
        document_type="authorization",
        document_category="authorization",
        confidence=0.91,
        raw_text=OCR_MARKER,
        extracted_data={
            "synthetic_field": EXTRACTED_MARKER,
        },
        field_confidences={
            "synthetic_field": 0.82,
        },
        field_evidence={
            "synthetic_field": {
                "value": EVIDENCE_MARKER,
                "confidence": 0.82,
                "source_text": SOURCE_TEXT_MARKER,
            }
        },
        validation_actions=[
            "synthetic_validation_action",
        ],
        rule_actions=[
            "synthetic_rule_action",
        ],
        needs_human_review=True,
        review_status="human review recommended",
        review_reasons=[
            "synthetic_review_reason",
        ],
        minimum_field_confidence=0.82,
    )

    result = MessageProcessingResult(
        message_id=MESSAGE_ID_MARKER,
        subject=SUBJECT_MARKER,
        downloaded_files=[
            Path(
                ATTACHMENT_PATH_MARKER
            )
        ],
        processed_documents=[
            document,
        ],
        skipped_files=[
            Path(
                SKIPPED_PATH_MARKER
            )
        ],
        errors=[
            MAILBOX_ERROR_MARKER,
            CREDENTIAL_MARKER,
        ],
        marked_as_read=False,
    )

    processor = FixedMailboxProcessor(
        results=[
            result,
        ]
    )

    with patch.object(
        test_mailbox_processor,
        "MailboxProcessor",
        return_value=processor,
    ):
        return capture_main(
            test_mailbox_processor.main
        )


def mailbox_failure_output():
    processor = FixedMailboxProcessor(
        error=RuntimeError(
            CREDENTIAL_MARKER
        )
    )

    with patch.object(
        test_mailbox_processor,
        "MailboxProcessor",
        return_value=processor,
    ):
        return capture_main(
            test_mailbox_processor.main
        )


def assert_marker_absent(
    output_factory,
    marker,
):
    output, escaped = output_factory()

    assert escaped is False
    assert marker not in output


def test_subject_is_not_exposed():
    assert_marker_absent(
        graph_connection_output,
        SUBJECT_MARKER,
    )


def test_sender_address_is_not_exposed():
    assert_marker_absent(
        graph_connection_output,
        SENDER_MARKER,
    )


def test_received_metadata_is_not_exposed():
    assert_marker_absent(
        read_status_output,
        RECEIVED_MARKER,
    )


def test_message_id_is_not_exposed():
    assert_marker_absent(
        read_status_output,
        MESSAGE_ID_MARKER,
    )


def test_attachment_filename_or_path_is_not_exposed():
    assert_marker_absent(
        attachment_output,
        ATTACHMENT_PATH_MARKER,
    )


def test_skipped_filename_or_path_is_not_exposed():
    assert_marker_absent(
        mailbox_output,
        SKIPPED_PATH_MARKER,
    )


def test_processed_document_path_is_not_exposed():
    assert_marker_absent(
        mailbox_output,
        PROCESSED_PATH_MARKER,
    )


def test_raw_ocr_text_is_not_exposed():
    assert_marker_absent(
        mailbox_output,
        OCR_MARKER,
    )


def test_extracted_value_is_not_exposed():
    assert_marker_absent(
        mailbox_output,
        EXTRACTED_MARKER,
    )


def test_source_text_is_not_exposed():
    assert_marker_absent(
        mailbox_output,
        SOURCE_TEXT_MARKER,
    )


def test_field_evidence_value_is_not_exposed():
    assert_marker_absent(
        mailbox_output,
        EVIDENCE_MARKER,
    )


def test_raw_mailbox_error_is_not_exposed():
    assert_marker_absent(
        mailbox_output,
        MAILBOX_ERROR_MARKER,
    )


def test_raw_provider_diagnostic_is_not_exposed():
    assert_marker_absent(
        lambda: graph_connection_failure_output(
            RuntimeError(
                PROVIDER_MARKER
            )
        ),
        PROVIDER_MARKER,
    )


def test_credential_like_value_is_not_exposed():
    assert_marker_absent(
        mailbox_output,
        CREDENTIAL_MARKER,
    )


def test_graph_connection_retains_safe_counts():
    output, escaped = graph_connection_output()

    assert escaped is False
    assert "Connection successful: True" in output
    assert "Messages checked: 1" in output
    assert "Unread messages: 1" in output
    assert "Messages with attachments: 1" in output
    assert "Status: completed" in output


def test_graph_boundary_category_is_retained():
    output, escaped = graph_connection_failure_output(
        GraphRequestError()
    )

    assert escaped is False
    assert "Connection successful: False" in output
    assert "Status: graph_request_failed" in output


def test_attachment_diagnostic_retains_safe_counts():
    output, escaped = attachment_output()

    assert escaped is False
    assert "Messages checked: 1" in output
    assert "Messages with attachments: 1" in output
    assert "Attachments downloaded: 1" in output
    assert "Skipped/errors: 0" in output
    assert "Status: completed" in output


def test_read_status_retains_safe_counts():
    output, escaped = read_status_output()

    assert escaped is False
    assert "Messages checked: 2" in output
    assert "Read messages: 1" in output
    assert "Unread messages: 1" in output
    assert "Status: completed" in output


def test_mailbox_diagnostic_retains_safe_counts_and_metadata():
    output, escaped = mailbox_output()

    assert escaped is False
    assert "Messages checked : 1" in output
    assert "Files downloaded : 1" in output
    assert "Files processed  : 1" in output
    assert "Files skipped    : 1" in output
    assert "Human review     : 1" in output
    assert "Errors           : 2" in output
    assert "Document type: authorization" in output
    assert "Classification confidence: 91.0%" in output
    assert "Minimum field confidence: 82.0%" in output
    assert "Field count: 1" in output
    assert "Service-line count: 0" in output
    assert "Validation-action count: 1" in output
    assert "Business-rule-action count: 1" in output
    assert "Review status: human review recommended" in output
    assert "Review required: True" in output
    assert "Review-reason count: 1" in output
    assert "Status            : completed_with_errors" in output


def test_attachment_failure_is_sanitized():
    output, escaped = attachment_failure_output()

    assert escaped is False
    assert PROVIDER_MARKER not in output
    assert "Skipped/errors: 1" in output
    assert "Status: attachment_diagnostic_failed" in output


def test_read_status_failure_is_sanitized():
    output, escaped = read_status_failure_output()

    assert escaped is False
    assert PROVIDER_MARKER not in output
    assert "Messages checked: 0" in output
    assert "Status: read_status_diagnostic_failed" in output


def test_mailbox_top_level_failure_is_sanitized():
    output, escaped = mailbox_failure_output()

    assert escaped is False
    assert CREDENTIAL_MARKER not in output
    assert "Errors           : 1" in output
    assert "Status            : completed_with_errors" in output


def run_test(
    name,
    operation,
):
    try:
        operation()
        print(
            f"PASSED: {name}"
        )
        return True
    except Exception as error:
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )
        return False


def main():
    tests = [
        ("subject suppressed", test_subject_is_not_exposed),
        ("sender suppressed", test_sender_address_is_not_exposed),
        ("received metadata suppressed", test_received_metadata_is_not_exposed),
        ("message ID suppressed", test_message_id_is_not_exposed),
        ("attachment path suppressed", test_attachment_filename_or_path_is_not_exposed),
        ("skipped path suppressed", test_skipped_filename_or_path_is_not_exposed),
        ("processed path suppressed", test_processed_document_path_is_not_exposed),
        ("raw OCR suppressed", test_raw_ocr_text_is_not_exposed),
        ("extracted value suppressed", test_extracted_value_is_not_exposed),
        ("source text suppressed", test_source_text_is_not_exposed),
        ("field evidence suppressed", test_field_evidence_value_is_not_exposed),
        ("mailbox error suppressed", test_raw_mailbox_error_is_not_exposed),
        ("provider diagnostic suppressed", test_raw_provider_diagnostic_is_not_exposed),
        ("credential-like value suppressed", test_credential_like_value_is_not_exposed),
        ("connection safe counts", test_graph_connection_retains_safe_counts),
        ("Graph category retained", test_graph_boundary_category_is_retained),
        ("attachment safe counts", test_attachment_diagnostic_retains_safe_counts),
        ("read-status safe counts", test_read_status_retains_safe_counts),
        ("mailbox safe counts", test_mailbox_diagnostic_retains_safe_counts_and_metadata),
        ("attachment failure sanitized", test_attachment_failure_is_sanitized),
        ("read-status failure sanitized", test_read_status_failure_is_sanitized),
        ("mailbox failure sanitized", test_mailbox_top_level_failure_is_sanitized),
    ]

    passed = 0
    failed = 0

    for name, operation in tests:
        if run_test(
            name,
            operation,
        ):
            passed += 1
        else:
            failed += 1

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
        "Live integrations: not called"
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
