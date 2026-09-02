from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from src.services.filename_policy_service import FilenamePolicyRequest, FilenamePolicyService
from src.services.intake_document_naming_service import IntakeDocumentTypeResolution
from src.services.reference_table_service import LookupResult


def resolved(value):
    return LookupResult(True, value, "resolved")


def unresolved(status="not_resolved"):
    return LookupResult(False, None, status)


def document_type(segment="AUTH NO CHANGE", *, subtype_status="Ready"):
    return IntakeDocumentTypeResolution(
        segment,
        "Ready",
        subtype_key="no_change" if subtype_status == "Ready" else "unknown",
        subtype_display="NO CHANGE" if subtype_status == "Ready" else "unknown",
        subtype_status=subtype_status,
        subtype_source_category=(
            "explicit_document_evidence" if subtype_status == "Ready" else "unresolved"
        ),
    )


def request(**changes):
    values = {
        "person_last": "EXAMPLE",
        "person_first": "SYNTHETIC",
        "person_middle": "Q",
        "payer_lookup": resolved("PLAN TOKEN"),
        "service_applicable": True,
        "service_lookup": resolved("SERVICE TOKEN"),
        "document_type_resolution": document_type(),
        "start_date": "2026-01-02",
        "end_date": "2026-02-03",
        "source_extension": ".pdf",
    }
    values.update(changes)
    return FilenamePolicyRequest(**values)


def test_complete_policy_matches_intake_order_comma_range_and_extension():
    result = FilenamePolicyService().resolve(request())
    assert result.filename == (
        "EXAMPLE, SYNTHETIC Q_PLAN TOKEN_SERVICE TOKEN_"
        "AUTH NO CHANGE_010226-020326.PDF"
    )
    assert result.complete is True
    assert result.filename_result == "complete_business"
    assert result.review_required is False


def test_payer_unresolved_uses_fixed_placeholder_without_guessing():
    result = FilenamePolicyService().resolve(
        request(payer_lookup=unresolved("ambiguous"))
    )
    assert result.complete is True
    assert "_[PAYER]_" in result.filename
    assert result.filename_result == "partial_business"
    assert result.placeholder_categories == ("payer",)


def test_service_resolved_omitted_and_expected_unresolved_are_distinct():
    included = FilenamePolicyService().resolve(request())
    omitted = FilenamePolicyService().resolve(
        request(service_applicable=False, service_lookup=None)
    )
    placeholder = FilenamePolicyService().resolve(
        request(service_applicable=True, service_lookup=unresolved("ambiguous"))
    )
    assert "_SERVICE TOKEN_" in included.filename
    assert "SERVICE TOKEN" not in omitted.filename
    assert "[SERVICE]" not in omitted.filename
    assert "_[SERVICE]_" in placeholder.filename


def test_unknown_authorization_subtype_uses_placeholder():
    result = FilenamePolicyService().resolve(
        request(document_type_resolution=document_type("AUTH [SUBTYPE]", subtype_status="Placeholder"))
    )
    assert "AUTH [SUBTYPE]" in result.filename
    assert result.placeholder_categories == ("document_subtype",)


def test_2067_is_one_document_type_segment_and_legacy_workflow_is_ignored():
    result = FilenamePolicyService().resolve(
        request(
            document_type_resolution=IntakeDocumentTypeResolution("2067", "Ready"),
            form_type="2067",
            workflow_lookup=resolved("INBOUND AUTH"),
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert "_2067_040526.PDF" in result.filename
    assert "INBOUND AUTH" not in result.filename


def test_single_supported_date_and_range_are_supported():
    single = FilenamePolicyService().resolve(
        request(start_date=None, end_date=None, naming_dates=("2026-04-05",))
    )
    date_range = FilenamePolicyService().resolve(request())
    assert single.filename.endswith("_040526.PDF")
    assert date_range.filename.endswith("_010226-020326.PDF")


def test_reversed_date_range_uses_placeholder_without_technical_fallback():
    result = FilenamePolicyService().resolve(
        request(start_date="2026-02-03", end_date="2026-01-02")
    )
    assert result.filename_result == "partial_business"
    assert result.placeholder_categories == ("date",)
    assert result.filename.endswith("_[DATE].PDF")


def test_missing_invalid_or_ambiguous_date_uses_date_placeholder():
    missing = FilenamePolicyService().resolve(
        request(start_date=None, end_date=None)
    )
    invalid = FilenamePolicyService().resolve(
        request(start_date="not-a-date", end_date=None)
    )
    ambiguous = FilenamePolicyService().resolve(
        request(start_date=None, end_date=None, naming_dates=("2026-04-05", "2026-04-06"))
    )
    for result in (missing, invalid, ambiguous):
        assert result.filename.endswith("_[DATE].PDF")
        assert "date" in result.placeholder_categories


def test_optional_middle_service_and_end_date_are_omitted():
    result = FilenamePolicyService().resolve(
        request(
            person_middle=None,
            service_applicable=False,
            service_lookup=None,
            end_date=None,
        )
    )
    assert result.filename == (
        "EXAMPLE, SYNTHETIC_PLAN TOKEN_AUTH NO CHANGE_010226.PDF"
    )
    assert result.optional_omission_count == 3


def test_person_and_extension_are_technical_fallback_boundaries():
    person = FilenamePolicyService().resolve(request(person_first=None))
    extension = FilenamePolicyService().resolve(request(source_extension=".doc"))
    assert person.filename_result == "technical_fallback"
    assert person.status == "person_name_unresolved"
    assert extension.filename_result == "technical_fallback"
    assert extension.status == "source_extension_unsupported"


def test_safe_source_extensions_are_preserved_as_canonical_business_suffixes():
    pdf = FilenamePolicyService().resolve(request(source_extension="PDF"))
    tif = FilenamePolicyService().resolve(request(source_extension=".tif"))
    assert pdf.filename.endswith(".PDF")
    assert tif.filename.endswith(".TIF")


def test_phi_bearing_filename_is_hidden_from_result_repr_and_output():
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = FilenamePolicyService().resolve(request())
    assert "EXAMPLE" not in repr(result)
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic names only; resolved filename is not printed")
