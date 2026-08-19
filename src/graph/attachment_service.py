import base64
from pathlib import Path

from .client import GraphClient
from .config import load_graph_config


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
