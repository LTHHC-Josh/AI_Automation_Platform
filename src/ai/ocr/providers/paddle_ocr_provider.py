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
        file_path,
    ) -> str:
        document_path = Path(file_path)

        self._validate_document_path(
            document_path
        )

        cache_path = self._get_cache_path(
            document_path
        )

        cached_text = self._read_cache(
            cache_path
        )

        if cached_text:
            print(
                "Using cached OCR text: "
                f"{cache_path}"
            )

            return cached_text

        print(
            "No OCR cache found. "
            f"Processing with PaddleOCR: {document_path.name}"
        )

        try:
            results = self.ocr.predict(
                str(document_path)
            )
        except Exception as ex:
            raise RuntimeError(
                "PaddleOCR failed to process "
                f"{document_path.name}: {ex}"
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
                f"in {document_path.name}."
            )

        self._write_cache(
            cache_path=cache_path,
            text=full_text,
        )

        print(
            "Saved OCR text to local cache: "
            f"{cache_path}"
        )

        return full_text

    def _validate_document_path(
        self,
        document_path: Path,
    ) -> None:
        if not document_path.exists():
            raise FileNotFoundError(
                "Document file was not found: "
                f"{document_path}"
            )

        if not document_path.is_file():
            raise ValueError(
                "Document path is not a file: "
                f"{document_path}"
            )

        extension = (
            document_path.suffix.lower()
        )

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "PaddleOCRProvider does not support "
                f"{extension or 'files without an extension'}."
            )

    def _get_cache_path(
        self,
        document_path: Path,
    ) -> Path:
        document_hash = self._calculate_file_hash(
            document_path
        )

        safe_stem = self._safe_filename(
            document_path.stem
        )

        cache_filename = (
            f"{safe_stem}_{document_hash[:16]}.txt"
        )

        return (
            self.CACHE_DIRECTORY
            / cache_filename
        )

    def _calculate_file_hash(
        self,
        document_path: Path,
    ) -> str:
        hasher = hashlib.sha256()

        with document_path.open(
            "rb"
        ) as document_file:
            while True:
                chunk = document_file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                hasher.update(chunk)

        return hasher.hexdigest()

    def _safe_filename(
        self,
        value: str,
    ) -> str:
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
                "Unable to read OCR cache. "
                f"PaddleOCR will run again: {ex}"
            )

            return None

        if not cached_text:
            return None

        return cached_text

    def _write_cache(
        self,
        cache_path: Path,
        text: str,
    ) -> None:
        try:
            cache_path.write_text(
                text,
                encoding="utf-8",
            )
        except OSError as ex:
            print(
                "Warning: OCR succeeded, but the local cache "
                f"could not be written: {ex}"
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

        if callable(json_value):
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
                    str(text)
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