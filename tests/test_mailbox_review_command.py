from src.services.mailbox_review_orchestration_service import (
    MailboxReviewOrchestrationResult,
)
from src.ui.mailbox_review_command import (
    MailboxReviewCommand,
    build_argument_parser,
)


passed = 0
failed = 0

TIMESTAMP = "2026-08-06T21:00:00Z"


class OutputRecorder:
    def __init__(self):
        self.lines = []

    def __call__(
        self,
        value,
    ):
        self.lines.append(
            str(value)
        )


class RecordingOrchestrationService:
    def __init__(
        self,
        *,
        result,
    ):
        self.result = result
        self.call_count = 0
        self.top_values = []
        self.created_at_values = []

    def run(
        self,
        *,
        top=10,
        created_at=None,
    ):
        self.call_count += 1
        self.top_values.append(
            top
        )
        self.created_at_values.append(
            created_at
        )

        return self.result


def successful_result():
    return MailboxReviewOrchestrationResult(
        message_count=2,
        document_count=3,
        submitted_count=2,
        cancelled_count=1,
        failed_count=0,
        success=True,
        status="completed_with_cancellations",
    )


def failed_result():
    return MailboxReviewOrchestrationResult(
        message_count=1,
        document_count=1,
        submitted_count=0,
        cancelled_count=0,
        failed_count=1,
        success=False,
        status="completed_with_failures",
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


def test_command_calls_orchestration_once():
    orchestration = RecordingOrchestrationService(
        result=successful_result()
    )
    output = OutputRecorder()

    command = MailboxReviewCommand(
        orchestration_service=orchestration,
        output_writer=output,
    )

    result = command.run(
        top=4,
        created_at=TIMESTAMP,
    )

    assert result.success is True
    assert orchestration.call_count == 1
    assert orchestration.top_values == [4]

    assert orchestration.created_at_values == [
        TIMESTAMP
    ]


def test_successful_summary_contains_safe_fields():
    output = OutputRecorder()

    command = MailboxReviewCommand(
        orchestration_service=(
            RecordingOrchestrationService(
                result=successful_result()
            )
        ),
        output_writer=output,
    )

    command.run()

    rendered = "\n".join(
        output.lines
    )

    expected_values = {
        "Messages   : 2",
        "Documents  : 3",
        "Submitted  : 2",
        "Cancelled  : 1",
        "Failed     : 0",
        "Success    : True",
        (
            "Status     : "
            "completed_with_cancellations"
        ),
    }

    assert all(
        value in rendered
        for value in expected_values
    )


def test_failed_summary_is_preserved():
    output = OutputRecorder()

    command = MailboxReviewCommand(
        orchestration_service=(
            RecordingOrchestrationService(
                result=failed_result()
            )
        ),
        output_writer=output,
    )

    result = command.run()

    assert result.success is False

    assert (
        "Status     : completed_with_failures"
        in output.lines
    )


def test_output_excludes_sensitive_terms():
    output = OutputRecorder()

    command = MailboxReviewCommand(
        orchestration_service=(
            RecordingOrchestrationService(
                result=successful_result()
            )
        ),
        output_writer=output,
    )

    command.run()

    rendered = "\n".join(
        output.lines
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


def test_parser_defaults_top_to_ten():
    parser = build_argument_parser()

    arguments = parser.parse_args(
        []
    )

    assert arguments.top == 10
    assert arguments.created_at is None


def test_parser_accepts_explicit_values():
    parser = build_argument_parser()

    arguments = parser.parse_args(
        [
            "--top",
            "5",
            "--created-at",
            TIMESTAMP,
        ]
    )

    assert arguments.top == 5
    assert arguments.created_at == TIMESTAMP


def test_command_does_not_print_created_at():
    output = OutputRecorder()

    command = MailboxReviewCommand(
        orchestration_service=(
            RecordingOrchestrationService(
                result=successful_result()
            )
        ),
        output_writer=output,
    )

    command.run(
        created_at=TIMESTAMP
    )

    rendered = "\n".join(
        output.lines
    )

    assert TIMESTAMP not in rendered


def test_command_does_not_construct_mailbox_data():
    orchestration = RecordingOrchestrationService(
        result=successful_result()
    )

    command = MailboxReviewCommand(
        orchestration_service=orchestration,
        output_writer=OutputRecorder(),
    )

    command.run()

    assert orchestration.call_count == 1


print("=" * 60)
print("Testing Mailbox Review Command")
print("=" * 60)

run_test(
    "command calls orchestration once",
    test_command_calls_orchestration_once,
)
run_test(
    "successful summary contains safe fields",
    test_successful_summary_contains_safe_fields,
)
run_test(
    "failed summary is preserved",
    test_failed_summary_is_preserved,
)
run_test(
    "output excludes sensitive terms",
    test_output_excludes_sensitive_terms,
)
run_test(
    "parser defaults top to ten",
    test_parser_defaults_top_to_ten,
)
run_test(
    "parser accepts explicit values",
    test_parser_accepts_explicit_values,
)
run_test(
    "created timestamp is not printed",
    test_command_does_not_print_created_at,
)
run_test(
    "command does not construct mailbox data",
    test_command_does_not_construct_mailbox_data,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Mock command-boundary test")
print("Orchestration service: Mocked")
print("Microsoft Graph: Not called")
print("Attachment download: Not called")
print("Document processing: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("Smartsheet: Not called")
print("External integration: Not called")
print(
    "PHI handling: Only counts, success, and status "
    "were displayed"
)

if failed:
    raise SystemExit(1)
