from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

from src.models.document import Document
from src.services.review_output_service import (
    ReviewOutput,
    ReviewOutputService,
)
from src.services.local_protected_review_errors import (
    ProtectedReviewFailedError,
    ProtectedReviewUnavailableError,
)


@dataclass(repr=False)
class ProtectedReviewViewModel:
    """Protected in-memory state supplied only to the local desktop view."""

    source_path: Path = field(repr=False)
    review_output: ReviewOutput = field(repr=False)


class ProtectedReviewView(Protocol):
    def show(
        self,
        *,
        model: ProtectedReviewViewModel,
        open_document: Callable[[], None],
    ) -> None:
        ...


def _load_tkinter() -> tuple[Any, Any]:
    import tkinter
    from tkinter import ttk

    return tkinter, ttk


class TkinterProtectedReviewView:
    """Synchronous local desktop view for protected review content."""

    def __init__(self) -> None:
        tkinter_module = None
        ttk_module = None

        try:
            tkinter_module, ttk_module = _load_tkinter()
        except Exception:
            pass

        if tkinter_module is None or ttk_module is None:
            raise ProtectedReviewUnavailableError(
                "protected_review_unavailable"
            )

        self._tk = tkinter_module
        self._ttk = ttk_module

    def show(
        self,
        *,
        model: ProtectedReviewViewModel,
        open_document: Callable[[], None],
    ) -> None:
        window = self._tk.Tk()
        window.title("Local Protected Document Review")
        window.geometry("1200x760")
        window.minsize(900, 600)

        container = self._ttk.Frame(
            window,
            padding=12,
        )
        container.pack(
            fill="both",
            expand=True,
        )

        source_status = self._tk.StringVar(
            value="Selected document is available locally."
        )
        open_failed = False

        def handle_open() -> None:
            nonlocal open_failed

            try:
                open_document()
            except Exception:
                open_failed = True
                source_status.set(
                    "Selected document could not be opened."
                )

        source_bar = self._ttk.Frame(container)
        source_bar.pack(fill="x", pady=(0, 10))
        self._ttk.Button(
            source_bar,
            text="Open selected document",
            command=handle_open,
        ).pack(side="left")
        self._ttk.Label(
            source_bar,
            textvariable=source_status,
        ).pack(side="left", padx=(12, 0))

        notebook = self._ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)

        self._add_overview_tab(
            notebook,
            model.review_output,
        )
        self._add_fields_tab(
            notebook,
            model.review_output,
        )
        self._add_service_lines_tab(
            notebook,
            model.review_output,
        )
        self._add_context_tab(
            notebook,
            model.review_output,
        )

        self._ttk.Button(
            container,
            text="Done",
            command=window.destroy,
        ).pack(side="right", pady=(10, 0))

        window.protocol(
            "WM_DELETE_WINDOW",
            window.destroy,
        )
        window.mainloop()

        if open_failed:
            raise ProtectedReviewFailedError(
                "protected_review_failed"
            )

    def _add_overview_tab(
        self,
        notebook: Any,
        output: ReviewOutput,
    ) -> None:
        frame = self._ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="Overview")

        rows = (
            ("Document type", output.document_type),
            ("Document category", output.document_category),
            ("Document subtype", output.document_subtype),
            (
                "Classification confidence",
                self._format_confidence(output.classification_confidence),
            ),
            ("Classification context", output.classification_reason),
            ("Review required", str(bool(output.needs_human_review))),
            ("Review status", output.review_status),
            (
                "Minimum field confidence",
                self._format_optional_confidence(
                    output.minimum_field_confidence
                ),
            ),
            ("Extraction attempts", str(output.extraction_attempt_count)),
            ("Retry triggered", str(output.extraction_retry_triggered)),
            (
                "Selected attempt",
                self._format_value(output.extraction_selected_attempt),
            ),
        )

        for row_number, (label, value) in enumerate(rows):
            self._ttk.Label(
                frame,
                text=label,
            ).grid(row=row_number, column=0, sticky="nw", padx=(0, 12), pady=3)
            self._ttk.Label(
                frame,
                text=self._format_value(value),
                wraplength=850,
                justify="left",
            ).grid(row=row_number, column=1, sticky="nw", pady=3)

        frame.columnconfigure(1, weight=1)

    def _add_fields_tab(
        self,
        notebook: Any,
        output: ReviewOutput,
    ) -> None:
        columns = (
            "field",
            "value",
            "confidence",
            "source_evidence",
            "support_state",
        )
        frame, tree = self._tree_tab(
            notebook,
            title="Extracted fields",
            columns=columns,
            headings=(
                "Field",
                "Extracted value",
                "Confidence",
                "Source evidence",
                "Support state",
            ),
        )

        for review_field in output.fields:
            evidence_present = bool(
                str(review_field.source_text or "").strip()
            )
            tree.insert(
                "",
                "end",
                values=(
                    review_field.name,
                    self._format_value(review_field.value),
                    self._format_confidence(review_field.confidence),
                    review_field.source_text,
                    (
                        "source evidence present"
                        if evidence_present
                        else "source evidence absent"
                    ),
                ),
            )

        self._finish_tree(frame, tree)

    def _add_service_lines_tab(
        self,
        notebook: Any,
        output: ReviewOutput,
    ) -> None:
        columns = (
            "line",
            "code",
            "modifier",
            "quantity",
            "start",
            "end",
            "status",
            "confidence",
            "source_evidence",
            "support_state",
        )
        frame, tree = self._tree_tab(
            notebook,
            title="Service lines",
            columns=columns,
            headings=(
                "Line",
                "Service code",
                "Modifier",
                "Quantity",
                "Start date",
                "End date",
                "Status",
                "Confidence",
                "Source evidence",
                "Support state",
            ),
        )

        for line_number, service_line in enumerate(
            output.service_lines,
            start=1,
        ):
            evidence_present = bool(
                str(service_line.source_text or "").strip()
            )
            tree.insert(
                "",
                "end",
                values=(
                    line_number,
                    self._format_value(service_line.service_code),
                    self._format_value(service_line.modifier),
                    self._format_value(service_line.quantity),
                    self._format_value(service_line.start_date),
                    self._format_value(service_line.end_date),
                    self._format_value(service_line.status),
                    self._format_confidence(service_line.confidence),
                    service_line.source_text,
                    (
                        "source evidence present"
                        if evidence_present
                        else "source evidence absent"
                    ),
                ),
            )

        self._finish_tree(frame, tree)

    def _add_context_tab(
        self,
        notebook: Any,
        output: ReviewOutput,
    ) -> None:
        frame, tree = self._tree_tab(
            notebook,
            title="Validation and review",
            columns=("category", "detail"),
            headings=("Category", "Detail"),
        )

        context_groups = (
            ("Validation", output.validation_actions),
            ("Business rule", output.rule_actions),
            ("Review reason", output.review_reasons),
        )

        for category, details in context_groups:
            for detail in details:
                tree.insert(
                    "",
                    "end",
                    values=(category, detail),
                )

        self._finish_tree(frame, tree)

    def _tree_tab(
        self,
        notebook: Any,
        *,
        title: str,
        columns: tuple[str, ...],
        headings: tuple[str, ...],
    ) -> tuple[Any, Any]:
        frame = self._ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=title)
        tree = self._ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
        )

        for column, heading in zip(columns, headings):
            tree.heading(column, text=heading)
            tree.column(column, width=150, minwidth=90, stretch=True)

        return frame, tree

    def _finish_tree(self, frame: Any, tree: Any) -> None:
        vertical = self._ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview,
        )
        horizontal = self._ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=tree.xview,
        )
        tree.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None:
            return "unknown"

        normalized = str(value)

        if not normalized.strip():
            return "unknown"

        return normalized

    @staticmethod
    def _format_confidence(value: Any) -> str:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            confidence = 0.0

        if confidence > 1:
            confidence = confidence / 100

        confidence = max(0.0, min(confidence, 1.0))
        return f"{confidence:.2f}"

    def _format_optional_confidence(self, value: Any) -> str:
        if value is None:
            return "unknown"

        return self._format_confidence(value)


class LocalProtectedReviewConsumer:
    """Build and synchronously display one local protected review."""

    def __init__(
        self,
        *,
        view_factory: Callable[[], ProtectedReviewView] | None = None,
        document_opener: Callable[[Path], None] | None = None,
    ) -> None:
        self._view_factory = view_factory or TkinterProtectedReviewView
        self._document_opener = document_opener or self._open_with_os_default

    def review(self, document: Document) -> None:
        if not isinstance(document, Document):
            raise ProtectedReviewFailedError(
                "protected_review_failed"
            )

        review_output = document.review_output

        if not isinstance(review_output, ReviewOutput):
            review_output = ReviewOutputService().build(document)

        model = ProtectedReviewViewModel(
            source_path=Path(document.file_path),
            review_output=review_output,
        )
        view = None

        try:
            view = self._view_factory()
        except ProtectedReviewUnavailableError:
            pass
        except Exception:
            pass

        if view is None:
            raise ProtectedReviewUnavailableError(
                "protected_review_unavailable"
            )

        review_failed = False

        try:
            view.show(
                model=model,
                open_document=lambda: self._open_document(
                    model.source_path
                ),
            )
        except Exception:
            review_failed = True

        if review_failed:
            raise ProtectedReviewFailedError(
                "protected_review_failed"
            )

    def _open_document(self, source_path: Path) -> None:
        open_failed = False

        try:
            self._document_opener(source_path)
        except Exception:
            open_failed = True

        if open_failed:
            raise ProtectedReviewFailedError(
                "protected_review_failed"
            )

    @staticmethod
    def _open_with_os_default(source_path: Path) -> None:
        os.startfile(source_path)
