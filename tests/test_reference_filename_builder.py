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


def test_document_type_is_one_canonical_component():
    service = ReferenceFilenameBuilderService()
    result = service.build(
        person_name="SYNTHETIC PERSON",
        payer_token="SP",
        document_type_token="2067",
        date_token="010126",
        policy=FilenameCompositionPolicy(separator="_", extension=".pdf"),
    )
    assert result.success is True
    assert result.filename == "SYNTHETIC PERSON_SP_2067_010126.pdf"


def test_fixed_placeholder_is_safe_as_a_document_type_component():
    service = ReferenceFilenameBuilderService()
    result = service.build(
        person_name="SYNTHETIC PERSON",
        payer_token="SP",
        document_type_token="AUTH [SUBTYPE]",
        date_token="010126-020126",
        policy=FilenameCompositionPolicy(separator="_", extension=".pdf"),
    )
    assert result.success is True
    assert result.filename == (
        "SYNTHETIC PERSON_SP_AUTH [SUBTYPE]_010126-020126.pdf"
    )


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: obviously synthetic person name only")
