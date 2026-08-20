import base64
from dataclasses import dataclass, field
from pathlib import Path

from .client import GraphClient
from .config import load_graph_config


@dataclass(repr=False)
class SupportedAttachmentDownloadResult:
    downloaded_files: list[Path] = field(default_factory=list, repr=False)
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

            output_path = self.download_dir / safe_filename
            if output_path.exists():
                result.collision_count += 1
                result.skipped_count += 1
                continue

            created_output = False
            try:
                content = base64.b64decode(content_bytes, validate=True)
                with output_path.open("xb") as output_file:
                    created_output = True
                    output_file.write(content)
            except FileExistsError:
                result.collision_count += 1
                result.skipped_count += 1
                continue
            except Exception:
                if created_output:
                    try:
                        output_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                result.skipped_count += 1
                continue

            result.downloaded_files.append(output_path)

        return result
