"""Transactional service-owned state, immutable versions and recoverable outbox."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256((value if isinstance(value, bytes) else canonical(value).encode())).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    SCHEMA = 1

    def __init__(self, directory, readonly=False):
        self.directory = Path(directory).resolve()
        if readonly:
            self.snapshots=self.directory/'snapshots'
            self.db=sqlite3.connect((self.directory/'monitor.sqlite').as_uri()+'?mode=ro',uri=True,timeout=10)
            self.db.row_factory=sqlite3.Row
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        self.snapshots = self.directory / 'snapshots'
        self.snapshots.mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.directory / 'monitor.sqlite', timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA synchronous=FULL')
        version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if version > self.SCHEMA:
            self.db.close()
            raise ValueError('state_schema_newer_than_runtime')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS records(kind TEXT, key TEXT, value TEXT NOT NULL, PRIMARY KEY(kind,key));
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, kind TEXT, key TEXT, value TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS outbox(key TEXT PRIMARY KEY, revision TEXT, payload TEXT, state TEXT, attempts INTEGER DEFAULT 0);
        PRAGMA user_version=1;
        ''')

    @contextmanager
    def transaction(self):
        with self.db:
            yield

    def get(self, kind, key, default=None):
        row = self.db.execute('SELECT value FROM records WHERE kind=? AND key=?', (kind,key)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, kind, key, value):
        self.db.execute('INSERT INTO records VALUES(?,?,?) ON CONFLICT(kind,key) DO UPDATE SET value=excluded.value', (kind,key,canonical(value)))

    def items(self, kind):
        return [(r['key'],json.loads(r['value'])) for r in self.db.execute('SELECT key,value FROM records WHERE kind=? ORDER BY key',(kind,))]

    def event(self, kind, key, value):
        self.db.execute('INSERT INTO events(kind,key,value,created) VALUES(?,?,?,?)',(kind,key,canonical(value),now()))

    def snapshot(self, raw):
        key=digest(raw)
        target=self.snapshots/key
        if not target.exists():
            temporary=target.with_suffix('.pending')
            temporary.write_bytes(raw)
            temporary.replace(target)
        elif digest(target.read_bytes())!=key:
            raise ValueError('snapshot_integrity_failure')
        return key

    def publish(self, key, payload, substantive=True, evidence_version=None):
        """Caller owns transaction. Human fields are never accepted here."""
        old=self.get('finding',key)
        comparable={k:v for k,v in payload.items() if k not in {'Last Successful Check','Source Health','Review Needed','Current Revision'}}
        revision=digest({'fields':comparable,'evidence':evidence_version})[:16] if substantive else (old or {}).get('Current Revision',digest(comparable)[:16])
        payload={**payload,'Finding Key':key,'Current Revision':revision}
        if old==payload:
            return False
        if old and old.get('Current Revision')!=revision:
            self.event('review_history',key,{'system':old,'human':self.get('human',key,{})})
        self.put('finding',key,payload)
        self.db.execute('INSERT INTO outbox(key,revision,payload,state) VALUES(?,?,?,?) ON CONFLICT(key) DO UPDATE SET revision=excluded.revision,payload=excluded.payload,state=CASE WHEN outbox.state="uncertain" THEN "uncertain" ELSE "pending" END', (key,revision,canonical(payload),'pending'))
        return True

    def observe_human(self,key,fields):
        old=self.get('human',key,{})
        if old!=fields:
            self.event('human_observation',key,{'previous':old,'current':fields})
            self.put('human',key,fields)

    def backup(self, destination):
        destination=Path(destination)
        destination.mkdir(parents=True,exist_ok=False)
        (destination/'snapshots').mkdir()
        target=sqlite3.connect(destination/'monitor.sqlite')
        self.db.backup(target)
        target.close()
        manifest={}
        for p in self.snapshots.iterdir():
            if len(p.name)==64:
                data=p.read_bytes()
                if digest(data)!=p.name: raise ValueError('snapshot_integrity_failure')
                (destination/'snapshots'/p.name).write_bytes(data)
                manifest[p.name]=p.name
        (destination/'manifest.json').write_text(canonical({'schema':self.SCHEMA,'database_digest':digest((destination/'monitor.sqlite').read_bytes()),'snapshots':manifest}),encoding='utf-8')

    def close(self):
        self.db.close()

    @classmethod
    def restore(cls,backup,destination):
        backup=Path(backup);destination=Path(destination)
        if destination.exists(): raise ValueError('restore_requires_new_destination')
        manifest=json.loads((backup/'manifest.json').read_text(encoding='utf-8'))
        if manifest['schema']>cls.SCHEMA: raise ValueError('backup_schema_newer_than_runtime')
        if digest((backup/'monitor.sqlite').read_bytes())!=manifest.get('database_digest'): raise ValueError('backup_database_integrity_failure')
        files=[]
        for name,expected in manifest['snapshots'].items():
            if len(name)!=64 or any(c not in '0123456789abcdef' for c in name): raise ValueError('invalid_snapshot_name')
            data=(backup/'snapshots'/name).read_bytes()
            if digest(data)!=expected or expected!=name: raise ValueError('snapshot_integrity_failure')
            files.append((name,data))
        source=sqlite3.connect(backup/'monitor.sqlite')
        if source.execute('PRAGMA integrity_check').fetchone()[0]!='ok': source.close();raise ValueError('backup_database_invalid')
        destination.mkdir(parents=True);(destination/'snapshots').mkdir()
        target=sqlite3.connect(destination/'monitor.sqlite');source.backup(target);target.close();source.close()
        for name,data in files: (destination/'snapshots'/name).write_bytes(data)
        return cls(destination)
