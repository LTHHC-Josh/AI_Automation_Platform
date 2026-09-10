"""Synthetic cross-process admission, fairness, crash and ownership regression."""
import multiprocessing as mp
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from src.ai.llm.inference_queue import InferenceQueue, SERVICE, service_class


def worker(directory, service, ready, start, output):
    queue = InferenceQueue(directory)
    ready.put(service)
    start.wait(10)
    with queue.request(service, wait_seconds=10) as lease:
        output.put(('start', service, time.monotonic()))
        time.sleep(0.08)
        output.put(('end', service, time.monotonic()))
        lease.complete()


def crash(directory, ready):
    with InferenceQueue(directory).request('dp'):
        ready.put(True)
        time.sleep(30)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.queue = InferenceQueue(self.temp.name)

    def finish(self, ticket):
        with self.queue.connect() as db:
            db.execute('DELETE FROM requests WHERE ticket=?', (ticket,))

    def test_dp_priority_and_bounded_background_fairness(self):
        background = [self.queue.enqueue('compliance'), self.queue.enqueue('training')]
        dp = [self.queue.enqueue('dp') for _ in range(8)]
        for i in range(3):
            self.assertFalse(self.queue.grant(background[0]))
            self.assertTrue(self.queue.grant(dp[i])); self.finish(dp[i])
        self.assertFalse(self.queue.grant(dp[3]))
        self.assertTrue(self.queue.grant(background[0])); self.finish(background[0])
        for i in range(3, 6):
            self.assertTrue(self.queue.grant(dp[i])); self.finish(dp[i])
        self.assertTrue(self.queue.grant(background[1]))

    def test_service_scope_restores_without_mutating_provider(self):
        self.assertEqual(SERVICE.get(), 'dp')
        with service_class('training'):
            self.assertEqual(SERVICE.get(), 'training')
            with service_class('compliance'):
                self.assertEqual(SERVICE.get(), 'compliance')
            self.assertEqual(SERVICE.get(), 'training')
        self.assertEqual(SERVICE.get(), 'dp')

    def test_real_provider_methods_classify_training_requests(self):
        from src.ai.llm.providers.ollama_provider import OllamaProvider
        from types import SimpleNamespace
        provider=object.__new__(OllamaProvider)
        provider.seed=42;provider._last_request_metrics={}
        provider._business_context_view=lambda *a: SimpleNamespace(rendered_text='Synthetic context')
        provider._attach_context_metrics=lambda *a: None
        seen=[]
        def chat(*args,**kwargs):
            seen.append(SERVICE.get());return {}
        provider._chat=chat
        provider.analyze_correction_context({'synthetic':True},schema={})
        self.assertEqual(seen,['training'])
        self.assertEqual(SERVICE.get(),'dp')

    def test_compliance_request_scope_uses_queue_without_worker_scan(self):
        from src.program_compliance.analysis import ComplianceModel
        provider=ComplianceModel('synthetic')
        seen=[]
        def chat(*args,**kwargs):
            seen.append(SERVICE.get());return {'obligations':[]}
        provider._chat=chat
        with patch('psutil.process_iter',side_effect=AssertionError('idle worker scan')):
            provider.analyze({'synthetic':True})
        self.assertEqual(seen,['compliance'])
        self.assertEqual(SERVICE.get(),'dp')

    def test_idle_process_markers_do_not_block_admission(self):
        with patch('psutil.process_iter', side_effect=AssertionError('must not scan idle workers')):
            with self.queue.request('compliance') as lease:
                lease.complete()

    def test_uncertain_request_blocks_without_time_based_eviction(self):
        with self.queue.request('dp'):
            pass
        with self.assertRaisesRegex(RuntimeError, 'local_model_queue_uncertain'):
            with self.queue.request('compliance'):
                self.fail('uncertain inference was overlapped')
        with self.queue.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM requests').fetchall(), [('uncertain',)])

    def test_completed_request_releases_on_downstream_validation_failure(self):
        with self.assertRaises(ValueError):
            with self.queue.request('dp') as lease:
                lease.complete()
                raise ValueError('synthetic validation failure')
        with self.queue.request('compliance') as lease:
            lease.complete()

    def test_wait_timeout_removes_only_waiter(self):
        ticket = self.queue.enqueue('dp'); self.assertTrue(self.queue.grant(ticket))
        with self.assertRaisesRegex(RuntimeError, 'local_model_queue_wait_timeout'):
            with self.queue.request('compliance', wait_seconds=0.01):
                self.fail('overlap')
        with self.queue.connect() as db:
            self.assertEqual(db.execute('SELECT ticket FROM requests').fetchall(), [(ticket,)])
        self.finish(ticket)

    def test_dead_waiter_removed_but_pid_reuse_not_treated_as_owner(self):
        ticket = self.queue.enqueue('dp')
        with self.queue.connect() as db:
            db.execute('UPDATE requests SET birth=-1 WHERE ticket=?', (ticket,))
        with self.queue.request('compliance') as lease:
            lease.complete()
        with self.queue.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM requests').fetchone()[0], 0)

    def test_separate_processes_never_overlap(self):
        context = mp.get_context('spawn')
        ready, output, start = context.Queue(), context.Queue(), context.Event()
        processes = [context.Process(target=worker, args=(self.temp.name, s, ready, start, output))
                     for s in ('dp', 'training', 'compliance', 'dp')]
        try:
            for process in processes: process.start()
            for _ in processes: ready.get(timeout=15)
            start.set()
            events = [output.get(timeout=15) for _ in range(8)]
            for process in processes:
                process.join(15); self.assertEqual(process.exitcode, 0)
            events.sort(key=lambda e: e[2])
            self.assertEqual([e[0] for e in events], ['start', 'end'] * 4)
        finally:
            for process in processes:
                if process.is_alive(): process.terminate(); process.join()

    def test_killed_owner_retains_active_reservation(self):
        context = mp.get_context('spawn'); ready = context.Queue()
        process = context.Process(target=crash, args=(self.temp.name, ready))
        process.start()
        try:
            ready.get(timeout=15)
        finally:
            process.terminate(); process.join()
        with self.assertRaisesRegex(RuntimeError, 'local_model_queue_uncertain'):
            with self.queue.request('compliance'): self.fail('orphan inference overlapped')

    def test_queue_contains_only_metadata_and_is_outside_service_memory(self):
        with self.queue.request('compliance') as lease: lease.complete()
        with self.queue.connect() as db:
            fields = {row[1] for row in db.execute('PRAGMA table_info(requests)')}
        self.assertEqual(fields, {'seq','ticket','service','pid','birth','state','queued','started'})
        self.assertNotIn('ProgramCompliance', str(self.queue.directory))


if __name__ == '__main__': unittest.main(verbosity=2)
