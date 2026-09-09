"""Value-free, bounded structure diagnostics. Never stringify model data."""
from math import isfinite


class ExtractionShapeDiagnosticService:
    VERSION = 1
    MAX_CAPTURED_LINES = 64  # Diagnostic retention only; not an extraction limit.
    FIELDS = ("intake_document_subtype", "payer", "service_code", "service_codes",
              "modifier", "start_date", "end_date", "authorized_units")
    LINE_FIELDS = ("service_code", "modifier", "quantity", "start_date", "end_date", "status")
    TYPES = frozenset({"null", "text", "boolean", "number", "nonfinite_number", "object", "array", "unsupported"})
    SUBTYPE_STATES = frozenset({"not_present", "low_confidence", "unsupported", "external_context_required", "resolved", "invalid_structure"})

    @classmethod
    def subtype_state(cls, evidence):
        # Run the existing deterministic contract, never a model or source scan.
        if type(evidence) is not dict:
            return "not_present" if evidence is None else "invalid_structure"
        if (cls.kind(evidence.get("value")) not in {"text", "null"}
                or cls.kind(evidence.get("source_text")) not in {"text", "null"}
                or cls.kind(evidence.get("confidence")) not in {"number", "null"}):
            return "invalid_structure"
        from src.services.intake_document_naming_service import IntakeDocumentNamingVocabulary
        _, state = IntakeDocumentNamingVocabulary.validate_document_evidence(evidence)
        return state if state in cls.SUBTYPE_STATES else "unsupported"

    @staticmethod
    def kind(value):
        if value is None: return "null"
        if type(value) is str: return "text"
        if type(value) is bool: return "boolean"
        if type(value) in (int, float):
            return "number" if type(value) is int or isfinite(value) else "nonfinite_number"
        if type(value) is dict: return "object"
        if type(value) is list: return "array"
        return "unsupported"

    @classmethod
    def invalid_line_fields(cls, row):
        invalid = []
        for name in cls.LINE_FIELDS:
            allowed = {"null", "text", "number"} if name == "quantity" else {"null", "text"}
            if cls.kind(row.get(name)) not in allowed:
                invalid.append(name)
        if cls.kind(row.get("source_text")) != "text": invalid.append("source_text")
        return invalid

    @classmethod
    def field(cls, item):
        item_type = cls.kind(item)
        evidence = item if type(item) is dict else {}
        source = evidence.get("source_text")
        return {
            "evidence_type": item_type,
            "value_type": cls.kind(evidence.get("value")),
            "confidence_type": cls.kind(evidence.get("confidence")),
            "source_type": cls.kind(source),
            "source_nonempty": type(source) is str and bool(source.strip()),
            "source_multiline": type(source) is str and len(source.splitlines()) > 1,
        }

    @classmethod
    def describe(cls, payload):
        payload = payload if type(payload) is dict else {}
        fields = payload.get("fields")
        fields = fields if type(fields) is dict else {}
        lines = payload.get("service_lines")
        items = lines if type(lines) is list else []
        records = []
        for index, item in enumerate(items[:cls.MAX_CAPTURED_LINES]):
            row = item if type(item) is dict else {}
            records.append({
                "line_number": index + 1,
                "row_type": cls.kind(item),
                "component_types": {name: cls.kind(row.get(name)) for name in cls.LINE_FIELDS},
                "source_type": cls.kind(row.get("source_text")),
                "confidence_type": cls.kind(row.get("confidence")),
                "invalid_components": cls.invalid_line_fields(row),
            })
        return {"version": cls.VERSION,
                "subtype_evidence_state": cls.subtype_state(fields.get("intake_document_subtype")),
                "fields": {name: cls.field(fields.get(name)) for name in cls.FIELDS},
                "service_lines_type": cls.kind(lines), "service_line_count": len(items),
                "omitted_line_count": max(0, len(items) - cls.MAX_CAPTURED_LINES),
                "service_lines": records}

    @classmethod
    def sanitize(cls, diagnostic):
        """Project stored/provider diagnostics again before audit; never trust extras."""
        if type(diagnostic) is not dict or diagnostic.get("version") != cls.VERSION:
            return None
        def count(value): return value if type(value) is int and value >= 0 else 0
        def kind(value): return value if type(value) is str and value in cls.TYPES else "unsupported"
        fields = diagnostic.get("fields")
        fields = fields if type(fields) is dict else {}
        safe_fields = {}
        for name in cls.FIELDS:
            item = fields.get(name)
            item = item if type(item) is dict else {}
            safe_fields[name] = {k:kind(item.get(k)) for k in ("evidence_type", "value_type", "confidence_type", "source_type")}
            safe_fields[name].update({k:item.get(k) is True for k in ("source_nonempty", "source_multiline")})
        rows = diagnostic.get("service_lines")
        rows = rows if type(rows) is list else []
        safe_rows = []
        for row in rows[:cls.MAX_CAPTURED_LINES]:
            if type(row) is not dict: continue
            components = row.get("component_types")
            components = components if type(components) is dict else {}
            invalid = row.get("invalid_components")
            invalid = invalid if type(invalid) is list else []
            safe_rows.append({"line_number":count(row.get("line_number")),
                "row_type":kind(row.get("row_type")),
                "component_types":{n:kind(components.get(n)) for n in cls.LINE_FIELDS},
                "source_type":kind(row.get("source_type")), "confidence_type":kind(row.get("confidence_type")),
                "invalid_components":[n for n in (*cls.LINE_FIELDS, "source_text") if n in invalid]})
        return {"version":cls.VERSION, "fields":safe_fields,
            "subtype_evidence_state": (diagnostic.get("subtype_evidence_state")
                if type(diagnostic.get("subtype_evidence_state")) is str
                and diagnostic.get("subtype_evidence_state") in cls.SUBTYPE_STATES else "invalid_structure"),
            "service_lines_type":kind(diagnostic.get("service_lines_type")),
            "service_line_count":count(diagnostic.get("service_line_count")),
            "omitted_line_count":count(diagnostic.get("omitted_line_count")), "service_lines":safe_rows}
