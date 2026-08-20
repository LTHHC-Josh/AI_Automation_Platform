from src.services.reference_filename_builder_service import (
    FilenameCompositionPolicy,
    ReferenceFilenameBuilderService,
)


def test_synthetic_components_compose_only_with_explicit_policy():
    service = ReferenceFilenameBuilderService()
    result = service.build(
        person_name="SYNTHETIC PERSON",
        payer_token="SP",
        service_token="T0000U1",
        document_type_token="AUTH TEST",
        date_token="010126",
        policy=FilenameCompositionPolicy(separator="_", extension=".pdf"),
    )
    assert result.success is True
    assert result.filename == "SYNTHETIC PERSON_SP_T0000U1_AUTH TEST_010126.pdf"


def test_unresolved_component_or_policy_blocks_final_name():
    service = ReferenceFilenameBuilderService()
    missing = service.build(
        person_name="SYNTHETIC PERSON", payer_token=None,
        service_token="T0000U1", document_type_token="AUTH TEST", date_token="010126",
        policy=FilenameCompositionPolicy(separator="_", extension=".pdf"),
    )
    unresolved_policy = service.build(
        person_name="SYNTHETIC PERSON", payer_token="SP",
        service_token="T0000U1", document_type_token="AUTH TEST", date_token="010126",
    )
    assert missing.success is False and missing.review_required is True
    assert unresolved_policy.success is False and unresolved_policy.filename is None


def test_form_type_and_optional_workflow_are_independent_components():
    service = ReferenceFilenameBuilderService()
    without_workflow = service.build(
        person_name="SYNTHETIC PERSON",
        payer_token="SP",
        form_type_token="2067",
        workflow_type_token=None,
        date_token="010126",
        policy=FilenameCompositionPolicy(separator="_", extension=".pdf"),
    )
    with_workflow = service.build(
        person_name="SYNTHETIC PERSON",
        payer_token="SP",
        form_type_token="2067",
        workflow_type_token="SUPPORTED WORKFLOW",
        date_token="010126",
        policy=FilenameCompositionPolicy(separator="_", extension=".pdf"),
    )
    assert without_workflow.success is True
    assert without_workflow.filename == "SYNTHETIC PERSON_SP_2067_010126.pdf"
    assert with_workflow.success is True
    assert with_workflow.filename == (
        "SYNTHETIC PERSON_SP_2067_SUPPORTED WORKFLOW_010126.pdf"
    )


def test_supported_qualifier_is_a_separate_optional_component():
    service = ReferenceFilenameBuilderService()
    result = service.build(
        person_name="SYNTHETIC PERSON",
        payer_token="SP",
        workflow_type_token="RENEW AUTH",
        qualifier_token="NO CHANGE",
        date_token="010126-020126",
        policy=FilenameCompositionPolicy(separator="_", extension=".pdf"),
    )
    assert result.success is True
    assert result.filename == (
        "SYNTHETIC PERSON_SP_RENEW AUTH_NO CHANGE_010126-020126.pdf"
    )


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: obviously synthetic person name only")
