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
            return SmartsheetRowWriteOperationResult(False, status=validation_status)
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
                return SmartsheetRowWriteOperationResult(False, status="invalid_column_id")

            cell = smartsheet.models.Cell()
            cell.column_id = column_id
            cell.value = value

            cells.append(
                cell
            )

        if not cells:
            return SmartsheetRowWriteOperationResult(False, status="empty_mapping")

        try:
            row = self.client.add_row(
                cells
            )
        except Exception:
            return SmartsheetRowWriteOperationResult(False, status="smartsheet_write_failed")
        row_id = getattr(row, "id", None)
        if not self._is_valid_column_id(row_id):
            return SmartsheetRowWriteOperationResult(True, status="invalid_written_row_id", column_count=len(cells))
        return SmartsheetRowWriteOperationResult(True, row_id, len(cells), True, "row_written")

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
        if not isinstance(mapping.values, dict): return "invalid_mapping_values"
        if not mapping.values: return "empty_mapping"
        if not isinstance(destination_validation.column_ids, dict): return "invalid_column_ids"
        if set(mapping.values) != set(destination_validation.column_ids): return "destination_mismatch"
        return None

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
