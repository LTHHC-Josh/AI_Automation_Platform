"""Development-only guarded writes; not imported by the production service."""
import hashlib
from pathlib import Path


def guarded_write(changes):
    """Verify every reviewed baseline before writing any shared file."""
    for path,expected,content in changes:
        path=Path(path)
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if actual not in (expected,hashlib.sha256(content).hexdigest()):
            raise RuntimeError('concurrent_change_preserved')
    for path,expected,content in changes:
        path=Path(path)
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if actual not in (expected,hashlib.sha256(content).hexdigest()):
            raise RuntimeError('concurrent_change_preserved')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)
