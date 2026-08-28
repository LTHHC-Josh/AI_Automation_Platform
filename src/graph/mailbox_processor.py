from dataclasses import dataclass, field
from pathlib import Path

from src.document_processing.document_processor import (
    DocumentProcessor,
)
from src.models.document import Document
from src.services.mailbox_processing_state_service import (
    MailboxProcessingStateService,
)
from src.services.mailbox_document_job_state_service import (
    MailboxDocumentJobStateService,
    MailboxDocumentWorkItem,
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


class MailboxAcceptanceGuardError(RuntimeError):
    """Fail-closed manual-acceptance refusal with aggregate counts only."""

    def __init__(self, category, *, message_count=None, document_count=None):
        super().__init__(category)
        self.category = category
        self.message_count = message_count
        self.document_count = document_count


@dataclass
class MessageProcessingResult:
    message_id: str = field(repr=False)
    subject: str = field(repr=False)
    downloaded_files: list[Path] = field(
        default_factory=list, repr=False
    )
    processed_documents: list[Document] = field(
        default_factory=list, repr=False
    )
    skipped_files: list[Path] = field(
        default_factory=list, repr=False
    )
    errors: list[str] = field(
        default_factory=list
    )
    marked_as_read: bool = False
    work_items: list[MailboxDocumentWorkItem] = field(default_factory=list, repr=False)
    business_actions_completed: bool = False

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
        job_state_service: MailboxDocumentJobStateService | None = None,
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
        self.job_state_service = job_state_service or MailboxDocumentJobStateService()

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
        *,
        acceptance_max_messages: int | None = None,
        acceptance_max_documents: int | None = None,
        stage_observer=None,
    ) -> list[MessageProcessingResult]:
        guarded = acceptance_max_messages is not None or acceptance_max_documents is not None
        discovery_top = top + 1 if guarded else top
        started_at = __import__("time").perf_counter()
        messages = self.email_service.get_unread_messages(top=discovery_top)
        if not isinstance(messages, list):
            raise MailboxAcceptanceGuardError("acceptance_count_unproven")
        self._observe(stage_observer, "mailbox_discovery", "completed", started_at,
                      candidate_message_count=len(messages))

        if guarded:
            if not isinstance(acceptance_max_messages, int) or acceptance_max_messages < 1:
                raise MailboxAcceptanceGuardError("acceptance_policy_invalid")
            if not isinstance(acceptance_max_documents, int) or acceptance_max_documents < 1:
                raise MailboxAcceptanceGuardError("acceptance_policy_invalid")
            if len(messages) > acceptance_max_messages:
                raise MailboxAcceptanceGuardError(
                    "acceptance_message_limit_exceeded", message_count=len(messages))
            document_count = 0
            for message in messages:
                message_id = message.get("id") if isinstance(message, dict) else None
                if not isinstance(message_id, str) or not message_id:
                    raise MailboxAcceptanceGuardError(
                        "acceptance_count_unproven", message_count=len(messages))
                count_result = self.attachment_service.count_supported_file_attachments(
                    message_id, supported_extensions=SUPPORTED_FILE_EXTENSIONS)
                if not getattr(count_result, "success", False) or not isinstance(
                    getattr(count_result, "count", None), int
                ):
                    raise MailboxAcceptanceGuardError(
                        "acceptance_count_unproven", message_count=len(messages))
                document_count += count_result.count
            if document_count > acceptance_max_documents:
                raise MailboxAcceptanceGuardError(
                    "acceptance_document_limit_exceeded",
                    message_count=len(messages), document_count=document_count)
            self._observe(stage_observer, "acceptance_guard", "passed", started_at,
                          candidate_message_count=len(messages),
                          candidate_document_count=document_count)

        results: list[
            MessageProcessingResult
        ] = []

        for message in messages:
            result = self.process_message(message, stage_observer=stage_observer)

            results.append(result)

        return results

    def process_message(
        self,
        message: dict,
        *,
        stage_observer=None,
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
            download_started_at = __import__("time").perf_counter()
            download_result = self.attachment_service.download_supported_file_attachments(
                message_id,
                supported_extensions=SUPPORTED_FILE_EXTENSIONS,
            )
            result.downloaded_files.extend(download_result.downloaded_files)
            self._observe(stage_observer, "attachment_download", "completed",
                          download_started_at,
                          candidate_document_count=len(download_result.candidate_outcomes))
        except Exception:
            result.errors.append(
                "Attachment download failed."
            )
            return result
        message_key = self.job_state_service.message_key(message_id)
        if message_key is None:
            result.errors.append("Mailbox job identity could not be derived.")
            return result
        if not download_result.candidate_outcomes:
            self._complete_handled_message(result)
            return result
        for candidate in download_result.candidate_outcomes:
            if candidate.status not in {"downloaded", "reused_identical", "identical_collision"}:
                result.errors.append("Attachment source collision blocked processing.")
                continue
            file_path = candidate.local_path
            discovery = self.job_state_service.discover(
                message_key=message_key,
                attachment_key=candidate.attachment_order_key,
                document_key=candidate.document_fingerprint,
                attachment_required=True,
            )
            if not discovery.success or discovery.state is None:
                result.errors.append("Mailbox document state could not be stored.")
                continue
            state = discovery.state
            if state.stage not in {"discovered", "processing"}:
                result.work_items.append(MailboxDocumentWorkItem(
                    state.job_key, message_key, candidate.attachment_order_key,
                    candidate.document_fingerprint, file_path, state.stage,
                ))
                continue
            lease = self.job_state_service.acquire_processing_lease(state.job_key)
            if not lease.success or lease.state is None:
                result.errors.append("Mailbox document job could not be claimed.")
                continue
            try:
                if stage_observer is None:
                    document = self.document_processor.process(file_path)
                else:
                    document = self.document_processor.process(
                        file_path, stage_observer=stage_observer)

                result.processed_documents.append(
                    document
                )
                pending = self.job_state_service.transition(
                    state.job_key, expected_stages={"processing"},
                    stage="row_write_pending", lease_token=lease.state.lease_token,
                )
                if not pending.success:
                    result.errors.append("Mailbox document state could not be stored.")
                    continue
                result.work_items.append(MailboxDocumentWorkItem(
                    state.job_key, message_key, candidate.attachment_order_key,
                    candidate.document_fingerprint, file_path,
                    "row_write_pending", document,
                ))
            except Exception:
                result.errors.append(
                    "Document processing failed."
                )
        return result

    @staticmethod
    def _observe(observer, stage, status, started_at, **counts):
        if not callable(observer):
            return
        duration = max(0.0, __import__("time").perf_counter() - started_at)
        observer(stage=stage, status=status, duration_seconds=duration, **counts)

    def complete_message(self, result: MessageProcessingResult) -> bool:
        if not isinstance(result, MessageProcessingResult):
            return False
        for item in result.work_items:
            loaded = self.job_state_service.load(item.job_key)
            if not loaded.success or loaded.state is None or loaded.state.stage != "attachment_written":
                result.errors.append("Mailbox business actions are incomplete.")
                return False
        result.business_actions_completed = True
        self._complete_handled_message(result)
        return result.marked_as_read

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
