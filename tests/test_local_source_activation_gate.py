"""Synthetic Windows lock/quarantine checks; no production operations."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
from types import SimpleNamespace as N
from src.services.local_source_activation_gate import document_source_ready, source_lease
from src.services.local_code_update_service import LocalCodeUpdateService
from src.services.local_code_update_authorization import LocalCodeUpdateAuthorization
from test_local_code_update_pipeline import Store, make, candidate, proof, BEFORE, AFTER

def test_optional_initial_state_and_nested_document_lease():
    with TemporaryDirectory() as directory:
        store=Store()
        with document_source_ready(root=directory,store=store):
            with document_source_ready(root=directory,store=store): pass

def test_durable_pending_blocks_after_restart():
    with TemporaryDirectory() as directory:
        store=Store(); store.save("audit","local-source-activation",{"pending":True,"receipt":"a"*64})
        for _ in range(2):
            try:
                with document_source_ready(root=directory,store=store):
                    raise AssertionError("unverified code used by document")
            except RuntimeError as error: assert str(error)=="local_source_activation_unverified"

def test_second_process_cannot_enter_held_lease():
    with TemporaryDirectory() as directory:
        script=("import sys\nfrom src.services.local_source_activation_gate import source_lease\n"
                "try:\n with source_lease(sys.argv[1]): sys.exit(9)\n"
                "except RuntimeError as e:\n sys.exit(0 if str(e)=='local_source_activation_busy' else 8)\n")
        with source_lease(directory):
            result=subprocess.run([sys.executable,"-c",script,directory],capture_output=True,timeout=15)
        assert result.returncode==0
        with source_lease(directory): pass

def test_exception_releases_os_lease():
    with TemporaryDirectory() as directory:
        try:
            with source_lease(directory): raise ValueError("synthetic")
        except ValueError: pass
        with source_lease(directory): pass

def test_interrupted_post_health_quarantines_then_recovers_same_release():
    with TemporaryDirectory() as directory:
        root=Path(directory); path=make(root); store=Store(); generated=[]
        LocalCodeUpdateAuthorization(store).record(receipt="a"*64,family="AUTH",
            code="correct_filename",resolution_verified=True)
        def generate(**kwargs): generated.append(True); return candidate()
        def verify(**kwargs):
            if kwargs.get("applied"): raise RuntimeError("synthetic lost health result")
            return proof()
        service=LocalCodeUpdateService(root=root,store=store,
            generator=N(propose=generate),tester=N(verify=verify),source_ready=lambda:True)
        assert service.process(receipt="a"*64,family="AUTH",code="correct_filename")=="update_failed"
        assert path.read_text()==AFTER
        assert store.load("audit","local-source-activation")["pending"] is True
        try:
            with document_source_ready(root=root,store=store): raise AssertionError("activation escaped quarantine")
        except RuntimeError: pass
        restarted=LocalCodeUpdateService(root=root,store=store,
            generator=N(propose=generate),tester=N(verify=lambda **kwargs:proof()),source_ready=lambda:True)
        assert restarted.process(receipt="a"*64,family="AUTH",code="correct_filename")=="promoted"
        assert generated==[True]
        with document_source_ready(root=root,store=store): pass

if __name__=="__main__":
    tests=[v for k,v in list(globals().items()) if k.startswith("test_")]
    for test in tests: test()
    print("Passed:",len(tests)); print("Failed: 0")
    print("Classification: synthetic/mock and real local Windows process lock")
