import inspect

from src.models.smartsheet_destination_validation import (
    SmartsheetDestinationValidationResult,
)
from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)
from src.services.mailbox_complete_review_smartsheet_service import (
    MailboxCompleteReviewSmartsheetService,
)
from src.services.mailbox_full_review_orchestration_service import (
    MailboxFullReviewOrchestrationService,
)
from src.services.review_decision_service import (
    ReviewDecisionService,
)
from src.services.review_output_service import (
    ReviewField,
    ReviewOutput,
)
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionService,
)
from src.services.smartsheet_reviewed_write_service import (
    SmartsheetReviewedWriteResult,
)
from src.ui.mailbox_full_review_command import (
    build_argument_parser,
)


class RecordingDestinationValidationService:
    def __init__(self, *, ready=True):
        self.ready = ready
        self.calls = []

    def validate(
        self,
        *,
        mapping,
        available_columns,
        available_column_types=None,
        available_system_column_types=None,
    ):
        self.calls.append(
            {
                "mapping": mapping,
                "available_columns": available_columns,
            }
        )

        return SmartsheetDestinationValidationResult(
            column_ids=(
                {
                    name: index + 1
                    for index, name in enumerate(
                        mapping.values
                    )
                }
                if self.ready
                else {}
            ),
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


class RecordingWriteService:
    def __init__(self):
        self.calls = []

    def write(
        self,
        *,
        mapping,
        destination_validation,
        attachment_source_path=None,
    ):
        self.calls.append(
            {
                "mapping": mapping,
                "destination_validation": (
                    destination_validation
                ),
                "attachment_supplied": (
                    attachment_source_path is not None
                ),
            }
        )

        return SmartsheetReviewedWriteResult(
            written=True,
            column_count=len(mapping.values),
            attachment_written=False,
            success=True,
            status="written",
        )


def build_review_output(*, needs_human_review=False):
    return ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_confidence=0.94,
        fields=[
            ReviewField(
                name="authorization_number",
                value="SYNTHETIC-AUTH",
                confidence=0.93,
                source_text="Synthetic supporting evidence",
            ),
            ReviewField(
                name="optional_missing",
                value=None,
                confidence=0.0,
                source_text="",
            ),
        ],
        needs_human_review=needs_human_review,
        review_status=(
            "Human Review Required"
            if needs_human_review
            else "Verified by AI"
        ),
        review_reasons=(
            ["Authorization status is not supported by its source evidence"]
            if needs_human_review
            else []
        ),
    )


def policies():
    return [
        SmartsheetColumnPolicy(
            source_field="authorization_number",
            column_name="Authorization #",
        ),
        SmartsheetColumnPolicy(
            source_field="optional_missing",
            column_name="Optional Missing",
        ),
    ]


def build_submission(*, destination_ready=True):
    destination = RecordingDestinationValidationService(
        ready=destination_ready
    )
    writer = RecordingWriteService()
    service = SmartsheetReviewSubmissionService(
        destination_validation_service=destination,
        write_service=writer,
    )
    return service, destination, writer


def test_submission_requires_no_approval_result():
    service, destination, writer = build_submission()

    result = service.submit(
        review_output=build_review_output(),
        policies=policies(),
        available_columns={},
        run_type="Synthetic Automatic Write",
    )

    assert result.success is True
    assert result.written is True
    assert len(destination.calls) == 1
    assert len(writer.calls) == 1


def test_review_required_mapping_is_write_ready():
    result = SmartsheetReviewRowMappingService().map(
        review_output=build_review_output(
            needs_human_review=True
        ),
        policies=policies(),
        run_type="Synthetic Automatic Write",
    )

    assert result.ready_for_write is True


def test_review_metadata_is_retained_for_review_required_row():
    review_output = build_review_output(
        needs_human_review=True
    )
    result = SmartsheetReviewRowMappingService().map(
        review_output=review_output,
        policies=policies(),
        run_type="Synthetic Automatic Write",
    )

    assert (
        result.values["AI Review Status"]
        == review_output.review_status
    )
    assert (
        result.values["AI Review Reasons"]
        == "Authorization Status: Could not be verified"
    )
    assert result.values["AI Review Required"] == "Yes"


def test_optional_missing_value_is_not_invented():
    result = SmartsheetReviewRowMappingService().map(
        review_output=build_review_output(),
        policies=policies(),
        run_type="Synthetic Automatic Write",
    )

    assert "Optional Missing" not in result.values
    assert result.ready_for_write is True


def test_existing_review_thresholds_are_unchanged():
    assert ReviewDecisionService.AUTO_APPROVE_CLASSIFICATION_THRESHOLD == 0.90
    assert ReviewDecisionService.HUMAN_REVIEW_CLASSIFICATION_THRESHOLD == 0.75
    assert ReviewDecisionService.FIELD_CONFIDENCE_THRESHOLD == 0.85
    assert EvidenceValidationService.SERVICE_LINE_LOW_CONFIDENCE_THRESHOLD == 0.85


def test_classification_confirmation_is_not_a_write_credential():
    parameters = inspect.signature(
        SmartsheetReviewSubmissionService.submit
    ).parameters

    assert "approval_result" not in parameters


def test_mailbox_path_requires_no_approval_flag():
    parameters = inspect.signature(
        MailboxCompleteReviewSmartsheetService.run
    ).parameters
    orchestration_parameters = inspect.signature(
        MailboxFullReviewOrchestrationService.run
    ).parameters

    assert "approve_complete_review" not in parameters
    assert "approve_complete_review" not in orchestration_parameters


def test_cli_has_no_complete_review_approval_option():
    option_strings = {
        option
        for action in build_argument_parser()._actions
        for option in action.option_strings
    }

    assert "--approve-complete-review" not in option_strings


def test_destination_validation_runs_before_write():
    service, destination, writer = build_submission()

    result = service.submit(
        review_output=build_review_output(),
        policies=policies(),
        available_columns={},
        run_type="Synthetic Automatic Write",
    )

    assert result.success is True
    assert len(destination.calls) == 1
    assert len(writer.calls) == 1
    assert (
        writer.calls[0]["destination_validation"]
        is not None
    )


def test_destination_failure_prevents_write():
    service, destination, writer = build_submission(
        destination_ready=False
    )

    result = service.submit(
        review_output=build_review_output(),
        policies=policies(),
        available_columns={},
        run_type="Synthetic Automatic Write",
    )

    assert result.success is False
    assert result.status == "destination_not_ready"
    assert len(destination.calls) == 1
    assert writer.calls == []


def test_mapping_is_explicit_and_not_wholesale_serialization():
    result = SmartsheetReviewRowMappingService().map(
        review_output=build_review_output(),
        policies=policies(),
        run_type="Synthetic Automatic Write",
    )

    forbidden_categories = {
        "Document",
        "ReviewOutput",
        "field_evidence",
        "processing_metrics",
        "credentials",
        "tokens",
        "file_path",
        "cache_metadata",
        "diagnostics",
        "raw_text",
        "source_text",
    }

    assert forbidden_categories.isdisjoint(
        result.values
    )
    assert set(result.values).issubset(
        {
            "Authorization #",
            "AI Review Status",
            "AI Review Required",
            "AI Correction",
            "AI Document Category",
            "AI Document Subtype",
            "AI Review Reasons",
            "Run Type",
            "AI Classification Confidence",
            "AI Minimum Field Confidence",
            "AI Selected Extraction Attempt",
            "AI Extraction Retry Triggered",
            "AI Authorized Units Reconciled",
        }
    )


def test_review_required_row_reaches_writer():
    service, destination, writer = build_submission()

    result = service.submit(
        review_output=build_review_output(
            needs_human_review=True
        ),
        policies=policies(),
        available_columns={},
        run_type="Synthetic Automatic Write",
    )

    assert result.success is True
    assert result.written is True
    assert len(destination.calls) == 1
    assert len(writer.calls) == 1


def test_empty_candidate_fields_are_not_inferred():
    review_output = build_review_output()
    review_output.fields = []

    result = SmartsheetReviewRowMappingService().map(
        review_output=review_output,
        policies=policies(),
        run_type="Synthetic Automatic Write",
    )

    assert "Authorization #" not in result.values
    assert "Optional Missing" not in result.values


TESTS = [
    (
        "submission requires no approval result",
        test_submission_requires_no_approval_result,
    ),
    (
        "review-required mapping is write-ready",
        test_review_required_mapping_is_write_ready,
    ),
    (
        "review metadata is retained",
        test_review_metadata_is_retained_for_review_required_row,
    ),
    (
        "optional missing value is not invented",
        test_optional_missing_value_is_not_invented,
    ),
    (
        "configured review thresholds are unchanged",
        test_existing_review_thresholds_are_unchanged,
    ),
    (
        "classification confirmation is not a write credential",
        test_classification_confirmation_is_not_a_write_credential,
    ),
    (
        "mailbox path requires no approval flag",
        test_mailbox_path_requires_no_approval_flag,
    ),
    (
        "CLI has no complete-review approval option",
        test_cli_has_no_complete_review_approval_option,
    ),
    (
        "destination validation runs before write",
        test_destination_validation_runs_before_write,
    ),
    (
        "destination failure prevents write",
        test_destination_failure_prevents_write,
    ),
    (
        "mapping is explicit and not wholesale",
        test_mapping_is_explicit_and_not_wholesale_serialization,
    ),
    (
        "review-required row reaches writer",
        test_review_required_row_reaches_writer,
    ),
    (
        "empty candidate fields are not inferred",
        test_empty_candidate_fields_are_not_inferred,
    ),
]


passed = 0
failed = 0

print("=" * 60)
print("Testing Automatic Smartsheet Write Boundary")
print("=" * 60)

for name, test in TESTS:
    try:
        test()
        passed += 1
        print(f"PASSED: {name}")
    except Exception as exception:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(exception).__name__}"
        )

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print("Real or mock: Synthetic deterministic/mock")
print("Smartsheet external API: Not called")
print("Microsoft Graph: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("PHI handling: Synthetic metadata and values only")

if failed:
    raise SystemExit(1)
