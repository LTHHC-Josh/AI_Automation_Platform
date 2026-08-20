from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from src.services.filename_policy_service import (
    FilenamePolicyRequest,
    FilenamePolicyService,
)
from src.services.reference_table_service import LookupResult


def resolved(value):
    return LookupResult(True, value, "resolved")


def unresolved(status="not_resolved"):
    return LookupResult(False, None, status)


def request(**changes):
    values = {
        "person_last": "EXAMPLE",
        "person_first": "SYNTHETIC",
        "person_middle": "Q",
        "payer_lookup": resolved("PLAN TOKEN"),
        "service_applicable": True,
        "service_lookup": resolved("SERVICE TOKEN"),
        "document_category": "authorization",
        "document_subtype": "initial",
        "start_date": "2026-01-02",
        "end_date": "2026-02-03",
        "source_extension": ".pdf",
    }
    values.update(changes)
    return FilenamePolicyRequest(**values)


def test_initial_policy_uses_confirmed_order_separators_range_and_no_timestamp():
    result = FilenamePolicyService().resolve(request())
    assert result.complete is True
    assert result.filename == (
        "EXAMPLE SYNTHETIC Q_PLAN TOKEN_SERVICE TOKEN_"
        "AUTH INIT_010226-020326.pdf"
    )
    assert result.status == "resolved"
    assert result.review_required is False
    assert "timestamp" not in result.filename.lower()


def test_payer_reference_token_is_mandatory_and_never_guessed():
    result = FilenamePolicyService().resolve(
        request(payer_lookup=unresolved("ambiguous"))
    )
    assert result.complete is False
    assert result.filename is None
    assert result.status == "payer_reference_unresolved"


def test_service_is_included_only_when_relevant_and_resolved():
    included = FilenamePolicyService().resolve(request())
    omitted = FilenamePolicyService().resolve(
        request(service_applicable=False, service_lookup=None)
    )
    unresolved_service = FilenamePolicyService().resolve(
        request(service_lookup=unresolved("ambiguous"))
    )
    assert "_SERVICE TOKEN_" in included.filename
    assert omitted.complete is True
    assert "SERVICE TOKEN" not in omitted.filename
    assert unresolved_service.complete is False
    assert unresolved_service.status == "service_reference_unresolved"
    assert unresolved_service.review_required is True


def test_2067_form_and_initial_workflow_coexist():
    result = FilenamePolicyService().resolve(request(form_type="2067"))
    assert result.complete is True
    assert "_2067_AUTH INIT_" in result.filename


def test_exactly_one_supported_naming_date_uses_single_date():
    result = FilenamePolicyService().resolve(
        request(start_date=None, end_date=None, naming_dates=("2026-04-05",))
    )
    assert result.complete is True
    assert result.filename.endswith("_040526.pdf")


def test_multiple_single_date_candidates_block_naming():
    result = FilenamePolicyService().resolve(
        request(
            start_date=None,
            end_date=None,
            naming_dates=("2026-04-05", "2026-04-06"),
        )
    )
    assert result.complete is False
    assert result.filename is None
    assert result.status == "date_ownership_unresolved"


def test_invalid_or_missing_supported_date_blocks_naming():
    invalid = FilenamePolicyService().resolve(
        request(start_date="not-a-date", end_date=None)
    )
    missing = FilenamePolicyService().resolve(
        request(start_date=None, end_date=None)
    )
    assert invalid.complete is False
    assert invalid.status == "date_invalid"
    assert missing.complete is False
    assert missing.status == "date_unresolved"


def test_renewal_token_remains_unresolved_and_blocks_final_name():
    result = FilenamePolicyService().resolve(
        request(document_subtype="renewal")
    )
    assert result.complete is False
    assert result.filename is None
    assert result.status == "workflow_token_unresolved"


def test_only_pdf_source_receives_pdf_extension_without_conversion_claim():
    pdf = FilenamePolicyService().resolve(request(source_extension="PDF"))
    other = FilenamePolicyService().resolve(request(source_extension=".tif"))
    assert pdf.complete is True
    assert pdf.filename.endswith(".pdf")
    assert other.complete is False
    assert other.status == "source_extension_unsupported"


def test_phi_bearing_filename_is_hidden_from_result_repr_and_output():
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = FilenamePolicyService().resolve(request())
    assert "EXAMPLE SYNTHETIC" not in repr(result)
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
