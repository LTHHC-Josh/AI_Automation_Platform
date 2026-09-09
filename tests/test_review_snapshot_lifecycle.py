"""Synthetic/mock snapshot, correction and truthful result regressions."""
from pathlib import Path
import runpy
from types import SimpleNamespace as N

fixtures=runpy.run_path(str(Path(__file__).with_name('test_local_document_correction.py')))
Harness=fixtures['Harness']; AdapterHarness=fixtures['AdapterHarness']
from src.services.document_processor_training_contracts import *
from src.services.evidence_only_correction_executor import REVIEW_SNAPSHOT_COLUMNS

def snapshot_harness():
    h=Harness(); h.refreshes=0
    h.values.update({'AI Review Reasons':'Synthetic prior warning','AI Review Status':'Human Review Recommended','AI Review Required':True})
    def prepare(*args):
        h.prepares+=1
        before={n:h.values.get(n) for n in REVIEW_SNAPSHOT_COLUMNS}
        after=dict(before,**{'AI Review Reasons':'Synthetic new warning '+str(h.prepares)})
        return {'updates':{'End Date':None},'before':{'End Date':h.values.get('End Date')},
                'review_snapshot':{'before':before,'after':after}}
    def refresh(row_id,snapshot,**kw):
        h.refreshes+=1; h.values.update(snapshot['after']); return True
    h.prepare=prepare; h.refresh_review_snapshot=refresh
    return h

def test_comment_analysis_refreshes_once_apply_and_resolution_preserve_snapshot():
    h=snapshot_harness(); assert h.cycle().analysis_ready_count==1
    snapshot={n:h.values[n] for n in REVIEW_SNAPSHOT_COLUMNS}
    h.cycle(); assert h.refreshes==1 and h.prepares==1
    assert h.approve().correction_applied_count==1
    assert all(h.values[n]==v for n,v in snapshot.items())
    assert 'review reason remains the analysis snapshot' in h.values[AI_RESOLUTION_RESULT]
    assert 'Updated row fields: AI Review Reasons' not in h.values[AI_RESOLUTION_RESULT]
    h.values[APPROVE_AI_RESOLUTION]=True; h.cycle(); h.cycle()
    assert h.refreshes==1 and all(h.values[n]==v for n,v in snapshot.items())

def test_new_comment_refreshes_new_generation_once_not_unchanged_poll():
    from dataclasses import replace
    h=snapshot_harness(); h.cycle(); first=h.store.load('case','synthetic-case')
    h.comments.append(replace(h.comments[0],comment_id=2,text='Another synthetic correction comment'))
    h.cycle(); h.cycle()
    assert h.refreshes==2 and h.prepares==2
    assert h.store.load('case','synthetic-case')['generation']==first['generation']+1

def test_noncomment_contract_upgrade_does_not_refresh_snapshot():
    h=snapshot_harness(); h.cycle()
    state=h.store.load('case','synthetic-case')
    state.update(phase='blocked',plan=None,preparation_contract_version=1)
    h.store.save('case','synthetic-case',state)
    h.cycle(); assert h.prepares==2 and h.refreshes==1

def test_uncertain_snapshot_blocks_new_analysis_and_never_claims_ready():
    from dataclasses import replace
    h=snapshot_harness()
    def uncertain(*args,**kw): h.refreshes+=1; raise ValueError('synthetic-private-detail')
    h.refresh_review_snapshot=uncertain
    result=h.cycle()
    assert result.analysis_ready_count==0 and result.implementation_failed_count==1
    assert h.store.load('case','synthetic-case')['phase']=='review_refresh'
    h.comments.append(replace(h.comments[0],comment_id=2,text='New synthetic feedback'))
    h.cycle(); assert h.prepares==1 and h.applies==0 and h.refreshes==1

def test_snapshot_restart_after_committed_refresh_reconciles_same_generation():
    h=snapshot_harness(); original=h.refresh_review_snapshot
    def interrupted(*args,**kw):
        original(*args,**kw); raise RuntimeError('synthetic interruption after write')
    h.refresh_review_snapshot=interrupted
    h.cycle(); state=h.store.load('case','synthetic-case')
    assert state['phase']=='review_refresh'
    h.refresh_review_snapshot=original
    assert h.cycle().analysis_ready_count==1
    h.cycle()
    assert h.store.load('case','synthetic-case')['generation']==state['generation']
    assert h.prepares==1 and h.applies==0

def test_executor_saved_application_never_writes_review_snapshot():
    h=AdapterHarness(); plan=h.plan()
    assert not REVIEW_SNAPSHOT_COLUMNS.intersection(plan['updates'])
    before={n:h.values.get(h.ids[n]) for n in REVIEW_SNAPSHOT_COLUMNS}
    h.executor.apply(1,plan)
    assert {n:h.values.get(h.ids[n]) for n in REVIEW_SNAPSHOT_COLUMNS}==before

def test_legacy_unapplied_review_write_fails_closed_before_request():
    h=AdapterHarness(); plan=h.plan()
    plan['before']['AI Review Reasons']=h.values.get(h.ids['AI Review Reasons'])
    plan['updates']['AI Review Reasons']='Synthetic different reason'
    try: h.executor.apply(1,plan)
    except ValueError as error: assert str(error)=='correction_review_snapshot_write_forbidden'
    else: raise AssertionError('legacy review overwrite permitted')
    assert h.calls==0

def test_snapshot_write_lost_response_reconciles_and_does_not_repeat():
    h=AdapterHarness()
    snapshot={'before':{n:h.values.get(h.ids[n]) for n in REVIEW_SNAPSHOT_COLUMNS},
              'after':{'AI Review Reasons':'Synthetic remaining warning','AI Review Status':'Human Review Recommended','AI Review Required':True}}
    original=h.update_row
    def lost(*args): original(*args); raise RuntimeError('synthetic-private-error')
    h.update_row=lost
    assert h.executor.refresh_review_snapshot(1,snapshot,generation_receipt='b'*64)
    assert h.executor.refresh_review_snapshot(1,snapshot,generation_receipt='b'*64)
    assert h.calls==1

def test_snapshot_unproven_write_does_not_retry():
    h=AdapterHarness()
    snapshot={'before':{n:h.values.get(h.ids[n]) for n in REVIEW_SNAPSHOT_COLUMNS},
              'after':{'AI Review Reasons':'Synthetic remaining warning','AI Review Status':'Human Review Recommended','AI Review Required':True}}
    def unavailable(*args): h.calls+=1; raise RuntimeError('synthetic-private-error')
    h.update_row=unavailable
    for _ in range(2):
        try: h.executor.refresh_review_snapshot(1,snapshot,generation_receipt='c'*64)
        except ValueError as error: assert str(error)=='correction_review_snapshot_unresolved'
        else: raise AssertionError('unproven snapshot treated as written')
    assert h.calls==1

def test_mismatched_readback_never_claims_correction_completed():
    h=Harness(); h.cycle()
    def no_change(*args): h.applies+=1; h.verified=True
    h.apply=no_change
    result=h.approve()
    assert result.correction_applied_count==0 and result.implementation_failed_count==1
    assert h.store.load('case','synthetic-case')['phase']=='applying'
    assert 'Readback verified' not in h.values.get(AI_RESOLUTION_RESULT,'')

def test_unchanged_review_value_not_reported_as_updated():
    h=Harness(); h.values['AI Review Reasons']='Synthetic unchanged reason'
    h.cycle(); state=h.store.load('case','synthetic-case')
    state['plan']['before']={'AI Review Reasons':'Synthetic unchanged reason'}
    state['plan']['updates']['AI Review Reasons']='Synthetic unchanged reason'
    h.store.save('case','synthetic-case',state)
    # Refresh presentation before fresh approval; no changes to human controls.
    h.cycle(); h.approve()
    assert 'Update the review' not in h.values[AI_RESOLUTION_RESULT]
    assert 'Updated the review' not in h.values[AI_RESOLUTION_RESULT]

def test_final_analysis_snapshot_removes_resolved_reason_and_retains_valid_reason():
    from dataclasses import replace
    h=AdapterHarness()
    h.review.needs_human_review=True
    h.review.review_status='Human Review Recommended'
    h.review.review_reasons=['authorization subtype could not be determined.']
    h.context['End Date']=None; h.context['End Date Conf.']=None
    h.values[h.ids['End Date']]=None; h.values[h.ids['End Date Conf.']]=None
    old='AI Document Subtype: Unknown; Service-line Date: Could not be verified'
    h.context['AI Review Reasons']=old; h.values[h.ids['AI Review Reasons']]=old
    analysis=replace(fixtures['fixture']['correction_analysis'](),affected_fields=('Service Line',))
    plan=h.executor.prepare(1,h.context,analysis)
    final=plan['review_snapshot']['after']
    assert final['AI Review Reasons']=='AI Document Subtype: Unknown'
    assert str(final['AI Review Required']).lower() in {'true','yes'}
    assert final['AI Review Status']=='Human Review Recommended'
    assert not REVIEW_SNAPSHOT_COLUMNS.intersection(plan['updates'])

def test_naming_reference_placeholders_do_not_create_snapshot_review_reasons():
    from src.services.review_reason_summary_service import ReviewReasonSummaryService
    summary=ReviewReasonSummaryService().summarize([
        'filename payer could not be resolved.', 'filename service could not be resolved.',
        'filename date could not be determined.', 'authorization subtype could not be determined.'])
    assert summary=='AI Document Subtype: Unknown'

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    for test in tests: test()
    print('Passed:',len(tests)); print('Failed: 0'); print('Classification: synthetic/mock; no external operations')
