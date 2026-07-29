from src.ai import config
from src.ai.provider_loader import ProviderLoader
from src.ai.ocr.ocr_registry import OCRRegistry
import src.ai.ocr.providers as providers


class OCRFactory:
    """
    Creates the configured OCR provider.
    """

    @staticmethod
    def create():

        ProviderLoader.load(providers)

        return OCRRegistry.get(config.OCR_PROVIDER)