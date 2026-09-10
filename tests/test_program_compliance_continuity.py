"""Development memory/routing and concurrent-edit preservation, synthetic/read-only."""
import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace as N
from src.program_compliance.continuity import guarded_write

ROOT=Path(__file__).resolve().parents[1]

class ContinuityTests(unittest.TestCase):
    def test_concurrent_shared_edit_preserved_without_partial_write(self):
        with tempfile.TemporaryDirectory() as directory:
            a=Path(directory)/'state.md';b=Path(directory)/'history.md'
            a.write_bytes(b'original');b.write_bytes(b'original')
            expected=hashlib.sha256(b'original').hexdigest()
            b.write_bytes(b'concurrent service work')
            with self.assertRaises(RuntimeError): guarded_write([(a,expected,b'proposed'),(b,expected,b'proposed')])
            self.assertEqual(a.read_bytes(),b'original');self.assertEqual(b.read_bytes(),b'concurrent service work')

    def test_resume_plan_has_complete_requirements_and_no_dp_history_dependency(self):
        plan=(ROOT/'docs/program_compliance_plan.md').read_text(encoding='utf-8-sig')
        for phrase in ('## Next Service Action','Full implementation authorization','ACCEPTANCE / DEFINITION OF DONE','SHARED','No patient data'):
            self.assertIn(phrase.lower(),plan.lower())
        self.assertIn('Full DP history is not required',plan)

    def test_shared_state_routes_both_services_without_erasing_dp_action(self):
        state=(ROOT/'PROJECT_STATE.md').read_text(encoding='utf-8-sig')
        self.assertEqual(state.count('## CURRENT NEXT START'),1)
        self.assertIn('## Document Processor — Pending Action',state)
        self.assertIn('Preserve blocked generation 3',state)
        self.assertIn('## Program Compliance Monitor — Current State',state)
        self.assertIn('docs/program_compliance_plan.md',state)

    def test_tracker_read_only_cannot_write_external_tasks(self):
        spec=importlib.util.spec_from_file_location('pcm_tracker_test',ROOT/'update_project_tracker.py')
        tracker=importlib.util.module_from_spec(spec);spec.loader.exec_module(tracker)
        class Tasks:
            def get_tasks(self): return [N(name=n) for n,_,_ in tracker.PROJECT_SMARTSHEET_TASKS]
            def sync_task(self,*args,**kwargs): raise AssertionError('external write forbidden')
        with patch.object(tracker,'ProjectStatusService',return_value=N(tasks=Tasks())),patch.object(tracker,'write_project_smartsheet_snapshot'),contextlib.redirect_stdout(io.StringIO()):
            result=tracker.inspect_project_smartsheet_read_only()
        self.assertEqual(result,{'not_found':0,'failed':0,'writes':0})

if __name__=='__main__': unittest.main(verbosity=2)
