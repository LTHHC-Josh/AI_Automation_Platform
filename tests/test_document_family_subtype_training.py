from pathlib import Path

from src.models.document import Document
from src.models.learning_document_evidence import LearningDocumentEvidence
from src.models.ocr_document import OCRBlock, OCRDocument, OCRPage
from src.services.deterministic_document_concept_service import (
    DeterministicDocumentConceptService,
)
from src.services.document_classification_resolution_service import (
    DocumentClassificationResolutionService,
)
from src.services.learning_evidence_grounding_service import (
    LearningEvidenceGroundingService,
)
from src.services.local_document_learning_report_service import (
    LocalDocumentLearningReportService,
)
from src.ai.llm.providers.ollama_provider import OllamaProvider
from src.models.document_taxonomy import DocumentTaxonomyRegistry
from src.services.review_decision_service import ReviewDecisionService


def ocr_document(*pages: tuple[str, ...]) -> OCRDocument:
    reading_order = 0
    output_pages = []
    for page_number, texts in enumerate(pages, start=1):
        blocks = []
        for block_number, text in enumerate(texts, start=1):
            reading_order += 1
            blocks.append(OCRBlock(
                block_id=f"page_{page_number}_block_{block_number}",
                text=text,
                reading_order=reading_order,
                confidence=0.82,
            ))
        output_pages.append(OCRPage(page_number=page_number, blocks=tuple(blocks)))
    return OCRDocument(pages=tuple(output_pages), relationship_status="preserved")


def resolve(document, category="2067", subtype="unknown"):
    concepts = DeterministicDocumentConceptService().analyze(document)
    result = DocumentClassificationResolutionService().resolve(
        {
            "document_category": category,
            "document_subtype": subtype,
            "confidence": 0.84,
            "reason": "Synthetic supported reason.",
        },
        concepts,
    )
    return result, concepts


def test_compact_aliases_ground_to_exact_internal_evidence():
    evidence = LearningDocumentEvidence.build(
        ocr_document(("Synthetic first block.",), ("Synthetic second block.",))
    )
    assert evidence.model_references == ("e0001", "e0002")
    prompt = evidence.to_local_prompt()
    assert 'ref="e0001"' in prompt
    assert "page_1_block_1" not in prompt

    result = LearningEvidenceGroundingService().resolve({
        "coverage": {
            "analyzed_page_refs": [1, 2],
            "complete_document_analyzed": True,
        },
        "observations": [{"evidence_refs": ["e0001", "e0002"]}],
        "contradictions": [],
    }, evidence)
    assert result.valid_reference_count == 2
    assert result.analysis["observations"][0]["evidence_refs"] == [
        "page_1_block_1", "page_2_block_1"
    ]


def test_invalid_and_duplicate_model_references_are_safely_counted():
    evidence = LearningDocumentEvidence.build(ocr_document(("Synthetic block.",)))
    result = LearningEvidenceGroundingService().resolve({
        "observations": [{
            "evidence_refs": ["e0001", "e0001", "e9999", "not a ref"]
        }],
    }, evidence)
    assert result.valid_reference_count == 1
    assert result.duplicate_reference_count == 1
    assert result.unsupported_reference_count == 1
    assert result.malformed_reference_count == 1
    assert "e9999" not in repr(result.analysis)


def test_learning_schema_restricts_references_to_request_aliases():
    evidence = LearningDocumentEvidence.build(ocr_document(("Synthetic block.",)))
    provider = OllamaProvider.__new__(OllamaProvider)
    schema = provider._learning_schema(evidence)
    observation_refs = schema["properties"]["observations"]["items"][
        "properties"
    ]["evidence_refs"]["items"]
    page_refs = schema["properties"]["coverage"]["properties"][
        "analyzed_page_refs"
    ]["items"]
    assert observation_refs["enum"] == ["e0001"]
    assert page_refs["enum"] == [1]


def test_clear_2067_contact_failure_without_literal_utl_resolves_utl():
    document = ocr_document(
        ("Form No. 2067", "Annual review information."),
        ("The team was unable to reach the member after an attempted call.",),
    )
    result, concepts = resolve(document)
    assert result["document_category"] == "2067"
    assert result["document_subtype"] == "utl"
    assert result["subtype_support_status"] == "supported"
    assert "UTL" not in document.raw_text
    assert {item.concept_name for item in concepts} == {
        "form_2067", "contact_failure"
    }


def test_standalone_2067_evidence_overrides_conflicting_legacy_family():
    document = ocr_document((
        "2067",
        "The team was unable to reach the member after an attempted call.",
    ))
    result, concepts = resolve(document, category="plan_of_care")
    assert {item.concept_name for item in concepts} == {
        "form_2067", "contact_failure"
    }
    assert result["document_category"] == "2067"
    assert result["document_subtype"] == "utl"
    assert result["document_type"] == "2067"


def test_bounded_prefixed_and_hyphenated_2067_form_marker_resolves_family():
    document = ocr_document((
        "A2067-ZZ",
        "The team was unable to reach the member after an attempted call.",
    ))
    result, concepts = resolve(document, category="plan_of_care")
    assert any(item.concept_name == "form_2067" for item in concepts)
    assert result["document_category"] == "2067"
    assert result["document_subtype"] == "utl"


def test_unbounded_or_digit_embedded_2067_numbers_are_not_form_markers():
    for marker in (
        "12067",
        "20670",
        "AB2067-ZZ",
        "A2067-ZZZZZZZZZ",
    ):
        result, concepts = resolve(
            ocr_document((marker,)), category="plan_of_care"
        )
        assert all(item.concept_name != "form_2067" for item in concepts)
        assert result["document_category"] == "plan_of_care"
        assert result["document_subtype"] == "unknown"


def test_varied_and_repeated_contact_failure_wording_preserves_repetition():
    document = ocr_document(
        ("2067 Form", "The member did not answer the attempted telephone call."),
        ("Prior calls failed and staff cannot reach the client.",),
    )
    result, concepts = resolve(document)
    contact = next(item for item in concepts if item.concept_name == "contact_failure")
    assert result["document_subtype"] == "utl"
    assert contact.support_occurrence_count == 2


def test_nearby_blocks_can_jointly_support_family_and_contact_concept():
    document = ocr_document((
        "Form Number",
        "2067",
        "Staff were unable to reach",
        "the member after attempted calls.",
    ))
    result, concepts = resolve(document)
    contact = next(item for item in concepts if item.concept_name == "contact_failure")
    assert result["document_category"] == "2067"
    assert result["document_subtype"] == "utl"
    assert contact.support_occurrence_count == 1


def test_2067_annual_only_and_plain_2067_keep_subtype_unknown():
    for document in (
        ocr_document(("Form 2067", "Annual review is due.")),
        ocr_document(("Form 2067", "Routine information.")),
    ):
        result, _ = resolve(document, subtype="utl")
        assert result["document_category"] == "2067"
        assert result["document_subtype"] == "unknown"
        assert result["subtype_support_status"] == "missing"


def test_conflicting_contact_evidence_keeps_subtype_unknown_and_reviewable():
    document = ocr_document((
        "Form 2067",
        "The team was unable to reach the member after an attempted call.",
        "The team successfully contacted the member.",
    ))
    result, concepts = resolve(document)
    contact = next(item for item in concepts if item.concept_name == "contact_failure")
    assert contact.support_status == "conflicting"
    assert result["document_subtype"] == "unknown"
    assert result["subtype_support_status"] == "conflicting"


def test_positive_contact_wording_is_preserved_as_separate_evidence():
    variants = (
        "The member answered the call.",
        "The member was successfully contacted.",
        "Contact was established.",
        "The client was reached successfully.",
    )
    for wording in variants:
        result, concepts = resolve(ocr_document(("Form 2067", wording)))
        concept_map = {item.concept_name: item for item in concepts}
        assert concept_map["contact_success"].support_status == "supported"
        assert concept_map["contact_failure"].support_status == "unsupported"
        assert result["document_subtype"] == "unknown"


def test_failure_plus_positive_contact_wording_is_mixed_and_not_utl():
    variants = (
        "The member answered the call.",
        "The member was successfully contacted.",
        "Contact was established.",
        "The client was reached successfully.",
    )
    for wording in variants:
        document = ocr_document((
            "Form 2067",
            "The team was unable to reach the member after an attempted call.",
            wording,
        ))
        result, concepts = resolve(document)
        concept_map = {item.concept_name: item for item in concepts}
        assert concept_map["contact_failure"].support_status == "conflicting"
        assert concept_map["contact_success"].support_status == "supported"
        assert result["document_subtype"] == "unknown"
        assert result["subtype_support_status"] == "conflicting"
        decision = ReviewDecisionService().evaluate(Document(
            file_path=Path("synthetic.pdf"),
            document_type=result["document_type"],
            document_category=result["document_category"],
            document_subtype=result["document_subtype"],
            classification_support_status=result["classification_support_status"],
            subtype_support_status=result["subtype_support_status"],
            confidence=0.84,
        ))
        assert decision.needs_human_review is True


def test_clear_contact_failure_still_resolves_utl_without_literal_token():
    document = ocr_document((
        "Form 2067",
        "The team was unable to reach the member after an attempted call.",
    ))
    result, _ = resolve(document)
    assert result["document_subtype"] == "utl"
    assert "UTL" not in document.raw_text


def test_contact_failure_without_2067_never_creates_utl():
    result, _ = resolve(
        ocr_document(("Unable to reach the member after a call.",)),
        category="authorization",
        subtype="utl",
    )
    assert result["document_category"] == "authorization"
    assert result["document_subtype"] == "unknown"


def test_taxonomy_preserves_authorization_legacy_routes_and_separate_dimensions():
    assert DocumentTaxonomyRegistry.normalize_subtype(
        "authorization", "renewal"
    ) == "renewal"
    assert DocumentTaxonomyRegistry.legacy_route(
        "authorization", "renewal"
    ) == "authorization_renewal"
    assert DocumentTaxonomyRegistry.normalize_subtype("2067", "utl") == "utl"
    assert DocumentTaxonomyRegistry.normalize_subtype(
        "authorization", "utl"
    ) == "unknown"


def test_supported_family_with_unknown_2067_subtype_routes_to_review():
    document = Document(
        file_path=Path("synthetic.pdf"),
        document_type="2067",
        document_category="2067",
        document_subtype="unknown",
        classification_reason="Synthetic supported reason.",
        confidence=0.91,
        extracted_data={"posted_date": "synthetic-present"},
        field_confidences={"posted_date": 0.91},
    )
    decision = ReviewDecisionService().evaluate(document)
    assert decision.needs_human_review is True
    assert decision.review_status == "Human Review Required"


def test_clear_utl_taxonomy_does_not_create_subtype_review():
    document = Document(
        file_path=Path("synthetic.pdf"),
        document_type="2067",
        document_category="2067",
        document_subtype="utl",
        classification_reason="Synthetic supported reason.",
        confidence=0.91,
        classification_support_status="supported",
        subtype_support_status="supported",
        extracted_data={"modeled_field": "synthetic-present"},
        field_confidences={"modeled_field": 0.91},
    )
    decision = ReviewDecisionService().evaluate(document)
    assert decision.needs_human_review is False
    assert all("2067 subtype" not in reason for reason in decision.reasons)


def test_unknown_family_cannot_be_supported_or_confident_in_report():
    document = Document(
        file_path=Path("synthetic.pdf"),
        document_category="unknown",
        document_subtype="unknown",
        classification_support_status="supported",
        subtype_support_status="supported",
        family_evidence_confidence=1.0,
        subtype_evidence_confidence=1.0,
    )
    report = LocalDocumentLearningReportService().build(document, {})
    for dimension in ("family", "subtype"):
        result = report["classification"][dimension]
        assert result["label"] == "unknown"
        assert result["support_status"] == "unknown"
        assert result["confidence"] is None
        assert result["evidence_reference_count"] == 0
        assert result["review_required"] is True


def test_supported_legacy_family_label_remains_visible_in_report():
    document = Document(
        file_path=Path("synthetic.pdf"),
        document_category="plan_of_care",
        document_subtype="unknown",
        classification_support_status="supported",
        family_evidence_confidence=0.88,
    )
    report = LocalDocumentLearningReportService().build(document, {})
    family = report["classification"]["family"]
    assert family["label"] == "plan_of_care"
    assert family["support_status"] == "supported"
    assert family["confidence"] == 0.88


def test_report_keeps_deterministic_and_model_observations_separate():
    protected_marker = "SYNTHETIC_PROTECTED_MARKER"
    ocr = ocr_document(("Form 2067",), (
        "The team was unable to reach the member after an attempted call.",
    ))
    result, concepts = resolve(ocr)
    document = Document(
        file_path=Path("synthetic.pdf"),
        raw_text=protected_marker,
        ocr_document=ocr,
        document_category=result["document_category"],
        document_subtype=result["document_subtype"],
        classification_support_status=result["classification_support_status"],
        subtype_support_status=result["subtype_support_status"],
        deterministic_concepts=concepts,
        confidence=0.84,
    )
    report = LocalDocumentLearningReportService().build(document, {
        "coverage": {
            "analyzed_page_refs": [1, 2],
            "complete_document_analyzed": True,
        },
        "observations": [{
            "observation_kind": "business_concept",
            "normalized_label": "contact_failure",
            "proposed_category": "business",
            "evidence_refs": ["page_2_block_1"],
            "evidence_status": "supported",
            "confidence": 0.71,
            "repetition_count": 1,
            "current_modeled_field": None,
        }],
    })
    assert report["report_schema_version"] == 3
    assert report["classification"]["family"]["label"] == "2067"
    assert report["classification"]["subtype"]["label"] == "utl"
    assert report["deterministic_concepts"][1]["deterministically_validated"] is True
    assert report["observations"][0]["deterministically_validated"] is False
    assert protected_marker not in repr(report)
    assert "page_2_block_1" not in repr(report)
