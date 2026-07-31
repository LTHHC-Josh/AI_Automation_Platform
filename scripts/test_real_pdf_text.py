from pathlib import Path

from src.ai.ocr.ocr_service import OCRService


PDF_DIRECTORY = Path("data/incoming")


def main() -> None:
    print("=" * 60)
    print("Testing Real PDF Text Extraction")
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

    ocr_service = OCRService()

    for pdf_file in pdf_files:
        print()
        print("-" * 60)
        print(f"PDF: {pdf_file}")

        try:
            extracted_text = (
                ocr_service.extract_text(
                    pdf_file
                )
            )

            print()
            print("EXTRACTED TEXT")
            print("-" * 60)
            print(extracted_text)

        except Exception as ex:
            print(f"ERROR: {ex}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()