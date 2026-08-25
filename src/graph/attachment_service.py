import base64
from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import tempfile

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
            if (
                attachment.get("@odata.type")
                != "#microsoft.graph.fileAttachment"
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
