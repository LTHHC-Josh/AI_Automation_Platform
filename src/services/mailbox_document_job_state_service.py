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
    "discovered", "processing", "row_write_pending", "row_write_uncertain",
    "row_written", "attachment_write_pending", "attachment_write_uncertain",
    "attachment_written", "blocked_permanent",
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


@dataclass(frozen=True)
class MailboxDocumentJobStateResult:
    success: bool
    status: str
    state: MailboxDocumentJobState | None = field(default=None, repr=False)


class MailboxDocumentJobStateService:
    SCHEMA_VERSION = 1
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

    def transition(self, job_key: str, *, expected_stages: set[str], stage: str,
                   lease_token: str | None = None, smartsheet_row_id: int | None = None,
                   failure_category: str | None = None, retryable: bool | None = None,
                   increment_row_attempt: bool = False,
                   increment_attachment_attempt: bool = False) -> MailboxDocumentJobStateResult:
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
            values.update(stage=stage, smartsheet_row_id=row_id,
                          last_failure_category=self._safe_category(failure_category),
                          retryable=current.retryable if retryable is None else bool(retryable),
                          lease_token=None, lease_expires_at=None, updated_at=self._utc_now(),
                          row_attempt_count=current.row_attempt_count + int(increment_row_attempt),
                          attachment_attempt_count=current.attachment_attempt_count + int(increment_attachment_attempt))
            return MailboxDocumentJobState(**values)
        return self._mutate(job_key, change)

    def _acquire_lease(self, current: MailboxDocumentJobState):
        if current.stage not in {"discovered", "processing"}:
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
        if not isinstance(payload, dict) or set(payload) != expected:
            return self._failure("state_corrupt")
        try: state = MailboxDocumentJobState(**payload)
        except TypeError: return self._failure("state_corrupt")
        if state.schema_version != self.SCHEMA_VERSION:
            return self._failure("state_version_unsupported")
        if state.job_key != expected_job_key or state.stage not in STAGES:
            return self._failure("state_inconsistent")
        if not all(self._valid_digest(value) for value in (state.job_key, state.message_key, state.attachment_key, state.document_key)):
            return self._failure("state_corrupt")
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (state.row_attempt_count, state.attachment_attempt_count)):
            return self._failure("state_corrupt")
        if state.smartsheet_row_id is not None and (isinstance(state.smartsheet_row_id, bool) or not isinstance(state.smartsheet_row_id, int) or state.smartsheet_row_id <= 0):
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
