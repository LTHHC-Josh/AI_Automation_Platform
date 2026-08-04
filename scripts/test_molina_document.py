from pathlib import Path
from typing import Any

from src.document_processing.document_processor import (
    DocumentProcessor,
)


PDF_DIRECTORY = Path(
    "data/incoming"
)


def format_percentage(
    value: float | None,
) -> str:
    if value is None:
        return "Not available"

    return f"{value * 100:.1f}%"


def format_value(
    value: Any,
) -> str:
    if value is None:
        return "None"

    return str(
        value
    )


def print_field_evidence(
    field_evidence: dict[str, dict[str, Any]],
) -> None:
    """
    Print extracted field evidence.

    This output may contain PHI and must remain local.
    """

    print("Field evidence:")

    if not field_evidence:
        print(
            "  No field evidence was returned."
        )
        return

    for field_name, evidence in field_evidence.items():
        print(
            f"  {field_name}:"
        )

        print(
            "    value: "
            f"{format_value(
                evidence.get('value')
            )}"
        )

        print(
            "    confidence: "
            f"{format_percentage(
                evidence.get(
                    'confidence',
                    0.0,
                )
            )}"
        )

        print(
            "    source_text: "
            f"{evidence.get(
                'source_text',
                '',
            ) or '[no source evidence]'}"
        )


def main() -> None:
    print("=" * 60)
    print("Testing Molina Authorization Document")
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

    processor = DocumentProcessor()

    for pdf_file in pdf_files:
        print()
        print("-" * 60)
        print(
            f"Processing: {pdf_file}"
        )

        try:
            document = processor.process(
                pdf_file
            )

            print(
                "Document type: "
                f"{document.document_type}"
            )

            print(
                "Classification confidence: "
                f"{format_percentage(
                    document.confidence
                )}"
            )

            print()

            print_field_evidence(
                document.field_evidence
            )

            print()

            print(
                "Deterministic validation actions: "
                f"{document.validation_actions}"
            )

            print(
                "Business-rule actions: "
                f"{document.rule_actions}"
            )

            print(
                "Minimum field confidence: "
                f"{format_percentage(
                    document.minimum_field_confidence
                )}"
            )

            print(
                "Review status: "
                f"{document.review_status}"
            )

            print(
                "Human verification required: "
                f"{document.needs_human_review}"
            )

            print(
                "Review reasons: "
                f"{document.review_reasons}"
            )

        except Exception as ex:
            print(
                "ERROR: "
                f"{type(ex).__name__}: {ex}"
            )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()