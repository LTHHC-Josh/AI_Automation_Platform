from abc import ABC, abstractmethod

from src.models.ocr_document import OCRDocument
from src.ai.ocr.errors import OCRCacheOnlyMissError


class OCRProvider(ABC):
    """
    Base class for every OCR implementation.
    """

    @abstractmethod
    def extract_text(self, file_path):
        pass

    def extract_document(self, file_path, *, cache_only: bool = False) -> OCRDocument:
        """Backward-compatible structured wrapper for text-only providers."""

        if cache_only:
            raise OCRCacheOnlyMissError("OCR cache is unavailable.") from None
        text = self.extract_text(file_path)
        return OCRDocument.from_flat_text(text)
