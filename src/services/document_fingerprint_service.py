from dataclasses import dataclass
import hashlib
from pathlib import Path


@dataclass(frozen=True)
class DocumentFingerprintResult:
    """
    PHI-safe result from hashing one local document.

    The contract deliberately excludes source path, filename, document
    content, OCR text, extracted values, and exception messages.
    """

    fingerprint: str | None
    byte_count: int
    success: bool
    status: str


class DocumentFingerprintService:
    """
    Calculates a SHA-256 fingerprint for one local file.

    Files are read locally in fixed-size chunks. No document path,
    filename, content, OCR text, or extracted value is logged or
    returned.
    """

    CHUNK_SIZE = 1024 * 1024

    def calculate(
        self,
        source_path: str | Path,
    ) -> DocumentFingerprintResult:
        try:
            path = Path(source_path)
        except (TypeError, ValueError):
            return self._failure("invalid_path")

        if not path.exists():
            return self._failure("not_found")

        if not path.is_file():
            return self._failure("not_a_file")

        hasher = hashlib.sha256()
        byte_count = 0

        try:
            with path.open("rb") as document_file:
                while True:
                    chunk = document_file.read(self.CHUNK_SIZE)

                    if not chunk:
                        break

                    hasher.update(chunk)
                    byte_count += len(chunk)
        except OSError:
            return self._failure("read_failed")

        return DocumentFingerprintResult(
            fingerprint=hasher.hexdigest(),
            byte_count=byte_count,
            success=True,
            status="calculated",
        )

    @staticmethod
    def _failure(
        status: str,
    ) -> DocumentFingerprintResult:
        return DocumentFingerprintResult(
            fingerprint=None,
            byte_count=0,
            success=False,
            status=status,
        )
