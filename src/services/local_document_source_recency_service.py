from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any


class LocalDocumentSourceRecencyService:
    """Private local ordering metadata for Graph-sourced documents."""

    SCHEMA_VERSION = 2
    DEFAULT_REGISTRY_PATH = Path(
        "data/mailbox_processing_state/local_document_source_recency.json"
    )
    _DIGEST = re.compile(r"[0-9a-f]{64}")
    _STATUSES = {"downloaded", "identical_collision"}

    def __init__(self, registry_path: str | Path | None = None) -> None:
        self._registry_path = Path(registry_path or self.DEFAULT_REGISTRY_PATH)

    @classmethod
    def normalize_received_datetime(cls, value: Any) -> str | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        normalized = parsed.astimezone(timezone.utc)
        return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")

    @staticmethod
    def message_tie_break(message_id: Any) -> str | None:
        if not isinstance(message_id, str) or not message_id:
            return None
        return hashlib.sha256(message_id.encode("utf-8")).hexdigest()

    @staticmethod
    def candidate_identity(local_path: Any) -> str | None:
        try:
            path = Path(local_path).resolve(strict=False)
        except (TypeError, ValueError, OSError):
            return None
        normalized = os.path.normcase(str(path))
        if not normalized:
            return None
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def record(
        self,
        *,
        local_path: Any,
        document_fingerprint: str,
        received_datetime: Any,
        message_id: Any,
        attachment_order_key: str,
        status: str,
    ) -> bool:
        normalized = self.normalize_received_datetime(received_datetime)
        message_key = self.message_tie_break(message_id)
        candidate_key = self.candidate_identity(local_path)
        candidate = {
            "document_fingerprint": document_fingerprint,
            "received_datetime": normalized,
            "message_tie_break": message_key,
            "attachment_order_key": attachment_order_key,
            "status": status,
        }
        if not self._valid_digest(candidate_key) or not self._valid_record(candidate):
            return False
        records = self._load_records()
        existing = records.get(candidate_key)
        if existing is None or self._sort_key(candidate) < self._sort_key(existing):
            records[candidate_key] = candidate
        return self._write_records(records)

    def ordering_key(
        self,
        local_path: Any,
        document_fingerprint: str,
    ) -> tuple[Any, ...] | None:
        candidate_key = self.candidate_identity(local_path)
        if not self._valid_digest(candidate_key) or not self._valid_digest(
            document_fingerprint
        ):
            return None
        record = self._load_records().get(candidate_key)
        if (
            record is None
            or record.get("document_fingerprint") != document_fingerprint
        ):
            return None
        return self._sort_key(record) if record is not None else None

    def _load_records(self) -> dict[str, dict[str, str]]:
        try:
            payload = json.loads(self._registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}
        if not isinstance(payload, dict) or payload.get("version") != self.SCHEMA_VERSION:
            return {}
        raw_records = payload.get("records")
        if not isinstance(raw_records, dict):
            return {}
        return {
            fingerprint: record
            for fingerprint, record in raw_records.items()
            if self._valid_digest(fingerprint) and self._valid_record(record)
        }

    def _write_records(self, records: dict[str, dict[str, str]]) -> bool:
        temporary_path = self._registry_path.with_suffix(".tmp")
        try:
            self._registry_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(
                    {"version": self.SCHEMA_VERSION, "records": records},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
                newline="\n",
            )
            os.replace(temporary_path, self._registry_path)
        except OSError:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False
        return True

    @classmethod
    def _valid_digest(cls, value: Any) -> bool:
        return isinstance(value, str) and cls._DIGEST.fullmatch(value) is not None

    @classmethod
    def _valid_record(cls, record: Any) -> bool:
        return (
            isinstance(record, dict)
            and set(record) == {
                "document_fingerprint",
                "received_datetime",
                "message_tie_break",
                "attachment_order_key",
                "status",
            }
            and cls._valid_digest(record.get("document_fingerprint"))
            and cls.normalize_received_datetime(record.get("received_datetime"))
            == record.get("received_datetime")
            and cls._valid_digest(record.get("message_tie_break"))
            and cls._valid_digest(record.get("attachment_order_key"))
            and record.get("status") in cls._STATUSES
        )

    @staticmethod
    def _sort_key(record: dict[str, str]) -> tuple[Any, ...]:
        parsed = datetime.fromisoformat(
            record["received_datetime"].replace("Z", "+00:00")
        )
        microseconds = int(parsed.timestamp() * 1_000_000)
        return (
            -microseconds,
            record["message_tie_break"],
            record["attachment_order_key"],
        )
