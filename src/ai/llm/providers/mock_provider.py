from src.ai.llm.llm_provider import LLMProvider
from src.ai.llm.provider_registration import register_llm_provider


@register_llm_provider("mock")
class MockProvider(LLMProvider):
    """
    Mock LLM provider used for development.
    """

    def classify(self, text):
        return {
            "document_type": "Authorization",
            "confidence": 1.0,
        }

    def extract(self, text, prompt):
        return {
            "patient_name": "John Smith",
            "payer": "Humana",
            "authorization_number": "A123456",
            "approved_visits": 12,
        }