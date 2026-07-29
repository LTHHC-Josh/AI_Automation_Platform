from src.ai.ocr.ocr_factory import OCRFactory


class OCRService:

    def __init__(self):

        self.provider = OCRFactory.create()

    def extract_text(self, file_path):

        return self.provider.extract_text(file_path)