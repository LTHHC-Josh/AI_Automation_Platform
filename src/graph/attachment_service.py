import base64
from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

from .client import GraphClient
from .config import load_graph_config


@dataclass(frozen=True, repr=False)
class SupportedAttachmentCandidateOutcome:
    local_path: Path = field(repr=False)
    document_fingerprint: str = field(repr=False)
    attachment_order_key: str = field(repr=False)
    status: str


@dataclass(repr=False)
class SupportedAttachmentDownloadResult:
    downloaded_files: list[Path] = field(default_factory=list, repr=False)
    candidate_outcomes: list[SupportedAttachmentCandidateOutcome] = field(
        default_factory=list,
        repr=False,
    )
    examined_count: int = 0
    skipped_count: int = 0
    collision_count: int = 0


@dataclass(frozen=True)
class SupportedAttachmentCountResult:
    """PHI-safe deterministic count from attachment metadata only."""

    count: int | None
    success: bool
    unsupported_document_type_count: int = 0
    unprovable_reason: str | None = None


class AttachmentService:
    def __init__(self, download_dir: str = "data/incoming"):
        self.client = GraphClient()
        self.config = load_graph_config()
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def get_attachments(self, message_id: str) -> list[dict]:
        endpoint = (
            f"/users/{self.config.mailbox}"
            f"/messages/{message_id}/attachments"
        )

        response = self.client.get(
            endpoint,
            operation_category=(
                "attachment_enumeration"
            ),
        )
        return response.get("value", [])

    def count_supported_file_attachments(
        self,
        message_id: str,
        *,
        supported_extensions: set[str],
    ) -> SupportedAttachmentCountResult:
        """Count processable documents without requesting attachment content."""
        endpoint = (
            f"/users/{self.config.mailbox}"
            f"/messages/{message_id}/attachments"
        )
        count = 0
        unsupported_document_type_count = 0
        request_endpoint = endpoint
        request_params = {"$select": "id,name,isInline"}
        seen_continuations: set[str] = set()

        while True:
            try:
                response = self.client.get(
                    request_endpoint,
                    params=request_params,
                    operation_category="attachment_enumeration",
                )
            except Exception:
                reason = (
                    "attachment_metadata_request_failed"
                    if not seen_continuations
                    else "attachment_metadata_pagination_request_failed"
                )
                return SupportedAttachmentCountResult(
                    count=None, success=False, unprovable_reason=reason
                )

            attachments = response.get("value") if isinstance(response, dict) else None
            if not isinstance(attachments, list):
                return SupportedAttachmentCountResult(
                    count=None, success=False,
                    unprovable_reason="attachment_metadata_response_invalid",
                )

            for attachment in attachments:
                if not isinstance(attachment, dict):
                    return SupportedAttachmentCountResult(
                        count=None, success=False,
                        unprovable_reason="attachment_metadata_item_invalid",
                    )
                attachment_type = attachment.get("@odata.type")
                if not isinstance(attachment_type, str):
                    return SupportedAttachmentCountResult(
                        count=None, success=False,
                        unprovable_reason="attachment_metadata_type_unprovable",
                    )
                normalized_type = attachment_type.removeprefix("#")
                if normalized_type not in {
                    "microsoft.graph.fileAttachment",
                    "microsoft.graph.itemAttachment",
                    "microsoft.graph.referenceAttachment",
                }:
                    return SupportedAttachmentCountResult(
                        count=None, success=False,
                        unprovable_reason="attachment_metadata_type_unprovable",
                    )
                if normalized_type != "microsoft.graph.fileAttachment":
                    continue
                is_inline = attachment.get("isInline")
                if not isinstance(is_inline, bool):
                    return SupportedAttachmentCountResult(
                        count=None, success=False,
                        unprovable_reason="attachment_metadata_inline_state_unprovable",
                    )
                if is_inline:
                    continue
                name = attachment.get("name")
                if not isinstance(name, str) or not name.strip():
                    return SupportedAttachmentCountResult(
                        count=None, success=False,
                        unprovable_reason="attachment_metadata_name_unprovable",
                    )
                if Path(Path(name).name).suffix.lower() in supported_extensions:
                    count += 1
                else:
                    unsupported_document_type_count += 1

            next_link = response.get("@odata.nextLink")
            if next_link is None:
                break
            continuation = self._attachment_continuation_endpoint(next_link)
            if continuation is None or continuation in seen_continuations:
                return SupportedAttachmentCountResult(
                    count=None, success=False,
                    unprovable_reason="attachment_metadata_pagination_invalid",
                )
            seen_continuations.add(continuation)
            request_endpoint = continuation
            request_params = None

        return SupportedAttachmentCountResult(
            count=count,
            success=True,
            unsupported_document_type_count=unsupported_document_type_count,
        )

    @staticmethod
    def _attachment_continuation_endpoint(value) -> str | None:
        """Accept only an opaque Microsoft Graph v1.0 continuation URL."""
        if not isinstance(value, str) or not value:
            return None
        parsed = urlsplit(value)
        if parsed.scheme != "https" or parsed.netloc.lower() != "graph.microsoft.com":
            return None
        prefix = "/v1.0"
        if not parsed.path.startswith(f"{prefix}/"):
            return None
        endpoint = parsed.path[len(prefix):]
        if parsed.query:
            endpoint = f"{endpoint}?{parsed.query}"
        return endpoint

    def download_file_attachments(self, message_id: str) -> list[Path]:
        attachments = self.get_attachments(message_id)
        downloaded_files: list[Path] = []

        for attachment in attachments:
            if (
                attachment.get("@odata.type")
                != "#microsoft.graph.fileAttachment"
            ):
                continue

            if attachment.get("isInline", False):
                continue

            filename = attachment.get("name")
            content_bytes = attachment.get("contentBytes")

            if not filename or not content_bytes:
                continue

            safe_filename = Path(filename).name
            output_path = self.download_dir / safe_filename

            output_path.write_bytes(
                base64.b64decode(content_bytes)
            )

            downloaded_files.append(output_path)

        return downloaded_files

    def download_supported_file_attachments(
        self,
        message_id: str,
        *,
        supported_extensions: set[str],
    ) -> SupportedAttachmentDownloadResult:
        """Download supported non-inline files without overwrite or rename."""

        result = SupportedAttachmentDownloadResult()
        attachments = self.get_attachments(message_id)

        for attachment in attachments:
            result.examined_count += 1
            attachment_type = attachment.get("@odata.type")
            normalized_type = (
                attachment_type.removeprefix("#")
                if isinstance(attachment_type, str)
                else ""
            )
            if (
                normalized_type != "microsoft.graph.fileAttachment"
                or attachment.get("isInline", False)
            ):
                result.skipped_count += 1
                continue

            filename = attachment.get("name")
            content_bytes = attachment.get("contentBytes")
            if not filename or not content_bytes:
                result.skipped_count += 1
                continue

            safe_filename = Path(str(filename)).name
            if Path(safe_filename).suffix.lower() not in supported_extensions:
                result.skipped_count += 1
                continue

            extension = Path(safe_filename).suffix.lower() or ".bin"
            try:
                content = base64.b64decode(content_bytes, validate=True)
            except Exception:
                result.skipped_count += 1
                continue
            document_fingerprint = hashlib.sha256(content).hexdigest()
            output_path = self.download_dir / f"{document_fingerprint}{extension}"
            attachment_identity = attachment.get("id")
            if not isinstance(attachment_identity, str) or not attachment_identity:
                attachment_identity = document_fingerprint
            attachment_order_key = hashlib.sha256(
                attachment_identity.encode("utf-8")
            ).hexdigest()
            if output_path.exists():
                result.collision_count += 1
                result.skipped_count += 1
                try:
                    existing_fingerprint = hashlib.sha256(
                        output_path.read_bytes()
                    ).hexdigest()
                except OSError:
                    existing_fingerprint = None
                status = (
                    "identical_collision"
                    if existing_fingerprint == document_fingerprint
                    else "different_content_collision"
                )
                result.candidate_outcomes.append(
                    SupportedAttachmentCandidateOutcome(
                        local_path=output_path,
                        document_fingerprint=document_fingerprint,
                        attachment_order_key=attachment_order_key,
                        status=status,
                    )
                )
                continue

            try:
                temporary_path = None
                with tempfile.NamedTemporaryFile(
                    "wb", dir=self.download_dir, prefix=f".{document_fingerprint}.",
                    suffix=".tmp", delete=False,
                ) as output_file:
                    temporary_path = Path(output_file.name)
                    output_file.write(content)
                    output_file.flush()
                    os.fsync(output_file.fileno())
                if output_path.exists():
                    existing_fingerprint = hashlib.sha256(output_path.read_bytes()).hexdigest()
                    if existing_fingerprint != document_fingerprint:
                        result.collision_count += 1
                        result.skipped_count += 1
                        temporary_path.unlink(missing_ok=True)
                        result.candidate_outcomes.append(SupportedAttachmentCandidateOutcome(
                            local_path=output_path, document_fingerprint=document_fingerprint,
                            attachment_order_key=attachment_order_key,
                            status="different_content_collision",
                        ))
                        continue
                    temporary_path.unlink(missing_ok=True)
                    status = "reused_identical"
                else:
                    os.replace(temporary_path, output_path)
                    status = "downloaded"
            except Exception:
                if temporary_path is not None:
                    try:
                        temporary_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                result.skipped_count += 1
                continue

            result.downloaded_files.append(output_path)
            result.candidate_outcomes.append(
                SupportedAttachmentCandidateOutcome(
                    local_path=output_path,
                    document_fingerprint=document_fingerprint,
                    attachment_order_key=attachment_order_key,
                    status=status,
                )
            )

        return result
