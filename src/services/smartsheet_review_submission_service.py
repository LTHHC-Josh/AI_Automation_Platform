from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
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
    PHI-safe result from one automatic Smartsheet submission.

    The result excludes mapped values, source_text, OCR text,
    document paths, filenames, row payloads, and patient data.
    """

    written: bool
    success: bool
    status: str


class SmartsheetReviewSubmissionService:
    """
    Coordinates the automatic Smartsheet write boundaries.

    Required order:

    logical mapping
    -> destination validation
    -> reviewed write

    This service does not perform OCR, classification, extraction,
    deterministic validation, business rules, or human review.

    Classification confirmation is not accepted as a credential or
    prerequisite. Write eligibility comes from the validated mapping
    and destination-validation contracts.

    A failed attachment after row creation is preserved as
    ``written=True, success=False``. Because this boundary does not
    persist external row references, explicit retry blocks when the
    prior result confirms that a row already exists.
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
        policies: list[SmartsheetColumnPolicy],
        available_columns: dict[str, int],
        attachment_source_path: str | Path | None = None,
        run_type: str = "",
    ) -> SmartsheetReviewSubmissionResult:
        """
        Submit one deterministically processed review output through
        the existing mapping, destination, and write boundaries.
        """

        if not isinstance(
            review_output,
            ReviewOutput,
        ):
            return self._failure(
                "invalid_review_output"
            )

        mapping = self.mapping_service.map(
            review_output=review_output,
            policies=policies,
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
            return SmartsheetReviewSubmissionResult(
                written=write_result.written,
                success=False,
                status=self._normalize_status(
                    write_result.status
                ),
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

    def retry(
        self,
        *,
        previous_result: SmartsheetReviewSubmissionResult,
        review_output: ReviewOutput,
        policies: list[SmartsheetColumnPolicy],
        available_columns: dict[str, int],
        attachment_source_path: str | Path | None = None,
        run_type: str = "",
    ) -> SmartsheetReviewSubmissionResult:
        """
        Retry only when the prior outcome proves that no row was created.

        No external row reference is stored by this service, so an
        existing-row attachment continuation cannot be performed safely.
        Existing or uncertain row outcomes are blocked to prevent blind
        duplicate row creation. Durable mailbox recovery performs exact-key
        reconciliation instead of using this direct retry path.
        """

        if not isinstance(
            previous_result,
            SmartsheetReviewSubmissionResult,
        ):
            return self._failure(
                "invalid_previous_submission_result"
            )

        if previous_result.written:
            return SmartsheetReviewSubmissionResult(
                written=True,
                success=False,
                status="retry_blocked_existing_row",
            )

        if previous_result.status in {
            "row_write_timeout",
            "row_write_response_invalid",
            "row_write_outcome_unknown",
        }:
            return SmartsheetReviewSubmissionResult(
                written=False,
                success=False,
                status="retry_blocked_uncertain_row",
            )

        return self.submit(
            review_output=review_output,
            policies=policies,
            available_columns=available_columns,
            attachment_source_path=attachment_source_path,
            run_type=run_type,
        )

    @staticmethod
    def _failure(
        status: Any,
    ) -> SmartsheetReviewSubmissionResult:
        return SmartsheetReviewSubmissionResult(
            written=False,
            success=False,
            status=(
                SmartsheetReviewSubmissionService
                ._normalize_status(
                    status
                )
            ),
        )

    @staticmethod
    def _normalize_status(
        status: Any,
    ) -> str:
        return str(
            status
            or "submission_failed"
        ).strip()
