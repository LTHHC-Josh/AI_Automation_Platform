"""Synthetic scoped-row confidence/recovery checks; no model or live API calls."""
from copy import deepcopy
from pathlib import Path
import json
import runpy

from src.services.correction_row_projection_service import CorrectionRowProjectionService as Projection
from src.services.smartsheet_review_configuration_service import APPROVED_DOCUMENT_FIELD_POLICIES as POLICIES
from src.services.review_output_service import ReviewField

fixtures = runpy.run_path(str(Path(__file__).with_name("test_local_document_correction.py")))
diagnostics = runpy.run_path(str(Path(__file__).with_name("test_extraction_correction_diagnostics.py")))


def project(current, replay, selected=None):
    return Projection.project(current, replay, policies=POLICIES,
                              selected=selected if selected is not None else {"AI Document Subtype"})


def pair(confidence=0.95):
    return {"Start Date":"2000-01-01", "Start Date Conf.":confidence}


def test_actual_five_unrelated_confidence_differences_are_reproduced():
    names = ("authorization_number", "days_per_week", "end_date", "hours", "start_date")
    current, replay = {}, {}
    for policy in POLICIES:
        if policy.source_field in names:
            current[policy.column_name] = replay[policy.column_name] = "synthetic"
            current[policy.confidence_column_name] = 0.95
            replay[policy.confidence_column_name] = 0.90
    original = deepcopy(replay)
    result, preserved, protected = project(current, replay)
    assert len(preserved) == 5 and len(protected) == 10
    assert all(result[n] == current[n] for n in preserved)
    assert result["AI Minimum Field Confidence"] == 0.95
    assert replay == original


def test_requested_confidence_uses_selected_candidate_not_existing_score():
    result, preserved, _ = project(pair(), pair(0.90), {"Start Date", "Start Date Conf."})
    assert result["Start Date Conf."] == 0.90 and not preserved


def test_changed_value_is_never_preserved_or_invented():
    replay = pair(0.90); replay["Start Date"] = "2001-01-01"
    result, preserved, _ = project(pair(), replay)
    assert result == replay and not preserved


def test_absent_or_unsupported_value_never_restored():
    for replay in ({}, {"Start Date":None, "Start Date Conf.":None}):
        result, preserved, _ = project(pair(), replay)
        assert result == replay and not preserved


def test_invalid_or_below_threshold_confidence_cannot_bypass_guard():
    for score in (None, False, True, "0.95", [], {}, float("nan"), float("inf"), 0.84, 0.96, 1.0):
        assert not project(pair(score), pair(0.90))[1]
        assert not project(pair(), pair(score))[1]


def test_existing_inclusive_thresholds_are_used():
    assert project(pair(0.85), pair(0.95))[0]["Start Date Conf."] == 0.85
    assert project(pair(0.95), pair(0.85))[0]["Start Date Conf."] == 0.95


def test_minimum_uses_displayed_pairs_not_classification_or_absent_scores():
    current = dict(pair(), **{"AI Classification Confidence":0.70})
    replay = dict(pair(0.90), **{"AI Classification Confidence":0.70,
        "Service Codes":"T0000", "Service Codes Conf.":0.85,
        "End Date":None, "End Date Conf.":None})
    result, _, _ = project(current, replay, {"Service Codes", "Service Codes Conf."})
    assert result["AI Minimum Field Confidence"] == 0.85
    assert result["AI Classification Confidence"] == 0.70


def test_classification_and_unknown_columns_do_not_get_exemptions():
    current = {"AI Document Category":"authorization", "AI Classification Confidence":0.95,
               "Private Column":0.95}
    replay = dict(current, **{"AI Classification Confidence":0.90, "Private Column":0.90})
    assert project(current, replay)[0] == replay and not project(current, replay)[1]


def test_empty_correction_scope_does_not_change_projection():
    result, preserved, protected = project(pair(), pair(0.90), set())
    assert result == pair(0.90) and not preserved and not protected


def harness():
    h = fixtures["AdapterHarness"]()
    h.review.fields.append(ReviewField(name="start_date", value="2000-01-01", confidence=0.90))
    h.context.update(pair())
    for name, value in pair().items(): h.values[h.ids[name]] = value
    return h


def test_executor_preserves_unrequested_pair_and_guards_it_during_apply():
    h = harness(); plan = h.plan()
    assert "Start Date" not in plan["updates"] and "Start Date Conf." not in plan["updates"]
    assert plan["before"]["Start Date Conf."] == 0.95
    assert plan["updates"]["AI Minimum Field Confidence"] == 0.95
    h.executor.apply(1, plan); h.executor.resume(1, plan)
    assert h.calls == 1 and h.executor.verify(1, plan)
    assert h.values[h.ids["Start Date Conf."]] == 0.95
    assert h.values[h.ids["AI Correction"]] is True


def test_fresh_readback_change_blocks_preparation():
    h = harness(); h.values[h.ids["Start Date Conf."]] = 0.85
    try: h.plan()
    except ValueError as error: assert str(error) == "correction_row_changed"
    else: raise AssertionError("concurrent edit ignored")
    assert h.calls == 0


def test_changed_preserved_pair_blocks_apply_and_restart():
    for field, value in (("Start Date", "2001-01-01"), ("Start Date Conf.",0.85)):
        h = harness(); plan = h.plan(); h.values[h.ids[field]] = value
        try: h.executor.resume(1, plan)
        except ValueError as error: assert str(error) == "correction_row_changed"
        else: raise AssertionError("concurrent edit overwritten")
        assert h.calls == 0


def test_genuine_unrelated_value_or_confidence_failure_still_blocks():
    for change in ("value", "confidence"):
        h = harness()
        if change == "value": h.context["Start Date"] = "2001-01-01"
        else: h.context["Start Date Conf."] = 0.5
        try: h.plan()
        except ValueError as error: assert str(error) == "correction_unrelated_field_change"
        else: raise AssertionError("unrelated change allowed")
        assert h.calls == 0


def test_projection_audit_contains_counts_only():
    h = harness(); h.plan()
    audit = h.executor.source.store.load("audit", "preparation-differences:" + "a"*64)["projection"]
    assert audit == {"version":1, "preserved_confidence_count":1, "remaining_unrelated_field_count":0}
    assert "2000" not in json.dumps(audit)


def test_real_failure_shape_reproduced_without_relaxing_service_validation():
    raw = diagnostics["payload"]()
    raw["fields"]["intake_document_subtype"] = {
        "value":"unspecified choice", "confidence":0.80, "source_text":"Synthetic evidence"}
    line = raw["service_lines"][0]
    line.update(modifier="U1, U2", confidence=0.90, source_text="Quantity: 8")
    raw["service_lines"].append(dict(line, service_code="T0001", quantity=9, source_text="Quantity: 9"))
    doc, _ = diagnostics["candidate"](raw)
    assert len(doc.service_lines) == 2
    for result in doc.service_lines:
        assert result.service_code is None and result.modifier is None
        assert result.candidate_evidence["service_code"] in ("T0000", "T0001")
    from src.services.intake_document_naming_service import IntakeDocumentNamingVocabulary
    assert IntakeDocumentNamingVocabulary.resolve(doc).subtype_key == "unknown"


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
