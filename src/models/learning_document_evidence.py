from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from src.models.ocr_document import OCRDocument


@dataclass(frozen=True, repr=False)
class LearningDocumentEvidence:
    """Protected complete-document evidence supplied only to local learning."""

    ocr_document: OCRDocument
    modeled_field_names: tuple[str, ...] = ()

    @property
    def evidence_ids(self) -> frozenset[str]:
        return self.ocr_document.evidence_ids

    @classmethod
    def build(
        cls,
        ocr_document: OCRDocument,
        modeled_field_names: Iterable[str] = (),
    ) -> "LearningDocumentEvidence":
        modeled = tuple(dict.fromkeys(
            str(name).strip() for name in modeled_field_names
            if re.fullmatch(r"[a-z][a-z0-9_]{0,63}", str(name).strip())
        ))
        return cls(ocr_document=ocr_document, modeled_field_names=modeled)

    def to_local_prompt(self) -> str:
        lines = [
            f"RELATIONSHIP_STATUS: {self.ocr_document.relationship_status}",
            "MODELED_FIELDS: " + ", ".join(self.modeled_field_names),
            "COMPLETE_DOCUMENT_EVIDENCE:",
        ]
        for page in self.ocr_document.pages:
            page_ref = str(page.page_number) if page.page_number is not None else "unknown"
            lines.append(f"<PAGE ref={page_ref}>")
            for block in page.blocks:
                hint = block.block_type if block.block_type else "unknown"
                bbox = (
                    ",".join(f"{item:.4f}" for item in block.bounding_box)
                    if block.bounding_box is not None else "unavailable"
                )
                lines.append(
                    f"<BLOCK id={block.block_id} hint={hint} bbox_hint={bbox}>"
                )
                lines.append(block.text)
                lines.append("</BLOCK>")
            lines.append("</PAGE>")
        return "\n".join(lines)
