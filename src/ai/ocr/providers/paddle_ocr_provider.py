from pathlib import Path
import json
from collections.abc import Iterator
from importlib.metadata import PackageNotFoundError, version
import os
import re
from time import perf_counter
from typing import Any

from paddleocr import PaddleOCR

from src.ai.ocr.errors import OCRCacheOnlyMissError
from src.ai.ocr.ocr_provider import OCRProvider
from src.ai.ocr.provider_registration import register_ocr_provider
from src.models.ocr_document import OCRBlock, OCRDocument, OCRPage
from src.models.ocr_diagnostics import OCRRunDiagnostics
from src.services.document_fingerprint_service import (
    DocumentFingerprintService,
)


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

        self.fingerprint_service = (
            DocumentFingerprintService()
        )

        self.ocr = None
        self.last_run_diagnostics = OCRRunDiagnostics()

    def _create_ocr(self) -> PaddleOCR:
        """Create the Paddle engine only when prediction is required."""

        return PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            engine="paddle",
        )

    def extract_text(
        self,
        file_path: str | Path,
        *,
        cache_only: bool = False,
    ) -> str:
        return self.extract_document(
            file_path,
            cache_only=cache_only,
        ).raw_text

    def extract_document(
        self,
        file_path: str | Path,
        *,
        cache_only: bool = False,
    ) -> OCRDocument:
        """
        Extract OCR text from a supported local document.

        Document names, document paths, cache paths, and OCR text are
        intentionally excluded from console messages and exceptions.
        """

        document_path = Path(
            file_path
        )

        diagnostics = OCRRunDiagnostics(
            input_type=("pdf" if document_path.suffix.lower() == ".pdf" else "raster"),
            configuration={
                "language": "en",
                "doc_orientation_classification": False,
                "document_unwarping": False,
                "textline_orientation": False,
                "engine": "paddle",
            },
            thread_counts={
                "omp": self._safe_thread_count("OMP_NUM_THREADS"),
                "mkl": self._safe_thread_count("MKL_NUM_THREADS"),
            },
            batch_metadata={"batch_size": "unknown"},
            render_metadata={"dpi": "unknown", "scale": "unknown"},
        )
        self.last_run_diagnostics = diagnostics

        self._validate_document_path(
            document_path
        )

        fingerprint_started_at = perf_counter()
        fingerprint_result = (
            self.fingerprint_service.calculate(
                document_path
            )
        )
        diagnostics.fingerprint_seconds = perf_counter() - fingerprint_started_at
        diagnostics.file_size_bucket = self._file_size_bucket(
            fingerprint_result.byte_count
        )

        if (
            not fingerprint_result.success
            or fingerprint_result.fingerprint is None
        ):
            raise RuntimeError(
                "The local document could not be read for OCR "
                "processing."
            )

        document_hash = fingerprint_result.fingerprint

        cache_path = self._get_cache_path(
            document_hash
        )

        structured_cache_path = self._get_structured_cache_path(document_hash)
        cache_started_at = perf_counter()
        structured_document = self._read_structured_cache(structured_cache_path)
        diagnostics.cache_lookup_seconds["structured"] = (
            perf_counter() - cache_started_at
        )
        if structured_document is not None:
            diagnostics.cache_category = "structured_hit"
            print("Using cached OCR text for local document.")
            return structured_document

        cache_started_at = perf_counter()
        cached_text = self._read_cache(
            cache_path
        )
        diagnostics.cache_lookup_seconds["flat"] = perf_counter() - cache_started_at

        if cached_text:
            diagnostics.cache_category = "flat_hit"
            print(
                "Using cached OCR text for local document."
            )

            return OCRDocument.from_flat_text(cached_text)

        legacy_cache_path = self._get_legacy_cache_path(
            document_path=document_path,
            document_hash=document_hash,
        )

        cache_started_at = perf_counter()
        legacy_cached_text = self._read_cache(
            legacy_cache_path
        )
        diagnostics.cache_lookup_seconds["legacy"] = perf_counter() - cache_started_at

        if legacy_cached_text:
            diagnostics.cache_category = "legacy_hit"
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

            return OCRDocument.from_flat_text(legacy_cached_text)

        if cache_only:
            diagnostics.cache_category = "miss"
            raise OCRCacheOnlyMissError(
                "OCR cache is unavailable."
            ) from None

        print(
            "No OCR cache found. Processing local document "
            "with PaddleOCR."
        )
        diagnostics.cache_category = "miss"

        if self.ocr is None:
            init_started_at = perf_counter()
            diagnostics.engine_creation_count += 1
            self.ocr = self._create_ocr()
            diagnostics.engine_init_seconds = perf_counter() - init_started_at
        self._capture_runtime_metadata(diagnostics)

        try:
            predict_started_at = perf_counter()
            diagnostics.predict_call_count += 1
            diagnostics.document_submission_count += 1
            results = self.ocr.predict(
                str(
                    document_path
                )
            )
            diagnostics.predict_return_seconds = perf_counter() - predict_started_at
        except Exception as ex:
            raise RuntimeError(
                "PaddleOCR failed to process the local document. "
                f"Error type: {type(ex).__name__}."
            ) from ex

        extracted_pages: list[OCRPage] = []
        global_order = 0
        result_iterator = iter(results)
        diagnostics.result_behavior = (
            "lazy" if isinstance(results, Iterator) else "eager"
        )
        consumption_started_at = perf_counter()
        page_number = 0
        seen_page_ordinals: set[int] = set()

        while True:
            yield_started_at = perf_counter()
            try:
                result = next(result_iterator)
            except StopIteration:
                break
            yield_seconds = perf_counter() - yield_started_at
            page_number += 1
            diagnostics.result_count += 1
            if page_number in seen_page_ordinals:
                diagnostics.page_ordinals_unique = False
            seen_page_ordinals.add(page_number)

            conversion_started_at = perf_counter()
            result_data = self._result_to_dict(
                result
            )
            conversion_seconds = perf_counter() - conversion_started_at
            diagnostics.result_conversion_count += 1
            diagnostics.result_conversion_seconds += conversion_seconds

            traversal_started_at = perf_counter()
            diagnostics.recognized_text_traversal_count += 1
            recognized_texts = (
                self._find_recognized_texts(
                    result_data,
                    diagnostics=diagnostics,
                )
            )
            traversal_seconds = perf_counter() - traversal_started_at
            diagnostics.recognized_text_traversal_seconds += traversal_seconds

            construction_started_at = perf_counter()
            page_blocks: list[OCRBlock] = []
            for text in recognized_texts:
                cleaned_text = str(
                    text
                ).strip()

                if cleaned_text:
                    global_order += 1
                    page_blocks.append(OCRBlock(
                        block_id=f"page_{page_number}_block_{len(page_blocks) + 1}",
                        text=cleaned_text,
                        reading_order=global_order,
                    ))

            extracted_pages.append(OCRPage(
                page_number=page_number,
                blocks=tuple(page_blocks),
            ))
            construction_seconds = perf_counter() - construction_started_at
            diagnostics.page_block_construction_seconds += construction_seconds
            diagnostics.recognized_block_count += len(page_blocks)
            diagnostics.page_timings.append({
                "page_ordinal": page_number,
                "result_yield_seconds": yield_seconds,
                "conversion_seconds": conversion_seconds,
                "traversal_seconds": traversal_seconds,
                "construction_seconds": construction_seconds,
            })

        diagnostics.result_consumption_seconds = perf_counter() - consumption_started_at
        self._update_execution_invariants(diagnostics)

        assembly_started_at = perf_counter()
        ocr_document = OCRDocument(
            pages=tuple(extracted_pages),
            relationship_status="preserved",
        )
        full_text = ocr_document.raw_text
        diagnostics.flat_text_assembly_seconds = perf_counter() - assembly_started_at

        if not full_text:
            raise RuntimeError(
                "PaddleOCR completed but did not recognize any text "
                "in the local document."
            )

        calls_before_writes = diagnostics.predict_call_count
        flat_write_started_at = perf_counter()
        cache_written = self._write_cache(
            cache_path=cache_path,
            text=full_text,
        )
        diagnostics.flat_cache_write_seconds = perf_counter() - flat_write_started_at
        diagnostics.flat_serialized_size_bucket = self._serialized_size_bucket(
            len(full_text.encode("utf-8"))
        )

        if cache_written:
            print(
                "Saved OCR text to the secured local cache."
            )

        serialization_started_at = perf_counter()
        structured_payload = json.dumps(
            ocr_document.to_protected_cache_dict(), separators=(",", ":")
        )
        diagnostics.structured_serialization_seconds = (
            perf_counter() - serialization_started_at
        )
        diagnostics.structured_serialized_size_bucket = self._serialized_size_bucket(
            len(structured_payload.encode("utf-8"))
        )
        structured_write_started_at = perf_counter()
        self._write_structured_cache_payload(
            cache_path=structured_cache_path,
            payload=structured_payload,
        )
        diagnostics.structured_cache_write_seconds = (
            perf_counter() - structured_write_started_at
        )
        diagnostics.extra_predict_calls_during_cache_writes = (
            diagnostics.predict_call_count - calls_before_writes
        )
        diagnostics.application_source_rereads_during_cache_writes = 0
        self._update_execution_invariants(diagnostics)

        return ocr_document

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

    def _get_structured_cache_path(self, document_hash: str) -> Path:
        return self.CACHE_DIRECTORY / f"{document_hash}.ocr.json"

    def _read_structured_cache(self, cache_path: Path) -> OCRDocument | None:
        if not cache_path.exists():
            return None
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return OCRDocument.from_protected_cache_dict(payload)

    def _write_structured_cache(
        self,
        *,
        cache_path: Path,
        document: OCRDocument,
    ) -> bool:
        payload = json.dumps(
            document.to_protected_cache_dict(), separators=(",", ":")
        )
        return self._write_structured_cache_payload(
            cache_path=cache_path,
            payload=payload,
        )

    def _write_structured_cache_payload(
        self,
        *,
        cache_path: Path,
        payload: str,
    ) -> bool:
        try:
            cache_path.write_text(
                payload,
                encoding="utf-8",
            )
        except OSError:
            return False
        return True

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
        *,
        diagnostics: OCRRunDiagnostics | None = None,
    ) -> list[str]:
        """
        Recursively locate PaddleOCR recognized-text arrays.
        """

        recognized_texts: list[str] = []

        if isinstance(
            value,
            dict,
        ):
            if diagnostics is not None:
                diagnostics.visited_container_count += 1
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
                        nested_value,
                        diagnostics=diagnostics,
                    )
                )

        elif isinstance(
            value,
            list,
        ):
            if diagnostics is not None:
                diagnostics.visited_container_count += 1
            for nested_value in value:
                recognized_texts.extend(
                    self._find_recognized_texts(
                        nested_value,
                        diagnostics=diagnostics,
                    )
                )

        return recognized_texts

    @staticmethod
    def _safe_thread_count(name: str) -> int | None:
        value = os.environ.get(name)
        try:
            count = int(value) if value is not None else None
        except (TypeError, ValueError):
            return None
        return count if count is not None and 0 < count <= 4096 else None

    @staticmethod
    def _file_size_bucket(byte_count: int) -> str:
        if byte_count < 1024 * 1024:
            return "under_1_mib"
        if byte_count < 10 * 1024 * 1024:
            return "1_to_10_mib"
        if byte_count < 50 * 1024 * 1024:
            return "10_to_50_mib"
        if byte_count < 200 * 1024 * 1024:
            return "50_to_200_mib"
        return "200_mib_or_more"

    @staticmethod
    def _serialized_size_bucket(byte_count: int) -> str:
        if byte_count < 64 * 1024:
            return "under_64_kib"
        if byte_count < 256 * 1024:
            return "64_to_256_kib"
        if byte_count < 1024 * 1024:
            return "256_kib_to_1_mib"
        if byte_count < 10 * 1024 * 1024:
            return "1_to_10_mib"
        return "10_mib_or_more"

    @staticmethod
    def _package_version(package_name: str) -> str:
        try:
            package_version = version(package_name)
        except PackageNotFoundError:
            return "unknown"
        return (
            package_version
            if re.fullmatch(r"[0-9A-Za-z.+-]{1,40}", package_version)
            else "unknown"
        )

    def _capture_runtime_metadata(self, diagnostics: OCRRunDiagnostics) -> None:
        diagnostics.paddle_version = self._package_version("paddlepaddle")
        diagnostics.paddleocr_version = self._package_version("paddleocr")
        self._capture_effective_paddleocr_settings(diagnostics)
        try:
            import paddle

            raw_device = str(paddle.device.get_device()).lower()
            diagnostics.device_type = next(
                (item for item in ("cpu", "gpu", "xpu") if raw_device.startswith(item)),
                "unknown",
            )
        except (AttributeError, RuntimeError, TypeError, ValueError):
            diagnostics.device_type = "unknown"
        diagnostics.global_flags_use_mkldnn = self._read_global_paddle_flag()

    def _capture_effective_paddleocr_settings(
        self,
        diagnostics: OCRRunDiagnostics,
    ) -> None:
        common_args = getattr(self.ocr, "_common_args", None)
        if not isinstance(common_args, dict):
            return

        enable_mkldnn = common_args.get("enable_mkldnn")
        if isinstance(enable_mkldnn, bool):
            diagnostics.effective_paddleocr_enable_mkldnn = enable_mkldnn

        cpu_threads = common_args.get("cpu_threads")
        if (
            isinstance(cpu_threads, int)
            and not isinstance(cpu_threads, bool)
            and 0 < cpu_threads <= 4096
        ):
            diagnostics.effective_cpu_threads = cpu_threads

        cache_capacity = common_args.get("mkldnn_cache_capacity")
        if (
            isinstance(cache_capacity, int)
            and not isinstance(cache_capacity, bool)
            and 0 <= cache_capacity <= 1_000_000
        ):
            diagnostics.effective_mkldnn_cache_capacity = cache_capacity

        engine = common_args.get("engine")
        if engine in {
            "paddle",
            "paddle_static",
            "paddle_dynamic",
            "transformers",
            "onnxruntime",
        }:
            diagnostics.effective_inference_engine = engine

    @staticmethod
    def _read_global_paddle_flag() -> bool | None:
        try:
            import paddle

            flags = paddle.get_flags(["FLAGS_use_mkldnn"])
            flag_value = flags.get("FLAGS_use_mkldnn")
            return flag_value if isinstance(flag_value, bool) else None
        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
            return None

    @staticmethod
    def _update_execution_invariants(diagnostics: OCRRunDiagnostics) -> None:
        diagnostics.repeated_conversion_detected = (
            diagnostics.result_conversion_count != diagnostics.result_count
        )
        diagnostics.repeated_prediction_detected = (
            diagnostics.predict_call_count != 1
            or diagnostics.document_submission_count != 1
        )
