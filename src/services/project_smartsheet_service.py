"""Non-authoritative PROJECT_SMARTSHEET presentation derived from Git history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import os
from pathlib import Path
import re
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_STATE_PATH = PROJECT_ROOT / "PROJECT_STATE.md"
PROJECT_HISTORY_PATH = PROJECT_ROOT / "PROJECT_HISTORY.md"
PROJECT_SMARTSHEET_PATH = PROJECT_ROOT / "PROJECT_SMARTSHEET.md"

# Deliberately conservative repository presentation bound with display/API
# headroom; exceeding it fails before any external sync.
PROJECT_SMARTSHEET_COMMENT_MAX_CHARS = 1800
PROJECT_SMARTSHEET_CHECKPOINT_START = "<!-- PROJECT_SMARTSHEET_CHECKPOINT_START"
PROJECT_SMARTSHEET_CHECKPOINT_END = "PROJECT_SMARTSHEET_CHECKPOINT_END -->"
_CHECKPOINT_PATTERN = re.compile(
    re.escape(PROJECT_SMARTSHEET_CHECKPOINT_START)
    + r"\s*(\{.*?\})\s*"
    + re.escape(PROJECT_SMARTSHEET_CHECKPOINT_END),
    re.DOTALL,
)
_CHECKPOINT_FIELDS = (
    "date",
    "work_summary",
    "key_result",
    "tests",
    "phi_handling",
    "limitation_acceptance",
    "exact_next_start",
)


@dataclass(frozen=True)
class ProjectSmartsheetPresentation:
    """A bounded management view; never an authoritative project record."""

    checkpoint: dict[str, str]
    summary: str


def load_project_smartsheet(
    *,
    state_path: str | Path = PROJECT_STATE_PATH,
    history_path: str | Path = PROJECT_HISTORY_PATH,
) -> ProjectSmartsheetPresentation:
    state_text = Path(state_path).read_text(encoding="utf-8-sig")
    history_text = Path(history_path).read_text(encoding="utf-8-sig")
    current_next_start = extract_current_next_start(state_text)
    checkpoint = extract_latest_smartsheet_checkpoint(history_text)
    if _normalize_text(checkpoint["exact_next_start"]) != _normalize_text(
        current_next_start
    ):
        raise ValueError("project_smartsheet_next_start_mismatch")
    summary = _render_summary(checkpoint)
    if len(summary) > PROJECT_SMARTSHEET_COMMENT_MAX_CHARS:
        raise ValueError("project_smartsheet_summary_too_long")
    return ProjectSmartsheetPresentation(checkpoint=checkpoint, summary=summary)


def extract_current_next_start(state_text: str) -> str:
    marker = "## CURRENT NEXT START"
    if state_text.count(marker) != 1:
        raise ValueError("project_state_next_start_count_invalid")
    value = state_text.split(marker, 1)[1].strip()
    if not value or re.search(r"(?m)^##\s", value):
        raise ValueError("project_state_next_start_invalid")
    return value


def extract_latest_smartsheet_checkpoint(history_text: str) -> dict[str, str]:
    matches = _CHECKPOINT_PATTERN.findall(history_text)
    if not matches:
        raise ValueError("project_history_checkpoint_missing")
    try:
        value: Any = json.loads(matches[-1])
    except (TypeError, ValueError):
        raise ValueError("project_history_checkpoint_invalid") from None
    if not isinstance(value, dict) or tuple(value) != _CHECKPOINT_FIELDS:
        raise ValueError("project_history_checkpoint_schema_invalid")
    checkpoint = {}
    for field in _CHECKPOINT_FIELDS:
        item = value.get(field)
        if not isinstance(item, str) or not item.strip():
            raise ValueError("project_history_checkpoint_value_invalid")
        checkpoint[field] = _normalize_text(item)
    try:
        date.fromisoformat(checkpoint["date"])
    except ValueError:
        raise ValueError("project_history_checkpoint_date_invalid") from None
    return checkpoint


def bound_project_smartsheet_comment(value: str) -> str:
    """Keep only complete sentences when a task comment exceeds the safe bound."""
    normalized = _normalize_text(value)
    if len(normalized) <= PROJECT_SMARTSHEET_COMMENT_MAX_CHARS:
        return normalized
    suffix = " See PROJECT_HISTORY.md for the authoritative detailed record."
    available = PROJECT_SMARTSHEET_COMMENT_MAX_CHARS - len(suffix)
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    selected = []
    for sentence in sentences:
        candidate = " ".join((*selected, sentence))
        if len(candidate) > available:
            break
        selected.append(sentence)
    if not selected:
        raise ValueError("project_smartsheet_comment_sentence_too_long")
    result = " ".join(selected) + suffix
    if len(result) > PROJECT_SMARTSHEET_COMMENT_MAX_CHARS:
        raise ValueError("project_smartsheet_comment_too_long")
    return result


def write_project_smartsheet_snapshot(
    presentation: ProjectSmartsheetPresentation,
    *,
    path: str | Path = PROJECT_SMARTSHEET_PATH,
) -> None:
    destination = Path(path)
    content = (
        "# PROJECT_SMARTSHEET\n\n"
        "> Non-authoritative concise Smartsheet presentation. "
        "PROJECT_STATE.md and PROJECT_HISTORY.md remain authoritative.\n\n"
        "## Current Smartsheet Summary\n\n"
        + presentation.summary
        + "\n\n"
        "## Safety Contract\n\n"
        "- The synchronized cell value is bounded to "
        f"{PROJECT_SMARTSHEET_COMMENT_MAX_CHARS} characters.\n"
        "- The summary is derived from the latest structured checkpoint in "
        "PROJECT_HISTORY.md.\n"
        "- Sync failure cannot modify or remove PROJECT_STATE.md or "
        "PROJECT_HISTORY.md.\n"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, destination)


def _render_summary(checkpoint: dict[str, str]) -> str:
    return "\n".join((
        f"Date: {checkpoint['date']}",
        f"Work: {checkpoint['work_summary']}",
        f"Result: {checkpoint['key_result']}",
        f"Tests: {checkpoint['tests']}",
        f"PHI: {checkpoint['phi_handling']}",
        f"Status: {checkpoint['limitation_acceptance']}",
        f"Next: {checkpoint['exact_next_start']}",
    ))


def _normalize_text(value: str) -> str:
    return " ".join(value.split())
