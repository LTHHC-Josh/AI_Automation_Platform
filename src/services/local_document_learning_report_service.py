from __future__ import annotations

from pathlib import Path
from math import isfinite
import re
from typing import Any, Iterable

from src.models.document import Document
from src.models.ocr_document import OCRDocument
from src.services.learning_label_sanitizer import LearningLabelSanitizer
from src.models.document_taxonomy import DocumentTaxonomyRegistry


class LocalDocumentLearningReportService:
    """Build a value-free structural report from one processed document."""

    SAFE_LABEL_TOKENS = {
        "annual", "approval", "approved", "assessment", "authorization",
        "business", "change", "claim", "communication", "contact",
        "continuation", "date", "denial", "direction", "document", "due",
        "effective", "end", "extension", "failure", "field", "form", "inbound",
        "initial", "locate", "missing", "modifier", "no", "notice",
        "outbound", "past", "posted", "purpose", "quantity", "reach",
        "referral", "renewal", "request", "requested", "review", "service",
        "start", "status", "termination", "to", "unable", "units", "unknown", "utl",
        "unmodeled", "visits", "workflow",
    }
    SAFE_EVIDENCE_STATUSES = {
        "supported", "unsupported", "conflicting", "ambiguous", "tentative",
        "missing", "unknown",
    }
    DATE_ROLES = {
        "posted", "effective", "start", "end", "request", "approval",
        "service", "communication", "unknown",
    }
    STRUCTURAL_TYPES = {
        "date", "identifier", "status", "checkbox", "quantity", "code",
        "name", "text", "selection", "table", "other",
    }
    SERVICE_FIELD_NAMES = (
        "service_code", "modifier", "quantity", "start_date", "end_date",
        "status",
    )

    def build(
        self,
        document: Document,
        analysis: Any,
        *,
        modeled_field_names: Iterable[str] = (),
    ) -> dict[str, Any]:
        safe_analysis = analysis if isinstance(analysis, dict) else {}
        modeled = tuple(dict.fromkeys(
            self._safe_modeled_field(name) for name in modeled_field_names
            if self._safe_modeled_field(name)
        ))
        if not modeled:
            modeled = tuple(dict.fromkeys(
                self._safe_modeled_field(name)
                for name in document.field_evidence
                if self._safe_modeled_field(name)
            ))

        field_inventory = [self._field_entry(document, name) for name in modeled]
        model_dates = self._safe_date_fields(safe_analysis.get("date_fields"))
        date_inventory = self._merge_date_fields(field_inventory, model_dates)
        concepts = self._safe_concepts(safe_analysis.get("business_concepts"))
        deterministic_concepts = self._deterministic_concepts(document)
        schema_gaps = self._safe_schema_gaps(safe_analysis.get("schema_gaps"))
        service_structure = self._service_structure(document, safe_analysis)
        review = self._review_structure(document, field_inventory, concepts)
        structure = safe_analysis.get("document_structure")
        structure = structure if isinstance(structure, dict) else {}
        ocr_document = (
            document.ocr_document
            if isinstance(document.ocr_document, OCRDocument)
            else OCRDocument.from_flat_text(document.raw_text)
        )
        evidence_index = self._evidence_index(ocr_document)
        observations = self._safe_observations(
            safe_analysis.get("observations"), evidence_index, set(modeled)
        )
        contradictions = self._safe_contradictions(
            safe_analysis.get("contradictions"), evidence_index
        )
        coverage = self._coverage(
            safe_analysis.get("coverage"), ocr_document, evidence_index,
            safe_analysis.get("grounding"),
        )
        novel_observations = [
            item for item in observations
            if item["current_modeled_field"] is None
        ]
        for field_item in field_inventory:
            candidates = [
                item for item in observations
                if item["current_modeled_field"] == field_item["field_name"]
            ]
            field_item["learning_candidate_count"] = len(candidates)
            field_item["learning_discovery_status"] = self._candidate_status(candidates)
            field_item["alternate_label_evidence_present"] = any(
                item["proposed_label"] != field_item["field_name"]
                for item in candidates
            )
        review["learning_review_reason_count"] = sum(
            item["observation_kind"] == "review_reason" for item in observations
        )
        review["learning_conflict_count"] = sum(
            item["evidence_status"] in {"conflicting", "ambiguous"}
            for item in observations
        ) + len(contradictions)
        review["whole_document_coverage_incomplete"] = (
            coverage["coverage_status"] != "complete"
        )
        review["learning_review_recommended"] = (
            review["learning_conflict_count"] > 0
            or review["whole_document_coverage_incomplete"]
            or any(item["requires_review"] for item in observations)
            or any(
                item["support_status"] in {"conflicting", "ambiguous", "unsupported"}
                for item in deterministic_concepts
            )
        )

        return {
            "report_schema_version": 3,
            "whole_document_coverage": coverage,
            "classification": {
                "family": self._classification_dimension(
                    document.document_category,
                    document.classification_support_status,
                    document.family_evidence_confidence,
                    deterministic_concepts,
                    "form_2067",
                    family=document.document_category,
                ),
                "subtype": self._classification_dimension(
                    document.document_subtype,
                    document.subtype_support_status,
                    document.subtype_evidence_confidence,
                    deterministic_concepts,
                    "contact_failure",
                    family=document.document_category,
                ),
            },
            "document_structure": {
                "document_form_type": self._safe_label(
                    structure.get("document_form_type"), "unknown"
                ),
                "document_category": self._safe_category(
                    structure.get("document_category"),
                    document.document_category,
                ),
                "document_subtype": self._safe_label(
                    structure.get("document_subtype"),
                    self._safe_label(document.document_subtype, "unknown"),
                ),
                "purpose_concepts": self._safe_label_list(
                    structure.get("purpose_concepts")
                ),
                "direction_context": self._safe_label_list(
                    structure.get("direction_context")
                ),
                "page_count": ocr_document.page_count or self._page_count(document.file_path),
                "analysis_basis": "local_model_structural_analysis",
            },
            "field_inventory": field_inventory,
            "date_structure": date_inventory,
            "authorization_service_structure": service_structure,
            "business_concepts": concepts,
            "deterministic_concepts": deterministic_concepts,
            "schema_gaps": schema_gaps,
            "observations": observations,
            "novel_observations": novel_observations,
            "contradictions": contradictions,
            "review_quality": review,
            "development_implications": self._development_implications(
                structure=structure,
                concepts=concepts,
                schema_gaps=schema_gaps,
                dates=date_inventory,
            ),
            "protected_values_suppressed": True,
        }

    @staticmethod
    def _candidate_status(candidates: list[dict[str, Any]]) -> str:
        statuses = {item["evidence_status"] for item in candidates}
        if "conflicting" in statuses:
            return "conflicting"
        if "ambiguous" in statuses:
            return "ambiguous"
        if "supported" in statuses:
            return "supported_repeated" if sum(
                max(item["repetition_count"], 1) for item in candidates
            ) > 1 else "supported"
        return "missing" if not candidates else "unsupported"

    @staticmethod
    def _evidence_index(ocr_document: OCRDocument) -> dict[str, dict[str, Any]]:
        index = {}
        for page in ocr_document.pages:
            for block_ordinal, block in enumerate(page.blocks, start=1):
                index[block.block_id] = {
                    "page_reference": page.page_number,
                    "block_ordinal": block_ordinal,
                    "evidence_kind": block.block_type
                    if block.block_type in {
                        "text", "table", "checkbox", "header", "footer", "unknown"
                    } else "unknown",
                }
        return index

    def _coverage(self, value, ocr_document, evidence_index, grounding=None):
        details = value if isinstance(value, dict) else {}
        supplied = details.get("analyzed_evidence_refs")
        supplied = supplied if isinstance(supplied, list) else []
        valid = list(dict.fromkeys(
            str(item) for item in supplied if str(item) in evidence_index
        ))
        all_ids = set(evidence_index)
        page_refs = details.get("analyzed_page_refs")
        page_refs = page_refs if isinstance(page_refs, list) else []
        valid_page_refs = sorted({
            item for item in page_refs
            if isinstance(item, int) and not isinstance(item, bool)
            and item in {page.page_number for page in ocr_document.pages}
        })
        expected_pages = sorted({
            page.page_number for page in ocr_document.pages
            if page.page_number is not None
        })
        legacy_complete = bool(all_ids) and set(valid) == all_ids
        complete = (
            details.get("complete_document_analyzed") is True
            and (valid_page_refs == expected_pages or legacy_complete)
        )
        safe_grounding = grounding if isinstance(grounding, dict) else {}
        return {
            "complete_document_analyzed": complete,
            "coverage_status": "complete" if complete else "incomplete",
            "page_relationship_status": ocr_document.relationship_status,
            "page_count": ocr_document.page_count,
            "evidence_block_count": len(all_ids),
            "analyzed_evidence_block_count": len(valid),
            "delivered_evidence_block_count": len(all_ids),
            "model_claimed_page_count": len(valid_page_refs),
            "grounded_reference_count": self._integer(
                safe_grounding.get("valid_reference_count")
            ),
            "unsupported_reference_count": self._integer(
                safe_grounding.get("unsupported_reference_count")
            ) + self._integer(safe_grounding.get("malformed_reference_count")),
            "layout_used_as_hint_only": True,
        }

    def _safe_observations(self, value, evidence_index, modeled):
        results = []
        sanitizer = LearningLabelSanitizer()
        allowed_kinds = {
            "document_family", "form_identifier", "modeled_field", "date_role",
            "service_structure", "business_concept", "free_text_concept",
            "schema_gap", "review_reason",
        }
        allowed_categories = {
            "business", "date", "document", "field", "form", "service",
            "workflow", "free_text", "other",
        }
        for ordinal, item in enumerate(value if isinstance(value, list) else [], start=1):
            if not isinstance(item, dict):
                continue
            kind = str(item.get("observation_kind") or "")
            if kind not in allowed_kinds:
                continue
            category = str(item.get("proposed_category") or "other")
            if category not in allowed_categories:
                category = "other"
            safe_label = sanitizer.sanitize(
                item.get("normalized_label"), category=category, ordinal=ordinal
            )
            refs = item.get("evidence_refs")
            refs = refs if isinstance(refs, list) else []
            refs = list(dict.fromkeys(str(ref) for ref in refs if str(ref) in evidence_index))
            requested_status = self._evidence_status(item.get("evidence_status"))
            supported = requested_status == "supported" and bool(refs)
            status = requested_status if refs else "unsupported"
            if requested_status in {"conflicting", "ambiguous"}:
                semantic_concept = None
            else:
                semantic_concept = safe_label.label if supported else None
            current = self._safe_modeled_field(item.get("current_modeled_field"))
            if current not in modeled:
                current = None
            results.append({
                "observation_id": f"observation_{ordinal}",
                "observation_kind": kind,
                "proposed_label": safe_label.label,
                "label_disposition": safe_label.disposition,
                "proposed_category": category,
                "normalized_concept": semantic_concept,
                "current_modeled_field": current,
                "evidence_status": status,
                "confidence": self._nullable_confidence(item.get("confidence")),
                "evidence_references": [
                    {
                        "page_reference": evidence_index[ref]["page_reference"],
                        "block_ordinal": evidence_index[ref]["block_ordinal"],
                        "evidence_kind": evidence_index[ref]["evidence_kind"],
                    }
                    for ref in refs
                ],
                "repetition_count": self._integer(item.get("repetition_count")),
                "requires_review": status in {
                    "unsupported", "conflicting", "ambiguous", "tentative", "unknown"
                },
                "deterministically_validated": False,
                "automatic_rule_change": False,
                "production_rule_status": "not_mapped",
            })
        return results

    def _deterministic_concepts(self, document: Document) -> list[dict[str, Any]]:
        results = []
        for concept in document.deterministic_concepts or ():
            support = list(concept.supporting_evidence)
            conflicts = list(concept.conflicting_evidence)
            results.append({
                "concept_label": self._safe_label(
                    concept.concept_name, "unknown"
                ),
                "support_status": self._evidence_status(concept.support_status),
                "confidence": self._nullable_confidence(concept.confidence),
                "supporting_evidence_count": len(support),
                "conflicting_evidence_count": len(conflicts),
                "support_occurrence_count": concept.support_occurrence_count,
                "conflict_occurrence_count": concept.conflict_occurrence_count,
                "repeated_evidence": concept.support_occurrence_count > 1,
                "evidence_references": [
                    {
                        "page_reference": item.page_ordinal,
                        "block_ordinal": item.block_ordinal,
                        "evidence_kind": item.evidence_kind,
                    }
                    for item in (*support, *conflicts)
                ],
                "deterministically_validated": True,
                "production_rule_status": (
                    "approved_subtype_evidence"
                    if concept.concept_name == "contact_failure"
                    else "approved_family_evidence"
                    if concept.concept_name == "form_2067"
                    else "not_mapped"
                ),
            })
        return results

    def _classification_dimension(
        self, label, status, confidence, concepts, evidence_concept, *, family
    ) -> dict[str, Any]:
        evidence_count = sum(
            item["supporting_evidence_count"]
            for item in concepts
            if item["concept_label"] == evidence_concept
        )
        normalized_label = (
            DocumentTaxonomyRegistry.normalize_family(label)
            if evidence_concept == "form_2067"
            else DocumentTaxonomyRegistry.normalize_subtype(family, label)
        )
        normalized_status = self._evidence_status(status)
        normalized_confidence = self._nullable_confidence(confidence)
        if normalized_label == "unknown":
            normalized_status = "unknown"
            normalized_confidence = None
        return {
            "label": normalized_label,
            "support_status": normalized_status,
            "confidence": normalized_confidence,
            "evidence_reference_count": evidence_count,
            "review_required": (
                normalized_label == "unknown"
                or normalized_status != "supported"
            ),
        }

    def _safe_contradictions(self, value, evidence_index):
        results = []
        sanitizer = LearningLabelSanitizer()
        for ordinal, item in enumerate(value if isinstance(value, list) else [], start=1):
            if not isinstance(item, dict):
                continue
            refs = item.get("evidence_refs")
            refs = refs if isinstance(refs, list) else []
            refs = list(dict.fromkeys(str(ref) for ref in refs if str(ref) in evidence_index))
            label = sanitizer.sanitize(
                item.get("contradiction_type"), category="other", ordinal=ordinal
            )
            status = str(item.get("evidence_status") or "unknown")
            if status not in {"conflicting", "ambiguous"} or not refs:
                status = "unknown"
            results.append({
                "contradiction_id": f"contradiction_{ordinal}",
                "contradiction_type": label.label,
                "label_disposition": label.disposition,
                "evidence_status": status,
                "evidence_reference_count": len(refs),
                "requires_review": True,
                "deterministically_validated": False,
            })
        return results

    def _field_entry(self, document: Document, name: str) -> dict[str, Any]:
        evidence = document.field_evidence.get(name)
        evidence = evidence if isinstance(evidence, dict) else {}
        value = evidence.get("value", document.extracted_data.get(name))
        source_present = bool(str(evidence.get("source_text") or "").strip())
        action_status = self._field_action_status(document, name)
        present = value is not None and (not isinstance(value, str) or bool(value.strip()))
        status = action_status or (
            "supported"
            if present and source_present
            else "unsupported"
            if present or source_present
            else "missing"
        )
        return {
            "field_name": name,
            "present": present,
            "support_status": status,
            "confidence": self._confidence(evidence.get(
                "confidence", document.field_confidences.get(name, 0.0)
            )),
            "evidence_available": source_present,
            "validation_status": action_status or "not_flagged",
        }

    def _field_action_status(self, document: Document, name: str) -> str | None:
        prefix = name.lower().replace("_", " ")
        for action in document.validation_actions or []:
            text = str(action or "").lower().replace("_", " ")
            if prefix not in text:
                continue
            if "conflict" in text or "multiple" in text:
                return "conflicting"
            if "ambigu" in text or "relationship" in text:
                return "ambiguous"
            return "unsupported"
        return None

    def _safe_date_fields(self, value: Any) -> list[dict[str, Any]]:
        results = []
        for item in value if isinstance(value, list) else []:
            if not isinstance(item, dict):
                continue
            label = self._safe_label(item.get("field_name"), "unmodeled_date_field")
            role = str(item.get("semantic_role") or "unknown").strip().lower()
            status = self._evidence_status(item.get("evidence_status"))
            results.append({
                "field_name": label,
                "semantic_role": role if role in self.DATE_ROLES else "unknown",
                "support_status": status,
                "deterministically_validated": False,
            })
        return self._deduplicate(results, "field_name")

    def _merge_date_fields(
        self, fields: list[dict[str, Any]], model_dates: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        results = list(model_dates)
        existing = {item["field_name"] for item in results}
        for field in fields:
            name = field["field_name"]
            if "date" not in name or name in existing:
                continue
            role = next((r for r in self.DATE_ROLES if r != "unknown" and r in name), "unknown")
            results.append({
                "field_name": name,
                "semantic_role": role,
                "support_status": field["support_status"],
                "deterministically_validated": True,
            })
        return results

    def _safe_concepts(self, value: Any) -> list[dict[str, Any]]:
        results = []
        for item in value if isinstance(value, list) else []:
            if not isinstance(item, dict) or item.get("explicitly_supported") is not True:
                continue
            label = self._safe_label(item.get("concept_label"), "unmodeled_business_concept")
            results.append({
                "concept_label": label,
                "explicitly_supported": True,
                "evidence_status": self._evidence_status(item.get("evidence_status")),
                "current_modeled_field": item.get("current_modeled_field") is True,
                "deterministically_validated": False,
            })
        return self._deduplicate(results, "concept_label")

    def _safe_schema_gaps(self, value: Any) -> list[dict[str, Any]]:
        results = []
        for item in value if isinstance(value, list) else []:
            if not isinstance(item, dict):
                continue
            structural_type = str(item.get("structural_type") or "other").lower()
            results.append({
                "candidate_name": self._safe_label(
                    item.get("candidate_name"), "unmodeled_field"
                ),
                "structural_type": (
                    structural_type if structural_type in self.STRUCTURAL_TYPES else "other"
                ),
                "evidence_status": self._evidence_status(item.get("evidence_status")),
                "deterministically_validated": False,
            })
        return self._deduplicate(results, "candidate_name")

    def _service_structure(self, document: Document, analysis: dict[str, Any]) -> dict[str, Any]:
        details = analysis.get("authorization_service_structure")
        details = details if isinstance(details, dict) else {}
        types = []
        for name in self.SERVICE_FIELD_NAMES:
            if any(self._present(getattr(line, name, None)) for line in document.service_lines):
                types.append(name)
        return {
            "authorization_concepts_present": details.get("authorization_concepts_present") is True,
            "service_line_count": len(document.service_lines),
            "service_field_types_present": types,
            "quantity_concepts_present": details.get("quantity_concepts_present") is True,
            "units_concepts_present": details.get("units_concepts_present") is True,
            "visits_concepts_present": details.get("visits_concepts_present") is True,
            "modifiers_present": "modifier" in types,
            "service_codes_present": "service_code" in types,
            "approval_concepts_present": details.get("approval_concepts_present") is True,
            "request_concepts_present": details.get("request_concepts_present") is True,
        }

    def _review_structure(
        self, document: Document, fields: list[dict[str, Any]], concepts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        unresolved = sorted({
            item["field_name"] for item in fields
            if item["support_status"] in {"ambiguous", "conflicting", "unsupported"}
        } | {
            item["concept_label"] for item in concepts
            if item["evidence_status"] in {"ambiguous", "conflicting", "tentative"}
        })
        reason_fields = sorted({
            item["field_name"] for item in fields
            if any(item["field_name"].replace("_", " ") in str(reason).lower().replace("_", " ")
                   for reason in document.review_reasons or [])
        })
        metrics = document.processing_metrics if isinstance(document.processing_metrics, dict) else {}
        return {
            "review_required": document.needs_human_review is True,
            "review_status": self._safe_review_status(document.review_status),
            "review_reason_fields": reason_fields,
            "classification_attempts": 1 if document.document_category else 0,
            "extraction_attempts": self._integer(metrics.get("extraction_attempt_count")),
            "selected_attempt": self._integer(metrics.get("extraction_selected_attempt")),
            "retry_occurred": metrics.get("extraction_retry_triggered") is True,
            "unresolved_ambiguities": unresolved,
        }

    def _development_implications(self, *, structure, concepts, schema_gaps, dates):
        implications = []
        for gap in schema_gaps:
            implications.append({
                "type": "potential_extraction_field",
                "target": gap["candidate_name"],
                "basis": "observed_evidence",
                "deterministically_validated": gap["deterministically_validated"],
                "automatic_rule_change": False,
            })
        for concept in concepts:
            if not concept["current_modeled_field"]:
                implications.append({
                    "type": "potential_workflow_context",
                    "target": concept["concept_label"],
                    "basis": "proposed_interpretation",
                    "deterministically_validated": False,
                    "automatic_rule_change": False,
                })
                implications.append({
                    "type": "reference_table_candidate",
                    "target": concept["concept_label"],
                    "basis": "proposed_interpretation",
                    "deterministically_validated": False,
                    "automatic_rule_change": False,
                })
        for date in dates:
            if date["support_status"] != "missing":
                implications.append({
                    "type": "potential_date_validation_rule",
                    "target": date["field_name"],
                    "basis": "proposed_interpretation",
                    "deterministically_validated": date["deterministically_validated"],
                    "automatic_rule_change": False,
                })
        form = self._safe_label(structure.get("document_form_type"), "unknown")
        if form != "unknown":
            implications.append({
                "type": "potential_document_classification",
                "target": form,
                "basis": "proposed_interpretation",
                "deterministically_validated": False,
                "automatic_rule_change": False,
            })
            implications.append({
                "type": "filename_rule_review_only",
                "target": form,
                "basis": "proposed_interpretation",
                "deterministically_validated": False,
                "automatic_rule_change": False,
            })
        return self._deduplicate(implications, "type", "target")

    def _page_count(self, path: Path) -> int | None:
        if path.suffix.lower() != ".pdf":
            return 1
        try:
            from pypdf import PdfReader
            return len(PdfReader(str(path)).pages)
        except Exception:
            return None

    def _safe_label(self, value: Any, fallback: str) -> str:
        label = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
        if not label or len(label) > 64:
            return fallback
        tokens = label.split("_")
        if all(token in self.SAFE_LABEL_TOKENS or token == "2067" for token in tokens):
            return label
        return fallback

    def _safe_modeled_field(self, value: Any) -> str:
        label = re.sub(r"[^a-z0-9_]+", "", str(value or "").strip().lower())
        return label if re.fullmatch(r"[a-z][a-z0-9_]{0,63}", label) else ""

    def _safe_label_list(self, value: Any) -> list[str]:
        items = value if isinstance(value, list) else []
        labels = [self._safe_label(item, "") for item in items]
        return list(dict.fromkeys(label for label in labels if label))

    def _safe_category(self, proposed: Any, fallback: Any) -> str:
        allowed = {
            "authorization", "referral", "termination", "denial", "assessment",
            "plan_of_care", "claim", "communication", "form", "2067", "other", "unknown",
        }
        value = str(proposed or fallback or "unknown").strip().lower()
        return value if value in allowed else "unknown"

    def _evidence_status(self, value: Any) -> str:
        status = str(value or "unknown").strip().lower()
        return status if status in self.SAFE_EVIDENCE_STATUSES else "unknown"

    @staticmethod
    def _confidence(value: Any) -> float:
        try:
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _nullable_confidence(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return None
        if normalized < 0 or normalized > 1:
            return None
        return normalized if isfinite(normalized) else None

    @staticmethod
    def _integer(value: Any) -> int:
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    @staticmethod
    def _present(value: Any) -> bool:
        return value is not None and (not isinstance(value, str) or bool(value.strip()))

    @staticmethod
    def _safe_review_status(value: Any) -> str:
        status = str(value or "unknown").strip()
        return status if status in {
            "Verified by AI", "Human Review Required", "Human Review Recommended"
        } else "unknown"

    @staticmethod
    def _deduplicate(items: list[dict[str, Any]], *keys: str) -> list[dict[str, Any]]:
        seen = set()
        results = []
        for item in items:
            marker = tuple(item.get(key) for key in keys)
            if marker in seen:
                continue
            seen.add(marker)
            results.append(item)
        return results
