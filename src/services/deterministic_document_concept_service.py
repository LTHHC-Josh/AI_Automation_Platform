from __future__ import annotations

import re

from src.models.document_concept import (
    DeterministicDocumentConcept,
    DocumentConceptEvidence,
)
from src.models.ocr_document import OCRDocument
from src.services.contact_failure_normalization_service import (
    ContactFailureNormalizationService,
)


class DeterministicDocumentConceptService:
    """Analyze registered concepts across every protected OCR block once."""

    FORM_2067 = re.compile(
        r"(?<![A-Za-z0-9])(?:[A-Za-z])?2067"
        r"(?:-[A-Za-z0-9]{1,8}(?![A-Za-z0-9])|(?![-A-Za-z0-9]))",
        re.IGNORECASE,
    )
    CONTACT_SUCCESS_ACTION_TERMS = {
        "answered", "contacted", "reached", "responded",
    }
    CONTACT_SUCCESS_STATE_TERMS = {
        "completed", "confirmed", "established", "successful", "successfully",
    }
    CONTACT_SPEECH_TERMS = {"spoke"}
    CONTACT_ATTEMPT_TERMS = {"attempt", "attempted", "trying", "tried"}
    NEGATED_FAILURE = re.compile(
        r"\b(?:not|no\s+longer)\s+(?:unable|unreachable)\b",
        re.IGNORECASE,
    )

    def __init__(self, *, contact_normalizer=None) -> None:
        self._contact_normalizer = (
            contact_normalizer or ContactFailureNormalizationService()
        )

    def analyze(self, ocr_document: OCRDocument) -> tuple[DeterministicDocumentConcept, ...]:
        form_support = []
        contact_support = []
        contact_conflict = []
        contact_success = []
        contact_support_occurrences = 0
        contact_conflict_occurrences = 0
        for page in ocr_document.pages:
            page_entries = []
            for block_ordinal, block in enumerate(page.blocks, start=1):
                reference = DocumentConceptEvidence(
                    block_id=block.block_id,
                    page_ordinal=page.page_number,
                    block_ordinal=block_ordinal,
                    source_text=block.text,
                    confidence=block.confidence,
                    evidence_kind=block.block_type,
                )
                page_entries.append((reference, block.text))

            for reference, text in page_entries:
                references = (reference,)
                if self.FORM_2067.search(text):
                    self._extend_unique(form_support, references)
                normalized = self._contact_normalizer.normalize(
                    source_text=text,
                    confidence=self._minimum_confidence(references),
                )
                if normalized.supported:
                    self._extend_unique(contact_support, references)
                    contact_support_occurrences += 1
                if self._contact_success_references(text):
                    self._extend_unique(contact_success, references)
                if self._contact_success_references(text) or self.NEGATED_FAILURE.search(text):
                    self._extend_unique(contact_conflict, references)
                    contact_conflict_occurrences += 1

            for left, right in zip(page_entries, page_entries[1:]):
                references = (left[0], right[0])
                text = f"{left[1]} {right[1]}"
                if self.FORM_2067.search(text):
                    self._extend_unique(form_support, references)
                known_support = {item.block_id for item in contact_support}
                normalized = self._contact_normalizer.normalize(
                    source_text=text,
                    confidence=self._minimum_confidence(references),
                )
                if normalized.supported and not any(
                    item.block_id in known_support for item in references
                ):
                    self._extend_unique(contact_support, references)
                    contact_support_occurrences += 1
                known_conflict = {item.block_id for item in contact_conflict}
                if (
                    self._contact_success_references(text)
                    or self.NEGATED_FAILURE.search(text)
                ) and not any(
                    item.block_id in known_conflict for item in references
                ):
                    self._extend_unique(contact_conflict, references)
                    contact_conflict_occurrences += 1
                if self._contact_success_references(text):
                    self._extend_unique(contact_success, references)

        concepts = []
        if form_support:
            concepts.append(self._concept(
                "form_2067", form_support, [], 1, 0
            ))
        if contact_support or contact_conflict:
            concepts.append(self._concept(
                "contact_failure", contact_support, contact_conflict,
                contact_support_occurrences, contact_conflict_occurrences,
            ))
        if contact_success:
            concepts.append(self._concept(
                "contact_success", contact_success, [], len(contact_success), 0
            ))
        return tuple(concepts)

    @classmethod
    def _contact_success_references(cls, text: str) -> bool:
        for tokens in ContactFailureNormalizationService._clauses(text):
            if tokens & cls.NEGATION_TERMS or tokens & cls.FAILURE_TERMS:
                continue
            if tokens & cls.CONTACT_ATTEMPT_TERMS:
                continue
            has_contact = bool(
                tokens & (cls.CONTACT_TERMS | cls.CONTACT_SUCCESS_ACTION_TERMS)
            )
            has_member = bool(tokens & cls.MEMBER_TERMS)
            if (
                has_contact
                and bool(tokens & cls.CONTACT_SUCCESS_STATE_TERMS)
            ):
                return True
            if (
                has_member
                and has_contact
                and bool(tokens & cls.CONTACT_SUCCESS_ACTION_TERMS)
            ):
                return True
            if has_member and bool(tokens & cls.CONTACT_SPEECH_TERMS):
                return True
        return False

    NEGATION_TERMS = ContactFailureNormalizationService.NEGATION_TERMS
    FAILURE_TERMS = ContactFailureNormalizationService.FAILURE_TERMS
    CONTACT_TERMS = ContactFailureNormalizationService.CONTACT_TERMS
    MEMBER_TERMS = ContactFailureNormalizationService.MEMBER_TERMS

    @staticmethod
    def _extend_unique(target, references) -> None:
        known = {item.block_id for item in target}
        target.extend(item for item in references if item.block_id not in known)

    @staticmethod
    def _minimum_confidence(references) -> float | None:
        values = [
            item.confidence for item in references if item.confidence is not None
        ]
        return min(values) if values else None

    @classmethod
    def _concept(
        cls, name, support, conflict, support_occurrences, conflict_occurrences
    ) -> DeterministicDocumentConcept:
        if support and conflict:
            status = "conflicting"
        elif support:
            status = "supported"
        elif conflict:
            status = "unsupported"
        else:
            status = "unknown"
        confidences = [
            item.confidence for item in support
            if item.confidence is not None
        ]
        confidence = min(confidences) if confidences else None
        return DeterministicDocumentConcept(
            concept_name=name,
            support_status=status,
            supporting_evidence=tuple(support),
            conflicting_evidence=tuple(conflict),
            confidence=confidence,
            support_occurrence_count=support_occurrences,
            conflict_occurrence_count=conflict_occurrences,
        )
