"""Operator CLI; end users use only the dedicated Smartsheet."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from dotenv import dotenv_values
from .store import Store, now
from .sources import Retriever
from .analysis import ComplianceModel
from .service import Monitor
from .sheet import SheetAPI, Synchronizer
from .runtime import OwnedLock, serve, stop_owned, run_tick

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description='Program Compliance Monitor — isolated CLASS pilot')
    parser.add_argument('command',choices=['setup','check','sync','status','backup','start','serve','stop','tick','schedule'])
    parser.add_argument('--analyze',action='store_true',help='Bounded local-model acceptance; no recurring activation')
    parser.add_argument('--discover',action='store_true')
    parser.add_argument('--minutes',type=int,default=60)
    parser.add_argument('--owner')
    parser.add_argument('--window',help='Explicit approved local-model window HH:MM-HH:MM')
    parser.add_argument('--confirm-idle-window',action='store_true')
    parser.add_argument('--enable',action='store_true')
    args=parser.parse_args()
    config=json.loads((ROOT/'config/program_compliance/class.json').read_text(encoding='utf-8-sig'))
    directory=Path(os.environ['LOCALAPPDATA'])/'LTHHC'/'ProgramCompliance'
    store=Store(directory,readonly=args.command=='status')
    try:
        if args.command=='schedule':
            import re
            from .deployment import install_schedule
            schedule=dict(config['schedule'])
            if args.enable:
                if not args.window or not args.confirm_idle_window or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d-(?:[01]\d|2[0-3]):[0-5]\d',args.window): raise ValueError('explicit_window_and_sharing_confirmation_required')
                start,end=args.window.split('-')
                if start==end: raise ValueError('bounded_window_required')
                schedule.update(enabled=True,model_window=[start,end],resource_sharing_confirmed=True)
            # Task activation is explicit, never part of setup or bounded acceptance.
            install_schedule(ROOT,directory,schedule['enabled'])
            with store.transaction(): store.put('config','schedule',schedule)
            print(json.dumps({'schedule_enabled':schedule['enabled'],'timezone':schedule['timezone'],'service_started':False}));return
        if args.command=='stop': print(json.dumps(stop_owned(store)));return
        if args.command=='status':
            print(json.dumps({'owner_state':store.get('runtime','owner',{}).get('state','stopped'),'schedule':store.get('config','schedule',config['schedule']),'finding_count':len(store.items('finding')),'source_count':len(store.items('source')),'sheet_configured':bool(store.get('config','sheet'))}));return
        if args.command=='backup':
            destination=directory.parent/'ProgramComplianceBackups'/now().replace(':','-')
            destination.parent.mkdir(parents=True,exist_ok=True)
            store.backup(destination);print(json.dumps({'backup':'verified_copy_created'}));return
        credentials=dotenv_values(ROOT/'.env')
        api=SheetAPI(credentials.get('SMARTSHEET_API_TOKEN'))
        model=ComplianceModel(model=credentials.get('OLLAMA_MODEL') or 'llama3.1:8b')
        monitor=Monitor(store,config,Retriever(config['boundaries']),model)
        if args.command=='setup':
            with OwnedLock(directory):
                binding=api.ensure(store);monitor.basic_rows();monitor.question();monitor.health_rows()
            print(json.dumps({'sheet_url':binding['url'],'sheet_name':binding['name'],'workspace':'LT Automation Platform','state':'configured'}));return
        binding=store.get('config','sheet')
        if not binding: raise ValueError('dedicated_sheet_setup_required')
        sync=Synchronizer(store,api,binding['id'])
        if args.command=='check':
            with OwnedLock(directory):
                result=monitor.cycle(discover=args.discover,allow_analysis=args.analyze)
                result['sync']=sync.sync()
            print(json.dumps(result));return
        if args.command=='sync':
            with OwnedLock(directory): print(json.dumps(sync.sync()))
            return
        if args.command=='tick': print(json.dumps(run_tick(store,monitor,sync)));return
        schedule=store.get('config','schedule',config['schedule'])
        if not schedule['enabled'] or not schedule.get('model_window') or not schedule.get('resource_sharing_confirmed'): raise ValueError('activation_decision_required')
        if args.command=='start':
            owner=uuid.uuid4().hex
            with OwnedLock(directory,'service'): pass
            subprocess.Popen([sys.executable,'-m','src.program_compliance','serve','--minutes',str(args.minutes),'--owner',owner],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            print(json.dumps({'state':'start_requested','bounded_minutes':args.minutes}));return
        if args.command=='serve': serve(store,monitor,sync,args.minutes,args.owner or '')
    except Exception as error:
        with store.transaction(): store.event('operator_failure','cli',{'category':type(error).__name__})
        # Fixed names only. Never print remote payloads, credential values or row identities.
        safe=str(error) if isinstance(error,(ValueError,RuntimeError)) and str(error).replace('_','').isalnum() and len(str(error))<90 else type(error).__name__
        print(json.dumps({'state':'failed','category':safe}));raise SystemExit(1)
    finally: store.close()

if __name__=='__main__': main()
