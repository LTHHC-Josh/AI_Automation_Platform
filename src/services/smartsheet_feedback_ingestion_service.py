from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable, Protocol, Sequence

from src.services.smartsheet_feedback_case_storage_service import (
    SmartsheetFeedbackCase,
    SmartsheetFeedbackCaseStorageResult,
)


@dataclass(frozen=True, repr=False)
class SmartsheetFeedbackRowReference:
    row_id: int
    flagged: bool


@dataclass(frozen=True, repr=False)
class SmartsheetFeedbackDiscussionResult:
    comments: tuple[str, ...]


class SmartsheetFeedbackRowReader(Protocol):
    def read_rows(
        self, *, checkbox_title: str, source_scope: str
    ) -> Sequence[SmartsheetFeedbackRowReference]: ...


class SmartsheetFeedbackDiscussionReader(Protocol):
    def read_discussions(
        self, *, row_id: int
    ) -> SmartsheetFeedbackDiscussionResult: ...


class SmartsheetFeedbackCaseStorage(Protocol):
    def store(
        self, feedback_case: SmartsheetFeedbackCase
    ) -> SmartsheetFeedbackCaseStorageResult: ...


@dataclass(frozen=True)
class SmartsheetFeedbackIngestionResult:
    flagged_row_count: int
    processed_feedback_case_count: int
    skipped_count: int
    success: bool
    status: str
    categories: tuple[str, ...]


class SmartsheetFeedbackIngestionService:
    """Read-only boundary for normalized incorrect-AI row feedback."""

    FAILURE_CATEGORIES = {
        "malformed_flag_state",
        "invalid_row_reference",
        "discussion_read_failed",
        "invalid_comments",
        "storage_failed",
    }

    def __init__(
        self,
        *,
        row_reader: SmartsheetFeedbackRowReader,
        discussion_reader: SmartsheetFeedbackDiscussionReader,
        case_storage: SmartsheetFeedbackCaseStorage,
        checkbox_title: str,
        source_scope: str,
        utc_now: Callable[[], datetime] | None = None,
    ) -> None:
        self.row_reader = row_reader
        self.discussion_reader = discussion_reader
        self.case_storage = case_storage
        self.checkbox_title = checkbox_title
        self.source_scope = source_scope
        self.utc_now = utc_now or (lambda: datetime.now(timezone.utc))

    def ingest(self) -> SmartsheetFeedbackIngestionResult:
        checkbox_title = self._nonblank_text(self.checkbox_title)
        source_scope = self._nonblank_text(self.source_scope)
        if checkbox_title is None or source_scope is None:
            return self._result(status="invalid_configuration")

        try:
            rows = self.row_reader.read_rows(
                checkbox_title=checkbox_title, source_scope=source_scope
            )
        except Exception:
            return self._result(status="row_read_failed")

        if not isinstance(rows, Sequence) or isinstance(
            rows, (str, bytes, bytearray)
        ):
            return self._result(status="row_read_failed")

        flagged_count = 0
        processed_count = 0
        skipped_count = 0
        categories: list[str] = []

        for row in rows:
            flag = getattr(row, "flagged", None)
            if not isinstance(flag, bool):
                skipped_count += 1
                categories.append("malformed_flag_state")
                continue
            if flag is False:
                continue

            flagged_count += 1
            row_id = getattr(row, "row_id", None)
            if (
                not isinstance(row_id, int)
                or isinstance(row_id, bool)
                or row_id <= 0
            ):
                skipped_count += 1
                categories.append("invalid_row_reference")
                continue

            try:
                discussion = self.discussion_reader.read_discussions(row_id=row_id)
            except Exception:
                skipped_count += 1
                categories.append("discussion_read_failed")
                continue

            comments = self._normalize_comments(discussion)
            if comments is None:
                skipped_count += 1
                categories.append("invalid_comments")
                continue

            feedback_case = self._build_case(
                source_scope=source_scope, row_id=row_id, comments=comments
            )
            try:
                storage_result = self.case_storage.store(feedback_case)
            except Exception:
                storage_result = SmartsheetFeedbackCaseStorageResult(
                    stored=False, duplicate=False, status="storage_failed"
                )

            if storage_result.stored:
                processed_count += 1
                categories.append(
                    "comments_present" if comments else "comments_missing"
                )
            else:
                skipped_count += 1
                categories.append(
                    "duplicate_feedback_case"
                    if storage_result.duplicate
                    else "storage_failed"
                )

        if flagged_count == 0 and skipped_count == 0:
            status = "no_flagged_rows"
        elif any(category in self.FAILURE_CATEGORIES for category in categories):
            status = "completed_with_failures"
        elif skipped_count:
            status = "completed_with_skips"
        else:
            status = "completed"

        return self._result(
            flagged_row_count=flagged_count,
            processed_feedback_case_count=processed_count,
            skipped_count=skipped_count,
            status=status,
            categories=categories,
        )

    def _build_case(
        self, *, source_scope: str, row_id: int, comments: tuple[str, ...]
    ) -> SmartsheetFeedbackCase:
        correlation = self._digest(
            {"source_scope": source_scope, "row_id": row_id}
        )
        snapshot = self._digest(
            {
                "row_correlation_digest": correlation,
                "comment_hashes": sorted(self._digest(comment) for comment in comments),
            }
        )
        captured_at = self.utc_now().astimezone(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
        return SmartsheetFeedbackCase(
            row_id=row_id,
            comments=comments,
            row_correlation_digest=correlation,
            snapshot_digest=snapshot,
            captured_at=captured_at,
        )

    @staticmethod
    def _digest(value: Any) -> str:
        serialized = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _nonblank_text(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _normalize_comments(
        discussion: Any,
    ) -> tuple[str, ...] | None:
        if not isinstance(discussion, SmartsheetFeedbackDiscussionResult):
            return None
        if not isinstance(discussion.comments, tuple):
            return None
        if any(not isinstance(comment, str) for comment in discussion.comments):
            return None
        return tuple(
            normalized
            for comment in discussion.comments
            if (normalized := comment.strip())
        )

    @staticmethod
    def _result(
        *,
        flagged_row_count: int = 0,
        processed_feedback_case_count: int = 0,
        skipped_count: int = 0,
        status: str,
        categories: Sequence[str] = (),
    ) -> SmartsheetFeedbackIngestionResult:
        return SmartsheetFeedbackIngestionResult(
            flagged_row_count=flagged_row_count,
            processed_feedback_case_count=processed_feedback_case_count,
            skipped_count=skipped_count,
            success=status
            not in {
                "invalid_configuration",
                "row_read_failed",
                "completed_with_failures",
            },
            status=status,
            categories=tuple(dict.fromkeys(categories)),
        )
