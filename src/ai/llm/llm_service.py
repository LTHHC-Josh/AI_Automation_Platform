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
    ) -> dict:
        """
        Extract structured data from OCR text.
        """

        return self.provider.extract(
            text,
            prompt,
        )