from pathlib import Path

from src.models.document import Document
from src.ai.ocr import OCRService


class DocumentClassifier:

    def __init__(self):

        self.ocr = OCRService()

    def classify(self, file_path):

        document = Document(
            file_path=Path(file_path)
        )

        #
        # Step 1
        # Convert document into text
        #

        document.raw_text = self.ocr.extract_text(file_path)

        #
        # Classification logic will be added here.
        #

        return document