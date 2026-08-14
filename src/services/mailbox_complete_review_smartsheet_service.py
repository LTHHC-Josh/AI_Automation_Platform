from dataclasses import dataclass
from typing import Iterable

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.services.review_output_service import (
    ReviewOutput,
)
from src.services.smartsheet_review_submission_service import (
    SmartsheetReviewSubmissionService,
)
from src.services.smartsheet_review_configuration_service import (
    SmartsheetReviewConfigurationService,
)


@dataclass(frozen=True)
class MailboxCompleteReviewSmartsheetResult:
    """
    PHI-safe summary of complete-review Smartsheet processing for an
    existing mailbox-processing result collection.

    The result excludes message identifiers, subjects, document paths,
    filenames, OCR text, extracted values, source_text, mapped values,
    Smartsheet payloads, row IDs, and patient data.

    Approval/rejection/cancellation counters are retained for backward
    result compatibility and remain zero on the automatic path.
    """

    message_count: int
    document_count: int
    approved_count: int
    written_count: int
    rejected_count: int
    cancelled_count: int
    failed_count: int
    success: bool
    status: str


class MailboxCompleteReviewSmartsheetService:
    """
    Applies automatic Smartsheet submission to already processed
    mailbox documents.

    The legacy class name is retained for caller compatibility. Human
    review is downstream exception handling and is not a write gate.

    For each valid ReviewOutput, this service resolves the explicitly
    approved mapping policy and current destination schema using the
    review output's document type.

    This service does not:
    - fetch mailbox messages;
    - download attachments;
    - run OCR or Ollama;
    - rerun extraction, validation, or business rules;
    - perform classification feedback;
    - infer mapping policy;
    - infer destination columns.

    Classification confirmation is not accepted as a write credential.
    """

    def __init__(
        self,
        *,
        submission_service: (
            SmartsheetReviewSubmissionService
            | None
        ) = None,
        configuration_service: (
            SmartsheetReviewConfigurationService
            | None
        ) = None,
    ) -> None:
        self.submission_service = (
            submission_service
            or SmartsheetReviewSubmissionService()
        )

        self.configuration_service = (
            configuration_service
            or SmartsheetReviewConfigurationService()
        )

    def run(
        self,
        *,
        message_results: Iterable[
            MessageProcessingResult
        ],
        run_type: str = "",
    ) -> MailboxCompleteReviewSmartsheetResult:
        try:
            results = list(
                message_results
            )
        except TypeError:
            return self._failure(
                "invalid_message_results"
            )

        if any(
            not isinstance(
                result,
                MessageProcessingResult,
            )
            for result in results
        ):
            return self._failure(
                "invalid_message_result"
            )

        message_count = len(
            results
        )

        document_count = 0
        approved_count = 0
        written_count = 0
        rejected_count = 0
        cancelled_count = 0
        failed_count = 0
        partial_success_count = 0

        for message_result in results:
            documents = getattr(
                message_result,
                "processed_documents",
                None,
            )

            if not isinstance(
                documents,
                list,
            ):
                failed_count += 1
                continue

            for document in documents:
                document_count += 1

                review_output = getattr(
                    document,
                    "review_output",
                    None,
                )

                if not isinstance(
                    review_output,
                    ReviewOutput,
                ):
                    failed_count += 1
                    continue

                configuration_result = (
                    self.configuration_service.resolve(
                        document_type=(
                            review_output.document_type
                        )
                    )
                )

                if not configuration_result.success:
                    failed_count += 1
                    continue

                try:
                    submission_result = (
                        self.submission_service.submit(
                            review_output=review_output,
                            policies=list(
                                configuration_result.policies
                            ),
                            available_columns=dict(
                                configuration_result
                                .available_columns
                            ),
                            attachment_source_path=(
                                document.file_path
                            ),
                            run_type=run_type,
                        )
                    )
                except Exception:
                    failed_count += 1
                    continue

                if submission_result.written:
                    written_count += 1

                if (
                    submission_result.success
                    and submission_result.written
                ):
                    continue

                if submission_result.written:
                    partial_success_count += 1

                failed_count += 1

        if document_count == 0:
            return MailboxCompleteReviewSmartsheetResult(
                message_count=message_count,
                document_count=0,
                approved_count=0,
                written_count=0,
                rejected_count=0,
                cancelled_count=0,
                failed_count=0,
                success=True,
                status="no_documents",
            )

        if failed_count:
            status = (
                "completed_with_partial_success"
                if partial_success_count
                else "completed_with_failures"
            )
            success = False

        else:
            status = "completed"
            success = True

        return MailboxCompleteReviewSmartsheetResult(
            message_count=message_count,
            document_count=document_count,
            approved_count=approved_count,
            written_count=written_count,
            rejected_count=rejected_count,
            cancelled_count=cancelled_count,
            failed_count=failed_count,
            success=success,
            status=status,
        )

    @staticmethod
    def _failure(
        status: str,
    ) -> MailboxCompleteReviewSmartsheetResult:
        return MailboxCompleteReviewSmartsheetResult(
            message_count=0,
            document_count=0,
            approved_count=0,
            written_count=0,
            rejected_count=0,
            cancelled_count=0,
            failed_count=0,
            success=False,
            status=status,
        )
