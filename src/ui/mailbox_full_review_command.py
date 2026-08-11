import argparse
from collections.abc import Callable, Sequence
from typing import Any

from src.services.mailbox_full_review_orchestration_service import (
    MailboxFullReviewOrchestrationResult,
    MailboxFullReviewOrchestrationService,
)


class MailboxFullReviewCommand:
    """
    Runs the explicit full mailbox-review workflow.

    The command displays PHI-safe counts, success, and status only.

    It does not display message IDs, subjects, filenames, paths,
    OCR text, extracted values, source_text, review payloads,
    fingerprints, Smartsheet payloads, row IDs, or patient data.
    """

    def __init__(
        self,
        *,
        orchestration_service: (
            MailboxFullReviewOrchestrationService
            | None
        ) = None,
        output_writer: Callable[[str], Any] = print,
    ) -> None:
        self.orchestration_service = (
            orchestration_service
            or MailboxFullReviewOrchestrationService()
        )

        self.output_writer = output_writer

    def run(
        self,
        *,
        top: Any = 10,
        created_at: Any = None,
        skip_classification_review: bool = False,
        approve_complete_review: bool = False,
        run_type: str = "",
    ) -> MailboxFullReviewOrchestrationResult:
        result = self.orchestration_service.run(
            top=top,
            created_at=created_at,
            skip_classification_review=(
                skip_classification_review
            ),
            approve_complete_review=(
                approve_complete_review
            ),
            run_type=run_type,
        )

        self.output_writer(
            "=" * 60
        )

        self.output_writer(
            "FULL MAILBOX REVIEW SUMMARY"
        )

        self.output_writer(
            "=" * 60
        )

        self.output_writer(
            f"Messages                  : {result.message_count}"
        )

        self.output_writer(
            f"Documents                 : {result.document_count}"
        )

        if skip_classification_review:
            self.output_writer(
                "Demo classification review skipped: True"
            )

        if approve_complete_review:
            self.output_writer(
                "Explicit complete review approval: True"
            )

        self.output_writer(
            "Classification submitted  : "
            f"{result.classification_submitted_count}"
        )

        self.output_writer(
            "Classification cancelled  : "
            f"{result.classification_cancelled_count}"
        )

        self.output_writer(
            f"Approved                  : {result.approved_count}"
        )

        self.output_writer(
            f"Written                   : {result.written_count}"
        )

        self.output_writer(
            f"Rejected                  : {result.rejected_count}"
        )

        self.output_writer(
            "Complete review cancelled : "
            f"{result.complete_review_cancelled_count}"
        )

        self.output_writer(
            f"Failed                    : {result.failed_count}"
        )

        self.output_writer(
            f"Success                   : {result.success}"
        )

        self.output_writer(
            f"Status                    : {result.status}"
        )

        return result


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Process unread mailbox documents, run explicit local "
            "classification review, run explicit complete review, "
            "and allow approved reviewed output to proceed through "
            "the controlled Smartsheet write workflow."
        )
    )

    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help=(
            "Maximum number of unread messages to request. "
            "Must be at least 1."
        ),
    )

    parser.add_argument(
        "--created-at",
        default=None,
        help=(
            "Optional PHI-safe timestamp supplied to classification "
            "feedback records."
        ),
    )

    parser.add_argument(
        "--demo-skip-classification-review",
        action="store_true",
        help=(
            "DEMO ONLY: allow the existing AI classification/extraction "
            "result to proceed without classification confirmation. "
            "Final complete-review approval is still required before "
            "Smartsheet writing."
        ),
    )

    parser.add_argument(
        "--run-type",
        required=True,
        help=(
            "Required PHI-safe description of the change or behavior "
            "being tested. Written to the Smartsheet Run Type column. "
            "Do not include patient information, document values, "
            "filenames, paths, or source_text."
        ),
    )

    parser.add_argument(
        "--approve-complete-review",
        action="store_true",
        help=(
            "Explicitly approve the complete-review decision without "
            "the terminal approval prompt. The existing complete-review "
            "approval service still blocks Human Review Required."
        ),
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    arguments = build_argument_parser().parse_args(
        argv
    )

    result = MailboxFullReviewCommand().run(
        top=arguments.top,
        created_at=arguments.created_at,
        skip_classification_review=(
            arguments.demo_skip_classification_review
        ),
        approve_complete_review=(
            arguments.approve_complete_review
        ),
        run_type=arguments.run_type,
    )

    if result.success:
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
