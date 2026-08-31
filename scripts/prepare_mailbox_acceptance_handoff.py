"""Prepare one PHI-safe sealed mailbox acceptance handoff before worker start."""

from __future__ import annotations

import argparse
import json

from src.graph.mailbox_processor import MailboxAcceptanceGuardError, MailboxProcessor
from src.services.mailbox_acceptance_handoff_service import (
    MailboxAcceptanceHandoffError,
    MailboxAcceptanceHandoffService,
)
from src.ui.mailbox_acceptance_selection import LocalMailboxAcceptanceSelector
from src.models.mailbox_acceptance import MailboxAcceptanceSelectionResult


_DIAGNOSTIC_FIELDS = (
    "eligible_candidate_count",
    "not_unread_count",
    "no_supported_document_count",
    "multiple_supported_documents_count",
    "unsupported_document_type_count",
    "document_count_unprovable_count",
    "attachment_metadata_request_failed_count",
    "attachment_metadata_response_invalid_count",
    "attachment_metadata_item_invalid_count",
    "attachment_metadata_type_unprovable_count",
    "attachment_metadata_inline_state_unprovable_count",
    "attachment_metadata_name_unprovable_count",
    "attachment_metadata_pagination_invalid_count",
    "attachment_metadata_pagination_request_failed_count",
)


class _DiagnosticOnlySelector:
    def select(self, candidates):
        return MailboxAcceptanceSelectionResult(
            candidate_number=None,
            popup_displayed=False,
            disposition="no_selection",
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostic-only", action="store_true")
    arguments = parser.parse_args(argv)
    handoff = MailboxAcceptanceHandoffService()
    diagnostics = {name: 0 for name in _DIAGNOSTIC_FIELDS}

    def observe(**event):
        if event.get("stage") != "candidate_selection":
            return
        for name in _DIAGNOSTIC_FIELDS:
            value = event.get(name)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                diagnostics[name] = value

    try:
        identity = MailboxProcessor().prepare_selected_acceptance(
            selector=(
                _DiagnosticOnlySelector()
                if arguments.diagnostic_only
                else LocalMailboxAcceptanceSelector()
            ),
            discovery_top=10,
            acceptance_max_messages=1,
            acceptance_max_documents=1,
            stage_observer=observe,
        )
        if arguments.diagnostic_only:
            raise RuntimeError("diagnostic_selector_returned_identity")
        handoff.create(identity)
    except (MailboxAcceptanceGuardError, MailboxAcceptanceHandoffError) as error:
        output = {
            "acceptance_handoff_ready": False,
            "category": error.category,
            "diagnostics": diagnostics,
        }
        if arguments.diagnostic_only and error.category in {
            "acceptance_no_eligible_candidate",
            "acceptance_selection_no_selection",
        }:
            output["acceptance_diagnostic_completed"] = True
            print(json.dumps(output, sort_keys=True))
            return 0
        print(json.dumps(output, sort_keys=True))
        return 1
    except Exception:
        print(json.dumps({"acceptance_handoff_ready": False,
                          "category": "acceptance_handoff_preparation_failed"}))
        return 1
    print(json.dumps({
        "acceptance_handoff_ready": True,
        "diagnostics": diagnostics,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
