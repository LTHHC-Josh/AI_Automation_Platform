import contextlib
import io
from types import SimpleNamespace

from src.graph.attachment_service import SupportedAttachmentCountResult
from src.graph.mailbox_processor import (
    MailboxAcceptanceGuardError,
    MailboxProcessor,
)
from src.ui.mailbox_acceptance_selection import (
    LocalMailboxAcceptanceSelector,
    safe_candidate_display_values,
)
from src.services.mailbox_full_review_orchestration_service import (
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
        if value is None:
            return SupportedAttachmentCountResult(count=None, success=False)
        return SupportedAttachmentCountResult(count=value, success=True)

    def download_supported_file_attachments(self, *args, **kwargs):
        self.download_calls += 1
        raise AssertionError("Expensive processing must not start in this mock.")


class RecordingSelector:
    def __init__(self, selection):
        self.selection = selection
        self.calls = []

    def select(self, candidates):
        self.calls.append(candidates)
        return self.selection


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
    processor.process_message = lambda selected, stage_observer=None: processed.append(
        selected
    ) or SimpleNamespace(processed_documents=[])
    return processor, email, attachments, processed


def assert_guard(operation, category):
    try:
        operation()
    except MailboxAcceptanceGuardError as error:
        assert error.category == category
        return error
    raise AssertionError("Expected the acceptance guard to block.")


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


def test_selected_candidate_unavailable_or_moved_never_falls_back():
    processor, email, attachments, processed = build_processor(
        [message(PROTECTED_ID), message("newest-unread-fallback")],
        {PROTECTED_ID: [1], "newest-unread-fallback": [1]},
        exact_error=RuntimeError("protected provider detail"),
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


if __name__ == "__main__":
    tests = [value for name, value in globals().copy().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic and mock")
    print("External integrations: not called")
    print("PHI handling: protected synthetic markers suppressed")
