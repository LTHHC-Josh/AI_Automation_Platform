from dataclasses import dataclass


@dataclass(frozen=True)
class MailboxAcceptanceCandidate:
    """PHI-safe candidate metadata supplied to the local acceptance popup."""

    candidate_number: int
    received_timestamp: str | None
    supported_document_count: int


@dataclass(frozen=True)
class MailboxAcceptanceSelectionResult:
    """PHI-safe local popup outcome containing no mailbox identity."""

    candidate_number: int | None
    popup_displayed: bool
    disposition: str
