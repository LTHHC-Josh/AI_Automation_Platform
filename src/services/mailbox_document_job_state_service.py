from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any
import uuid


STAGES = {
    "discovered", "processing", "row_write_pending", "row_create_in_flight",
    "row_write_uncertain", "row_retry_ready",
    "row_written", "attachment_write_pending", "attachment_write_uncertain",
    "attachment_written", "blocked_permanent",
}

RECONCILIATION_CARDINALITIES = {
    "not_attempted", "zero", "one", "multiple", "unavailable",
}

ROW_RECOVERY_STATES = {
    "none", "reconcile_only", "retry_ready", "blocked",
}


@dataclass(frozen=True, repr=False)
class MailboxDocumentWorkItem:
    job_key: str = field(repr=False)
    message_key: str = field(repr=False)
    attachment_key: str = field(repr=False)
    document_key: str = field(repr=False)
    local_path: Path = field(repr=False)
    status: str = "discovered"
    document: Any = field(default=None, repr=False, compare=False)
    lease_token: str | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True, repr=False)
class MailboxDocumentJobState:
    schema_version: int
    job_key: str = field(repr=False)
    message_key: str = field(repr=False)
    attachment_key: str = field(repr=False)
    document_key: str = field(repr=False)
    stage: str
    smartsheet_row_id: int | None = field(default=None, repr=False)
    attachment_required: bool = True
    row_attempt_count: int = 0
    attachment_attempt_count: int = 0
    last_failure_category: str | None = None
    retryable: bool = True
    lease_token: str | None = field(default=None, repr=False)
    lease_expires_at: str | None = None
    updated_at: str = ""
    attachment_filename: str | None = field(default=None, repr=False)
    attachment_naming_status: str | None = None
    attachment_business_filename_attempted: bool = False
    attachment_required_component_failure_count: int = 0
    attachment_optional_component_omission_count: int = 0
    attachment_placeholder_categories: tuple[str, ...] = ()
    attachment_technical_fallback_reason: str = "none"
    row_create_attempted: bool = False
    row_outcome_proven: bool = False
    row_reconciliation_attempted: bool = False
    row_reconciliation_match_cardinality: str = "not_attempted"
    row_recovery_state: str = "none"
    recoverable: bool = False
    attachment_blocked_due_to_unresolved_row: bool = False


@dataclass(frozen=True)
class MailboxDocumentJobStateResult:
    success: bool
    status: str
    state: MailboxDocumentJobState | None = field(default=None, repr=False)


@dataclass(frozen=True)
class MailboxDocumentJobBatchSummary:
    """PHI-safe aggregate derived from explicitly selected durable jobs."""

    completed_document_count: int
    pending_document_count: int | None
    row_attempt_count: int | None
    attachment_attempt_count: int | None
    failure_category: str | None
    retryable: bool
    recoverable: bool
    row_create_attempted: bool
    row_outcome_proven: bool
    row_reconciliation_attempted: bool
    row_reconciliation_match_cardinality: str
    row_recovery_state: str
    attachment_blocked_due_to_unresolved_row: bool
    success: bool
    status: str


class MailboxDocumentJobStateService:
    SCHEMA_VERSION = 2
    DEFAULT_STATE_DIR = Path("data/mailbox_processing_state/jobs")
    _DIGEST_LENGTH = 64

    def __init__(self, state_dir: str | Path | None = None, *, lease_seconds: int = 900):
        self.state_dir = Path(state_dir or self.DEFAULT_STATE_DIR)
        self.lease_seconds = max(1, int(lease_seconds))

    @staticmethod
    def message_key(message_id: Any) -> str | None:
        if not isinstance(message_id, str) or not message_id.strip():
            return None
        return hashlib.sha256(message_id.strip().encode("utf-8")).hexdigest()

    @classmethod
    def job_key(cls, message_key: str, attachment_key: str, document_key: str) -> str | None:
        if not all(cls._valid_digest(value) for value in (message_key, attachment_key, document_key)):
            return None
        material = f"mailbox-document-job:v1:{message_key}:{attachment_key}:{document_key}"
        return hashlib.sha256(material.encode("ascii")).hexdigest()

    def discover(self, *, message_key: str, attachment_key: str, document_key: str,
                 attachment_required: bool = True) -> MailboxDocumentJobStateResult:
        job_key = self.job_key(message_key, attachment_key, document_key)
        if job_key is None:
            return self._failure("invalid_job_identity")
        existing = self.load(job_key)
        if existing.success:
            state = existing.state
            if state and (state.message_key, state.attachment_key, state.document_key) != (
                message_key, attachment_key, document_key
            ):
                return self._failure("state_inconsistent")
            return existing
        if existing.status != "state_not_found":
            return existing
        now = self._utc_now()
        state = MailboxDocumentJobState(
            schema_version=self.SCHEMA_VERSION, job_key=job_key, message_key=message_key,
            attachment_key=attachment_key, document_key=document_key, stage="discovered",
            attachment_required=bool(attachment_required), updated_at=now,
        )
        return self._create(state)

    def load(self, job_key: str) -> MailboxDocumentJobStateResult:
        if not self._valid_digest(job_key):
            return self._failure("invalid_job_key")
        path = self.state_dir / f"{job_key}.json"
        try:
            if not path.is_file():
                return self._failure("state_not_found")
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            return self._failure("state_unavailable")
        except json.JSONDecodeError:
            return self._failure("state_corrupt")
        return self._decode(payload, expected_job_key=job_key)

    def acquire_processing_lease(self, job_key: str) -> MailboxDocumentJobStateResult:
        return self._mutate(job_key, self._acquire_lease)

    def acquire_business_action_lease(self, job_key: str) -> MailboxDocumentJobStateResult:
        return self._mutate(job_key, self._acquire_business_action_lease)

    def summarize(self, job_keys) -> MailboxDocumentJobBatchSummary:
        """Summarize only the supplied durable jobs without directory enumeration."""
        try:
            keys = list(dict.fromkeys(job_keys))
        except (TypeError, ValueError):
            return self._summary_failure("invalid_job_keys")
        if any(not self._valid_digest(key) for key in keys):
            return self._summary_failure("invalid_job_key")

        states = []
        for key in keys:
            loaded = self.load(key)
            if not loaded.success or loaded.state is None:
                return self._summary_failure(loaded.status)
            states.append(loaded.state)

        completed = sum(state.stage == "attachment_written" for state in states)
        pending = len(states) - completed
        row_attempts = sum(state.row_attempt_count for state in states)
        attachment_attempts = sum(state.attachment_attempt_count for state in states)
        categories = []
        retryable = bool(pending)

        for state in states:
            if state.stage == "attachment_written":
                continue
            category, state_retryable = self._state_retry_disposition(state)
            categories.append(category)
            if not state_retryable:
                retryable = False

        distinct_categories = list(dict.fromkeys(categories))
        if not distinct_categories:
            failure_category = None
        elif len(distinct_categories) == 1:
            failure_category = distinct_categories[0]
        else:
            failure_category = "multiple_failures"

        cardinalities = {
            state.row_reconciliation_match_cardinality for state in states
        }
        recovery_states = {state.row_recovery_state for state in states}
        return MailboxDocumentJobBatchSummary(
            completed_document_count=completed,
            pending_document_count=pending,
            row_attempt_count=row_attempts,
            attachment_attempt_count=attachment_attempts,
            failure_category=failure_category,
            retryable=retryable,
            recoverable=any(state.recoverable for state in states),
            row_create_attempted=any(state.row_create_attempted for state in states),
            row_outcome_proven=all(state.row_outcome_proven for state in states),
            row_reconciliation_attempted=any(
                state.row_reconciliation_attempted for state in states
            ),
            row_reconciliation_match_cardinality=(
                next(iter(cardinalities)) if len(cardinalities) == 1 else "mixed"
            ),
            row_recovery_state=(
                next(iter(recovery_states)) if len(recovery_states) == 1 else "mixed"
            ),
            attachment_blocked_due_to_unresolved_row=any(
                state.attachment_blocked_due_to_unresolved_row for state in states
            ),
            success=True,
            status="ready",
        )

    def transition(self, job_key: str, *, expected_stages: set[str], stage: str,
                   lease_token: str | None = None, smartsheet_row_id: int | None = None,
                   failure_category: str | None = None, retryable: bool | None = None,
                   increment_row_attempt: bool = False,
                   increment_attachment_attempt: bool = False,
                   attachment_filename: str | None = None,
                   attachment_naming_status: str | None = None,
                   attachment_business_filename_attempted: bool | None = None,
                   attachment_required_component_failure_count: int | None = None,
                   attachment_optional_component_omission_count: int | None = None,
                   attachment_placeholder_categories: tuple[str, ...] | None = None,
                   attachment_technical_fallback_reason: str | None = None,
                   row_create_attempted: bool | None = None,
                   row_outcome_proven: bool | None = None,
                   row_reconciliation_attempted: bool | None = None,
                   row_reconciliation_match_cardinality: str | None = None,
                   row_recovery_state: str | None = None,
                   recoverable: bool | None = None,
                   attachment_blocked_due_to_unresolved_row: bool | None = None,
                   retain_lease: bool = False) -> MailboxDocumentJobStateResult:
        if stage not in STAGES or not expected_stages or not expected_stages <= STAGES:
            return self._failure("invalid_transition")
        def change(current: MailboxDocumentJobState):
            if current.stage not in expected_stages:
                return "state_conflict"
            if current.lease_token and lease_token != current.lease_token:
                return "lease_conflict"
            row_id = current.smartsheet_row_id if smartsheet_row_id is None else smartsheet_row_id
            if row_id is not None and (isinstance(row_id, bool) or not isinstance(row_id, int) or row_id <= 0):
                return "invalid_row_reference"
            values = asdict(current)
            filename = current.attachment_filename
            naming_status = current.attachment_naming_status
            business_attempted = current.attachment_business_filename_attempted
            required_failure_count = current.attachment_required_component_failure_count
            optional_omission_count = current.attachment_optional_component_omission_count
            placeholder_categories = current.attachment_placeholder_categories
            technical_fallback_reason = current.attachment_technical_fallback_reason
            if attachment_filename is not None:
                candidate = str(attachment_filename)
                if candidate != Path(candidate).name or any(c in candidate for c in "\\/\r\n"):
                    return "invalid_attachment_filename"
                filename = candidate
                naming_status = self._safe_category(attachment_naming_status)
                supplied_attempted = (
                    False
                    if attachment_business_filename_attempted is None
                    else attachment_business_filename_attempted
                )
                if not isinstance(supplied_attempted, bool):
                    return "invalid_filename_diagnostic"
                business_attempted = supplied_attempted
                counts = (
                    0 if attachment_required_component_failure_count is None
                    else attachment_required_component_failure_count,
                    0 if attachment_optional_component_omission_count is None
                    else attachment_optional_component_omission_count,
                )
                if any(
                    isinstance(value, bool) or not isinstance(value, int) or value < 0
                    for value in counts
                ):
                    return "invalid_filename_diagnostic"
                required_failure_count, optional_omission_count = counts
                categories = attachment_placeholder_categories or ()
                if not isinstance(categories, tuple) or any(
                    category not in {
                        "payer", "service", "document_type",
                        "document_subtype", "date",
                    }
                    for category in categories
                ):
                    return "invalid_filename_diagnostic"
                placeholder_categories = tuple(dict.fromkeys(categories))
                technical_fallback_reason = self._safe_category(
                    attachment_technical_fallback_reason
                ) or "none"
            supplied_booleans = {
                "row_create_attempted": row_create_attempted,
                "row_outcome_proven": row_outcome_proven,
                "row_reconciliation_attempted": row_reconciliation_attempted,
                "recoverable": recoverable,
                "attachment_blocked_due_to_unresolved_row": (
                    attachment_blocked_due_to_unresolved_row
                ),
            }
            if any(
                value is not None and not isinstance(value, bool)
                for value in supplied_booleans.values()
            ):
                return "invalid_operation_diagnostic"
            cardinality = (
                current.row_reconciliation_match_cardinality
                if row_reconciliation_match_cardinality is None
                else row_reconciliation_match_cardinality
            )
            if cardinality not in RECONCILIATION_CARDINALITIES:
                return "invalid_operation_diagnostic"
            recovery_state = (
                current.row_recovery_state
                if row_recovery_state is None else row_recovery_state
            )
            if recovery_state not in ROW_RECOVERY_STATES:
                return "invalid_operation_diagnostic"
            values.update(stage=stage, smartsheet_row_id=row_id,
                          last_failure_category=self._safe_category(failure_category),
                          retryable=current.retryable if retryable is None else bool(retryable),
                          lease_token=current.lease_token if retain_lease else None,
                          lease_expires_at=current.lease_expires_at if retain_lease else None,
                          updated_at=self._utc_now(),
                          row_attempt_count=current.row_attempt_count + int(increment_row_attempt),
                          attachment_attempt_count=current.attachment_attempt_count + int(increment_attachment_attempt),
                          attachment_filename=filename,
                          attachment_naming_status=naming_status,
                          attachment_business_filename_attempted=business_attempted,
                          attachment_required_component_failure_count=required_failure_count,
                          attachment_optional_component_omission_count=optional_omission_count,
                          attachment_placeholder_categories=placeholder_categories,
                          attachment_technical_fallback_reason=technical_fallback_reason,
                          row_create_attempted=(
                              current.row_create_attempted
                              if row_create_attempted is None else row_create_attempted
                          ),
                          row_outcome_proven=(
                              current.row_outcome_proven
                              if row_outcome_proven is None else row_outcome_proven
                          ),
                          row_reconciliation_attempted=(
                              current.row_reconciliation_attempted
                              if row_reconciliation_attempted is None
                              else row_reconciliation_attempted
                          ),
                          row_reconciliation_match_cardinality=cardinality,
                          row_recovery_state=recovery_state,
                          recoverable=(
                              current.recoverable if recoverable is None else recoverable
                          ),
                          attachment_blocked_due_to_unresolved_row=(
                              current.attachment_blocked_due_to_unresolved_row
                              if attachment_blocked_due_to_unresolved_row is None
                              else attachment_blocked_due_to_unresolved_row
                          ))
            return MailboxDocumentJobState(**values)
        return self._mutate(job_key, change)

    def _acquire_lease(self, current: MailboxDocumentJobState):
        if current.stage not in {"discovered", "processing", "row_retry_ready"}:
            return "state_conflict"
        now = datetime.now(timezone.utc)
        if current.stage == "processing" and current.lease_token and current.lease_expires_at:
            try:
                if datetime.fromisoformat(current.lease_expires_at) > now:
                    return "lease_active"
            except ValueError:
                return "state_corrupt"
        values = asdict(current)
        values.update(stage="processing", lease_token=uuid.uuid4().hex,
                      lease_expires_at=(now + timedelta(seconds=self.lease_seconds)).isoformat(),
                      updated_at=now.isoformat())
        return MailboxDocumentJobState(**values)

    def _acquire_business_action_lease(self, current: MailboxDocumentJobState):
        if current.stage not in {
            "row_write_pending", "row_create_in_flight", "row_write_uncertain",
            "row_written", "attachment_write_pending", "attachment_write_uncertain",
        }:
            return "state_conflict"
        now = datetime.now(timezone.utc)
        if current.lease_token and current.lease_expires_at:
            try:
                if datetime.fromisoformat(current.lease_expires_at) > now:
                    return "lease_active"
            except ValueError:
                return "state_corrupt"
        values = asdict(current)
        values.update(
            lease_token=uuid.uuid4().hex,
            lease_expires_at=(now + timedelta(seconds=self.lease_seconds)).isoformat(),
            updated_at=now.isoformat(),
        )
        return MailboxDocumentJobState(**values)

    def _state_retry_disposition(self, state: MailboxDocumentJobState):
        if not state.retryable:
            return (
                state.last_failure_category or state.stage,
                False,
            )
        if state.stage == "row_write_pending":
            return "processed_result_unavailable", False
        if state.stage in {"row_create_in_flight", "row_write_uncertain"}:
            return state.last_failure_category or state.stage, True
        if state.stage == "row_retry_ready":
            return state.last_failure_category or "row_reconciliation_zero_matches", True
        if state.stage in {"attachment_write_uncertain", "blocked_permanent"}:
            return state.last_failure_category or state.stage, False
        if state.stage == "processing" and self._lease_is_active(state):
            return "processing_lease_active", False
        if state.stage in {
            "discovered", "processing",
            "row_written",
            "attachment_write_pending",
        }:
            return "work_pending", True
        return "retryability_unresolved", False

    @staticmethod
    def _lease_is_active(state: MailboxDocumentJobState) -> bool:
        if not state.lease_token or not state.lease_expires_at:
            return False
        try:
            return datetime.fromisoformat(state.lease_expires_at) > datetime.now(timezone.utc)
        except ValueError:
            return True

    def _mutate(self, job_key: str, operation) -> MailboxDocumentJobStateResult:
        if not self._valid_digest(job_key):
            return self._failure("invalid_job_key")
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            lock = self.state_dir / f"{job_key}.lock"
            lock.mkdir()
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime <= self.lease_seconds:
                    return self._failure("state_locked")
                lock.rmdir()
                lock.mkdir()
            except (OSError, FileExistsError):
                return self._failure("state_locked")
        except OSError:
            return self._failure("state_unavailable")
        try:
            loaded = self.load(job_key)
            if not loaded.success or loaded.state is None:
                return loaded
            changed = operation(loaded.state)
            if isinstance(changed, str):
                return self._failure(changed)
            return self._replace(changed)
        finally:
            try:
                lock.rmdir()
            except OSError:
                pass

    def _create(self, state: MailboxDocumentJobState) -> MailboxDocumentJobStateResult:
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            path = self.state_dir / f"{state.job_key}.json"
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(asdict(state), handle, separators=(",", ":"), sort_keys=True)
                handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        except FileExistsError:
            return self.load(state.job_key)
        except OSError:
            return self._failure("state_unavailable")
        return MailboxDocumentJobStateResult(True, "state_created", state)

    def _replace(self, state: MailboxDocumentJobState) -> MailboxDocumentJobStateResult:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=self.state_dir,
                                             prefix=f".{state.job_key}.", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(asdict(state), handle, separators=(",", ":"), sort_keys=True)
                handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, self.state_dir / f"{state.job_key}.json")
        except OSError:
            if temporary:
                try: temporary.unlink(missing_ok=True)
                except OSError: pass
            return self._failure("state_unavailable")
        return MailboxDocumentJobStateResult(True, "state_updated", state)

    def _decode(self, payload: Any, *, expected_job_key: str) -> MailboxDocumentJobStateResult:
        expected = {field.name for field in __import__("dataclasses").fields(MailboxDocumentJobState)}
        keys = frozenset(payload) if isinstance(payload, dict) else frozenset()
        required = {
            "schema_version", "job_key", "message_key", "attachment_key",
            "document_key", "stage", "smartsheet_row_id", "attachment_required",
            "row_attempt_count", "attachment_attempt_count", "last_failure_category",
            "retryable", "lease_token", "lease_expires_at", "updated_at",
        }
        if not isinstance(payload, dict):
            return self._failure("state_corrupt")
        if payload.get("schema_version") not in {1, self.SCHEMA_VERSION}:
            return self._failure("state_version_unsupported")
        if not required <= keys or not keys <= expected:
            return self._failure("state_corrupt")
        if payload.get("schema_version") == self.SCHEMA_VERSION and keys != expected:
            return self._failure("state_corrupt")
        legacy_stage = str(payload.get("stage", ""))
        raw_row_attempt_count = payload.get("row_attempt_count", 0)
        legacy_row_attempted = (
            isinstance(raw_row_attempt_count, int)
            and not isinstance(raw_row_attempt_count, bool)
            and raw_row_attempt_count > 0
        )
        legacy_row_proven = payload.get("smartsheet_row_id") is not None
        defaults = {
            "attachment_filename": None,
            "attachment_naming_status": None,
            "attachment_business_filename_attempted": False,
            "attachment_required_component_failure_count": 0,
            "attachment_optional_component_omission_count": 0,
            "attachment_placeholder_categories": (),
            "attachment_technical_fallback_reason": "none",
            "row_create_attempted": legacy_row_attempted,
            "row_outcome_proven": legacy_row_proven,
            "row_reconciliation_attempted": legacy_stage == "row_write_uncertain",
            "row_reconciliation_match_cardinality": (
                "unavailable" if legacy_stage == "row_write_uncertain"
                else "not_attempted"
            ),
            "row_recovery_state": (
                "reconcile_only" if legacy_stage == "row_write_uncertain"
                else "blocked" if legacy_stage == "blocked_permanent" else "none"
            ),
            "recoverable": legacy_stage == "row_write_uncertain",
            "attachment_blocked_due_to_unresolved_row": (
                legacy_stage == "row_write_uncertain" and not legacy_row_proven
            ),
        }
        payload = {**defaults, **payload, "schema_version": self.SCHEMA_VERSION}
        if isinstance(payload.get("attachment_placeholder_categories"), list):
            payload["attachment_placeholder_categories"] = tuple(
                payload["attachment_placeholder_categories"]
            )
        try: state = MailboxDocumentJobState(**payload)
        except TypeError: return self._failure("state_corrupt")
        if state.job_key != expected_job_key or state.stage not in STAGES:
            return self._failure("state_inconsistent")
        if not all(self._valid_digest(value) for value in (state.job_key, state.message_key, state.attachment_key, state.document_key)):
            return self._failure("state_corrupt")
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (state.row_attempt_count, state.attachment_attempt_count)):
            return self._failure("state_corrupt")
        if state.smartsheet_row_id is not None and (isinstance(state.smartsheet_row_id, bool) or not isinstance(state.smartsheet_row_id, int) or state.smartsheet_row_id <= 0):
            return self._failure("state_corrupt")
        if (
            not isinstance(state.attachment_business_filename_attempted, bool)
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in (
                    state.attachment_required_component_failure_count,
                    state.attachment_optional_component_omission_count,
                )
            )
            or not isinstance(state.attachment_placeholder_categories, tuple)
            or any(
                category not in {
                    "payer", "service", "document_type",
                    "document_subtype", "date",
                }
                for category in state.attachment_placeholder_categories
            )
            or self._safe_category(
                state.attachment_technical_fallback_reason
            ) != state.attachment_technical_fallback_reason
            or any(
                not isinstance(value, bool)
                for value in (
                    state.row_create_attempted,
                    state.row_outcome_proven,
                    state.row_reconciliation_attempted,
                    state.recoverable,
                    state.attachment_blocked_due_to_unresolved_row,
                )
            )
            or state.row_reconciliation_match_cardinality
            not in RECONCILIATION_CARDINALITIES
            or state.row_recovery_state not in ROW_RECOVERY_STATES
        ):
            return self._failure("state_corrupt")
        return MailboxDocumentJobStateResult(True, "state_loaded", state)

    @classmethod
    def _valid_digest(cls, value: Any) -> bool:
        return isinstance(value, str) and len(value) == cls._DIGEST_LENGTH and all(c in "0123456789abcdef" for c in value)

    @staticmethod
    def _safe_category(value: Any) -> str | None:
        if value is None: return None
        text = str(value).strip().lower()
        return text if text and len(text) <= 80 and all(c.isalnum() or c == "_" for c in text) else "operation_failed"

    @staticmethod
    def _utc_now() -> str: return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _failure(status: str) -> MailboxDocumentJobStateResult:
        return MailboxDocumentJobStateResult(False, status, None)

    @staticmethod
    def _summary_failure(status: str) -> MailboxDocumentJobBatchSummary:
        return MailboxDocumentJobBatchSummary(
            completed_document_count=0,
            pending_document_count=None,
            row_attempt_count=None,
            attachment_attempt_count=None,
            failure_category=str(status),
            retryable=False,
            recoverable=False,
            row_create_attempted=False,
            row_outcome_proven=False,
            row_reconciliation_attempted=False,
            row_reconciliation_match_cardinality="unavailable",
            row_recovery_state="blocked",
            attachment_blocked_due_to_unresolved_row=False,
            success=False,
            status=str(status),
        )
