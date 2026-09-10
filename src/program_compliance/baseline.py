"""Checkpointed full bounded-registry analysis using the existing local pipeline."""
import json
import re
from collections import Counter
from datetime import datetime, timezone
from .analysis import package, validate, direct_duty, baseline_key
from .determinations import prior_context
from .store import digest, now

FAILURE_CODES = frozenset(('citation_invalid','actor_unsupported','untrusted_instruction',
    'ungrounded_date_in_prose','outside_requested_paragraphs','context_incomplete',
    'local_model_unavailable','local_model_request_timeout','local_model_request_failed',
    'local_model_http_error','local_model_response_incomplete','local_model_queue_wait_timeout',
    'local_model_queue_uncertain','local_model_queue_schema_unverified','local_model_identity_unproven',
    'local_model_context_configuration_invalid','local_model_endpoint_required',
    'local_model_context_contract_unproven','compliance_busy'))


def paragraphs(text):
    """Keep a duty's following list with its lead-in, conditions and exceptions."""
    result = []
    listing = False
    for line in text.splitlines():
        if not line.strip(): continue
        bullet = bool(re.match(r'^\s*(?:[•*-]|\d+[.)]|[a-z][.)])\s+', line))
        if result and (result[-1].rstrip().endswith(':') or (listing and bullet)):
            result[-1] += '\n' + line
            listing = True
        else:
            result.append(line)
            listing = False
    return result


def dependencies(store, section):
    references = sorted(set(re.findall(r'\b(?:Section\s+\d{3,5}|Appendix\s+[IVX]+|\d+\s+TAC\s+(?:Section\s+)?[\d.]+)', section['text'])))
    resolved = {}
    for ref in references:
        label = ref.removeprefix('Section ')
        candidates = {}
        for sid, source in store.items('source'):
            if source.get('test') or source.get('health') != 'Healthy': continue
            for other in store.get('document', sid, {}).get('sections', []):
                if re.match(r'^' + re.escape(label) + r'(?:\b|\s)', other['heading'], re.I):
                    candidates[digest(other)] = other
        if len(candidates) == 1: resolved[ref] = next(iter(candidates.values()))
    return references, resolved


def analyze_source(monitor, source, budget):
    from .service import align
    store = monitor.store
    document = store.get('document', source['id'])
    if source.get('test'): return 0
    if not document or source.get('health') != 'Healthy':
        with store.transaction(): store.put('baseline_source', source['id'], {'state':'blocked','reason':source.get('failure','source_not_retrieved'),'sections':len((document or {}).get('sections',[]))})
        return 0
    used = 0
    heading_counts = Counter()
    live_sections = set()
    states = Counter()
    for section in document['sections']:
        heading_counts[section['heading']] += 1
        key = source['id'] + ':' + digest(section['heading'])[:12]
        if heading_counts[section['heading']] > 1: key += ':' + str(heading_counts[section['heading']])
        live_sections.add(key)
        texts = paragraphs(section['text'])
        blocks = align(store.get('section', key, {'paragraphs':[]})['paragraphs'], texts)
        targets = [i for i, text in enumerate(texts) if direct_duty(text)]
        report = {'source':source['id'],'source_version':source['version'],'heading':section['heading'],
                  'text_version':digest(section['text']),'targets':len(targets),'found':0,'gaps':[],'state':'assessed'}
        with store.transaction(): store.put('section', key, {'heading':section['heading'],'paragraphs':blocks,'version':digest(section['text'])})
        if not targets:
            # Do not silently certify an ambiguous inherited/generic actor duty as irrelevant.
            if re.search(r'\bDSAs?\b|direct services agenc', section['text']+' '+section['heading'], re.I) and re.search(r'\bmust\b|\bshall\b|\brequired\b', section['text'], re.I):
                report.update(state='gap',gaps=['actor_or_inherited_duty_requires_context_review'])
            else: report['state'] = 'context_only'
        else:
            refs, resolved = dependencies(store, section)
            with store.transaction(): store.put('dependencies', key, {'references':refs,'resolved':{r:digest(v) for r,v in resolved.items()}})
            if len(refs) != len(resolved):
                report.update(state='gap',gaps=['referenced_context_unavailable: '+', '.join(r for r in refs if r not in resolved)])
            else:
                profile = {k:v for k,v in monitor.profile().items() if k != 'version'}
                pkg = package(source, section, profile, resolved)
                pkg['paragraphs'] = [{'paragraph':i,'text':text} for i,text in enumerate(texts)]
                pkg['source_version'] = digest(section['text'])
                for start in range(0, len(targets), 3):
                    chunk = {**pkg,'target_paragraphs':targets[start:start+3],'baseline_contract':'all-targets-v1'}
                    context = {}
                    for i in chunk['target_paragraphs']:
                        finding_key = 'requirement:' + key + ':' + blocks[i]['id']
                        old = store.get('requirement_evidence', finding_key, {})
                        prior = prior_context(store, finding_key, old.get('meaning_version'))
                        if prior:
                            prior['compatible_with_current_evidence'] = (prior['support'].get('quote') == texts[i]
                                and prior['support'].get('section_version') == digest(section['text'])
                                and prior['support'].get('profile') == {k:profile[k] for k in prior['support'].get('profile',{})}
                                and prior['support'].get('dependencies') == resolved)
                            context[str(i)] = prior
                    chunk['prior_agency_determinations'] = context
                    request_key = baseline_key(chunk, monitor.model.model)
                    cached = store.get('baseline_analysis', request_key)
                    if cached is None:
                        failure = store.get('baseline_failure', request_key)
                        if failure:
                            report['gaps'].append(failure['category']); continue
                        if store.get('baseline_attempt', request_key):
                            report['gaps'].append('interrupted_analysis_requires_reconciliation'); continue
                        if used >= budget:
                            report['state'] = 'pending'; continue
                        if len(json.dumps(chunk,ensure_ascii=False)) > 14000:
                            with store.transaction(): store.put('baseline_failure', request_key, {'category':'complete_context_exceeds_verified_budget'})
                            report['gaps'].append('complete_context_exceeds_verified_budget'); continue
                        used += 1
                        with store.transaction(): store.put('baseline_attempt', request_key, {'started':now(),'source':source['id'],'section':key})
                        try:
                            raw = monitor.model.analyze_baseline(chunk)
                            with store.transaction():
                                store.put('baseline_candidate', request_key, {'result':raw,
                                    'metrics':monitor.model._last_request_metrics,'source':source['id'],'section':key})
                            obligations = validate(raw, chunk)
                            if any(o['paragraph'] not in chunk['target_paragraphs'] for o in obligations):
                                raise ValueError('outside_requested_paragraphs')
                            missing = sorted(set(chunk['target_paragraphs']) - {o['paragraph'] for o in obligations})
                            cached = {'obligations':obligations,'missing':missing,'metrics':monitor.model._last_request_metrics,
                                      'prior_determinations_digest':digest(context)}
                            with store.transaction(): store.put('baseline_analysis', request_key, cached)
                        except Exception as error:
                            code = str(error)
                            category = code if code in FAILURE_CODES else type(error).__name__
                            with store.transaction(): store.put('baseline_failure', request_key, {'category':category,'source':source['id'],'section':key})
                            report['gaps'].append(category); continue
                    if cached['missing']: report['gaps'].append('model_did_not_resolve_all_target_duties')
                    for obligation in cached['obligations']:
                        i = obligation['paragraph']; finding_key = 'requirement:' + key + ':' + blocks[i]['id']
                        if len(obligation['quote']) > 3500:
                            report['gaps'].append('complete_requirement_exceeds_sheet_excerpt_budget'); continue
                        publish(monitor, source, section, resolved, profile, obligation, finding_key, request_key)
                        report['found'] += 1
        if report['gaps'] and report['state'] != 'pending': report['state'] = 'gap'
        report['gaps'] = sorted(set(report['gaps']))
        with store.transaction(): store.put('baseline_section', key, report)
        states[report['state']] += 1
        # A removed duty or unresolved changed context cannot leave a prior Met
        # report looking current merely because no replacement was publishable.
        for finding_key, item in store.items('finding'):
            if not finding_key.startswith('requirement:' + key + ':'): continue
            evidence = store.get('requirement_evidence', finding_key, {})
            if evidence.get('section_version') != digest(section['text']):
                reassess(store, finding_key, item, digest(section['text']))
    for finding_key, item in store.items('finding'):
        if not finding_key.startswith('requirement:' + source['id'] + ':'): continue
        section_key = finding_key[len('requirement:'):].rsplit(':', 1)[0]
        if section_key not in live_sections:
            reassess(store, finding_key, item, 'removed-section:' + source['version'])
    with store.transaction():
        store.put('baseline_source', source['id'], {'state':'pending' if states['pending'] else ('gap' if states['gap'] else 'assessed'), 'sections':sum(states.values()),'section_states':dict(states)})
        store.put('source_analysis', source['id'], {'pending':bool(states['pending'] or states['gap']),'reason':'See grouped baseline coverage; unresolved sections retain exact gaps.' if states['pending'] or states['gap'] else ''})
    return used


def publish(monitor, source, section, resolved, profile, obligation, key, request_key):
    store = monitor.store
    supporting = {k:profile[k] for k in ('program','role')}
    if obligation['scope'] != 'Agency-wide': supporting.update(contracted_services=profile['contracted_services'],active_services=profile['active_services'])
    meaning = digest({'quote':obligation['quote'],'section':digest(section['text']),'profile':supporting,'dependencies':resolved,'rules':'pcm-applicability-1'})
    previous = store.get('requirement_evidence', key)
    if previous and store.get('finding',key) and all((
        previous.get('quote') == obligation['quote'], previous.get('section_version') == digest(section['text']),
        previous.get('profile') == supporting, previous.get('dependencies') == resolved)):
        revision_key=key+':'+store.get('finding',key)['Current Revision']
        if store.get('requirement_revision',revision_key) is None:
            with store.transaction():store.put('requirement_revision',revision_key,previous)
        return
    # Deduplicate only identical source evidence/context; uncertain cross-source matches stay separate.
    signature = digest({'quote':obligation['quote'],'context':section['text'],'profile':supporting,'dependencies':resolved})
    canonical = store.get('baseline_equivalent', signature)
    if canonical and canonical != key and store.get('finding', canonical):
        with store.transaction(): store.put('requirement_alias', key, {'canonical':canonical,'source':source['id']})
        return
    proposed = 'proposed' in source['url'].lower() or source.get('type') == 'Proposed rule'
    row = monitor.record('Reference' if proposed else ('Actionable Change' if previous else 'Requirement'),
        obligation['topic'], obligation['quote'], 'Review proposal; it is not an effective requirement.' if proposed else obligation['action'],
        **{'Responsible Party/Duty Scope':'DSA / '+obligation['scope'],
           'Source Section/Link':section['heading']+' | '+source['url'],
           'Suggested Applicability/Reason':('Proposed rule; not effective.' if proposed else obligation['applicability']+' — '+obligation['reason'])+' Implementation is not assessed.',
           'Effective Date':None if proposed else obligation['effective'],
           'Source Deadline/Trigger':None if proposed else obligation['deadline'],
           'Evidence / Before and After':(('Before: '+previous['quote']+'\nAfter: ') if previous else 'Evidence: ')+obligation['quote'],
           'Related Findings':'question:agency-services' if obligation['scope']!='Agency-wide' else '',
           'Suggested Owner':monitor.config.get('routing',{}).get(obligation['scope'],''),'Review Needed':True})
    if len(row['Evidence / Before and After'])>3800:
        row['Evidence / Before and After']='Current evidence: '+obligation['quote']+'\nPrevious evidence remains in revision history.'
    with store.transaction():
        if previous and store.get('finding',key):
            store.put('requirement_revision',key+':'+store.get('finding',key)['Current Revision'],previous)
        store.put('requirement_evidence',key,{'quote':obligation['quote'],'meaning_version':meaning,'source_version':source['version'],
            'section_version':digest(section['text']),'profile':supporting,'dependencies':resolved,'request_key':request_key})
        store.publish(key,row,evidence_version=meaning)
        store.put('requirement_revision',key+':'+store.get('finding',key)['Current Revision'],store.get('requirement_evidence',key))
        store.put('baseline_equivalent',signature,key)


def reassess(store, key, item, version):
    if store.get('reassessment',key,{}).get('context_version') == version: return
    with store.transaction():
        support=store.get('requirement_evidence',key)
        if support: store.put('requirement_revision',key+':'+item['Current Revision'],support)
        store.publish(key,{**item,'Record Type':'Actionable Change','Review Needed':True,
            'Proposed Action':'Source duty or supporting context changed or was removed. Reassess against retained prior evidence; current interpretation is pending.'},evidence_version=version)
        if support:
            store.put('requirement_revision',key+':'+store.get('finding',key)['Current Revision'],
                {**support,'pending_context_version':version,'context_unresolved':True})
        store.put('reassessment',key,{'context_version':version})


def health_rows(monitor):
    store=monitor.store
    sources=[s for _,s in store.items('source') if not s.get('test')]
    stale=[s for s in sources if s.get('health')=='Healthy' and s.get('last_success') and
           (datetime.now(timezone.utc)-datetime.fromisoformat(s['last_success'])).total_seconds()>172800]
    failed=[s for s in sources if s.get('health')!='Healthy']+[{**s,'failure':'last_success_is_stale'} for s in stale]
    sections=[v for _,v in store.items('baseline_section')]
    gaps=[v for v in sections if v['state']=='gap'];pending=[v for v in sections if v['state']=='pending']
    source_details='\n'.join(s['url']+' — '+s.get('failure','source_not_retrieved') for s in failed)
    categories=Counter(g.split(':')[0] for section in gaps for g in section['gaps'])
    gap_details='\n'.join(str(count)+' section(s): '+category for category,count in sorted(categories.items()))
    details={'sources':source_details,'analysis':gap_details+'\nFull source/section gap evidence is retained in service state; unresolved agency scope is consolidated under Agency Questions.'}
    rows=[('sources','Source availability',f'{len(sources)-len(failed)} of {len(sources)} sources retrieved successfully; {len(failed)} access/parser gaps.', 'Unavailable' if failed else 'Healthy'),
          ('analysis','Requirement coverage',f'{len(sections)} sections assessed or triaged; {len(gaps)} have explicit context/analysis gaps; {len(pending)} remain pending. These counts do not certify complete legal coverage.','Coverage Gap' if gaps or pending else 'Healthy')]
    with store.transaction():
        for key,topic,summary,health in rows:
            detail=details[key]
            if len(detail)>3700: detail=detail[:3500].rsplit('\n',1)[0]+'\nAdditional source gaps are retained in service state.'
            store.publish('health:baseline:'+key,monitor.record('Source Health',topic,summary,'Review consolidated coverage gaps where agency input or access is required.' if health!='Healthy' else '',**{'Source Health':health,'Review Needed':health!='Healthy','Evidence / Before and After':detail,'Last Successful Check':max((s.get('last_success') or '' for s in sources),default='')}),substantive=False)
