from pathlib import Path

from src.ai.llm.providers.ollama_provider import OllamaProvider
from src.models.document import Document
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.filename_policy_service import (
    FilenamePolicyRequest,
    FilenamePolicyService,
)
from src.services.filename_validated_input_service import (
    FilenameValidatedInputService,
)
from src.services.reference_table_service import LookupResult


def resolved(value):
    return LookupResult(True, value, "resolved")


def unresolved(status="unresolved"):
    return LookupResult(False, None, status)


def document(*, category="other", subtype="unknown", evidence=None):
    result = Document(
        file_path=Path("synthetic-filename-input.pdf"),
        document_category=category,
        document_subtype=subtype,
    )
    result.field_evidence = evidence or {}
    result.validation_actions = EvidenceValidationService().validate(result)
    return result


def policy_request(inputs, **changes):
    values = {
        "person_last": "EXAMPLE",
        "person_first": "SYNTHETIC",
        "payer_lookup": resolved("PLAN TOKEN"),
        "service_applicable": False,
        "form_type": "2067",
        "workflow_lookup": inputs.workflow_context.lookup,
        "document_category": "formal_communication",
        "document_subtype": None,
        "posted_date_lookup": inputs.posted_date.lookup,
        "start_date": "2026-01-02",
        "end_date": "2026-02-03",
    }
    values.update(changes)
    return FilenamePolicyRequest(**values)


def test_supported_posted_date_preserves_complete_evidence_boundary():
    source_text = "Posted Date: 04/05/2026"
    extracted = object.__new__(OllamaProvider)._normalize_fields(
        {
            "posted_date": {
                "value": "04/05/2026",
                "confidence": 0.91,
                "source_text": source_text,
            }
        }
    )
    subject = document(evidence=extracted)
    inputs = FilenameValidatedInputService().resolve(
        subject,
        form_type="2067",
        workflow_context=resolved("INBOUND AUTH"),
    )
    assert subject.extracted_data["posted_date"] == "2026-04-05"
    assert inputs.posted_date.lookup.value == "2026-04-05"
    assert inputs.posted_date.confidence == 0.91
    assert inputs.posted_date.source_text == source_text
    assert inputs.review_required is False
    assert source_text not in repr(inputs)
    assert "2026-04-05" not in repr(inputs)


def test_missing_posted_date_remains_unknown_and_requires_review():
    subject = document()
    inputs = FilenameValidatedInputService().resolve(
        subject,
        form_type="2067",
        workflow_context=resolved("INBOUND AUTH"),
    )
    assert inputs.posted_date.lookup.resolved is False
    assert inputs.posted_date.lookup.value is None
    assert inputs.posted_date.lookup.status == "missing"
    assert inputs.review_required is True


def test_conflicting_posted_date_is_cleared_and_review_safe():
    source_text = "Posted Date: 04/05/2026; Posted Date: 04/06/2026"
    subject = document(
        evidence={
            "posted_date": {
                "value": ["04/05/2026", "04/06/2026"],
                "confidence": 0.90,
                "source_text": source_text,
            }
        }
    )
    inputs = FilenameValidatedInputService().resolve(
        subject,
        form_type="2067",
        workflow_context=resolved("INBOUND AUTH"),
    )
    assert subject.extracted_data["posted_date"] is None
    assert inputs.posted_date.lookup.resolved is False
    assert inputs.posted_date.lookup.status == "conflicting"
    assert inputs.posted_date.source_text == source_text
    assert inputs.review_required is True


def test_2067_policy_consumes_only_boundary_posted_date():
    subject = document(
        evidence={
            "posted_date": {
                "value": "04/05/2026",
                "confidence": 0.90,
                "source_text": "Posted Date: 04/05/2026",
            }
        }
    )
    inputs = FilenameValidatedInputService().resolve(
        subject,
        form_type="2067",
        workflow_context=resolved("INBOUND AUTH"),
    )
    result = FilenamePolicyService().resolve(policy_request(inputs))
    assert result.complete is True
    assert result.filename.endswith("_040526.pdf")
    assert "010226" not in result.filename
    assert "020326" not in result.filename


def test_explicit_workflow_context_survives_separately_from_2067():
    subject = document(category="authorization", subtype="initial")
    inputs = FilenameValidatedInputService().resolve(
        subject,
        form_type="2067",
        workflow_context=resolved("INBOUND AUTH"),
    )
    assert inputs.workflow_context.lookup.resolved is True
    assert inputs.workflow_context.lookup.value == "INBOUND AUTH"
    assert inputs.workflow_context.lookup.value != subject.document_subtype


def test_missing_or_unsupported_workflow_context_is_never_guessed():
    subject = document(category="authorization", subtype="initial")
    missing = FilenameValidatedInputService().resolve(
        subject,
        form_type="2067",
        workflow_context=None,
    )
    unsupported_context = FilenameValidatedInputService().resolve(
        subject,
        form_type="2067",
        workflow_context=unresolved("unsupported"),
    )
    assert missing.workflow_context.lookup.status == "missing"
    assert unsupported_context.workflow_context.lookup.status == "unsupported"
    assert missing.workflow_context.lookup.value is None
    assert unsupported_context.workflow_context.lookup.value is None
    assert missing.review_required is True
    assert unsupported_context.review_required is True


def test_supported_no_change_preserves_evidence_without_inferring_renewal():
    source_text = "Renewal Qualifier: NO CHANGE"
    renewal = document(
        category="authorization",
        subtype="renewal",
        evidence={
            "renewal_qualifier": {
                "value": "no change",
                "confidence": 0.89,
                "source_text": source_text,
            }
        },
    )
    inputs = FilenameValidatedInputService().resolve(
        renewal,
        qualifier_reference=resolved("NO CHANGE"),
    )
    assert inputs.renewal_qualifier.lookup.resolved is True
    assert inputs.renewal_qualifier.lookup.value == "NO CHANGE"
    assert inputs.renewal_qualifier.confidence == 0.89
    assert inputs.renewal_qualifier.source_text == source_text
    assert source_text not in repr(inputs)
    assert "NO CHANGE" not in repr(inputs)

    initial = document(
        category="authorization",
        subtype="initial",
        evidence={
            "renewal_qualifier": {
                "value": "NO CHANGE",
                "confidence": 0.89,
                "source_text": source_text,
            }
        },
    )
    rejected = FilenameValidatedInputService().resolve(
        initial,
        qualifier_reference=resolved("NO CHANGE"),
    )
    assert rejected.renewal_qualifier.lookup.resolved is False
    assert rejected.renewal_qualifier.lookup.status == "not_applicable"
    assert initial.document_subtype == "initial"


def test_qualifier_ambiguity_and_generic_wording_remain_review_safe():
    ambiguous = document(
        category="authorization",
        subtype="renewal",
        evidence={
            "renewal_qualifier": {
                "value": ["NO CHANGE", "OTHER"],
                "confidence": 0.90,
                "source_text": (
                    "Renewal Qualifier: NO CHANGE; Renewal Qualifier: OTHER"
                ),
            }
        },
    )
    ambiguous_inputs = FilenameValidatedInputService().resolve(
        ambiguous,
        qualifier_reference=unresolved("ambiguous"),
    )
    assert ambiguous.extracted_data["renewal_qualifier"] is None
    assert ambiguous_inputs.renewal_qualifier.lookup.status == "conflicting"
    assert ambiguous_inputs.review_required is True

    generic = document(
        category="authorization",
        subtype="renewal",
        evidence={
            "renewal_qualifier": {
                "value": "NO CHANGE",
                "confidence": 0.90,
                "source_text": "Authorized hours appear unchanged.",
            }
        },
    )
    generic_inputs = FilenameValidatedInputService().resolve(
        generic,
        qualifier_reference=resolved("NO CHANGE"),
    )
    assert generic.extracted_data["renewal_qualifier"] is None
    assert generic_inputs.renewal_qualifier.lookup.status == "unsupported"
    assert generic_inputs.review_required is True


def test_boundary_is_not_connected_to_production_filename_callers():
    import src.services.document_attachment_naming_service as attachment_module

    assert not hasattr(attachment_module, "FilenameValidatedInputService")


if __name__ == "__main__":
    tests = [
        value
        for name, value in list(globals().items())
        if name.startswith("test_")
    ]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic evidence only; evidence values are not printed")
