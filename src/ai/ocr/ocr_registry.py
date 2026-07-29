class OCRRegistry:
    """
    Registry of available OCR providers.
    """

    _providers = {}

    @classmethod
    def register(cls, name, provider_class):
        cls._providers[name] = provider_class

    @classmethod
    def get(cls, name):
        """
        Return the registered provider class.
        """

        provider_class = cls._providers.get(name)

        if provider_class is None:
            raise ValueError(
                f"Unknown OCR provider: {name}"
            )

        return provider_class