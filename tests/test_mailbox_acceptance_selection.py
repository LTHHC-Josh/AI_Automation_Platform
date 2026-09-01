import contextlib
import io
from types import SimpleNamespace

from src.graph.attachment_service import SupportedAttachmentCountResult
from src.graph.mailbox_processor import (
    MailboxAcceptanceGuardError,
    MailboxProcessor,
)
from src.models.mailbox_acceptance import MailboxAcceptanceSelectionResult
from src.ui.mailbox_acceptance_selection import (
    LocalMailboxAcceptanceSelector,
    safe_candidate_display_values,
)
from src.services.mailbox_full_review_orchestration_service import (
    FirstEligibleMailboxCandidateSelector,
    MailboxClassificationReviewMode,
    MailboxFullReviewOrchestrationService,
)


PROTECTED_ID = "PROTECTED-SYNTHETIC-MESSAGE-IDENTITY"
PROTECTED_SUBJECT = "PROTECTED-SYNTHETIC-SUBJECT"
PROTECTED_SENDER = "PROTECTED-SYNTHETIC-SENDER"
PROTECTED_FILENAME = "PROTECTED-SYNTHETIC-FILENAME.pdf"


class SyntheticEmail:
    def __init__(self, messages, exact_message=None, exact_error=None):
        self.messages = messages
        self.exact_message = exact_message
        self.exact_error = exact_error
        self.list_tops = []
        self.exact_calls = []

    def get_unread_messages(self, top=10):
        self.list_tops.append(top)
        return self.messages[:top]

    def get_unread_inbox_message(self, message_id):
        self.exact_calls.append(message_id)
        if self.exact_error is not None:
            raise self.exact_error
        return self.exact_message


class SyntheticAttachments:
    def __init__(self, counts):
        self.counts = {key: list(values) for key, values in counts.items()}
        self.count_calls = []
        self.download_calls = 0

    def count_supported_file_attachments(self, message_id, *, supported_extensions):
        self.count_calls.append(message_id)
        value = self.counts[message_id].pop(0)
        if isinstance(value, SupportedAttachmentCountResult):
            return value
        unsupported_count = 0
        if isinstance(value, tuple):
            value, unsupported_count = value
        if value is None:
            return SupportedAttachmentCountResult(count=None, success=False)
        return SupportedAttachmentCountResult(
            count=value,
            success=True,
            unsupported_document_type_count=unsupported_count,
        )

    def download_supported_file_attachments(self, *args, **kwargs):
        self.download_calls += 1
        raise AssertionError("Expensive processing must not start in this mock.")


class RecordingSelector:
    def __init__(self, selection, *, disposition=None, popup_displayed=True):
        self.selection = selection
        self.disposition = disposition or (
            "selected" if selection is not None else "cancelled"
        )
        self.popup_displayed = popup_displayed
        self.calls = []

    def select(self, candidates):
        self.calls.append(candidates)
        return MailboxAcceptanceSelectionResult(
            candidate_number=self.selection,
            popup_displayed=self.popup_displayed,
            disposition=self.disposition,
        )


def message(identity, *, is_read=False, received="2026-08-31T15:45:00Z"):
    return {
        "id": identity,
        "subject": PROTECTED_SUBJECT,
        "from": PROTECTED_SENDER,
        "receivedDateTime": received,
        "hasAttachments": True,
        "isRead": is_read,
    }


def build_processor(messages, counts, *, exact_message=None, exact_error=None):
    email = SyntheticEmail(messages, exact_message=exact_message, exact_error=exact_error)
    attachments = SyntheticAttachments(counts)
    processor = MailboxProcessor(
        email_service=email,
        attachment_service=attachments,
        document_processor=SimpleNamespace(),
        processing_state_service=SimpleNamespace(),
        job_state_service=SimpleNamespace(),
    )
    processed = []

    def process_message(
        selected,
        stage_observer=None,
        proven_supported_document_count=None,
    ):
        processed.append(selected)
        return SimpleNamespace(
            processed_documents=[],
            proven_supported_document_count=proven_supported_document_count,
        )

    processor.process_message = process_message
    return processor, email, attachments, processed


def assert_guard(operation, category):
    try:
        operation()
    except MailboxAcceptanceGuardError as error:
        assert error.category == category
        return error
    raise AssertionError("Expected the acceptance guard to block.")


def test_unattended_selector_processes_only_newest_eligible_with_exact_reverification():
    first = "synthetic-newest"
    second = "synthetic-older"
    processor, email, _, processed = build_processor(
        [message(first), message(second)],
        {first: [1, 1], second: [1]},
        exact_message=message(first),
    )
    results = processor.process_selected_unread_message(
        selector=FirstEligibleMailboxCandidateSelector(),
        discovery_top=10,
        require_popup=False,
    )
    assert len(results) == 1
    assert email.exact_calls == [first]
    assert len(processed) == 1
    assert processed[0]["id"] == first
    assert results[0].proven_supported_document_count == 1


def test_unattended_exact_candidate_loss_never_falls_back():
    first = "synthetic-newest"
    second = "synthetic-older"
    processor, email, attachments, processed = build_processor(
        [message(first), message(second)],
        {first: [1], second: [1]},
        exact_message=None,
    )
    error = assert_guard(
        lambda: processor.process_selected_unread_message(
            selector=FirstEligibleMailboxCandidateSelector(),
            discovery_top=10,
            require_popup=False,
        ),
        "acceptance_selected_candidate_unavailable",
    )
    assert error.message_count is None
    assert email.exact_calls == [first]
    assert attachments.download_calls == 0
    assert processed == []


def test_unattended_invocations_process_sequential_candidates_one_at_a_time():
    first = "synthetic-newest"
    second = "synthetic-older"
    processor, email, _, processed = build_processor(
        [message(first), message(second)],
        {first: [1, 1], second: [1, 1, 1]},
        exact_message=message(first),
    )
    selector = FirstEligibleMailboxCandidateSelector()
    first_results = processor.process_selected_unread_message(
        selector=selector, discovery_top=10, require_popup=False
    )
    email.messages = [message(second)]
    email.exact_message = message(second)
    second_results = processor.process_selected_unread_message(
        selector=selector, discovery_top=10, require_popup=False
    )
    assert len(first_results) == len(second_results) == 1
    assert [item["id"] for item in processed] == [first, second]
    assert email.exact_calls == [first, second]


def test_popup_receives_only_eligible_phi_safe_candidates():
    identities = ["two-docs", PROTECTED_ID, "zero-docs"]
    messages = [message(identity) for identity in identities]
    processor, email, _, processed = build_processor(
        messages,
        {
            "two-docs": [2],
            PROTECTED_ID: [1, 1],
            "zero-docs": [0],
        },
        exact_message=message(PROTECTED_ID),
    )
    selector = RecordingSelector(1)
    results = processor.process_selected_unread_message(selector=selector)

    assert len(results) == 1
    assert email.list_tops == [10]
    assert email.exact_calls == [PROTECTED_ID]
    assert len(processed) == 1
    assert results[0].proven_supported_document_count == 1
    assert len(selector.calls[0]) == 1
    candidate = selector.calls[0][0]
    assert candidate.candidate_number == 1
    assert candidate.received_timestamp == "2026-08-31 15:45:00 UTC"
    assert candidate.supported_document_count == 1
    assert safe_candidate_display_values(candidate) == (
        "Candidate 1",
        "2026-08-31 15:45:00 UTC",
        1,
    )
    rendered = repr(selector.calls[0]) + repr(safe_candidate_display_values(candidate))
    for protected in (
        PROTECTED_ID,
        PROTECTED_SUBJECT,
        PROTECTED_SENDER,
        PROTECTED_FILENAME,
    ):
        assert protected not in rendered


def test_cancel_and_invalid_selection_fail_closed():
    for selection, category in (
        (None, "acceptance_selection_cancelled"),
        (0, "acceptance_selection_invalid"),
        (2, "acceptance_selection_invalid"),
        (True, "acceptance_selection_invalid"),
    ):
        processor, email, attachments, processed = build_processor(
            [message(PROTECTED_ID)],
            {PROTECTED_ID: [1]},
            exact_message=message(PROTECTED_ID),
        )
        assert_guard(
            lambda: processor.process_selected_unread_message(
                selector=RecordingSelector(selection)
            ),
            category,
        )
        assert email.exact_calls == []
        assert attachments.download_calls == 0
        assert processed == []


def test_close_and_no_selection_fail_closed_with_distinct_safe_categories():
    for disposition, category in (
        ("closed", "acceptance_selection_closed"),
        ("no_selection", "acceptance_selection_no_selection"),
    ):
        processor, email, attachments, processed = build_processor(
            [message(PROTECTED_ID)],
            {PROTECTED_ID: [1]},
            exact_message=message(PROTECTED_ID),
        )
        assert_guard(
            lambda disposition=disposition: processor.process_selected_unread_message(
                selector=RecordingSelector(None, disposition=disposition)
            ),
            category,
        )
        assert email.exact_calls == []
        assert attachments.download_calls == 0
        assert processed == []


def test_no_eligible_or_unprovable_discovery_blocks_before_popup():
    for count in (0, 2, None, True):
        processor, email, attachments, processed = build_processor(
            [message(PROTECTED_ID)],
            {PROTECTED_ID: [count]},
        )
        selector = RecordingSelector(1)
        assert_guard(
            lambda: processor.process_selected_unread_message(selector=selector),
            "acceptance_no_eligible_candidate",
        )
        assert selector.calls == []
        assert email.exact_calls == []
        assert attachments.download_calls == 0
        assert processed == []


def test_zero_eligible_discovery_reports_only_aggregate_exclusion_counts():
    identities = (
        "PRIVATE-ID-A", "PRIVATE-ID-B", "PRIVATE-ID-C", "PRIVATE-ID-D", "PRIVATE-ID-E"
    )
    messages = [
        message(identities[0], is_read=True),
        *(message(identity) for identity in identities[1:]),
    ]
    processor, _, attachments, processed = build_processor(
        messages,
        {
            identities[0]: [],
            identities[1]: [0],
            identities[2]: [(0, 1)],
            identities[3]: [2],
            identities[4]: [None],
        },
    )
    events = []
    assert_guard(
        lambda: processor.process_selected_unread_message(
            selector=RecordingSelector(1),
            stage_observer=lambda **event: events.append(event),
        ),
        "acceptance_no_eligible_candidate",
    )
    terminal = [event for event in events if event["stage"] == "candidate_selection"][-1]
    assert terminal == {
        "stage": "candidate_selection",
        "status": "failed",
        "duration_seconds": terminal["duration_seconds"],
        "discovery_completed": True,
        "eligible_candidate_count": 0,
        "popup_displayed": False,
        "candidate_selected": False,
        "failure_category": "acceptance_no_eligible_candidate",
        "not_unread_count": 1,
        "no_supported_document_count": 1,
        "multiple_supported_documents_count": 1,
        "unsupported_document_type_count": 1,
        "document_count_unprovable_count": 1,
        "attachment_metadata_request_failed_count": 0,
        "attachment_metadata_response_invalid_count": 0,
        "attachment_metadata_item_invalid_count": 0,
        "attachment_metadata_type_unprovable_count": 0,
        "attachment_metadata_inline_state_unprovable_count": 0,
        "attachment_metadata_name_unprovable_count": 0,
        "attachment_metadata_pagination_invalid_count": 0,
        "attachment_metadata_pagination_request_failed_count": 0,
    }
    assert attachments.download_calls == 0
    assert processed == []
    rendered = repr(events)
    for protected in identities + (
        PROTECTED_SUBJECT, PROTECTED_SENDER, PROTECTED_FILENAME,
    ):
        assert protected not in rendered


def test_unprovable_reason_is_reported_only_as_an_allowlisted_aggregate_count():
    processor, _, attachments, processed = build_processor(
        [message(PROTECTED_ID)],
        {PROTECTED_ID: [SupportedAttachmentCountResult(
            count=None,
            success=False,
            unprovable_reason="attachment_metadata_request_failed",
        )]},
    )
    events = []
    assert_guard(
        lambda: processor.process_selected_unread_message(
            selector=RecordingSelector(1),
            stage_observer=lambda **event: events.append(event),
        ),
        "acceptance_no_eligible_candidate",
    )
    terminal = [event for event in events if event["stage"] == "candidate_selection"][-1]
    assert terminal["document_count_unprovable_count"] == 1
    assert terminal["attachment_metadata_request_failed_count"] == 1
    assert sum(
        value for key, value in terminal.items()
        if key.startswith("attachment_metadata_") and key.endswith("_count")
    ) == 1
    assert PROTECTED_ID not in repr(terminal)
    assert attachments.download_calls == 0
    assert processed == []


def test_selected_candidate_unavailable_or_moved_never_falls_back():
    cases = (
        {"exact_message": None},
        {"exact_error": RuntimeError("protected provider detail")},
    )
    for exact_options in cases:
        processor, email, attachments, processed = build_processor(
            [message(PROTECTED_ID), message("newest-unread-fallback")],
            {PROTECTED_ID: [1], "newest-unread-fallback": [1]},
            **exact_options,
        )
        assert_guard(
            lambda: processor.process_selected_unread_message(
                selector=RecordingSelector(1)
            ),
            "acceptance_selected_candidate_unavailable",
        )
        assert email.list_tops == [10]
        assert email.exact_calls == [PROTECTED_ID]
        assert attachments.download_calls == 0
        assert processed == []


def test_selected_candidate_read_or_identity_mismatch_blocks():
    cases = (
        (message(PROTECTED_ID, is_read=True), "acceptance_selected_candidate_read"),
        (message("different-identity"), "acceptance_selected_candidate_unavailable"),
    )
    for exact_message, category in cases:
        processor, _, attachments, processed = build_processor(
            [message(PROTECTED_ID)],
            {PROTECTED_ID: [1]},
            exact_message=exact_message,
        )
        assert_guard(
            lambda: processor.process_selected_unread_message(
                selector=RecordingSelector(1)
            ),
            category,
        )
        assert attachments.download_calls == 0
        assert processed == []


def test_selected_document_count_is_reverified_and_must_equal_one():
    for reverification_count, category in (
        (0, "acceptance_document_count_invalid"),
        (2, "acceptance_document_count_invalid"),
        (None, "acceptance_count_unproven"),
    ):
        processor, email, attachments, processed = build_processor(
            [message(PROTECTED_ID)],
            {PROTECTED_ID: [1, reverification_count]},
            exact_message=message(PROTECTED_ID),
        )
        assert_guard(
            lambda: processor.process_selected_unread_message(
                selector=RecordingSelector(1)
            ),
            category,
        )
        assert email.exact_calls == [PROTECTED_ID]
        assert attachments.download_calls == 0
        assert processed == []


def test_selection_and_reverification_events_are_complete_and_phi_safe():
    processor, _, _, processed = build_processor(
        [message(PROTECTED_ID)],
        {PROTECTED_ID: [1, 1]},
        exact_message=message(PROTECTED_ID),
    )
    events = []
    processor.process_selected_unread_message(
        selector=RecordingSelector(1),
        stage_observer=lambda **event: events.append(event),
    )

    selection_events = [event for event in events if event["stage"] == "candidate_selection"]
    reverification_events = [
        event for event in events if event["stage"] == "candidate_reverification"
    ]
    assert [event["status"] for event in selection_events] == ["started", "completed"]
    assert selection_events[-1]["discovery_completed"] is True
    assert selection_events[-1]["eligible_candidate_count"] == 1
    assert selection_events[-1]["popup_displayed"] is True
    assert selection_events[-1]["candidate_selected"] is True
    assert [event["status"] for event in reverification_events] == [
        "started", "completed"
    ]
    completed = reverification_events[-1]
    for proof in (
        "candidate_available",
        "unread_state_proven",
        "inbox_membership_proven",
        "exact_identity_match_proven",
        "exactly_one_supported_document_proven",
    ):
        assert completed[proof] is True
    assert len(processed) == 1

    rendered = repr(events)
    for protected in (
        PROTECTED_ID,
        PROTECTED_SUBJECT,
        PROTECTED_SENDER,
        PROTECTED_FILENAME,
    ):
        assert protected not in rendered


def test_guard_failures_emit_safe_terminal_stage_events():
    cases = (
        (
            [],
            {},
            None,
            RecordingSelector(1),
            "candidate_selection",
            "acceptance_no_eligible_candidate",
        ),
        (
            [message(PROTECTED_ID)],
            {PROTECTED_ID: [1]},
            message(PROTECTED_ID),
            RecordingSelector(None),
            "candidate_selection",
            "acceptance_selection_cancelled",
        ),
        (
            [message(PROTECTED_ID)],
            {PROTECTED_ID: [1]},
            None,
            RecordingSelector(1),
            "candidate_reverification",
            "acceptance_selected_candidate_unavailable",
        ),
        (
            [message(PROTECTED_ID)],
            {PROTECTED_ID: [1]},
            message(PROTECTED_ID, is_read=True),
            RecordingSelector(1),
            "candidate_reverification",
            "acceptance_selected_candidate_read",
        ),
    )
    for messages, counts, exact_message, selector, stage, category in cases:
        processor, _, _, processed = build_processor(
            messages,
            counts,
            exact_message=exact_message,
        )
        events = []
        assert_guard(
            lambda: processor.process_selected_unread_message(
                selector=selector,
                stage_observer=lambda **event: events.append(event),
            ),
            category,
        )
        terminal = [event for event in events if event["stage"] == stage][-1]
        assert terminal["failure_category"] == category
        assert terminal["status"] in {"failed", "cancelled"}
        assert processed == []
        assert PROTECTED_ID not in repr(events)


def test_selector_failure_is_sanitized_and_identity_is_not_output():
    class FailingView:
        def show(self, *, candidates):
            raise RuntimeError(PROTECTED_ID)

    selector = LocalMailboxAcceptanceSelector(view_factory=FailingView)
    processor, _, attachments, processed = build_processor(
        [message(PROTECTED_ID)],
        {PROTECTED_ID: [1]},
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        error = assert_guard(
            lambda: processor.process_selected_unread_message(selector=selector),
            "acceptance_selection_unavailable",
        )
    rendered = repr(error) + str(error) + stdout.getvalue() + stderr.getvalue()
    assert PROTECTED_ID not in rendered
    assert attachments.download_calls == 0
    assert processed == []


def test_acceptance_policy_cannot_broaden_one_message_one_document_limits():
    processor, _, _, _ = build_processor([], {})
    for options in (
        {"acceptance_max_messages": 2},
        {"acceptance_max_documents": 2},
        {"discovery_top": 0},
    ):
        assert_guard(
            lambda options=options: processor.process_selected_unread_message(
                selector=RecordingSelector(None),
                **options,
            ),
            "acceptance_policy_invalid",
        )


def test_preselected_acceptance_refetches_only_exact_identity_without_enumeration():
    processor, email, _, processed = build_processor(
        [message("unrelated")],
        {PROTECTED_ID: [1]},
        exact_message=message(PROTECTED_ID),
    )
    results = processor.process_preselected_acceptance(PROTECTED_ID)
    assert len(results) == 1
    assert email.list_tops == []
    assert email.exact_calls == [PROTECTED_ID]
    assert len(processed) == 1


def test_acceptance_orchestration_entrypoint_keeps_selection_inside_application():
    service = MailboxFullReviewOrchestrationService.__new__(
        MailboxFullReviewOrchestrationService
    )
    calls = []
    service.run = lambda **kwargs: calls.append(kwargs) or "safe-result"
    selector = RecordingSelector(1)

    result = service.run_selected_acceptance(
        discovery_top=10,
        run_type="safe-run-type",
        selector=selector,
    )

    assert result == "safe-result"
    assert calls == [{
        "top": 1,
        "created_at": None,
        "review_mode": MailboxClassificationReviewMode.DOWNSTREAM,
        "run_type": "safe-run-type",
        "acceptance_max_messages": 1,
        "acceptance_max_documents": 1,
        "acceptance_selector": selector,
        "acceptance_discovery_top": 10,
        "stage_observer": None,
    }]


def test_unattended_orchestration_no_candidate_is_successful_noop():
    service = MailboxFullReviewOrchestrationService.__new__(
        MailboxFullReviewOrchestrationService
    )
    service.mailbox_processor = SimpleNamespace(job_state_service=None)
    calls = []
    service.run = lambda **kwargs: calls.append(kwargs) or service._failure(
        "acceptance_no_eligible_candidate",
        stage="acceptance_guard",
        message_count=0,
        document_count=0,
    )
    result = service.run_unattended_once(run_type="safe-unattended")
    assert result.success is True
    assert result.status == "no_eligible_candidate"
    assert result.message_count == 0 and result.document_count == 0
    assert calls[0]["acceptance_require_popup"] is False
    assert isinstance(calls[0]["acceptance_selector"], FirstEligibleMailboxCandidateSelector)
    assert calls[0]["acceptance_max_messages"] == 1
    assert calls[0]["acceptance_max_documents"] == 1


if __name__ == "__main__":
    tests = [value for name, value in globals().copy().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic and mock")
    print("External integrations: not called")
    print("PHI handling: protected synthetic markers suppressed")
