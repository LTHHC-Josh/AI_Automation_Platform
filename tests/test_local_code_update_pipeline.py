"""Synthetic/mock local update transaction, capability and rollback regressions."""
import ast
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as N

from src.services.local_code_candidate_service import LocalCodeCandidate, validate_candidate
from src.services.local_code_release_service import LocalCodeReleaseService, digest
from src.services.local_code_update_authorization import LocalCodeUpdateAuthorization
from src.services.local_code_update_service import LocalCodeUpdateService
from src.services.local_candidate_test_service import LocalCandidateTestResult

BEFORE="class Rule:\n    def apply(self, value):\n        return value\n"
AFTER="class Rule:\n    def apply(self, value):\n        if value is None:\n            return None\n        return value\n"
PATH="src/services/filename_policy_service.py"

class Store:
    def __init__(self): self.data={}
    def load(self,kind,key): return deepcopy(self.data.get((kind,key)))
    def save(self,kind,key,value): self.data[kind,key]=deepcopy(value)

def candidate(): return LocalCodeCandidate(PATH,BEFORE,AFTER,"Rule.apply")
def proof(): return LocalCandidateTestResult(True,"passed",digest(AFTER),True)
def make(root):
    path=root/PATH; path.parent.mkdir(parents=True); path.write_text(BEFORE,encoding="utf-8")
    return path

def test_pure_body_change_allowed():
    assert validate_candidate(BEFORE,AFTER,"Rule.apply")

def test_new_capabilities_and_literals_denied():
    for body in ("return open(value)","return value.__class__","import os\nreturn value",
                 "return eval(value)","return 'synthetic-invented-value'",
                 "global other\nreturn value","return value.read_text()"):
        after="class Rule:\n    def apply(self, value):\n"+"".join("        "+x+"\n" for x in body.splitlines())
        try: validate_candidate(BEFORE,after,"Rule.apply")
        except ValueError: pass
        else: raise AssertionError("new capability accepted")

def test_changes_outside_method_denied():
    for after in (AFTER+"other=1\n", AFTER.replace("self, value","self, value, other"),
                  "import os\n"+AFTER):
        try: validate_candidate(BEFORE,after,"Rule.apply")
        except ValueError: pass
        else: raise AssertionError("unapproved scope accepted")

def test_exact_promotion_idempotent_and_rollback():
    with TemporaryDirectory() as directory:
        root=Path(directory); path=make(root); store=Store()
        release=LocalCodeReleaseService(root=root,store=store)
        assert release.promote(receipt="a"*64,candidate=candidate(),proof=proof())=="promoted"
        assert path.read_text()==AFTER
        assert release.promote(receipt="a"*64,candidate=candidate(),proof=proof())=="promoted"
        assert release.rollback(receipt="a"*64)=="rolled_back"
        assert path.read_text()==BEFORE
        assert release.promote(receipt="a"*64,candidate=candidate(),proof=proof())=="rolled_back"

def test_wrong_test_proof_cannot_promote():
    with TemporaryDirectory() as directory:
        root=Path(directory); path=make(root)
        release=LocalCodeReleaseService(root=root,store=Store())
        for item in (N(passed=False,cleanup_proven=True,candidate_digest=digest(AFTER)),
                     N(passed=True,cleanup_proven=False,candidate_digest=digest(AFTER)),
                     N(passed=True,cleanup_proven=True,candidate_digest="wrong")):
            try: release.promote(receipt="a"*64,candidate=candidate(),proof=item)
            except ValueError: pass
            else: raise AssertionError("invalid proof accepted")
        assert path.read_text()==BEFORE

def test_external_edit_not_overwritten_by_rollback():
    with TemporaryDirectory() as directory:
        root=Path(directory); path=make(root)
        release=LocalCodeReleaseService(root=root,store=Store())
        release.promote(receipt="a"*64,candidate=candidate(),proof=proof())
        path.write_text("# synthetic human edit\n"+AFTER)
        try: release.rollback(receipt="a"*64)
        except ValueError as error: assert str(error)=="local_rollback_external_change"
        else: raise AssertionError("external change overwritten")
        assert path.read_text().startswith("# synthetic human edit")

def test_crash_after_replace_reconciles_without_replacing_again():
    with TemporaryDirectory() as directory:
        root=Path(directory); path=make(root); store=Store()
        release=LocalCodeReleaseService(root=root,store=store)
        original=store.save
        def fail(kind,key,value):
            if value.get("status")=="promoted": raise OSError("synthetic-private-marker")
            original(kind,key,value)
        store.save=fail
        try: release.promote(receipt="a"*64,candidate=candidate(),proof=proof())
        except OSError: pass
        assert path.read_text()==AFTER
        store.save=original
        release._replace=lambda *args: (_ for _ in ()).throw(AssertionError("duplicate replacement"))
        assert release.promote(receipt="a"*64,candidate=candidate(),proof=proof())=="promoted"

def pipeline(mode):
    with TemporaryDirectory() as directory:
        root=Path(directory); path=make(root); store=Store(); calls=[]
        if mode!="unapproved":
            LocalCodeUpdateAuthorization(store).record(receipt="a"*64,family="AUTH",
                code="correct_filename",resolution_verified=True)
        def generate(**kwargs):
            calls.append("generate")
            return None if mode=="no_change" else candidate()
        def verify(**kwargs):
            calls.append("test")
            passed=not (mode=="test_failed" or mode=="health_failed" and kwargs.get("applied"))
            return LocalCandidateTestResult(passed,"passed" if passed else "sandbox_tests_failed",digest(AFTER),True)
        service=LocalCodeUpdateService(root=root,store=store,
            generator=N(propose=generate),tester=N(verify=verify),
            source_ready=lambda:mode!="dirty")
        result=service.process(receipt="a"*64,family="AUTH",code="correct_filename")
        following=service.process(receipt="a"*64,family="AUTH",code="correct_filename")
        return result,following,calls,path.read_text(),store

def test_pipeline_promotes_once():
    result,next_result,calls,text,_=pipeline("success")
    assert result==next_result=="promoted" and calls==["generate","test","test"] and text==AFTER

def test_pipeline_failure_preserves_old():
    result,_,calls,text,_=pipeline("test_failed")
    assert result=="tests_failed" and calls==["generate","test"] and text==BEFORE

def test_pipeline_health_failure_rolls_back():
    result,_,calls,text,_=pipeline("health_failed")
    assert result=="rolled_back" and text==BEFORE and calls==["generate","test","test"]

def test_no_change_never_promotes():
    result,_,calls,text,_=pipeline("no_change")
    assert result=="guidance_only" and calls==["generate"] and text==BEFORE

def test_unapproved_or_dirty_never_generates():
    for mode,expected in (("unapproved","approval_unproven"),("dirty","waiting_for_clean_source")):
        result,_,calls,text,_=pipeline(mode)
        assert result==expected and not calls and text==BEFORE

def test_restart_during_promotion_reconciles_then_health_checks_once():
    from dataclasses import asdict
    with TemporaryDirectory() as directory:
        root=Path(directory); path=make(root); store=Store(); calls=[]
        LocalCodeUpdateAuthorization(store).record(receipt="a"*64,family="AUTH",
            code="correct_filename",resolution_verified=True)
        release=LocalCodeReleaseService(root=root,store=store)
        release.promote(receipt="a"*64,candidate=candidate(),proof=proof())
        store.save("audit","local-code-job:"+"a"*64,
            {"phase":"promoting","candidate":asdict(candidate()),"proof":asdict(proof())})
        def forbidden(**kwargs): raise AssertionError("generation repeated after restart")
        def verify(**kwargs): calls.append(kwargs["applied"]); return proof()
        restarted=LocalCodeUpdateService(root=root,store=store,
            generator=N(propose=forbidden),tester=N(verify=verify),source_ready=lambda:True)
        assert restarted.process(receipt="a"*64,family="AUTH",code="correct_filename")=="promoted"
        assert restarted.process(receipt="a"*64,family="AUTH",code="correct_filename")=="promoted"
        assert calls==[True] and path.read_text()==AFTER


if __name__=="__main__":
    tests=[v for k,v in list(globals().items()) if k.startswith("test_")]
    for test in tests: test()
    print("Passed:",len(tests)); print("Failed: 0")
