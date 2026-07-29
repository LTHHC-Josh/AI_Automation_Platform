class LLMRegistry:
    """
    Registry of available LLM providers.
    """

    _providers = {}

    @classmethod
    def register(cls, name, provider_class):
        cls._providers[name] = provider_class

    @classmethod
    def get(cls, name):

        provider = cls._providers.get(name)

        if provider is None:
            raise ValueError(
                f"Unknown LLM provider: {name}"
            )

        return provider()