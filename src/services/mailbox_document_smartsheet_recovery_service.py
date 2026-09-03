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
from src.services.production_filename_assembly_service import (
    ProductionFilenameAssemblyResult,
    ProductionFilenameAssemblyService,
)
from src.services.production_filename_assembly_service import FilenameReadinessDiagnostic


@dataclass(frozen=True)
class MailboxDocumentSmartsheetRecoveryResult:
    completed: bool
    row_known: bool
    attachment_known: bool
    success: bool
    status: str
    row_action: str = "skipped"
    attachment_action: str = "skipped"
    filename_readiness: FilenameReadinessDiagnostic | None = None
    row_create_attempted: bool = False
    row_outcome_proven: bool = False
    reconciliation_attempted: bool = False
    reconciliation_match_cardinality: str = "not_attempted"
    row_recovery_state: str = "none"
    attachment_blocked_due_to_unresolved_row: bool = False
    failure_category: str | None = None
    retryable: bool = False
    recoverable: bool = False
    request_contract_version: int = 0
    request_contract_rearm_count: int = 0
    mapped_field_count: int = 0
    included_cell_count: int = 0
    omitted_field_count: int = 0
    mapping_validation_passed: bool = False
    schema_validation_passed: bool = False
    type_validation_passed: bool = False
    rejected_field_categories: tuple[str, ...] = ()
    rejection_safe_category: str = "none"
    api_status_class: str = "unavailable"
    api_error_code: int | None = None


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

    def run(
        self, *, work_item: MailboxDocumentWorkItem, run_type: str = "",
        stage_observer=None,
    ):
        if not isinstance(work_item, MailboxDocumentWorkItem):
            return self._failure("invalid_work_item")
        loaded = self.job_state_service.load(work_item.job_key)
        if not loaded.success or loaded.state is None:
            return self._failure(loaded.status)
        state = loaded.state
        filename_diagnostic = None
        if state.stage == "attachment_written":
            return MailboxDocumentSmartsheetRecoveryResult(
                True, True, True, True, "completed", "skipped", "skipped",
                self._persisted_filename_diagnostic(state),
                row_create_attempted=state.row_create_attempted,
                row_outcome_proven=True,
                reconciliation_attempted=state.row_reconciliation_attempted,
                reconciliation_match_cardinality=(
                    state.row_reconciliation_match_cardinality
                ),
                row_recovery_state="none",
                **self._state_diagnostics(state),
            )
        if state.stage == "blocked_permanent":
            return self._state_failure(state, "blocked_permanent")
        if state.stage == "row_retry_ready" and work_item.document is None:
            return self._state_failure(state, state.last_failure_category or "row_retry_ready")
        if state.stage not in {"row_create_in_flight", "row_write_uncertain"}:
            state, naming_status, filename_diagnostic = (
                self._ensure_attachment_name(
                    work_item, state, lease_token=work_item.lease_token
                )
            )
            if state is None:
                return self._failure(naming_status)
        key_configuration = self.submission_key_configuration_service.resolve()
        if not key_configuration.success or key_configuration.column_title is None:
            return self._failure(key_configuration.status)
        title = key_configuration.column_title

        lease_token = work_item.lease_token
        if not (
            state.lease_token is not None
            and lease_token is not None
            and state.lease_token == lease_token
        ):
            leased = self.job_state_service.acquire_business_action_lease(
                work_item.job_key
            )
            if not leased.success or leased.state is None:
                return self._failure(leased.status)
            state = leased.state
            lease_token = state.lease_token

        row_id = state.smartsheet_row_id
        row_action = "skipped"
        if state.stage in {
            "row_write_pending", "row_create_in_flight", "row_write_uncertain"
        }:
            document = work_item.document
            review_output = getattr(document, "review_output", None)
            reconciliation_only = state.stage in {
                "row_create_in_flight", "row_write_uncertain"
            }
            has_prior_attempt = state.row_attempt_count > 0
            configuration = None
            if review_output is not None:
                configuration = self.configuration_service.resolve(
                    document_type=review_output.document_type,
                    document_family=review_output.document_category,
                    document_subtype=review_output.document_subtype,
                )
                if not configuration.success:
                    return self._block(
                        work_item.job_key, state.stage, configuration.status,
                        lease_token=lease_token,
                    )
                if title not in configuration.available_columns:
                    return self._block(
                        work_item.job_key, state.stage,
                        "submission_key_column_missing", lease_token=lease_token,
                    )
            column_id = (configuration.available_columns[title] if configuration else None)
            matches = self._find_rows(column_id, work_item.job_key, title=title)
            if matches is None:
                target_stage = (
                    "row_write_uncertain"
                    if reconciliation_only or has_prior_attempt
                    else "row_retry_ready"
                )
                stored = self.job_state_service.transition(
                    work_item.job_key, expected_stages={state.stage},
                    stage=target_stage, lease_token=lease_token,
                    failure_category="row_reconciliation_unavailable",
                    retryable=True, recoverable=True,
                    row_reconciliation_attempted=True,
                    row_reconciliation_match_cardinality="unavailable",
                    row_recovery_state=(
                        "reconcile_only"
                        if reconciliation_only or has_prior_attempt
                        else "retry_ready"
                    ),
                    attachment_blocked_due_to_unresolved_row=True,
                )
                return self._state_failure(
                    stored.state or state, "row_reconciliation_unavailable"
                )
            if len(matches) > 1:
                return self._block(
                    work_item.job_key, state.stage, "row_reconciliation_ambiguous",
                    lease_token=lease_token, reconciliation_cardinality="multiple",
                )
            if len(matches) == 1:
                row_id = matches[0]
                row_action = "reconciled_existing"
                stored = self.job_state_service.transition(
                    work_item.job_key, expected_stages={state.stage},
                    stage="row_written", lease_token=lease_token,
                    smartsheet_row_id=row_id, retain_lease=True,
                    row_outcome_proven=True,
                    row_reconciliation_attempted=True,
                    row_reconciliation_match_cardinality="one",
                    row_recovery_state="none", recoverable=False,
                    retryable=False,
                    attachment_blocked_due_to_unresolved_row=False,
                )
                if not stored.success or stored.state is None:
                    return self._failure(stored.status, row_action=row_action)
                state = stored.state
            elif reconciliation_only or review_output is None:
                stored = self.job_state_service.transition(
                    work_item.job_key, expected_stages={state.stage},
                    stage="row_retry_ready", lease_token=lease_token,
                    failure_category="row_reconciliation_zero_matches",
                    retryable=True, recoverable=True,
                    row_reconciliation_attempted=True,
                    row_reconciliation_match_cardinality="zero",
                    row_recovery_state="retry_ready",
                    attachment_blocked_due_to_unresolved_row=True,
                )
                return self._state_failure(
                    stored.state or state, "row_reconciliation_zero_matches"
                )
            else:
                mapping = self.mapping_service.map(
                    review_output=review_output,
                    policies=list(configuration.policies), run_type=run_type,
                )
                if not mapping.ready_for_write:
                    return self._block(
                        work_item.job_key, state.stage, "mapping_not_ready",
                        lease_token=lease_token,
                    )
                values = dict(mapping.values)
                values[title] = work_item.job_key
                mapping = SmartsheetRowMappingResult(
                    values=values,
                    missing_required_columns=list(mapping.missing_required_columns),
                    review_only_columns=list(mapping.review_only_columns),
                    prohibited_fields=list(mapping.prohibited_fields),
                    warnings=list(mapping.warnings), ready_for_write=True,
                    omitted_columns=list(mapping.omitted_columns),
                    duplicate_destination_columns=list(
                        mapping.duplicate_destination_columns
                    ),
                )
                available = dict(configuration.available_columns)
                validation = self.destination_validation_service.validate(
                    mapping,
                    available,
                    available_column_types=dict(
                        configuration.available_column_types
                    ),
                    available_system_column_types=dict(
                        configuration.available_system_column_types
                    ),
                )
                if not validation.ready_for_write:
                    return self._block(
                        work_item.job_key,
                        state.stage,
                        validation.rejection_safe_category
                        if validation.rejection_safe_category != "none"
                        else "destination_not_ready",
                        lease_token=lease_token,
                        row_diagnostics=self._validation_diagnostics(validation),
                    )
                is_contract_rearm = state.row_attempt_count > 0
                if is_contract_rearm and not (
                    state.row_request_contract_rearm_count == 0
                    and state.row_request_contract_version
                    < validation.request_contract_version
                ):
                    stored = self.job_state_service.transition(
                        work_item.job_key,
                        expected_stages={state.stage},
                        stage="row_retry_ready",
                        lease_token=lease_token,
                        failure_category="row_request_contract_rearm_unavailable",
                        retryable=False,
                        recoverable=True,
                        row_recovery_state="retry_ready",
                        attachment_blocked_due_to_unresolved_row=True,
                        **self._validation_diagnostics(validation),
                    )
                    return self._state_failure(
                        stored.state or state,
                        "row_request_contract_rearm_unavailable",
                    )
                in_flight = self.job_state_service.transition(
                    work_item.job_key, expected_stages={state.stage},
                    stage="row_create_in_flight", lease_token=lease_token,
                    retain_lease=True, increment_row_attempt=True,
                    retryable=False, recoverable=True,
                    row_create_attempted=True, row_outcome_proven=False,
                    row_reconciliation_attempted=True,
                    row_reconciliation_match_cardinality="zero",
                    row_recovery_state="reconcile_only",
                    attachment_blocked_due_to_unresolved_row=True,
                    row_request_contract_version=(
                        validation.request_contract_version
                    ),
                    increment_row_request_contract_rearm=is_contract_rearm,
                    **self._validation_diagnostics(validation),
                )
                if not in_flight.success or in_flight.state is None:
                    return self._failure(in_flight.status)
                state = in_flight.state
                self._observe(stage_observer, "smartsheet_row_create_attempted", "completed")
                operation = self.write_service.create_row(
                    mapping=mapping, destination_validation=validation)
                if operation.success:
                    row_id = operation.row_id
                    row_action = "created"
                    stored = self.job_state_service.transition(
                        work_item.job_key, expected_stages={state.stage},
                        stage="row_written", lease_token=lease_token,
                        smartsheet_row_id=row_id, retain_lease=True,
                        row_outcome_proven=True, row_recovery_state="none",
                        retryable=False, recoverable=False,
                        attachment_blocked_due_to_unresolved_row=False,
                    )
                    if not stored.success or stored.state is None:
                        return self._failure(stored.status, row_action="failed")
                    state = stored.state
                else:
                    matches = self._find_rows(column_id, work_item.job_key, title=title)
                    if matches is not None and len(matches) == 1:
                        row_id = matches[0]
                        row_action = "reconciled_existing"
                        stored = self.job_state_service.transition(
                            work_item.job_key, expected_stages={state.stage},
                            stage="row_written", lease_token=lease_token,
                            smartsheet_row_id=row_id, retain_lease=True,
                            row_outcome_proven=True,
                            row_reconciliation_attempted=True,
                            row_reconciliation_match_cardinality="one",
                            row_recovery_state="none", retryable=False,
                            recoverable=False,
                            attachment_blocked_due_to_unresolved_row=False,
                        )
                        if not stored.success or stored.state is None:
                            return self._failure(stored.status, row_action="failed")
                        state = stored.state
                    elif matches is not None and len(matches) > 1:
                        return self._block(
                            work_item.job_key, state.stage,
                            "row_reconciliation_ambiguous",
                            lease_token=lease_token,
                            reconciliation_cardinality="multiple",
                        )
                    elif operation.outcome_proven:
                        cardinality = (
                            "zero" if matches is not None else "unavailable"
                        )
                        stored = self.job_state_service.transition(
                            work_item.job_key, expected_stages={state.stage},
                            stage=(
                                "row_retry_ready"
                                if cardinality == "zero"
                                else "row_write_uncertain"
                            ),
                            lease_token=lease_token,
                            failure_category=operation.status,
                            retryable=False, recoverable=True,
                            row_outcome_proven=True,
                            row_reconciliation_attempted=matches is not None,
                            row_reconciliation_match_cardinality=cardinality,
                            row_recovery_state=(
                                "retry_ready"
                                if cardinality == "zero"
                                else "reconcile_only"
                            ),
                            attachment_blocked_due_to_unresolved_row=True,
                            **self._operation_diagnostics(operation),
                        )
                        return self._state_failure(
                            stored.state or state, operation.status
                        )
                    else:
                        cardinality = "zero" if matches is not None else "unavailable"
                        target_stage = (
                            "row_retry_ready" if cardinality == "zero"
                            else "row_write_uncertain"
                        )
                        category = (
                            "row_reconciliation_zero_matches"
                            if cardinality == "zero" else operation.status
                        )
                        stored = self.job_state_service.transition(
                            work_item.job_key, expected_stages={state.stage},
                            stage=target_stage, lease_token=lease_token,
                            failure_category=category, retryable=False,
                            recoverable=True, row_outcome_proven=False,
                            row_reconciliation_attempted=True,
                            row_reconciliation_match_cardinality=cardinality,
                            row_recovery_state=(
                                "retry_ready" if cardinality == "zero"
                                else "reconcile_only"
                            ),
                            attachment_blocked_due_to_unresolved_row=True,
                            **self._operation_diagnostics(operation),
                        )
                        return self._state_failure(stored.state or state, category)

        if state is None or state.smartsheet_row_id is None:
            return self._failure(
                "row_reference_unavailable",
                attachment_blocked_due_to_unresolved_row=True,
            )
        if state.attachment_filename is None:
            state, naming_status, filename_diagnostic = (
                self._ensure_attachment_name(
                    work_item, state, lease_token=lease_token
                )
            )
            if state is None:
                return self._failure(naming_status)
        row_id = state.smartsheet_row_id
        expected_name = state.attachment_filename
        if expected_name is None:
            return self._failure("attachment_filename_unavailable")
        names = self._attachment_names(row_id)
        if names is None:
            stored = self.job_state_service.transition(
                work_item.job_key, expected_stages={state.stage},
                stage="attachment_write_uncertain", lease_token=lease_token,
                failure_category="attachment_reconciliation_unavailable",
                retryable=False, recoverable=True,
            )
            return self._state_failure(
                stored.state or state, "attachment_reconciliation_unavailable",
                row_action=row_action, attachment_action="failed",
            )
        count = sum(name == expected_name for name in names)
        if count > 1:
            return self._block(
                work_item.job_key, state.stage, "duplicate_attachment_conflict",
                row_action=row_action, attachment_action="failed",
                lease_token=lease_token,
            )
        if count == 0 and state.stage in {
            "attachment_write_pending", "attachment_write_uncertain"
        }:
            return self._state_failure(
                state, "attachment_write_outcome_unknown", row_action=row_action,
                attachment_action="failed",
            )
        attachment_action = "reconciled_existing" if count == 1 else "skipped"
        if count == 0:
            if state.stage in {"attachment_write_pending", "attachment_write_uncertain"}:
                return self._state_failure(
                    state, "attachment_write_outcome_unknown",
                    row_action=row_action, attachment_action="failed",
                )
            pending = self.job_state_service.transition(
                work_item.job_key, expected_stages={state.stage},
                stage="attachment_write_pending", lease_token=lease_token,
                retain_lease=True, increment_attachment_attempt=True,
            )
            if not pending.success or pending.state is None:
                return self._failure(
                    pending.status, row_action=row_action,
                    attachment_action="failed",
                )
            state = pending.state
            operation = self.write_service.attach_to_existing_row(
                row_id=row_id, attachment_source_path=work_item.local_path,
                technical_attachment_name=expected_name)
            if not operation.success:
                names = self._attachment_names(row_id)
                if names is None or sum(name == expected_name for name in names) != 1:
                    stored = self.job_state_service.transition(
                        work_item.job_key, expected_stages={state.stage}, stage="attachment_write_uncertain",
                        failure_category="attachment_write_outcome_unknown", retryable=False,
                        recoverable=True, lease_token=lease_token)
                    return self._state_failure(
                        stored.state or state, "attachment_write_outcome_unknown",
                        row_action=row_action, attachment_action="failed",
                    )
                attachment_action = "reconciled_existing"
            else:
                attachment_action = "uploaded"
        stored = self.job_state_service.transition(
            work_item.job_key, expected_stages={state.stage}, stage="attachment_written",
            lease_token=lease_token)
        if not stored.success:
            return self._failure(
                stored.status, row_action=row_action,
                attachment_action=attachment_action)
        return MailboxDocumentSmartsheetRecoveryResult(
            True, True, True, True, "completed", row_action, attachment_action,
            filename_diagnostic or self._persisted_filename_diagnostic(state),
            row_create_attempted=state.row_create_attempted,
            row_outcome_proven=True,
            reconciliation_attempted=state.row_reconciliation_attempted,
            reconciliation_match_cardinality=(
                state.row_reconciliation_match_cardinality
            ),
            row_recovery_state="none",
            **self._state_diagnostics(state),
        )

    def _ensure_attachment_name(self, work_item, state, *, lease_token=None):
        if state.attachment_filename is not None:
            return state, "ready", self._persisted_filename_diagnostic(state)
        assembly = getattr(work_item.document, "filename_assembly_result", None)
        if not isinstance(assembly, ProductionFilenameAssemblyResult):
            assembly = self.filename_assembly_service.evaluate(
                document=work_item.document,
                source_extension=Path(work_item.local_path).suffix.lower() or ".bin",
            )
        preparation = self.attachment_naming_service.prepare(
            source_path=work_item.local_path,
            filename_policy_result=assembly.policy_result,
        )
        if not preparation.success or preparation.temporary_path is None:
            return None, preparation.status, assembly.diagnostic
        expected_name = preparation.temporary_path.name
        if not self.attachment_naming_service.cleanup(preparation.temporary_path):
            return (
                None,
                "attachment_preparation_cleanup_failed",
                assembly.diagnostic,
            )
        stored = self.job_state_service.transition(
            work_item.job_key,
            expected_stages={state.stage},
            stage=state.stage,
            attachment_filename=expected_name,
            attachment_naming_status=(
                f"{assembly.policy_result.filename_result}_filename"
                if assembly.business_name_resolved else "technical_fallback"
            ),
            attachment_business_filename_attempted=(
                assembly.business_filename_attempted
            ),
            attachment_required_component_failure_count=(
                assembly.required_component_failure_count
            ),
            attachment_optional_component_omission_count=(
                assembly.optional_component_omission_count
            ),
            attachment_placeholder_categories=(
                assembly.policy_result.placeholder_categories
            ),
            attachment_technical_fallback_reason=(
                assembly.diagnostic.technical_fallback_reason
                if assembly.diagnostic is not None else assembly.status
            ),
            lease_token=lease_token,
            retain_lease=lease_token is not None,
        )
        if not stored.success or stored.state is None:
            return None, stored.status, assembly.diagnostic
        return stored.state, "ready", assembly.diagnostic

    @staticmethod
    def _persisted_filename_diagnostic(state):
        naming_status = getattr(state, "attachment_naming_status", None)
        if naming_status in {"business_filename", "complete_business_filename"}:
            filename_result = "complete_business"
        elif naming_status == "partial_business_filename":
            filename_result = "partial_business"
        else:
            filename_result = "technical_fallback"
        business = filename_result != "technical_fallback"
        placeholder_categories = tuple(
            getattr(state, "attachment_placeholder_categories", ()) or ()
        )
        attempted = bool(
            getattr(state, "attachment_business_filename_attempted", False)
        )
        required_failure_count = int(
            getattr(state, "attachment_required_component_failure_count", 0) or 0
        )
        optional_omission_count = int(
            getattr(state, "attachment_optional_component_omission_count", 0) or 0
        )
        fallback_reason = str(
            getattr(state, "attachment_technical_fallback_reason", "none")
            or "none"
        )
        if not attempted and not business:
            fallback_reason = "persisted_technical_fallback"
        return FilenameReadinessDiagnostic(
            person_components_ready=False,
            payer_lookup_ready=False,
            service_lookup_ready=False,
            dates_ready=False,
            workflow_ready=False,
            qualifier_status="Not Evaluated",
            filename_result=filename_result,
            filename_failure_category=(
                "none" if business else fallback_reason
            ),
            business_filename_attempted=attempted,
            required_component_failure_count=required_failure_count,
            optional_component_omission_count=optional_omission_count,
            service_component_status="Not Evaluated",
            form_component_status="Not Evaluated",
            workflow_component_status="Not Evaluated",
            extension_ready=False,
            extension_component_status="Not Evaluated",
            payer_lookup_status="not_evaluated",
            document_type_component_status="Not Evaluated",
            subtype_component_status="Not Evaluated",
            placeholder_count=len(placeholder_categories),
            placeholder_categories=placeholder_categories,
            technical_fallback_reason=(
                "none" if business else fallback_reason
            ),
        )

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
        attachment_action="skipped", lease_token=None,
        reconciliation_cardinality=None,
        row_diagnostics=None,
    ):
        stored = self.job_state_service.transition(
            job_key, expected_stages={stage}, stage="blocked_permanent",
            lease_token=lease_token, failure_category=category, retryable=False,
            recoverable=False, row_recovery_state="blocked",
            row_reconciliation_attempted=(
                True if reconciliation_cardinality is not None else None
            ),
            row_reconciliation_match_cardinality=reconciliation_cardinality,
            attachment_blocked_due_to_unresolved_row=(row_action == "failed"),
            **(row_diagnostics or {}),
        )
        if stored.success and stored.state is not None:
            return self._state_failure(
                stored.state, category, row_action=row_action,
                attachment_action=attachment_action,
            )
        return self._failure(
            stored.status, row_action=row_action,
            attachment_action=attachment_action,
        )

    @staticmethod
    def _state_failure(
        state, status, *, row_action="failed", attachment_action="skipped",
    ):
        return MailboxDocumentSmartsheetRecoveryResult(
            False, bool(state.smartsheet_row_id), False, False, str(status),
            row_action, attachment_action,
            MailboxDocumentSmartsheetRecoveryService._persisted_filename_diagnostic(
                state
            ),
            row_create_attempted=state.row_create_attempted,
            row_outcome_proven=state.row_outcome_proven,
            reconciliation_attempted=state.row_reconciliation_attempted,
            reconciliation_match_cardinality=(
                state.row_reconciliation_match_cardinality
            ),
            row_recovery_state=state.row_recovery_state,
            attachment_blocked_due_to_unresolved_row=(
                state.attachment_blocked_due_to_unresolved_row
            ),
            failure_category=state.last_failure_category or str(status),
            retryable=state.retryable,
            recoverable=state.recoverable,
            **MailboxDocumentSmartsheetRecoveryService._state_diagnostics(
                state
            ),
        )

    @staticmethod
    def _failure(
        status, *, row_action="failed", attachment_action="skipped",
        attachment_blocked_due_to_unresolved_row=False,
    ):
        return MailboxDocumentSmartsheetRecoveryResult(
            False, False, False, False, str(status), row_action, attachment_action,
            attachment_blocked_due_to_unresolved_row=(
                attachment_blocked_due_to_unresolved_row
            ),
            failure_category=str(status),
        )

    @staticmethod
    def _validation_diagnostics(validation):
        return {
            "row_mapped_field_count": validation.mapped_field_count,
            "row_included_cell_count": validation.included_cell_count,
            "row_omitted_field_count": validation.omitted_field_count,
            "row_mapping_validation_passed": (
                validation.mapping_validation_passed
            ),
            "row_schema_validation_passed": (
                validation.schema_validation_passed
            ),
            "row_type_validation_passed": validation.type_validation_passed,
            "row_rejected_field_categories": tuple(
                validation.rejected_field_categories
            ),
            "row_rejection_safe_category": validation.rejection_safe_category,
        }

    @staticmethod
    def _operation_diagnostics(operation):
        return {
            "row_mapped_field_count": operation.mapped_field_count,
            "row_included_cell_count": operation.included_cell_count,
            "row_omitted_field_count": operation.omitted_field_count,
            "row_mapping_validation_passed": (
                operation.mapping_validation_passed
            ),
            "row_schema_validation_passed": operation.schema_validation_passed,
            "row_type_validation_passed": operation.type_validation_passed,
            "row_rejected_field_categories": tuple(
                operation.rejected_field_categories
            ),
            "row_rejection_safe_category": operation.rejection_safe_category,
            "row_api_status_class": operation.api_status_class,
            "row_api_error_code": operation.api_error_code,
        }

    @staticmethod
    def _state_diagnostics(state):
        return {
            "request_contract_version": state.row_request_contract_version,
            "request_contract_rearm_count": (
                state.row_request_contract_rearm_count
            ),
            "mapped_field_count": state.row_mapped_field_count,
            "included_cell_count": state.row_included_cell_count,
            "omitted_field_count": state.row_omitted_field_count,
            "mapping_validation_passed": (
                state.row_mapping_validation_passed
            ),
            "schema_validation_passed": state.row_schema_validation_passed,
            "type_validation_passed": state.row_type_validation_passed,
            "rejected_field_categories": tuple(
                state.row_rejected_field_categories
            ),
            "rejection_safe_category": state.row_rejection_safe_category,
            "api_status_class": state.row_api_status_class,
            "api_error_code": state.row_api_error_code,
        }

    @staticmethod
    def _observe(observer, stage, status):
        if not callable(observer):
            return
        try:
            observer(stage=stage, status=status, duration_seconds=0.0)
        except Exception:
            return
