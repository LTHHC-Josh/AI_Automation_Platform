from src.ai import config
from src.ai.provider_loader import ProviderLoader

import src.ai.ocr.providers as providers

from src.ai.ocr.ocr_registry import OCRRegistry


class OCRFactory:
    """
    Creates the configured OCR provider.
    """

    @staticmethod
    def create():
        """
        Create the configured OCR provider instance.
        """

        ProviderLoader.load(providers)

        provider_class = OCRRegistry.get(config.OCR_PROVIDER)

        if provider_class is None:
            raise ValueError(
                f"No OCR provider registered with the name "
                f"'{config.OCR_PROVIDER}'."
            )

        return provider_class()