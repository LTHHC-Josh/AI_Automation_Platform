from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import smartsheet

from src.clients.smartsheet_client import (
    SmartsheetClient,
)
from src.models.smartsheet_destination_validation import (
    SmartsheetDestinationValidationResult,
)
from src.models.smartsheet_mapping import (
    SmartsheetRowMappingResult,
)
from src.services.document_attachment_naming_service import (
    DocumentAttachmentNamingService,
)
from src.services.smartsheet_destination_validation_service import (
    SmartsheetDestinationValidationService,
)


@dataclass(frozen=True)
class SmartsheetReviewedWriteResult:
    """
    PHI-safe result from one reviewed Smartsheet write attempt.

    This result excludes mapped values, row payloads, row identifiers,
    OCR text, source_text, document paths, filenames, and patient data.
    """

    written: bool
    column_count: int
    attachment_written: bool
    success: bool
    status: str


@dataclass(frozen=True, repr=False)
class SmartsheetRowWriteOperationResult:
    written: bool
    row_id: int | None = field(default=None, repr=False)
    column_count: int = 0
    success: bool = False
    status: str = "smartsheet_write_failed"
    request_attempted: bool = False
    outcome_proven: bool = False
    retryable: bool = False
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


@dataclass(frozen=True)
class SmartsheetAttachmentWriteOperationResult:
    written: bool
    success: bool
    status: str


class SmartsheetReviewedWriteService:
    """
    Writes one previously mapped and destination-validated review row.

    The service does not perform extraction, validation, business rules,
    human review, logical row mapping, or destination-column discovery.

    It accepts only the existing logical mapping and destination
    validation contracts and refuses to write unless both independently
    authorize automatic writing.
    """

    def __init__(
        self,
        *,
        client: SmartsheetClient | None = None,
        attachment_naming_service=None,
    ) -> None:
        self.client = (
            client
            or SmartsheetClient(
                sheet_id_env_var=(
                    "SMARTSHEET_AI_DESTINATION_SHEET_ID"
                )
            )
        )

        self.attachment_naming_service = (
            attachment_naming_service
            or DocumentAttachmentNamingService()
        )

    def write(
        self,
        *,
        mapping: SmartsheetRowMappingResult,
        destination_validation: (
            SmartsheetDestinationValidationResult
        ),
        attachment_source_path: str | Path | None = None,
        filename_policy_result: Any = None,
    ) -> SmartsheetReviewedWriteResult:
        """
        Add one Smartsheet row only after all write boundaries pass.
        """

        if not isinstance(
            mapping,
            SmartsheetRowMappingResult,
        ):
            return self._failure(
                "invalid_mapping"
            )

        if not isinstance(
            destination_validation,
            SmartsheetDestinationValidationResult,
        ):
            return self._failure(
                "invalid_destination_validation"
            )

        if not mapping.ready_for_write:
            return self._failure(
                "mapping_not_ready"
            )

        if not destination_validation.ready_for_write:
            return self._failure(
                "destination_not_ready"
            )

        if not isinstance(
            mapping.values,
            dict,
        ):
            return self._failure(
                "invalid_mapping_values"
            )

        if not mapping.values:
            return self._failure(
                "empty_mapping"
            )

        if not isinstance(
            destination_validation.column_ids,
            dict,
        ):
            return self._failure(
                "invalid_column_ids"
            )

        mapping_columns = set(
            mapping.values.keys()
        )

        validated_columns = set(
            destination_validation.column_ids.keys()
        )

        if mapping_columns != validated_columns:
            return self._failure(
                "destination_mismatch"
            )

        row_result = self.create_row(
            mapping=mapping,
            destination_validation=destination_validation,
        )
        if not row_result.success:
            if row_result.written and attachment_source_path is not None:
                preparation_arguments = {"source_path": attachment_source_path}
                if filename_policy_result is not None:
                    preparation_arguments["filename_policy_result"] = filename_policy_result
                preparation = self.attachment_naming_service.prepare(**preparation_arguments)
                if preparation.success:
                    self.attachment_naming_service.cleanup(preparation.temporary_path)
                return SmartsheetReviewedWriteResult(
                    written=True, column_count=row_result.column_count,
                    attachment_written=False, success=False, status=row_result.status,
                )
            return self._failure(row_result.status)

        attachment_written = False
        if attachment_source_path is not None:
            attachment_result = self.attach_to_existing_row(
                row_id=row_result.row_id,
                attachment_source_path=attachment_source_path,
                filename_policy_result=filename_policy_result,
            )
            if not attachment_result.success:
                return SmartsheetReviewedWriteResult(
                    written=True, column_count=row_result.column_count,
                    attachment_written=attachment_result.written,
                    success=False, status=attachment_result.status,
                )
            attachment_written = True

        return SmartsheetReviewedWriteResult(
            written=True, column_count=row_result.column_count,
            attachment_written=attachment_written, success=True,
            status=("written_with_attachment_naming_review"
                    if attachment_written and attachment_result.status == "attachment_written_naming_review"
                    else "written_with_attachment" if attachment_written else "written"),
        )

    def create_row(self, *, mapping, destination_validation) -> SmartsheetRowWriteOperationResult:
        validation_status = self._validate_write_inputs(mapping, destination_validation)
        if validation_status is not None:
            return self._row_result(
                destination_validation,
                status=validation_status,
                rejection_safe_category=(
                    destination_validation.rejection_safe_category
                    if isinstance(
                        destination_validation,
                        SmartsheetDestinationValidationResult,
                    )
                    and destination_validation.rejection_safe_category != "none"
                    else validation_status
                ),
            )
        cells = []

        for column_name, value in mapping.values.items():
            column_id = (
                destination_validation
                .column_ids
                .get(
                    column_name
                )
            )

            if not self._is_valid_column_id(
                column_id
            ):
                return self._row_result(
                    destination_validation,
                    status="invalid_column_id",
                    rejection_safe_category="row_mapping_invalid_column_id",
                    rejected_field_categories=(
                        "row_mapping_invalid_column_id",
                    ),
                )

            column_type = destination_validation.column_types.get(column_name)
            rejection_category = (
                SmartsheetDestinationValidationService()
                .value_rejection_category(
                    value=value,
                    column_type=column_type or "",
                )
            )
            if rejection_category is not None:
                return self._row_result(
                    destination_validation,
                    status="destination_type_not_ready",
                    rejection_safe_category=rejection_category,
                    rejected_field_categories=(rejection_category,),
                )

            cell = smartsheet.models.Cell()
            cell.column_id = column_id
            cell.value = value

            serialized_cell = cell.to_dict()
            if "value" not in serialized_cell or serialized_cell["value"] is None:
                return self._row_result(
                    destination_validation,
                    status="row_mapping_unsupported_value_type",
                    rejection_safe_category="row_mapping_unsupported_value_type",
                    rejected_field_categories=(
                        "row_mapping_unsupported_value_type",
                    ),
                )

            cells.append(
                cell
            )

        if not cells:
            return self._row_result(
                destination_validation,
                status="empty_mapping",
                rejection_safe_category="row_mapping_empty",
            )

        try:
            row = self.client.add_row(
                cells
            )
        except smartsheet.exceptions.ServerTimeoutExceededError:
            return self._row_result(
                destination_validation,
                column_count=len(cells), status="row_write_timeout",
                request_attempted=True, retryable=False,
            )
        except smartsheet.exceptions.ApiError as error:
            api_error_code, api_status_class = self._safe_api_diagnostics(error)
            return self._row_result(
                destination_validation,
                column_count=len(cells), status="row_write_api_rejected",
                request_attempted=True, outcome_proven=True, retryable=False,
                rejection_safe_category=self._api_rejection_category(
                    api_error_code
                ),
                api_status_class=api_status_class,
                api_error_code=api_error_code,
            )
        except smartsheet.exceptions.UnexpectedRequestError as error:
            cause = getattr(error, "__cause__", None)
            category = (
                "row_write_timeout"
                if cause is not None and "timeout" in type(cause).__name__.lower()
                else "row_write_outcome_unknown"
            )
            return self._row_result(
                destination_validation,
                column_count=len(cells), status=category,
                request_attempted=True, retryable=False,
            )
        except smartsheet.exceptions.HttpError:
            return self._row_result(
                destination_validation,
                column_count=len(cells),
                status="row_write_outcome_unknown",
                request_attempted=True, retryable=False,
            )
        except (AttributeError, IndexError, KeyError, TypeError):
            return self._row_result(
                destination_validation,
                column_count=len(cells),
                status="row_write_response_invalid",
                request_attempted=True, retryable=False,
            )
        except Exception:
            return self._row_result(
                destination_validation,
                column_count=len(cells),
                status="row_write_outcome_unknown",
                request_attempted=True, retryable=False,
            )
        row_id = getattr(row, "id", None)
        if not self._is_valid_column_id(row_id):
            return self._row_result(
                destination_validation,
                column_count=len(cells), status="row_write_response_invalid",
                request_attempted=True, retryable=False,
            )
        return self._row_result(
            destination_validation,
            written=True, row_id=row_id, column_count=len(cells),
            success=True, status="row_written", request_attempted=True,
            outcome_proven=True, retryable=False,
        )

    def attach_to_existing_row(self, *, row_id, attachment_source_path,
                               filename_policy_result: Any = None,
                               technical_attachment_name: str | None = None) -> SmartsheetAttachmentWriteOperationResult:
        if not self._is_valid_column_id(row_id):
            return SmartsheetAttachmentWriteOperationResult(False, False, "invalid_written_row_id")
        temporary_path = None
        try:
            preparation_arguments = {
                "source_path": attachment_source_path,
            }
            if filename_policy_result is not None:
                preparation_arguments["filename_policy_result"] = (
                    filename_policy_result
                )
            if technical_attachment_name is not None and hasattr(self.attachment_naming_service, "prepare_technical"):
                preparation = self.attachment_naming_service.prepare_technical(
                    source_path=attachment_source_path, technical_name=technical_attachment_name)
            else:
                preparation = self.attachment_naming_service.prepare(**preparation_arguments)

            if not preparation.success:
                return SmartsheetAttachmentWriteOperationResult(False, False, preparation.status)

            temporary_path = (
                preparation.temporary_path
            )

            try:
                self.client.attach_file_to_row(
                    row_id,
                    temporary_path,
                )
            except Exception:
                self.attachment_naming_service.cleanup(
                    temporary_path
                )

                return SmartsheetAttachmentWriteOperationResult(False, False, "smartsheet_attachment_failed")

            if not self.attachment_naming_service.cleanup(
                temporary_path
            ):
                return SmartsheetAttachmentWriteOperationResult(True, False, "attachment_cleanup_failed")
            return SmartsheetAttachmentWriteOperationResult(
                True, True,
                "attachment_written_naming_review"
                if preparation.status == "prepared_naming_fallback_review"
                else "attachment_written",
            )
        except Exception:
            if temporary_path is not None:
                self.attachment_naming_service.cleanup(temporary_path)
            return SmartsheetAttachmentWriteOperationResult(False, False, "attachment_preparation_failed")

    @staticmethod
    def _validate_write_inputs(mapping, destination_validation) -> str | None:
        if not isinstance(mapping, SmartsheetRowMappingResult): return "invalid_mapping"
        if not isinstance(destination_validation, SmartsheetDestinationValidationResult): return "invalid_destination_validation"
        if not mapping.ready_for_write: return "mapping_not_ready"
        if not destination_validation.ready_for_write: return "destination_not_ready"
        if not destination_validation.mapping_validation_passed: return "mapping_not_ready"
        if not destination_validation.schema_validation_passed: return "destination_schema_not_ready"
        if not destination_validation.type_validation_passed: return "destination_type_not_ready"
        if not isinstance(mapping.values, dict): return "invalid_mapping_values"
        if not mapping.values: return "empty_mapping"
        if not isinstance(destination_validation.column_ids, dict): return "invalid_column_ids"
        if not isinstance(destination_validation.column_types, dict): return "invalid_column_types"
        if set(mapping.values) != set(destination_validation.column_ids): return "destination_mismatch"
        if set(mapping.values) != set(destination_validation.column_types): return "destination_type_mismatch"
        if any(value is None for value in mapping.values.values()): return "row_mapping_value_missing"
        return None

    @staticmethod
    def _safe_api_diagnostics(error: Any) -> tuple[int | None, str]:
        result = getattr(getattr(error, "error", None), "result", None)
        raw_code = getattr(result, "code", None)
        if raw_code is None:
            raw_code = getattr(result, "error_code", None)
        code = (
            raw_code
            if isinstance(raw_code, int)
            and not isinstance(raw_code, bool)
            and 0 < raw_code <= 999999
            else None
        )
        raw_status = getattr(result, "status_code", None)
        status_class = (
            f"{raw_status // 100}xx"
            if isinstance(raw_status, int)
            and not isinstance(raw_status, bool)
            and 100 <= raw_status <= 599
            else "unavailable"
        )
        return code, status_class

    @staticmethod
    def _api_rejection_category(code: int | None) -> str:
        categories = {
            1001: "row_write_api_permission_denied",
            1002: "row_write_api_permission_denied",
            1004: "row_write_api_permission_denied",
            1005: "row_write_api_permission_denied",
            1006: "row_write_api_destination_unavailable",
            1008: "row_write_api_request_invalid",
            1011: "row_write_api_request_invalid",
            1012: "row_write_api_request_invalid",
            1013: "row_write_api_cell_invalid",
            1014: "row_write_api_cell_invalid",
            1032: "row_write_api_column_not_writable",
            1042: "row_write_api_cell_invalid",
            4003: "row_write_api_rate_limited",
        }
        return categories.get(code, "row_write_api_rejected")

    @staticmethod
    def _row_result(
        destination_validation: Any,
        *,
        written: bool = False,
        row_id: int | None = None,
        column_count: int = 0,
        success: bool = False,
        status: str = "smartsheet_write_failed",
        request_attempted: bool = False,
        outcome_proven: bool = False,
        retryable: bool = False,
        rejected_field_categories: tuple[str, ...] | None = None,
        rejection_safe_category: str | None = None,
        api_status_class: str = "unavailable",
        api_error_code: int | None = None,
    ) -> SmartsheetRowWriteOperationResult:
        validation = (
            destination_validation
            if isinstance(
                destination_validation,
                SmartsheetDestinationValidationResult,
            )
            else SmartsheetDestinationValidationResult()
        )
        return SmartsheetRowWriteOperationResult(
            written=written,
            row_id=row_id,
            column_count=column_count,
            success=success,
            status=status,
            request_attempted=request_attempted,
            outcome_proven=outcome_proven,
            retryable=retryable,
            mapped_field_count=validation.mapped_field_count,
            included_cell_count=(column_count or validation.included_cell_count),
            omitted_field_count=validation.omitted_field_count,
            mapping_validation_passed=validation.mapping_validation_passed,
            schema_validation_passed=validation.schema_validation_passed,
            type_validation_passed=validation.type_validation_passed,
            rejected_field_categories=(
                tuple(validation.rejected_field_categories)
                if rejected_field_categories is None
                else tuple(rejected_field_categories)
            ),
            rejection_safe_category=(
                validation.rejection_safe_category
                if rejection_safe_category is None
                else rejection_safe_category
            ),
            api_status_class=api_status_class,
            api_error_code=api_error_code,
        )

    @staticmethod
    def _is_valid_column_id(
        value: Any,
    ) -> bool:
        if isinstance(
            value,
            bool,
        ):
            return False

        return (
            isinstance(
                value,
                int,
            )
            and value > 0
        )

    @staticmethod
    def _failure(
        status: str,
    ) -> SmartsheetReviewedWriteResult:
        return SmartsheetReviewedWriteResult(
            written=False,
            column_count=0,
            attachment_written=False,
            success=False,
            status=status,
        )
