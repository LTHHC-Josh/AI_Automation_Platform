from dataclasses import asdict, replace
import json

from src.ai.llm.providers.ollama_provider import OllamaProvider
from src.models.document_processor_business_context import (
    BUSINESS_CONTEXT_VERSION,
    DOCUMENT_PROCESSOR_BUSINESS_CONTEXT,
)
from src.models.document_taxonomy import DocumentTaxonomyRegistry
from src.services.document_processor_business_context_service import (
    BUSINESS_CONTEXT_SEMANTIC_DIGESTS,
    CONTEXT_ROLES,
    DocumentProcessorBusinessContextService,
)
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.field_validation_diagnostic_service import (
    FieldValidationDiagnosticService,
    FieldValidationState,
)
from src.services.filename_policy_service import FilenamePolicyService
from src.services.intake_document_naming_service import IntakeDocumentNamingVocabulary
from src.services.review_decision_service import ReviewDecisionService


def test_shared_context_is_valid_deterministic_and_phi_free():
    service = DocumentProcessorBusinessContextService()
    assert service.context.business_context_version == BUSINESS_CONTEXT_VERSION == 1
    assert service.digest(service.context) == BUSINESS_CONTEXT_SEMANTIC_DIGESTS[1]
    serialized = json.dumps(asdict(service.context), sort_keys=True).lower()
    for prohibited in (
        "patient_value", "member_value", "row_id", "sheet_id", "comment_text",
        "source_text", "document_path", "attachment_name", "request_payload",
    ):
        assert prohibited not in serialized


def test_every_existing_local_model_role_has_a_bounded_context_view():
    service = DocumentProcessorBusinessContextService()
    views = {role: service.view(role) for role in CONTEXT_ROLES}
    assert set(views) == {
        "classification", "extraction", "intake_naming_subtype",
        "dp_training_correction", "structural_learning",
    }
    assert all(view.business_context_version == 1 for view in views.values())
    assert views["dp_training_correction"].rendered_character_count <= 4096
    assert "AUTH INIT" in views["extraction"].rendered_text
    assert "AUTH DECREASE" in views["extraction"].rendered_text
    assert "COMMENTS" in views["dp_training_correction"].rendered_text.upper()


def test_semantic_change_requires_a_new_version_and_registered_digest():
    changed = replace(
        DOCUMENT_PROCESSOR_BUSINESS_CONTEXT,
        filename_outcomes=("changed_without_version",),
    )
    try:
        DocumentProcessorBusinessContextService(changed)
        raise AssertionError("unversioned semantic context change was accepted")
    except ValueError as error:
        assert str(error) == "business_context_version_digest_mismatch"


def test_deterministic_facades_use_shared_taxonomy_and_policy_values():
    context = DOCUMENT_PROCESSOR_BUSINESS_CONTEXT
    assert DocumentTaxonomyRegistry.families() == tuple(
        item.family for item in context.document_taxonomy
    )
    assert IntakeDocumentNamingVocabulary.TOP_LEVEL_TOKENS == dict(
        context.top_level_naming_tokens
    )
    assert {
        item.key: (item.token, item.requires_external_context)
        for item in IntakeDocumentNamingVocabulary.AUTHORIZATION_SUBTYPES
    } == {
        item.key: (item.token, item.requires_external_context)
        for item in context.intake_subtype_taxonomy
    }
    placeholders = dict(context.placeholder_policy)
    assert FilenamePolicyService.PAYER_PLACEHOLDER == placeholders["payer"]
    assert FilenamePolicyService.SERVICE_PLACEHOLDER == placeholders["service"]
    assert tuple(item.value for item in FieldValidationState) == tuple(
        name for name, _ in context.field_state_semantics
    )
    assert FieldValidationDiagnosticService.DEFAULT_ACCEPTANCE_THRESHOLD == (
        context.confidence_policy.field_acceptance
    )
    assert ReviewDecisionService.FIELD_CONFIDENCE_THRESHOLD == (
        context.confidence_policy.field_acceptance
    )
    assert EvidenceValidationService.AUTHORIZATION_UNIT_CANONICAL == {
        alias: canonical
        for canonical, aliases in context.quantity_unit_policy.supported_units
        for alias in aliases
    }


def test_live_prompts_include_role_and_version_without_model_contact():
    provider = object.__new__(OllamaProvider)
    prompts = {
        "classification": provider._classification_prompt(),
        "extraction": provider._extraction_prompt(),
        "structural_learning": provider._learning_analysis_prompt(),
    }
    for role, prompt in prompts.items():
        assert "DOCUMENT PROCESSOR BUSINESS CONTEXT v1" in prompt
        assert f"ROLE: {role}" in prompt
    assert "AUTH INIT" in prompts["extraction"]
    assert "external" in prompts["extraction"].lower()
    assert "sender/source" in prompts["classification"].lower()
    assert len(prompts["classification"]) <= 5000
    assert len(prompts["extraction"]) <= 10000
    assert len(prompts["structural_learning"]) <= 3500

    provider._last_request_metrics = {}
    provider._attach_context_metrics("classification")
    assert provider._last_request_metrics == {
        "business_context_version": BUSINESS_CONTEXT_VERSION,
        "business_context_role": "classification",
        "business_context_character_count": service_character_count(
            "classification"
        ),
    }


def service_character_count(role):
    return DocumentProcessorBusinessContextService().view(
        role
    ).rendered_character_count


if __name__ == "__main__":
    tests = [value for name, value in tuple(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/mock")
    print("External integrations: not called")
    print("PHI handling: static PHI-free context only")
