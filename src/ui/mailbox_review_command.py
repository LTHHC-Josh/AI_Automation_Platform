import argparse
from collections.abc import Callable, Sequence
from typing import Any

from src.services.mailbox_review_orchestration_service import (
    MailboxReviewOrchestrationResult,
    MailboxReviewOrchestrationService,
)


class MailboxReviewCommand:
    """
    Runs the mailbox-review orchestration from an explicit local command.

    Output is limited to PHI-safe counts, success, and status.
    """

    def __init__(
        self,
        *,
        orchestration_service: (
            MailboxReviewOrchestrationService
            | None
        ) = None,
        output_writer: Callable[[str], Any] = print,
    ) -> None:
        self.orchestration_service = (
            orchestration_service
            or MailboxReviewOrchestrationService()
        )
        self.output_writer = output_writer

    def run(
        self,
        *,
        top: Any = 10,
        created_at: Any = None,
    ) -> MailboxReviewOrchestrationResult:
        """
        Run one explicitly requested mailbox-review workflow.
        """

        result = self.orchestration_service.run(
            top=top,
            created_at=created_at,
        )

        self.output_writer(
            "=" * 60
        )
        self.output_writer(
            "MAILBOX REVIEW SUMMARY"
        )
        self.output_writer(
            "=" * 60
        )
        self.output_writer(
            f"Messages   : {result.message_count}"
        )
        self.output_writer(
            f"Documents  : {result.document_count}"
        )
        self.output_writer(
            f"Submitted  : {result.submitted_count}"
        )
        self.output_writer(
            f"Cancelled  : {result.cancelled_count}"
        )
        self.output_writer(
            f"Failed     : {result.failed_count}"
        )
        self.output_writer(
            f"Success    : {result.success}"
        )
        self.output_writer(
            f"Status     : {result.status}"
        )

        return result


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build the explicit local command-line contract.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Process unread mailbox documents and run explicit "
            "local classification review."
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
            "Optional PHI-safe timestamp supplied to feedback records."
        ),
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """
    Run the opt-in command.

    No mailbox or review work occurs unless this function is explicitly
    invoked.
    """

    arguments = build_argument_parser().parse_args(
        argv
    )

    result = MailboxReviewCommand().run(
        top=arguments.top,
        created_at=arguments.created_at,
    )

    if result.success:
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
