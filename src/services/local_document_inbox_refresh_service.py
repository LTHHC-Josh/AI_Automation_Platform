from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.graph.attachment_service import AttachmentService
from src.graph.email_service import EmailService
from src.graph.errors import GraphBoundaryError
from src.services.local_document_source_recency_service import (
    LocalDocumentSourceRecencyService,
)


@dataclass(frozen=True)
class LocalDocumentInboxRefreshResult:
    success: bool
    status: str
    messages_checked: int = 0
    messages_with_attachments: int = 0
    attachments_examined: int = 0
    attachments_downloaded: int = 0
    attachments_skipped: int = 0
    filename_collisions: int = 0

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "messages_checked": self.messages_checked,
            "messages_with_attachments": self.messages_with_attachments,
            "attachments_examined": self.attachments_examined,
            "attachments_downloaded": self.attachments_downloaded,
            "attachments_skipped": self.attachments_skipped,
            "filename_collisions": self.filename_collisions,
        }


class LocalDocumentInboxRefreshService:
    """Read newest mailbox items and download supported attachments only."""

    MAX_TOP = 25

    def __init__(
        self,
        *,
        email_service_factory: Callable[[], Any] = EmailService,
        attachment_service_factory: Callable[[], Any] = AttachmentService,
        source_recency_service: Any | None = None,
    ) -> None:
        self._email_service_factory = email_service_factory
        self._attachment_service_factory = attachment_service_factory
        self._source_recency_service = (
            source_recency_service
            if source_recency_service is not None
            else LocalDocumentSourceRecencyService()
        )

    def refresh(
        self,
        *,
        top: int,
        supported_extensions: set[str],
    ) -> LocalDocumentInboxRefreshResult:
        if (
            not isinstance(top, int)
            or isinstance(top, bool)
            or top < 1
            or top > self.MAX_TOP
        ):
            return LocalDocumentInboxRefreshResult(
                success=False,
                status="invalid_refresh_limit",
            )

        normalized_extensions = {
            str(extension).lower()
            for extension in supported_extensions
            if str(extension).startswith(".")
        }
        if not normalized_extensions:
            return LocalDocumentInboxRefreshResult(
                success=False,
                status="refresh_configuration_unavailable",
            )

        try:
            email_service = self._email_service_factory()
            attachment_service = self._attachment_service_factory()
            messages = email_service.get_recent_attachment_messages(top=top)
        except GraphBoundaryError as error:
            return LocalDocumentInboxRefreshResult(
                success=False,
                status=error.category,
            )
        except Exception:
            return LocalDocumentInboxRefreshResult(
                success=False,
                status="inbox_refresh_failed",
            )

        messages_checked = 0
        messages_with_attachments = 0
        attachments_examined = 0
        attachments_downloaded = 0
        attachments_skipped = 0
        filename_collisions = 0

        for message in messages if isinstance(messages, list) else []:
            messages_checked += 1
            if not isinstance(message, dict):
                continue
            if message.get("hasAttachments") is not True:
                continue
            messages_with_attachments += 1
            message_id = message.get("id")
            if not isinstance(message_id, str) or not message_id:
                attachments_skipped += 1
                continue
            received_datetime = (
                self._source_recency_service.normalize_received_datetime(
                    message.get("receivedDateTime")
                )
            )
            try:
                download = attachment_service.download_supported_file_attachments(
                    message_id,
                    supported_extensions=normalized_extensions,
                )
            except GraphBoundaryError as error:
                return LocalDocumentInboxRefreshResult(
                    success=False,
                    status=error.category,
                    messages_checked=messages_checked,
                    messages_with_attachments=messages_with_attachments,
                    attachments_examined=attachments_examined,
                    attachments_downloaded=attachments_downloaded,
                    attachments_skipped=attachments_skipped,
                    filename_collisions=filename_collisions,
                )
            except Exception:
                return LocalDocumentInboxRefreshResult(
                    success=False,
                    status="inbox_refresh_failed",
                    messages_checked=messages_checked,
                    messages_with_attachments=messages_with_attachments,
                    attachments_examined=attachments_examined,
                    attachments_downloaded=attachments_downloaded,
                    attachments_skipped=attachments_skipped,
                    filename_collisions=filename_collisions,
                )

            attachments_examined += int(download.examined_count)
            attachments_downloaded += len(download.downloaded_files)
            attachments_skipped += int(download.skipped_count)
            filename_collisions += int(download.collision_count)
            if received_datetime is None:
                continue
            for outcome in download.candidate_outcomes:
                if outcome.status not in {"downloaded", "identical_collision"}:
                    continue
                if not self._source_recency_service.record(
                    local_path=outcome.local_path,
                    document_fingerprint=outcome.document_fingerprint,
                    received_datetime=received_datetime,
                    message_id=message_id,
                    attachment_order_key=outcome.attachment_order_key,
                    status=outcome.status,
                ):
                    return LocalDocumentInboxRefreshResult(
                        success=False,
                        status="source_recency_storage_failed",
                        messages_checked=messages_checked,
                        messages_with_attachments=messages_with_attachments,
                        attachments_examined=attachments_examined,
                        attachments_downloaded=attachments_downloaded,
                        attachments_skipped=attachments_skipped,
                        filename_collisions=filename_collisions,
                    )

        return LocalDocumentInboxRefreshResult(
            success=True,
            status="completed",
            messages_checked=messages_checked,
            messages_with_attachments=messages_with_attachments,
            attachments_examined=attachments_examined,
            attachments_downloaded=attachments_downloaded,
            attachments_skipped=attachments_skipped,
            filename_collisions=filename_collisions,
        )
