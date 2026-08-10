from dataclasses import dataclass
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
                return self._failure(
                    "invalid_column_id"
                )

            cell = smartsheet.models.Cell()
            cell.column_id = column_id
            cell.value = value

            cells.append(
                cell
            )

        if not cells:
            return self._failure(
                "empty_mapping"
            )

        temporary_path = None

        try:
            row = self.client.add_row(
                cells
            )
        except Exception:
            return self._failure(
                "smartsheet_write_failed"
            )

        attachment_written = False

        if attachment_source_path is not None:
            preparation = (
                self.attachment_naming_service.prepare(
                    source_path=attachment_source_path
                )
            )

            if not preparation.success:
                return SmartsheetReviewedWriteResult(
                    written=True,
                    column_count=len(cells),
                    attachment_written=False,
                    success=False,
                    status=preparation.status,
                )

            temporary_path = (
                preparation.temporary_path
            )

            row_id = getattr(
                row,
                "id",
                None,
            )

            if (
                isinstance(row_id, bool)
                or not isinstance(row_id, int)
                or row_id <= 0
            ):
                self.attachment_naming_service.cleanup(
                    temporary_path
                )

                return SmartsheetReviewedWriteResult(
                    written=True,
                    column_count=len(cells),
                    attachment_written=False,
                    success=False,
                    status="invalid_written_row_id",
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

                return SmartsheetReviewedWriteResult(
                    written=True,
                    column_count=len(cells),
                    attachment_written=False,
                    success=False,
                    status="smartsheet_attachment_failed",
                )

            attachment_written = True

            if not self.attachment_naming_service.cleanup(
                temporary_path
            ):
                return SmartsheetReviewedWriteResult(
                    written=True,
                    column_count=len(cells),
                    attachment_written=True,
                    success=False,
                    status="attachment_cleanup_failed",
                )

        return SmartsheetReviewedWriteResult(
            written=True,
            column_count=len(
                cells
            ),
            attachment_written=attachment_written,
            success=True,
            status=(
                "written_with_attachment"
                if attachment_written
                else "written"
            ),
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
