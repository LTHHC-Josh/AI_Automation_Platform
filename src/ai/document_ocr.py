from pathlib import Path


class OCRService:
    """
    Responsible for converting documents into raw text.
    """

    def extract_text(self, file_path):

        file_path = Path(file_path)

        print(f"Reading document: {file_path.name}")

        #
        # OCR implementation will be added later.
        #

        return ""