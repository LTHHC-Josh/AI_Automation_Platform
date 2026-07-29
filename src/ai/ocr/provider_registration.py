from src.ai.ocr.ocr_registry import OCRRegistry


def register_ocr_provider(name):
    """
    Decorator used to register an OCR provider.
    """

    def decorator(provider_class):
        OCRRegistry.register(name, provider_class)
        return provider_class

    return decorator