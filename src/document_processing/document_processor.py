from src.ai.ocr.ocr_service import OCRService
from src.ai.llm.llm_service import LLMService
from src.models.document import Document


class DocumentProcessor:
    """
    Coordinates the complete AI document processing pipeline.

    Pipeline:

        File
          │
          ▼
        OCR
          │
          ▼
        Classification
          │
          ▼
        Data Extraction
          │
          ▼
        Document
    """

    def __init__(self):

        self.ocr = OCRService()
        self.llm = LLMService()

    def process(self, file_path):
        """
        Process a document through the AI pipeline.

        Returns
        -------
        Document
        """

        document = Document(file_path=file_path)

        #
        # OCR
        #

        document.raw_text = self.ocr.extract_text(file_path)

        #
        # Classification
        #

        classification = self.llm.classify(
            document.raw_text
        )

        document.document_type = classification.get(
            "document_type",
            ""
        )

        document.confidence = classification.get(
            "confidence",
            0.0
        )

        #
        # Extraction
        #

        document.extracted_data = self.llm.extract(
            document.raw_text,
            document.document_type,
        )

        return document