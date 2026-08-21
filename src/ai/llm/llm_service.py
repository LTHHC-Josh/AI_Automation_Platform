from src.ai.llm.llm_factory import LLMFactory


class LLMService:
    """
    Application service for the configured LLM provider.
    """

    def __init__(self) -> None:
        self.provider = LLMFactory.create()

    def classify(
        self,
        text: str,
    ) -> dict:
        """
        Classify OCR text.
        """

        return self.provider.classify(
            text
        )

    def extract(
        self,
        text: str,
        prompt: str,
        attempt: int = 1,
    ) -> dict:
        """
        Extract structured data from OCR text.

        The attempt number is forwarded without interpretation so the
        configured provider can apply a deterministic retry strategy.
        """

        return self.provider.extract(
            text,
            prompt,
            attempt=attempt,
        )

    def analyze_learning_structure(self, evidence) -> dict:
        """Analyze one document's structure without returning field values."""

        return self.provider.analyze_learning_structure(
            evidence
        )
