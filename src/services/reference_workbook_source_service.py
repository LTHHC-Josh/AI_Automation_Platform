from dataclasses import dataclass, field
import os
from urllib.parse import quote

from src.graph.client import GraphClient


REFERENCE_DRIVE_ENV = "GRAPH_REFERENCE_DRIVE_ID"
REFERENCE_ITEM_ENV = "GRAPH_REFERENCE_ITEM_ID"


@dataclass(frozen=True)
class ReferenceWorkbookSourceConfig:
    drive_id: str = field(repr=False)
    item_id: str = field(repr=False)


def load_reference_workbook_source_config() -> ReferenceWorkbookSourceConfig:
    config = ReferenceWorkbookSourceConfig(
        drive_id=os.getenv(REFERENCE_DRIVE_ENV, "").strip(),
        item_id=os.getenv(REFERENCE_ITEM_ENV, "").strip(),
    )
    if not config.drive_id or not config.item_id:
        raise ValueError(
            "Reference workbook source configuration requires "
            f"{REFERENCE_DRIVE_ENV} and {REFERENCE_ITEM_ENV}."
        )
    return config


class GraphReferenceWorkbookSource:
    """Read SharePoint drive-item metadata and workbook bytes through Graph."""

    def __init__(self, *, client: GraphClient | None = None, config: ReferenceWorkbookSourceConfig | None = None):
        self.client = client or GraphClient()
        self.config = config or load_reference_workbook_source_config()

    def get_version(self) -> str:
        metadata = self.client.get(
            self._endpoint(),
            params={"$select": "eTag,lastModifiedDateTime,size"},
            operation_category="reference_metadata",
        )
        if not isinstance(metadata, dict):
            raise ValueError("Reference metadata is invalid.")
        version = str(metadata.get("eTag") or metadata.get("lastModifiedDateTime") or "").strip()
        if not version:
            raise ValueError("Reference version is unavailable.")
        return version

    def download(self) -> bytes:
        content = self.client.get_content(
            f"{self._endpoint()}/content",
            operation_category="reference_download",
        )
        if not isinstance(content, bytes) or not content:
            raise ValueError("Reference workbook content is unavailable.")
        return content

    def _endpoint(self) -> str:
        drive = quote(self.config.drive_id, safe="")
        item = quote(self.config.item_id, safe="")
        return f"/drives/{drive}/items/{item}"
