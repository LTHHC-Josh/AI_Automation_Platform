from pathlib import Path

from src.document_processing.document_processor import (
    DocumentProcessor,
)


PDF_DIRECTORY = Path("data/incoming")


def format_percentage(
    value: float | None,
) -> str:
    if value is None:
        return "Not available"

    return f"{value * 100:.1f}%"


def main() -> None:
    print("=" * 60)
    print("Testing Molina Authorization Document")
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

    processor = DocumentProcessor()

    for pdf_file in pdf_files:
        print()
        print("-" * 60)
        print(f"Processing: {pdf_file}")

        try:
            document = processor.process(
                pdf_file
            )

            print(
                f"Document type: "
                f"{document.document_type}"
            )

            print(
                "Classification confidence: "
                f"{format_percentage(document.confidence)}"
            )

            print("Extracted data:")

            for field_name, field_value in (
                document.extracted_data.items()
            ):
                print(
                    f"  {field_name}: "
                    f"{field_value}"
                )

            print("Field confidences:")

            for field_name, confidence in (
                document.field_confidences.items()
            ):
                print(
                    f"  {field_name}: "
                    f"{format_percentage(confidence)}"
                )

            print(
                "Minimum field confidence: "
                f"{format_percentage(
                    document.minimum_field_confidence
                )}"
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

        except Exception as ex:
            print(
                f"ERROR: "
                f"{type(ex).__name__}: {ex}"
            )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()