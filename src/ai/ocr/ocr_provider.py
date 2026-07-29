from abc import ABC, abstractmethod


class OCRProvider(ABC):
    """
    Base class for every OCR implementation.
    """

    @abstractmethod
    def extract_text(self, file_path):
        pass