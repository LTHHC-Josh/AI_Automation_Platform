from src.ai.ocr.ocr_factory import OCRFactory


class OCRService:
    """
    Service responsible for OCR operations.

    The service hides the provider implementation from the rest
    of the application. It simply delegates OCR processing to
    the configured provider returned by the OCRFactory.
    """

    def __init__(self):
        self.provider = OCRFactory.create()

    def extract_text(self, file_path):
        """
        Extract text from the supplied document.

        Args:
            file_path: Path to the document.

        Returns:
            Extracted text from the configured OCR provider.
        """

        return self.provider.extract_text(file_path)