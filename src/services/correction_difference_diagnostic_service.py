"""Exact correction comparison, projected to approved field names without values."""
from src.services.extraction_shape_diagnostic_service import ExtractionShapeDiagnosticService
from src.services.smartsheet_review_configuration_service import APPROVED_DOCUMENT_FIELD_POLICIES
from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService


class CorrectionDifferenceDiagnosticService:
    @staticmethod
    def build(current, replay, *, production_columns, selected, dependent):
        pairs = {p.confidence_column_name: p.column_name
                 for p in APPROVED_DOCUMENT_FIELD_POLICIES if p.confidence_column_name}
        pairs["AI Classification Confidence"] = "AI Document Category"
        value_names = {p.column_name for p in APPROVED_DOCUMENT_FIELD_POLICIES}
        allowed = value_names | set(pairs) | set(SmartsheetReviewRowMappingService.OPERATIONAL_METADATA_COLUMNS)
        ignored = {"AI Correction", "Run Type"}
        records = []
        # Only static, code-approved labels can enter output. Never emit keys
        # received from runtime configuration, row data, or model output.
        for name in sorted(allowed):
            if name not in production_columns or current.get(name) == replay.get(name):
                continue
            governing = pairs.get(name)
            records.append({
                "field": name,
                "kind": "confidence" if governing else "value" if name in value_names else "metadata",
                "current_type": ExtractionShapeDiagnosticService.kind(current.get(name)),
                "replay_type": ExtractionShapeDiagnosticService.kind(replay.get(name)),
                "current_present": current.get(name) is not None,
                "replay_present": replay.get(name) is not None,
                "requested": name in selected,
                "dependent": name in dependent,
                "ignored": name in ignored,
                "blocked": bool(selected) and name not in selected | dependent | ignored,
                "governing_value_changed": (current.get(governing) != replay.get(governing)) if governing else None,
            })
        unknown_count = sum(current.get(n) != replay.get(n) for n in production_columns - allowed)
        return {"version": 1, "fields": records, "changed_field_count": len(records) + unknown_count,
                "unmapped_changed_field_count": unknown_count,
                "unrelated_field_count": sum(bool(selected) and n not in selected | dependent | ignored
                                             and current.get(n) != replay.get(n) for n in production_columns),
                "confidence_only_change_count": sum(r["kind"] == "confidence" and r["governing_value_changed"] is False
                                                    for r in records)}
