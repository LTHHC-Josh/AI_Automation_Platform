from src.ai.llm.llm_provider import LLMProvider
from src.ai.llm.provider_registration import register_llm_provider


@register_llm_provider("mock")
class MockProvider(LLMProvider):
    """
    Mock LLM provider used for development.

    The attempt parameter is accepted for compatibility with the shared
    provider interface. It does not change the deterministic mock result.
    """

    def classify(
        self,
        text: str,
    ) -> dict:
        return {
            "document_category": "authorization",
            "document_subtype": "initial",
            "document_type": "authorization",
            "confidence": 0.95,
            "reason": (
                "Synthetic mock classification for interface testing."
            ),
        }

    def extract(
        self,
        text: str,
        prompt: str,
        attempt: int = 1,
    ) -> dict:
        return {
            "patient_name": "John Smith",
            "payer": "Humana",
            "authorization_number": "A123456",
            "approved_visits": 12,
        }