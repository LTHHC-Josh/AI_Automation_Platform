from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)
from src.services.complete_review_approval_service import (
    CompleteReviewApprovalResult,
)
from src.services.review_output_service import (
    ReviewOutput,
)
from src.services.smartsheet_destination_validation_service import (
    SmartsheetDestinationValidationService,
)
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)
from src.services.smartsheet_reviewed_write_service import (
    SmartsheetReviewedWriteService,
)


@dataclass(frozen=True)
class SmartsheetReviewSubmissionResult:
    """
    PHI-safe result from one approval-gated Smartsheet submission.

    The result excludes mapped values, source_text, OCR text,
    document paths, filenames, row payloads, and patient data.
    """

    written: bool
    success: bool
    status: str


class SmartsheetReviewSubmissionService:
    """
    Coordinates the existing approved Smartsheet write boundaries.

    Required order:

    complete human-review approval
    -> logical mapping
    -> destination validation
    -> reviewed write

    This service does not perform OCR, classification, extraction,
    deterministic validation, business rules, or human review.

    It does not treat classification confirmation as permission
    to write.
    """

    def __init__(
        self,
        *,
        mapping_service=None,
        destination_validation_service=None,
        write_service=None,
    ) -> None:
        self.mapping_service = (
            mapping_service
            or SmartsheetReviewRowMappingService()
        )
        self.destination_validation_service = (
            destination_validation_service
            or SmartsheetDestinationValidationService()
        )
        self.write_service = (
            write_service
            or SmartsheetReviewedWriteService()
        )

    def submit(
        self,
        *,
        review_output: ReviewOutput,
        approval_result: CompleteReviewApprovalResult,
        policies: list[SmartsheetColumnPolicy],
        available_columns: dict[str, int],
        attachment_source_path: str | Path | None = None,
        run_type: str = "",
    ) -> SmartsheetReviewSubmissionResult:
        """
        Submit one completely reviewed and explicitly approved
        review output through the existing write boundaries.
        """

        if not isinstance(
            review_output,
            ReviewOutput,
        ):
            return self._failure(
                "invalid_review_output"
            )

        if not isinstance(
            approval_result,
            CompleteReviewApprovalResult,
        ):
            return self._failure(
                "invalid_approval_result"
            )

        if (
            not approval_result.success
            or not approval_result.approved
            or approval_result.status != "approved"
        ):
            return self._failure(
                "complete_review_not_approved"
            )

        mapping = self.mapping_service.map(
            review_output=review_output,
            policies=policies,
            complete_review_approved=True,
            run_type=run_type,
        )

        if not mapping.ready_for_write:
            return self._failure(
                "mapping_not_ready"
            )

        destination_validation = (
            self.destination_validation_service.validate(
                mapping=mapping,
                available_columns=available_columns,
            )
        )

        if not destination_validation.ready_for_write:
            return self._failure(
                "destination_not_ready"
            )

        write_result = self.write_service.write(
            mapping=mapping,
            destination_validation=destination_validation,
            attachment_source_path=attachment_source_path,
        )

        if not write_result.success:
            return self._failure(
                write_result.status
            )

        if not write_result.written:
            return self._failure(
                "write_not_completed"
            )

        return SmartsheetReviewSubmissionResult(
            written=True,
            success=True,
            status=write_result.status,
        )

    @staticmethod
    def _failure(
        status: Any,
    ) -> SmartsheetReviewSubmissionResult:
        normalized_status = str(
            status
            or "submission_failed"
        ).strip()

        return SmartsheetReviewSubmissionResult(
            written=False,
            success=False,
            status=normalized_status,
        )
