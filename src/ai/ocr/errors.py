class OCRCacheOnlyMissError(RuntimeError):
    """
    Raised when explicitly requested cached OCR text is unavailable.

    The message is application-owned and must not contain a document or
    cache path, filename, OCR text, or provider diagnostic.
    """
