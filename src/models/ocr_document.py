from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


@dataclass(frozen=True, repr=False)
class OCRBlock:
    """One protected OCR block in document reading order."""

    block_id: str
    text: str = field(repr=False)
    reading_order: int
    block_type: str = "unknown"
    confidence: float | None = None
    bounding_box: tuple[float, float, float, float] | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", self.block_id):
            raise ValueError("OCR block identifier must be an opaque safe label.")
        if self.block_type not in {
            "text", "table", "checkbox", "header", "footer", "unknown"
        }:
            object.__setattr__(self, "block_type", "unknown")


@dataclass(frozen=True, repr=False)
class OCRPage:
    """One page and its protected OCR blocks."""

    page_number: int | None
    blocks: tuple[OCRBlock, ...] = ()


@dataclass(frozen=True, repr=False)
class OCRDocument:
    """Protected complete-document OCR with optional page/layout relations."""

    pages: tuple[OCRPage, ...]
    relationship_status: str
    schema_version: int = 1

    @property
    def raw_text(self) -> str:
        return "\n\n".join(
            "\n".join(block.text for block in page.blocks if block.text.strip())
            for page in self.pages
            if any(block.text.strip() for block in page.blocks)
        ).strip()

    @property
    def evidence_ids(self) -> frozenset[str]:
        return frozenset(
            block.block_id for page in self.pages for block in page.blocks
        )

    @property
    def page_count(self) -> int | None:
        numbered = [page.page_number for page in self.pages if page.page_number]
        return max(numbered) if numbered else None

    @classmethod
    def from_flat_text(cls, text: str) -> "OCRDocument":
        cleaned = str(text or "").strip()
        blocks = (
            (OCRBlock(block_id="block_1", text=cleaned, reading_order=1),)
            if cleaned
            else ()
        )
        return cls(
            pages=(OCRPage(page_number=None, blocks=blocks),),
            relationship_status="unavailable_legacy_flat",
        )

    def to_protected_cache_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "relationship_status": self.relationship_status,
            "pages": [
                {
                    "page_number": page.page_number,
                    "blocks": [
                        {
                            "block_id": block.block_id,
                            "text": block.text,
                            "reading_order": block.reading_order,
                            "block_type": block.block_type,
                            "confidence": block.confidence,
                            "bounding_box": list(block.bounding_box)
                            if block.bounding_box is not None else None,
                        }
                        for block in page.blocks
                    ],
                }
                for page in self.pages
            ],
        }

    @classmethod
    def from_protected_cache_dict(cls, value: Any) -> "OCRDocument | None":
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            return None
        status = value.get("relationship_status")
        if status not in {"preserved", "unavailable_legacy_flat"}:
            return None
        raw_pages = value.get("pages")
        if not isinstance(raw_pages, list):
            return None
        pages = []
        seen_ids: set[str] = set()
        for raw_page in raw_pages:
            if not isinstance(raw_page, dict):
                return None
            page_number = raw_page.get("page_number")
            if page_number is not None and (
                not isinstance(page_number, int) or isinstance(page_number, bool)
                or page_number < 1
            ):
                return None
            raw_blocks = raw_page.get("blocks")
            if not isinstance(raw_blocks, list):
                return None
            blocks = []
            for raw_block in raw_blocks:
                if not isinstance(raw_block, dict):
                    return None
                block_id = str(raw_block.get("block_id") or "")
                text = str(raw_block.get("text") or "").strip()
                order = raw_block.get("reading_order")
                if (
                    not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", block_id)
                    or block_id in seen_ids or not text
                    or not isinstance(order, int) or isinstance(order, bool) or order < 1
                ):
                    return None
                seen_ids.add(block_id)
                confidence = raw_block.get("confidence")
                if confidence is not None:
                    try:
                        confidence = max(0.0, min(float(confidence), 1.0))
                    except (TypeError, ValueError):
                        confidence = None
                bbox = raw_block.get("bounding_box")
                if isinstance(bbox, list) and len(bbox) == 4:
                    try:
                        bbox_value = tuple(float(item) for item in bbox)
                    except (TypeError, ValueError):
                        bbox_value = None
                else:
                    bbox_value = None
                blocks.append(OCRBlock(
                    block_id=block_id,
                    text=text,
                    reading_order=order,
                    block_type=str(raw_block.get("block_type") or "unknown"),
                    confidence=confidence,
                    bounding_box=bbox_value,
                ))
            pages.append(OCRPage(page_number=page_number, blocks=tuple(blocks)))
        document = cls(pages=tuple(pages), relationship_status=status)
        return document if document.raw_text else None
