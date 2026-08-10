from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from src.services.document_fingerprint_service import (
    DocumentFingerprintService,
)


@dataclass(frozen=True)
class DocumentAttachmentPreparationResult:
    prepared: bool
    temporary_path: Path | None
    success: bool
    status: str


class DocumentAttachmentNamingService:
    """
    Creates a temporary locally renamed copy for Smartsheet attachment.

    TEST CONVENTION ONLY:
    LTHHC_AUTH_TEST_<fingerprint-prefix>.<extension>

    The original source file is never renamed or modified.
    """

    PREFIX = "LTHHC_AUTH_TEST"
    FINGERPRINT_LENGTH = 12

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

        extension = (
            path.suffix.lower()
            if path.suffix
            else ".bin"
        )

        safe_name = (
            f"{self.PREFIX}_"
            f"{fingerprint_result.fingerprint[:self.FINGERPRINT_LENGTH]}"
            f"{extension}"
        )

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
            status="prepared",
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
