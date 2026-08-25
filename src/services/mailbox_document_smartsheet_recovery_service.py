from dataclasses import dataclass
from pathlib import Path

from src.models.smartsheet_mapping import SmartsheetRowMappingResult
from src.services.mailbox_document_job_state_service import (
    MailboxDocumentJobStateService, MailboxDocumentWorkItem,
)
from src.services.smartsheet_destination_validation_service import SmartsheetDestinationValidationService
from src.services.smartsheet_review_configuration_service import SmartsheetReviewConfigurationService
from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService
from src.services.smartsheet_reviewed_write_service import SmartsheetReviewedWriteService
from src.services.smartsheet_submission_key_configuration_service import SmartsheetSubmissionKeyConfigurationService


@dataclass(frozen=True)
class MailboxDocumentSmartsheetRecoveryResult:
    completed: bool
    row_known: bool
    attachment_known: bool
    success: bool
    status: str


class MailboxDocumentSmartsheetRecoveryService:
    """Perform one bounded, durable, idempotent business-action attempt."""

    def __init__(self, *, job_state_service=None, submission_key_configuration_service=None,
                 configuration_service=None, mapping_service=None,
                 destination_validation_service=None, write_service=None):
        self.job_state_service = job_state_service or MailboxDocumentJobStateService()
        self.submission_key_configuration_service = (
            submission_key_configuration_service or SmartsheetSubmissionKeyConfigurationService())
        self.configuration_service = configuration_service or SmartsheetReviewConfigurationService()
        self.mapping_service = mapping_service or SmartsheetReviewRowMappingService()
        self.destination_validation_service = destination_validation_service or SmartsheetDestinationValidationService()
        self.write_service = write_service or SmartsheetReviewedWriteService()

    def run(self, *, work_item: MailboxDocumentWorkItem, run_type: str = ""):
        if not isinstance(work_item, MailboxDocumentWorkItem):
            return self._failure("invalid_work_item")
        loaded = self.job_state_service.load(work_item.job_key)
        if not loaded.success or loaded.state is None:
            return self._failure(loaded.status)
        state = loaded.state
        if state.stage == "attachment_written":
            return MailboxDocumentSmartsheetRecoveryResult(True, True, True, True, "completed")
        if state.stage == "blocked_permanent":
            return self._failure("blocked_permanent")
        key_configuration = self.submission_key_configuration_service.resolve()
        if not key_configuration.success or key_configuration.column_title is None:
            return self._failure(key_configuration.status)
        title = key_configuration.column_title

        row_id = state.smartsheet_row_id
        if state.stage in {"row_write_pending", "row_write_uncertain"}:
            document = work_item.document
            review_output = getattr(document, "review_output", None)
            if state.stage == "row_write_pending" and review_output is None:
                return self._failure("processed_result_unavailable")
            configuration = None
            if review_output is not None:
                configuration = self.configuration_service.resolve(
                    document_type=review_output.document_type,
                    document_family=review_output.document_category,
                    document_subtype=review_output.document_subtype,
                )
                if not configuration.success:
                    return self._block(work_item.job_key, state.stage, configuration.status)
                if title not in configuration.available_columns:
                    return self._block(work_item.job_key, state.stage, "submission_key_column_missing")
            column_id = (configuration.available_columns[title] if configuration else None)
            matches = self._find_rows(column_id, work_item.job_key, title=title)
            if matches is None:
                if state.stage == "row_write_uncertain":
                    return self._failure("row_write_uncertain")
                matches = []
            if len(matches) > 1:
                return self._block(work_item.job_key, state.stage, "duplicate_row_conflict")
            if len(matches) == 1:
                row_id = matches[0]
            elif state.stage == "row_write_uncertain":
                return self._failure("row_write_uncertain")
            else:
                mapping = self.mapping_service.map(
                    review_output=review_output,
                    policies=list(configuration.policies), run_type=run_type,
                )
                if not mapping.ready_for_write:
                    return self._block(work_item.job_key, state.stage, "mapping_not_ready")
                values = dict(mapping.values)
                values[title] = work_item.job_key
                mapping = SmartsheetRowMappingResult(
                    values=values,
                    missing_required_columns=list(mapping.missing_required_columns),
                    review_only_columns=list(mapping.review_only_columns),
                    prohibited_fields=list(mapping.prohibited_fields),
                    warnings=list(mapping.warnings), ready_for_write=True,
                )
                available = dict(configuration.available_columns)
                validation = self.destination_validation_service.validate(mapping, available)
                if not validation.ready_for_write:
                    return self._block(work_item.job_key, state.stage, "destination_not_ready")
                operation = self.write_service.create_row(mapping=mapping, destination_validation=validation)
                if operation.success:
                    row_id = operation.row_id
                else:
                    matches = self._find_rows(column_id, work_item.job_key, title=title)
                    if matches is not None and len(matches) == 1:
                        row_id = matches[0]
                    elif matches is not None and len(matches) > 1:
                        return self._block(work_item.job_key, state.stage, "duplicate_row_conflict")
                    else:
                        self.job_state_service.transition(
                            work_item.job_key, expected_stages={state.stage}, stage="row_write_uncertain",
                            failure_category="row_write_outcome_unknown", retryable=False,
                            increment_row_attempt=True)
                        return self._failure("row_write_uncertain")
            stored = self.job_state_service.transition(
                work_item.job_key, expected_stages={state.stage}, stage="row_written",
                smartsheet_row_id=row_id, increment_row_attempt=(len(matches) == 0))
            if not stored.success:
                return self._failure(stored.status)
            state = stored.state

        if state is None or state.smartsheet_row_id is None:
            return self._failure("row_reference_unavailable")
        row_id = state.smartsheet_row_id
        extension = Path(work_item.local_path).suffix.lower() or ".bin"
        technical_name = f"{work_item.job_key}{extension}"
        names = self._attachment_names(row_id)
        if names is None:
            if state.stage == "attachment_write_uncertain":
                return self._failure("attachment_write_uncertain")
            names = []
        count = sum(name == technical_name for name in names)
        if count > 1:
            return self._block(work_item.job_key, state.stage, "duplicate_attachment_conflict")
        if count == 0 and state.stage == "attachment_write_uncertain":
            return self._failure("attachment_write_uncertain")
        if count == 0:
            operation = self.write_service.attach_to_existing_row(
                row_id=row_id, attachment_source_path=work_item.local_path,
                technical_attachment_name=technical_name)
            if not operation.success:
                names = self._attachment_names(row_id)
                if names is None or sum(name == technical_name for name in names) != 1:
                    self.job_state_service.transition(
                        work_item.job_key, expected_stages={state.stage}, stage="attachment_write_uncertain",
                        failure_category="attachment_write_outcome_unknown", retryable=False,
                        increment_attachment_attempt=True)
                    return self._failure("attachment_write_uncertain")
        stored = self.job_state_service.transition(
            work_item.job_key, expected_stages={state.stage}, stage="attachment_written",
            increment_attachment_attempt=(count == 0))
        if not stored.success:
            return self._failure(stored.status)
        return MailboxDocumentSmartsheetRecoveryResult(True, True, True, True, "completed")

    def _find_rows(self, column_id, key, *, title):
        try:
            if isinstance(column_id, int) and not isinstance(column_id, bool) and column_id > 0:
                return list(self.write_service.client.find_row_ids_by_exact_column_value(column_id=column_id, value=key))
            return list(self.write_service.client.find_row_ids_by_exact_column_title_value(column_title=title, value=key))
        except Exception: return None

    def _attachment_names(self, row_id):
        try: return list(self.write_service.client.list_row_attachment_names(row_id=row_id))
        except Exception: return None

    def _block(self, job_key, stage, category):
        self.job_state_service.transition(job_key, expected_stages={stage}, stage="blocked_permanent",
                                          failure_category=category, retryable=False)
        return self._failure(category)

    @staticmethod
    def _failure(status):
        return MailboxDocumentSmartsheetRecoveryResult(False, False, False, False, str(status))
