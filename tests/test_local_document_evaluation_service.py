import contextlib
import io
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models.document import (
    AuthorizationServiceLine,
    Document,
)


PROTECTED_MARKER = "PROTECTED_SYNTHETIC_MARKER"
SAFE_RUN_TYPE = "Controlled Local Evaluation"


class RecordingProcessor:
    def __init__(self, document=None, error=None):
        self.document = document
        self.error = error
        self.calls = []

    def process(self, file_path, *, ocr_cache_only=False):
        self.calls.append(
            {
                "file_path": file_path,
                "ocr_cache_only": ocr_cache_only,
            }
        )

        print(PROTECTED_MARKER)
        print(PROTECTED_MARKER, file=sys.stderr)

        if self.error is not None:
            raise self.error

        return self.document


class RecordingProtectedReviewConsumer:
    def __init__(self):
        self.documents = []

    def review(self, document):
        self.documents.append(document)
        print(PROTECTED_MARKER)


def build_document(path: Path) -> Document:
    document = Document(
        file_path=path,
        document_type="authorization",
        document_category="authorization",
        document_subtype="initial",
        classification_reason=PROTECTED_MARKER,
        confidence=0.91,
        raw_text=PROTECTED_MARKER,
    )

    document.extracted_data = {
        "supported_high": PROTECTED_MARKER,
        "supported_low": PROTECTED_MARKER,
        "empty_field": None,
    }

    document.field_confidences = {
        "supported_high": 0.91,
        "supported_low": 0.50,
        "empty_field": 0.0,
    }

    document.field_evidence = {
        "supported_high": {
            "value": PROTECTED_MARKER,
            "confidence": 0.91,
            "source_text": PROTECTED_MARKER,
        }
    }

    document.service_lines = [
        AuthorizationServiceLine(
            service_code=PROTECTED_MARKER,
            confidence=0.91,
            source_text=PROTECTED_MARKER,
        ),
        AuthorizationServiceLine(
            quantity=7,
            confidence=0.50,
            source_text=PROTECTED_MARKER,
        ),
    ]

    document.validation_actions = [
        PROTECTED_MARKER,
        PROTECTED_MARKER,
    ]

    document.rule_actions = [
        PROTECTED_MARKER,
    ]

    document.needs_human_review = True
    document.review_status = "Human Review Required"
    document.review_reasons = [
        PROTECTED_MARKER,
        PROTECTED_MARKER,
        PROTECTED_MARKER,
    ]
    document.minimum_field_confidence = 0.50

    document.processing_metrics = {
        "ocr_wall_seconds": 0.10,
        "classification_wall_seconds": 0.20,
        "extraction_wall_seconds": 0.30,
        "validation_wall_seconds": 0.40,
        "business_rules_wall_seconds": 0.50,
        "human_review_wall_seconds": 0.60,
        "total_wall_seconds": 2.10,
        "extraction_attempt_count": 2,
        "extraction_retry_triggered": True,
        "extraction_selected_attempt": 2,
        "provider_detail": PROTECTED_MARKER,
    }

    document.review_output = {
        "protected": PROTECTED_MARKER,
    }

    return document


def evaluate_with_synthetic_document(
    *,
    protected_review_consumer=None,
):
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
        LocalEvaluationExecutionClassification,
    )

    temporary_directory = TemporaryDirectory()
    root = Path(temporary_directory.name)
    protected_path = root / f"{PROTECTED_MARKER}.pdf"
    protected_path.write_bytes(b"synthetic")

    document = build_document(protected_path)
    processor = RecordingProcessor(document=document)

    service = LocalDocumentEvaluationService(
        document_directory=root,
        processor_factory=lambda: processor,
        execution_classification=(
            LocalEvaluationExecutionClassification.SYNTHETIC_MOCK
        ),
        protected_review_consumer=protected_review_consumer,
    )

    stdout = io.StringIO()
    stderr = io.StringIO()

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        result = service.evaluate(
            document_index=1,
            run_type=SAFE_RUN_TYPE,
            authorize_cached_ocr_access=True,
            authorize_local_ollama=True,
        )

    return (
        temporary_directory,
        protected_path,
        processor,
        result,
        stdout.getvalue(),
        stderr.getvalue(),
    )


def test_numeric_selector_is_required_before_document_access():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    factory_calls = []
    service = LocalDocumentEvaluationService(
        document_directory=Path("unused"),
        processor_factory=lambda: factory_calls.append(True),
    )

    result = service.evaluate(
        document_index=None,
        run_type=SAFE_RUN_TYPE,
        authorize_cached_ocr_access=True,
        authorize_local_ollama=True,
    )

    assert result.success is False
    assert result.failure_category == "invalid_document_selector"
    assert factory_calls == []


def test_blank_run_type_is_rejected_before_document_access():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    factory_calls = []
    service = LocalDocumentEvaluationService(
        document_directory=Path("unused"),
        processor_factory=lambda: factory_calls.append(True),
    )

    result = service.evaluate(
        document_index=1,
        run_type="   ",
        authorize_cached_ocr_access=True,
        authorize_local_ollama=True,
    )

    assert result.success is False
    assert result.failure_category == "invalid_run_type"
    assert result.run_type == ""
    assert factory_calls == []


def test_cached_ocr_authorization_is_required():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    service = LocalDocumentEvaluationService(
        document_directory=Path("unused"),
    )

    result = service.evaluate(
        document_index=1,
        run_type=SAFE_RUN_TYPE,
        authorize_cached_ocr_access=False,
        authorize_local_ollama=True,
    )

    assert result.failure_category == "protected_document_access_not_authorized"


def test_local_ollama_authorization_is_required():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
    )

    service = LocalDocumentEvaluationService(
        document_directory=Path("unused"),
    )

    result = service.evaluate(
        document_index=1,
        run_type=SAFE_RUN_TYPE,
        authorize_cached_ocr_access=True,
        authorize_local_ollama=False,
    )

    assert result.failure_category == "local_ollama_not_authorized"


def test_processing_uses_cache_only_and_suppresses_nested_output():
    temporary, protected_path, processor, result, stdout, stderr = (
        evaluate_with_synthetic_document()
    )

    try:
        assert result.success is True
        assert processor.calls == [
            {
                "file_path": protected_path,
                "ocr_cache_only": True,
            }
        ]
        assert stdout == ""
        assert stderr == ""
    finally:
        temporary.cleanup()


def test_filename_path_and_protected_values_are_absent_from_result():
    temporary, protected_path, _, result, stdout, stderr = (
        evaluate_with_synthetic_document()
    )

    try:
        rendered = repr(result)
        safe_mapping = result.to_safe_dict()
        serialized = repr(safe_mapping)

        for forbidden in (
            PROTECTED_MARKER,
            str(protected_path),
            protected_path.name,
        ):
            assert forbidden not in rendered
            assert forbidden not in serialized
            assert forbidden not in stdout
            assert forbidden not in stderr

        assert not hasattr(result, "document")
        assert not hasattr(result, "review_output")
        assert not hasattr(result, "document_path")
        assert not hasattr(result, "filename")
        assert not hasattr(result, "fingerprint")
    finally:
        temporary.cleanup()


def test_aggregate_counts_and_review_metadata_are_preserved():
    temporary, _, _, result, _, _ = evaluate_with_synthetic_document()

    try:
        assert result.final_field_count == 2
        assert result.service_line_count == 2
        assert result.low_confidence_field_count == 1
        assert result.low_confidence_service_line_count == 1
        assert result.validation_action_count == 2
        assert result.business_rule_action_count == 1
        assert result.review_required is True
        assert result.review_status == "Human Review Required"
        assert result.review_reason_count == 3
        assert result.minimum_field_confidence == 0.50
        assert result.extraction_attempt_count == 2
        assert result.retry_triggered is True
        assert result.selected_attempt == 2
    finally:
        temporary.cleanup()


def test_only_allowlisted_stage_timings_are_returned():
    temporary, _, _, result, _, _ = evaluate_with_synthetic_document()

    try:
        assert set(result.stage_timings) == {
            "ocr",
            "classification",
            "extraction",
            "validation",
            "business_rules",
            "review",
        }
        assert result.total_timing == 2.10
        assert PROTECTED_MARKER not in repr(result.stage_timings)
    finally:
        temporary.cleanup()


def test_execution_classification_and_suppression_provenance_are_explicit():
    from src.services.local_document_evaluation_service import (
        LocalEvaluationExecutionClassification,
    )

    temporary, _, _, result, _, _ = evaluate_with_synthetic_document()

    try:
        assert result.execution_classification == (
            LocalEvaluationExecutionClassification.SYNTHETIC_MOCK.value
        )
        assert result.cache_only_enforced is True
        assert result.processing_stdout_suppressed is True
        assert result.processing_stderr_suppressed is True
        assert result.protected_values_suppressed is True
        assert result.external_integrations_invoked is False
    finally:
        temporary.cleanup()


def test_raw_provider_exception_is_sanitized_without_context():
    from src.services.local_document_evaluation_service import (
        LocalDocumentEvaluationService,
        LocalEvaluationExecutionClassification,
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        protected_path = root / f"{PROTECTED_MARKER}.pdf"
        protected_path.write_bytes(b"synthetic")

        raw_error = RuntimeError(PROTECTED_MARKER)
        raw_error.__cause__ = ValueError(PROTECTED_MARKER)
        processor = RecordingProcessor(error=raw_error)

        service = LocalDocumentEvaluationService(
            document_directory=root,
            processor_factory=lambda: processor,
            execution_classification=(
                LocalEvaluationExecutionClassification.SYNTHETIC_MOCK
            ),
        )

        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = service.evaluate(
                document_index=1,
                run_type=SAFE_RUN_TYPE,
                authorize_cached_ocr_access=True,
                authorize_local_ollama=True,
            )

        assert result.success is False
        assert result.failure_category == "local_processing_failed"
        assert result.execution_status == "failed"
        assert PROTECTED_MARKER not in repr(result)
        assert PROTECTED_MARKER not in stdout.getvalue()
        assert PROTECTED_MARKER not in stderr.getvalue()


def test_protected_review_handoff_is_in_memory_and_not_in_result():
    consumer = RecordingProtectedReviewConsumer()
    temporary, _, _, result, stdout, stderr = evaluate_with_synthetic_document(
        protected_review_consumer=consumer,
    )

    try:
        assert len(consumer.documents) == 1
        assert consumer.documents[0].raw_text == PROTECTED_MARKER
        assert result.protected_review_handoff_completed is True
        assert PROTECTED_MARKER not in repr(result)
        assert stdout == ""
        assert stderr == ""
    finally:
        temporary.cleanup()


def test_service_has_no_external_integration_imports():
    import inspect

    from src.services import local_document_evaluation_service

    source = inspect.getsource(
        local_document_evaluation_service
    ).lower()

    for forbidden_import in (
        "src.graph",
        "smartsheet",
        "mailbox",
    ):
        assert forbidden_import not in source


def test_cli_requires_selector_run_type_and_authorizations():
    from scripts.evaluate_local_document import (
        build_argument_parser,
    )

    parser = build_argument_parser()

    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        try:
            parser.parse_args([])
        except SystemExit as error:
            assert error.code != 0
        else:
            raise AssertionError("Expected required CLI arguments.")


def test_cli_rejects_blank_run_type():
    from scripts.evaluate_local_document import (
        build_argument_parser,
    )

    parser = build_argument_parser()

    with contextlib.redirect_stderr(io.StringIO()):
        try:
            parser.parse_args(
                [
                    "--document-index",
                    "1",
                    "--run-type",
                    "   ",
                    "--authorize-cached-ocr-access",
                    "--authorize-local-ollama",
                ]
            )
        except SystemExit as error:
            assert error.code != 0
        else:
            raise AssertionError("Expected blank Run Type rejection.")


def test_cli_accepts_only_explicit_safe_preflight_values():
    from scripts.evaluate_local_document import (
        build_argument_parser,
    )

    parser = build_argument_parser()
    args = parser.parse_args(
        [
            "--document-index",
            "1",
            "--run-type",
            f"  {SAFE_RUN_TYPE}  ",
            "--authorize-cached-ocr-access",
            "--authorize-local-ollama",
        ]
    )

    assert args.document_index == 1
    assert args.run_type == SAFE_RUN_TYPE
    assert args.authorize_cached_ocr_access is True
    assert args.authorize_local_ollama is True
