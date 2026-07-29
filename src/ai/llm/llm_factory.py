from src.ai import config
from src.ai.provider_loader import ProviderLoader
from src.ai.llm.llm_registry import LLMRegistry
import src.ai.llm.providers as providers


class LLMFactory:
    """
    Creates the configured LLM provider.
    """

    @staticmethod
    def create():

        ProviderLoader.load(providers)

        return LLMRegistry.get(config.LLM_PROVIDER)