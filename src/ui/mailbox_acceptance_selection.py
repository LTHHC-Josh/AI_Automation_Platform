from __future__ import annotations

from typing import Any, Callable, Protocol

from src.models.mailbox_acceptance import (
    MailboxAcceptanceCandidate,
    MailboxAcceptanceSelectionResult,
)


class MailboxAcceptanceSelectionUnavailableError(RuntimeError):
    """The local acceptance selector could not be displayed safely."""


class MailboxAcceptanceSelectionView(Protocol):
    def show(
        self,
        *,
        candidates: tuple[MailboxAcceptanceCandidate, ...],
    ) -> MailboxAcceptanceSelectionResult:
        ...


def safe_candidate_display_values(
    candidate: MailboxAcceptanceCandidate,
) -> tuple[str, str, int]:
    """Build the complete allowlisted row shown by the acceptance popup."""
    return (
        f"Candidate {candidate.candidate_number}",
        candidate.received_timestamp or "Unavailable",
        candidate.supported_document_count,
    )


def _load_tkinter() -> tuple[Any, Any]:
    import tkinter
    from tkinter import ttk

    return tkinter, ttk


class TkinterMailboxAcceptanceSelectionView:
    """Synchronous local popup containing only PHI-safe candidate labels."""

    def __init__(self) -> None:
        tkinter_module = None
        ttk_module = None
        try:
            tkinter_module, ttk_module = _load_tkinter()
        except Exception:
            pass
        if tkinter_module is None or ttk_module is None:
            raise MailboxAcceptanceSelectionUnavailableError(
                "acceptance_selection_unavailable"
            )
        self._tk = tkinter_module
        self._ttk = ttk_module

    def show(
        self,
        *,
        candidates: tuple[MailboxAcceptanceCandidate, ...],
    ) -> MailboxAcceptanceSelectionResult:
        window = self._tk.Tk()
        window.title("Select Manual Mailbox Acceptance Candidate")
        window.geometry("720x420")
        window.minsize(560, 300)
        selected_number: int | None = None
        disposition = "no_selection"
        popup_displayed = True

        container = self._ttk.Frame(window, padding=12)
        container.pack(fill="both", expand=True)
        self._ttk.Label(
            container,
            text="Select exactly one eligible candidate for this manual acceptance.",
        ).pack(anchor="w", pady=(0, 10))

        tree = self._ttk.Treeview(
            container,
            columns=("candidate", "received", "documents"),
            show="headings",
            selectmode="browse",
        )
        tree.heading("candidate", text="Candidate")
        tree.heading("received", text="Received (UTC)")
        tree.heading("documents", text="Supported documents")
        tree.column("candidate", width=150, minwidth=120, stretch=False)
        tree.column("received", width=300, minwidth=220, stretch=True)
        tree.column("documents", width=170, minwidth=150, stretch=False)
        tree.pack(fill="both", expand=True)

        for candidate in candidates:
            tree.insert(
                "",
                "end",
                iid=str(candidate.candidate_number),
                values=safe_candidate_display_values(candidate),
            )

        def choose() -> None:
            nonlocal selected_number, disposition
            selection = tree.selection()
            if len(selection) != 1:
                disposition = "no_selection"
                window.destroy()
                return
            try:
                selected_number = int(selection[0])
            except (TypeError, ValueError):
                disposition = "no_selection"
                window.destroy()
                return
            disposition = "selected"
            window.destroy()

        def cancel() -> None:
            nonlocal disposition
            disposition = "cancelled"
            window.destroy()

        def close() -> None:
            nonlocal disposition
            disposition = "closed"
            window.destroy()

        actions = self._ttk.Frame(container)
        actions.pack(fill="x", pady=(10, 0))
        self._ttk.Button(
            actions,
            text="Cancel",
            command=cancel,
        ).pack(side="right")
        self._ttk.Button(
            actions,
            text="Process selected candidate",
            command=choose,
        ).pack(side="right", padx=(0, 8))
        tree.bind("<Double-1>", lambda _event: choose())
        window.protocol("WM_DELETE_WINDOW", close)
        window.mainloop()
        return MailboxAcceptanceSelectionResult(
            candidate_number=selected_number,
            popup_displayed=popup_displayed,
            disposition=disposition,
        )


class LocalMailboxAcceptanceSelector:
    """Return only a safe candidate number from a local synchronous popup."""

    def __init__(
        self,
        *,
        view_factory: Callable[[], MailboxAcceptanceSelectionView] | None = None,
    ) -> None:
        self._view_factory = view_factory or TkinterMailboxAcceptanceSelectionView

    def select(
        self,
        candidates: tuple[MailboxAcceptanceCandidate, ...],
    ) -> MailboxAcceptanceSelectionResult:
        try:
            view = self._view_factory()
            return view.show(candidates=candidates)
        except MailboxAcceptanceSelectionUnavailableError:
            pass
        except Exception:
            pass
        raise MailboxAcceptanceSelectionUnavailableError(
            "acceptance_selection_unavailable"
        )
