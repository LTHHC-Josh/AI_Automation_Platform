from dataclasses import asdict, dataclass
import json
from pathlib import Path


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
    """Stores protected feedback snapshots without exposing their contents."""

    DEFAULT_STORAGE_DIRECTORY = Path("data/smartsheet_feedback")
    ALLOWED_KEYS = {
        "row_id",
        "comments",
        "row_correlation_digest",
        "snapshot_digest",
        "captured_at",
    }

    def __init__(self, storage_directory: Path | str | None = None) -> None:
        self.storage_directory = Path(
            storage_directory or self.DEFAULT_STORAGE_DIRECTORY
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

        case_path = self.storage_directory / f"{feedback_case.snapshot_digest}.json"
        try:
            self.storage_directory.mkdir(parents=True, exist_ok=True)
            serialized = json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            )
            with case_path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(serialized)
                handle.write("\n")
        except FileExistsError:
            return SmartsheetFeedbackCaseStorageResult(
                stored=False,
                duplicate=True,
                status="duplicate_feedback_case",
            )
        except (OSError, TypeError, ValueError):
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
                for path in self.storage_directory.glob("*.json")
                if path.is_file()
            )
        except OSError:
            return 0
