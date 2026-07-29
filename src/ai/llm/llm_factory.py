from src.ai import config
from src.ai.provider_loader import ProviderLoader

import src.ai.llm.providers as providers

from src.ai.llm.llm_registry import LLMRegistry


class LLMFactory:
    """
    Creates the configured LLM provider.
    """

    @staticmethod
    def create():
        """
        Create the configured LLM provider instance.
        """

        ProviderLoader.load(providers)

        provider_class = LLMRegistry.get(config.LLM_PROVIDER)

        if provider_class is None:
            raise ValueError(
                f"No LLM provider registered with the name "
                f"'{config.LLM_PROVIDER}'."
            )

        return provider_class()