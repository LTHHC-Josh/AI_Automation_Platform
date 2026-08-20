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


def test_2067_form_and_supported_workflow_coexist():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            workflow_lookup=resolved("INBOUND AUTH"),
            document_category="formal_communication",
            document_subtype=None,
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert result.complete is True
    assert "_2067_INBOUND AUTH_040526.pdf" in result.filename


def test_2067_accepts_explicitly_supported_inbound_auth_workflow():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            workflow_lookup=resolved("INBOUND AUTH"),
            document_category="formal_communication",
            document_subtype=None,
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert result.complete is True
    assert "_2067_INBOUND AUTH_" in result.filename


def test_2067_accepts_explicitly_supported_init_workflow():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            workflow_lookup=resolved("INIT"),
            document_category="formal_communication",
            document_subtype=None,
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert result.complete is True
    assert "_2067_INIT_" in result.filename


def test_2067_without_supported_workflow_omits_it_without_guessing():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            workflow_lookup=None,
            document_category="formal_communication",
            document_subtype=None,
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert result.complete is True
    assert "_2067_" in result.filename
    assert "AUTH INIT" not in result.filename
    assert "INBOUND AUTH" not in result.filename
    assert "INIT" not in result.filename


def test_2067_accepts_future_supported_workflow_without_fixed_choice_list():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            workflow_lookup=resolved("FUTURE SUPPORTED WORKFLOW"),
            document_category="formal_communication",
            document_subtype=None,
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert result.complete is True
    assert "_2067_FUTURE SUPPORTED WORKFLOW_" in result.filename


def test_2067_rejects_unresolved_workflow_instead_of_guessing():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            workflow_lookup=unresolved("ambiguous"),
            document_category="formal_communication",
            document_subtype=None,
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert result.complete is False
    assert result.filename is None
    assert result.status == "workflow_token_unresolved"


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


def test_actual_authorization_renewal_uses_confirmed_token():
    result = FilenamePolicyService().resolve(
        request(document_subtype="renewal")
    )
    assert result.complete is True
    assert "_RENEW AUTH_" in result.filename
    assert "INBOUND AUTH" not in result.filename


def test_authorization_renewal_does_not_inherit_inbound_auth_workflow():
    result = FilenamePolicyService().resolve(
        request(
            form_type=None,
            workflow_lookup=resolved("INBOUND AUTH"),
            document_category="authorization",
            document_subtype="renewal",
        )
    )
    assert result.complete is True
    assert "_RENEW AUTH_" in result.filename
    assert "INBOUND AUTH" not in result.filename


def test_supported_no_change_qualifier_coexists_without_inferring_renewal():
    renewal = FilenamePolicyService().resolve(
        request(
            document_subtype="renewal",
            qualifier_lookup=resolved("NO CHANGE"),
        )
    )
    qualifier_only = FilenamePolicyService().resolve(
        request(
            document_category="authorization",
            document_subtype="initial",
            workflow_lookup=None,
            qualifier_lookup=resolved("NO CHANGE"),
        )
    )
    assert "_RENEW AUTH_NO CHANGE_" in renewal.filename
    assert qualifier_only.complete is False
    assert qualifier_only.filename is None
    assert qualifier_only.status == "qualifier_not_applicable"


def test_missing_qualifier_is_omitted_and_unresolved_qualifier_blocks_naming():
    missing = FilenamePolicyService().resolve(
        request(document_subtype="renewal", qualifier_lookup=None)
    )
    unresolved_qualifier = FilenamePolicyService().resolve(
        request(
            document_subtype="renewal",
            qualifier_lookup=unresolved("unsupported"),
        )
    )
    assert "NO CHANGE" not in missing.filename
    assert unresolved_qualifier.complete is False
    assert unresolved_qualifier.status == "qualifier_token_unresolved"


def test_2067_never_infers_init_without_supported_external_context():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            document_category="formal_communication",
            document_subtype="initial",
            workflow_lookup=None,
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert result.complete is True
    assert "_2067_040526.pdf" in result.filename
    assert "INIT" not in result.filename


def test_2067_accepts_future_database_supported_workflow_refinement():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            document_category="formal_communication",
            document_subtype=None,
            workflow_lookup=resolved("FUTURE DATABASE WORKFLOW"),
            posted_date_lookup=resolved("2026-04-05"),
        )
    )
    assert "_2067_FUTURE DATABASE WORKFLOW_" in result.filename


def test_2067_uses_only_supported_posted_date():
    result = FilenamePolicyService().resolve(
        request(
            form_type="2067",
            document_category="formal_communication",
            document_subtype=None,
            workflow_lookup=resolved("INBOUND AUTH"),
            posted_date_lookup=resolved("2026-04-05"),
            start_date="2026-01-02",
            end_date="2026-02-03",
            naming_dates=("2026-06-07",),
        )
    )
    assert result.filename.endswith("_040526.pdf")
    assert "010226" not in result.filename
    assert "020326" not in result.filename
    assert "060726" not in result.filename


def test_2067_missing_unsupported_conflicting_or_invalid_posted_date_blocks():
    changes = (
        {"posted_date_lookup": None},
        {"posted_date_lookup": unresolved("unsupported")},
        {"posted_date_lookup": unresolved("conflicting")},
        {"posted_date_lookup": resolved("not-a-date")},
    )
    results = [
        FilenamePolicyService().resolve(
            request(
                form_type="2067",
                document_category="formal_communication",
                document_subtype=None,
                workflow_lookup=resolved("INBOUND AUTH"),
                **change,
            )
        )
        for change in changes
    ]
    assert all(not result.complete for result in results)
    assert [result.status for result in results] == [
        "posted_date_unresolved",
        "posted_date_unresolved",
        "posted_date_unresolved",
        "posted_date_invalid",
    ]


def test_document_type_and_workflow_are_separate_request_dimensions():
    policy_fields = FilenamePolicyRequest.__dataclass_fields__
    assert "form_type" in policy_fields
    assert "workflow_lookup" in policy_fields
    assert "qualifier_lookup" in policy_fields
    assert "posted_date_lookup" in policy_fields
    assert policy_fields["form_type"] is not policy_fields["workflow_lookup"]


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
