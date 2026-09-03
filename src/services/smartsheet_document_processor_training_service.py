"""Least-privilege Smartsheet adapters for Document Processor Training."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from src.clients.smartsheet_client import SmartsheetClient
from src.models.smartsheet_mapping import SmartsheetRowMappingResult
from src.services.document_processor_training_contracts import (
    AI_CORRECTION,
    AI_CORRECTION_STATUS,
    AI_CORRECTION_TYPE,
    AI_PROPOSED_CORRECTION,
    AI_RESOLUTION_RESULT,
    APPROVE_AI_CORRECTION,
    APPROVE_AI_RESOLUTION,
    CORRECTION_STATUSES,
    CORRECTION_TYPES,
    CorrectionComment,
    CorrectionRow,
    CorrectionSchemaResult,
    HUMAN_OWNED_COLUMNS,
    REQUIRED_COLUMNS,
    WORKFLOW_OWNED_COLUMNS,
    normalize_checkbox,
)
from src.services.smartsheet_destination_schema_service import (
    SmartsheetDestinationSchemaService,
)
from src.services.smartsheet_destination_validation_service import (
    SmartsheetDestinationValidationService,
)
from src.services.smartsheet_review_configuration_service import (
    APPROVED_DOCUMENT_FIELD_POLICIES,
)
from src.services.smartsheet_review_row_mapping_service import (
    SmartsheetReviewRowMappingService,
)


ALLOWED_COLUMN_TYPES = {
    AI_CORRECTION: frozenset({"CHECKBOX"}),
    AI_PROPOSED_CORRECTION: frozenset({"TEXT_NUMBER"}),
    AI_CORRECTION_TYPE: frozenset({"TEXT_NUMBER", "PICKLIST"}),
    APPROVE_AI_CORRECTION: frozenset({"CHECKBOX"}),
    AI_CORRECTION_STATUS: frozenset({"TEXT_NUMBER", "PICKLIST"}),
    APPROVE_AI_RESOLUTION: frozenset({"CHECKBOX"}),
    AI_RESOLUTION_RESULT: frozenset({"TEXT_NUMBER"}),
}
APPROVED_CONTEXT_COLUMNS = frozenset(
    set(SmartsheetReviewRowMappingService.OPERATIONAL_METADATA_COLUMNS)
    | {policy.column_name for policy in APPROVED_DOCUMENT_FIELD_POLICIES}
    | {
        policy.confidence_column_name
        for policy in APPROVED_DOCUMENT_FIELD_POLICIES
        if policy.confidence_column_name
    }
) - REQUIRED_COLUMNS


@dataclass(frozen=True)
class CorrectionWriteResult:
    success: bool
    status: str
    field_count: int
    request_attempted: bool
    outcome_proven: bool


class SmartsheetCorrectionSchemaService:
    """Resolve exactly the seven existing correction columns."""

    def __init__(self, *, client: SmartsheetClient | None = None) -> None:
        self.client = client or SmartsheetClient(
            sheet_id_env_var="SMARTSHEET_AI_DESTINATION_SHEET_ID"
        )

    def read(self) -> CorrectionSchemaResult:
        try:
            response = self.client.get_columns()
            raw_columns = list(getattr(response, "data", response))
        except Exception:
            return self._failure("schema_read_failed")
        selected = [
            column for column in raw_columns
            if getattr(column, "title", None) in REQUIRED_COLUMNS
        ]
        if len(selected) != len(REQUIRED_COLUMNS):
            return self._failure("schema_missing_or_duplicate_columns")
        ids: dict[str, int] = {}
        types: dict[str, str] = {}
        system_types: dict[str, str] = {}
        for column in selected:
            title = getattr(column, "title", None)
            column_id = getattr(column, "id", None)
            column_type = str(getattr(column, "type", "") or "").strip().upper()
            system_type = SmartsheetDestinationSchemaService.system_column_type_category(
                getattr(column, "system_column_type", None)
            )
            formula = str(getattr(column, "formula", "") or "").strip()
            if (
                not isinstance(title, str)
                or title in ids
                or isinstance(column_id, bool)
                or not isinstance(column_id, int)
                or column_id <= 0
                or column_type not in ALLOWED_COLUMN_TYPES.get(title, ())
                or system_type != "none"
                or bool(formula)
            ):
                return self._failure("schema_incompatible")
            if column_type == "PICKLIST":
                options = tuple(getattr(column, "options", ()) or ())
                required_options = (
                    CORRECTION_TYPES
                    if title == AI_CORRECTION_TYPE
                    else CORRECTION_STATUSES
                )
                if (
                    any(not isinstance(option, str) for option in options)
                    or not set(required_options).issubset(options)
                ):
                    return self._failure("schema_picklist_options_incompatible")
            ids[title] = column_id
            types[title] = column_type
            system_types[title] = system_type
        if len(set(ids.values())) != len(ids):
            return self._failure("schema_duplicate_destinations")
        context_ids: dict[str, int] = {}
        for column in raw_columns:
            title = getattr(column, "title", None)
            column_id = getattr(column, "id", None)
            if title not in APPROVED_CONTEXT_COLUMNS:
                continue
            if (
                title in context_ids
                or isinstance(column_id, bool)
                or not isinstance(column_id, int)
                or column_id <= 0
            ):
                return self._failure("context_schema_incompatible")
            context_ids[title] = column_id
        if set(context_ids.values()).intersection(ids.values()):
            return self._failure("context_schema_incompatible")
        return CorrectionSchemaResult(
            success=True,
            status="ready",
            column_count=len(ids),
            column_ids=ids,
            column_types=types,
            system_column_types=system_types,
            context_column_ids=context_ids,
        )

    @staticmethod
    def _failure(status: str) -> CorrectionSchemaResult:
        return CorrectionSchemaResult(False, status, 0, {}, {}, {}, {})


class SmartsheetCorrectionReader:
    """Read selected correction cells and row discussions without attachments."""

    def __init__(self, *, client: SmartsheetClient) -> None:
        self.client = client

    def read_rows(self, *, schema: CorrectionSchemaResult) -> tuple[CorrectionRow, ...]:
        if not schema.success:
            raise ValueError("correction_schema_not_ready")
        version, rows = self.client.get_selected_rows(
            column_ids=list(schema.column_ids.values())
        )
        return tuple(self._normalize_row(row, version=version, schema=schema) for row in rows)

    def read_context_row(
        self, *, row_id: int, schema: CorrectionSchemaResult
    ) -> CorrectionRow:
        """Load approved protected context only after a row is flagged."""
        if not schema.success:
            raise ValueError("correction_schema_not_ready")
        version, row = self.client.get_selected_row(
            row_id=row_id,
            column_ids=(
                list(schema.column_ids.values())
                + list(schema.context_column_ids.values())
            ),
        )
        return self._normalize_row(row, version=version, schema=schema)

    def read_row(self, *, row_id: int, schema: CorrectionSchemaResult) -> CorrectionRow:
        if not schema.success:
            raise ValueError("correction_schema_not_ready")
        version, row = self.client.get_selected_row(
            row_id=row_id,
            column_ids=list(schema.column_ids.values()),
            # Exact correction rereads deliberately omit protected context values.
        )
        return self._normalize_row(row, version=version, schema=schema)

    def read_comments(self, *, row_id: int) -> tuple[CorrectionComment, ...]:
        discussions = self.client.get_row_discussions(row_id=row_id)
        comments = []
        for discussion in discussions:
            discussion_id = getattr(discussion, "id", None)
            if isinstance(discussion_id, bool) or not isinstance(discussion_id, int):
                raise RuntimeError("discussion_identity_invalid")
            for comment in list(getattr(discussion, "comments", []) or []):
                comment_id = getattr(comment, "id", None)
                text = getattr(comment, "text", None)
                if (
                    isinstance(comment_id, bool)
                    or not isinstance(comment_id, int)
                    or not isinstance(text, str)
                ):
                    raise RuntimeError("comment_contract_invalid")
                created_by = getattr(comment, "created_by", None)
                author = str(getattr(created_by, "name", "") or "").strip()
                comments.append(CorrectionComment(
                    discussion_id=discussion_id,
                    comment_id=comment_id,
                    created_at=str(getattr(comment, "created_at", "") or ""),
                    modified_at=str(getattr(comment, "modified_at", "") or ""),
                    author_display=author,
                    text=text,
                ))
        return tuple(sorted(comments, key=lambda item: (
            item.modified_at or item.created_at, item.discussion_id, item.comment_id
        )))

    @staticmethod
    def _normalize_row(
        row: Any,
        *,
        version: int,
        schema: CorrectionSchemaResult,
    ) -> CorrectionRow:
        row_id = getattr(row, "id", None)
        if isinstance(row_id, bool) or not isinstance(row_id, int) or row_id <= 0:
            raise RuntimeError("correction_row_identity_invalid")
        titles = {
            column_id: title
            for title, column_id in {
                **schema.column_ids,
                **schema.context_column_ids,
            }.items()
        }
        values = {title: None for title in REQUIRED_COLUMNS | APPROVED_CONTEXT_COLUMNS}
        seen_columns: set[int] = set()
        for cell in list(getattr(row, "cells", []) or []):
            column_id = getattr(cell, "column_id", None)
            title = titles.get(column_id)
            if title is not None:
                if column_id in seen_columns:
                    raise RuntimeError("correction_row_duplicate_cell")
                seen_columns.add(column_id)
                value = getattr(cell, "value", None)
                if title in WORKFLOW_OWNED_COLUMNS:
                    if value is not None and not isinstance(value, str):
                        raise RuntimeError("correction_workflow_value_invalid")
                elif title not in HUMAN_OWNED_COLUMNS:
                    if (
                        value is not None
                        and not isinstance(value, (str, bool, int, float))
                    ):
                        raise RuntimeError("correction_context_value_invalid")
                    if isinstance(value, float) and not math.isfinite(value):
                        raise RuntimeError("correction_context_value_invalid")
                values[title] = value
        for title in HUMAN_OWNED_COLUMNS:
            values[title] = normalize_checkbox(values[title])
        return CorrectionRow(row_id=row_id, values=values, sheet_version=version)


class SmartsheetCorrectionWriter:
    """Update only DP Training-owned cells with validation and exact readback."""

    def __init__(
        self,
        *,
        client: SmartsheetClient,
        reader: SmartsheetCorrectionReader,
        validation_service: SmartsheetDestinationValidationService | None = None,
    ) -> None:
        self.client = client
        self.reader = reader
        self.validation_service = validation_service or SmartsheetDestinationValidationService()

    def write(
        self,
        *,
        row_id: int,
        updates: dict[str, Any],
        schema: CorrectionSchemaResult,
        expected_proposal_hash_values: dict[str, Any] | None = None,
    ) -> CorrectionWriteResult:
        if not isinstance(updates, dict) or not updates or not set(updates) <= WORKFLOW_OWNED_COLUMNS:
            return CorrectionWriteResult(False, "workflow_write_scope_invalid", 0, False, True)
        if set(updates).intersection(HUMAN_OWNED_COLUMNS):
            return CorrectionWriteResult(False, "human_owned_write_blocked", 0, False, True)
        if any(value is None for value in updates.values()):
            return CorrectionWriteResult(False, "workflow_write_value_missing", 0, False, True)
        if any(not isinstance(value, str) or not value.strip() for value in updates.values()):
            return CorrectionWriteResult(False, "workflow_write_value_invalid", 0, False, True)
        if (
            AI_CORRECTION_TYPE in updates
            and updates[AI_CORRECTION_TYPE] not in CORRECTION_TYPES
        ):
            return CorrectionWriteResult(False, "workflow_write_vocabulary_invalid", 0, False, True)
        if (
            AI_CORRECTION_STATUS in updates
            and updates[AI_CORRECTION_STATUS] not in CORRECTION_STATUSES
        ):
            return CorrectionWriteResult(False, "workflow_write_vocabulary_invalid", 0, False, True)
        validation_types = dict(schema.column_types)
        for title in updates:
            if validation_types.get(title) == "PICKLIST":
                validation_types[title] = "TEXT_NUMBER"
        mapping = SmartsheetRowMappingResult(values=dict(updates), ready_for_write=True)
        validation = self.validation_service.validate(
            mapping,
            schema.column_ids,
            validation_types,
            schema.system_column_types,
        )
        if not validation.ready_for_write:
            return CorrectionWriteResult(False, "workflow_write_validation_failed", 0, False, True)
        try:
            before = self.reader.read_row(row_id=row_id, schema=schema)
        except Exception:
            return CorrectionWriteResult(False, "workflow_write_precondition_unavailable", 0, False, True)
        expected = expected_proposal_hash_values or {}
        if not isinstance(expected, dict) or not set(expected) <= WORKFLOW_OWNED_COLUMNS:
            return CorrectionWriteResult(False, "workflow_write_precondition_invalid", 0, False, True)
        if any(before.values.get(title) != value for title, value in expected.items()):
            return CorrectionWriteResult(False, "workflow_write_stale", 0, False, True)
        if all(before.values.get(title) == value for title, value in updates.items()):
            return CorrectionWriteResult(
                True, "workflow_write_already_reconciled", len(updates), False, True
            )
        payload = {
            validation.column_ids[title]: value
            for title, value in updates.items()
        }
        try:
            self.client.update_row(row_id, payload)
        except Exception:
            return self._reconcile(row_id=row_id, updates=updates, schema=schema, attempted=True)
        return self._reconcile(row_id=row_id, updates=updates, schema=schema, attempted=True)

    def _reconcile(
        self,
        *,
        row_id: int,
        updates: dict[str, Any],
        schema: CorrectionSchemaResult,
        attempted: bool,
    ) -> CorrectionWriteResult:
        try:
            after = self.reader.read_row(row_id=row_id, schema=schema)
        except Exception:
            return CorrectionWriteResult(
                False, "workflow_write_outcome_unresolved", 0, attempted, False
            )
        if all(after.values.get(title) == value for title, value in updates.items()):
            return CorrectionWriteResult(
                True, "workflow_write_reconciled", len(updates), attempted, True
            )
        return CorrectionWriteResult(False, "workflow_write_rejected", 0, attempted, True)
