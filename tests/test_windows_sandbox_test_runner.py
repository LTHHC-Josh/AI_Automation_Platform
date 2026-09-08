"""Synthetic/mock sandbox ownership and isolation-contract checks."""
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from xml.etree.ElementTree import fromstring
from src.services.windows_sandbox_test_runner import WindowsSandboxTestRunner

def test_configuration_exposes_only_read_only_staging():
    root=fromstring(WindowsSandboxTestRunner.configuration("synthetic-input","synthetic-runtime"))
    for name in ("Networking","ClipboardRedirection","VGpu","AudioInput","VideoInput","PrinterRedirection"):
        assert root.findtext(name)=="Disable"
    mappings=root.findall("MappedFolders/MappedFolder")
    assert len(mappings)==2 and all(m.findtext("ReadOnly")=="true" for m in mappings)
    assert {m.findtext("SandboxFolder") for m in mappings}=={r"C:\TestInput",r"C:\Python"}

def exercise(mode):
    with TemporaryDirectory(prefix="lthhc-sandbox-test-") as directory:
        root=Path(directory)
        # Synthetic placeholders only; no executable is actually launched.
        for relative in ("wsb.exe","input/run_tests.py","runtime/python.exe"):
            path=root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.touch()
        calls=[]
        def command(args, **kwargs):
            calls.append(args)
            assert kwargs["timeout"]>0 and kwargs["capture_output"]
            action=args[1]
            if action=="list":
                return SimpleNamespace(returncode=0,stdout=json.dumps({
                    "WindowsSandboxEnvironments":[] if mode=="already_gone" else [{}]}))
            identity=args[args.index("--id")+1]
            if mode=="timeout" and action=="exec": raise subprocess.TimeoutExpired(args,1)
            if mode=="start_lost" and action=="start": raise subprocess.TimeoutExpired(args,1)
            if mode in {"cleanup_failed","already_gone"} and action=="stop": raise OSError("synthetic-sensitive")
            payload={"Id":identity} if action=="start" else {"ExitCode":0 if mode!="test_failed" else 1} if action=="exec" else {}
            if mode=="bad_response" and action=="exec": payload={"ExitCode":True}
            return SimpleNamespace(returncode=0,stdout=json.dumps(payload))
        result=WindowsSandboxTestRunner(cli=root/"wsb.exe",command=command).run(
            input_dir=root/"input",runtime_dir=root/"runtime")
        assert len({c[c.index("--id")+1] for c in calls if "--id" in c})==1
        assert calls[-1][1] in {"stop","list"}
        assert "synthetic-sensitive" not in repr(result)
        return result

def test_success_and_owned_cleanup():
    result=exercise("success"); assert result.success and result.cleanup_proven

def test_failed_tests_cannot_pass():
    result=exercise("test_failed"); assert not result.success and result.exit_code==1

def test_timeout_always_cleans_exact_owned_vm():
    result=exercise("timeout"); assert not result.success and result.category=="sandbox_timeout" and result.cleanup_proven

def test_lost_start_response_cleans_reserved_identity():
    result=exercise("start_lost"); assert not result.success and result.cleanup_proven

def test_cleanup_failure_blocks_success():
    result=exercise("cleanup_failed"); assert not result.success and not result.cleanup_proven

def test_invalid_exit_shape_fails_closed():
    assert not exercise("bad_response").success

def test_already_exited_vm_proven_by_empty_inventory():
    result=exercise("already_gone")
    assert result.success and result.cleanup_proven


def test_durable_owner_recovered_before_next_reservation():
    old="11111111-1111-4111-8111-111111111111"
    new="22222222-2222-4222-8222-222222222222"
    class Store:
        value={"identity":old,"marker":"local-code-v1"}
        def load(self,*args): return dict(self.value)
        def save(self,kind,key,value): self.value=dict(value)
    store=Store(); runner=WindowsSandboxTestRunner(owner_store=store); calls=[]
    runner._call=lambda args,timeout:calls.append(args) or {}
    runner._reserve_owner(new)
    assert calls==[["stop","--raw","--id",old]]
    assert store.value["identity"]==new
    store.value={"identity":old,"marker":"external"}
    calls.clear()
    try: runner._reserve_owner(new)
    except ValueError: pass
    else: raise AssertionError("unproven ownership accepted")
    assert calls==[]


if __name__=="__main__":
    tests=[v for k,v in list(globals().items()) if k.startswith("test_")]
    for test in tests: test()
    print("Passed:",len(tests)); print("Failed: 0")
