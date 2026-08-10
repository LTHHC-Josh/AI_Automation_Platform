from collections.abc import Callable
from typing import Any

from src.services.complete_review_approval_service import (
    CompleteReviewApprovalResult,
    CompleteReviewApprovalService,
)
from src.services.review_output_service import (
    ReviewOutput,
)


class CompleteReviewApprovalInteraction:
    """
    Runs one explicit final complete-review approval interaction.

    The interaction displays PHI-safe workflow metadata only.

    It does not display field values, service-line values, source_text,
    OCR text, classification reasons, document paths, filenames, or
    patient data.

    This interaction does not call Smartsheet.
    """

    def __init__(
        self,
        *,
        approval_service: (
            CompleteReviewApprovalService
            | None
        ) = None,
        input_reader: Callable[[str], str] = input,
        output_writer: Callable[[str], Any] = print,
    ) -> None:
        self.approval_service = (
            approval_service
            or CompleteReviewApprovalService()
        )
        self.input_reader = input_reader
        self.output_writer = output_writer

    def run(
        self,
        *,
        review_output: ReviewOutput,
        approve_without_prompt: bool = False,
    ) -> CompleteReviewApprovalResult:
        """
        Request one explicit final approval or rejection decision.
        """

        if not isinstance(
            review_output,
            ReviewOutput,
        ):
            return self._failure(
                "invalid_review_output"
            )

        field_count = self._safe_count(
            review_output.fields
        )

        service_line_count = self._safe_count(
            review_output.service_lines
        )

        review_reason_count = self._safe_count(
            review_output.review_reasons
        )

        self.output_writer(
            "=" * 60
        )
        self.output_writer(
            "COMPLETE REVIEW APPROVAL"
        )
        self.output_writer(
            "=" * 60
        )
        self.output_writer(
            f"Fields present       : {field_count}"
        )
        self.output_writer(
            f"Service lines present: {service_line_count}"
        )
        self.output_writer(
            "Review still required: "
            f"{bool(review_output.needs_human_review)}"
        )
        self.output_writer(
            f"Review reason count  : {review_reason_count}"
        )
        self.output_writer(
            ""
        )

        if approve_without_prompt:
            result = self.approval_service.decide(
                review_output=review_output,
                reviewer_decision="approved",
            )

            self.output_writer(
                f"Approval status: {result.status}"
            )

            return result

        self.output_writer(
            "1. Approve complete review"
        )
        self.output_writer(
            "2. Reject complete review"
        )
        self.output_writer(
            "0. Cancel"
        )

        choice = self._read_text(
            "Selection: "
        )

        if choice == "0":
            return self._failure(
                "cancelled"
            )

        if choice == "1":
            decision = "approved"

        elif choice == "2":
            decision = "rejected"

        else:
            return self._failure(
                "invalid_selection"
            )

        result = self.approval_service.decide(
            review_output=review_output,
            reviewer_decision=decision,
        )

        self.output_writer(
            f"Approval status: {result.status}"
        )

        return result

    def _read_text(
        self,
        prompt: str,
    ) -> str:
        value = self.input_reader(
            prompt
        )

        return str(
            value
            or ""
        ).strip()

    @staticmethod
    def _safe_count(
        value: Any,
    ) -> int:
        if not isinstance(
            value,
            list,
        ):
            return 0

        return len(
            value
        )

    @staticmethod
    def _failure(
        status: str,
    ) -> CompleteReviewApprovalResult:
        return CompleteReviewApprovalResult(
            approved=False,
            success=False,
            status=status,
        )
