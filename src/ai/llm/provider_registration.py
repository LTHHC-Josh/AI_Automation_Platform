from src.ai.llm.llm_registry import LLMRegistry


def register_llm_provider(name):
    """
    Decorator used to register an LLM provider.
    """

    def decorator(provider_class):
        LLMRegistry.register(name, provider_class)
        return provider_class

    return decorator