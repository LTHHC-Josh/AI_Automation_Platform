from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MailboxProcessingStateResult:
    """
    PHI-safe result from one mailbox processing-state operation.

    The result excludes the Graph message ID, message content, sender,
    subject, attachment names, document paths, OCR text, and extracted
    values.
    """

    handled: bool
    stored: bool
    duplicate: bool
    success: bool
    status: str


class MailboxProcessingStateService:
    """
    Maintains durable local handled-state for Graph mailbox messages.

    Graph message IDs are never written to disk. A SHA-256 digest of the
    message ID is used only as the filename for a handled marker.

    This service provides sequential-run idempotency. It does not yet
    implement concurrent worker claiming or interrupted-processing lease
    recovery.
    """

    DEFAULT_STATE_DIR = Path(
        "data/mailbox_processing_state"
    )

    MARKER_SUFFIX = ".handled"

    def __init__(
        self,
        state_dir: str | Path | None = None,
    ) -> None:
        self.state_dir = Path(
            state_dir
            or self.DEFAULT_STATE_DIR
        )

    def check(
        self,
        message_id: Any,
    ) -> MailboxProcessingStateResult:
        fingerprint = self._fingerprint_message_id(
            message_id
        )

        if fingerprint is None:
            return self._failure(
                "invalid_message_id"
            )

        marker_path = self._marker_path(
            fingerprint
        )

        try:
            handled = marker_path.is_file()
        except OSError:
            return self._failure(
                "state_check_failed"
            )

        if handled:
            return MailboxProcessingStateResult(
                handled=True,
                stored=False,
                duplicate=True,
                success=True,
                status="already_handled",
            )

        return MailboxProcessingStateResult(
            handled=False,
            stored=False,
            duplicate=False,
            success=True,
            status="not_handled",
        )

    def mark_handled(
        self,
        message_id: Any,
    ) -> MailboxProcessingStateResult:
        fingerprint = self._fingerprint_message_id(
            message_id
        )

        if fingerprint is None:
            return self._failure(
                "invalid_message_id"
            )

        marker_path = self._marker_path(
            fingerprint
        )

        try:
            self.state_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError:
            return self._failure(
                "state_storage_failed"
            )

        try:
            with marker_path.open(
                "x",
                encoding="ascii",
                newline="\n",
            ) as handle:
                handle.write(
                    "handled\n"
                )
                handle.flush()

        except FileExistsError:
            return MailboxProcessingStateResult(
                handled=True,
                stored=False,
                duplicate=True,
                success=True,
                status="already_handled",
            )

        except OSError:
            return self._failure(
                "state_storage_failed"
            )

        return MailboxProcessingStateResult(
            handled=True,
            stored=True,
            duplicate=False,
            success=True,
            status="handled_recorded",
        )

    def _marker_path(
        self,
        fingerprint: str,
    ) -> Path:
        return (
            self.state_dir
            / (
                fingerprint
                + self.MARKER_SUFFIX
            )
        )

    @staticmethod
    def _fingerprint_message_id(
        message_id: Any,
    ) -> str | None:
        if not isinstance(
            message_id,
            str,
        ):
            return None

        normalized = message_id.strip()

        if not normalized:
            return None

        return hashlib.sha256(
            normalized.encode(
                "utf-8"
            )
        ).hexdigest()

    @staticmethod
    def _failure(
        status: str,
    ) -> MailboxProcessingStateResult:
        return MailboxProcessingStateResult(
            handled=False,
            stored=False,
            duplicate=False,
            success=False,
            status=status,
        )
