from pathlib import Path
from time import perf_counter
from typing import Any

from src.document_processing.document_processor import (
    DocumentProcessor,
)


PDF_DIRECTORY = Path(
    "data/incoming"
)


def format_duration(
    seconds: float,
) -> str:
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


def main() -> None:
    print("=" * 60)
    print("Testing Combined Local Ollama Analysis Timing")
    print("=" * 60)

    pdf_files = sorted(
        PDF_DIRECTORY.glob(
            "*.pdf"
        )
    )

    if not pdf_files:
        print(
            "No PDF files were found in "
            f"{PDF_DIRECTORY}."
        )
        return

    pdf_file = pdf_files[0]

    total_started_at = perf_counter()

    initialization_started_at = perf_counter()

    processor = DocumentProcessor()

    initialization_seconds = (
        perf_counter()
        - initialization_started_at
    )

    original_ocr_method = (
        processor.ocr.extract_text
    )

    original_analyze_method = (
        processor.llm.analyze
    )

    timings: dict[str, float] = {
        "ocr": 0.0,
        "combined_analysis": 0.0,
    }

    def timed_ocr(
        *args: Any,
        **kwargs: Any,
    ) -> str:
        started_at = perf_counter()

        try:
            return original_ocr_method(
                *args,
                **kwargs,
            )
        finally:
            timings["ocr"] = (
                perf_counter()
                - started_at
            )

    def timed_analysis(
        *args: Any,
        **kwargs: Any,
    ) -> dict:
        started_at = perf_counter()

        try:
            return original_analyze_method(
                *args,
                **kwargs,
            )
        finally:
            timings["combined_analysis"] = (
                perf_counter()
                - started_at
            )

    processor.ocr.extract_text = (
        timed_ocr
    )

    processor.llm.analyze = (
        timed_analysis
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
        - total_started_at
    )

    validation_and_review_seconds = max(
        processing_seconds
        - timings["ocr"]
        - timings["combined_analysis"],
        0.0,
    )

    print()
    print("DOCUMENT RESULT")
    print("-" * 60)

    print(
        f"Document type: "
        f"{document.document_type}"
    )

    print(
        "Classification confidence: "
        f"{format_percentage(
            document.confidence
        )}"
    )

    print(
        f"Extracted data: "
        f"{document.extracted_data}"
    )

    print(
        f"Business-rule actions: "
        f"{document.rule_actions}"
    )

    print(
        f"Review status: "
        f"{document.review_status}"
    )

    print(
        "Human verification required: "
        f"{document.needs_human_review}"
    )

    print(
        f"Review reasons: "
        f"{document.review_reasons}"
    )

    print()
    print("TIMING RESULTS")
    print("-" * 60)

    print(
        "Provider/model initialization: "
        f"{format_duration(
            initialization_seconds
        )}"
    )

    print(
        "OCR/cache lookup: "
        f"{format_duration(
            timings['ocr']
        )}"
    )

    print(
        "Combined Ollama analysis: "
        f"{format_duration(
            timings['combined_analysis']
        )}"
    )

    print(
        "Validation and review: "
        f"{format_duration(
            validation_and_review_seconds
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
        f"{format_duration(
            total_seconds
        )}"
    )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()