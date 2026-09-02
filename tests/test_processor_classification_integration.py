from pathlib import Path
from tempfile import TemporaryDirectory

from src.business_rules.rule_service import RuleService
from src.document_processing.document_processor import DocumentProcessor
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.review_decision_service import ReviewDecisionService
from src.services.review_output_service import ReviewOutputService
from src.services.intake_document_naming_service import (
    IntakeDocumentNamingVocabulary,
)
from src.services.production_filename_assembly_service import (
    ProductionFilenameAssemblyService,
)


passed = 0
failed = 0


class SyntheticOCR:
    """
    Synthetic OCR test double.

    No PaddleOCR model initialization or prediction occurs.
    """

    def __init__(self, text=None):
        self.calls = 0
        self.text = text or (
            "Synthetic healthcare document text for deterministic "
            "classification integration testing."
        )

    def extract_text(self, file_path):
        self.calls += 1

        assert Path(file_path).is_file()

        return self.text


class SyntheticLLM:
    """
    Synthetic local-LLM test double.

    No Ollama server or model request occurs.
    """

    def __init__(self, classification):
        self.classification = dict(classification)

        # Match the real LLMService boundary used by DocumentProcessor.
        # The processor reads PHI-safe metrics from self.llm.provider.
        self.provider = self

        self.classify_calls = 0
        self.extract_calls = []
        self.last_metrics = {}

    def classify(self, text):
        self.classify_calls += 1

        assert isinstance(text, str)
        assert text

        self.last_metrics = {
            "request_type": "classification",
            "seed": 42,
            "total_duration_seconds": 0.8,
            "load_duration_seconds": 0.1,
            "prompt_eval_duration_seconds": 0.2,
            "eval_duration_seconds": 0.5,
            "prompt_eval_count": 10,
            "eval_count": 6,
        }

        return dict(self.classification)

    def extract(
        self,
        text,
        prompt,
        attempt=1,
    ):
        self.extract_calls.append(
            {
                "attempt": attempt,
                "prompt": prompt,
            }
        )

        self.last_metrics = {
            "request_type": "extraction",
            "attempt": attempt,
            "seed": 41 + attempt,
            "retry_prompt_applied": attempt > 1,
            "total_duration_seconds": 1.0 + attempt,
            "load_duration_seconds": 0.1,
            "prompt_eval_duration_seconds": 0.3,
            "eval_duration_seconds": 0.6 + attempt,
            "prompt_eval_count": 20,
            "eval_count": 10 + attempt,
        }

        return {
            "fields": {},
            "service_lines": [],
        }

    def get_last_request_metrics(self):
        return dict(self.last_metrics)


def run_test(name, test):
    global passed
    global failed

    try:
        test()
        passed += 1
        print(f"PASSED: {name}")
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def build_processor(classification, *, ocr_text=None):
    processor = DocumentProcessor.__new__(
        DocumentProcessor
    )

    processor.ocr = SyntheticOCR(ocr_text)
    processor.llm = SyntheticLLM(
        classification
    )
    processor.evidence_validation = (
        EvidenceValidationService()
    )
    processor.rules = RuleService()
    processor.review_decisions = (
        ReviewDecisionService()
    )
    processor.review_outputs = ReviewOutputService()
    processor.intake_document_naming = IntakeDocumentNamingVocabulary()
    processor.filename_assembly = ProductionFilenameAssemblyService(
        tables_provider=lambda: None
    )

    return processor


def process_classification(classification, *, ocr_text=None, stage_observer=None):
    with TemporaryDirectory() as directory:
        file_path = (
            Path(directory)
            / "synthetic-document.txt"
        )

        file_path.write_text(
            "Synthetic file content.",
            encoding="utf-8",
        )

        processor = build_processor(
            classification,
            ocr_text=ocr_text,
        )

        document = processor.process(
            file_path,
            stage_observer=stage_observer,
        )

        return processor, document


def classification(
    *,
    category,
    subtype,
    document_type,
    reason="Synthetic supported classification reason.",
    confidence=0.90,
):
    return {
        "document_category": category,
        "document_subtype": subtype,
        "document_type": document_type,
        "reason": reason,
        "confidence": confidence,
    }


def test_referral_survives_processor():
    processor, document = process_classification(
        classification(
            category="referral",
            subtype="unknown",
            document_type="referral",
        )
    )
    assert document.ocr_document is not None
    assert document.ocr_document.relationship_status == "unavailable_legacy_flat"

    assert document.document_category == "referral"
    assert document.document_subtype == "unknown"
    assert document.document_type == "referral"
    assert processor.ocr.calls == 1
    assert processor.llm.classify_calls == 1


def test_initial_authorization_survives_processor():
    _, document = process_classification(
        classification(
            category="authorization",
            subtype="initial",
            document_type="authorization",
        )
    )

    assert document.document_category == "authorization"
    assert document.document_subtype == "initial"
    assert document.document_type == "authorization"


def test_renewal_uses_legacy_routing():
    processor, document = process_classification(
        classification(
            category="authorization",
            subtype="renewal",
            document_type="authorization_renewal",
        )
    )

    assert document.document_category == "authorization"
    assert document.document_subtype == "renewal"
    assert document.document_type == "authorization_renewal"

    assert all(
        call["prompt"] == "authorization_renewal"
        for call in processor.llm.extract_calls
    )


def test_authorization_termination_survives_processor():
    _, document = process_classification(
        classification(
            category="termination",
            subtype="authorization_termination",
            document_type="termination",
        )
    )

    assert document.document_category == "termination"
    assert document.document_subtype == (
        "authorization_termination"
    )
    assert document.document_type == "termination"


def test_service_termination_survives_processor():
    _, document = process_classification(
        classification(
            category="termination",
            subtype="service_termination",
            document_type="termination",
        )
    )

    assert document.document_category == "termination"
    assert document.document_subtype == (
        "service_termination"
    )


def test_reason_and_confidence_survive_processor():
    reason = (
        "Synthetic evidence supports an authorization renewal."
    )

    _, document = process_classification(
        classification(
            category="authorization",
            subtype="renewal",
            document_type="authorization_renewal",
            reason=reason,
            confidence=0.87,
        )
    )

    assert document.classification_reason == reason
    assert document.confidence == 0.87


def test_review_output_preserves_classification():
    _, document = process_classification(
        classification(
            category="termination",
            subtype="service_termination",
            document_type="termination",
            reason=(
                "Synthetic evidence supports service termination."
            ),
            confidence=0.88,
        )
    )

    output = document.review_output

    assert output is not None
    assert output.document_category == "termination"
    assert output.document_subtype == (
        "service_termination"
    )
    assert output.document_type == "termination"
    assert output.classification_reason == (
        "Synthetic evidence supports service termination."
    )
    assert output.classification_confidence == 0.88


def test_classification_metrics_are_phi_safe():
    _, document = process_classification(
        classification(
            category="referral",
            subtype="unknown",
            document_type="referral",
        )
    )

    metrics = document.processing_metrics[
        "classification_ollama"
    ]

    assert metrics["request_type"] == "classification"
    assert metrics["seed"] == 42
    assert "text" not in metrics
    assert "reason" not in metrics
    assert "document_category" not in metrics
    assert "document_subtype" not in metrics


def test_unknown_classification_is_preserved():
    _, document = process_classification(
        classification(
            category="unknown",
            subtype="unknown",
            document_type="unknown",
            reason=(
                "Synthetic evidence does not support a known category."
            ),
            confidence=0.20,
        )
    )

    assert document.document_category == "unknown"
    assert document.document_subtype == "unknown"
    assert document.document_type == "unknown"
    assert document.confidence == 0.0
    assert document.classification_support_status == "unknown"
    assert document.family_evidence_confidence is None


def test_deterministic_2067_utl_overrides_legacy_plan_of_care():
    _, document = process_classification(
        classification(
            category="plan_of_care",
            subtype="unknown",
            document_type="plan_of_care",
            confidence=1.0,
        ),
        ocr_text=(
            "2067. The team was unable to reach the member after an "
            "attempted call."
        ),
    )
    assert document.document_category == "2067"
    assert document.document_subtype == "utl"
    assert document.document_type == "2067"
    assert document.classification_support_status == "supported"
    assert document.subtype_support_status == "supported"
    assert "UTL" not in document.raw_text


def test_no_real_local_ai_provider_is_initialized():
    processor = build_processor(
        classification(
            category="referral",
            subtype="unknown",
            document_type="referral",
        )
    )

    assert isinstance(
        processor.ocr,
        SyntheticOCR,
    )
    assert isinstance(
        processor.llm,
        SyntheticLLM,
    )


def test_one_attempt_lifecycle_exposes_safe_metrics_and_selection():
    events = []
    process_classification(
        classification(
            category="referral", subtype="unknown", document_type="referral"
        ),
        stage_observer=lambda **event: events.append(event),
    )
    names = [(event["stage"], event["status"]) for event in events]
    assert ("extraction_attempt_1", "started") in names
    assert ("extraction_attempt_1", "completed") in names
    assert ("validation_attempt_1", "completed") in names
    assert ("extraction_retry_decision", "completed") in names
    assert ("extraction_attempt_2", "started") not in names
    selection = next(
        event for event in events
        if event["stage"] == "extraction_candidate_selection"
    )
    assert selection["selected_attempt"] == 1
    assert selection["attempt_count"] == 1
    completion = next(
        event for event in events if event["stage"] == "document_processing"
    )
    assert completion["extraction_wall_seconds"] >= 0
    assert completion["validation_wall_seconds"] >= 0
    extraction = next(
        event for event in events
        if event["stage"] == "extraction_attempt_1"
        and event["status"] == "completed"
    )
    assert extraction["prompt_token_count"] == 20
    assert extraction["generated_token_count"] == 11
    protected_keys = {
        "text", "source_text", "prompt", "filename", "row_id", "patient"
    }
    assert protected_keys.isdisjoint(
        key for event in events for key in event
    )


def test_two_attempt_lifecycle_validates_each_attempt_and_selects_second():
    events = []
    processor = build_processor(
        classification(
            category="authorization",
            subtype="initial",
            document_type="authorization",
        )
    )
    original_select = processor._select_validated_candidate
    processor._select_validated_candidate = lambda **kwargs: (
        kwargs["second_candidate"], 2
    )
    try:
        with TemporaryDirectory() as directory:
            file_path = Path(directory) / "synthetic-document.txt"
            file_path.write_text("Synthetic file content.", encoding="utf-8")
            document = processor.process(
                file_path, stage_observer=lambda **event: events.append(event)
            )
    finally:
        processor._select_validated_candidate = original_select
    names = [(event["stage"], event["status"]) for event in events]
    for expected in (
        ("extraction_attempt_2", "started"),
        ("extraction_attempt_2", "completed"),
        ("validation_attempt_2", "completed"),
    ):
        assert expected in names
    decision = next(
        event for event in events if event["stage"] == "extraction_retry_decision"
    )
    assert decision["retry_triggered"] is True
    assert decision["raw_retry_required"] is True
    selection = next(
        event for event in events
        if event["stage"] == "extraction_candidate_selection"
    )
    assert selection == {
        "stage": "extraction_candidate_selection",
        "status": "completed",
        "selected_attempt": 2,
        "attempt_count": 2,
    }
    assert document.processing_metrics["extraction_selected_attempt"] == 2


print("=" * 60)
print("Testing Processor Classification Integration")
print("=" * 60)

run_test(
    "referral survives processor",
    test_referral_survives_processor,
)
run_test(
    "initial authorization survives processor",
    test_initial_authorization_survives_processor,
)
run_test(
    "renewal uses legacy routing",
    test_renewal_uses_legacy_routing,
)
run_test(
    "authorization termination survives processor",
    test_authorization_termination_survives_processor,
)
run_test(
    "service termination survives processor",
    test_service_termination_survives_processor,
)
run_test(
    "reason and confidence survive processor",
    test_reason_and_confidence_survive_processor,
)
run_test(
    "review output preserves classification",
    test_review_output_preserves_classification,
)
run_test(
    "classification metrics are PHI-safe",
    test_classification_metrics_are_phi_safe,
)
run_test(
    "unknown classification is preserved",
    test_unknown_classification_is_preserved,
)
run_test(
    "deterministic 2067 UTL overrides legacy plan of care",
    test_deterministic_2067_utl_overrides_legacy_plan_of_care,
)
run_test(
    "no real local AI provider is initialized",
    test_no_real_local_ai_provider_is_initialized,
)
run_test(
    "one-attempt lifecycle exposes safe metrics and selection",
    test_one_attempt_lifecycle_exposes_safe_metrics_and_selection,
)
run_test(
    "two-attempt lifecycle validates each attempt and selects second",
    test_two_attempt_lifecycle_validates_each_attempt_and_selects_second,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(
    "Real or mock: Synthetic deterministic integration test"
)
print("PaddleOCR prediction: Not called")
print("Local Ollama request: Not called")
print("External integration: Not called")
print(
    "PHI handling: No OCR or extracted values printed"
)

if failed:
    raise SystemExit(1)
