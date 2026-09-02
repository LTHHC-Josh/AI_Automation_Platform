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
from src.services.mailbox_document_smartsheet_recovery_service import (
    MailboxDocumentSmartsheetRecoveryService,
)
from src.services.production_filename_assembly_service import FilenameReadinessDiagnostic
from src.services.review_reason_summary_service import ReviewReasonSummaryService
from src.services.field_validation_diagnostic_service import (
    FieldValidationDiagnosticService, FinalValidationSummary,
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
    row_action: str = "skipped"
    attachment_action: str = "skipped"
    filename_readiness: FilenameReadinessDiagnostic | None = None
    review_reason_count: int = 0
    review_reason_categories: tuple[str, ...] = ()
    validation_summary: FinalValidationSummary = FinalValidationSummary()


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
        recovery_service: MailboxDocumentSmartsheetRecoveryService | None = None,
    ) -> None:
        self.submission_service = (
            submission_service
            or SmartsheetReviewSubmissionService()
        )

        self.configuration_service = (
            configuration_service
            or SmartsheetReviewConfigurationService()
        )
        self.recovery_service = recovery_service or MailboxDocumentSmartsheetRecoveryService(
            configuration_service=self.configuration_service,
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
        row_actions = []
        attachment_actions = []
        filename_diagnostics = []
        review_reason_categories = []
        review_reason_count = 0
        reason_summary = ReviewReasonSummaryService()
        validation_summaries = []

        for message_result in results:
            work_items = getattr(message_result, "work_items", [])
            if self.recovery_service is not None and work_items:
                message_complete = True
                for work_item in work_items:
                    document_count += 1
                    review_output = getattr(
                        getattr(work_item, "document", None), "review_output", None)
                    validation_summaries.append(
                        FieldValidationDiagnosticService().summarize(
                            getattr(work_item, "document", None)
                        )
                    )
                    final_reasons = tuple(dict.fromkeys(
                        str(reason) for reason in getattr(
                            review_output, "review_reasons", ()) if str(reason).strip()
                    ))
                    codes = reason_summary.summarize_codes(
                        final_reasons)
                    canonical_codes = tuple(
                        code for code in codes.split("; ") if code
                    )
                    review_reason_count += len(canonical_codes)
                    review_reason_categories.extend(canonical_codes)
                    try:
                        recovery_result = self.recovery_service.run(
                            work_item=work_item, run_type=run_type)
                    except Exception:
                        recovery_result = None
                    if recovery_result is not None:
                        written_count += int(recovery_result.row_action == "created")
                        row_actions.append(recovery_result.row_action)
                        attachment_actions.append(recovery_result.attachment_action)
                        if recovery_result.filename_readiness is not None:
                            filename_diagnostics.append(recovery_result.filename_readiness)
                    if recovery_result is not None and recovery_result.completed:
                        pass
                    else:
                        failed_count += 1
                        message_complete = False
                        if recovery_result is None:
                            row_actions.append("failed")
                            attachment_actions.append("skipped")
                message_result.business_actions_completed = message_complete
                continue
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
                validation_summaries.append(
                    FieldValidationDiagnosticService().summarize(document)
                )
                codes = reason_summary.summarize_codes(
                    getattr(review_output, "review_reasons", ()))
                canonical_codes = tuple(
                    code for code in codes.split("; ") if code
                )
                review_reason_count += len(canonical_codes)
                review_reason_categories.extend(canonical_codes)

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
                        ),
                        document_family=(
                            review_output.document_category
                        ),
                        document_subtype=(
                            review_output.document_subtype
                        ),
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
                    row_actions.append("created")
                    attachment_actions.append(
                        "uploaded" if submission_result.success else "failed")
                else:
                    row_actions.append("failed")
                    attachment_actions.append("skipped")

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
                row_action="skipped",
                attachment_action="skipped",
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
            row_action=self._aggregate_actions(row_actions),
            attachment_action=self._aggregate_actions(attachment_actions),
            filename_readiness=(
                filename_diagnostics[0] if len(filename_diagnostics) == 1 else None
            ),
            review_reason_count=review_reason_count,
            review_reason_categories=tuple(dict.fromkeys(review_reason_categories)),
            validation_summary=self._aggregate_validation_summaries(
                validation_summaries
            ),
        )

    @staticmethod
    def _aggregate_validation_summaries(summaries):
        summaries = [item for item in summaries if isinstance(item, FinalValidationSummary)]
        if not summaries:
            return FinalValidationSummary()
        count_fields = (
            "accepted_field_count", "optional_absent_field_count",
            "missing_required_count", "low_confidence_count",
            "unsupported_count", "ambiguous_count", "conflicting_count",
            "invalid_count",
        )
        values = {
            name: sum(getattr(item, name) for item in summaries)
            for name in count_fields
        }
        unit_sources = {item.unit_source_category for item in summaries}
        return FinalValidationSummary(
            **values,
            quantity_present=any(item.quantity_present for item in summaries),
            unit_source_category=(
                next(iter(unit_sources)) if len(unit_sources) == 1 else "unresolved"
            ),
        )

    @staticmethod
    def _aggregate_actions(actions):
        distinct = set(actions)
        if not distinct:
            return "skipped"
        if len(distinct) == 1:
            return next(iter(distinct))
        return "mixed"

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
            row_action="failed",
            attachment_action="skipped",
        )
