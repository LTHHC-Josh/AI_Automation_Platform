"""Synthetic/mock checks: no model, Smartsheet, mailbox, or document access."""
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as N
import runpy
from src.services.local_correction_memory_service import LocalCorrectionStore, ApprovedDocumentLessons
from src.services.local_document_correction_workflow import LocalDocumentCorrectionWorkflow
from src.services.document_processor_training_contracts import *
from src.services.evidence_only_correction_executor import EvidenceOnlyCorrectionExecutor
from src.ai.llm.providers.ollama_provider import OllamaProvider

fixture = runpy.run_path(str(Path(__file__).with_name("test_document_processor_training.py")))

class FakeStore:
    def __init__(self): self.data = {}
    def load(self, kind, identity):
        import copy
        return copy.deepcopy(self.data.get((kind,str(identity))))
    def save(self, kind, identity, value):
        import copy
        self.data[(kind,str(identity))] = copy.deepcopy(value)

class Harness:
    def __init__(self, mode="local_correction"):
        self.values = {AI_CORRECTION:True, APPROVE_AI_CORRECTION:False,
                       APPROVE_AI_RESOLUTION:False, "End Date":"synthetic-old"}
        self.comments = [CorrectionComment(1, 1, "synthetic-time", "synthetic-time", "synthetic-author", "synthetic feedback")]
        self.writes, self.applies, self.prepares = [], 0, 0
        self.fail_after_apply, self.verified = False, False
        self.store = FakeStore()
        self.schema = fixture["schema_result"]()
        self.workflow = LocalDocumentCorrectionWorkflow(
            schema_service=N(read=lambda:self.schema), reader=self,
            writer=self, repository=N(exclusive_operation=nullcontext,
                load_or_create=lambda **kw:N(case_id="synthetic-case")),
            analyzer=N(analyze=lambda **kw:fixture["correction_analysis"]()),
            executor=self, mode=mode, store=self.store,
        )
    def read_rows(self, **kw): return [self.read_context_row()]
    def read_context_row(self, **kw): return N(row_id=1, values=dict(self.values))
    def read_comments(self, **kw): return self.comments
    def write(self, *, updates, expected_proposal_hash_values, **kw):
        assert not set(updates) & HUMAN_OWNED_COLUMNS
        assert all(self.values.get(k)==v for k,v in expected_proposal_hash_values.items())
        self.writes.append(dict(updates)); self.values.update(updates)
        return N(success=True,outcome_proven=True)
    def prepare(self, *args):
        self.prepares += 1
        return {"updates":{"End Date":None}}
    def apply(self, *args):
        self.applies += 1
        self.values["End Date"] = None
        self.verified = True
        if self.fail_after_apply: raise RuntimeError("synthetic-private-marker")
    def verify(self, *args): return self.verified
    def cycle(self): return self.workflow.run_cycle()
    def proposal(self):
        self.cycle(); self.cycle()
    def approve(self):
        self.values[APPROVE_AI_CORRECTION] = True
        return self.cycle()

def test_complete_same_row_workflow_and_bounded_learning():
    h=Harness(); h.proposal()
    assert h.applies==0
    assert not h.store.load("lesson","authorization")
    result=h.approve()
    assert result.implementation_completed_count==1 and h.applies==1
    assert h.values[AI_CORRECTION_STATUS]=="Awaiting Resolution Approval"
    assert h.values[AI_CORRECTION] is True
    h.cycle() # observe new resolution false baseline
    h.values[APPROVE_AI_RESOLUTION]=True
    assert h.cycle().resolved_count==1
    assert h.values[AI_CORRECTION_STATUS]=="Resolved"
    assert h.store.load("lesson","authorization")["active"]==["remain_blank_when_absent"]
    updates=[v for (kind,key),v in h.store.data.items()
             if kind=="audit" and key.startswith("local-code-update:")]
    assert len(updates)==1
    assert updates[0]["status"]=="awaiting_verified_isolation"
    assert updates[0]["promotion_attempt_count"]==0
    assert "application code has not changed" in h.values[AI_RESOLUTION_RESULT]
    h.cycle(); assert h.applies==1 and h.prepares==1
    assert h.comments[0].text=="synthetic feedback"

def test_stale_approval_and_stale_resolution_are_not_consumed():
    h=Harness()
    h.values[APPROVE_AI_CORRECTION]=True
    h.proposal(); h.cycle(); assert h.applies==0
    h.values[APPROVE_AI_CORRECTION]=False; h.cycle()
    h.values[APPROVE_AI_RESOLUTION]=True
    h.approve(); h.cycle()
    assert h.values[AI_CORRECTION_STATUS]=="Awaiting Resolution Approval"
    assert not h.store.load("lesson","authorization")

def test_lost_response_reconciles_without_second_apply_or_new_generation():
    h=Harness(); h.proposal(); h.fail_after_apply=True
    assert h.approve().implementation_failed_count==1
    assert h.applies==1
    h.cycle(); h.cycle()
    assert h.applies==1 and h.prepares==1
    assert h.values[AI_CORRECTION_STATUS]=="Awaiting Resolution Approval"

def test_unproven_outcome_never_retries_even_with_new_comment():
    h=Harness(); h.proposal(); h.fail_after_apply=True; h.approve()
    h.verified=False
    h.comments.append(CorrectionComment(1, 2, "synthetic-time", "synthetic-time", "synthetic-author", "new instruction"))
    result=h.cycle(); h.cycle()
    assert h.applies==1 and h.prepares==1
    assert result.implementation_failed_count==1
    assert "synthetic-private-marker" not in repr(result)

def test_proposal_only_cannot_apply_or_learn():
    h=Harness("proposal_write"); h.proposal(); h.approve(); h.cycle()
    assert h.applies==0 and not h.store.load("lesson","authorization")

def test_read_only_never_analyzes_or_writes():
    h=Harness("read_only"); h.cycle()
    assert h.prepares==0 and h.writes==[]

def test_changed_row_invalidates_resolution():
    h=Harness(); h.proposal(); h.approve(); h.cycle()
    h.values["End Date"]="synthetic-changed"
    h.values[APPROVE_AI_RESOLUTION]=True
    h.cycle()
    assert not h.store.load("lesson","authorization")

def test_lesson_scope_bounds_and_fail_closed():
    store=FakeStore(); lessons=ApprovedDocumentLessons(store)
    allowed=[k for k in BEHAVIOR_CODES if k not in {"needs_investigation","external_dependency"}]
    for i,code in enumerate(allowed):
        lessons.approve(family="AUTH",code=code,receipt=f"{i:064x}",resolution_verified=True)
    assert len(store.load("lesson","authorization")["active"])==8
    assert len(lessons.render("authorization_renewal"))<=1800
    assert lessons.render("2067")==""
    assert lessons.family("authorization-invented") is None
    for family,code,verified in [("unknown",allowed[0],True),("AUTH","external_dependency",True),("AUTH",allowed[0],False)]:
        try: lessons.approve(family=family,code=code,receipt="a"*64,resolution_verified=verified)
        except ValueError: pass
        else: raise AssertionError("unapproved lesson accepted")
    store.save("lesson","authorization",{"active":["synthetic-private-marker"]})
    assert lessons.render("AUTH")==""

def test_sealed_store_atomic_roundtrip_and_corrupt_rejection():
    with TemporaryDirectory() as root:
        store=LocalCorrectionStore(root,protect=lambda b:b[::-1],unprotect=lambda b:b[::-1])
        store.save("case","synthetic",{"state":"proposed"})
        assert store.load("case","synthetic")["state"]=="proposed"
        assert not list(Path(root).rglob("*.tmp"))
        path=store._path("case","synthetic")
        # Use injected corrupt decoder rather than writing arbitrary fixture data.
        store.unprotect=lambda b:b"invalid"
        try: store.load("case","synthetic")
        except ValueError as e: assert str(e)=="local_record_unavailable"
        else: raise AssertionError("corrupt state accepted")

def test_actual_provider_call_boundary_receives_role_context():
    class Captured(Exception): pass
    provider=object.__new__(OllamaProvider)
    provider.seed=42
    provider._last_request_metrics={}
    captured=[]
    def chat(**kw): captured.append(kw["system_prompt"]); raise Captured()
    provider._chat=chat
    for invoke,role in [
        (lambda:provider.classify("Synthetic document purpose for a context boundary test."),"classification"),
        (lambda:provider.extract("Synthetic evidence for context boundary test.","authorization"),"extraction"),
        (lambda:provider.analyze_correction_context({},schema={}),"dp_training_correction"),
    ]:
        try: invoke()
        except Captured: pass
        assert f"ROLE: {role}" in captured[-1]
    assert "same-row" in captured[-1]
    assert "Codex/cloud" in captured[-1]

class AdapterHarness:
    def __init__(self):
        from src.services.review_output_service import ReviewOutput, ReviewField
        from src.services.smartsheet_review_configuration_service import APPROVED_DOCUMENT_FIELD_POLICIES
        from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService
        self.review=ReviewOutput(document_type="authorization",document_category="authorization",
             fields=[ReviewField(name="end_date",final_state="not_present",confidence_available=False)])
        mapper=SmartsheetReviewRowMappingService()
        self.context=dict(mapper.map(self.review,list(APPROVED_DOCUMENT_FIELD_POLICIES),run_type="Synthetic").values)
        self.context["End Date"]="2000-01-01"
        self.context["End Date Conf."]=0.95
        names=set(self.context)|set(mapper.OPERATIONAL_METADATA_COLUMNS)|{p.column_name for p in APPROVED_DOCUMENT_FIELD_POLICIES}|{
            p.confidence_column_name for p in APPROVED_DOCUMENT_FIELD_POLICIES if p.confidence_column_name}
        self.ids={n:i+1 for i,n in enumerate(sorted(names))}
        self.types={n:("CHECKBOX" if n in {"AI Correction","AI Review Required","AI Extraction Retry Triggered","AI Authorized Units Reconciled"} else "DATE" if n in {"Start Date","End Date"} else "TEXT_NUMBER") for n in names}
        self.config=N(success=True,policies=APPROVED_DOCUMENT_FIELD_POLICIES,
           available_columns=self.ids,available_column_types=self.types,
           available_system_column_types={n:"none" for n in names})
        self.values={self.ids[n]:v for n,v in self.context.items()}
        self.values[self.ids["AI Correction"]]=True
        self.calls=0
        self.executor=EvidenceOnlyCorrectionExecutor(
           client=self, source=N(store=FakeStore(),get=lambda row:{"path":"synthetic.pdf","fingerprint":"a"*64}),
           processor_factory=lambda:N(process=lambda *a,**kw:N(document_type="authorization",review_output=self.review)),
           configuration=N(resolve=lambda **kw:self.config))
    def get_selected_row(self, **kw):
        return 1,N(cells=[N(column_id=k,value=v) for k,v in self.values.items()])
    def update_row(self,row_id,updates):
        import smartsheet
        self.calls+=1
        for k,v in updates.items():
            self.values[k]=None if isinstance(v,smartsheet.models.ExplicitNull) else v
    def plan(self):
        return self.executor.prepare(1,self.context,fixture["correction_analysis"]())

def test_real_mapper_executor_clears_only_approved_date_and_confidence():
    h=AdapterHarness(); plan=h.plan()
    assert plan["updates"]["End Date"] is None
    assert plan["updates"]["End Date Conf."] is None
    assert "AI Correction" not in plan["updates"]
    h.executor.apply(1,plan)
    assert h.executor.verify(1,plan)
    assert h.calls==1 and h.values[h.ids["AI Correction"]] is True

def test_executor_rejects_human_column_and_objects_before_api():
    h=AdapterHarness()
    for updates in [{"AI Correction":False},{"End Date":{}},{"End Date":42},{"AI Review Required":"true"}]:
        try: h.executor._validate(updates,h.config)
        except ValueError: pass
        else: raise AssertionError("unsafe correction accepted")
    assert h.calls==0

def test_executor_schema_drift_and_changed_row_fail_before_write():
    h=AdapterHarness(); plan=h.plan()
    h.values[h.ids["End Date"]]="2001-01-01"
    try: h.executor.apply(1,plan)
    except ValueError: pass
    else: raise AssertionError("stale row accepted")
    assert h.calls==0
    h=AdapterHarness(); plan=h.plan()
    h.config.available_column_types["End Date"]="CONTACT_LIST"
    try: h.executor.apply(1,plan)
    except ValueError: pass
    else: raise AssertionError("schema drift accepted")
    assert h.calls==0

def test_executor_rejects_unrelated_replay_changes():
    h=AdapterHarness()
    h.context["AI Document Category"]="2067"
    try: h.plan()
    except ValueError as e: assert str(e)=="correction_unrelated_field_change"
    else: raise AssertionError("unrelated change accepted")
    assert h.calls==0

def test_executor_no_verified_change_does_not_claim_success():
    h=AdapterHarness()
    h.context["End Date"]=None; h.context["End Date Conf."]=None
    h.values[h.ids["End Date"]]=None; h.values[h.ids["End Date Conf."]]=None
    try: h.plan()
    except ValueError as e: assert str(e)=="correction_no_verified_change"
    else: raise AssertionError("no-op reported as correction")

def test_local_target_blocks_remote_cloud_redirects_and_unproven_metadata():
    from unittest.mock import patch
    provider=object.__new__(OllamaProvider)
    provider.model="synthetic-model"; provider.timeout=1
    for endpoint in ["https://remote.invalid","http://127.0.0.1@remote.invalid","http://localhost/path","http://localhost?x=y"]:
        provider.base_url=endpoint
        with patch("src.ai.llm.providers.ollama_provider.requests.post") as post:
            try: provider._verify_local_inference_target()
            except RuntimeError as e: assert str(e)=="local_model_endpoint_required"
            else: raise AssertionError("nonlocal endpoint accepted")
            post.assert_not_called()
    provider.base_url="http://127.0.0.1:11434"
    for data,status in [
        ({"model_info":{}},200),
        ({"model_info":{"architecture":"synthetic"},"remote_host":"remote.invalid"},200),
        ({"model_info":{"architecture":"synthetic"}},302),
    ]:
        with patch("src.ai.llm.providers.ollama_provider.requests.post",return_value=N(status_code=status,json=lambda:data)):
            try: provider._verify_local_inference_target()
            except RuntimeError as e: assert str(e)=="local_model_identity_unproven"
            else: raise AssertionError("unproven local model accepted")
    with patch("src.ai.llm.providers.ollama_provider.requests.post",return_value=N(status_code=200,json=lambda:{"model_info":{"architecture":"synthetic"}})) as post:
        provider._verify_local_inference_target()
        assert post.call_args.kwargs["allow_redirects"] is False
        assert post.call_args.kwargs["proxies"]=={"http":"","https":""}

def test_production_factory_has_no_dispatcher_even_legacy_gate_enabled():
    from unittest.mock import patch
    import src.services.document_processor_training_application_service as module
    for mode in ["proposal_write","local_correction","approval_dispatch"]:
        with patch.object(module,"load_runtime_dp_training_capabilities",return_value=N(mode=mode,smartsheet_writes_enabled=True,codex_dispatch_enabled=True)), \
             patch.object(module,"SmartsheetClient"), patch.object(module,"LocalCorrectionAnalysisService"), \
             patch.object(module,"BoundedCodexDispatcher") as dispatcher:
            service=module.DocumentProcessorTrainingApplicationService.from_environment()
            assert isinstance(service,LocalDocumentCorrectionWorkflow)
            dispatcher.assert_not_called()

def test_visibility_failure_cannot_change_local_outcome():
    h=Harness(); h.proposal(); h.values[APPROVE_AI_CORRECTION]=True
    def broken(**kw): raise RuntimeError("synthetic-private-marker")
    result=h.workflow.run_cycle(stage_observer=broken)
    assert result.implementation_completed_count==1 and h.applies==1

def test_executor_lost_row_response_recovers_without_second_write():
    h=AdapterHarness(); plan=h.plan(); original=h.update_row
    def lost(row, updates):
        original(row,updates)
        raise RuntimeError("synthetic-private-marker")
    h.update_row=lost
    try: h.executor.apply(1,plan)
    except RuntimeError: pass
    assert h.calls==1
    h.executor.resume(1,plan)
    assert h.executor.verify(1,plan) and h.calls==1

def test_executor_unproven_update_is_not_retried():
    h=AdapterHarness(); plan=h.plan()
    def lost(row, updates):
        h.calls+=1
        raise RuntimeError("synthetic-private-marker")
    h.update_row=lost
    for invoke in (h.executor.apply,h.executor.resume):
        try: invoke(1,plan)
        except (ValueError,RuntimeError): pass
    assert h.calls==1 and not h.executor.verify(1,plan)

def test_attachment_version_exact_identity_and_uncertain_no_retry():
    from io import BytesIO
    class UploadPath:
        def open(self, mode): return BytesIO(b"synthetic")
    for lost in (False,True):
        h=AdapterHarness(); plan=h.plan()
        plan["attachment"]={"id":11,"before_name":"synthetic-old.pdf","name":"synthetic-new.pdf"}
        records=[{"id":11,"name":"synthetic-old.pdf"}]
        counts={"uploads":0,"cleanups":0}
        def upload(*args):
            counts["uploads"]+=1
            records[:]=[{"id":12,"name":"synthetic-new.pdf"}]
            if lost: raise RuntimeError("synthetic-private-marker")
            return N(result=N(id=12,name="synthetic-new.pdf"))
        h.sheet_id=1
        h.client=N(Attachments=N(attach_new_version=upload))
        h.executor._attachments=lambda row:list(records)
        h.executor.naming=N(
            prepare_technical=lambda **kw:N(success=True,temporary_path=UploadPath()),
            cleanup=lambda p:counts.update(cleanups=counts["cleanups"]+1))
        try: h.executor.apply(1,plan)
        except RuntimeError: pass
        for _ in range(2):
            try: h.executor.resume(1,plan)
            except ValueError: pass
        assert counts=={"uploads":1,"cleanups":1}
        assert h.executor.verify(1,plan) is (not lost)
        assert h.calls==1

def test_attachment_never_attempted_if_row_unproven():
    h=AdapterHarness(); plan=h.plan()
    plan["attachment"]={"id":11,"before_name":"synthetic-old.pdf","name":"synthetic-new.pdf"}
    def lost(row, updates): raise RuntimeError("synthetic-private-marker")
    h.update_row=lost
    def forbidden(*a,**kw): raise AssertionError("attachment call before proven row")
    h.executor._attachments=forbidden
    try: h.executor.apply(1,plan)
    except RuntimeError: pass

def test_immediate_approval_after_publication_is_not_a_polling_race():
    h=Harness(); h.cycle()
    assert h.approve().implementation_completed_count==1
    h.values[APPROVE_AI_RESOLUTION]=True
    assert h.cycle().resolved_count==1


def test_source_binding_is_exact_hash_scoped_and_original_file_is_unchanged():
    from src.services.evidence_only_correction_executor import LocalCorrectionSource
    import hashlib
    with TemporaryDirectory() as directory:
        root=Path(directory); incoming=root/"data/incoming"; incoming.mkdir(parents=True)
        content=b"SYNTHETIC DOCUMENT"
        fingerprint=hashlib.sha256(content).hexdigest()
        path=incoming/(fingerprint+".pdf")
        path.write_bytes(content)
        store=FakeStore(); source=LocalCorrectionSource(store); source.ROOT=root
        item=N(local_path=path,document_key=fingerprint,job_key="b"*64)
        state=N(stage="attachment_written",smartsheet_row_id=1,attachment_filename="synthetic-original.pdf")
        source.bind(row_id=1,work_item=item,state=state)
        assert source.get(1)["fingerprint"]==fingerprint
        assert path.read_bytes()==content
        item.document_key="c"*64
        try: source.bind(row_id=1,work_item=item,state=state)
        except ValueError: pass
        else: raise AssertionError("wrong content identity accepted")
        record=store.load("source","1"); record["path"]=str(root/"outside.pdf")
        store.save("source","1",record)
        try: source.get(1)
        except ValueError as e: assert str(e)=="correction_source_outside_scope"
        else: raise AssertionError("out of scope source accepted")

def test_end_to_end_workflow_uses_real_mapping_and_typed_update_adapter():
    h=Harness(); adapter=AdapterHarness()
    h.workflow.executor=adapter.executor
    original_read=h.read_context_row
    def read(**kw):
        row=original_read()
        production={name:adapter.values.get(identity) for name,identity in adapter.ids.items()}
        production.update({k:v for k,v in h.values.items() if k in REQUIRED_COLUMNS})
        return N(row_id=1,values=production)
    h.read_context_row=read
    h.cycle()
    assert h.approve().correction_applied_count==1
    assert adapter.calls==1
    h.values[APPROVE_AI_RESOLUTION]=True
    result=h.cycle()
    assert result.approved_lesson_count==1 and result.codex_dispatch_count==0
    h.cycle(); assert adapter.calls==1
    assert adapter.values[adapter.ids["AI Correction"]] is True


def test_resolution_wires_local_update_without_extra_approval():
    h=Harness(); calls=[]
    h.workflow.code_updates=N(process=lambda **kw: calls.append(kw) or "guidance_only")
    h.proposal(); h.approve()
    assert calls==[]
    h.values[APPROVE_AI_RESOLUTION]=True
    result=h.cycle()
    assert result.resolved_count==1 and len(calls)==1
    assert h.values[AI_CORRECTION] is True and h.values[APPROVE_AI_RESOLUTION] is True
    assert "Local code review found no change necessary" in h.values[AI_RESOLUTION_RESULT]
    assert "row_id" not in calls[0] and "comments" not in calls[0]


def test_code_failure_visible_without_changing_human_controls():
    h=Harness()
    h.workflow.code_updates=N(process=lambda **kw:"tests_failed")
    h.proposal(); h.approve(); h.values[APPROVE_AI_RESOLUTION]=True
    result=h.cycle()
    assert result.polling_result=="completed_with_failures"
    assert h.values[APPROVE_AI_RESOLUTION] is True
    assert "no successful installation is claimed" in h.values[AI_RESOLUTION_RESULT]


def test_resolution_learning_survives_restart_and_reaches_later_extraction():
    from unittest.mock import patch
    h=Harness(); h.proposal()
    assert ApprovedDocumentLessons(h.store).render("AUTH")==""
    h.approve()
    assert ApprovedDocumentLessons(h.store).render("AUTH")==""
    h.values[APPROVE_AI_RESOLUTION]=True
    assert h.cycle().approved_lesson_count==1
    previous=h.workflow
    h.workflow=LocalDocumentCorrectionWorkflow(
        schema_service=previous.schema_service,reader=h,writer=h,
        repository=previous.repository,analyzer=previous.analyzer,executor=h,
        mode="local_correction",store=h.store)
    assert h.cycle().approved_lesson_count==0
    assert h.applies==1 and h.prepares==1
    lessons=ApprovedDocumentLessons(h.store)
    expected=BEHAVIOR_CODES["remain_blank_when_absent"]
    assert expected in lessons.render("authorization")
    assert lessons.render("2067")==""
    class Captured(Exception): pass
    captured=[]
    provider=object.__new__(OllamaProvider)
    provider.seed=42; provider._last_request_metrics={}
    def chat(**kwargs):
        captured.append(kwargs); raise Captured()
    provider._chat=chat
    with patch("src.services.local_correction_memory_service.ApprovedDocumentLessons",return_value=lessons):
        for family in ("authorization","2067"):
            try: provider.extract("A later synthetic document.",family)
            except Captured: pass
    assert expected in captured[0]["system_prompt"]
    assert expected not in captured[1]["system_prompt"]
    assert "synthetic feedback" not in repr(captured)
    assert "not evidence; deterministic validation still required" in captured[0]["system_prompt"]


def test_resolved_checked_cases_cannot_starve_later_feedback():
    h=Harness(); visited=[]
    h.read_rows=lambda **kwargs:[N(row_id=i,values={AI_CORRECTION:True}) for i in range(12)]
    h.workflow._advance=lambda identity,schema,counts:visited.append(identity)
    for _ in range(3): h.cycle()
    assert len(visited)==15 and set(visited)==set(range(12))
    assert h.store.load("audit","local-poll-cursor")=={"offset":3}


if __name__=="__main__":
    tests=[v for k,v in list(globals().items()) if k.startswith("test_")]
    for test in tests: test()
    print(f"Passed: {len(tests)}"); print("Failed: 0")
    print("Classification: synthetic deterministic/mock; no external integrations")
