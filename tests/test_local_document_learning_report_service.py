import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models.document import AuthorizationServiceLine, Document


PROTECTED_MARKER = "PROTECTED_SYNTHETIC_LEARNING_MARKER"


def build_document(path: Path) -> Document:
    document = Document(
        file_path=path,
        document_category="other",
        document_subtype="unknown",
        confidence=0.72,
        raw_text=PROTECTED_MARKER,
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
        "document_structure", "field_inventory", "date_structure",
        "authorization_service_structure", "business_concepts",
        "schema_gaps", "review_quality", "development_implications",
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
