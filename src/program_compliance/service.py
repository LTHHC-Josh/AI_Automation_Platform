"""Bounded incremental source checks, grounded baseline and durable review queue."""
from __future__ import annotations
import difflib
import re
import time
import uuid
from datetime import datetime,timezone,timedelta
from urllib.parse import urlsplit
from .analysis import package, validate, analysis_key
from .sources import parse, SourceFailure, allowed, canonical_url
from .store import digest, now


def record(kind,topic,summary,action='',**fields):
    return {'Record Type':kind,'Program':fields.pop('program',''),'Topic':topic,'Requirement/Change Summary':summary,'Proposed Action':action,**fields}


def align(old,texts):
    """Keep ordinary edited/moved paragraph identities; split/merge stays explicitly unresolved."""
    result=[None]*len(texts)
    previous=[p['text'] for p in old]
    for tag,a,b,c,d in difflib.SequenceMatcher(None,previous,texts,autojunk=False).get_opcodes():
        if tag=='equal' or (tag=='replace' and b-a==d-c):
            for oi,ni in zip(range(a,b),range(c,d)): result[ni]={'id':old[oi]['id'],'text':texts[ni]}
    for i,item in enumerate(result):
        if item is None: result[i]={'id':uuid.uuid4().hex[:16],'text':texts[i]}
    return result


class Monitor:
    def __init__(self,store,config,retriever,model):
        self.store=store;self.config=config;self.retriever=retriever;self.model=model
        with store.transaction():
            if not store.get('profile','agency'): store.put('profile','agency',config['profile'])
            for source in config['seeds']:
                if not store.get('source',source['id']): store.put('source',source['id'],{**source,'health':'Coverage Gap','checked':None})
            store.put('config','registry',config)

    def record(self,*args,**kwargs):
        return record(*args,program=self.profile()['program'],**kwargs)

    def profile(self): return self.store.get('profile','agency')

    def basic_rows(self):
        with self.store.transaction():
            control=self.record('Control','Check Now','Enter a new request label in Check Now Request for one bounded source check. Requests are processed while the service is enabled.','Use a different label for each request. Recurring activation remains disabled until its operating window is confirmed.')
            previous=self.store.get('finding','control:check-now',{})
            if previous.get('Check Now Result'): control['Check Now Result']=previous['Check Now Result']
            self.store.publish('control:check-now',control,substantive=False)
            self.store.publish('reference:how-to-review',self.record('Reference','How to review a requirement','Read the source and evidence, enter your decision/status and copy Current Revision into Reviewed Revision when finished. An old acknowledgment never acknowledges a newer version.','Owners, notes, status, targets and completion evidence are never overwritten. Source deadline and internal target are separate. Policy coverage is not assessed.'))
            for i,gap in enumerate(self.config['coverage_gaps']): self.store.publish('coverage:'+str(i),self.record('Coverage','Coverage boundary',gap,'Review if this missing coverage affects agency decisions.',**{'Source Health':'Coverage Gap'}))

    def question(self):
        profile=self.profile()
        related=[key for key,item in self.store.items('finding') if item.get('Suggested Applicability/Reason','').startswith('Needs Confirmation')]
        if profile.get('contracted_services') is not None and profile.get('active_services') is not None: return
        if self.store.get('proposed_profile','agency'):
            with self.store.transaction():
                row=self.store.get('finding','question:agency-services');row['Related Findings']='\n'.join(related)[:3800]
                self.store.publish('question:agency-services',row,substantive=False)
            return
        with self.store.transaction():
            self.store.publish('question:agency-services',self.record('Question','Confirm agency service scope','One shared question affects service-specific findings. Contracted and actively delivered services are both unknown. Staffing does not establish contractual scope.','In Decision Notes, enter two lines: contracted: service list; active: service list. Then copy Current Revision into Reviewed Revision to confirm those agency facts.',**{'Related Findings':'\n'.join(related)[:3800],'Suggested Applicability/Reason':'Needs Confirmation'}),substantive=False)

    def ingest_answers(self):
        key='question:agency-services';human=self.store.get('human',key,{});finding=self.store.get('finding',key,{})
        notes=human.get('Decision Notes','') or ''
        if self.store.get('answer_digest',key)==digest(notes): return False
        facts={}
        for line in notes.splitlines():
            if ':' in line:
                label,value=line.split(':',1)
                if label.strip().lower() in ('contracted','active') and value.strip(): facts[label.strip().lower()]=value.strip()
        if set(facts)!= {'contracted','active'}: return False
        proposal=self.store.get('proposed_profile','agency',{})
        if proposal.get('digest')!=digest(notes):
            with self.store.transaction():
                self.store.put('proposed_profile','agency',{'digest':digest(notes),'facts':facts})
                self.store.publish(key,self.record('Question','Confirm reported agency facts','Contracted: '+facts['contracted']+'\nActive: '+facts['active'],'Review these reported facts, then copy this new Current Revision into Reviewed Revision to confirm them.',**{'Suggested Applicability/Reason':'Needs Confirmation'}),evidence_version=digest(notes))
            return False
        if not human.get('Reviewed Revision') or human.get('Reviewed Revision')!=finding.get('Current Revision'): return False
        profile=self.profile();profile.update(contracted_services=facts['contracted'],active_services=facts['active'],version=profile['version']+1)
        with self.store.transaction():
            self.store.event('profile_history','agency',self.profile());self.store.put('profile','agency',profile)
            self.store.put('answer_digest',key,digest(notes))
            self.store.put('profile_evidence','agency',{'question_revision':finding['Current Revision'],'answer_digest':digest(notes)})
        return True

    def discover(self,source,links):
        known={canonical_url(s['url']) for _,s in self.store.items('source')}
        discovered=sum(1 for k,_ in self.store.items('source') if k.startswith('discovered:'))
        for url in links:
            if url in known: continue
            # Shared publisher paths are allowed only with relevant CLASS/EVV/rule linkage.
            relevant=any(t in url.lower() for t in ('class','/26-','/25-','259','electronic-visit-verification','/forms/','/texreg/','/tac/'))
            if not allowed(url,self.config['boundaries']):
                if relevant: self.store.put('coverage_candidate',digest(url),{'url':url,'parent':source['id'],'reason':'outside_approved_boundary'})
                continue
            if not relevant or discovered>=self.config['limits']['discovered_sources']: continue
            # Do not turn the general Register archive into an unbounded statewide crawl.
            if 'sos.texas.gov' in url and not any(t in url.lower() for t in ('259','26.health','/tac/')): continue
            identity='discovered:'+digest(url)[:20]
            self.store.put('source',identity,{'id':identity,'url':url,'publisher':urlsplit(url).hostname,'type':'Linked official source','scope':'Linked from '+source['id'],'analyze':True,'health':'Coverage Gap','checked':None,'parent':source['id']})
            discovered+=1;known.add(url)

    def check_source(self,source,discover=False):
        key=source['id']
        try:
            fetched=self.retriever.get(source['url'],source)
            timestamp=now()
            if fetched.get('unchanged'):
                if not source.get('version'): raise SourceFailure('no_valid_version_for_304')
                source.update(health='Healthy',checked=timestamp,last_success=timestamp)
            else:
                parsed=parse(fetched['raw'],fetched['type'],fetched['url'])
                previous=self.store.get('document',key)
                if previous and len(parsed['text'])<len(previous['text'])*0.3: raise SourceFailure('suspicious_content_loss')
                version=digest(parsed['text']);raw_version=self.store.snapshot(fetched['raw'])
                with self.store.transaction():
                    self.store.put('source_version',key+':'+raw_version,{'raw':raw_version,'normalized':version,'url':fetched['url'],'retrieved':timestamp,'parsed':parsed})
                    self.store.put('document',key,parsed)
                    if source.get('version')!=version: self.store.event('source_change',key,{'before':source.get('version'),'after':version})
                source.update(health='Healthy',checked=timestamp,last_success=timestamp,version=version,raw_version=raw_version,etag=fetched.get('etag'),modified=fetched.get('modified'),url=fetched['url'])
                if discover:
                    with self.store.transaction(): self.discover(source,parsed['links'])
            with self.store.transaction(): self.store.put('source',key,source)
            return True
        except SourceFailure as error:
            source.update(health='Parser Failed' if str(error) in ('parser_failed','suspicious_content_loss') else 'Unavailable',checked=now(),failure=str(error))
            with self.store.transaction():
                self.store.put('source',key,source);self.store.event('retrieval_failed',key,{'category':str(error)})
            return False

    def health_rows(self):
        with self.store.transaction():
            for key,source in self.store.items('source'):
                pending=self.store.get('source_analysis',key,{})
                health=source['health']
                if health=='Healthy' and source.get('last_success') and (datetime.now(timezone.utc)-datetime.fromisoformat(source['last_success'])).total_seconds()>172800: health='Stale'
                if health=='Healthy' and pending.get('pending'): health='Analysis Pending'
                summary=source['scope']+'. Coverage is limited to successfully retrieved and analyzed content.'
                if pending.get('pending'): summary+=' Analysis pending: '+pending.get('reason','bounded backlog')+'.'
                self.store.publish('health:'+key,self.record('Source Health',source['scope'],summary,'Review persistent access failures or unresolved source coverage.' if health!='Healthy' else '',**{'Source Section/Link':source['url'],'Source Health':health,'Last Successful Check':source.get('last_success'),'Review Needed':health!='Healthy'}),substantive=False)

    def analyze_source(self,source,budget):
        document=self.store.get('document',source['id'])
        if not document or not source.get('analyze'): return 0
        used=0;pending=False;reason='bounded backlog'
        for section in document['sections']:
            if not re.search(r'\bDSA\s+(?:must|shall)\b',section['text']): continue
            section_key=source['id']+':'+digest(section['heading'])[:12]
            old=self.store.get('section',section_key,{'paragraphs':[]})
            texts=section['text'].split('\n')
            blocks=align(old['paragraphs'],texts)
            with self.store.transaction(): self.store.put('section',section_key,{'heading':section['heading'],'paragraphs':blocks,'version':digest(section['text'])})
            dependencies={}
            references=re.findall(r'\b(?:Section\s+\d{3,5}|Appendix\s+[IVX]+|\d+\s+TAC\s+(?:Section\s+)?[\d.]+)',section['text'])
            if references:
                # Missing authoritative cross-reference context blocks this section only.
                for ref in references:
                    candidates=[s for _,doc in self.store.items('document') for s in doc['sections'] if ref.replace('Section ','') in s['heading']]
                    if len(candidates)==1: dependencies[ref]=candidates[0]
                if len(dependencies)!=len(set(references)):
                    pending=True;reason='referenced context unavailable';continue
            profile=self.profile()
            # Agency-wide-only sections do not depend on unknown service lists.
            pkg=package(source,section,profile,dependencies)
            pkg['source_version']=digest(section['text'])
            pkg['profile']={k:v for k,v in profile.items() if k!='version'}
            request_key=analysis_key(pkg,self.model.model)
            with self.store.transaction(): self.store.put('dependencies',section_key,{'references':references,'resolved':{k:digest(v) for k,v in dependencies.items()}})
            result=self.store.get('analysis',request_key)
            if result is None:
                # Retain invalid candidates for diagnosis; unchanged cycles do not repeat inference.
                failure=self.store.get('analysis_failure',request_key)
                retry_due=failure and failure.get('retry_after') and datetime.now(timezone.utc)>=datetime.fromisoformat(failure['retry_after']) and failure.get('attempts',3)<3
                if failure and not retry_due: pending=True;reason='retained analysis failure or bounded retry backoff';continue
                if self.store.get('analysis_attempt',request_key) and not retry_due: pending=True;reason='interrupted analysis requires reconciliation';continue
                if used>=budget: pending=True;continue
                used+=1
                try:
                    with self.store.transaction(): self.store.put('analysis_attempt',request_key,{'state':'reserved','started':now()})
                    raw=self.model.analyze(pkg)
                    with self.store.transaction(): self.store.put('analysis_candidate',request_key,{'result':raw,'metrics':self.model._last_request_metrics,'source':source['id']})
                    result=validate(raw,pkg)
                    with self.store.transaction(): self.store.put('analysis',request_key,result)
                except Exception as error:
                    pending=True;reason='analysis validation or local model failure'
                    transient=str(error) in ('local_model_unavailable','local_model_request_timeout','local_model_request_failed','shared_model_capacity_deferred','compliance_busy')
                    attempts=(failure or {}).get('attempts',0)+1
                    retry_after=(datetime.now(timezone.utc)+timedelta(minutes=15*attempts)).isoformat() if transient and attempts<3 else None
                    with self.store.transaction(): self.store.put('analysis_failure',request_key,{'category':str(error) if transient else type(error).__name__,'metrics':self.model._last_request_metrics,'attempts':attempts,'retry_after':retry_after})
                    continue
            for obligation in result:
                block=blocks[obligation['paragraph']];key='requirement:'+section_key+':'+block['id']
                old_finding=self.store.get('finding',key)
                previous=self.store.get('requirement_evidence',key)
                supporting_profile={k:profile[k] for k in ('program','role')}
                if obligation['scope']!='Agency-wide': supporting_profile.update(contracted_services=profile['contracted_services'],active_services=profile['active_services'])
                meaning={'quote':obligation['quote'],'profile':supporting_profile,'dependencies':dependencies,'rules':'pcm-applicability-1'}
                meaning_version=digest(meaning)
                # Keep compatible model wording stable if evidence and supporting facts did not change.
                if previous and previous['meaning_version']==meaning_version: continue
                is_change=old_finding is not None
                proposed='proposed' in source['url'].lower() or source.get('type')=='Proposed rule'
                payload=self.record('Reference' if proposed else ('Actionable Change' if is_change else 'Requirement'),obligation['topic'],obligation['quote'],('Review proposal; it is not an effective requirement.' if proposed else obligation['action']),**{
                    'Responsible Party/Duty Scope':'DSA / '+obligation['scope'],
                    'Source Section/Link':section['heading']+' | '+source['url'],
                    'Suggested Applicability/Reason':('Proposed rule â€” not an effective requirement.' if proposed else obligation['applicability']+' â€” '+obligation['reason']),
                    'Effective Date':None if proposed else obligation['effective'],'Source Deadline/Trigger':None if proposed else obligation['deadline'],
                    'Evidence / Before and After':(('Before: '+previous['quote']+'\nAfter: ') if previous else 'Evidence: ')+obligation['quote'],
                    'Related Findings':'question:agency-services' if obligation['scope']!='Agency-wide' else '',
                    'Suggested Owner':self.config.get('routing',{}).get(obligation['scope'],''),
                    'Review Needed':True})
                if source.get('test'):
                    payload['Record Type']='TEST Change' if is_change else 'TEST Requirement'
                    payload['Topic']='TEST â€” '+payload['Topic']
                    payload['Source Section/Link']='TEST fixture; not an official revision. Basis: '+source['url']
                    payload['Evidence / Before and After']='TEST ONLY\n'+payload['Evidence / Before and After']
                if any(isinstance(v,str) and len(v)>3800 for v in payload.values()): pending=True;reason='evidence exceeds concise presentation limit';continue
                with self.store.transaction():
                    self.store.put('requirement_evidence',key,{'quote':obligation['quote'],'meaning_version':meaning_version,'source_version':source['version'],'section_version':pkg['source_version'],'profile':supporting_profile,'dependencies':dependencies,'request_key':request_key})
                    self.store.publish(key,payload,evidence_version=meaning_version)
            # Deleted/moved or split paragraphs do not silently retire duties.
            ids={p['id'] for p in blocks}
            selected_ids={blocks[o['paragraph']]['id'] for o in result}
            for key,item in self.store.items('finding'):
                block_id=key.rsplit(':',1)[1]
                previous_evidence=self.store.get('requirement_evidence',key,{})
                current_text=next((p['text'] for p in blocks if p['id']==block_id),None)
                changed_unselected=block_id not in selected_ids and current_text!=previous_evidence.get('quote')
                if key.startswith('requirement:'+section_key+':') and (block_id not in ids or changed_unselected):
                    with self.store.transaction(): self.store.publish(key,{**item,'Record Type':'Actionable Change','Proposed Action':'Source paragraph removed, split or moved. Review continued applicability; previous evidence is retained.','Review Needed':True})
        with self.store.transaction(): self.store.put('source_analysis',source['id'],{'pending':pending,'reason':reason if pending else ''})
        return used

    def cycle(self,check_sources=True,discover=False,allow_analysis=True):
        self.basic_rows();self.ingest_answers();started=time.monotonic()
        counts={'checked':0,'retrieval_failed':0,'model_calls':0}
        sources=[s for _,s in self.store.items('source') if not s.get('test')]
        seeds={s['id']:i for i,s in enumerate(self.config['seeds'])}
        sources.sort(key=lambda s:(s.get('checked') or '',seeds.get(s['id'],100)))
        if check_sources:
            for source in sources[:self.config['limits']['sources_per_check']]:
                if time.monotonic()-started>self.config['limits']['seconds_per_check']: break
                counts['checked']+=1
                if not self.check_source(source,discover): counts['retrieval_failed']+=1
        if allow_analysis:
            for _,source in self.store.items('source'):
                if source.get('test'): continue
                remaining=self.config['limits']['analyses_per_check']-counts['model_calls']
                if remaining<=0 or time.monotonic()-started>self.config['limits']['seconds_per_check']: break
                counts['model_calls']+=self.analyze_source(source,remaining)
        self.question();self.health_rows()
        with self.store.transaction(): self.store.put('runtime','last_cycle',{'at':now(),**counts})
        return counts
