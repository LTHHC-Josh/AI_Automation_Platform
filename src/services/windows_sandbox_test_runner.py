"""Headless, network-disabled Windows Sandbox execution of staged synthetic tests.

Only caller-staged input and a sanitized Python runtime are mapped, read-only.
The production repository, environment, credentials and output folders are not
shared. Result authority is the installed Sandbox CLI process exit-code contract.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from xml.etree.ElementTree import Element, SubElement, tostring


@dataclass(frozen=True)
class SandboxTestResult:
    success: bool
    category: str
    exit_code: int | None = None
    cleanup_proven: bool = False


class WindowsSandboxTestRunner:
    # Explicit infrastructure time budgets, not business confidence thresholds.
    START_TIMEOUT = 180
    TEST_TIMEOUT = 300
    STOP_TIMEOUT = 45

    def __init__(self, *, cli=None, command=None, owner_store=None):
        self.cli = Path(cli or Path(os.environ.get("LOCALAPPDATA", "")) /
                        "Microsoft/WindowsApps/wsb.exe")
        self.command = command or subprocess.run
        self.owner_store = owner_store

    def _stop_owned(self, identity):
        try:
            self._call(["stop", "--raw", "--id", identity], self.STOP_TIMEOUT)
        except Exception:
            # The installed CLI reports an exact empty list when no VM remains.
            state=self._call(["list","--raw"], self.STOP_TIMEOUT)
            if state.get("WindowsSandboxEnvironments") != []:
                raise RuntimeError("sandbox_cleanup_unproven") from None
        if self.owner_store:
            self.owner_store.save("audit","local-sandbox-owner",{"identity":None,"marker":"local-code-v1"})

    def _reserve_owner(self, identity):
        if not self.owner_store:
            return
        prior=self.owner_store.load("audit","local-sandbox-owner")
        if prior and prior.get("identity") is not None:
            if prior.get("marker")!="local-code-v1":
                raise ValueError("sandbox_ownership_unproven")
            previous=prior["identity"]
            if str(uuid.UUID(previous))!=previous:
                raise ValueError("sandbox_ownership_unproven")
            self._stop_owned(previous)
        self.owner_store.save("audit","local-sandbox-owner",{"identity":identity,"marker":"local-code-v1"})

    @staticmethod
    def configuration(input_dir, runtime_dir):
        root = Element("Configuration")
        for name in ("VGpu", "Networking", "ClipboardRedirection", "AudioInput",
                     "VideoInput", "PrinterRedirection"):
            SubElement(root, name).text = "Disable"
        folders = SubElement(root, "MappedFolders")
        for source, destination in ((input_dir, r"C:\TestInput"),
                                    (runtime_dir, r"C:\Python")):
            folder = SubElement(folders, "MappedFolder")
            SubElement(folder, "HostFolder").text = str(Path(source).resolve())
            SubElement(folder, "SandboxFolder").text = destination
            SubElement(folder, "ReadOnly").text = "true"
        return tostring(root, encoding="unicode")

    @staticmethod
    def stage_python(destination, *, base=None, dependencies=()):
        """Copy the stdlib runtime only; exclude site packages, user config and tools."""
        source = Path(base or sys.base_prefix).resolve()
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        for name in ("python.exe", "python3.dll", "python313.dll",
                     "vcruntime140.dll", "vcruntime140_1.dll"):
            original = source / name
            if not original.is_file() or original.is_symlink():
                raise ValueError("sandbox_python_runtime_unavailable")
            shutil.copyfile(original, destination / name)
        for directory in ("Lib", "DLLs"):
            for original in (source / directory).rglob("*"):
                relative = original.relative_to(source)
                if (not original.is_file() or original.is_symlink()
                        or any(part in {"site-packages", "__pycache__", "test", "tests", "idlelib", "ensurepip"} for part in relative.parts)
                        or original.suffix.lower() not in {".py", ".pyd", ".dll"}):
                    continue
                if not original.resolve().is_relative_to(source):
                    raise ValueError("sandbox_python_runtime_invalid")
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, target)
        if dependencies:
            WindowsSandboxTestRunner._stage_dependencies(destination, dependencies)

    @staticmethod
    def _stage_dependencies(destination, dependencies):
        from importlib.metadata import distribution
        from packaging.requirements import Requirement
        pending=list(dependencies); copied=set()
        target_root=Path(destination)/"Lib/site-packages"
        while pending:
            name=pending.pop()
            if name.lower() in copied:
                continue
            dist=distribution(name)
            copied.add(name.lower())
            package_root=Path(dist.locate_file("")).resolve()
            for requirement in dist.requires or ():
                parsed=Requirement(requirement)
                if parsed.marker is None or parsed.marker.evaluate({"extra":""}):
                    pending.append(parsed.name)
            for entry in dist.files or ():
                rel=Path(str(entry))
                if rel.is_absolute() or ".." in rel.parts or rel.suffix.lower() not in {".py",".pyd",".dll",".pem"}:
                    continue
                original=Path(dist.locate_file(entry))
                if original.is_symlink() or not original.resolve().is_relative_to(package_root):
                    raise ValueError("sandbox_dependency_path_invalid")
                if not original.is_file():
                    raise ValueError("sandbox_dependency_unavailable")
                target=target_root/rel
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(original,target)

    def _call(self, args, timeout):
        result = self.command(
            [str(self.cli), *args], capture_output=True, text=True,
            timeout=timeout, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0:
            raise RuntimeError("sandbox_command_failed")
        if len(result.stdout or "") > 4096:
            raise RuntimeError("sandbox_response_invalid")
        return json.loads(result.stdout) if (result.stdout or "").strip() else {}

    def run(self, *, input_dir, runtime_dir):
        input_dir, runtime_dir = Path(input_dir), Path(runtime_dir)
        if (not self.cli.is_file() or not (input_dir / "run_tests.py").is_file()
                or not (runtime_dir / "python.exe").is_file()):
            return SandboxTestResult(False, "sandbox_prerequisite_unavailable")
        # Reserve identity before startup: even a lost startup response can only
        # trigger cleanup of this exact random instance, never an external VM.
        identity = str(uuid.uuid4())
        try:
            self._reserve_owner(identity)
        except Exception:
            return SandboxTestResult(False,"sandbox_ownership_unproven")
        cleanup = False
        outcome = SandboxTestResult(False, "sandbox_start_failed")
        try:
            started = self._call([
                "start", "--raw", "--id", identity, "--config",
                self.configuration(input_dir, runtime_dir)], self.START_TIMEOUT)
            if started.get("Id", "").lower() != identity:
                raise ValueError("sandbox_identity_unproven")
            result = self._call([
                "exec", "--raw", "--id", identity, "-r", "System",
                "-c", r"C:\Python\python.exe -I -S -B C:\TestInput\run_tests.py",
            ], self.TEST_TIMEOUT)
            exit_code = result.get("ExitCode")
            if type(exit_code) is not int:
                outcome = SandboxTestResult(False, "sandbox_response_invalid")
            else:
                outcome = SandboxTestResult(exit_code == 0,
                    "passed" if exit_code == 0 else "sandbox_tests_failed", exit_code)
        except subprocess.TimeoutExpired:
            outcome = SandboxTestResult(False, "sandbox_timeout")
        except Exception:
            outcome = SandboxTestResult(False, "sandbox_execution_unproven")
        finally:
            try:
                self._stop_owned(identity)
                cleanup = True
            except Exception:
                cleanup = False
        # A cleanup failure blocks promotion even if the tests passed.
        return SandboxTestResult(
            outcome.success and cleanup,
            outcome.category if cleanup else "sandbox_cleanup_unproven",
            outcome.exit_code, cleanup,
        )
