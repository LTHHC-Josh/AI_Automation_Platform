"""Owned compliance-only controls and explicit timezone scheduling; no DP imports."""
from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from .store import now


class OwnedLock:
    def __init__(self,directory,name='cycle'):
        if name not in ('cycle','service','model'): raise ValueError('invalid_compliance_lock')
        self.path=Path(directory)/('pcm-'+name+'.lock');self.handle=None
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        try:
            self.handle=open(self.path,'a+b')
            if self.path.stat().st_size==0: self.handle.write(b'0');self.handle.flush()
            self.handle.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            if self.handle: self.handle.close()
            self.handle=None;raise RuntimeError('compliance_busy') from None
        return self
    def __exit__(self,*args):
        if self.handle: self.handle.close();self.handle=None


def schedule_due(schedule,previous,instant=None):
    instant=instant or datetime.now(timezone.utc)
    local=instant.astimezone(ZoneInfo(schedule['timezone']))
    if not schedule['enabled']: return {'sync':False,'daily':False,'weekly':False,'model':False}
    window=schedule.get('model_window')
    model=False
    if window and schedule.get('resource_sharing_confirmed'):
        value=local.strftime('%H:%M');start,end=window
        model=start<=value<end if start<end else value>=start or value<end
    daily=local.strftime('%H:%M')>=schedule['daily_time'] and previous.get('daily')!=local.date().isoformat()
    week=local.strftime('%G-%V')
    weekly=local.weekday()==schedule['weekly_day'] and previous.get('weekly')!=week
    last=datetime.fromisoformat(previous['sync']) if previous.get('sync') else None
    sync=not last or (instant-last).total_seconds()>=schedule['sync_minutes']*60
    return {'sync':sync,'daily':daily,'weekly':weekly,'model':model,'date':local.date().isoformat(),'week':week}


def pending_check(store):
    human=store.get('human','control:check-now',{})
    request=human.get('Check Now Request')
    return request if isinstance(request,str) and request.strip() and request!=store.get('control','last_check_request') else None


def run_tick(store,monitor,sync,instant=None):
    schedule=store.get('config','schedule',monitor.config['schedule'])
    previous=store.get('runtime','schedule',{})
    due=schedule_due(schedule,previous,instant)
    if not schedule['enabled']: return {'state':'activation_pending'}
    with OwnedLock(store.directory):
        result={}
        if due['sync']:
            monitor.health_rows()
            result['sync']=sync.sync();monitor.ingest_answers();previous['sync']=now()
        request=pending_check(store)
        check=due['daily'] or due['weekly'] or request is not None
        if request:
            # Reserve before work. A crash reports interrupted, never hot-replays the request.
            with store.transaction(): store.put('control','last_check_request',request);store.put('control','request_state','running')
        if check or (due['model'] and due['sync']):
            result['cycle']=monitor.cycle(check_sources=bool(check),discover=due['weekly'],allow_analysis=due['model'])
            if due['daily']: previous['daily']=due['date']
            if due['weekly']: previous['weekly']=due['week']
            if request:
                with store.transaction():
                    store.put('control','request_state','completed')
                    row=store.get('finding','control:check-now');row['Check Now Result']='Bounded request completed. See source-health rows; failures are not no-change results.'
                    store.publish('control:check-now',row,substantive=False)
            result['publication']=sync.sync()
        with store.transaction(): store.put('runtime','schedule',previous)
        return result


def serve(store,monitor,sync,minutes,owner):
    if not 1<=minutes<=1440 or len(owner)!=32: raise ValueError('bounded_service_identity_required')
    with OwnedLock(store.directory,'service'):
        with store.transaction(): store.put('runtime','owner',{'marker':owner,'pid':os.getpid(),'started':now(),'state':'running'})
        deadline=time.monotonic()+minutes*60
        try:
            while time.monotonic()<deadline:
                if store.get('control','stop')==owner: break
                run_tick(store,monitor,sync)
                time.sleep(5)
        finally:
            with store.transaction(): store.put('runtime','owner',{'marker':owner,'pid':os.getpid(),'state':'stopped'})


def stop_owned(store):
    owner=store.get('runtime','owner')
    if not owner or owner.get('state')!='running': return {'state':'already_stopped'}
    # Cooperative signal tied to this service generation; no PID kill or shared stop controls.
    with store.transaction(): store.put('control','stop',owner['marker'])
    return {'state':'stop_requested'}
