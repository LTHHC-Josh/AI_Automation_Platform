"""Resolution-authorized local candidate/test/release transaction. No Codex."""
from dataclasses import asdict
from pathlib import Path
import subprocess

from src.services.local_code_candidate_service import LocalCodeCandidateService, LocalCodeCandidate, TARGETS
from src.services.local_candidate_test_service import LocalCandidateTestService, LocalCandidateTestResult
from src.services.local_code_release_service import LocalCodeReleaseService, digest
from src.services.local_code_update_authorization import LocalCodeUpdateAuthorization
from src.services.local_source_activation_gate import source_lease


class LocalCodeUpdateService:
    TERMINAL=frozenset({"guidance_only","promoted","rolled_back","scope_unavailable",
                       "generation_unresolved","tests_failed","update_failed"})

    def __init__(self, *, root, store, generator=None, tester=None, release=None, source_ready=None):
        self.root=Path(root).resolve(); self.store=store
        self.generator=generator or LocalCodeCandidateService()
        self.tester=tester or LocalCandidateTestService()
        self.release=release or LocalCodeReleaseService(root=self.root,store=store)
        self.source_ready=source_ready or self._source_ready

    def _source_ready(self):
        result=subprocess.run(["git","status","--porcelain","--untracked-files=normal"],
            cwd=self.root,capture_output=True,text=True,timeout=30,check=False)
        if result.returncode: return False
        # Previous local releases have sealed provenance. Never overwrite unrelated
        # human edits or treat arbitrary dirty source as an approved baseline.
        heads=(self.store.load("audit","local-release-heads") or {}).get("files",{})
        for line in result.stdout.splitlines():
            if not line.startswith(" M "): return False
            relative=line[3:]
            if relative not in TARGETS.values() or relative not in heads: return False
            if digest((self.root/relative).read_text(encoding="utf-8-sig"))!=heads[relative]:
                return False
        return True

    def _head(self,candidate,*,rollback=False):
        state=self.store.load("audit","local-release-heads") or {"files":{}}
        state["files"][candidate.path]=digest(candidate.before if rollback else candidate.after)
        self.store.save("audit","local-release-heads",state)

    def process(self,*,receipt,family,code):
        # Workflow already verified the exact human approval. This immutable record
        # also prevents reusing that approval with a changed generalized intent.
        authorization=self.store.load("audit","local-code-update:"+receipt)
        if not authorization or authorization.get("intent",{}).get("resolution_approved") is not True:
            return "approval_unproven"
        LocalCodeUpdateAuthorization(self.store).record(
            receipt=receipt,family=family,code=code,resolution_verified=True)
        identity="local-code-job:"+receipt
        state=self.store.load("audit",identity) or {"phase":"pending"}
        if state["phase"] in self.TERMINAL: return state["phase"]
        try:
            if state["phase"]=="pending":
                if code not in TARGETS:
                    state["phase"]="scope_unavailable"
                    self.store.save("audit",identity,state); return state["phase"]
                if not self.source_ready(): return "waiting_for_clean_source"
                state["phase"]="generating"
                self.store.save("audit",identity,state)
                candidate=self.generator.propose(root=self.root,family=family,code=code)
                if candidate is None:
                    state["phase"]="guidance_only"
                    self.store.save("audit",identity,state); return state["phase"]
                state["candidate"]=asdict(candidate); state["phase"]="testing"
                self.store.save("audit",identity,state)
            elif state["phase"]=="generating":
                # Do not silently repeat an interrupted model generation.
                state["phase"]="generation_unresolved"
                self.store.save("audit",identity,state); return state["phase"]
            candidate=LocalCodeCandidate(**state["candidate"])
            if state["phase"]=="testing":
                proof=self.tester.verify(root=self.root,candidate=candidate)
                if not proof.passed or not proof.cleanup_proven:
                    state["phase"]="tests_failed"
                    self.store.save("audit",identity,state); return state["phase"]
                if not self.source_ready(): return "waiting_for_clean_source"
                state["proof"]=asdict(proof); state["phase"]="promoting"
                self.store.save("audit",identity,state)
            if state["phase"]=="promoting":
                with source_lease(self.root):
                    activation=self.store.load("audit","local-source-activation")
                    if activation and activation.get("pending") is not False and activation.get("receipt")!=receipt:
                        return "update_failed"
                    # Quarantine persists after crash, unlike an OS lock. No new
                    # document may consume source until health/rollback is proven.
                    self.store.save("audit","local-source-activation",{"pending":True,"receipt":receipt})
                    result=self.release.promote(receipt=receipt,candidate=candidate,
                        proof=LocalCandidateTestResult(**state["proof"]))
                    if result=="rolled_back":
                        state["phase"]="rolled_back"
                    else:
                        self._head(candidate)
                        health=self.tester.verify(root=self.root,candidate=candidate,applied=True)
                        if not health.passed or not health.cleanup_proven:
                            self.release.rollback(receipt=receipt)
                            self._head(candidate,rollback=True)
                            state["phase"]="rolled_back"
                        else:
                            state["phase"]="promoted"
                    self.store.save("audit","local-source-activation",{"pending":False,"receipt":receipt})
                self.store.save("audit",identity,state)
                return state["phase"]
            return "update_failed"
        except Exception:
            # If promotion may have happened, preserve its phase/receipt for exact
            # recovery rather than guessing failure or overwriting somebody's edit.
            if state.get("phase")!="promoting":
                state["phase"]="update_failed"; self.store.save("audit",identity,state)
            return "update_failed"
