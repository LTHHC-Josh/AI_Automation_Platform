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
from src.services.document_attachment_naming_service import DocumentAttachmentNamingService
from src.services.production_filename_assembly_service import ProductionFilenameAssemblyService


@dataclass(frozen=True)
class MailboxDocumentSmartsheetRecoveryResult:
    completed: bool
    row_known: bool
    attachment_known: bool
    success: bool
    status: str
    row_action: str = "skipped"
    attachment_action: str = "skipped"


class MailboxDocumentSmartsheetRecoveryService:
    """Perform one bounded, durable, idempotent business-action attempt."""

    def __init__(self, *, job_state_service=None, submission_key_configuration_service=None,
                 configuration_service=None, mapping_service=None,
                 destination_validation_service=None, write_service=None,
                 filename_assembly_service=None, attachment_naming_service=None):
        self.job_state_service = job_state_service or MailboxDocumentJobStateService()
        self.submission_key_configuration_service = (
            submission_key_configuration_service or SmartsheetSubmissionKeyConfigurationService())
        self.configuration_service = configuration_service or SmartsheetReviewConfigurationService()
        self.mapping_service = mapping_service or SmartsheetReviewRowMappingService()
        self.destination_validation_service = destination_validation_service or SmartsheetDestinationValidationService()
        self.write_service = write_service or SmartsheetReviewedWriteService()
        self.filename_assembly_service = filename_assembly_service or ProductionFilenameAssemblyService()
        self.attachment_naming_service = attachment_naming_service or DocumentAttachmentNamingService()

    def run(self, *, work_item: MailboxDocumentWorkItem, run_type: str = ""):
        if not isinstance(work_item, MailboxDocumentWorkItem):
            return self._failure("invalid_work_item")
        loaded = self.job_state_service.load(work_item.job_key)
        if not loaded.success or loaded.state is None:
            return self._failure(loaded.status)
        state = loaded.state
        if state.stage == "attachment_written":
            return MailboxDocumentSmartsheetRecoveryResult(
                True, True, True, True, "completed", "skipped", "skipped")
        if state.stage == "blocked_permanent":
            return self._failure("blocked_permanent")
        if state.stage != "row_write_uncertain":
            state, naming_status = self._ensure_attachment_name(work_item, state)
            if state is None:
                return self._failure(naming_status)
        key_configuration = self.submission_key_configuration_service.resolve()
        if not key_configuration.success or key_configuration.column_title is None:
            return self._failure(key_configuration.status)
        title = key_configuration.column_title

        row_id = state.smartsheet_row_id
        row_action = "skipped"
        row_create_attempted = False
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
                    return self._failure("row_write_uncertain", row_action="failed")
                matches = []
            if len(matches) > 1:
                return self._block(work_item.job_key, state.stage, "duplicate_row_conflict")
            if len(matches) == 1:
                row_id = matches[0]
                row_action = "reconciled_existing"
            elif state.stage == "row_write_uncertain":
                return self._failure("row_write_uncertain", row_action="failed")
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
                row_create_attempted = True
                operation = self.write_service.create_row(
                    mapping=mapping, destination_validation=validation)
                if operation.success:
                    row_id = operation.row_id
                    row_action = "created"
                else:
                    matches = self._find_rows(column_id, work_item.job_key, title=title)
                    if matches is not None and len(matches) == 1:
                        row_id = matches[0]
                        row_action = "created"
                    elif matches is not None and len(matches) > 1:
                        return self._block(work_item.job_key, state.stage, "duplicate_row_conflict")
                    else:
                        self.job_state_service.transition(
                            work_item.job_key, expected_stages={state.stage}, stage="row_write_uncertain",
                            failure_category="row_write_outcome_unknown", retryable=False,
                            increment_row_attempt=True)
                        return self._failure("row_write_uncertain", row_action="failed")
            stored = self.job_state_service.transition(
                work_item.job_key, expected_stages={state.stage}, stage="row_written",
                smartsheet_row_id=row_id,
                increment_row_attempt=row_create_attempted)
            if not stored.success:
                return self._failure(stored.status, row_action=row_action)
            state = stored.state

        if state is None or state.smartsheet_row_id is None:
            return self._failure("row_reference_unavailable")
        if state.attachment_filename is None:
            state, naming_status = self._ensure_attachment_name(work_item, state)
            if state is None:
                return self._failure(naming_status)
        row_id = state.smartsheet_row_id
        expected_name = state.attachment_filename
        if expected_name is None:
            return self._failure("attachment_filename_unavailable")
        names = self._attachment_names(row_id)
        if names is None:
            if state.stage == "attachment_write_uncertain":
                return self._failure(
                    "attachment_write_uncertain", row_action=row_action,
                    attachment_action="failed")
            names = []
        count = sum(name == expected_name for name in names)
        if count > 1:
            return self._block(
                work_item.job_key, state.stage, "duplicate_attachment_conflict",
                row_action=row_action, attachment_action="failed")
        if count == 0 and state.stage == "attachment_write_uncertain":
            return self._failure(
                "attachment_write_uncertain", row_action=row_action,
                attachment_action="failed")
        attachment_action = "reconciled_existing" if count == 1 else "skipped"
        attachment_upload_attempted = False
        if count == 0:
            attachment_upload_attempted = True
            operation = self.write_service.attach_to_existing_row(
                row_id=row_id, attachment_source_path=work_item.local_path,
                technical_attachment_name=expected_name)
            if not operation.success:
                names = self._attachment_names(row_id)
                if names is None or sum(name == expected_name for name in names) != 1:
                    self.job_state_service.transition(
                        work_item.job_key, expected_stages={state.stage}, stage="attachment_write_uncertain",
                        failure_category="attachment_write_outcome_unknown", retryable=False,
                        increment_attachment_attempt=True)
                    return self._failure(
                        "attachment_write_uncertain", row_action=row_action,
                        attachment_action="failed")
            attachment_action = "uploaded"
        stored = self.job_state_service.transition(
            work_item.job_key, expected_stages={state.stage}, stage="attachment_written",
            increment_attachment_attempt=attachment_upload_attempted)
        if not stored.success:
            return self._failure(
                stored.status, row_action=row_action,
                attachment_action=attachment_action)
        return MailboxDocumentSmartsheetRecoveryResult(
            True, True, True, True, "completed", row_action, attachment_action)

    def _ensure_attachment_name(self, work_item, state):
        if state.attachment_filename is not None:
            return state, "ready"
        assembly = self.filename_assembly_service.resolve(
            document=work_item.document,
            source_extension=Path(work_item.local_path).suffix.lower() or ".bin",
        )
        preparation = self.attachment_naming_service.prepare(
            source_path=work_item.local_path,
            filename_policy_result=assembly.policy_result,
        )
        if not preparation.success or preparation.temporary_path is None:
            return None, preparation.status
        expected_name = preparation.temporary_path.name
        if not self.attachment_naming_service.cleanup(preparation.temporary_path):
            return None, "attachment_preparation_cleanup_failed"
        stored = self.job_state_service.transition(
            work_item.job_key,
            expected_stages={state.stage},
            stage=state.stage,
            attachment_filename=expected_name,
            attachment_naming_status=(
                "business_filename" if assembly.business_name_resolved
                else "technical_fallback"
            ),
        )
        if not stored.success or stored.state is None:
            return None, stored.status
        return stored.state, "ready"

    def _find_rows(self, column_id, key, *, title):
        try:
            if isinstance(column_id, int) and not isinstance(column_id, bool) and column_id > 0:
                return list(self.write_service.client.find_row_ids_by_exact_column_value(column_id=column_id, value=key))
            return list(self.write_service.client.find_row_ids_by_exact_column_title_value(column_title=title, value=key))
        except Exception: return None

    def _attachment_names(self, row_id):
        try: return list(self.write_service.client.list_row_attachment_names(row_id=row_id))
        except Exception: return None

    def _block(
        self, job_key, stage, category, *, row_action="failed",
        attachment_action="skipped",
    ):
        self.job_state_service.transition(job_key, expected_stages={stage}, stage="blocked_permanent",
                                          failure_category=category, retryable=False)
        return self._failure(
            category, row_action=row_action, attachment_action=attachment_action)

    @staticmethod
    def _failure(status, *, row_action="failed", attachment_action="skipped"):
        return MailboxDocumentSmartsheetRecoveryResult(
            False, False, False, False, str(status), row_action, attachment_action)
