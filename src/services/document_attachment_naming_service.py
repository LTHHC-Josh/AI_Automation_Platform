from dataclasses import dataclass, field
from pathlib import Path
import shutil
import tempfile

from src.services.document_fingerprint_service import (
    DocumentFingerprintService,
)
from src.services.filename_policy_service import FilenamePolicyResult


@dataclass(frozen=True)
class DocumentAttachmentPreparationResult:
    prepared: bool
    temporary_path: Path | None = field(repr=False)
    success: bool
    status: str


class DocumentAttachmentNamingService:
    """
    Creates a temporary locally renamed copy for Smartsheet attachment.

    Deterministic technical fallback:
    LTHHC_TECHNICAL_DOCUMENT_<full-document-fingerprint>.<extension>

    The original source file is never renamed or modified.
    """

    PREFIX = "LTHHC_TECHNICAL_DOCUMENT"
    SAFE_EXTENSIONS = {".pdf", ".tif", ".tiff", ".png", ".jpg", ".jpeg"}

    def __init__(
        self,
        *,
        fingerprint_service=None,
    ) -> None:
        self.fingerprint_service = (
            fingerprint_service
            or DocumentFingerprintService()
        )

    def prepare(
        self,
        *,
        source_path,
        filename_policy_result=None,
    ) -> DocumentAttachmentPreparationResult:
        try:
            path = Path(source_path)
        except (TypeError, ValueError):
            return self._failure(
                "invalid_source_path"
            )

        if not path.exists():
            return self._failure(
                "source_not_found"
            )

        if not path.is_file():
            return self._failure(
                "source_not_file"
            )

        fingerprint_result = (
            self.fingerprint_service.calculate(
                path
            )
        )

        if (
            not fingerprint_result.success
            or not fingerprint_result.fingerprint
        ):
            return self._failure(
                "fingerprint_failed"
            )

        extension = path.suffix.lower()
        if extension not in self.SAFE_EXTENSIONS:
            extension = ".bin"

        fallback_name = f"{self.PREFIX}_{fingerprint_result.fingerprint}{extension}"

        safe_name = fallback_name
        preparation_status = "prepared"
        if filename_policy_result is not None:
            if self._is_safe_business_policy_result(
                filename_policy_result,
                source_extension=extension,
            ):
                safe_name = filename_policy_result.filename
                preparation_status = "prepared_reference_filename"
            else:
                preparation_status = "prepared_naming_fallback_review"

        try:
            temporary_directory = Path(
                tempfile.mkdtemp(
                    prefix="lthhc_attachment_"
                )
            )

            temporary_path = (
                temporary_directory
                / safe_name
            )

            shutil.copy2(
                path,
                temporary_path,
            )
        except OSError:
            return self._failure(
                "temporary_copy_failed"
            )

        return DocumentAttachmentPreparationResult(
            prepared=True,
            temporary_path=temporary_path,
            success=True,
            status=preparation_status,
        )

    def prepare_technical(self, *, source_path, technical_name) -> DocumentAttachmentPreparationResult:
        try:
            path = Path(source_path)
            name = str(technical_name)
        except (TypeError, ValueError):
            return self._failure("invalid_technical_attachment")
        if not path.is_file() or name != Path(name).name or any(c in name for c in "\\/\r\n"):
            return self._failure("invalid_technical_attachment")
        try:
            temporary_directory = Path(tempfile.mkdtemp(prefix="lthhc_attachment_"))
            temporary_path = temporary_directory / name
            shutil.copy2(path, temporary_path)
        except OSError:
            return self._failure("temporary_copy_failed")
        return DocumentAttachmentPreparationResult(True, temporary_path, True, "prepared_technical")

    @staticmethod
    def _is_safe_business_policy_result(result, *, source_extension: str) -> bool:
        if not isinstance(result, FilenamePolicyResult):
            return False
        if (
            not result.complete
            or result.filename_result not in {"complete_business", "partial_business"}
            or not result.filename
        ):
            return False
        filename = str(result.filename)
        return (
            filename == Path(filename).name
            and not any(character in filename for character in "\\/\r\n")
            and Path(filename).suffix.lower() == source_extension.lower()
        )

    @staticmethod
    def cleanup(
        temporary_path,
    ) -> bool:
        try:
            path = Path(
                temporary_path
            )
        except (TypeError, ValueError):
            return False

        try:
            if path.exists():
                path.unlink()

            parent = path.parent

            if (
                parent.exists()
                and parent.name.startswith(
                    "lthhc_attachment_"
                )
            ):
                parent.rmdir()
        except OSError:
            return False

        return True

    @staticmethod
    def _failure(
        status,
    ) -> DocumentAttachmentPreparationResult:
        return DocumentAttachmentPreparationResult(
            prepared=False,
            temporary_path=None,
            success=False,
            status=str(status),
        )
