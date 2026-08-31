import contextlib
import io
import json

import scripts.prepare_mailbox_acceptance_handoff as preparation
from src.graph.mailbox_processor import MailboxAcceptanceGuardError


PROTECTED_MARKER = "PROTECTED-SYNTHETIC-IDENTITY"


class NoWriteHandoff:
    create_calls = 0

    def create(self, identity):
        self.create_calls += 1
        raise AssertionError("Diagnostic-only mode must not create a handoff.")


class ZeroEligibleProcessor:
    def prepare_selected_acceptance(self, **kwargs):
        kwargs["stage_observer"](
            stage="candidate_selection",
            status="failed",
            eligible_candidate_count=0,
            not_unread_count=1,
            no_supported_document_count=2,
            multiple_supported_documents_count=3,
            unsupported_document_type_count=1,
            document_count_unprovable_count=2,
            attachment_metadata_request_failed_count=1,
            attachment_metadata_name_unprovable_count=1,
        )
        raise MailboxAcceptanceGuardError("acceptance_no_eligible_candidate")


def test_diagnostic_only_output_is_aggregate_and_creates_no_handoff():
    original_processor = preparation.MailboxProcessor
    original_handoff = preparation.MailboxAcceptanceHandoffService
    preparation.MailboxProcessor = ZeroEligibleProcessor
    preparation.MailboxAcceptanceHandoffService = NoWriteHandoff
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exit_code = preparation.main(["--diagnostic-only"])
    finally:
        preparation.MailboxProcessor = original_processor
        preparation.MailboxAcceptanceHandoffService = original_handoff

    payload = json.loads(output.getvalue())
    assert exit_code == 0
    assert payload == {
        "acceptance_diagnostic_completed": True,
        "acceptance_handoff_ready": False,
        "category": "acceptance_no_eligible_candidate",
        "diagnostics": {
            "eligible_candidate_count": 0,
            "not_unread_count": 1,
            "no_supported_document_count": 2,
            "multiple_supported_documents_count": 3,
            "unsupported_document_type_count": 1,
            "document_count_unprovable_count": 2,
            "attachment_metadata_request_failed_count": 1,
            "attachment_metadata_response_invalid_count": 0,
            "attachment_metadata_item_invalid_count": 0,
            "attachment_metadata_type_unprovable_count": 0,
            "attachment_metadata_inline_state_unprovable_count": 0,
            "attachment_metadata_name_unprovable_count": 1,
            "attachment_metadata_pagination_invalid_count": 0,
            "attachment_metadata_pagination_request_failed_count": 0,
        },
    }
    assert NoWriteHandoff.create_calls == 0
    assert PROTECTED_MARKER not in output.getvalue()


if __name__ == "__main__":
    test_diagnostic_only_output_is_aggregate_and_creates_no_handoff()
    print("Passed: 1")
    print("Failed: 0")
    print("Classification: synthetic deterministic and mock")
    print("External integrations: not called")
    print("PHI handling: aggregate allowlisted eligibility counts only")
