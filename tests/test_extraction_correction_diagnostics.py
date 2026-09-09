"""Synthetic/model-mock boundaries only; never read protected documents or call APIs."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as N
import json
import runpy

from src.ai.llm.providers.ollama_provider import OllamaProvider
from src.document_processing.document_processor import DocumentProcessor
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.extraction_shape_diagnostic_service import ExtractionShapeDiagnosticService as Shapes
from src.services.correction_difference_diagnostic_service import CorrectionDifferenceDiagnosticService as Differences
from src.services.review_output_service import ReviewOutputService
from src.services.review_reason_summary_service import ReviewReasonSummaryService
from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService
from src.services.smartsheet_review_configuration_service import APPROVED_DOCUMENT_FIELD_POLICIES

labels = runpy.run_path(str(Path(__file__).with_name("test_explicit_authorization_labels.py")))
correction = runpy.run_path(str(Path(__file__).with_name("test_local_document_correction.py")))


def payload():
    return {"fields": {"intake_document_subtype": {"value": "INITIAL", "confidence": 0.95,
                "source_text": "Type of Authorization: Initial"}},
            "service_lines": [{"service_code": "T0000", "modifier": "U1", "quantity": 8,
                "start_date": None, "end_date": None, "status": None, "confidence": 0.95,
                "source_text": "HCPC Code: T0000\nModifier(s): U1\nQuantity: 8"}]}


def candidate(raw):
    provider = object.__new__(OllamaProvider)
    normalized = {"fields": provider._normalize_fields(raw["fields"]),
                  "service_lines": provider._normalize_service_lines(raw["service_lines"])}
    processor = object.__new__(DocumentProcessor)
    processor.evidence_validation = EvidenceValidationService()
    doc = processor._build_validated_candidate(labels["fixtures"]["authorization"](subtype=None), normalized)
    return doc, normalized


def test_flat_label_candidate_crosses_adapter_validation_and_mapping():
    doc, normalized = candidate(payload())
    assert doc.service_lines[0].service_code == "T0000"
    assert doc.service_lines[0].modifier == "U1"
    assert doc.field_evidence["intake_document_subtype"]["value"] == "init"
    assert doc.processing_metrics["adapter_shapes"] == Shapes.describe(normalized)
    mapped = SmartsheetReviewRowMappingService().map(ReviewOutputService().build(doc),
               list(APPROVED_DOCUMENT_FIELD_POLICIES), run_type="Synthetic")
    assert "Invalid" not in mapped.values["AI Review Reasons"]


def test_provider_records_raw_shape_before_normalization_without_model_call():
    provider = object.__new__(OllamaProvider)
    provider.seed = 42
    provider._last_request_metrics = {}
    raw = payload(); raw["service_lines"][0]["modifier"] = ["U1"]
    provider._chat = lambda **kw: deepcopy(raw)
    provider._approved_correction_guidance = lambda document_type: ""
    result = provider.extract("Synthetic document evidence only.", "authorization")
    assert result["service_lines"][0]["modifier"] == ["U1"]
    metrics = provider.get_last_request_metrics()
    assert metrics["extraction_shapes"] == Shapes.describe(raw)
    assert "T0000" not in json.dumps(metrics) and "U1" not in json.dumps(metrics)


def test_exact_label_and_unproven_excerpt_remain_distinguishable_without_guessing():
    raw = payload()
    raw["fields"]["intake_document_subtype"]["source_text"] = "Type of Authorization:\nInitial"
    assert Shapes.describe(raw)["subtype_evidence_state"] == "resolved"
    raw["fields"]["intake_document_subtype"]["source_text"] += "\nType of Authorization: Renewal"
    assert Shapes.describe(raw)["subtype_evidence_state"] != "resolved"
    assert Shapes.describe(raw)["fields"]["intake_document_subtype"]["source_multiline"]


def test_nested_service_candidate_is_preserved_not_stringified_or_accepted():
    raw = payload()
    raw["service_lines"][0]["service_code"] = {"value": "T0000", "source_text": "PRIVATE_SYNTHETIC"}
    raw["service_lines"][0]["modifier"] = ["U1"]
    doc, normalized = candidate(raw)
    assert isinstance(normalized["service_lines"][0]["service_code"], dict)
    assert doc.service_lines[0].service_code is None and doc.service_lines[0].modifier is None
    assert doc.service_lines[0].candidate_evidence["service_code"] == raw["service_lines"][0]["service_code"]
    assert doc.service_lines[0].candidate_evidence["confidence"] == 0.95
    reasons = ReviewReasonSummaryService().summarize(doc.validation_actions)
    assert "Service-line Service Code: Invalid" in reasons
    assert "Service-line Modifier: Invalid" in reasons
    mapped = SmartsheetReviewRowMappingService().map(ReviewOutputService().build(doc),
               list(APPROVED_DOCUMENT_FIELD_POLICIES), run_type="Synthetic")
    assert mapped.values.get("Service Codes") is None
    assert mapped.values.get("Service Codes Conf.") is None
    assert "PRIVATE_SYNTHETIC" not in json.dumps(Shapes.describe(raw))


def test_all_invalid_line_component_types_fail_closed():
    for field in Shapes.LINE_FIELDS:
        raw = payload(); raw["service_lines"][0][field] = {"value": "PRIVATE_SYNTHETIC"}
        doc, _ = candidate(raw)
        assert doc.service_lines and getattr(doc.service_lines[0], field) is None
        assert any(field.replace("_", " ") + " has invalid structure" in a for a in doc.validation_actions)


def test_invalid_source_container_never_becomes_text_evidence():
    raw = payload(); raw["service_lines"][0]["source_text"] = {"value": "T0000 U1 8"}
    doc, normalized = candidate(raw)
    assert isinstance(normalized["service_lines"][0]["source_text"], dict)
    assert not doc.service_lines
    assert "source_text" in Shapes.describe(raw)["service_lines"][0]["invalid_components"]


def test_subtype_diagnostics_explain_shape_support_and_confidence_separately():
    raw = payload()
    assert Shapes.describe(raw)["subtype_evidence_state"] == "resolved"
    raw["fields"]["intake_document_subtype"]["source_text"] = "Initial visit"
    assert Shapes.describe(raw)["subtype_evidence_state"] == "external_context_required"
    raw["fields"]["intake_document_subtype"]["confidence"] = 0.5
    assert Shapes.describe(raw)["subtype_evidence_state"] == "low_confidence"
    raw["fields"]["intake_document_subtype"]["value"] = {"value": "INITIAL"}
    assert Shapes.describe(raw)["subtype_evidence_state"] == "invalid_structure"


def test_shape_diagnostics_never_stringify_objects():
    class Hostile:
        def __str__(self): raise AssertionError("must not stringify")
        def __repr__(self): raise AssertionError("must not repr")
    raw = payload(); raw["service_lines"][0]["modifier"] = Hostile()
    assert Shapes.describe(raw)["service_lines"][0]["component_types"]["modifier"] == "unsupported"


def test_shape_projection_removes_unknown_fields_and_bounds_retention():
    raw = payload(); raw["service_lines"] *= 70
    diagnostic = Shapes.describe(raw)
    assert diagnostic["service_line_count"] == 70 and diagnostic["omitted_line_count"] == 6
    diagnostic["PRIVATE_KEY"] = "PRIVATE_VALUE"
    diagnostic["fields"]["payer"]["value"] = "PRIVATE_VALUE"
    diagnostic["fields"]["payer"]["source_type"] = "PRIVATE_VALUE"
    safe = Shapes.sanitize(diagnostic)
    assert len(safe["service_lines"]) == 64
    assert "PRIVATE" not in json.dumps(safe)


def difference(current, replay):
    return Differences.build(current, replay, production_columns=set(current.keys()) | set(replay.keys()),
             selected={"Service Codes"}, dependent={"AI Minimum Field Confidence"})


def test_confidence_only_difference_is_exact_and_still_blocked():
    result = difference({"Start Date": "2000-01-01", "Start Date Conf.": 0.95},
                        {"Start Date": "2000-01-01", "Start Date Conf.": 0.90})
    assert result["confidence_only_change_count"] == 1 and result["unrelated_field_count"] == 1
    assert result["fields"][0]["governing_value_changed"] is False
    assert "2000" not in json.dumps(result) and "0.95" not in json.dumps(result)


def test_value_change_is_not_misreported_as_confidence_only():
    result = difference({"Start Date": "2000-01-01", "Start Date Conf.": 0.95},
                        {"Start Date": "2000-02-01", "Start Date Conf.": 0.90})
    assert result["confidence_only_change_count"] == 0 and result["unrelated_field_count"] == 2


def test_unknown_column_names_and_values_cannot_leak():
    result = difference({"PRIVATE_KEY": "PRIVATE_VALUE"}, {})
    assert result["unmapped_changed_field_count"] == 1
    assert result["unrelated_field_count"] == 1 and not result["fields"]
    assert "PRIVATE" not in json.dumps(result)


def test_ignored_human_feedback_and_dependent_fields_do_not_block():
    result = difference({"AI Correction": True, "AI Minimum Field Confidence": 0.95},
                        {"AI Correction": False, "AI Minimum Field Confidence": 0.90})
    assert result["unrelated_field_count"] == 0


def test_executor_saves_exact_differences_before_guard_without_writes():
    h = correction["AdapterHarness"]()
    h.context["AI Document Category"] = "2067"
    try: h.plan()
    except ValueError as error: assert str(error) == "correction_unrelated_field_change"
    else: raise AssertionError("guard bypassed")
    records = list(h.executor.source.store.data.values())
    assert len(records) == 2
    assert any(r["field"] == "AI Document Category" and r["blocked"] for r in records[0]["fields"])
    assert h.calls == 0 and h.values[h.ids["AI Correction"]] is True


def test_attempt_shapes_are_retained_independently_before_mapping_failure():
    h = correction["AdapterHarness"](); doc, _ = candidate(payload())
    one = Shapes.describe(payload()); raw = payload(); raw["service_lines"][0]["modifier"] = ["U1"]
    two = Shapes.describe(raw)
    doc.processing_metrics.update(extraction_selected_attempt=2, extraction_attempts=[
        {"attempt":1,"ollama":{"extraction_shapes":one,"PRIVATE":"PRIVATE"},"adapter_shapes":one},
        {"attempt":2,"ollama":{"extraction_shapes":two},"adapter_shapes":two}])
    h.executor.processor_factory = lambda: N(process=lambda *a, **kw: doc)
    h.executor.configuration = N(resolve=lambda **kw:N(success=False))
    try: h.plan()
    except ValueError as error: assert str(error) == "correction_schema_unavailable"
    safe = next(iter(h.executor.source.store.data.values()))
    assert safe["selected_attempt"] == 2 and len(safe["extraction_shapes"]) == 2
    assert safe["extraction_shapes"][0]["model"] != safe["extraction_shapes"][1]["model"]
    assert "PRIVATE" not in json.dumps(safe)


if __name__ == "__main__":
    tests = [v for k,v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try: test()
        except Exception as error:
            failed += 1; print("FAIL:", test.__name__, type(error).__name__)
    print("Passed:", len(tests)-failed); print("Failed:", failed)
    print("Classification: synthetic/mock; no external operations")
    raise SystemExit(bool(failed))
