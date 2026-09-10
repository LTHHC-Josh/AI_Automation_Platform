"""Synthetic reset, full-batch, agency-feedback and hierarchy regression."""
import copy
import unittest
from unittest.mock import patch
from contextlib import contextmanager
from test_program_compliance import ComplianceTests, FakeAPI
from src.program_compliance.store import Store, digest
from src.program_compliance.sheet import SheetAPI, Synchronizer, HUMAN, REVIEW_FORMULA, columns
from src.program_compliance.topics import assign


class Model:
    model='synthetic'; _last_request_metrics={}
    def __init__(self): self.calls=0; self.packages=[]
    def analyze_baseline(self,pkg):
        self.calls+=1; self.packages.append(copy.deepcopy(pkg))
        prior=pkg.get('prior_agency_determinations')
        return {'obligations':[{'paragraph':i,'actor':'DSA','topic':'Staff coverage',
            'action':'Review changed duty against prior implementation.' if prior else 'Review the existing process and evidence.'} for i in pkg['target_paragraphs']]}


class HierarchyAPI(FakeAPI):
    def request(self,method,path,**kwargs):
        result=super().request(method,path,**kwargs)
        if method!='GET':
            for payload in kwargs['json']:
                row=next(r for r in self.rows if r['id']==payload['id']) if 'id' in payload else self.rows[-1]
                for name in ('parentId','expanded'):
                    if name in payload: row[name]=payload[name]
        return result


class BaselineFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.fixture=ComplianceTests(); self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.store=self.fixture.store; self.monitor=self.fixture.monitor; self.model=Model(); self.monitor.model=self.model
        with self.store.transaction():
            self.store.put('config','baseline_engine',True)
            self.store.put('config','baseline_presentation',{'group_health':True,'suppress_test':True})
        self.source=self.store.get('source','test-source')
        self.api=HierarchyAPI()
        with self.store.transaction(): self.store.put('config','sheet',{'id':999})
        self.sync=Synchronizer(self.store,self.api,999)

    def baseline(self):
        self.monitor.check_source(self.source)
        self.monitor.analyze_source(self.source,20)
        return next((k,v) for k,v in self.store.items('finding') if k.startswith('requirement:'))

    def test_all_targets_beyond_three_are_processed_in_durable_batches(self):
        self.fixture.fetch.text='\n'.join('A DSA must maintain staff procedure '+str(i)+'.' for i in range(5))
        self.monitor.check_source(self.source)
        self.assertEqual(self.monitor.analyze_source(self.source,1),1)
        self.assertEqual(self.monitor.analyze_source(self.source,1),1)
        self.assertEqual(self.monitor.analyze_source(self.source,1),0)
        self.assertEqual(len([k for k,_ in self.store.items('finding') if k.startswith('requirement:')]),5)
        self.assertEqual(self.store.get('baseline_source','test-source')['state'],'assessed')

    def test_unavailable_reference_is_an_explicit_section_gap(self):
        self.fixture.fetch.text+=' See Section 9999.'
        self.monitor.check_source(self.source);self.monitor.analyze_source(self.source,20)
        self.assertEqual(self.model.calls,0)
        self.assertTrue(any('referenced_context_unavailable' in ' '.join(v['gaps']) for _,v in self.store.items('baseline_section')))

    def test_analysis_failure_never_exposes_unrecognized_exception_text(self):
        self.monitor.check_source(self.source)
        with patch.object(self.model,'analyze_baseline',side_effect=RuntimeError('PRIVATEVALUE')):
            self.monitor.analyze_source(self.source,20)
        self.assertEqual([v['category'] for _,v in self.store.items('baseline_failure')],['RuntimeError'])
        self.assertNotIn('PRIVATEVALUE',str(self.store.items('baseline_section')))

    def test_met_is_reported_for_reviewed_revision_and_unchanged_reuses_analysis(self):
        key,row=self.baseline();self.sync.sync()
        self.api.edit(key,{'Implementation Status':'Met','Reviewed Revision':row['Current Revision'],
            'Review Status':'Complete','Completion Evidence':'Synthetic evidence','Decision Notes':'Reported completed'})
        self.sync.sync(); calls=self.model.calls
        self.monitor.analyze_source(self.source,20)
        self.assertEqual(self.model.calls,calls)
        result=self.sync.sync();self.assertEqual(result['updated'],0)
        actual=next(r for r in self.sync.read() if r['values'].get('Finding Key')==key)['values']
        self.assertIn('no repeat implementation',actual['Proposed Action'])
        self.assertIn('not independently certified',actual['Implementation Assessment'])
        self.assertEqual(self.store.get('determination',key)['reviewed_revision'],row['Current Revision'])

    def test_changed_requirement_uses_prior_report_and_requires_reassessment(self):
        key,row=self.baseline();self.sync.sync()
        human={'Implementation Status':'Met','Reviewed Revision':row['Current Revision'],'Review Status':'Complete',
               'Completion Evidence':'Synthetic evidence','Decision Notes':'Reported completed','Owner':'Synthetic owner','Applicability Decision':'Applies'}
        self.api.edit(key,human);self.sync.sync()
        self.fixture.fetch.text+=' Review this process annually.'
        self.monitor.check_source(self.source);self.monitor.analyze_source(self.source,20)
        context=self.model.packages[-1]['prior_agency_determinations']
        self.assertTrue(context);self.assertFalse(next(iter(context.values()))['compatible_with_current_evidence'])
        self.assertEqual(next(iter(context.values()))['applicability_decision'],'Applies')
        self.sync.sync()
        new=self.store.get('finding',key);self.assertNotEqual(new['Current Revision'],row['Current Revision'])
        actual=next(r for r in self.sync.read() if r['values'].get('Finding Key')==key)['values']
        for name,value in human.items(): self.assertEqual(actual[name],value)
        self.assertIn('Reassessment required',actual['Implementation Assessment'])
        self.assertEqual(self.store.get('determination',key)['reviewed_revision'],row['Current Revision'])
        self.api.edit(key,{'Reviewed Revision':new['Current Revision']});self.sync.sync()
        self.assertEqual(self.store.get('determination',key)['reviewed_revision'],new['Current Revision'])
        self.assertEqual(len(self.store.items('determination_version')),2)

    def test_completed_review_without_report_does_not_mean_met(self):
        key,row=self.baseline();self.sync.sync()
        self.api.edit(key,{'Review Status':'Complete','Reviewed Revision':row['Current Revision']});self.sync.sync()
        actual=next(r for r in self.sync.read() if r['values'].get('Finding Key')==key)['values']
        self.assertTrue(actual['Implementation Assessment'].startswith('Not Assessed'))
        self.assertIsNone(self.store.get('determination',key))
        self.api.edit(key,{'Applicability Decision':'Applies'});self.sync.sync()
        report=self.store.get('determination',key)
        self.assertEqual(report['implementation_status'],'Not Assessed')
        self.assertEqual(report['applicability_decision'],'Applies')
        self.assertIsNone(self.store.get('human',key).get('Implementation Status'))
        self.assertIn('Implementation Status',HUMAN)
        self.assertEqual(next(c for c in columns() if c['title']=='Implementation Status')['options'],['Not Assessed','Met','Partially Met','Not Met','Not Applicable'])

    def test_partial_report_focuses_remaining_gaps_without_new_inference(self):
        key,row=self.baseline();self.sync.sync();calls=self.model.calls
        self.api.edit(key,{'Implementation Status':'Partially Met','Reviewed Revision':row['Current Revision'],
            'Completion Evidence':'Synthetic completed portion','Decision Notes':'One portion remains'})
        self.sync.sync();self.monitor.analyze_source(self.source,20)
        actual=next(r for r in self.sync.read() if r['values'].get('Finding Key')==key)['values']
        self.assertIn('remaining gaps',actual['Proposed Action'])
        self.assertIn('preserve work already reported complete',actual['Proposed Action'])
        self.assertEqual(self.model.calls,calls)
        self.assertEqual(self.sync.sync()['updated'],0)

    def test_changed_surrounding_condition_reassesses_prior_met(self):
        key,row=self.baseline();self.sync.sync()
        self.api.edit(key,{'Implementation Status':'Met','Reviewed Revision':row['Current Revision']});self.sync.sync()
        self.fixture.fetch.text+='\nThis duty applies only when the program authorizes the service.'
        self.monitor.check_source(self.source);self.monitor.analyze_source(self.source,20);self.sync.sync()
        self.assertNotEqual(self.store.get('finding',key)['Current Revision'],row['Current Revision'])
        self.assertFalse(next(iter(self.model.packages[-1]['prior_agency_determinations'].values()))['compatible_with_current_evidence'])
        actual=next(r for r in self.sync.read() if r['values'].get('Finding Key')==key)['values']
        self.assertEqual(actual['Implementation Status'],'Met')
        self.assertIn('Reassessment required',actual['Implementation Assessment'])

    def test_removed_duty_preserves_report_and_reassesses_once(self):
        key,row=self.baseline();self.sync.sync()
        self.api.edit(key,{'Implementation Status':'Met','Reviewed Revision':row['Current Revision'],'Completion Evidence':'Retained proof'});self.sync.sync()
        self.fixture.fetch.text='This section contains program background information with sufficient text to remain a valid source page.'
        self.monitor.check_source(self.source);self.monitor.analyze_source(self.source,20);self.sync.sync()
        revision=self.store.get('finding',key)['Current Revision']
        self.assertNotEqual(revision,row['Current Revision'])
        self.monitor.analyze_source(self.source,20);self.assertEqual(self.sync.sync()['updated'],0)
        self.assertEqual(self.store.get('finding',key)['Current Revision'],revision)
        self.assertEqual(self.store.get('determination',key)['completion_evidence'],'Retained proof')

    def test_service_profile_change_invalidates_only_service_specific_report(self):
        self.fixture.fetch.text+='\nA DSA must provide the authorized service.'
        self.baseline();self.sync.sync()
        before={k:v for k,v in self.store.items('finding') if k.startswith('requirement:')}
        for key,row in before.items():
            self.api.edit(key,{'Implementation Status':'Met','Reviewed Revision':row['Current Revision']})
        self.sync.sync()
        with self.store.transaction():
            profile=self.monitor.profile();profile.update(contracted_services=['Synthetic service'],active_services=['Synthetic service'])
            self.store.put('profile','agency',profile)
        self.monitor.analyze_source(self.source,20);self.sync.sync()
        for key,row in before.items():
            current=self.store.get('finding',key)
            if row['Responsible Party/Duty Scope']=='DSA / Agency-wide':
                self.assertEqual(current['Current Revision'],row['Current Revision'])
            else:self.assertNotEqual(current['Current Revision'],row['Current Revision'])
            self.assertEqual(self.store.get('human',key)['Implementation Status'],'Met')

    def test_late_report_binds_known_old_revision_without_becoming_current(self):
        key,row=self.baseline();self.sync.sync()
        self.fixture.fetch.text+=' Review the process annually.'
        self.monitor.check_source(self.source);self.monitor.analyze_source(self.source,20);self.sync.sync()
        self.api.edit(key,{'Implementation Status':'Met','Reviewed Revision':row['Current Revision'],
            'Completion Evidence':'Evidence for the older duty','Decision Notes':'Late agency report'})
        self.sync.sync()
        report=self.store.get('determination',key)
        self.assertEqual(report['reviewed_revision'],row['Current Revision'])
        self.assertNotIn('annually',report['support']['quote'])
        actual=next(r for r in self.sync.read() if r['values'].get('Finding Key')==key)['values']
        self.assertIn('Reassessment required',actual['Implementation Assessment'])

    def test_maintenance_state_is_rechecked_after_lock_admission(self):
        from src.program_compliance.runtime import run_tick
        with self.store.transaction():
            self.store.put('config','schedule',{**self.fixture.config['schedule'],'enabled':True})
        @contextmanager
        def admission(directory):
            with self.store.transaction():self.store.put('maintenance','authorized_baseline',{'state':'analyzing'})
            yield
        with patch('src.program_compliance.runtime.OwnedLock',side_effect=admission):
            self.assertEqual(run_tick(self.store,self.monitor,self.sync),{'state':'authorized_maintenance'})
        self.assertEqual(self.api.writes,[]);self.assertEqual(self.model.calls,0)

    def test_disabled_schedule_is_rechecked_after_lock_admission(self):
        from src.program_compliance.runtime import run_tick
        schedule={**self.fixture.config['schedule'],'enabled':True}
        with self.store.transaction():self.store.put('config','schedule',schedule)
        @contextmanager
        def admission(directory):
            with self.store.transaction():self.store.put('config','schedule',{**schedule,'enabled':False})
            yield
        with patch('src.program_compliance.runtime.OwnedLock',side_effect=admission):
            self.assertEqual(run_tick(self.store,self.monitor,self.sync),{'state':'activation_pending'})
        self.assertEqual(self.api.writes,[]);self.assertEqual(self.model.calls,0)

    def test_report_evidence_notes_and_unchanged_reuse_survive_restart(self):
        key,row=self.baseline();self.sync.sync()
        self.api.edit(key,{'Implementation Status':'Met','Reviewed Revision':row['Current Revision'],
            'Completion Evidence':'Synthetic completion record','Decision Notes':'Synthetic agency report'})
        self.sync.sync();before=self.store.get('determination',key);calls=self.model.calls
        self.store.close()
        reopened=Store(self.store.directory);self.addCleanup(reopened.close)
        self.monitor.store=reopened
        self.assertEqual(reopened.get('determination',key),before)
        self.assertEqual(self.monitor.analyze_source(self.source,20),0)
        self.assertEqual(self.model.calls,calls)
        self.assertEqual(Synchronizer(reopened,self.api,999).sync()['updated'],0)

    def test_existing_sheet_adds_columns_at_one_index_without_human_lock(self):
        fixture=self
        class API(SheetAPI):
            def __init__(self):
                self.cols=[{**c,'id':i+1} for i,c in enumerate(columns()) if c['title'] not in ('Implementation Status','Implementation Assessment')]
                self.added=[]
            def workspace(self,name):return 77
            def workspace_sheets(self,workspace):return [{'name':'Program Compliance','id':999}]
            def request(self,method,path,**kwargs):
                if method=='GET':return {'id':999,'columns':self.cols,'permalink':'synthetic'}
                if method=='POST':
                    self.added=kwargs['json'];fixture.assertEqual(len({c['index'] for c in self.added}),1)
                    self.cols += [{**c,'id':100+i} for i,c in enumerate(self.added)]
                else:
                    next(c for c in self.cols if c['id']==int(path.rsplit('/',1)[1])).update(kwargs['json'])
                return {}
        api=API()
        with self.store.transaction():self.store.put('config','sheet',{'workspace':77,'id':999})
        api.ensure(self.store)
        self.assertEqual(len(api.added),2)
        self.assertFalse(next(c for c in api.cols if c['title']=='Implementation Status').get('locked',False))
        self.assertTrue(next(c for c in api.cols if c['title']=='Implementation Assessment')['locked'])

    def test_authorized_recreation_restores_only_exact_backed_up_human_fields(self):
        key,row=self.baseline()
        human={'Implementation Status':'Met','Reviewed Revision':row['Current Revision'],'Decision Notes':'Preserved note','Completion Evidence':'Preserved evidence'}
        with self.store.transaction():
            self.store.observe_human(key,human)
            self.store.put('maintenance','authorized_baseline',{'id':'authorized-reset','state':'rows_cleared'})
            self.store.put('human_restore',key,{'reset_id':'authorized-reset','fields':human,'digest':digest(human),'state':'pending'})
        self.assertEqual(self.sync.sync()['created'],1)
        actual=self.sync.read()[0]['values']
        for name,value in human.items():self.assertEqual(actual[name],value)
        self.assertEqual(self.sync.sync()['updated'],0)

    def test_unapproved_human_restore_is_blocked(self):
        key,row=self.baseline()
        with self.store.transaction():self.store.put('human_restore',key,{'reset_id':'unapproved','fields':{},'digest':digest({}),'state':'pending'})
        self.assertEqual(self.sync.sync()['blocked'],1);self.assertEqual(self.api.rows,[])

    def test_groups_are_stable_collapsed_and_preserve_existing_expansion(self):
        key,row=self.baseline()
        with self.store.transaction():self.store.put('config','topic_groups',True)
        self.assertEqual(self.sync.sync()['blocked'],0)
        rows=self.sync.read();parent=next(r for r in rows if r['values']['Record Type']=='Group');child=next(r for r in rows if r['values']['Record Type']=='Requirement')
        self.assertEqual(child['parent_id'],parent['id']);self.assertFalse(parent['expanded'])
        next(r for r in self.api.rows if r['id']==parent['id'])['expanded']=True
        writes=len(self.api.writes);self.sync.sync();self.assertEqual(len(self.api.writes),writes)
        self.assertTrue(next(r for r in self.sync.read() if r['id']==parent['id'])['expanded'])
        self.assertIn('[Record Type]@row = "Group"',REVIEW_FORMULA)

    def test_new_findings_reuse_parent_and_topic_move_preserves_child_identity(self):
        key,row=self.baseline()
        with self.store.transaction():self.store.put('config','topic_groups',True)
        self.sync.sync();child=next(r for r in self.sync.read() if r['values'].get('Finding Key')==key)
        self.api.edit(key,{'Implementation Status':'Partially Met','Decision Notes':'Keep note'})
        self.fixture.fetch.text+='\nA DSA must train additional staff.'
        self.monitor.check_source(self.source);self.monitor.analyze_source(self.source,20);self.sync.sync()
        self.assertEqual(len([r for r in self.sync.read() if r['values']['Record Type']=='Group']),1)
        with self.store.transaction():assign(self.store,key,'Agency Administration and Provider Responsibilities')
        self.sync.sync();moved=next(r for r in self.sync.read() if r['values'].get('Finding Key')==key)
        self.assertEqual(moved['id'],child['id']);self.assertNotEqual(moved['parent_id'],child['parent_id'])
        self.assertEqual(moved['values']['Decision Notes'],'Keep note')
        self.assertEqual(moved['values']['Implementation Status'],'Partially Met')
        self.assertFalse(any(method=='DELETE' for method,_ in self.api.writes))


if __name__=='__main__': unittest.main(verbosity=2)
