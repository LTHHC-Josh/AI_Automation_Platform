"""Small current-user Windows DPAPI primitive with purpose separation."""

from __future__ import annotations

import ctypes
from ctypes import wintypes


class WindowsDpapiError(RuntimeError):
    """A fixed-category DPAPI failure."""

    def __init__(self, category: str):
        super().__init__(category)
        self.category = category


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


def protect_current_user(data: bytes, *, purpose: bytes) -> bytes:
    if not isinstance(data, bytes) or not isinstance(purpose, bytes) or not purpose:
        raise WindowsDpapiError("dpapi_input_invalid")
    source, source_buffer = _blob(data)
    entropy, entropy_buffer = _blob(purpose)
    output = _DataBlob()
    if not _crypt32.CryptProtectData(
        ctypes.byref(source), None, ctypes.byref(entropy), None, None, 1,
        ctypes.byref(output),
    ):
        raise WindowsDpapiError("dpapi_encryption_failed")
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        _kernel32.LocalFree(output.pbData)
        del source_buffer, entropy_buffer


def unprotect_current_user(data: bytes, *, purpose: bytes) -> bytes:
    if not isinstance(data, bytes) or not isinstance(purpose, bytes) or not purpose:
        raise WindowsDpapiError("dpapi_input_invalid")
    source, source_buffer = _blob(data)
    entropy, entropy_buffer = _blob(purpose)
    output = _DataBlob()
    description = wintypes.LPWSTR()
    if not _crypt32.CryptUnprotectData(
        ctypes.byref(source), ctypes.byref(description), ctypes.byref(entropy), None, None, 1,
        ctypes.byref(output),
    ):
        raise WindowsDpapiError("dpapi_decryption_failed")
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        _kernel32.LocalFree(output.pbData)
        if description:
            _kernel32.LocalFree(description)
        del source_buffer, entropy_buffer
