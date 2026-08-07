from dataclasses import dataclass, field
from pathlib import Path

from src.document_processing.document_processor import (
    DocumentProcessor,
)
from src.models.document import Document
from src.services.mailbox_processing_state_service import (
    MailboxProcessingStateService,
)

from .attachment_service import AttachmentService
from .email_service import EmailService


SUPPORTED_FILE_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
}


@dataclass
class MessageProcessingResult:
    message_id: str
    subject: str
    downloaded_files: list[Path] = field(
        default_factory=list
    )
    processed_documents: list[Document] = field(
        default_factory=list
    )
    skipped_files: list[Path] = field(
        default_factory=list
    )
    errors: list[str] = field(
        default_factory=list
    )
    marked_as_read: bool = False

    @property
    def succeeded(self) -> bool:
        return (
            bool(self.processed_documents)
            and not self.errors
        )


class MailboxProcessor:
    """
    Coordinates Microsoft Graph mailbox ingestion with
    DocumentProcessor.

    Pipeline:

        Unread email
            -> Check durable local message state
            -> Download non-inline attachments
            -> Filter supported document types
            -> DocumentProcessor
            -> OCR
            -> Classification
            -> Structured extraction
            -> Record durable handled state
            -> Mark email as read

    Messages already recorded as handled skip attachment download and
    document processing and only retry the mark-read operation.

    Messages that contain no processable document are recorded as
    handled and marked read after successful inspection.

    Processing, download, and local state failures remain unread for
    retry.
    """

    def __init__(
        self,
        email_service: EmailService | None = None,
        attachment_service: AttachmentService | None = None,
        document_processor: DocumentProcessor | None = None,
        processing_state_service: (
            MailboxProcessingStateService
            | None
        ) = None,
    ):
        self.email_service = (
            email_service or EmailService()
        )

        self.attachment_service = (
            attachment_service
            or AttachmentService()
        )

        self.document_processor = (
            document_processor
            or DocumentProcessor()
        )

        self.processing_state_service = (
            processing_state_service
            or MailboxProcessingStateService()
        )

    def is_supported_file(
        self,
        file_path: Path,
    ) -> bool:
        return (
            file_path.suffix.lower()
            in SUPPORTED_FILE_EXTENSIONS
        )

    def process_unread_messages(
        self,
        top: int = 10,
    ) -> list[MessageProcessingResult]:
        messages = (
            self.email_service
            .get_unread_messages(top=top)
        )

        results: list[
            MessageProcessingResult
        ] = []

        for message in messages:
            result = self.process_message(
                message
            )

            results.append(result)

        return results

    def process_message(
        self,
        message: dict,
    ) -> MessageProcessingResult:
        message_id = message.get(
            "id",
            "",
        )

        subject = message.get(
            "subject",
            "(No subject)",
        )

        result = MessageProcessingResult(
            message_id=message_id,
            subject=subject,
        )

        if not message_id:
            result.errors.append(
                "Message does not contain an ID."
            )

            return result

        state_result = (
            self.processing_state_service
            .check(
                message_id
            )
        )

        if not state_result.success:
            result.errors.append(
                "Mailbox processing state "
                "could not be checked."
            )

            return result

        if state_result.handled:
            self._mark_as_read(
                result
            )

            return result

        if not message.get(
            "hasAttachments",
            False,
        ):
            self._complete_handled_message(
                result
            )

            return result

        try:
            downloaded_files = (
                self.attachment_service
                .download_file_attachments(
                    message_id
                )
            )

            result.downloaded_files.extend(
                downloaded_files
            )

        except Exception:
            result.errors.append(
                "Attachment download failed."
            )

            return result

        for downloaded_file in (
            result.downloaded_files
        ):
            file_path = Path(
                downloaded_file
            )

            if not self.is_supported_file(
                file_path
            ):
                result.skipped_files.append(
                    file_path
                )

                continue

            try:
                document = (
                    self.document_processor
                    .process(
                        file_path
                    )
                )

                result.processed_documents.append(
                    document
                )

            except Exception:
                result.errors.append(
                    "Document processing failed."
                )

        if (
            result.succeeded
            or (
                not result.processed_documents
                and not result.errors
            )
        ):
            self._complete_handled_message(
                result
            )

        return result

    def _complete_handled_message(
        self,
        result: MessageProcessingResult,
    ) -> None:
        state_result = (
            self.processing_state_service
            .mark_handled(
                result.message_id
            )
        )

        if not state_result.success:
            result.errors.append(
                "Mailbox processing state "
                "could not be stored."
            )

            return

        self._mark_as_read(
            result
        )

    def _mark_as_read(
        self,
        result: MessageProcessingResult,
    ) -> None:
        try:
            marked_as_read = (
                self.email_service
                .mark_as_read(
                    result.message_id
                )
            )

            result.marked_as_read = (
                marked_as_read is True
            )

            if not result.marked_as_read:
                result.errors.append(
                    "Email could not be marked as read."
                )

        except Exception:
            result.errors.append(
                "Email could not be marked as read."
            )
