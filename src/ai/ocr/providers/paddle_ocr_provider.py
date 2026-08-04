import hashlib
from pathlib import Path
from typing import Any

from paddleocr import PaddleOCR

from src.ai.ocr.ocr_provider import OCRProvider
from src.ai.ocr.provider_registration import register_ocr_provider


@register_ocr_provider("paddle")
class PaddleOCRProvider(OCRProvider):
    """
    Runs local PaddleOCR against images and scanned PDFs.

    Extracted OCR text is cached locally so unchanged documents do not
    need to be processed by PaddleOCR again during testing.

    Cache location:
        data/ocr_cache

    Cache filenames use only the document SHA-256 hash. Original
    document names are not included because filenames may contain PHI.

    The cache may contain protected health information and must remain
    inside the secured local environment.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp",
    }

    CACHE_DIRECTORY = Path(
        "data/ocr_cache"
    )

    def __init__(self) -> None:
        self.CACHE_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.ocr = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            engine="paddle",
        )

    def extract_text(
        self,
        file_path: str | Path,
    ) -> str:
        """
        Extract OCR text from a supported local document.

        Document names, document paths, cache paths, and OCR text are
        intentionally excluded from console messages and exceptions.
        """

        document_path = Path(
            file_path
        )

        self._validate_document_path(
            document_path
        )

        document_hash = self._calculate_file_hash(
            document_path
        )

        cache_path = self._get_cache_path(
            document_hash
        )

        cached_text = self._read_cache(
            cache_path
        )

        if cached_text:
            print(
                "Using cached OCR text for local document."
            )

            return cached_text

        legacy_cache_path = self._get_legacy_cache_path(
            document_path=document_path,
            document_hash=document_hash,
        )

        legacy_cached_text = self._read_cache(
            legacy_cache_path
        )

        if legacy_cached_text:
            migration_succeeded = self._write_cache(
                cache_path=cache_path,
                text=legacy_cached_text,
            )

            if migration_succeeded:
                self._remove_legacy_cache(
                    legacy_cache_path
                )

            print(
                "Using cached OCR text for local document."
            )

            return legacy_cached_text

        print(
            "No OCR cache found. Processing local document "
            "with PaddleOCR."
        )

        try:
            results = self.ocr.predict(
                str(
                    document_path
                )
            )
        except Exception as ex:
            raise RuntimeError(
                "PaddleOCR failed to process the local document. "
                f"Error type: {type(ex).__name__}."
            ) from ex

        extracted_lines: list[str] = []

        for result in results:
            result_data = self._result_to_dict(
                result
            )

            recognized_texts = (
                self._find_recognized_texts(
                    result_data
                )
            )

            for text in recognized_texts:
                cleaned_text = str(
                    text
                ).strip()

                if cleaned_text:
                    extracted_lines.append(
                        cleaned_text
                    )

        full_text = "\n".join(
            extracted_lines
        ).strip()

        if not full_text:
            raise RuntimeError(
                "PaddleOCR completed but did not recognize any text "
                "in the local document."
            )

        cache_written = self._write_cache(
            cache_path=cache_path,
            text=full_text,
        )

        if cache_written:
            print(
                "Saved OCR text to the secured local cache."
            )

        return full_text

    def _validate_document_path(
        self,
        document_path: Path,
    ) -> None:
        """
        Validate the input path without exposing it in exceptions.
        """

        if not document_path.exists():
            raise FileNotFoundError(
                "The local document file was not found."
            )

        if not document_path.is_file():
            raise ValueError(
                "The local document path is not a file."
            )

        extension = (
            document_path.suffix.lower()
        )

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "PaddleOCRProvider does not support the local "
                "document type."
            )

    def _get_cache_path(
        self,
        document_hash: str,
    ) -> Path:
        """
        Build a cache path using only the SHA-256 document hash.
        """

        cache_filename = (
            f"{document_hash}.txt"
        )

        return (
            self.CACHE_DIRECTORY
            / cache_filename
        )

    def _get_legacy_cache_path(
        self,
        document_path: Path,
        document_hash: str,
    ) -> Path:
        """
        Build the former filename-based cache path for local migration.

        This path must never be logged because the source stem may
        contain PHI.
        """

        safe_stem = self._safe_filename(
            document_path.stem
        )

        legacy_cache_filename = (
            f"{safe_stem}_{document_hash[:16]}.txt"
        )

        return (
            self.CACHE_DIRECTORY
            / legacy_cache_filename
        )

    def _calculate_file_hash(
        self,
        document_path: Path,
    ) -> str:
        hasher = hashlib.sha256()

        try:
            with document_path.open(
                "rb"
            ) as document_file:
                while True:
                    chunk = document_file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    hasher.update(
                        chunk
                    )
        except OSError as ex:
            raise RuntimeError(
                "The local document could not be read for OCR "
                f"processing. Error type: {type(ex).__name__}."
            ) from ex

        return hasher.hexdigest()

    def _safe_filename(
        self,
        value: str,
    ) -> str:
        """
        Reproduce the former cache naming format for migration only.
        """

        safe_characters: list[str] = []

        for character in value:
            if (
                character.isalnum()
                or character in {
                    "-",
                    "_",
                }
            ):
                safe_characters.append(
                    character
                )
            else:
                safe_characters.append(
                    "_"
                )

        safe_value = "".join(
            safe_characters
        ).strip("_")

        if not safe_value:
            return "document"

        return safe_value[:100]

    def _read_cache(
        self,
        cache_path: Path,
    ) -> str | None:
        if not cache_path.exists():
            return None

        try:
            cached_text = cache_path.read_text(
                encoding="utf-8"
            ).strip()
        except OSError as ex:
            print(
                "Unable to read the secured local OCR cache. "
                "PaddleOCR will run again. "
                f"Error type: {type(ex).__name__}."
            )

            return None

        if not cached_text:
            return None

        return cached_text

    def _write_cache(
        self,
        cache_path: Path,
        text: str,
    ) -> bool:
        try:
            cache_path.write_text(
                text,
                encoding="utf-8",
            )
        except OSError as ex:
            print(
                "Warning: OCR succeeded, but the secured local "
                "cache could not be written. "
                f"Error type: {type(ex).__name__}."
            )

            return False

        return True

    def _remove_legacy_cache(
        self,
        legacy_cache_path: Path,
    ) -> None:
        """
        Remove a filename-based legacy cache after successful migration.

        Failure to remove it does not invalidate the migrated cache.
        """

        try:
            legacy_cache_path.unlink(
                missing_ok=True
            )
        except OSError as ex:
            print(
                "Warning: The legacy OCR cache entry could not be "
                "removed after migration. "
                f"Error type: {type(ex).__name__}."
            )

    def _result_to_dict(
        self,
        result: Any,
    ) -> dict:
        """
        Convert a PaddleOCR result object into a dictionary.

        PaddleOCR 3.x result objects may expose their structured result
        through either a json property or a res property.
        """

        json_value = getattr(
            result,
            "json",
            None,
        )

        if callable(
            json_value
        ):
            json_value = json_value()

        if isinstance(
            json_value,
            dict,
        ):
            return json_value

        result_value = getattr(
            result,
            "res",
            None,
        )

        if isinstance(
            result_value,
            dict,
        ):
            return {
                "res": result_value,
            }

        if isinstance(
            result,
            dict,
        ):
            return result

        return {}

    def _find_recognized_texts(
        self,
        value: Any,
    ) -> list[str]:
        """
        Recursively locate PaddleOCR recognized-text arrays.
        """

        recognized_texts: list[str] = []

        if isinstance(
            value,
            dict,
        ):
            rec_texts = value.get(
                "rec_texts"
            )

            if isinstance(
                rec_texts,
                list,
            ):
                recognized_texts.extend(
                    str(
                        text
                    )
                    for text in rec_texts
                    if text is not None
                )

            for nested_value in value.values():
                recognized_texts.extend(
                    self._find_recognized_texts(
                        nested_value
                    )
                )

        elif isinstance(
            value,
            list,
        ):
            for nested_value in value:
                recognized_texts.extend(
                    self._find_recognized_texts(
                        nested_value
                    )
                )

        return recognized_texts