from pathlib import Path

from src.document_processing.document_processor import DocumentProcessor


def main():

    processor = DocumentProcessor()

    document = processor.process(
        Path("sample_authorization.pdf")
    )

    print()

    print("=" * 60)
    print("DOCUMENT PROCESSOR TEST")
    print("=" * 60)

    print()

    print("File:")
    print(document.file_path)

    print()

    print("Type:")
    print(document.document_type)

    print()

    print("Confidence:")
    print(document.confidence)

    print()

    print("Raw Text:")
    print(document.raw_text)

    print()

    print("Extracted Data:")

    for key, value in document.extracted_data.items():
        print(f"{key}: {value}")

    print()

    print("=" * 60)
    print("SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()