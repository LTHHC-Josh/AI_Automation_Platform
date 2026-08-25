from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, repr=False)
class DocumentConceptEvidence:
    """Protected evidence for one normalized deterministic concept."""

    block_id: str = field(repr=False)
    page_ordinal: int | None
    block_ordinal: int
    source_text: str = field(repr=False)
    confidence: float | None = None
    evidence_kind: str = "unknown"


@dataclass(frozen=True, repr=False)
class DeterministicDocumentConcept:
    """A normalized concept kept separate from literal evidence and rules."""

    concept_name: str
    support_status: str
    supporting_evidence: tuple[DocumentConceptEvidence, ...] = field(
        default=(), repr=False
    )
    conflicting_evidence: tuple[DocumentConceptEvidence, ...] = field(
        default=(), repr=False
    )
    confidence: float | None = None
    support_occurrence_count: int = 0
    conflict_occurrence_count: int = 0

    @property
    def supported(self) -> bool:
        return self.support_status == "supported" and bool(self.supporting_evidence)
