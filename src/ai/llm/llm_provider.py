from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Base class for every LLM implementation.
    """

    @abstractmethod
    def classify(
        self,
        text: str,
    ) -> dict:
        """
        Classify OCR text.
        """

        raise NotImplementedError

    @abstractmethod
    def extract(
        self,
        text: str,
        prompt: str,
    ) -> dict:
        """
        Extract structured data from OCR text.
        """

        raise NotImplementedError