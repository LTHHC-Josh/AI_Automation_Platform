from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.document_processing.document_processor import (
    DocumentProcessor,
)
from src.models.document import Document
from src.models.mailbox_acceptance import (
    MailboxAcceptanceCandidate,
    MailboxAcceptanceSelectionResult,
)
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

    def _prepare_selected_acceptance(
        self,
        *,
        selector,
        discovery_top: int = 10,
        acceptance_max_messages: int = 1,
        acceptance_max_documents: int = 1,
        stage_observer=None,
    ) -> tuple[str, dict]:
        """Select and prove one candidate, returning its identity only in memory."""
        if (
            not isinstance(discovery_top, int)
            or isinstance(discovery_top, bool)
            or discovery_top < 1
            or not isinstance(acceptance_max_messages, int)
            or isinstance(acceptance_max_messages, bool)
            or acceptance_max_messages != 1
            or not isinstance(acceptance_max_documents, int)
            or isinstance(acceptance_max_documents, bool)
            or acceptance_max_documents != 1
        ):
            raise MailboxAcceptanceGuardError("acceptance_policy_invalid")

        started_at = __import__("time").perf_counter()
        messages = self.email_service.get_unread_messages(top=discovery_top)
        if not isinstance(messages, list):
            raise MailboxAcceptanceGuardError("acceptance_count_unproven")

        safe_candidates: list[MailboxAcceptanceCandidate] = []
        selected_identities: list[str] = []
        exclusion_counts = {
            "not_unread_count": 0,
            "no_supported_document_count": 0,
            "multiple_supported_documents_count": 0,
            "unsupported_document_type_count": 0,
            "document_count_unprovable_count": 0,
        }
        unprovable_reason_counts = {
            f"{reason}_count": 0
            for reason in (
                "attachment_metadata_request_failed",
                "attachment_metadata_response_invalid",
                "attachment_metadata_item_invalid",
                "attachment_metadata_type_unprovable",
                "attachment_metadata_inline_state_unprovable",
                "attachment_metadata_name_unprovable",
                "attachment_metadata_pagination_invalid",
                "attachment_metadata_pagination_request_failed",
            )
        }
        for message in messages:
            if not isinstance(message, dict):
                raise MailboxAcceptanceGuardError("acceptance_count_unproven")
            message_id = message.get("id")
            if not isinstance(message_id, str) or not message_id:
                raise MailboxAcceptanceGuardError("acceptance_count_unproven")
            if message.get("isRead") is not False:
                exclusion_counts["not_unread_count"] += 1
                continue
            count_result = self.attachment_service.count_supported_file_attachments(
                message_id,
                supported_extensions=SUPPORTED_FILE_EXTENSIONS,
            )
            count = getattr(count_result, "count", None)
            if (
                not getattr(count_result, "success", False)
                or not isinstance(count, int)
                or isinstance(count, bool)
            ):
                exclusion_counts["document_count_unprovable_count"] += 1
                reason_key = f"{getattr(count_result, 'unprovable_reason', '')}_count"
                if reason_key in unprovable_reason_counts:
                    unprovable_reason_counts[reason_key] += 1
                continue
            if count == 0:
                unsupported_count = getattr(
                    count_result, "unsupported_document_type_count", 0
                )
                if (
                    isinstance(unsupported_count, int)
                    and not isinstance(unsupported_count, bool)
                    and unsupported_count > 0
                ):
                    exclusion_counts["unsupported_document_type_count"] += 1
                else:
                    exclusion_counts["no_supported_document_count"] += 1
                continue
            if count > 1:
                exclusion_counts["multiple_supported_documents_count"] += 1
                continue
            candidate_number = len(safe_candidates) + 1
            safe_candidates.append(
                MailboxAcceptanceCandidate(
                    candidate_number=candidate_number,
                    received_timestamp=self._safe_received_timestamp(
                        message.get("receivedDateTime")
                    ),
                    supported_document_count=count,
                )
            )
            selected_identities.append(message_id)

        self._observe(
            stage_observer,
            "mailbox_discovery",
            "completed",
            started_at,
            candidate_message_count=len(safe_candidates),
        )
        selection_started_at = __import__("time").perf_counter()
        self._observe(
            stage_observer,
            "candidate_selection",
            "started",
            selection_started_at,
            discovery_completed=True,
            eligible_candidate_count=len(safe_candidates),
            popup_displayed=False,
            candidate_selected=False,
            failure_category=None,
            **exclusion_counts,
            **unprovable_reason_counts,
        )
        if not safe_candidates:
            self._observe(
                stage_observer,
                "candidate_selection",
                "failed",
                selection_started_at,
                discovery_completed=True,
                eligible_candidate_count=0,
                popup_displayed=False,
                candidate_selected=False,
                failure_category="acceptance_no_eligible_candidate",
                **exclusion_counts,
                **unprovable_reason_counts,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_no_eligible_candidate",
                message_count=0,
                document_count=0,
            )

        try:
            selection = selector.select(tuple(safe_candidates))
        except Exception:
            self._observe(
                stage_observer,
                "candidate_selection",
                "failed",
                selection_started_at,
                discovery_completed=True,
                eligible_candidate_count=len(safe_candidates),
                popup_displayed=False,
                candidate_selected=False,
                failure_category="acceptance_selection_unavailable",
                **exclusion_counts,
                **unprovable_reason_counts,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_selection_unavailable"
            ) from None

        if not isinstance(selection, MailboxAcceptanceSelectionResult):
            self._observe(
                stage_observer,
                "candidate_selection",
                "failed",
                selection_started_at,
                discovery_completed=True,
                eligible_candidate_count=len(safe_candidates),
                popup_displayed=False,
                candidate_selected=False,
                failure_category="acceptance_selection_invalid",
                **exclusion_counts,
                **unprovable_reason_counts,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_selection_invalid"
            )

        selection_categories = {
            "cancelled": "acceptance_selection_cancelled",
            "closed": "acceptance_selection_closed",
            "no_selection": "acceptance_selection_no_selection",
        }
        if selection.disposition in selection_categories:
            category = selection_categories[selection.disposition]
            self._observe(
                stage_observer,
                "candidate_selection",
                "cancelled" if selection.disposition != "no_selection" else "failed",
                selection_started_at,
                discovery_completed=True,
                eligible_candidate_count=len(safe_candidates),
                popup_displayed=selection.popup_displayed is True,
                candidate_selected=False,
                failure_category=category,
                **exclusion_counts,
                **unprovable_reason_counts,
            )
            raise MailboxAcceptanceGuardError(category)

        selected_number = selection.candidate_number
        if (
            selection.disposition != "selected"
            or selection.popup_displayed is not True
            or not isinstance(selected_number, int)
            or isinstance(selected_number, bool)
            or selected_number < 1
            or selected_number > len(selected_identities)
        ):
            self._observe(
                stage_observer,
                "candidate_selection",
                "failed",
                selection_started_at,
                discovery_completed=True,
                eligible_candidate_count=len(safe_candidates),
                popup_displayed=selection.popup_displayed is True,
                candidate_selected=False,
                failure_category="acceptance_selection_invalid",
                **exclusion_counts,
                **unprovable_reason_counts,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_selection_invalid"
            )

        self._observe(
            stage_observer,
            "candidate_selection",
            "completed",
            selection_started_at,
            discovery_completed=True,
            eligible_candidate_count=len(safe_candidates),
            popup_displayed=True,
            candidate_selected=True,
            failure_category=None,
            **exclusion_counts,
            **unprovable_reason_counts,
        )

        selected_identity = selected_identities[selected_number - 1]
        reverification_started_at = __import__("time").perf_counter()
        reverification = {
            "candidate_available": False,
            "unread_state_proven": False,
            "inbox_membership_proven": False,
            "exact_identity_match_proven": False,
            "exactly_one_supported_document_proven": False,
        }
        self._observe(
            stage_observer,
            "candidate_reverification",
            "started",
            reverification_started_at,
            failure_category=None,
            **reverification,
        )
        try:
            selected_message = self.email_service.get_unread_inbox_message(
                selected_identity
            )
        except Exception:
            self._observe(
                stage_observer,
                "candidate_reverification",
                "failed",
                reverification_started_at,
                failure_category="acceptance_selected_candidate_unavailable",
                **reverification,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_selected_candidate_unavailable"
            ) from None
        if (
            not isinstance(selected_message, dict)
            or selected_message.get("id") != selected_identity
        ):
            if isinstance(selected_message, dict):
                reverification["inbox_membership_proven"] = True
            self._observe(
                stage_observer,
                "candidate_reverification",
                "failed",
                reverification_started_at,
                failure_category="acceptance_selected_candidate_unavailable",
                **reverification,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_selected_candidate_unavailable"
            )
        reverification.update(
            candidate_available=True,
            inbox_membership_proven=True,
            exact_identity_match_proven=True,
        )
        if selected_message.get("isRead") is not False:
            self._observe(
                stage_observer,
                "candidate_reverification",
                "failed",
                reverification_started_at,
                failure_category="acceptance_selected_candidate_read",
                **reverification,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_selected_candidate_read",
                message_count=1,
            )
        reverification["unread_state_proven"] = True

        count_result = self.attachment_service.count_supported_file_attachments(
            selected_identity,
            supported_extensions=SUPPORTED_FILE_EXTENSIONS,
        )
        document_count = getattr(count_result, "count", None)
        if (
            not getattr(count_result, "success", False)
            or not isinstance(document_count, int)
            or isinstance(document_count, bool)
        ):
            self._observe(
                stage_observer,
                "candidate_reverification",
                "failed",
                reverification_started_at,
                failure_category="acceptance_count_unproven",
                candidate_document_count=None,
                **reverification,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_count_unproven",
                message_count=1,
            )
        if document_count != 1:
            self._observe(
                stage_observer,
                "candidate_reverification",
                "failed",
                reverification_started_at,
                failure_category="acceptance_document_count_invalid",
                candidate_document_count=document_count,
                **reverification,
            )
            raise MailboxAcceptanceGuardError(
                "acceptance_document_count_invalid",
                message_count=1,
                document_count=document_count,
            )
        reverification["exactly_one_supported_document_proven"] = True
        self._observe(
            stage_observer,
            "candidate_reverification",
            "completed",
            reverification_started_at,
            failure_category=None,
            candidate_document_count=1,
            **reverification,
        )

        self._observe(
            stage_observer,
            "acceptance_guard",
            "passed",
            started_at,
            candidate_message_count=1,
            candidate_document_count=1,
        )
        return selected_identity, selected_message

    def prepare_selected_acceptance(
        self,
        *,
        selector,
        discovery_top: int = 10,
        acceptance_max_messages: int = 1,
        acceptance_max_documents: int = 1,
        stage_observer=None,
    ) -> str:
        """Prepare a preflight handoff without retaining mailbox content."""
        identity, _ = self._prepare_selected_acceptance(
            selector=selector,
            discovery_top=discovery_top,
            acceptance_max_messages=acceptance_max_messages,
            acceptance_max_documents=acceptance_max_documents,
            stage_observer=stage_observer,
        )
        return identity

    def process_selected_unread_message(
        self,
        *,
        selector,
        discovery_top: int = 10,
        acceptance_max_messages: int = 1,
        acceptance_max_documents: int = 1,
        stage_observer=None,
    ) -> list[MessageProcessingResult]:
        """Preserve the same-process popup acceptance entrypoint."""
        _, selected_message = self._prepare_selected_acceptance(
            selector=selector,
            discovery_top=discovery_top,
            acceptance_max_messages=acceptance_max_messages,
            acceptance_max_documents=acceptance_max_documents,
            stage_observer=stage_observer,
        )
        return [self.process_message(
            selected_message,
            stage_observer=stage_observer,
            proven_supported_document_count=1,
        )]

    def process_preselected_acceptance(
        self,
        message_identity: str,
        *,
        acceptance_max_messages: int = 1,
        acceptance_max_documents: int = 1,
        stage_observer=None,
    ) -> list[MessageProcessingResult]:
        """Re-verify only the handed-off exact identity, with no enumeration fallback."""
        if (
            not isinstance(message_identity, str) or not message_identity
            or acceptance_max_messages != 1 or acceptance_max_documents != 1
            or isinstance(acceptance_max_messages, bool)
            or isinstance(acceptance_max_documents, bool)
        ):
            raise MailboxAcceptanceGuardError("acceptance_policy_invalid")
        started_at = __import__("time").perf_counter()
        proof = {
            "candidate_available": False,
            "unread_state_proven": False,
            "inbox_membership_proven": False,
            "exact_identity_match_proven": False,
            "exactly_one_supported_document_proven": False,
        }
        self._observe(stage_observer, "candidate_reverification", "started", started_at,
                      failure_category=None, **proof)
        try:
            message = self.email_service.get_unread_inbox_message(message_identity)
        except Exception:
            message = None
        if not isinstance(message, dict) or message.get("id") != message_identity:
            self._observe(stage_observer, "candidate_reverification", "failed", started_at,
                          failure_category="acceptance_selected_candidate_unavailable", **proof)
            raise MailboxAcceptanceGuardError("acceptance_selected_candidate_unavailable")
        proof.update(candidate_available=True, inbox_membership_proven=True,
                     exact_identity_match_proven=True)
        if message.get("isRead") is not False:
            self._observe(stage_observer, "candidate_reverification", "failed", started_at,
                          failure_category="acceptance_selected_candidate_read", **proof)
            raise MailboxAcceptanceGuardError("acceptance_selected_candidate_read", message_count=1)
        proof["unread_state_proven"] = True
        count_result = self.attachment_service.count_supported_file_attachments(
            message_identity, supported_extensions=SUPPORTED_FILE_EXTENSIONS)
        count = getattr(count_result, "count", None)
        if (not getattr(count_result, "success", False) or not isinstance(count, int)
                or isinstance(count, bool)):
            self._observe(stage_observer, "candidate_reverification", "failed", started_at,
                          failure_category="acceptance_count_unproven",
                          candidate_document_count=None, **proof)
            raise MailboxAcceptanceGuardError("acceptance_count_unproven", message_count=1)
        if count != 1:
            self._observe(stage_observer, "candidate_reverification", "failed", started_at,
                          failure_category="acceptance_document_count_invalid",
                          candidate_document_count=count, **proof)
            raise MailboxAcceptanceGuardError("acceptance_document_count_invalid",
                                              message_count=1, document_count=count)
        proof["exactly_one_supported_document_proven"] = True
        self._observe(stage_observer, "candidate_reverification", "completed", started_at,
                      failure_category=None, candidate_document_count=1, **proof)
        self._observe(stage_observer, "acceptance_guard", "passed", started_at,
                      candidate_message_count=1, candidate_document_count=1)
        return [self.process_message(
            message,
            stage_observer=stage_observer,
            proven_supported_document_count=1,
        )]

    @staticmethod
    def _safe_received_timestamp(value) -> str | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = datetime.fromisoformat(
                value.strip().replace("Z", "+00:00")
            )
            if parsed.tzinfo is None:
                return None
            return parsed.astimezone(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        except (TypeError, ValueError, OverflowError):
            return None

    def process_message(
        self,
        message: dict,
        *,
        stage_observer=None,
        proven_supported_document_count: int | None = None,
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
            self._observe(
                stage_observer,
                "attachment_download",
                "skipped",
                __import__("time").perf_counter(),
                candidate_document_count=(
                    proven_supported_document_count
                    if proven_supported_document_count == 1
                    else None
                ),
                failure_category="message_already_handled",
            )
            self._mark_as_read(
                result
            )

            return result

        if (
            proven_supported_document_count != 1
            and not message.get("hasAttachments", False)
        ):
            self._observe(
                stage_observer,
                "attachment_download",
                "skipped",
                __import__("time").perf_counter(),
                candidate_document_count=0,
                failure_category="message_attachment_flag_false",
            )
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
            self._observe(
                stage_observer,
                "attachment_download",
                "skipped",
                download_started_at,
                candidate_document_count=0,
                failure_category="attachment_download_no_candidates",
            )
            if proven_supported_document_count == 1:
                result.errors.append(
                    "Proven attachment could not be acquired."
                )
                return result
            self._complete_handled_message(result)
            return result
        self._observe(
            stage_observer,
            "attachment_download",
            "completed",
            download_started_at,
            candidate_document_count=len(download_result.candidate_outcomes),
        )
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
