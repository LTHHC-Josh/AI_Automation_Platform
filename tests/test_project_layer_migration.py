import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.project_smartsheet_service import (
    PROJECT_SMARTSHEET_COMMENT_MAX_CHARS,
    bound_project_smartsheet_comment,
    extract_current_next_start,
    extract_latest_smartsheet_checkpoint,
    load_project_smartsheet,
    write_project_smartsheet_snapshot,
)


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_LEGACY_HASHES = {
    "LEGACY_PROJECT_MEMORY": (
        "b3cdade975fdd3d01168567d413d2ef9e035e799928a548b439eee73e1ea41fc"
    ),
    "LEGACY_PROJECT_JOURNAL": (
        "d764b370a77528f22df36183cc4133b3c945efea1934cd7ed2619e28551230c9"
    ),
    "LEGACY_TRACKER_UPDATES": (
        "c09ed37b76ff958bf3c1ba7d523184931aa7e6fead81b312274a6079c2e51e8d"
    ),
}


def read(path):
    return path.read_text(encoding="utf-8-sig")


def normalized_digest(value):
    return hashlib.sha256(value.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def historical_payload(history, name):
    start = f"<!-- {name}_START -->"
    end = f"<!-- {name}_END -->"
    assert history.count(start) == 1
    assert history.count(end) == 1
    return history.split(start, 1)[1].split(end, 1)[0].strip("\n")


def test_all_legacy_content_payloads_are_preserved_verbatim():
    history = read(ROOT / "PROJECT_HISTORY.md")
    for name, expected in EXPECTED_LEGACY_HASHES.items():
        assert normalized_digest(historical_payload(history, name)) == expected
    assert "Legacy memory characters: `115945`" in history
    assert "Legacy journal characters: `407495`" in history
    assert "Legacy tracker-updates characters: `26273`" in history


def test_project_history_retains_complete_audit_categories():
    history = read(ROOT / "PROJECT_HISTORY.md")
    assert "Legacy `PROJECT_MEMORY.md` section map:" in history
    assert "Legacy tracker content map:" in history
    assert history.count("Exact next start:") >= 30
    for required in (
        "Files changed", "Passed:", "Failed:", "PHI", "Synthetic",
        "Real", "limitations", "checkpoint",
    ):
        assert required.casefold() in history.casefold()


def test_project_state_is_current_focused_with_one_next_start():
    state = read(ROOT / "PROJECT_STATE.md")
    assert state.count("## CURRENT NEXT START") == 1
    assert "checkpoint (2026-" not in state.casefold()
    assert "PROJECT_STATE.md" in state
    assert "PROJECT_HISTORY.md" in state
    assert "PROJECT_SMARTSHEET.md" in state
    assert "business_context_version`: 1" in state
    assert "analysis_contract_version`: 3" in state


def test_project_smartsheet_is_derived_bounded_and_next_start_exact():
    state = read(ROOT / "PROJECT_STATE.md")
    history = read(ROOT / "PROJECT_HISTORY.md")
    presentation = load_project_smartsheet()
    checkpoint = extract_latest_smartsheet_checkpoint(history)
    assert presentation.checkpoint == checkpoint
    assert len(presentation.summary) <= PROJECT_SMARTSHEET_COMMENT_MAX_CHARS
    assert checkpoint["exact_next_start"] == " ".join(
        extract_current_next_start(state).split()
    )
    assert "Work:" in presentation.summary
    assert "Result:" in presentation.summary
    assert "Tests:" in presentation.summary
    assert "PHI:" in presentation.summary
    assert "Status:" in presentation.summary
    assert "Next:" in presentation.summary


def test_project_smartsheet_snapshot_is_explicitly_non_authoritative():
    snapshot = read(ROOT / "PROJECT_SMARTSHEET.md")
    presentation = load_project_smartsheet()
    assert "Non-authoritative concise Smartsheet presentation" in snapshot
    assert presentation.summary in snapshot
    assert "PROJECT_STATE.md and PROJECT_HISTORY.md remain authoritative" in snapshot


def test_task_comment_bounding_keeps_complete_sentences():
    sentence = "A complete project statement."
    oversized = " ".join(sentence for _ in range(100))
    result = bound_project_smartsheet_comment(oversized)
    assert len(result) <= PROJECT_SMARTSHEET_COMMENT_MAX_CHARS
    assert result.endswith(
        "See PROJECT_HISTORY.md for the authoritative detailed record."
    )
    retained = result.split(" See PROJECT_HISTORY.md", 1)[0]
    assert retained.endswith(".")
    assert retained.count(sentence) > 1


def test_every_project_smartsheet_task_comment_is_bounded():
    spec = importlib.util.spec_from_file_location(
        "project_tracker_comments", ROOT / "update_project_tracker.py"
    )
    tracker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tracker)
    updates = tracker.project_smartsheet_updates(load_project_smartsheet())
    assert len(updates) == 38
    assert all(
        0 < len(comment) <= PROJECT_SMARTSHEET_COMMENT_MAX_CHARS
        for _, _, comment in updates
    )
    assert updates[0][2] == load_project_smartsheet().summary


def test_sync_failure_cannot_modify_authoritative_history():
    spec = importlib.util.spec_from_file_location(
        "project_tracker_under_test", ROOT / "update_project_tracker.py"
    )
    tracker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tracker)
    history_path = ROOT / "PROJECT_HISTORY.md"
    before = normalized_digest(read(history_path))

    class FailingTasks:
        def find_task(self, task_name):
            raise RuntimeError("synthetic_sync_failure")

    class FailingProjectStatusService:
        def __init__(self):
            self.tasks = FailingTasks()

    tracker.ProjectStatusService = FailingProjectStatusService
    tracker.write_project_smartsheet_snapshot = lambda presentation: None
    with contextlib.redirect_stdout(io.StringIO()):
        tracker.synchronize_project_smartsheet()
    assert normalized_digest(read(history_path)) == before


def test_snapshot_write_does_not_touch_state_or_history():
    state = read(ROOT / "PROJECT_STATE.md")
    history = read(ROOT / "PROJECT_HISTORY.md")
    with TemporaryDirectory() as directory:
        destination = Path(directory) / "PROJECT_SMARTSHEET.md"
        write_project_smartsheet_snapshot(
            load_project_smartsheet(), path=destination
        )
        assert destination.exists()
    assert read(ROOT / "PROJECT_STATE.md") == state
    assert read(ROOT / "PROJECT_HISTORY.md") == history


def test_begin_end_day_and_codex_references_use_new_layers():
    agents = read(ROOT / "AGENTS.md")
    codex = read(ROOT / "src/services/document_processor_training_codex_service.py")
    assert "read all of `PROJECT_STATE.md`" in agents
    assert "latest relevant checkpoint in `PROJECT_HISTORY.md`" in agents
    assert "append the complete checkpoint to `PROJECT_HISTORY.md`" in agents
    assert "refresh the derived `PROJECT_SMARTSHEET.md`" in agents
    assert "PROJECT_STATE.md, then the latest relevant PROJECT_HISTORY.md" in codex


def test_no_active_project_memory_dependency_remains():
    assert not (ROOT / "PROJECT_MEMORY.md").exists()
    sources = [
        ROOT / "AGENTS.md",
        ROOT / "PROJECT_STATE.md",
        ROOT / "update_project_tracker.py",
        *sorted((ROOT / "src").rglob("*.py")),
        *sorted(
            path
            for path in (ROOT / "tests").rglob("*.py")
            if path != Path(__file__).resolve()
        ),
        *sorted((ROOT / "docs").rglob("*.md")),
    ]
    stale = [str(path.relative_to(ROOT)) for path in sources if "PROJECT_MEMORY.md" in read(path)]
    assert stale == []


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic project-layer migration")
    print("External integrations: not called")
    print("PHI handling: repository metadata and synthetic values only")
