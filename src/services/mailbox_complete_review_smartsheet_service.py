from dataclasses import dataclass
from typing import Iterable

from src.graph.mailbox_processor import (
    MessageProcessingResult,
)
from src.services.complete_review_smartsheet_workflow_service import (
    CompleteReviewSmartsheetWorkflowService,
)
from src.services.review_output_service import (
    ReviewOutput,
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
    Applies the existing complete-review-to-Smartsheet workflow to
    already processed mailbox documents.

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

    Classification confirmation is not accepted as write authority.
    """

    REJECTED_STATUS = "rejected"
    CANCELLED_STATUS = "cancelled"

    def __init__(
        self,
        *,
        workflow_service: (
            CompleteReviewSmartsheetWorkflowService
            | None
        ) = None,
        configuration_service: (
            SmartsheetReviewConfigurationService
            | None
        ) = None,
    ) -> None:
        self.workflow_service = (
            workflow_service
            or CompleteReviewSmartsheetWorkflowService()
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
        approve_complete_review: bool = False,
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
                    workflow_result = (
                        self.workflow_service.run(
                            review_output=review_output,
                            policies=list(
                                configuration_result.policies
                            ),
                            available_columns=dict(
                                configuration_result
                                .available_columns
                            ),
                            approve_complete_review=(
                                approve_complete_review
                            ),
                            attachment_source_path=(
                                document.file_path
                            ),
                        )
                    )
                except Exception:
                    failed_count += 1
                    continue

                if workflow_result.approved:
                    approved_count += 1

                if (
                    workflow_result.success
                    and workflow_result.written
                    and workflow_result.status
                    == "written"
                ):
                    written_count += 1
                    continue

                if (
                    workflow_result.status
                    == self.REJECTED_STATUS
                ):
                    rejected_count += 1
                    continue

                if (
                    workflow_result.status
                    == self.CANCELLED_STATUS
                ):
                    cancelled_count += 1
                    continue

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
            status = "completed_with_failures"
            success = False

        elif cancelled_count:
            status = "completed_with_cancellations"
            success = True

        elif rejected_count:
            status = "completed_with_rejections"
            success = True

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
