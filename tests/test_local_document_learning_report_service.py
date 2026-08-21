import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models.document import AuthorizationServiceLine, Document
from src.models.ocr_document import OCRBlock, OCRDocument, OCRPage


PROTECTED_MARKER = "PROTECTED_SYNTHETIC_LEARNING_MARKER"


def build_document(path: Path) -> Document:
    document = Document(
        file_path=path,
        document_category="other",
        document_subtype="unknown",
        confidence=0.72,
        raw_text=PROTECTED_MARKER,
    )
    document.ocr_document = OCRDocument(
        pages=(
            OCRPage(page_number=1, blocks=(
                OCRBlock(
                    block_id="page_1_block_1",
                    text=PROTECTED_MARKER,
                    reading_order=1,
                    block_type="header",
                ),
            )),
            OCRPage(page_number=2, blocks=(
                OCRBlock(
                    block_id="page_2_block_1",
                    text=PROTECTED_MARKER,
                    reading_order=2,
                    block_type="text",
                ),
            )),
        ),
        relationship_status="preserved",
    )
    document.field_evidence = {
        "posted_date": {
            "value": PROTECTED_MARKER,
            "confidence": 0.82,
            "source_text": PROTECTED_MARKER,
        },
        "modifier": {
            "value": None,
            "confidence": 0.0,
            "source_text": "",
        },
    }
    document.extracted_data = {
        "posted_date": PROTECTED_MARKER,
        "modifier": None,
    }
    document.field_confidences = {
        "posted_date": 0.82,
        "modifier": 0.0,
    }
    document.service_lines = [
        AuthorizationServiceLine(
            service_code=PROTECTED_MARKER,
            quantity=1,
            confidence=0.8,
            source_text=PROTECTED_MARKER,
        )
    ]
    document.validation_actions = [
        "posted_date is not supported by its source evidence",
    ]
    document.needs_human_review = True
    document.review_status = "Human Review Required"
    document.review_reasons = ["posted_date requires review"]
    document.processing_metrics = {
        "extraction_attempt_count": 2,
        "extraction_selected_attempt": 2,
        "extraction_retry_triggered": True,
    }
    return document


def structural_analysis():
    return {
        "document_structure": {
            "document_form_type": "communication_form",
            "document_category": "communication",
            "purpose_concepts": ["unable_to_locate", PROTECTED_MARKER],
            "direction_context": ["inbound", PROTECTED_MARKER],
        },
        "date_fields": [
            {
                "field_name": "posted_date",
                "semantic_role": "posted",
                "evidence_status": "supported",
            },
            {
                "field_name": PROTECTED_MARKER,
                "semantic_role": "communication",
                "evidence_status": "tentative",
            },
        ],
        "authorization_service_structure": {
            "authorization_concepts_present": True,
            "quantity_concepts_present": True,
            "units_concepts_present": False,
            "visits_concepts_present": False,
            "approval_concepts_present": False,
            "request_concepts_present": True,
        },
        "business_concepts": [
            {
                "concept_label": "unable_to_locate",
                "explicitly_supported": True,
                "evidence_status": "supported",
                "current_modeled_field": False,
            },
            {
                "concept_label": PROTECTED_MARKER,
                "explicitly_supported": True,
                "evidence_status": "supported",
                "current_modeled_field": False,
            },
        ],
        "schema_gaps": [
            {
                "candidate_name": "workflow_status",
                "structural_type": "status",
                "evidence_status": "supported",
            },
            {
                "candidate_name": PROTECTED_MARKER,
                "structural_type": "text",
                "evidence_status": "supported",
            },
        ],
        "coverage": {
            "analyzed_evidence_refs": ["page_1_block_1", "page_2_block_1"],
            "complete_document_analyzed": True,
        },
        "observations": [
            {
                "observation_id": "modeled",
                "observation_kind": "modeled_field",
                "normalized_label": "posted_date",
                "proposed_category": "date",
                "evidence_refs": ["page_1_block_1", "page_2_block_1"],
                "evidence_status": "conflicting",
                "confidence": 0.61,
                "repetition_count": 2,
                "current_modeled_field": "posted_date",
                "production_rule_status": "not_mapped",
                "deterministically_validated": False,
            },
            {
                "observation_id": PROTECTED_MARKER,
                "observation_kind": "business_concept",
                "normalized_label": "contact_failure",
                "proposed_category": "business",
                "evidence_refs": ["page_1_block_1", "page_2_block_1"],
                "evidence_status": "supported",
                "confidence": 0.74,
                "repetition_count": 2,
                "current_modeled_field": None,
                "production_rule_status": "not_mapped",
                "deterministically_validated": False,
            },
            {
                "observation_id": "unsafe",
                "observation_kind": "schema_gap",
                "normalized_label": PROTECTED_MARKER,
                "proposed_category": "field",
                "evidence_refs": ["missing_block"],
                "evidence_status": "supported",
                "confidence": None,
                "repetition_count": 1,
                "current_modeled_field": None,
                "production_rule_status": "not_mapped",
                "deterministically_validated": False,
            },
        ],
        "contradictions": [
            {
                "contradiction_type": "service_status",
                "evidence_refs": ["page_1_block_1", "page_2_block_1"],
                "evidence_status": "conflicting",
            },
        ],
    }


def test_report_is_comprehensive_and_contains_no_protected_values():
    from src.services.local_document_learning_report_service import (
        LocalDocumentLearningReportService,
    )

    with TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.png"
        path.write_bytes(b"synthetic")
        report = LocalDocumentLearningReportService().build(
            build_document(path),
            structural_analysis(),
            modeled_field_names=("posted_date", "modifier"),
        )

    assert set(report) == {
        "report_schema_version", "whole_document_coverage",
        "document_structure", "field_inventory", "date_structure",
        "authorization_service_structure", "business_concepts",
        "schema_gaps", "observations", "novel_observations",
        "contradictions", "review_quality", "development_implications",
        "protected_values_suppressed",
    }
    rendered = repr(report)
    assert PROTECTED_MARKER not in rendered
    assert "synthetic.png" not in rendered
    assert report["protected_values_suppressed"] is True
    assert {item["field_name"] for item in report["field_inventory"]} == {
        "posted_date", "modifier"
    }
    assert report["field_inventory"][0]["support_status"] == "unsupported"
    assert report["authorization_service_structure"]["service_line_count"] == 1
    assert report["review_quality"]["selected_attempt"] == 2
    assert report["whole_document_coverage"]["coverage_status"] == "complete"
    assert report["whole_document_coverage"]["page_count"] == 2
    assert report["field_inventory"][0]["learning_discovery_status"] == "conflicting"
    assert report["observations"][0]["normalized_concept"] is None
    assert report["observations"][1]["normalized_concept"] == "contact_failure"
    assert report["observations"][1]["production_rule_status"] == "not_mapped"
    assert report["observations"][2]["normalized_concept"] is None
    assert report["observations"][2]["evidence_status"] == "unsupported"
    assert report["observations"][2]["confidence"] is None


def test_unknown_model_labels_are_withheld_without_losing_gap_signal():
    from src.services.local_document_learning_report_service import (
        LocalDocumentLearningReportService,
    )

    with TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.png"
        path.write_bytes(b"synthetic")
        report = LocalDocumentLearningReportService().build(
            build_document(path),
            structural_analysis(),
            modeled_field_names=("posted_date",),
        )

    assert "unmodeled_business_concept" in {
        item["concept_label"] for item in report["business_concepts"]
    }
    assert "unmodeled_field" in {
        item["candidate_name"] for item in report["schema_gaps"]
    }
    assert "unmodeled_date_field" in {
        item["field_name"] for item in report["date_structure"]
    }


def test_existing_evaluator_opt_in_reuses_selected_processed_document():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
        LocalEvaluationExecutionClassification,
    )

    calls = []

    class Processor:
        def __init__(self, document):
            self.document = document

        def process(self, path, *, ocr_cache_only=False):
            calls.append((path, ocr_cache_only))
            return self.document

    with TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "synthetic.png"
        path.write_bytes(b"synthetic")
        document = build_document(path)
        processor = Processor(document)
        service = LocalDocumentEvaluationService(
            document_directory=root,
            processor_factory=lambda: processor,
            selection_snapshot_path=root / "selection.json",
            execution_classification=LocalEvaluationExecutionClassification.SYNTHETIC_MOCK,
            learning_analysis_factory=lambda supplied, _: (
                structural_analysis() if supplied is document else None
            ),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = service.evaluate(
                document_index=1,
                run_type="Synthetic Learning",
                authorize_cached_ocr_access=True,
                authorize_local_ollama=True,
                include_learning_report=True,
            )

    assert calls == [(path, True)]
    assert result.success is True
    assert result.learning_report_requested is True
    assert result.learning_report_status == "completed"
    assert result.learning_report is not None
    assert PROTECTED_MARKER not in repr(result)
    assert PROTECTED_MARKER not in repr(result.to_safe_dict())
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""


def test_learning_failure_is_sanitized():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    class Processor:
        def __init__(self, document):
            self.document = document

        def process(self, path, *, ocr_cache_only=False):
            return self.document

    with TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "synthetic.pdf"
        path.write_bytes(b"synthetic")
        service = LocalDocumentEvaluationService(
            document_directory=root,
            processor_factory=lambda: Processor(build_document(path)),
            selection_snapshot_path=root / "selection.json",
            learning_analysis_factory=lambda *_: (_ for _ in ()).throw(
                RuntimeError(PROTECTED_MARKER)
            ),
        )
        result = service.evaluate(
            document_index=1,
            run_type="Synthetic Learning",
            authorize_cached_ocr_access=True,
            authorize_local_ollama=True,
            include_learning_report=True,
        )

    assert result.success is False
    assert result.failure_category == "learning_analysis_failed"
    assert result.learning_report_status == "failed"
    assert PROTECTED_MARKER not in repr(result)


def test_default_learning_path_receives_structured_complete_document_envelope():
    from src.models.learning_document_evidence import LearningDocumentEvidence
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    captured = []

    class LearningLLM:
        provider = type("Provider", (), {"FIELD_NAMES": ("posted_date",)})()

        def analyze_learning_structure(self, evidence):
            captured.append(evidence)
            return structural_analysis()

    class Processor:
        llm = LearningLLM()

        def __init__(self, document):
            self.document = document

        def process(self, path, *, ocr_cache_only=False):
            return self.document

    with TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "synthetic.pdf"
        path.write_bytes(b"synthetic")
        service = LocalDocumentEvaluationService(
            document_directory=root,
            processor_factory=lambda: Processor(build_document(path)),
            selection_snapshot_path=root / "selection.json",
        )
        result = service.evaluate(
            document_index=1,
            run_type="Synthetic Learning",
            authorize_cached_ocr_access=True,
            authorize_local_ollama=True,
            include_learning_report=True,
        )

    assert result.success is True
    assert len(captured) == 1
    assert isinstance(captured[0], LearningDocumentEvidence)
    assert captured[0].evidence_ids == {
        "page_1_block_1", "page_2_block_1"
    }
