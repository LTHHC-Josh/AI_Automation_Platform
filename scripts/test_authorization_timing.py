from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from src.document_processing.document_processor import DocumentProcessor


PDF_DIRECTORY = Path("data/incoming")


class MethodTimer:
    """
    Wraps service methods and records their execution time.

    This lets us measure the existing pipeline without changing
    production processing behavior.
    """

    def __init__(self) -> None:
        self.durations: dict[str, float] = {}

    def wrap(
        self,
        target: Any,
        method_name: str,
        timing_name: str,
    ) -> bool:
        """
        Wrap a method when it exists on the target object.

        Returns True when the method was found and wrapped.
        """

        if target is None:
            return False

        original_method = getattr(
            target,
            method_name,
            None,
        )

        if not callable(original_method):
            return False

        def timed_method(
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            started_at = perf_counter()

            try:
                return original_method(
                    *args,
                    **kwargs,
                )
            finally:
                elapsed = (
                    perf_counter()
                    - started_at
                )

                self.durations[timing_name] = (
                    self.durations.get(
                        timing_name,
                        0.0,
                    )
                    + elapsed
                )

        setattr(
            target,
            method_name,
            timed_method,
        )

        return True


def format_duration(
    seconds: float,
) -> str:
    """
    Format a duration as seconds and minutes.
    """

    return (
        f"{seconds:.2f} seconds "
        f"({seconds / 60:.2f} minutes)"
    )


def format_percentage(
    value: float | None,
) -> str:
    if value is None:
        return "Not available"

    return f"{value * 100:.1f}%"


def find_service(
    processor: DocumentProcessor,
    attribute_names: tuple[str, ...],
) -> Any:
    """
    Return the first matching service attribute on DocumentProcessor.
    """

    for attribute_name in attribute_names:
        service = getattr(
            processor,
            attribute_name,
            None,
        )

        if service is not None:
            return service

    return None


def wrap_first_available_method(
    timer: MethodTimer,
    target: Any,
    method_names: tuple[str, ...],
    timing_name: str,
) -> bool:
    """
    Wrap the first matching method on a service.
    """

    for method_name in method_names:
        wrapped = timer.wrap(
            target=target,
            method_name=method_name,
            timing_name=timing_name,
        )

        if wrapped:
            return True

    return False


def print_document_result(
    document: Any,
) -> None:
    print()
    print("DOCUMENT RESULT")
    print("-" * 60)

    print(
        f"Document type: "
        f"{getattr(document, 'document_type', None)}"
    )

    print(
        "Classification confidence: "
        f"{format_percentage(
            getattr(document, 'confidence', None)
        )}"
    )

    print(
        f"Business-rule actions: "
        f"{getattr(document, 'rule_actions', [])}"
    )

    print(
        f"Review status: "
        f"{getattr(document, 'review_status', None)}"
    )

    print(
        "Human verification required: "
        f"{getattr(
            document,
            'needs_human_review',
            None,
        )}"
    )

    print(
        f"Review reasons: "
        f"{getattr(document, 'review_reasons', [])}"
    )


def print_timing_result(
    setup_seconds: float,
    processing_seconds: float,
    total_seconds: float,
    timer: MethodTimer,
    validation_wrapped: bool,
    review_wrapped: bool,
) -> None:
    durations = timer.durations

    ocr_seconds = durations.get(
        "ocr",
        0.0,
    )

    classification_seconds = durations.get(
        "classification",
        0.0,
    )

    extraction_seconds = durations.get(
        "extraction",
        0.0,
    )

    validation_seconds = durations.get(
        "validation",
        0.0,
    )

    review_seconds = durations.get(
        "human_review",
        0.0,
    )

    measured_processing_seconds = sum(
        (
            ocr_seconds,
            classification_seconds,
            extraction_seconds,
            validation_seconds,
            review_seconds,
        )
    )

    unmeasured_overhead_seconds = max(
        processing_seconds
        - measured_processing_seconds,
        0.0,
    )

    print()
    print("TIMING RESULTS")
    print("-" * 60)

    print(
        "Provider/model initialization: "
        f"{format_duration(setup_seconds)}"
    )

    print(
        "OCR: "
        f"{format_duration(ocr_seconds)}"
    )

    print(
        "Classification: "
        f"{format_duration(
            classification_seconds
        )}"
    )

    print(
        "Extraction: "
        f"{format_duration(extraction_seconds)}"
    )

    if validation_wrapped:
        print(
            "Business-rule validation: "
            f"{format_duration(
                validation_seconds
            )}"
        )
    else:
        print(
            "Business-rule validation: "
            "method was not detected separately"
        )

    if review_wrapped:
        print(
            "Human-review decision: "
            f"{format_duration(review_seconds)}"
        )
    else:
        print(
            "Human-review decision: "
            "method was not detected separately"
        )

    print(
        "Other pipeline overhead: "
        f"{format_duration(
            unmeasured_overhead_seconds
        )}"
    )

    print(
        "Document processing total: "
        f"{format_duration(
            processing_seconds
        )}"
    )

    print(
        "Overall total including initialization: "
        f"{format_duration(total_seconds)}"
    )


def main() -> None:
    print("=" * 60)
    print("Testing Authorization Document Timing")
    print("=" * 60)

    pdf_files = sorted(
        PDF_DIRECTORY.glob("*.pdf")
    )

    if not pdf_files:
        print(
            "No PDF files were found in "
            f"{PDF_DIRECTORY}."
        )
        return

    pdf_file = pdf_files[0]

    print(f"Document: {pdf_file}")
    print()

    overall_started_at = perf_counter()

    setup_started_at = perf_counter()
    processor = DocumentProcessor()
    setup_seconds = (
        perf_counter()
        - setup_started_at
    )

    timer = MethodTimer()

    ocr_service = find_service(
        processor,
        (
            "ocr",
            "ocr_service",
        ),
    )

    llm_service = find_service(
        processor,
        (
            "llm",
            "llm_service",
        ),
    )

    business_rule_service = find_service(
        processor,
        (
            "business_rules",
            "business_rule_service",
            "rule_service",
            "rules",
        ),
    )

    review_service = find_service(
        processor,
        (
            "review_decision",
            "review_decision_service",
            "human_review",
            "human_review_service",
            "review_service",
        ),
    )

    ocr_wrapped = wrap_first_available_method(
        timer=timer,
        target=ocr_service,
        method_names=(
            "extract_text",
            "extract",
            "process",
        ),
        timing_name="ocr",
    )

    classification_wrapped = (
        wrap_first_available_method(
            timer=timer,
            target=llm_service,
            method_names=(
                "classify",
                "classify_document",
            ),
            timing_name="classification",
        )
    )

    extraction_wrapped = (
        wrap_first_available_method(
            timer=timer,
            target=llm_service,
            method_names=(
                "extract",
                "extract_data",
                "extract_fields",
            ),
            timing_name="extraction",
        )
    )

    validation_wrapped = (
        wrap_first_available_method(
            timer=timer,
            target=business_rule_service,
            method_names=(
                "apply",
                "apply_rules",
                "execute",
                "evaluate",
                "validate",
                "process",
            ),
            timing_name="validation",
        )
    )

    review_wrapped = (
        wrap_first_available_method(
            timer=timer,
            target=review_service,
            method_names=(
                "evaluate",
                "decide",
                "make_decision",
                "determine_review",
                "process",
                "apply",
            ),
            timing_name="human_review",
        )
    )

    print("Detected timed stages:")
    print(f"  OCR: {ocr_wrapped}")
    print(
        "  Classification: "
        f"{classification_wrapped}"
    )
    print(
        "  Extraction: "
        f"{extraction_wrapped}"
    )
    print(
        "  Business-rule validation: "
        f"{validation_wrapped}"
    )
    print(
        "  Human-review decision: "
        f"{review_wrapped}"
    )

    processing_started_at = perf_counter()

    document = processor.process(
        pdf_file
    )

    processing_seconds = (
        perf_counter()
        - processing_started_at
    )

    total_seconds = (
        perf_counter()
        - overall_started_at
    )

    print_document_result(
        document
    )

    print_timing_result(
        setup_seconds=setup_seconds,
        processing_seconds=processing_seconds,
        total_seconds=total_seconds,
        timer=timer,
        validation_wrapped=validation_wrapped,
        review_wrapped=review_wrapped,
    )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
