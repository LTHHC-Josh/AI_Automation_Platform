"""Cross-process local inference admission; metadata only, no service knowledge.

One active request, DP priority capped at three consecutive grants while background
work waits. Uncertain active requests are never evicted on a timer or process death.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import os
import sqlite3
import time
import uuid
import psutil

SERVICE = ContextVar('inference_service', default='dp')


@contextmanager
def service_class(name):
    if name not in ('dp', 'training', 'compliance'):
        raise ValueError('inference_service_invalid')
    token = SERVICE.set(name)
    try:
        yield
    finally:
        SERVICE.reset(token)


def queue_directory():
    return Path(os.environ['LOCALAPPDATA']) / 'LTHHC' / 'InferenceQueue'


def alive(pid, birth):
    try:
        return psutil.Process(pid).create_time() == birth
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied:
        return True  # Unknown ownership is not grounds for deleting a waiter.


class InferenceQueue:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else queue_directory()
        self.directory.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise RuntimeError('local_model_queue_schema_unverified')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS requests (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, ticket TEXT UNIQUE,
                    service TEXT, pid INTEGER, birth REAL, state TEXT,
                    queued REAL, started REAL);
                CREATE UNIQUE INDEX IF NOT EXISTS one_active ON requests(state)
                    WHERE state IN ('active');
                CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY, streak INTEGER);
                INSERT OR IGNORE INTO policy VALUES (1, 0);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, service TEXT,
                    event TEXT, at REAL);
                PRAGMA user_version=1;
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.directory / 'queue.sqlite3', timeout=10)
        db.execute('PRAGMA synchronous=FULL')
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def event(db, service, event):
        db.execute('INSERT INTO events(service,event,at) VALUES (?,?,?)',
                   (service, event, time.time()))
        db.execute('DELETE FROM events WHERE seq <= (SELECT MAX(seq)-200 FROM events)')

    def enqueue(self, service):
        if service not in ('dp', 'training', 'compliance'):
            raise ValueError('inference_service_invalid')
        ticket = uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO requests(ticket,service,pid,birth,state,queued) VALUES (?,?,?,?,?,?)',
                       (ticket, service, os.getpid(), psutil.Process().create_time(), 'waiting', time.time()))
        return ticket

    def grant(self, ticket):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            active = db.execute("SELECT pid,birth,state FROM requests WHERE state != 'waiting'").fetchone()
            if active:
                if active[2] == 'uncertain' or not alive(active[0], active[1]):
                    raise RuntimeError('local_model_queue_uncertain')
                return False
            for seq, pid, birth in db.execute("SELECT seq,pid,birth FROM requests WHERE state='waiting'").fetchall():
                if not alive(pid, birth):
                    db.execute('DELETE FROM requests WHERE seq=?', (seq,))
            rows = db.execute('SELECT ticket,service FROM requests ORDER BY seq').fetchall()
            if not rows:
                return False
            streak = db.execute('SELECT streak FROM policy WHERE id=1').fetchone()[0]
            foreground = next((r for r in rows if r[1] == 'dp'), None)
            background = next((r for r in rows if r[1] != 'dp'), None)
            chosen = background if background and (not foreground or streak >= 3) else foreground
            if chosen[0] != ticket:
                return False
            db.execute("UPDATE requests SET state='active',started=? WHERE ticket=?", (time.time(), ticket))
            db.execute('UPDATE policy SET streak=? WHERE id=1',
                       (min(streak + 1, 3) if chosen[1] == 'dp' else 0,))
            self.event(db, chosen[1], 'started')
            return True

    @contextmanager
    def request(self, service=None, wait_seconds=1800):
        service = service or SERVICE.get()
        ticket = self.enqueue(service)
        granted = False
        lease = Lease()
        deadline = time.monotonic() + wait_seconds
        try:
            while not self.grant(ticket):
                if time.monotonic() >= deadline:
                    raise RuntimeError('local_model_queue_wait_timeout')
                time.sleep(0.05)
            granted = True
            yield lease
        finally:
            with self.connect() as db:
                if not granted or lease.finished:
                    db.execute('DELETE FROM requests WHERE ticket=?', (ticket,))
                    if granted:
                        self.event(db, service, 'finished')
                else:
                    db.execute("UPDATE requests SET state='uncertain' WHERE ticket=?", (ticket,))
                    self.event(db, service, 'uncertain')


class Lease:
    finished = False

    def complete(self):
        self.finished = True
