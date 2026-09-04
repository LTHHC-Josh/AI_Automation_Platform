"""Single-attempt, PHI-safe Codex dispatcher for approved corrections."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable

from src.services.document_processor_training_analysis_service import (
    PhiSafeImplementationTask,
    serialize_phi_safe_task,
)


@dataclass(frozen=True)
class CodexDispatchResult:
    success: bool
    status: str
    attempt_started: bool
    committed: bool
    pushed: bool
    commit_sha: str = ""
    retryable: bool = False
    changed_layers: tuple[str, ...] = ()
    business_context_version_after: int = 0


class BoundedCodexDispatcher:
    """Run at most one ephemeral Codex process for one validated task."""

    TIMEOUT_SECONDS = 60 * 60
    RESULT_SCHEMA = Path("src/contracts/dp_training_codex_result.schema.json")
    LOCK_PATH = Path("data/smartsheet_feedback/codex-implementation.lock")

    def __init__(
        self,
        *,
        repository_root: str | Path | None = None,
        enabled: bool = False,
        timeout_seconds: int = TIMEOUT_SECONDS,
    ) -> None:
        self.repository_root = Path(repository_root or Path(__file__).resolve().parents[2])
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds

    def dispatch(
        self,
        task: PhiSafeImplementationTask,
        *,
        on_started: Callable[[], None] | None = None,
    ) -> CodexDispatchResult:
        process = None
        process_started = False
        try:
            task_json = serialize_phi_safe_task(task)
        except Exception:
            return self._failure("codex_task_invalid")
        if not self.enabled:
            return self._failure("codex_dispatch_disabled")
        if not self._repository_ready():
            return CodexDispatchResult(
                False, "codex_repository_waiting", False, False, False, retryable=True
            )
        lock = self.repository_root / self.LOCK_PATH
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return CodexDispatchResult(
                False, "codex_repository_locked", False, False, False, retryable=True
            )
        except OSError:
            return self._failure("codex_lock_unavailable")
        try:
            os.write(descriptor, (task.task_id + "\n").encode("ascii"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        result_path = lock.with_suffix(".result.json")
        try:
            codex = shutil.which("codex.cmd") or shutil.which("codex")
            schema = self.repository_root / self.RESULT_SCHEMA
            if codex is None or not schema.is_file():
                return self._failure("codex_runtime_unavailable")
            prompt = self._prompt(task_json)
            command = [
                codex,
                "exec",
                "--ephemeral",
                "--sandbox",
                "workspace-write",
                "--approve-for-me",
                "--cd",
                str(self.repository_root),
                "--output-schema",
                str(schema),
                "--output-last-message",
                str(result_path),
                "-",
            ]
            creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            process = subprocess.Popen(
                command,
                cwd=self.repository_root,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                creationflags=creation_flags,
            )
            process_started = True
            if on_started is not None:
                on_started()
            try:
                process.communicate(prompt, timeout=self.timeout_seconds)
            except subprocess.TimeoutExpired:
                self._terminate_process_tree(process.pid)
                return CodexDispatchResult(
                    False, "codex_timeout", True, False, False, retryable=False
                )
            if process.returncode != 0:
                return CodexDispatchResult(
                    False, "codex_failed", True, False, False, retryable=False
                )
            parsed = self._read_result(result_path)
            if parsed and parsed.get("outcome") == "requires_external_system":
                return CodexDispatchResult(
                    False, "codex_requires_external_system", True, False, False,
                    retryable=False,
                )
            if parsed is None or parsed.get("outcome") != "implemented":
                status = "codex_needs_more_information" if (
                    parsed and parsed.get("outcome") == "needs_more_information"
                ) else "codex_incomplete"
                return CodexDispatchResult(
                    False, status, True, False, False, retryable=False
                )
            if parsed.get("failure_category") != "none":
                return CodexDispatchResult(
                    False, "codex_safety_gate_failed", True, False, False,
                    retryable=False,
                )
            if not self._valid_context_result(parsed, task):
                return CodexDispatchResult(
                    False, "codex_context_verification_failed", True, False, False,
                    retryable=False,
                )
            required_gates = (
                "compiled",
                "focused_tests_passed",
                "affected_tests_passed",
                "tracker_passed",
                "git_safety_passed",
                "pushed",
            )
            if any(parsed.get(name) is not True for name in required_gates):
                return CodexDispatchResult(
                    False, "codex_safety_gate_failed", True, False, False,
                    retryable=False,
                )
            commit_sha = str(parsed.get("commit_sha") or "").strip().lower()
            if not self._verified_committed_sync(commit_sha):
                return CodexDispatchResult(
                    False, "codex_git_verification_failed", True, False, False,
                    retryable=False,
                )
            return CodexDispatchResult(
                True, "codex_implemented", True, True, True, commit_sha, False,
                tuple(parsed.get("changed_layers", ())),
                parsed.get("business_context_version_after", 0),
            )
        except Exception:
            if process is not None and process.poll() is None:
                self._terminate_process_tree(process.pid)
            return CodexDispatchResult(
                False, "codex_dispatch_failed", process_started, False, False,
                retryable=False,
            )
        finally:
            try:
                result_path.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                lock.unlink(missing_ok=True)
            except OSError:
                pass

    def _repository_ready(self) -> bool:
        try:
            status = self._git("status", "--porcelain")
            relation = self._git("rev-list", "--left-right", "--count", "HEAD...origin/main")
            return status == "" and relation.split() == ["0", "0"]
        except Exception:
            return False

    def _verified_committed_sync(self, commit_sha: str) -> bool:
        if len(commit_sha) != 40 or any(value not in "0123456789abcdef" for value in commit_sha):
            return False
        try:
            return (
                self._git("status", "--porcelain") == ""
                and self._git("rev-parse", "HEAD") == commit_sha
                and self._git("rev-parse", "origin/main") == commit_sha
                and self._git(
                    "rev-list", "--left-right", "--count", "HEAD...origin/main"
                ).split()
                == ["0", "0"]
            )
        except Exception:
            return False

    @staticmethod
    def _valid_context_result(
        parsed: dict[str, Any], task: PhiSafeImplementationTask
    ) -> bool:
        layers = parsed.get("changed_layers")
        before = parsed.get("business_context_version_before")
        after = parsed.get("business_context_version_after")
        analysis_version = parsed.get("analysis_contract_version")
        if (
            not isinstance(layers, list)
            or any(not isinstance(item, str) for item in layers)
            or isinstance(before, bool)
            or not isinstance(before, int)
            or isinstance(after, bool)
            or not isinstance(after, int)
            or before != task.business_context_version
            or analysis_version != task.analysis_contract_version
        ):
            return False
        context_changed = "Business Context" in layers
        return after > before if context_changed else after == before

    def _git(self, *arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=self.repository_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("git_check_failed")
        return completed.stdout.strip()

    @staticmethod
    def _read_result(path: Path) -> dict[str, Any] | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _terminate_process_tree(process_id: int) -> None:
        try:
            subprocess.run(
                ["taskkill.exe", "/PID", str(process_id), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
                check=False,
            )
        except Exception:
            pass

    @staticmethod
    def _prompt(task_json: str) -> str:
        return (
            "Implement exactly one approved PHI-safe correction task. Read AGENTS.md "
            "and all PROJECT_MEMORY.md first. Preserve uncommitted work. Inspect callers "
            "and tests, make the smallest safe change, compile, run focused and affected "
            "regressions, update tracker and continuity when truth changes, and perform "
            "the full Git/PHI safety review. Commit and push only if every gate passes. "
            "Never access live Smartsheet, mailbox, OCR, Ollama, protected documents, or "
            "protected local state. Determine which durable layers changed and whether "
            "the shared business context/rule source needs a generalized update. Never "
            "create a patient-specific or unsupported payer-specific rule. Return only "
            "the required JSON result.\n\n"
            + task_json
        )

    @staticmethod
    def _failure(status: str) -> CodexDispatchResult:
        return CodexDispatchResult(False, status, False, False, False, retryable=False)
