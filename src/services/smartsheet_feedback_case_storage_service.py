import base64
import hashlib
import hmac
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
from typing import Any, Callable
from uuid import uuid4

from src.services.windows_dpapi_service import (
    WindowsDpapiError,
    protect_current_user,
    unprotect_current_user,
)


FEEDBACK_SNAPSHOT_PURPOSE = b"LTHHC Smartsheet feedback snapshot v2"
CORRECTION_CASE_PURPOSE = b"LTHHC DP training correction case v1"
CORRECTION_IDENTITY_KEY_PURPOSE = b"LTHHC DP training identity key v1"
CASE_SCHEMA_VERSION = 2


class CorrectionCaseStorageError(RuntimeError):
    """Fixed-category protected-state failure."""

    def __init__(self, category: str):
        super().__init__(category)
        self.category = category


@dataclass(frozen=True, repr=False)
class SmartsheetFeedbackCase:
    """Protected local snapshot of feedback attached to one Smartsheet row."""

    row_id: int
    comments: tuple[str, ...]
    row_correlation_digest: str
    snapshot_digest: str
    captured_at: str


@dataclass(frozen=True)
class SmartsheetFeedbackCaseStorageResult:
    stored: bool
    duplicate: bool
    status: str


class SmartsheetFeedbackCaseStorageService:
    """Stores sealed legacy feedback snapshots without exposing their contents."""

    DEFAULT_STORAGE_DIRECTORY = (
        Path(__file__).resolve().parents[2] / "data/smartsheet_feedback"
    )
    ALLOWED_KEYS = {
        "row_id",
        "comments",
        "row_correlation_digest",
        "snapshot_digest",
        "captured_at",
    }

    def __init__(
        self,
        storage_directory: Path | str | None = None,
        *,
        protect: Callable[[bytes], bytes] | None = None,
    ) -> None:
        self.storage_directory = Path(
            storage_directory or self.DEFAULT_STORAGE_DIRECTORY
        )
        self.protect = protect or (
            lambda value: protect_current_user(
                value, purpose=FEEDBACK_SNAPSHOT_PURPOSE
            )
        )

    def store(
        self,
        feedback_case: SmartsheetFeedbackCase,
    ) -> SmartsheetFeedbackCaseStorageResult:
        if not isinstance(feedback_case, SmartsheetFeedbackCase):
            return SmartsheetFeedbackCaseStorageResult(
                stored=False, duplicate=False, status="storage_failed"
            )

        payload = asdict(feedback_case)
        if set(payload) != self.ALLOWED_KEYS:
            return SmartsheetFeedbackCaseStorageResult(
                stored=False, duplicate=False, status="storage_failed"
            )

        case_path = self.storage_directory / f"{feedback_case.snapshot_digest}.feedback"
        try:
            self.storage_directory.mkdir(parents=True, exist_ok=True)
            serialized = json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            sealed = self.protect(serialized)
            with case_path.open("xb") as handle:
                handle.write(sealed)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            return SmartsheetFeedbackCaseStorageResult(
                stored=False,
                duplicate=True,
                status="duplicate_feedback_case",
            )
        except (OSError, TypeError, ValueError, WindowsDpapiError):
            return SmartsheetFeedbackCaseStorageResult(
                stored=False, duplicate=False, status="storage_failed"
            )

        return SmartsheetFeedbackCaseStorageResult(
            stored=True, duplicate=False, status="stored"
        )

    def count(self) -> int:
        try:
            return sum(
                1
                for path in self.storage_directory.glob("*.feedback")
                if path.is_file()
            )
        except OSError:
            return 0


@dataclass(repr=False)
class CorrectionCase:
    """One protected correction lifecycle keyed to one Smartsheet row."""

    case_id: str
    row_id: int
    source_scope: str
    created_at: str
    updated_at: str
    status: str = "New"
    input_digest: str = ""
    comment_checkpoint_digest: str = ""
    row_snapshot: dict[str, Any] = field(default_factory=dict, repr=False)
    comments: list[dict[str, Any]] = field(default_factory=list, repr=False)
    proposal_generation: int = 0
    proposal_text: str = field(default="", repr=False)
    correction_type: str = "Needs Investigation"
    related_correction_types: list[str] = field(default_factory=list)
    behavior_code: str = "needs_investigation"
    affected_fields: list[str] = field(default_factory=list)
    likely_layers: list[str] = field(default_factory=list)
    technical_disposition: str = "Needs Investigation"
    feedback_relationship: str = "Insufficient"
    observed_failure_type: str = "Other"
    affected_document_category: str = "not_applicable"
    desired_intake_subtype: str = "not_applicable"
    required_filename_components: list[str] = field(default_factory=list)
    excluded_filename_components: list[str] = field(default_factory=list)
    analysis_outcome_category: str = "legacy_unversioned"
    analysis_contract_version: int = 1
    business_context_version: int = 0
    analysis_attempt_key: str = ""
    analysis_attempt_state: str = "none"
    proposal_hash: str = ""
    correction_approval_baseline_seen: bool = False
    correction_approval_previous: bool | None = None
    correction_approval_consumed_generation: int = 0
    implementation_job_id: str = ""
    implementation_state: str = "none"
    implementation_attempt_count: int = 0
    implementation_commit_sha: str = ""
    result_generation: int = 0
    resolution_result: str = field(default="", repr=False)
    resolution_hash: str = ""
    resolution_approval_baseline_seen: bool = False
    resolution_approval_previous: bool | None = None
    resolution_approval_consumed_generation: int = 0
    pending_feedback: bool = False
    write_intent: dict[str, Any] = field(default_factory=dict, repr=False)
    transition_history: list[dict[str, str]] = field(default_factory=list)
    schema_version: int = CASE_SCHEMA_VERSION

    def __repr__(self) -> str:
        return "<CorrectionCase protected>"


class ProtectedCorrectionCaseRepository:
    """DPAPI-sealed, atomic, exact-schema correction lifecycle repository."""

    DEFAULT_DIRECTORY = (
        Path(__file__).resolve().parents[2] / "data/smartsheet_feedback/cases"
    )
    KEY_NAME = ".case-identity-key.dpapi"

    def __init__(
        self,
        directory: str | Path | None = None,
        *,
        protect: Callable[[bytes], bytes] | None = None,
        unprotect: Callable[[bytes], bytes] | None = None,
        utc_now: Callable[[], datetime] | None = None,
    ) -> None:
        self.directory = Path(directory or self.DEFAULT_DIRECTORY)
        self._injected_protect = protect
        self._injected_unprotect = unprotect
        self.utc_now = utc_now or (lambda: datetime.now(timezone.utc))

    def case_id(self, *, source_scope: str, row_id: int) -> str:
        if not isinstance(source_scope, str) or not source_scope.strip():
            raise CorrectionCaseStorageError("case_scope_invalid")
        if isinstance(row_id, bool) or not isinstance(row_id, int) or row_id <= 0:
            raise CorrectionCaseStorageError("case_row_reference_invalid")
        message = f"{source_scope.strip()}:{row_id}".encode("utf-8")
        return hmac.new(self._identity_key(), message, hashlib.sha256).hexdigest()

    def load(self, case_id: str) -> CorrectionCase | None:
        path = self._case_path(case_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(self._unprotect_case(path.read_bytes()).decode("utf-8"))
            return self._decode_case(payload, expected_case_id=case_id)
        except CorrectionCaseStorageError:
            raise
        except Exception:
            raise CorrectionCaseStorageError("case_state_corrupt") from None

    def load_or_create(self, *, source_scope: str, row_id: int) -> CorrectionCase:
        identity = self.case_id(source_scope=source_scope, row_id=row_id)
        existing = self.load(identity)
        if existing is not None:
            return existing
        now = self._timestamp()
        correction_case = CorrectionCase(
            case_id=identity,
            row_id=row_id,
            source_scope=source_scope.strip(),
            created_at=now,
            updated_at=now,
            transition_history=[{"status": "New", "at": now}],
        )
        self.save(correction_case, exclusive=True)
        return self.load(identity) or correction_case

    def save(self, correction_case: CorrectionCase, *, exclusive: bool = False) -> None:
        if not isinstance(correction_case, CorrectionCase):
            raise CorrectionCaseStorageError("case_state_invalid")
        correction_case.updated_at = self._timestamp()
        payload = asdict(correction_case)
        names = {item.name for item in CorrectionCase.__dataclass_fields__.values()}
        if set(payload) != names:
            raise CorrectionCaseStorageError("case_schema_invalid")
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        sealed = self._protect_case(serialized)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self._case_path(correction_case.case_id)
        if exclusive:
            try:
                with path.open("xb") as stream:
                    stream.write(sealed)
                    stream.flush()
                    os.fsync(stream.fileno())
                return
            except FileExistsError:
                return
            except OSError:
                raise CorrectionCaseStorageError("case_storage_failed") from None
        temporary = self.directory / f".{correction_case.case_id}.{uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(sealed)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except OSError:
            raise CorrectionCaseStorageError("case_storage_failed") from None
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def list_cases(self) -> tuple[CorrectionCase, ...]:
        try:
            paths = tuple(self.directory.glob("*.case"))
        except OSError:
            raise CorrectionCaseStorageError("case_list_failed") from None
        return tuple(
            loaded
            for path in paths
            if (loaded := self.load(path.stem)) is not None
        )

    def _identity_key(self) -> bytes:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / self.KEY_NAME
        if path.exists():
            try:
                decoded = base64.b64decode(path.read_bytes(), validate=True)
                key = self._unprotect_identity_key(decoded)
            except Exception:
                raise CorrectionCaseStorageError("case_identity_key_invalid") from None
            if len(key) != 32:
                raise CorrectionCaseStorageError("case_identity_key_invalid")
            return key
        key = secrets.token_bytes(32)
        encoded = base64.b64encode(self._protect_identity_key(key))
        try:
            with path.open("xb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            return self._identity_key()
        except OSError:
            raise CorrectionCaseStorageError("case_identity_key_storage_failed") from None
        return key

    def _decode_case(self, payload: Any, *, expected_case_id: str) -> CorrectionCase:
        if not isinstance(payload, dict):
            raise CorrectionCaseStorageError("case_state_corrupt")
        names = {item.name for item in CorrectionCase.__dataclass_fields__.values()}
        schema_version = payload.get("schema_version")
        if schema_version == 1:
            new_fields = {
                "related_correction_types", "technical_disposition",
                "feedback_relationship", "observed_failure_type",
                "affected_document_category", "desired_intake_subtype",
                "required_filename_components", "excluded_filename_components",
                "analysis_outcome_category", "analysis_contract_version",
                "business_context_version", "analysis_attempt_key",
                "analysis_attempt_state",
            }
            if set(payload) != names - new_fields:
                raise CorrectionCaseStorageError("case_schema_unsupported")
            payload = {
                **payload,
                "related_correction_types": [],
                "technical_disposition": "Needs Investigation",
                "feedback_relationship": "Insufficient",
                "observed_failure_type": "Other",
                "affected_document_category": "not_applicable",
                "desired_intake_subtype": "not_applicable",
                "required_filename_components": [],
                "excluded_filename_components": [],
                "analysis_outcome_category": "legacy_unversioned",
                "analysis_contract_version": 1,
                "business_context_version": 0,
                "analysis_attempt_key": "",
                "analysis_attempt_state": "none",
                "schema_version": CASE_SCHEMA_VERSION,
            }
        if set(payload) != names or payload.get("schema_version") != CASE_SCHEMA_VERSION:
            raise CorrectionCaseStorageError("case_schema_unsupported")
        if payload.get("case_id") != expected_case_id:
            raise CorrectionCaseStorageError("case_identity_mismatch")
        try:
            return CorrectionCase(**payload)
        except (TypeError, ValueError):
            raise CorrectionCaseStorageError("case_state_corrupt") from None

    def _case_path(self, case_id: str) -> Path:
        if (
            not isinstance(case_id, str)
            or len(case_id) != 64
            or any(character not in "0123456789abcdef" for character in case_id)
        ):
            raise CorrectionCaseStorageError("case_identity_invalid")
        return self.directory / f"{case_id}.case"

    def _protect_case(self, value: bytes) -> bytes:
        if self._injected_protect is not None:
            return self._injected_protect(value)
        return self._dpapi_protect(value, CORRECTION_CASE_PURPOSE)

    def _unprotect_case(self, value: bytes) -> bytes:
        if self._injected_unprotect is not None:
            return self._injected_unprotect(value)
        return self._dpapi_unprotect(value, CORRECTION_CASE_PURPOSE)

    def _protect_identity_key(self, value: bytes) -> bytes:
        if self._injected_protect is not None:
            return self._injected_protect(value)
        return self._dpapi_protect(value, CORRECTION_IDENTITY_KEY_PURPOSE)

    def _unprotect_identity_key(self, value: bytes) -> bytes:
        if self._injected_unprotect is not None:
            return self._injected_unprotect(value)
        return self._dpapi_unprotect(value, CORRECTION_IDENTITY_KEY_PURPOSE)

    @staticmethod
    def _dpapi_protect(value: bytes, purpose: bytes) -> bytes:
        try:
            return protect_current_user(value, purpose=purpose)
        except WindowsDpapiError:
            raise CorrectionCaseStorageError("case_encryption_failed") from None

    @staticmethod
    def _dpapi_unprotect(value: bytes, purpose: bytes) -> bytes:
        try:
            return unprotect_current_user(value, purpose=purpose)
        except WindowsDpapiError:
            raise CorrectionCaseStorageError("case_decryption_failed") from None

    def _timestamp(self) -> str:
        return self.utc_now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_digest(value: Any) -> str:
    """Create a deterministic digest without exposing the input."""
    serialized = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
