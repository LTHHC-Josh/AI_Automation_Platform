"""Synthetic same-case label-upgrade reservation; no external calls."""
from pathlib import Path
from types import SimpleNamespace as N
import runpy

from src.services.local_document_correction_workflow import preparation_upgrade_applies
from src.services.document_processor_training_contracts import APPROVE_AI_CORRECTION, APPROVE_AI_RESOLUTION

fixtures=runpy.run_path(str(Path(__file__).with_name('test_local_document_correction.py')))
Harness=fixtures['Harness']


def blocked():
    h=Harness(); h.cycle()
    state=h.store.load('case','synthetic-case')
    state.update(phase='blocked',plan=None,preparation_contract_version=4,
                 preparation_failure_category='correction_no_verified_change')
    state['analysis'].update(affected_document_category='authorization',
        affected_fields=['Document Subtype','Filename'],behavior_code='correct_filename')
    h.store.save('case','synthetic-case',state)
    return h,state


def test_label_upgrade_reserves_once_reuses_intent_and_does_not_apply():
    h,old=blocked()
    def no_analysis(**kwargs): raise AssertionError('intent_repeated')
    h.workflow.analyzer=N(analyze=no_analysis)
    h.cycle(); h.cycle()
    state=h.store.load('case','synthetic-case')
    assert state['generation']==old['generation']+1
    assert state['preparation_contract_version']==5
    assert h.prepares==2 and h.applies==0
    assert any(kind=='audit' and value==old for (kind,key),value in h.store.data.items())


def test_label_upgrade_excludes_other_categories_and_failures():
    for kind in ('failure','family','behavior','field'):
        h,state=blocked()
        if kind=='failure': state['preparation_failure_category']='correction_schema_unavailable'
        if kind=='family': state['analysis']['affected_document_category']='2067'
        if kind=='behavior': state['analysis']['behavior_code']='remain_blank_when_absent'
        if kind=='field': state['analysis']['affected_fields']=['Quantity']
        assert not preparation_upgrade_applies(state)
        h.store.save('case','synthetic-case',state); h.cycle()
        assert h.prepares==1 and h.applies==0


def test_label_upgrade_cannot_consume_human_approval():
    for name in (APPROVE_AI_CORRECTION,APPROVE_AI_RESOLUTION):
        h,_=blocked(); h.values[name]=True; h.cycle()
        assert h.prepares==1 and h.applies==0 and h.values[name] is True


def test_interrupted_upgrade_never_repeats_inference():
    h,_=blocked()
    def interrupted(*args):
        h.prepares+=1
        state=h.store.load('case','synthetic-case')
        assert state['phase']=='preparing' and state['preparation_contract_version']==5
        raise RuntimeError('synthetic-private-marker')
    h.prepare=interrupted
    h.cycle(); h.cycle()
    assert h.prepares==2 and h.applies==0
    assert 'synthetic-private-marker' not in repr(h.store.data)+repr(h.writes)


def test_same_version_never_rearms():
    h,state=blocked(); state['preparation_contract_version']=5
    h.store.save('case','synthetic-case',state); h.cycle()
    assert h.prepares==1 and h.applies==0


if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    failed=0
    for test in tests:
        try: test()
        except Exception as error:
            failed+=1; print('FAIL:',test.__name__,type(error).__name__)
    print('Passed:',len(tests)-failed); print('Failed:',failed)
    print('Classification: synthetic/mock; no external operations')
    raise SystemExit(bool(failed))
