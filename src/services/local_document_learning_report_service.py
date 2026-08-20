from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Iterable

from src.models.document import Document


class LocalDocumentLearningReportService:
    """Build a value-free structural report from one processed document."""

    SAFE_LABEL_TOKENS = {
        "annual", "approval", "approved", "assessment", "authorization",
        "business", "change", "claim", "communication", "contact",
        "continuation", "date", "denial", "direction", "document", "due",
        "effective", "end", "extension", "field", "form", "inbound",
        "initial", "locate", "missing", "modifier", "no", "notice",
        "outbound", "past", "posted", "purpose", "quantity", "reach",
        "referral", "renewal", "request", "requested", "review", "service",
        "start", "status", "termination", "to", "unable", "units", "unknown",
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
        schema_gaps = self._safe_schema_gaps(safe_analysis.get("schema_gaps"))
        service_structure = self._service_structure(document, safe_analysis)
        review = self._review_structure(document, field_inventory, concepts)
        structure = safe_analysis.get("document_structure")
        structure = structure if isinstance(structure, dict) else {}

        return {
            "document_structure": {
                "document_form_type": self._safe_label(
                    structure.get("document_form_type"), "unknown"
                ),
                "document_category": self._safe_category(
                    structure.get("document_category"),
                    document.document_category,
                ),
                "purpose_concepts": self._safe_label_list(
                    structure.get("purpose_concepts")
                ),
                "direction_context": self._safe_label_list(
                    structure.get("direction_context")
                ),
                "page_count": self._page_count(document.file_path),
                "analysis_basis": "local_model_structural_analysis",
            },
            "field_inventory": field_inventory,
            "date_structure": date_inventory,
            "authorization_service_structure": service_structure,
            "business_concepts": concepts,
            "schema_gaps": schema_gaps,
            "review_quality": review,
            "development_implications": self._development_implications(
                structure=structure,
                concepts=concepts,
                schema_gaps=schema_gaps,
                dates=date_inventory,
            ),
            "protected_values_suppressed": True,
        }

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
            "plan_of_care", "claim", "communication", "form", "other", "unknown",
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
