"""Synthetic agency-actor filtering and same-row human-history preservation."""
import unittest
from test_compliance_baseline_feedback import BaselineFeedbackTests
from src.program_compliance.responsibility import assess,reconcile
from src.program_compliance.analysis import validate

class ResponsibilityTests(unittest.TestCase):
    def test_dsa_duty_is_not_excluded_for_mentioning_other_actors(self):
        text='The DSA must notify the CMA and assist the member before HHSC reviews the plan.'
        result=assess(text);self.assertEqual(result['status'],'ours');self.assertEqual(result['duty'],text)

    def test_other_party_only_duties_are_not_agency_requirements(self):
        for actor in ('CMA','HHSC','program manager','client','member'):
            result=assess('The '+actor+' must review the plan.')
            self.assertEqual(result['status'],'other');self.assertEqual(result['duty'],'')
            self.assertIn(actor,result['other_context'][0])

    def test_shared_process_projects_only_our_part_and_keeps_context(self):
        text='The CMA must authorize the plan. The DSA must implement the authorized plan. The member must sign the form.'
        result=assess(text)
        self.assertEqual(result['duty'],'The DSA must implement the authorized plan.')
        self.assertEqual(len(result['other_context']),2);self.assertEqual(result['source_excerpt'],text)

    def test_joint_duty_retains_explicit_dsa_part(self):
        result=assess('The DSA and CMA must coordinate the transition.')
        self.assertEqual(result['status'],'ours');self.assertEqual(result['duty'],'Provider/DSA must coordinate the transition.')
        self.assertEqual(assess('The DSA and provider must coordinate.')['status'],'ours')
        self.assertEqual(assess('The DSA or CMA must coordinate.')['status'],'ambiguous')

    def test_provider_requires_source_definition_not_agency_self_description(self):
        duty='The provider must retain the record.'
        self.assertEqual(assess(duty,'Our agency is a DSA and a provider.')['status'],'ambiguous')
        self.assertEqual(assess(duty,'Provider means the direct services agency (DSA).')['status'],'ours')
        self.assertEqual(assess(duty,'Provider means the CMA.')['status'],'other')
        self.assertEqual(assess(duty,'Provider means a DSA or CMA.')['status'],'ambiguous')

    def test_nested_question_does_not_establish_our_duty(self):
        self.assertEqual(assess('HHSC determines whether the DSA must provide the service.')['status'],'ambiguous')

    def test_dependency_definition_does_not_establish_source_provider_alias(self):
        pkg={'paragraphs':[{'text':'The provider must retain records.'}],
             'cross_reference_context':{'Other source':{'text':'Provider means the DSA.'}}}
        with self.assertRaisesRegex(ValueError,'actor_unsupported'):
            validate({'obligations':[{'paragraph':0,'actor':'DSA','topic':'Records','action':'Review records.'}]},pkg)

    def test_other_party_deadline_is_not_our_deadline(self):
        text='The DSA must notify the CMA. The CMA must respond within five days.'
        pkg={'paragraphs':[{'text':text}],'cross_reference_context':{}}
        result=validate({'obligations':[{'paragraph':0,'actor':'DSA','topic':'Notification','action':'Review the notification process.'}]},pkg)[0]
        self.assertIsNone(result['deadline']);self.assertEqual(result['agency_duty'],'The DSA must notify the CMA.')

    def test_related_actor_questions_consolidate_without_global_alias_assumption(self):
        f=BaselineFeedbackTests();f.setUp();self.addCleanup(f.doCleanups)
        with f.store.transaction():
            for i in range(2):
                sid='linked-'+str(i)
                f.store.put('source',sid,{'id':sid,'parent':'test-source','url':'https://official.example/class/'+sid})
                f.store.put('source_actor_context',sid+':section',{'paragraphs':[assess('The provider must retain records.')],'definition_context':''})
                f.store.put('section',sid+':section',{'heading':'Source section '+str(i)})
        reconcile(f.store)
        questions=[v for k,v in f.store.items('finding') if k.startswith('question:actor-family:')]
        self.assertEqual(len(questions),1)
        self.assertIn('2 related source(s)',questions[0]['Requirement/Change Summary'])
        self.assertIn('no common Provider alias',questions[0]['Requirement/Change Summary'])

    def test_live_projection_preserves_human_fields_revision_and_restart_reuse(self):
        f=BaselineFeedbackTests();f.setUp();self.addCleanup(f.doCleanups)
        key,row=f.baseline();f.sync.sync()
        f.api.edit(key,{'Implementation Status':'Met','Reviewed Revision':row['Current Revision'],'Completion Evidence':'Synthetic proof','Decision Notes':'Preserve note'})
        f.sync.sync()
        with f.store.transaction():
            support=f.store.get('requirement_evidence',key)
            support['quote']='The DSA must notify the CMA. The CMA must respond within five days.'
            f.store.put('requirement_evidence',key,support)
        f.sync.sync();current=f.store.get('finding',key)
        self.assertEqual(current['Requirement/Change Summary'],'The DSA must notify the CMA.')
        self.assertNotEqual(current['Current Revision'],row['Current Revision'])
        self.assertEqual(f.store.get('human',key)['Implementation Status'],'Met')
        self.assertEqual(f.store.get('human',key)['Completion Evidence'],'Synthetic proof')
        self.assertEqual(f.sync.sync()['updated'],0)
        self.assertEqual(reconcile(f.store)['changed'],0)

    def test_other_party_reclassification_keeps_same_row_and_human_history(self):
        f=BaselineFeedbackTests();f.setUp();self.addCleanup(f.doCleanups)
        key,row=f.baseline();f.sync.sync();identity=f.sync.read()[0]['id']
        f.api.edit(key,{'Decision Notes':'Preserve prior note'});f.sync.sync()
        with f.store.transaction():
            support=f.store.get('requirement_evidence',key);support['quote']='The CMA must approve the plan.';f.store.put('requirement_evidence',key,support)
        f.sync.sync();actual=next(r for r in f.sync.read() if r['id']==identity)
        self.assertEqual(actual['values']['Record Type'],'Reference')
        self.assertEqual(actual['values']['Decision Notes'],'Preserve prior note')
        self.assertEqual(actual['values'].get('Implementation Assessment'),'')
        self.assertEqual(f.sync.sync()['updated'],0)

if __name__=='__main__':unittest.main(verbosity=2)
