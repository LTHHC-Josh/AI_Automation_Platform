"""Windows process exclusion and crash-persistent activation quarantine."""
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
import msvcrt
import threading
from src.services.local_correction_memory_service import LocalCorrectionStore

ROOT=Path(__file__).resolve().parents[2]
_mutex=threading.RLock()
_local=threading.local()

@contextmanager
def source_lease(root=ROOT):
    root=Path(root).resolve()
    if getattr(_local,"root",None)==root:
        yield
        return
    if not _mutex.acquire(blocking=False):
        raise RuntimeError("local_source_activation_busy")
    stream=None; locked=False
    try:
        path=root/"data/smartsheet_feedback/source-activation.lock"
        path.parent.mkdir(parents=True,exist_ok=True)
        stream=path.open("a+b")
        if path.stat().st_size==0:
            stream.write(b"0"); stream.flush()
        stream.seek(0)
        try: msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        except OSError: raise RuntimeError("local_source_activation_busy") from None
        locked=True; _local.root=root
        yield
    finally:
        _local.root=None
        if stream:
            if locked:
                stream.seek(0); msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            stream.close()
        _mutex.release()

@contextmanager
def document_source_ready(*,root=ROOT,store=None):
    with source_lease(root):
        state=(store or LocalCorrectionStore()).load("audit","local-source-activation")
        if state and state.get("pending") is not False:
            raise RuntimeError("local_source_activation_unverified")
        yield

def guard_document_source(function):
    @wraps(function)
    def guarded(*args,**kwargs):
        with document_source_ready():
            return function(*args,**kwargs)
    return guarded
