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

    @property
    def model_reference_map(self) -> dict[str, str]:
        return {
            f"e{ordinal:04d}": block.block_id
            for ordinal, block in enumerate(
                (
                    block
                    for page in self.ocr_document.pages
                    for block in page.blocks
                ),
                start=1,
            )
        }

    @property
    def model_references(self) -> tuple[str, ...]:
        return tuple(self.model_reference_map)

    @property
    def page_references(self) -> tuple[int, ...]:
        return tuple(
            page.page_number for page in self.ocr_document.pages
            if page.page_number is not None
        )

    def resolve_model_reference(self, value: str) -> str | None:
        reference = str(value or "").strip()
        mapped = self.model_reference_map.get(reference)
        if mapped is not None:
            return mapped
        # Backward-compatible migration support for schema-v2 mock/provider
        # responses that returned protected internal identifiers directly.
        return reference if reference in self.evidence_ids else None

    def is_well_formed_model_reference(self, value: str) -> bool:
        reference = str(value or "").strip()
        return bool(
            re.fullmatch(r"e\d{4}", reference)
            or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", reference)
        )

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
        aliases = self.model_reference_map
        internal_to_alias = {internal: alias for alias, internal in aliases.items()}
        lines = [
            f"RELATIONSHIP_STATUS: {self.ocr_document.relationship_status}",
            "MODELED_FIELDS: " + ", ".join(self.modeled_field_names),
            "COMPLETE_DOCUMENT_EVIDENCE:",
        ]
        for page in self.ocr_document.pages:
            page_ref = str(page.page_number) if page.page_number is not None else "unknown"
            lines.append(f'<PAGE ref="{page_ref}">')
            for block_ordinal, block in enumerate(page.blocks, start=1):
                hint = block.block_type if block.block_type else "unknown"
                bbox = (
                    ",".join(f"{item:.4f}" for item in block.bounding_box)
                    if block.bounding_box is not None else "unavailable"
                )
                lines.append(
                    f'<BLOCK ref="{internal_to_alias[block.block_id]}" '
                    f'ordinal="{block_ordinal}" hint="{hint}" bbox_hint="{bbox}">'
                )
                lines.append(block.text)
                lines.append("</BLOCK>")
            lines.append("</PAGE>")
        return "\n".join(lines)
