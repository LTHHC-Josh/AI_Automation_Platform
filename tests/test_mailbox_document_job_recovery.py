import json
from pathlib import Path
from types import SimpleNamespace

from src.services.mailbox_document_job_state_service import (
    MailboxDocumentJobStateService, MailboxDocumentWorkItem,
)
from src.services.mailbox_document_smartsheet_recovery_service import (
    MailboxDocumentSmartsheetRecoveryService,
)
from src.services.smartsheet_submission_key_configuration_service import (
    SmartsheetSubmissionKeyConfigurationService,
)
from src.graph.mailbox_processor import MailboxProcessor, MessageProcessingResult
from src.services.mailbox_processing_state_service import MailboxProcessingStateResult


def digest(character):
    return character * 64


def discovered(service):
    return service.discover(
        message_key=digest("a"), attachment_key=digest("b"),
        document_key=digest("c"), attachment_required=True,
    )


def test_job_identity_is_stable_and_source_event_specific(tmp_path):
    service = MailboxDocumentJobStateService(tmp_path)
    first = discovered(service)
    repeated = discovered(service)
    distinct = service.discover(
        message_key=digest("d"), attachment_key=digest("b"),
        document_key=digest("c"), attachment_required=True,
    )
    assert first.success and repeated.success and distinct.success
    assert first.state.job_key == repeated.state.job_key
    assert first.state.job_key != distinct.state.job_key
    assert digest("a") not in repr(first)


def test_atomic_state_transitions_and_active_lease_exclusion(tmp_path):
    service = MailboxDocumentJobStateService(tmp_path, lease_seconds=60)
    state = discovered(service).state
    lease = service.acquire_processing_lease(state.job_key)
    excluded = service.acquire_processing_lease(state.job_key)
    pending = service.transition(
        state.job_key, expected_stages={"processing"}, stage="row_write_pending",
        lease_token=lease.state.lease_token,
    )
    assert lease.success
    assert excluded.status == "lease_active"
    assert pending.success and pending.state.stage == "row_write_pending"
    assert not list(tmp_path.glob("*.tmp"))


def test_corrupt_and_unsupported_state_fail_closed_without_overwrite(tmp_path):
    service = MailboxDocumentJobStateService(tmp_path)
    state = discovered(service).state
    path = tmp_path / f"{state.job_key}.json"
    path.write_text("{", encoding="utf-8")
    assert service.load(state.job_key).status == "state_corrupt"
    assert service.discover(
        message_key=digest("a"), attachment_key=digest("b"), document_key=digest("c")
    ).status == "state_corrupt"
    payload = {field: value for field, value in json.loads(json.dumps({
        "schema_version": 2, "job_key": state.job_key, "message_key": digest("a"),
        "attachment_key": digest("b"), "document_key": digest("c"), "stage": "discovered",
        "smartsheet_row_id": None, "attachment_required": True, "row_attempt_count": 0,
        "attachment_attempt_count": 0, "last_failure_category": None, "retryable": True,
        "lease_token": None, "lease_expires_at": None, "updated_at": "synthetic",
    })).items()}
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert service.load(state.job_key).status == "state_version_unsupported"


def test_submission_key_configuration_has_no_default_or_public_title():
    missing = SmartsheetSubmissionKeyConfigurationService(environment={}).resolve()
    configured = SmartsheetSubmissionKeyConfigurationService(environment={
        "SMARTSHEET_AI_SUBMISSION_KEY_COLUMN_TITLE": "Synthetic Technical Key"
    }).resolve()
    assert not missing.success and missing.status == "submission_key_configuration_missing"
    assert configured.success and configured.configured
    assert "Synthetic Technical Key" not in repr(configured)


class ZeroMatchClient:
    def __init__(self):
        self.row_creations = 0
    def find_row_ids_by_exact_column_title_value(self, **kwargs):
        return []


def test_uncertain_row_never_automatically_creates_again(tmp_path):
    state_service = MailboxDocumentJobStateService(tmp_path)
    state = discovered(state_service).state
    lease = state_service.acquire_processing_lease(state.job_key).state
    pending = state_service.transition(
        state.job_key, expected_stages={"processing"}, stage="row_write_pending",
        lease_token=lease.lease_token).state
    uncertain = state_service.transition(
        state.job_key, expected_stages={"row_write_pending"}, stage="row_write_uncertain",
        failure_category="row_write_outcome_unknown", retryable=False).state
    client = ZeroMatchClient()
    recovery = MailboxDocumentSmartsheetRecoveryService(
        job_state_service=state_service,
        submission_key_configuration_service=SmartsheetSubmissionKeyConfigurationService(
            environment={"SMARTSHEET_AI_SUBMISSION_KEY_COLUMN_TITLE": "Synthetic Technical Key"}),
        write_service=SimpleNamespace(client=client),
    )
    result = recovery.run(work_item=MailboxDocumentWorkItem(
        uncertain.job_key, digest("a"), digest("b"), digest("c"),
        Path("synthetic.pdf"), "row_write_uncertain"))
    assert not result.success and result.status == "row_write_uncertain"
    assert client.row_creations == 0
    assert state_service.load(state.job_key).state.stage == "row_write_uncertain"


class OrderedMessageState:
    def __init__(self, events): self.events = events
    def mark_handled(self, message_id):
        self.events.append("handled")
        return MailboxProcessingStateResult(True, True, False, True, "handled_recorded")


class OrderedEmail:
    def __init__(self, events): self.events = events
    def mark_as_read(self, message_id):
        self.events.append("read")
        return True


def test_message_completion_occurs_only_after_attachment_state(tmp_path):
    jobs = MailboxDocumentJobStateService(tmp_path)
    state = discovered(jobs).state
    lease = jobs.acquire_processing_lease(state.job_key).state
    pending = jobs.transition(state.job_key, expected_stages={"processing"},
                              stage="row_write_pending", lease_token=lease.lease_token).state
    row = jobs.transition(state.job_key, expected_stages={"row_write_pending"},
                          stage="row_written", smartsheet_row_id=7).state
    events = []
    processor = MailboxProcessor.__new__(MailboxProcessor)
    processor.job_state_service = jobs
    processor.processing_state_service = OrderedMessageState(events)
    processor.email_service = OrderedEmail(events)
    result = MessageProcessingResult("synthetic", "synthetic", work_items=[
        MailboxDocumentWorkItem(row.job_key, digest("a"), digest("b"), digest("c"),
                                Path("synthetic.pdf"), "row_written")])
    assert processor.complete_message(result) is False
    assert events == []
    result.errors.clear()
    jobs.transition(state.job_key, expected_stages={"row_written"}, stage="attachment_written")
    assert processor.complete_message(result) is True
    assert events == ["handled", "read"]
