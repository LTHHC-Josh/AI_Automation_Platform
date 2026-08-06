from pathlib import Path

from src.models.document import Document
from src.services.review_confirmation_submission_service import (
    ReviewConfirmationSubmissionResult,
)
from src.services.review_output_service import ReviewOutput
from src.ui.classification_review_interaction import (
    ClassificationReviewInteraction,
)


passed = 0
failed = 0

TIMESTAMP = "2026-08-06T19:00:00Z"


class InputSequence:
    def __init__(
        self,
        values,
    ):
        self.values = list(
            values
        )
        self.prompts = []

    def __call__(
        self,
        prompt,
    ):
        self.prompts.append(
            prompt
        )

        if not self.values:
            raise AssertionError(
                "Unexpected input request."
            )

        return self.values.pop(
            0
        )


class OutputRecorder:
    def __init__(self):
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


class RecordingSubmissionService:
    def __init__(
        self,
        *,
        success=True,
        status="stored",
    ):
        self.call_count = 0
        self.arguments = None
        self.success = success
        self.status = status

    def submit(
        self,
        *,
        document,
        confirmed_category,
        confirmed_subtype,
        reviewer_confirmation_status,
        created_at=None,
    ):
        self.call_count += 1

        self.arguments = {
            "document": document,
            "confirmed_category": confirmed_category,
            "confirmed_subtype": confirmed_subtype,
            "reviewer_confirmation_status": (
                reviewer_confirmation_status
            ),
            "created_at": created_at,
        }

        return ReviewConfirmationSubmissionResult(
            fingerprint="a" * 64,
            byte_count=20,
            success=self.success,
            status=self.status,
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


def build_document():
    document = Document(
        file_path=Path(
            "sensitive-patient-name.pdf"
        )
    )

    document.raw_text = (
        "Synthetic OCR content that must not be displayed."
    )

    document.extracted_data = {
        "patient_name": "Synthetic Patient",
        "authorization_number": "SYNTHETIC-AUTH",
    }

    document.review_output = ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_reason=(
            "Synthetic reason containing sensitive evidence."
        ),
        classification_confidence=0.88,
        needs_human_review=True,
        review_status="Human Review Recommended",
    )

    return document


def build_interaction(
    inputs,
    submission_service=None,
):
    input_reader = InputSequence(
        inputs
    )
    output_writer = OutputRecorder()

    interaction = (
        ClassificationReviewInteraction(
            submission_service=(
                submission_service
                or RecordingSubmissionService()
            ),
            input_reader=input_reader,
            output_writer=output_writer,
        )
    )

    return (
        interaction,
        input_reader,
        output_writer,
    )


def test_confirm_uses_predicted_labels():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["1"],
        submission,
    )

    document = build_document()

    result = interaction.run(
        document=document,
        created_at=TIMESTAMP,
    )

    assert result.success is True
    assert submission.call_count == 1

    assert (
        submission.arguments[
            "confirmed_category"
        ]
        == "authorization"
    )

    assert (
        submission.arguments[
            "confirmed_subtype"
        ]
        == "renewal"
    )

    assert (
        submission.arguments[
            "reviewer_confirmation_status"
        ]
        == "confirmed"
    )


def test_correction_uses_entered_labels():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        [
            "2",
            "authorization",
            "initial",
        ],
        submission,
    )

    result = interaction.run(
        document=build_document(),
        created_at=TIMESTAMP,
    )

    assert result.success is True
    assert submission.call_count == 1

    assert (
        submission.arguments[
            "confirmed_category"
        ]
        == "authorization"
    )

    assert (
        submission.arguments[
            "confirmed_subtype"
        ]
        == "initial"
    )

    assert (
        submission.arguments[
            "reviewer_confirmation_status"
        ]
        == "corrected"
    )


def test_correction_input_is_trimmed():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        [
            "2",
            " authorization ",
            " renewal ",
        ],
        submission,
    )

    interaction.run(
        document=build_document()
    )

    assert (
        submission.arguments[
            "confirmed_category"
        ]
        == "authorization"
    )

    assert (
        submission.arguments[
            "confirmed_subtype"
        ]
        == "renewal"
    )


def test_cancel_does_not_submit():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["0"],
        submission,
    )

    result = interaction.run(
        document=build_document()
    )

    assert result.success is False
    assert result.status == "cancelled"
    assert submission.call_count == 0


def test_invalid_selection_does_not_submit():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["9"],
        submission,
    )

    result = interaction.run(
        document=build_document()
    )

    assert result.success is False
    assert result.status == "invalid_selection"
    assert submission.call_count == 0


def test_blank_correction_is_rejected():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        [
            "2",
            "",
            "renewal",
        ],
        submission,
    )

    result = interaction.run(
        document=build_document()
    )

    assert result.success is False

    assert (
        result.status
        == "correction_labels_required"
    )

    assert submission.call_count == 0


def test_invalid_document_is_rejected():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        [],
        submission,
    )

    result = interaction.run(
        document={}
    )

    assert result.success is False
    assert result.status == "invalid_document"
    assert submission.call_count == 0


def test_missing_review_output_is_rejected():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        [],
        submission,
    )

    document = Document(
        file_path=Path(
            "synthetic.pdf"
        )
    )

    result = interaction.run(
        document=document
    )

    assert result.success is False
    assert result.status == "review_output_missing"
    assert submission.call_count == 0


def test_output_contains_only_safe_classification_metadata():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        output,
    ) = build_interaction(
        ["1"],
        submission,
    )

    document = build_document()

    interaction.run(
        document=document
    )

    rendered = "\n".join(
        output.lines
    )

    assert "authorization" in rendered
    assert "renewal" in rendered
    assert "0.88" in rendered

    prohibited_values = {
        str(document.file_path),
        "sensitive-patient-name",
        document.raw_text,
        "Synthetic Patient",
        "SYNTHETIC-AUTH",
        document.review_output.classification_reason,
    }

    assert all(
        value not in rendered
        for value in prohibited_values
    )


def test_entered_correction_is_not_echoed():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        output,
    ) = build_interaction(
        [
            "2",
            "synthetic-private-category",
            "synthetic-private-subtype",
        ],
        submission,
    )

    interaction.run(
        document=build_document()
    )

    rendered = "\n".join(
        output.lines
    )

    assert (
        "synthetic-private-category"
        not in rendered
    )

    assert (
        "synthetic-private-subtype"
        not in rendered
    )


def test_submission_failure_status_is_preserved():
    submission = RecordingSubmissionService(
        success=False,
        status="feedback_invalid",
    )

    (
        interaction,
        _,
        output,
    ) = build_interaction(
        ["1"],
        submission,
    )

    result = interaction.run(
        document=build_document()
    )

    assert result.success is False
    assert result.status == "feedback_invalid"

    assert (
        "Submission status: feedback_invalid"
        in output.lines
    )


def test_interaction_does_not_mutate_document():
    submission = RecordingSubmissionService()

    (
        interaction,
        _,
        _,
    ) = build_interaction(
        ["1"],
        submission,
    )

    document = build_document()
    original_review_output = document.review_output
    original_extracted_data = dict(
        document.extracted_data
    )

    interaction.run(
        document=document
    )

    assert (
        document.review_output
        is original_review_output
    )

    assert (
        document.extracted_data
        == original_extracted_data
    )


print("=" * 60)
print("Testing Classification Review Interaction")
print("=" * 60)

run_test(
    "confirm uses predicted labels",
    test_confirm_uses_predicted_labels,
)
run_test(
    "correction uses entered labels",
    test_correction_uses_entered_labels,
)
run_test(
    "correction input is trimmed",
    test_correction_input_is_trimmed,
)
run_test(
    "cancel does not submit",
    test_cancel_does_not_submit,
)
run_test(
    "invalid selection does not submit",
    test_invalid_selection_does_not_submit,
)
run_test(
    "blank correction is rejected",
    test_blank_correction_is_rejected,
)
run_test(
    "invalid document is rejected",
    test_invalid_document_is_rejected,
)
run_test(
    "missing review output is rejected",
    test_missing_review_output_is_rejected,
)
run_test(
    "output contains only safe metadata",
    test_output_contains_only_safe_classification_metadata,
)
run_test(
    "entered correction is not echoed",
    test_entered_correction_is_not_echoed,
)
run_test(
    "submission failure is preserved",
    test_submission_failure_status_is_preserved,
)
run_test(
    "document is not mutated",
    test_interaction_does_not_mutate_document,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic UI-boundary test")
print("Document processing: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("Microsoft Graph: Not called")
print("Smartsheet: Not called")
print("External integration: Not called")
print(
    "PHI handling: Only category, subtype, confidence, "
    "and submission status were displayed"
)

if failed:
    raise SystemExit(1)
