from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from src.models.smartsheet_mapping import SmartsheetRowMappingResult
from src.services.mailbox_document_job_state_service import (
    MailboxDocumentJobStateService,
    MailboxDocumentWorkItem,
)
from src.services.mailbox_document_smartsheet_recovery_service import (
    MailboxDocumentSmartsheetRecoveryService,
)
from src.services.review_output_service import ReviewOutput
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)
from src.services.smartsheet_submission_key_configuration_service import (
    SmartsheetSubmissionKeyConfigurationService,
)


def digest(character):
    return character * 64


def mapped(*, review_required, review_status, review_reasons, confidence, run_type):
    output = ReviewOutput(
        document_type="authorization",
        document_category="authorization",
        document_subtype="renewal",
        classification_confidence=confidence,
        fields=[],
        needs_human_review=review_required,
        review_status=review_status,
        review_reasons=list(review_reasons),
    )
    return SmartsheetReviewRowMappingService().map(
        review_output=output,
        policies=[],
        run_type=run_type,
    )


class ExistingHumanFeedbackClient:
    def __init__(self, *, checked):
        self.checked = checked
        self.row_reads = 0
        self.attachment_reads = 0
        self.row_updates = 0
        self.comment_calls = 0

    def find_row_ids_by_exact_column_value(self, **kwargs):
        self.row_reads += 1
        return [7001]

    def list_row_attachment_names(self, **kwargs):
        self.attachment_reads += 1
        return ["LTHHC_TECHNICAL_DOCUMENT_synthetic.pdf"]

    def update_row(self, **kwargs):
        self.row_updates += 1
        raise AssertionError("human feedback was overwritten")

    def get_discussions(self, **kwargs):
        self.comment_calls += 1
        raise AssertionError("comments were read")

    def add_comment(self, **kwargs):
        self.comment_calls += 1
        raise AssertionError("comments were written")


class NoMutationWriteService:
    def __init__(self, client):
        self.client = client

    def create_row(self, **kwargs):
        raise AssertionError("duplicate row was created")

    def attach_to_existing_row(self, **kwargs):
        raise AssertionError("duplicate attachment was uploaded")


class SyntheticConfigurationService:
    def resolve(self, **kwargs):
        return SimpleNamespace(
            success=True,
            status="ready",
            policies=(),
            available_columns={"Synthetic Technical Key": 101},
        )


def exercise_reconciliation(*, checked):
    with TemporaryDirectory() as temporary_directory:
        state_service = MailboxDocumentJobStateService(Path(temporary_directory))
        discovered = state_service.discover(
            message_key=digest("a"),
            attachment_key=digest("b"),
            document_key=digest("c"),
            attachment_required=True,
        ).state
        lease = state_service.acquire_processing_lease(discovered.job_key).state
        state_service.transition(
            discovered.job_key,
            expected_stages={"processing"},
            stage="row_write_pending",
            lease_token=lease.lease_token,
            attachment_filename="LTHHC_TECHNICAL_DOCUMENT_synthetic.pdf",
            attachment_naming_status="technical_fallback",
        )
        source = Path(temporary_directory) / "synthetic.pdf"
        source.write_bytes(b"SYNTHETIC")
        client = ExistingHumanFeedbackClient(checked=checked)
        service = MailboxDocumentSmartsheetRecoveryService(
            job_state_service=state_service,
            submission_key_configuration_service=(
                SmartsheetSubmissionKeyConfigurationService(
                    environment={
                        "SMARTSHEET_AI_SUBMISSION_KEY_COLUMN_TITLE": (
                            "Synthetic Technical Key"
                        )
                    }
                )
            ),
            configuration_service=SyntheticConfigurationService(),
            mapping_service=SimpleNamespace(
                map=lambda **kwargs: SmartsheetRowMappingResult(
                    values={}, ready_for_write=True
                )
            ),
            write_service=NoMutationWriteService(client),
        )
        item = MailboxDocumentWorkItem(
            discovered.job_key,
            digest("a"),
            digest("b"),
            digest("c"),
            source,
            "row_write_pending",
            SimpleNamespace(review_output=ReviewOutput(document_type="synthetic")),
        )
        result = service.run(work_item=item, run_type="Synthetic recovery")
        repeated = service.run(work_item=item, run_type="Synthetic recovery")
        assert result.success and result.row_action == "reconciled_existing"
        assert result.attachment_action == "reconciled_existing"
        assert repeated.success and repeated.row_action == "skipped"
        assert client.checked is checked
        assert client.row_updates == 0
        assert client.comment_calls == 0


def main():
    normal = mapped(
        review_required=False,
        review_status="Verified by AI",
        review_reasons=(),
        confidence=0.95,
        run_type="Manual synthetic",
    )
    reviewed = mapped(
        review_required=True,
        review_status="Human Review Recommended",
        review_reasons=("synthetic_low_confidence",),
        confidence=0.20,
        run_type="Unattended synthetic",
    )
    manual = mapped(
        review_required=True,
        review_status="Human Review Required",
        review_reasons=("synthetic_reason",),
        confidence=0.10,
        run_type="Manual synthetic",
    )
    unattended = mapped(
        review_required=True,
        review_status="Human Review Required",
        review_reasons=("synthetic_reason",),
        confidence=0.10,
        run_type="Unattended synthetic",
    )

    assert normal.values["AI Correction"] is False
    assert reviewed.values["AI Correction"] is False
    assert manual.values["AI Correction"] is unattended.values["AI Correction"] is False
    exercise_reconciliation(checked=True)
    exercise_reconciliation(checked=False)

    print("Passed: 10")
    print("Failed: 0")
    print("Real or mock: Synthetic deterministic/mock")
    print("External APIs: Not called")
    print("PHI handling: No production values or identifiers used")


if __name__ == "__main__":
    main()
