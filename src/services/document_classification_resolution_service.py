from __future__ import annotations

from typing import Any, Iterable

from src.models.document_concept import DeterministicDocumentConcept
from src.models.document_taxonomy import DocumentTaxonomyRegistry


class DocumentClassificationResolutionService:
    """Resolve family/subtype without allowing model output to bypass rules."""

    def resolve(
        self,
        classification: Any,
        concepts: Iterable[DeterministicDocumentConcept],
    ) -> dict[str, Any]:
        candidate = classification if isinstance(classification, dict) else {}
        concept_map = {item.concept_name: item for item in concepts}
        family = DocumentTaxonomyRegistry.normalize_family(
            candidate.get("document_category")
        )
        form_2067 = concept_map.get("form_2067")
        if form_2067 is not None and form_2067.supported:
            family = "2067"
        elif family == "2067":
            family = "unknown"

        requested_subtype = DocumentTaxonomyRegistry.normalize_subtype(
            family, candidate.get("document_subtype")
        )
        subtype = requested_subtype
        subtype_status = "supported" if subtype != "unknown" else "unknown"
        family_confidence = self._nullable_confidence(candidate.get("confidence"))
        subtype_confidence = family_confidence if subtype != "unknown" else None
        if family == "unknown":
            family_confidence = None
            subtype_confidence = None
            candidate = {**candidate, "confidence": None}
        if family == "2067":
            family_confidence = form_2067.confidence if form_2067 is not None else None
            contact = concept_map.get("contact_failure")
            if contact is not None and contact.supported:
                subtype = "utl"
                subtype_status = "supported"
                subtype_confidence = contact.confidence
            else:
                subtype = "unknown"
                subtype_confidence = None
                subtype_status = (
                    contact.support_status if contact is not None else "missing"
                )

        return {
            **candidate,
            "document_category": family,
            "document_subtype": subtype,
            "document_type": DocumentTaxonomyRegistry.legacy_route(family, subtype),
            "classification_support_status": (
                "supported" if family != "unknown" else "unknown"
            ),
            "subtype_support_status": subtype_status,
            "family_evidence_confidence": family_confidence,
            "subtype_evidence_confidence": subtype_confidence,
        }

    @staticmethod
    def _nullable_confidence(value) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return None
        if normalized > 1:
            normalized /= 100
        return normalized if 0 <= normalized <= 1 else None
