from src.services.contact_failure_normalization_service import (
    ContactFailureNormalizationService,
)


def normalize(source_text, confidence=0.81):
    return ContactFailureNormalizationService().normalize(
        source_text=source_text,
        confidence=confidence,
    )


def test_clear_inability_reaching_member_supports_contact_failure():
    source = "The team was unable to reach the member after an attempted call."
    result = normalize(source)

    assert result.value == "contact_failure"
    assert result.supported is True
    assert result.review_required is False
    assert result.confidence == 0.81
    assert result.source_text == source


def test_supported_request_to_contact_member_normalizes_without_literal_utl():
    source = "Please contact the member because prior call attempts were unsuccessful."
    result = normalize(source, confidence=0.73)

    assert result.value == "contact_failure"
    assert result.confidence == 0.73
    assert "UTL" not in source
    assert "utl" not in result.value


def test_contact_evidence_and_conditional_service_consequence_share_concept():
    source = (
        "The coordinator cannot reach the member. "
        "If contact cannot be completed, services may be terminated."
    )
    result = normalize(source)

    assert result.value == "contact_failure"
    assert result.status == "supported_with_service_consequence"


def test_consequence_without_contact_evidence_remains_unknown():
    result = normalize("If required information is missing, services may be delayed.")

    assert result.value is None
    assert result.supported is False
    assert result.review_required is True
    assert result.status == "unknown"


def test_annual_due_and_literal_utl_do_not_imply_contact_failure_or_utl_mapping():
    for source in (
        "The annual review is due.",
        "The case is past due.",
        "UTL",
        "Form 2067 Posted Date",
    ):
        result = normalize(source)
        assert result.value is None
        assert result.review_required is True


def test_general_communication_does_not_over_trigger():
    for source in (
        "The member requested a routine communication.",
        "Please call the member about available services.",
        "A contact number is listed for the member.",
    ):
        result = normalize(source)
        assert result.value is None
        assert result.supported is False
        assert result.review_required is True


def test_missing_response_wording_is_supported_and_evidence_survives():
    source = "The member did not answer the attempted telephone call."
    result = normalize(source, confidence=0.64)

    assert result.value == "contact_failure"
    assert result.confidence == 0.64
    assert result.source_text == source
    assert "source_text" not in repr(result)
