from pathlib import Path

from pypdf import PdfReader

from src.ai.ocr.ocr_provider import OCRProvider
from src.ai.ocr.provider_registration import register_ocr_provider


@register_ocr_provider("pdf_text")
class PDFTextProvider(OCRProvider):
    """
    Extracts embedded text from searchable PDF documents.

    Image-only scanned PDFs will require a separate image OCR provider.
    """

    def extract_text(
        self,
        file_path,
    ) -> str:
        document_path = Path(file_path)

        if not document_path.exists():
            raise FileNotFoundError(
                f"PDF file was not found: {document_path}"
            )

        if not document_path.is_file():
            raise ValueError(
                f"PDF path is not a file: {document_path}"
            )

        if document_path.suffix.lower() != ".pdf":
            raise ValueError(
                "PDFTextProvider only supports PDF files. "
                f"Received: {document_path.suffix}"
            )

        try:
            reader = PdfReader(str(document_path))
        except Exception as ex:
            raise RuntimeError(
                f"Unable to open PDF file "
                f"{document_path.name}: {ex}"
            ) from ex

        extracted_pages: list[str] = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            try:
                page_text = page.extract_text() or ""
            except Exception as ex:
                raise RuntimeError(
                    f"Unable to extract text from page "
                    f"{page_number} of {document_path.name}: {ex}"
                ) from ex

            cleaned_text = page_text.strip()

            if cleaned_text:
                extracted_pages.append(cleaned_text)

        full_text = "\n\n".join(
            extracted_pages
        ).strip()

        if not full_text:
            raise RuntimeError(
                "No embedded text was found in "
                f"{document_path.name}. The PDF may be scanned "
                "or image-only and will require image OCR."
            )

        return full_text