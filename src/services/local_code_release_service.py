"""One-file atomic promotion with sealed before/after receipts and exact rollback.

Called only under the correction repository's exclusive operation lock. This
module never executes candidate code, touches human data, or resets Git.
"""
import hashlib
import os
from pathlib import Path
from uuid import uuid4
from src.services.local_code_candidate_service import TARGETS, validate_candidate


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class LocalCodeReleaseService:
    def __init__(self, *, root, store):
        self.root=Path(root).resolve()
        self.store=store

    def _path(self, relative):
        if relative not in TARGETS.values():
            raise ValueError("local_release_scope_invalid")
        path=self.root/relative
        if path.is_symlink() or not path.resolve().is_relative_to(self.root):
            raise ValueError("local_release_path_invalid")
        return path

    @staticmethod
    def _replace(path, text):
        temporary=path.with_name("."+uuid4().hex+".local-update")
        try:
            with temporary.open("x",encoding="utf-8",newline="\n") as stream:
                stream.write(text); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary,path)
        finally:
            temporary.unlink(missing_ok=True)

    def promote(self, *, receipt, candidate, proof):
        if (proof.passed is not True or proof.cleanup_proven is not True
                or proof.candidate_digest != digest(candidate.after)):
            raise ValueError("local_release_test_proof_invalid")
        validate_candidate(candidate.before,candidate.after,candidate.changed_function)
        identity="local-release:"+receipt
        intended={"path":candidate.path,"before":candidate.before,"after":candidate.after}
        state=self.store.load("audit",identity)
        if state and any(state.get(k)!=v for k,v in intended.items()):
            raise ValueError("local_release_identity_conflict")
        path=self._path(candidate.path)
        current=path.read_text(encoding="utf-8-sig")
        if state and state.get("status")=="rolled_back":
            return "rolled_back"
        if state and current==candidate.after:
            self.store.save("audit",identity,dict(intended,status="promoted"))
            return "promoted"
        if current!=candidate.before:
            raise ValueError("local_release_baseline_changed")
        if not state:
            self.store.save("audit",identity,dict(intended,status="promotion_reserved"))
        self._replace(path,candidate.after)
        if path.read_text(encoding="utf-8-sig")!=candidate.after:
            raise ValueError("local_release_readback_unproven")
        self.store.save("audit",identity,dict(intended,status="promoted"))
        return "promoted"

    def rollback(self, *, receipt):
        identity="local-release:"+receipt
        state=self.store.load("audit",identity)
        if not state:
            raise ValueError("local_rollback_receipt_missing")
        path=self._path(state["path"])
        current=path.read_text(encoding="utf-8-sig")
        if current==state["before"]:
            state["status"]="rolled_back"; self.store.save("audit",identity,state)
            return "rolled_back"
        if current!=state["after"]:
            raise ValueError("local_rollback_external_change")
        self._replace(path,state["before"])
        if path.read_text(encoding="utf-8-sig")!=state["before"]:
            raise ValueError("local_rollback_readback_unproven")
        state["status"]="rolled_back"; self.store.save("audit",identity,state)
        return "rolled_back"
