from dataclasses import dataclass
from typing import Any

from src.services.review_output_service import (
    ReviewOutput,
)


@dataclass(frozen=True)
class CompleteReviewApprovalResult:
    """
    PHI-safe result from one complete-review approval decision.

    The result excludes review fields, service lines, source_text,
    extracted values, OCR text, filenames, paths, and patient data.
    """

    approved: bool
    success: bool
    status: str


class CompleteReviewApprovalService:
    """
    Applies one explicit human approval decision to an existing
    ReviewOutput snapshot.

    This service does not rerun OCR, classification, extraction,
    deterministic validation, business rules, or review-output
    construction.

    It does not mutate ReviewOutput and does not call Smartsheet.

    A document that still has unresolved human-review requirements
    cannot be approved for downstream automation.
    """

    APPROVE_DECISION = "approved"
    REJECT_DECISION = "rejected"

    HUMAN_REVIEW_RECOMMENDED_STATUS = (
        "human review recommended"
    )

    EXPLICIT_DECISIONS = {
        APPROVE_DECISION,
        REJECT_DECISION,
    }

    def decide(
        self,
        *,
        review_output: ReviewOutput,
        reviewer_decision: Any,
    ) -> CompleteReviewApprovalResult:
        """
        Apply an explicit reviewer decision to one complete review
        snapshot.
        """

        if not isinstance(
            review_output,
            ReviewOutput,
        ):
            return self._failure(
                "invalid_review_output"
            )

        decision = self._normalize_decision(
            reviewer_decision
        )

        if decision not in self.EXPLICIT_DECISIONS:
            return self._failure(
                "decision_not_explicit"
            )

        if decision == self.REJECT_DECISION:
            return CompleteReviewApprovalResult(
                approved=False,
                success=True,
                status="rejected",
            )

        if bool(
            review_output.needs_human_review
        ):
            review_status = self._normalize_decision(
                review_output.review_status
            )

            if (
                review_status
                != self.HUMAN_REVIEW_RECOMMENDED_STATUS
            ):
                return CompleteReviewApprovalResult(
                    approved=False,
                    success=False,
                    status="review_still_required",
                )

        return CompleteReviewApprovalResult(
            approved=True,
            success=True,
            status="approved",
        )

    @staticmethod
    def _normalize_decision(
        value: Any,
    ) -> str:
        return str(
            value
            or ""
        ).strip().lower()

    @staticmethod
    def _failure(
        status: str,
    ) -> CompleteReviewApprovalResult:
        return CompleteReviewApprovalResult(
            approved=False,
            success=False,
            status=status,
        )
