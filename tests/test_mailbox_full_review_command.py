from src.services.mailbox_full_review_orchestration_service import (
    MailboxFullReviewOrchestrationResult,
)
from src.ui.mailbox_full_review_command import (
    MailboxFullReviewCommand,
    build_argument_parser,
)


passed = 0
failed = 0

TIMESTAMP = "2026-08-07T16:30:00Z"


class OutputRecorder:
    def __init__(
        self,
    ):
        self.lines = []

    def __call__(
        self,
        value,
    ):
        self.lines.append(
            str(
                value
            )
        )


class RecordingOrchestrationService:
    def __init__(
        self,
        *,
        result,
    ):
        self.result = result
        self.calls = []

    def run(
        self,
        *,
        top=10,
        created_at=None,
        skip_classification_review=False,
        run_type="",
    ):
        self.calls.append(
            {
                "top": top,
                "created_at": created_at,
                "skip_classification_review": (
                    skip_classification_review
                ),
                "run_type": run_type,
            }
        )

        return self.result


def successful_result():
    return MailboxFullReviewOrchestrationResult(
        message_count=2,
        document_count=3,
        classification_submitted_count=3,
        classification_cancelled_count=0,
        approved_count=0,
        written_count=2,
        rejected_count=0,
        complete_review_cancelled_count=0,
        failed_count=0,
        success=True,
        status="completed",
    )


def failed_result():
    return MailboxFullReviewOrchestrationResult(
        message_count=1,
        document_count=1,
        classification_submitted_count=1,
        classification_cancelled_count=0,
        approved_count=0,
        written_count=0,
        rejected_count=0,
        complete_review_cancelled_count=0,
        failed_count=1,
        success=False,
        status="completed_with_failures",
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


def test_command_calls_full_orchestration_once():
    orchestration = (
        RecordingOrchestrationService(
            result=successful_result()
        )
    )

    command = MailboxFullReviewCommand(
        orchestration_service=orchestration,
        output_writer=OutputRecorder(),
    )

    result = command.run(
        top=4,
        created_at=TIMESTAMP,
    )

    assert result.success is True

    assert orchestration.calls == [
        {
            "top": 4,
            "created_at": TIMESTAMP,
            "skip_classification_review": False,
            "run_type": "",
        }
    ]


def test_successful_summary_contains_safe_counts():
    output = OutputRecorder()

    command = MailboxFullReviewCommand(
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

    expected = {
        "Messages                  : 2",
        "Documents                 : 3",
        "Classification submitted  : 3",
        "Classification cancelled  : 0",
        "Written                   : 2",
        "Failed                    : 0",
        "Success                   : True",
        (
            "Status                    : "
            "completed"
        ),
    }

    assert all(
        value in rendered
        for value in expected
    )


def test_failed_summary_is_preserved():
    output = OutputRecorder()

    command = MailboxFullReviewCommand(
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
        "Status                    : "
        "completed_with_failures"
        in output.lines
    )


def test_output_excludes_sensitive_terms():
    output = OutputRecorder()

    command = MailboxFullReviewCommand(
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
        "payload",
        "row_id",
    }

    assert all(
        term not in rendered
        for term in prohibited_terms
    )

    assert TIMESTAMP not in rendered


def test_parser_requires_run_type():
    parser = build_argument_parser()

    try:
        parser.parse_args(
            []
        )
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError(
            "--run-type must be required."
        )

def test_parser_accepts_explicit_values():
    parser = build_argument_parser()

    arguments = parser.parse_args(
        [
            "--top",
            "5",
            "--created-at",
            TIMESTAMP,
            "--run-type",
            "Parser explicit values",
        ]
    )

    assert arguments.top == 5
    assert arguments.created_at == TIMESTAMP
    assert (
        arguments.run_type
        == "Parser explicit values"
    )


def test_demo_skip_flag_reaches_orchestration():
    orchestration = RecordingOrchestrationService(
        result=successful_result()
    )

    output = OutputRecorder()

    command = MailboxFullReviewCommand(
        orchestration_service=orchestration,
        output_writer=output,
    )

    result = command.run(
        top=5,
        skip_classification_review=True,
    )

    assert result.success is True

    assert orchestration.calls == [
        {
            "top": 5,
            "created_at": None,
            "skip_classification_review": True,
            "run_type": "",
        }
    ]

    assert (
        "Demo classification review skipped: True"
        in output.lines
    )

    parser = build_argument_parser()

    arguments = parser.parse_args(
        [
            "--top",
            "5",
            "--demo-skip-classification-review",
            "--run-type",
            "Classification review bypass",
        ]
    )

    assert arguments.top == 5
    assert (
        arguments.demo_skip_classification_review
        is True
    )


def test_complete_review_approval_option_is_absent():
    option_strings = {
        option
        for action in build_argument_parser()._actions
        for option in action.option_strings
    }

    assert "--approve-complete-review" not in option_strings


def test_run_type_reaches_orchestration_and_parser():
    orchestration = RecordingOrchestrationService(
        result=successful_result()
    )

    command = MailboxFullReviewCommand(
        orchestration_service=orchestration,
        output_writer=OutputRecorder(),
    )

    result = command.run(
        run_type="Review reason visibility"
    )

    assert result.success is True

    assert (
        orchestration.calls[0][
            "run_type"
        ]
        == "Review reason visibility"
    )

    parser = build_argument_parser()

    arguments = parser.parse_args(
        [
            "--run-type",
            "Classification and review reason columns",
        ]
    )

    assert (
        arguments.run_type
        == "Classification and review reason columns"
    )


def test_command_does_not_construct_workflow_data():
    orchestration = (
        RecordingOrchestrationService(
            result=successful_result()
        )
    )

    command = MailboxFullReviewCommand(
        orchestration_service=orchestration,
        output_writer=OutputRecorder(),
    )

    command.run()

    assert len(
        orchestration.calls
    ) == 1

    assert (
        orchestration.calls[0][
            "skip_classification_review"
        ]
        is False
    )


def test_existing_classification_command_is_not_imported():
    import src.ui.mailbox_full_review_command as module

    names = {
        name
        for name in module.__dict__.keys()
    }

    assert (
        "MailboxReviewCommand"
        not in names
    )


print(
    "=" * 60
)
print(
    "Testing Full Mailbox Review Command"
)
print(
    "=" * 60
)

run_test(
    "command calls full orchestration once",
    test_command_calls_full_orchestration_once,
)

run_test(
    "successful summary contains safe counts",
    test_successful_summary_contains_safe_counts,
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
    "parser requires run type",
    test_parser_requires_run_type,
)

run_test(
    "parser accepts explicit values",
    test_parser_accepts_explicit_values,
)

run_test(
    "demo skip flag reaches orchestration",
    test_demo_skip_flag_reaches_orchestration,
)

run_test(
    "complete review approval option is absent",
    test_complete_review_approval_option_is_absent,
)

run_test(
    "run type reaches orchestration and parser",
    test_run_type_reaches_orchestration_and_parser,
)
run_test(
    "command does not construct workflow data",
    test_command_does_not_construct_workflow_data,
)

run_test(
    "classification-only command remains separate",
    test_existing_classification_command_is_not_imported,
)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Mock command-boundary test"
)
print(
    "Full orchestration service: Mocked"
)
print(
    "Microsoft Graph: Not called"
)
print(
    "Attachment download: Not called"
)
print(
    "Document processing: Not called"
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
    "PHI handling: Only counts, booleans, and statuses displayed"
)

if failed:
    raise SystemExit(1)
