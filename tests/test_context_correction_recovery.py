"""Synthetic one-time context-contract upgrade of an existing blocked case."""
from pathlib import Path
from types import SimpleNamespace as N
import runpy
from src.services.local_document_correction_workflow import preparation_upgrade_applies
from src.services.document_processor_training_contracts import APPROVE_AI_CORRECTION, APPROVE_AI_RESOLUTION

fixtures=runpy.run_path(str(Path(__file__).with_name('test_label_correction_recovery.py')))

def blocked():
    h,state=fixtures['blocked']()
    state.update(preparation_contract_version=5,preparation_failure_category='correction_unrelated_field_change')
    h.store.save('case','synthetic-case',state)
    return h,state

def test_context_upgrade_same_identity_exactly_once_without_reanalysis():
    h,old=blocked()
    def forbidden(**kwargs):raise AssertionError('intent_repeated')
    h.workflow.analyzer=N(analyze=forbidden)
    h.cycle();h.cycle()
    state=h.store.load('case','synthetic-case')
    assert state['generation']==old['generation']+1 and state['preparation_contract_version']==6
    assert h.prepares==2 and h.applies==0
    assert any(kind=='audit' and value==old for (kind,key),value in h.store.data.items())

def test_unrelated_v5_failures_or_saved_plans_never_rearm():
    for variant in ('category','failure','scope','plan','behavior'):
        h,state=blocked()
        if variant=='category':state['analysis']['affected_document_category']='2067'
        if variant=='failure':state['preparation_failure_category']='correction_schema_unavailable'
        if variant=='scope':state['analysis']['affected_fields']=['Document Subtype']
        if variant=='plan':state['plan']={'updates':{}}
        if variant=='behavior':state['analysis']['behavior_code']='remain_blank_when_absent'
        assert not preparation_upgrade_applies(state)

def test_human_approval_blocks_upgrade_and_stays_unchanged():
    for column in (APPROVE_AI_CORRECTION,APPROVE_AI_RESOLUTION):
        h,_=blocked();h.values[column]=True;h.cycle()
        assert h.prepares==1 and h.applies==0 and h.values[column] is True

def test_untouched_blank_approvals_allow_preparation_but_never_application():
    h,old=blocked()
    def verified_filename(*args):
        h.prepares+=1
        return {'updates':{},'attachment':{
            'name':'SYNTHETIC_COMPLETE.PDF','before_name':'SYNTHETIC_[SERVICE].PDF'}}
    h.prepare=verified_filename
    h.values[APPROVE_AI_CORRECTION]=None
    h.values[APPROVE_AI_RESOLUTION]=None
    h.cycle();h.cycle()
    state=h.store.load('case','synthetic-case')
    assert state['generation']==old['generation']+1
    assert state['phase']=='proposed' and state['preparation_contract_version']==6
    assert h.prepares==2 and h.applies==0
    assert h.values[APPROVE_AI_CORRECTION] is None
    assert h.values[APPROVE_AI_RESOLUTION] is None

def test_context_failure_is_reserved_and_does_not_hot_retry():
    h,_=blocked()
    def failure(*args):
        h.prepares+=1
        state=h.store.load('case','synthetic-case')
        assert state['phase']=='preparing' and state['preparation_contract_version']==6
        raise RuntimeError('local_model_response_incomplete')
    h.prepare=failure;h.cycle();h.cycle()
    state=h.store.load('case','synthetic-case')
    assert state['phase']=='blocked' and state['preparation_failure_category']=='local_model_response_incomplete'
    assert h.prepares==2 and h.applies==0

def test_same_context_contract_never_rearms():
    h,state=blocked();state['preparation_contract_version']=6
    assert not preparation_upgrade_applies(state)
    h.store.save('case','synthetic-case',state);h.cycle()
    assert h.prepares==1

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    failed=0
    for test in tests:
        try:test()
        except Exception as error:failed+=1;print('FAIL:',test.__name__,type(error).__name__)
    print('Passed:',len(tests)-failed);print('Failed:',failed)
    print('Classification: synthetic/mock; no external operations')
    raise SystemExit(bool(failed))
