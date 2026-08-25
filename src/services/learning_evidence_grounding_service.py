from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from src.models.learning_document_evidence import LearningDocumentEvidence


@dataclass(frozen=True, repr=False)
class LearningGroundingResult:
    analysis: dict[str, Any]
    valid_reference_count: int
    unsupported_reference_count: int
    malformed_reference_count: int
    duplicate_reference_count: int


class LearningEvidenceGroundingService:
    """Resolve request-local model aliases to protected internal evidence."""

    def resolve(self, analysis: Any, evidence: LearningDocumentEvidence) -> LearningGroundingResult:
        value = deepcopy(analysis) if isinstance(analysis, dict) else {}
        valid = unsupported = malformed = duplicates = 0

        def resolve_list(raw_value):
            nonlocal valid, unsupported, malformed, duplicates
            supplied = raw_value if isinstance(raw_value, list) else []
            results = []
            seen = set()
            for raw in supplied:
                reference = str(raw or "").strip()
                internal = evidence.resolve_model_reference(reference)
                if internal is None:
                    if not evidence.is_well_formed_model_reference(reference):
                        malformed += 1
                    else:
                        unsupported += 1
                    continue
                if internal in seen:
                    duplicates += 1
                    continue
                seen.add(internal)
                results.append(internal)
                valid += 1
            return results

        coverage = value.get("coverage")
        if isinstance(coverage, dict):
            if "analyzed_evidence_refs" in coverage:
                coverage["analyzed_evidence_refs"] = resolve_list(
                    coverage.get("analyzed_evidence_refs")
                )
            page_refs = coverage.get("analyzed_page_refs")
            page_refs = page_refs if isinstance(page_refs, list) else []
            valid_pages = []
            allowed_pages = set(evidence.page_references)
            for raw in page_refs:
                try:
                    page = int(raw)
                except (TypeError, ValueError):
                    continue
                if page in allowed_pages and page not in valid_pages:
                    valid_pages.append(page)
            coverage["analyzed_page_refs"] = valid_pages
        for section in ("observations", "contradictions"):
            items = value.get(section)
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    item["evidence_refs"] = resolve_list(item.get("evidence_refs"))

        value["grounding"] = {
            "valid_reference_count": valid,
            "unsupported_reference_count": unsupported,
            "malformed_reference_count": malformed,
            "duplicate_reference_count": duplicates,
        }
        return LearningGroundingResult(
            analysis=value,
            valid_reference_count=valid,
            unsupported_reference_count=unsupported,
            malformed_reference_count=malformed,
            duplicate_reference_count=duplicates,
        )
