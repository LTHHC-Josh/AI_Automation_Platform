"""Current-user sealed, expiring, single-use mailbox acceptance handoff."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Callable


HANDOFF_LEASE_SECONDS = 15 * 60
_PURPOSE = b"LTHHC mailbox acceptance handoff v1"


class MailboxAcceptanceHandoffError(RuntimeError):
    """Sanitized fail-closed handoff error."""

    def __init__(self, category: str):
        super().__init__(category)
        self.category = category


@dataclass(frozen=True, repr=False)
class MailboxAcceptanceHandoff:
    message_identity: str = field(repr=False)


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


_crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_crypt32.CryptProtectData.argtypes = [
    ctypes.POINTER(_DataBlob), wintypes.LPCWSTR, ctypes.POINTER(_DataBlob),
    ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
]
_crypt32.CryptProtectData.restype = wintypes.BOOL
_crypt32.CryptUnprotectData.argtypes = [
    ctypes.POINTER(_DataBlob), ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(_DataBlob),
    ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
]
_crypt32.CryptUnprotectData.restype = wintypes.BOOL
_kernel32.LocalFree.argtypes = [ctypes.c_void_p]
_kernel32.LocalFree.restype = ctypes.c_void_p


def _blob(data: bytes):
    buffer = ctypes.create_string_buffer(data)
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


def _dpapi_protect(data: bytes) -> bytes:
    source, source_buffer = _blob(data)
    entropy, entropy_buffer = _blob(_PURPOSE)
    output = _DataBlob()
    if not _crypt32.CryptProtectData(
        ctypes.byref(source), None, ctypes.byref(entropy), None, None, 1,
        ctypes.byref(output),
    ):
        raise MailboxAcceptanceHandoffError("handoff_encryption_failed")
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        _kernel32.LocalFree(output.pbData)
        del source_buffer, entropy_buffer


def _dpapi_unprotect(data: bytes) -> bytes:
    source, source_buffer = _blob(data)
    entropy, entropy_buffer = _blob(_PURPOSE)
    output = _DataBlob()
    description = wintypes.LPWSTR()
    if not _crypt32.CryptUnprotectData(
        ctypes.byref(source), ctypes.byref(description), ctypes.byref(entropy), None, None, 1,
        ctypes.byref(output),
    ):
        raise MailboxAcceptanceHandoffError("handoff_decryption_failed")
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        _kernel32.LocalFree(output.pbData)
        if description:
            _kernel32.LocalFree(description)
        del source_buffer, entropy_buffer


class MailboxAcceptanceHandoffService:
    """Persist one DPAPI-sealed identity outside configuration and Git."""

    def __init__(
        self,
        directory: Path | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
        protect: Callable[[bytes], bytes] | None = None,
        unprotect: Callable[[bytes], bytes] | None = None,
    ):
        base = os.environ.get("LOCALAPPDATA")
        self.directory = directory or Path(base or tempfile.gettempdir()) / "LTHHC" / "runtime"
        self.path = self.directory / "mailbox-acceptance.handoff"
        self.claim_path = self.directory / "mailbox-acceptance.claim"
        self.lock_path = self.directory / "mailbox-acceptance.lock"
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.protect = protect or _dpapi_protect
        self.unprotect = unprotect or _dpapi_unprotect

    def create(self, message_identity: str) -> None:
        if not isinstance(message_identity, str) or not message_identity:
            raise MailboxAcceptanceHandoffError("handoff_identity_invalid")
        self.directory.mkdir(parents=True, exist_ok=True)
        with self._lock():
            if self.claim_path.exists():
                raise MailboxAcceptanceHandoffError("handoff_already_exists")
            if self.path.exists():
                if not self._existing_is_expired():
                    raise MailboxAcceptanceHandoffError("handoff_already_exists")
                self.path.unlink()
            now = self.clock().astimezone(timezone.utc)
            payload = json.dumps({
                "version": 1,
                "identity": message_identity,
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(seconds=HANDOFF_LEASE_SECONDS)).isoformat(),
            }, separators=(",", ":")).encode("utf-8")
            sealed = self.protect(payload)
            try:
                with self.path.open("xb") as stream:
                    stream.write(sealed)
                    stream.flush()
                    os.fsync(stream.fileno())
            except FileExistsError:
                raise MailboxAcceptanceHandoffError("handoff_already_exists") from None

    def _existing_is_expired(self) -> bool:
        try:
            payload = json.loads(self.unprotect(self.path.read_bytes()).decode("utf-8"))
            expires_at = datetime.fromisoformat(payload["expires_at"])
            return expires_at.tzinfo is not None and (
                self.clock().astimezone(timezone.utc) >= expires_at
            )
        except MailboxAcceptanceHandoffError:
            raise
        except Exception:
            raise MailboxAcceptanceHandoffError("handoff_corrupt") from None

    def claim(self) -> MailboxAcceptanceHandoff:
        self.directory.mkdir(parents=True, exist_ok=True)
        with self._lock():
            return self._claim_locked()

    def _claim_locked(self) -> MailboxAcceptanceHandoff:
        try:
            os.rename(self.path, self.claim_path)
        except FileNotFoundError:
            raise MailboxAcceptanceHandoffError("handoff_missing") from None
        except OSError:
            raise MailboxAcceptanceHandoffError("handoff_claim_failed") from None
        try:
            try:
                raw = self.claim_path.read_bytes()
                payload = json.loads(self.unprotect(raw).decode("utf-8"))
                identity = payload.get("identity")
                expires_at = datetime.fromisoformat(payload["expires_at"])
                if payload.get("version") != 1 or not isinstance(identity, str) or not identity:
                    raise ValueError
                if expires_at.tzinfo is None or self.clock().astimezone(timezone.utc) >= expires_at:
                    raise MailboxAcceptanceHandoffError("handoff_expired")
            except MailboxAcceptanceHandoffError:
                raise
            except Exception:
                raise MailboxAcceptanceHandoffError("handoff_corrupt") from None
            return MailboxAcceptanceHandoff(identity)
        finally:
            self.claim_path.unlink(missing_ok=True)

    def cleanup(self) -> None:
        self.path.unlink(missing_ok=True)
        self.claim_path.unlink(missing_ok=True)

    class _Lock:
        def __init__(self, path: Path): self.path = path
        def __enter__(self):
            for _ in range(100):
                try:
                    self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    return self
                except (FileExistsError, PermissionError):
                    time.sleep(0.01)
            raise MailboxAcceptanceHandoffError("handoff_lock_unavailable")
        def __exit__(self, *_):
            os.close(self.fd)
            self.path.unlink(missing_ok=True)

    def _lock(self):
        return self._Lock(self.lock_path)
