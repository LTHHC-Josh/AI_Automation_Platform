from contextlib import contextmanager
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any, Iterator

from src.services.classification_feedback_service import (
    ClassificationFeedback,
)


@dataclass(frozen=True)
class ClassificationFeedbackStorageResult:
    """
    PHI-safe result from one local feedback-storage operation.
    """

    stored: bool
    duplicate: bool
    record_count: int
    status: str


class ClassificationFeedbackStorageService:
    """
    Stores validated PHI-safe classification feedback as local JSONL.

    Duplicate detection and append operations execute inside an atomic
    lock-directory boundary so concurrent local reviewer submissions
    cannot write the same fingerprint more than once.

    The service accepts only ClassificationFeedback records. It never
    receives document paths, document bytes, OCR text, source_text,
    extracted values, email metadata, or patient identifiers.
    """

    DEFAULT_STORAGE_PATH = Path(
        "data/classification_feedback/classification_feedback.jsonl"
    )

    ALLOWED_KEYS = {
        "document_fingerprint",
        "predicted_category",
        "predicted_subtype",
        "confirmed_category",
        "confirmed_subtype",
        "classification_confidence",
        "correction_required",
        "reviewer_confirmation_status",
        "created_at",
    }

    LOCK_TIMEOUT_SECONDS = 5.0
    LOCK_RETRY_SECONDS = 0.01

    def __init__(
        self,
        storage_path: Path | str | None = None,
    ) -> None:
        self.storage_path = Path(
            storage_path
            or self.DEFAULT_STORAGE_PATH
        )

        self.lock_path = self.storage_path.with_name(
            self.storage_path.name
            + ".lock"
        )

    def store(
        self,
        feedback: ClassificationFeedback,
    ) -> ClassificationFeedbackStorageResult:
        """
        Atomically store one record unless its fingerprint already exists.
        """

        if not isinstance(
            feedback,
            ClassificationFeedback,
        ):
            return ClassificationFeedbackStorageResult(
                stored=False,
                duplicate=False,
                record_count=self._count_records(),
                status="invalid_feedback_type",
            )

        payload = asdict(
            feedback
        )

        if set(
            payload
        ) != self.ALLOWED_KEYS:
            return ClassificationFeedbackStorageResult(
                stored=False,
                duplicate=False,
                record_count=self._count_records(),
                status="invalid_feedback_schema",
            )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            with self._acquire_lock():
                existing_fingerprints = self._read_fingerprints()

                if (
                    feedback.document_fingerprint
                    in existing_fingerprints
                ):
                    return ClassificationFeedbackStorageResult(
                        stored=False,
                        duplicate=True,
                        record_count=len(
                            existing_fingerprints
                        ),
                        status="duplicate_fingerprint",
                    )

                serialized = json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(
                        ",",
                        ":",
                    ),
                )

                with self.storage_path.open(
                    "a",
                    encoding="utf-8",
                    newline="\n",
                ) as handle:
                    handle.write(
                        serialized
                    )
                    handle.write(
                        "\n"
                    )
                    handle.flush()

                return ClassificationFeedbackStorageResult(
                    stored=True,
                    duplicate=False,
                    record_count=(
                        len(
                            existing_fingerprints
                        )
                        + 1
                    ),
                    status="stored",
                )

        except TimeoutError:
            return ClassificationFeedbackStorageResult(
                stored=False,
                duplicate=False,
                record_count=self._count_records(),
                status="storage_lock_timeout",
            )

    def count(
        self,
    ) -> int:
        """
        Return the number of unique valid stored records.
        """

        return self._count_records()

    def contains_fingerprint(
        self,
        document_fingerprint: Any,
    ) -> bool:
        """
        Check whether one normalized fingerprint already exists.
        """

        normalized = str(
            document_fingerprint
            or ""
        ).strip().lower()

        return normalized in self._read_fingerprints()

    @contextmanager
    def _acquire_lock(
        self,
    ) -> Iterator[None]:
        """
        Acquire an atomic local lock by creating a dedicated directory.
        """

        deadline = (
            time.monotonic()
            + self.LOCK_TIMEOUT_SECONDS
        )

        while True:
            try:
                self.lock_path.mkdir()
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "Classification feedback storage lock timed out."
                    )

                time.sleep(
                    self.LOCK_RETRY_SECONDS
                )

        try:
            yield
        finally:
            try:
                self.lock_path.rmdir()
            except FileNotFoundError:
                pass

    def _count_records(
        self,
    ) -> int:
        return len(
            self._read_fingerprints()
        )

    def _read_fingerprints(
        self,
    ) -> set[str]:
        if not self.storage_path.exists():
            return set()

        fingerprints: set[str] = set()

        with self.storage_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line in handle:
                normalized_line = line.strip()

                if not normalized_line:
                    continue

                try:
                    payload = json.loads(
                        normalized_line
                    )
                except json.JSONDecodeError:
                    continue

                if not isinstance(
                    payload,
                    dict,
                ):
                    continue

                if set(
                    payload
                ) != self.ALLOWED_KEYS:
                    continue

                fingerprint = str(
                    payload.get(
                        "document_fingerprint"
                    )
                    or ""
                ).strip().lower()

                if fingerprint:
                    fingerprints.add(
                        fingerprint
                    )

        return fingerprints
