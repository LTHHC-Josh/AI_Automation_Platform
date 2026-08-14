from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.review_output_service import (
    ReviewOutput,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionResult,
    SmartsheetReviewSubmissionService,
)
from src.ui.complete_review_approval_interaction import (
    CompleteReviewApprovalInteraction,
)


@dataclass(frozen=True)
class CompleteReviewSmartsheetWorkflowResult:
    """
    PHI-safe result from one complete-review-to-Smartsheet workflow.

    The result excludes review values, source_text, OCR text,
    filenames, paths, mapped payloads, row IDs, and patient data.
    """

    approved: bool
    written: bool
    success: bool
    status: str


class CompleteReviewSmartsheetWorkflowService:
    """
    Preserves the separate optional human complete-review workflow.

    This is not the normal production write path. Production mailbox
    processing uses automatic Smartsheet submission without approval.

    Order:

    complete-review interaction
    -> explicit CompleteReviewApprovalResult
    -> optional manually initiated Smartsheet submission

    This service does not rerun OCR, Ollama, extraction, deterministic
    validation, business rules, or review-output construction.

    It does not treat classification confirmation as approval.
    """

    def __init__(
        self,
        *,
        review_interaction: (
            CompleteReviewApprovalInteraction
            | None
        ) = None,
        submission_service: (
            SmartsheetReviewSubmissionService
            | None
        ) = None,
    ) -> None:
        self.review_interaction = (
            review_interaction
            or CompleteReviewApprovalInteraction()
        )

        self.submission_service = (
            submission_service
            or SmartsheetReviewSubmissionService()
        )

    def run(
        self,
        *,
        review_output: ReviewOutput,
        policies: list[SmartsheetColumnPolicy],
        available_columns: dict[str, int],
        approve_complete_review: bool = False,
        attachment_source_path: str | Path | None = None,
        run_type: str = "",
    ) -> CompleteReviewSmartsheetWorkflowResult:
        """
        Run one explicit approval decision and submit only when the
        complete review is successfully approved.
        """

        if not isinstance(
            review_output,
            ReviewOutput,
        ):
            return self._failure(
                "invalid_review_output"
            )

        approval_result = (
            self.review_interaction.run(
                review_output=review_output,
                approve_without_prompt=(
                    approve_complete_review
                ),
            )
        )

        if (
            not approval_result.success
            or not approval_result.approved
            or approval_result.status != "approved"
        ):
            return CompleteReviewSmartsheetWorkflowResult(
                approved=False,
                written=False,
                success=(
                    approval_result.success
                    and approval_result.status
                    in {
                        "rejected",
                        "cancelled",
                    }
                ),
                status=approval_result.status,
            )

        submission_result = (
            self.submission_service.submit(
                review_output=review_output,
                policies=policies,
                available_columns=available_columns,
                attachment_source_path=attachment_source_path,
                run_type=run_type,
            )
        )

        return CompleteReviewSmartsheetWorkflowResult(
            approved=True,
            written=bool(
                submission_result.written
            ),
            success=bool(
                submission_result.success
            ),
            status=str(
                submission_result.status
            ),
        )

    @staticmethod
    def _failure(
        status: Any,
    ) -> CompleteReviewSmartsheetWorkflowResult:
        return CompleteReviewSmartsheetWorkflowResult(
            approved=False,
            written=False,
            success=False,
            status=str(
                status
                or "workflow_failed"
            ),
        )
