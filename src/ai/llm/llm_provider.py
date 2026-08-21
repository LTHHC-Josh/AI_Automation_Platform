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
        attempt: int = 1,
    ) -> dict:
        """
        Extract structured data from OCR text.

        Args:
            text:
                OCR text to process.

            prompt:
                Confirmed classification or extraction context.

            attempt:
                One-based extraction-attempt number. Providers may use
                this value to apply a deterministic alternate generation
                configuration for a controlled retry.

        Existing callers may omit attempt and will use attempt 1.
        """

        raise NotImplementedError

    def analyze_learning_structure(self, evidence) -> dict:
        """Return value-free structural observations for local learning."""

        raise NotImplementedError
