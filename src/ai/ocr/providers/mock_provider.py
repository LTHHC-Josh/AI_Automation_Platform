from src.ai.ocr.ocr_provider import OCRProvider
from src.ai.ocr.provider_registration import register_ocr_provider


@register_ocr_provider("mock")
class MockProvider(OCRProvider):
    """
    Mock OCR provider used for development.
    """

    def extract_text(self, file_path):
        return """
Authorization

Patient:
John Smith

Insurance:
Humana

Authorization Number:
A123456

Visits Approved:
12
"""