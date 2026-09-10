"""Dedicated-sheet REST boundary with human ownership and uncertain-write reconciliation."""
from __future__ import annotations
import json
import time
import requests
from .store import canonical, now, digest
from .determinations import STATUSES, presentation

HUMAN=('Implementation Status','Applicability Decision','Decision Notes','Owner','Review Status','Internal Target Date','Completion Evidence','Reviewed Revision','Check Now Request')
SYSTEM=('Implementation Assessment','Record Type','Program','Topic','Responsible Party/Duty Scope','Source Section/Link','Requirement/Change Summary','Suggested Applicability/Reason','Proposed Action','Publication Date','Effective Date','Source Deadline/Trigger','Review Needed','Current Revision','Finding Key','Source Health','Last Successful Check','Evidence / Before and After','Related Findings','Suggested Owner','Check Now Result')
REVIEW_FORMULA='=IF(OR([Record Type]@row = "Group", [Record Type]@row = "Reference", [Record Type]@row = "Control"), 0, IF([Record Type]@row = "Source Health", IF([Source Health]@row = "Healthy", 0, 1), IF(AND([Reviewed Revision]@row = [Current Revision]@row, NOT(ISBLANK([Reviewed Revision]@row))), 0, 1)))'


class SheetFailure(RuntimeError):
    pass


def same_value(left,right):
    return left==right or (left in ('',None) and right in ('',None))


def columns():
    titles=['Topic','Record Type','Program','Review Needed','Suggested Applicability/Reason','Proposed Action','Applicability Decision','Owner','Review Status','Implementation Status','Implementation Assessment','Reviewed Revision','Current Revision','Internal Target Date','Completion Evidence','Decision Notes','Responsible Party/Duty Scope','Source Section/Link','Requirement/Change Summary','Publication Date','Effective Date','Source Deadline/Trigger','Evidence / Before and After','Source Health','Last Successful Check','Related Findings','Suggested Owner','Check Now Request','Check Now Result','Finding Key']
    result=[]
    for title in titles:
        col={'title':title,'type':'TEXT_NUMBER','width':180}
        if title=='Topic': col.update(primary=True,width=240)
        if title in ('Publication Date','Effective Date','Internal Target Date'): col['type']='DATE'
        if title=='Review Needed': col.update(type='CHECKBOX',width=95)
        if title=='Applicability Decision': col.update(type='PICKLIST',options=['Needs Confirmation','Applies','Does Not Apply','Other Party'])
        if title=='Implementation Status': col.update(type='PICKLIST',options=list(STATUSES),width=160)
        if title=='Implementation Assessment': col['width']=280
        if title=='Review Status': col.update(type='PICKLIST',options=['Unreviewed','Investigating','Action Planned','In Progress','Complete','No Action'])
        if title in SYSTEM: col['locked']=True
        if title=='Finding Key': col['hidden']=True
        result.append(col)
    return result


class SheetAPI:
    BASE='https://api.smartsheet.com/2.0'
    def __init__(self,token,session=None):
        if not token: raise SheetFailure('credentials_unavailable')
        self.session=session or requests.Session()
        self.session.headers.update({'Authorization':'Bearer '+token,'Content-Type':'application/json'})

    def request(self,method,path,**kwargs):
        if not path.startswith(('/workspaces','/sheets')): raise SheetFailure('api_boundary')
        attempts=3 if method=='GET' else 1
        for attempt in range(attempts):
            try:
                r=self.session.request(method,self.BASE+path,timeout=(10,30),allow_redirects=False,**kwargs)
                if 200<=r.status_code<300:
                    value=r.json()
                    if isinstance(value,dict): return value
                if r.status_code not in (429,500,502,503,504):
                    try: code=r.json().get('errorCode',0)
                    except ValueError: code=0
                    code=code if type(code) is int else 0
                    raise SheetFailure('sheet_request_rejected_'+str(r.status_code)+'_'+str(code))
            except (requests.RequestException,ValueError):
                pass
            if attempt+1<attempts: time.sleep(2**attempt)
        raise SheetFailure('sheet_read_unavailable' if method=='GET' else 'sheet_write_uncertain')

    def workspace(self,name):
        data=self.request('GET','/workspaces',params={'includeAll':'true'})
        matches=[w for w in data['data'] if w['name']==name]
        if len(matches)!=1: raise SheetFailure('workspace_ambiguous')
        return matches[0]['id']

    def workspace_sheets(self,workspace):
        data=self.request('GET','/workspaces/'+str(workspace),params={'loadAll':'true'})
        def walk(node):
            yield from node.get('sheets',[])
            for child in node.get('folders',[]): yield from walk(child)
        return list(walk(data))

    def ensure(self,store,workspace_name='LT Automation Platform',sheet_name='Program Compliance'):
        workspace=self.workspace(workspace_name)
        matches=[s for s in self.workspace_sheets(workspace) if s['name']==sheet_name]
        if len(matches)>1: raise SheetFailure('sheet_name_ambiguous')
        binding=store.get('config','sheet')
        if binding and (binding['workspace']!=workspace or not matches or binding['id']!=matches[0]['id']): raise SheetFailure('sheet_binding_changed')
        if not matches:
            intent=store.get('config','sheet_create')
            if intent and intent.get('state')!='rejected': raise SheetFailure('sheet_creation_uncertain_requires_reconciliation')
            with store.transaction(): store.put('config','sheet_create',{'workspace':workspace,'name':sheet_name,'state':'reserved'})
            try:
                creation_columns=[{k:v for k,v in c.items() if k!='locked'} for c in columns()]
                created=self.request('POST',f'/workspaces/{workspace}/sheets',json={'name':sheet_name,'columns':creation_columns})
                created_id=created.get('result',{}).get('id')
                if type(created_id) is int:
                    with store.transaction(): store.put('config','sheet_create',{'workspace':workspace,'name':sheet_name,'state':'created_pending_readback','id':created_id})
            except SheetFailure as error:
                if str(error).startswith('sheet_request_rejected_'):
                    with store.transaction(): store.put('config','sheet_create',{'workspace':workspace,'name':sheet_name,'state':'rejected','category':str(error)})
                raise
            matches=[s for s in self.workspace_sheets(workspace) if s['name']==sheet_name]
            if not matches and type(created_id) is int:
                # Exact returned identity can reconcile eventual workspace-list visibility.
                direct=self.request('GET','/sheets/'+str(created_id),params={'pageSize':1})
                if direct.get('name')==sheet_name: matches=[{'id':created_id,'name':sheet_name}]
            if len(matches)!=1: raise SheetFailure('sheet_creation_readback_failed')
        sheet=self.request('GET','/sheets/'+str(matches[0]['id']),params={'pageSize':1})
        expected={c['title']:c['type'] for c in columns()}
        actual={c['title']:c['type'] for c in sheet['columns']}
        missing=set(expected)-set(actual)
        if missing and missing <= {'Implementation Status','Implementation Assessment'}:
            additions=[]
            for col in columns():
                if col['title'] in missing:
                    additions.append({**{k:v for k,v in col.items() if k!='locked'},'index':len(sheet['columns'])})
            self.request('POST',f'/sheets/{sheet["id"]}/columns',json=additions)
            sheet=self.request('GET','/sheets/'+str(sheet['id']),params={'pageSize':1})
            actual={c['title']:c['type'] for c in sheet['columns']}
        if any(actual.get(k)!=v for k,v in expected.items()): raise SheetFailure('existing_sheet_schema_requires_review')
        for col in sheet['columns']:
            if col['title'] in SYSTEM and not col.get('locked'):
                self.request('PUT',f'/sheets/{sheet["id"]}/columns/{col["id"]}',json={'locked':True})
        value={'id':sheet['id'],'workspace':workspace,'url':sheet['permalink'],'name':sheet_name}
        with store.transaction(): store.put('config','sheet',value)
        return value


class Synchronizer:
    def __init__(self,store,api,sheet_id):
        self.store=store;self.api=api;self.sheet_id=sheet_id
        binding=store.get('config','sheet')
        if not binding or binding['id']!=sheet_id: raise SheetFailure('dedicated_sheet_binding_required')
        self.path='/sheets/'+str(sheet_id)

    def read(self):
        page=1;seen=set();rows=[];version=None;total=None;schema=None
        while True:
            data=self.api.request('GET',self.path,params={'pageSize':100,'page':page})
            if version is None: version=data['version'];total=data['totalRowCount'];schema={c['title']:c for c in data['columns']}
            if version!=data['version'] or total!=data['totalRowCount']: raise SheetFailure('sheet_changed_during_read')
            if not set(SYSTEM+HUMAN)<=set(schema): raise SheetFailure('sheet_schema_changed')
            inverse={c['id']:name for name,c in schema.items()}
            batch=data.get('rows',[])
            for row in batch:
                if row['id'] in seen: raise SheetFailure('sheet_pagination_invalid')
                seen.add(row['id'])
                cells={inverse[c['columnId']]:c.get('value') for c in row['cells'] if c['columnId'] in inverse}
                formulas={inverse[c['columnId']]:c.get('formula') for c in row['cells'] if c.get('formula') and c['columnId'] in inverse}
                rows.append({'id':row['id'],'values':cells,'formulas':formulas,'parent_id':row.get('parentId'),'expanded':row.get('expanded')})
            if len(rows)==total: break
            if not batch or len(rows)>total: raise SheetFailure('sheet_pagination_invalid')
            page+=1
        self.schema=schema
        return rows

    def cell(self,title,value):
        if title not in SYSTEM: raise SheetFailure('human_field_write_blocked')
        col=self.schema[title]
        if title=='Review Needed': return {'columnId':col['id'],'formula':REVIEW_FORMULA}
        if value is None: return {'columnId':col['id'],'value':None}
        if type(value) not in (str,bool,int,float) or (isinstance(value,str) and len(value)>3900): raise SheetFailure('cell_shape_invalid')
        if isinstance(value,str) and value.startswith(('=','+','@')): value="'"+value
        return {'columnId':col['id'],'value':value,'strict':True}

    def sync(self):
        rows=self.read();bykey={}
        for row in rows:
            key=row['values'].get('Finding Key')
            if key: bykey.setdefault(key,[]).append(row)
        with self.store.transaction():
            for key,matches in bykey.items():
                if len(matches)==1:
                    self.store.observe_human(key,{name:matches[0]['values'].get(name) for name in HUMAN},capture_determination=False)
        from .responsibility import reconcile
        reconcile(self.store)
        with self.store.transaction():
            for key,matches in bykey.items():
                if len(matches)==1:self.store.observe_human(key,self.store.get('human',key,{}))
        counts={'created':0,'updated':0,'unchanged':0,'blocked':0}
        # Always reconcile known findings, including restored backups and human acknowledgments.
        findings=self.store.items('finding')
        if self.store.get('config','topic_groups'):
            from .topics import prepare
            findings=prepare(self.store)
        for key,payload in findings:
            if self.store.get('config','baseline_presentation',{}).get('suppress_test') and payload.get('Record Type','').startswith('TEST'): continue
            payload=presentation(self.store,key,payload)
            try:
                matches=bykey.get(key,[])
                if len(matches)>1: raise SheetFailure('finding_duplicate')
                old=matches[0] if matches else None
                intent=self.store.db.execute('SELECT * FROM outbox WHERE key=?',(key,)).fetchone()
                if old is None and (self.store.get('row_binding',key) or (intent and intent['state']=='uncertain')):
                    raise SheetFailure('row_missing_after_uncertain_write')
                assignment=self.store.get('topic_assignment',key) if self.store.get('config','topic_groups') else None
                parent_id=None
                if assignment:
                    parents=bykey.get(assignment['group_key'],[])
                    if len(parents)!=1: raise SheetFailure('topic_parent_unverified')
                    parent_id=parents[0]['id']
                hierarchy_changed=bool(assignment and (old is None or old.get('parent_id')!=parent_id))
                changes={name:payload.get(name) for name in SYSTEM if name!='Review Needed' and ((old is None and payload.get(name) not in ('',None)) or (old is not None and not same_value(old['values'].get(name),payload.get(name))))}
                if old is None or old['formulas'].get('Review Needed')!=REVIEW_FORMULA: changes['Review Needed']=True
                if not changes and not hierarchy_changed:
                    counts['unchanged']+=1
                    with self.store.transaction():
                        self.store.db.execute('UPDATE outbox SET state="verified" WHERE key=?',(key,))
                        self.store.put('row_binding',key,{'id':old['id']})
                    continue
                cells=[self.cell(name,value) for name,value in changes.items()]
                restore=self.store.get('human_restore',key)
                restored_fields={}
                if old is None and restore and restore.get('state')=='pending':
                    maintenance=self.store.get('maintenance','authorized_baseline',{})
                    if restore['reset_id']!=maintenance.get('id') or digest(restore['fields'])!=restore['digest']:
                        raise SheetFailure('authorized_human_restore_unproven')
                    # Only exact previously observed human values are restored atomically
                    # with recreation, under the explicit authorized reset. Never update
                    # existing human cells or invent a reported implementation status.
                    restored_fields={k:v for k,v in restore['fields'].items() if k in HUMAN and v not in ('',None)}
                    for name,value in restored_fields.items():
                        cells.append({'columnId':self.schema[name]['id'],'value':value,'strict':True})
                with self.store.transaction():
                    self.store.db.execute('UPDATE outbox SET state="uncertain",attempts=attempts+1 WHERE key=?',(key,))
                    self.store.event('write_reserved',key,{'revision':payload['Current Revision'],'field_names':list(changes)})
                request={'cells':cells}
                if old: request['id']=old['id']
                else: request['toBottom']=True
                if hierarchy_changed: request.update(parentId=parent_id,toBottom=True)
                if old is None and payload.get('Record Type')=='Group': request['expanded']=False
                self.api.request('PUT' if old else 'POST',self.path+'/rows',json=[request])
                fresh=[r for r in self.read() if r['values'].get('Finding Key')==key]
                if len(fresh)!=1: raise SheetFailure('write_readback_ambiguous')
                actual=fresh[0]
                if hierarchy_changed and actual.get('parent_id')!=parent_id: raise SheetFailure('topic_hierarchy_readback_mismatch')
                bykey[key]=[actual]
                if any((actual['formulas'].get(k)!=REVIEW_FORMULA if k=='Review Needed' else not same_value(actual['values'].get(k),v)) for k,v in changes.items()): raise SheetFailure('write_readback_mismatch')
                if any(not same_value(actual['values'].get(k),v) for k,v in restored_fields.items()):
                    raise SheetFailure('authorized_human_restore_readback_mismatch')
                with self.store.transaction():
                    if restore:
                        self.store.put('human_restore',key,{**restore,'state':'reconciled'})
                    self.store.put('row_binding',key,{'id':actual['id']})
                    self.store.db.execute('UPDATE outbox SET state="verified" WHERE key=?',(key,))
                    self.store.event('write_verified',key,{'revision':payload['Current Revision']})
                    self.store.observe_human(key,{name:actual['values'].get(name) for name in HUMAN})
                counts['updated' if old else 'created']+=1
            except SheetFailure as error:
                counts['blocked']+=1
                with self.store.transaction(): self.store.event('sync_failed',key,{'category':str(error)})
        return counts
