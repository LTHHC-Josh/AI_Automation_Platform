"""Source-grounded agency responsibility projection, independent of applicability."""
import re
from .store import digest

VERSION='provider-dsa-1'
DSA=r'(?:DSAs?|direct services? agenc(?:y|ies))'
OTHER=r'(?:CMAs?|case management agenc(?:y|ies)|HHSC|Texas Health and Human Services(?: Commission)?|program managers?|clients?|members?|individuals?)'
PROVIDER=r'providers?'
ACTOR=rf'(?:{DSA}|{OTHER}|{PROVIDER})'
MODAL=r'(?:must|shall|will|(?:is|are) (?:required|responsible)|may not|cannot|agrees? to|need not)'
SUBJECT=re.compile(rf'\b(?P<actor>{ACTOR})(?:\s*\([^)]{{1,100}}\))?(?: provider)?(?P<joint>(?:\s+(?:and|or)\s+(?:the\s+)?{ACTOR})*)\s+(?P<modal>{MODAL})\b',re.I)
DEFINITION=re.compile(rf'\bproviders?\b\s*(?:means|refers to|is defined as|is the term for|[:—–])\s+([^\n.]{{1,500}})',re.I)


def definitions(context):
    """A DSA being a provider does not establish that every provider is a DSA."""
    evidence=[m.group(0) for m in DEFINITION.finditer(context)]
    roles=set()
    for value in evidence:
        rhs=DEFINITION.search(value).group(1)
        if re.search(rf'\b{DSA}\b',rhs,re.I):roles.add('ours')
        if re.search(rf'\b{OTHER}\b',rhs,re.I):roles.add('other')
        if not re.search(rf'\b(?:{DSA}|{OTHER})\b',rhs,re.I):roles.add('ambiguous')
    return {'provider':next(iter(roles)) if len(roles)==1 else 'ambiguous','evidence':evidence}


def definition_context(document):
    return '\n'.join(m.group(0) for s in document.get('sections',[]) for m in DEFINITION.finditer(s['text']))


def assess(text,context=''):
    alias=definitions(context)
    ours=[];other=[];ambiguous=[];qualifiers=[]
    # Split independent sentences/explicitly coordinated actor clauses only.
    pieces=re.split(rf'(?<=[.!?])\s+(?=[A-Z])|;\s*(?=(?:the\s+)?{ACTOR}\b)|,\s*and\s+(?=(?:the\s+)?{ACTOR}\b)',text)
    for piece in pieces:
        matches=list(SUBJECT.finditer(piece))
        if not matches:
            if re.search(r'\b(?:unless|except|does not apply|only if|provided that|this requirement|however)\b',piece,re.I):qualifiers.append(piece)
            elif re.search(rf'\b{MODAL}\b',piece,re.I):ambiguous.append(piece)
            continue
        roles=[]
        for match in matches:
            actors=[match['actor']]+re.findall(ACTOR,match['joint'],re.I)
            roles.extend('ours' if re.fullmatch(DSA,a,re.I) else alias['provider'] if re.fullmatch(PROVIDER,a,re.I) else 'other' for a in actors)
        prefix=piece[:matches[0].start()]
        if re.search(r'\bwhether\b|\bdetermine if\b|\bexample\b',prefix,re.I) or re.fullmatch(r'\s*if\s+(?:the\s+|a\s+)?',prefix,re.I):
            ambiguous.append(piece);continue
        if len(matches)>1 and len(set(roles))>1:
            ambiguous.append(piece);continue
        if 'ambiguous' in roles and 'ours' not in roles:
            ambiguous.append(piece);continue
        if 'ours' in roles:
            match=matches[0]
            if match['joint']:
                if re.search(r'\bor\b',match['joint'],re.I):ambiguous.append(piece);continue
                if 'ambiguous' in roles:ambiguous.append(piece)
                # Explicit joint duty: the predicate belongs to our agency too.
                condition=prefix if re.search(r'\b(?:if|when|unless|before|after)\b',prefix,re.I) else ''
                ours.append(condition+'Provider/DSA '+piece[match.start('modal'):])
            else:ours.append(piece)
        else:other.append(piece)
    status='ours' if ours else 'ambiguous' if ambiguous else 'other' if other else 'context'
    duty=text if ours and not other and not ambiguous and not any(m['joint'] for m in SUBJECT.finditer(text)) else '\n'.join(ours+qualifiers) if ours else ''
    provider_subject=any(re.fullmatch(PROVIDER,m['actor'],re.I) or re.search(r'\bproviders?\b',m['joint'],re.I) for m in SUBJECT.finditer(text))
    return {'version':VERSION,'status':status,'duty':duty,'other_context':other,'provider_subject':provider_subject,
        'ambiguous_context':ambiguous,'provider_definition':alias,'source_excerpt':text}


def reconcile(store):
    """Preserve row identity/human cells; withdraw non-agency requirement attribution."""
    counts={'ours':0,'other':0,'ambiguous':0,'context':0,'changed':0}
    sources=dict(store.items('source'))
    with store.transaction():
        for key,row in store.items('finding'):
            evidence=store.get('requirement_evidence',key)
            if not evidence or row.get('Record Type','').startswith('TEST'):continue
            source_id=next((sid for sid in sources if key.startswith('requirement:'+sid+':')),None)
            if not source_id:continue
            doc=store.get('document',source_id,{})
            context=definition_context(doc)
            result=assess(evidence['quote'],context)
            counts[result['status']]+=1
            previous=store.get('actor_assessment',key)
            store.put('actor_assessment',key,{**result,'source_version':sources[source_id].get('version')})
            target=dict(row)
            if result['status']=='ours':
                target['Requirement/Change Summary']=result['duty']
                if result['duty']!=evidence['quote']:
                    from .analysis import duty_scope
                    scope=duty_scope(result['duty'])
                    target['Responsible Party/Duty Scope']='DSA / '+scope
                    target['Suggested Applicability/Reason']='Provider/DSA responsibility is source-supported. '+('Agency-wide duty.' if scope=='Agency-wide' else 'Contracted/active service applicability needs separate confirmation.')+' Implementation is reported separately.'
                    target['Proposed Action']='Review our Provider/DSA duty and existing agency process. Other parties are supporting context, not assigned agency work.'
                    target['Evidence / Before and After']='Source evidence, including other actors as context:\n'+evidence['quote']
                    target['Source Deadline/Trigger']=result['duty'] if re.search(r'\b(within|before|after|no later than|annually|days|hours)\b',result['duty'],re.I) else None
                if row.get('Record Type') in ('Question','Reference') and previous and previous['status']!='ours':
                    target['Record Type']='Actionable Change'
                    target['Responsible Party/Duty Scope']='Provider/DSA / Service applicability remains separate'
            elif result['status']=='ambiguous':
                target.update({'Record Type':'Question','Topic':'Confirm responsible actor',
                    'Requirement/Change Summary':'Confirm from the cited source definitions whether this duty belongs to our Provider/DSA. It is not currently attributed to our agency.',
                    'Responsible Party/Duty Scope':'Actor assignment needs confirmation',
                    'Proposed Action':'Identify the source-supported actor definition and record the evidence in Decision Notes. Agency service scope and implementation status do not resolve this actor question.',
                    'Evidence / Before and After':'Actor context needing confirmation:\n'+evidence['quote']})
            else:
                target.update({'Record Type':'Reference','Topic':'Responsibility attribution withdrawn',
                    'Requirement/Change Summary':'This is not an established Provider/DSA requirement. Other-party evidence is retained in service history and relevant dependencies.',
                    'Responsible Party/Duty Scope':'Other party / context only','Proposed Action':'',
                    'Evidence / Before and After':'Prior source evidence and human history are retained; this row is not an agency requirement.'})
            if result['status']!='ours':
                target.update({'Effective Date':None,'Source Deadline/Trigger':None,
                    'Suggested Applicability/Reason':'Responsibility filtering is separate from agency service applicability and implementation.','Related Findings':''})
            definition_changed=bool(previous and result['provider_subject'] and previous['provider_definition']!=result['provider_definition'])
            if definition_changed or any(target.get(k)!=row.get(k) for k in target):
                revision=row['Current Revision']
                if store.get('requirement_revision',key+':'+revision) is None:store.put('requirement_revision',key+':'+revision,evidence)
                store.publish(key,target,evidence_version=digest({'support':evidence['meaning_version'],'actor':result}))
                store.put('requirement_revision',key+':'+store.get('finding',key)['Current Revision'],{**evidence,'responsibility':result})
                # Move the same row into the appropriate organizational group.
                from .topics import assign,choose
                assign(store,key,choose(target));counts['changed']+=1
            else:
                revision_key=key+':'+row['Current Revision']
                binding=store.get('requirement_revision',revision_key,evidence)
                if 'responsibility' not in binding:store.put('requirement_revision',revision_key,{**binding,'responsibility':result})
        questions={}
        for section_key,record in store.items('source_actor_context'):
            source_id=next((sid for sid in sources if section_key.startswith(sid+':')),None)
            if not source_id:continue
            if any(r['status']=='ambiguous' and re.search(rf'\b(?:{DSA}|{PROVIDER})\b',r['source_excerpt'],re.I) for r in record['paragraphs']):
                questions.setdefault(source_id,[]).append(store.get('section',section_key,{}).get('heading','Source section'))
        families={}
        for source_id,headings in questions.items():
            root=source_id;seen=set()
            while root not in seen and sources[root].get('parent') in sources:
                seen.add(root);root=sources[root]['parent']
            families.setdefault(root,[]).append((source_id,headings))
        for root,entries in families.items():
            details=[]
            for source_id,headings in entries:
                line=sources[source_id]['url']+' | '+', '.join(sorted(set(headings)))
                if len('\n'.join(details+[line]))>3300:
                    details.append('Additional source-specific context is retained in the coverage registry.');break
                details.append(line)
            store.publish('question:actor-family:'+root,{'Record Type':'Question','Program':'CLASS','Topic':'Confirm Provider/DSA source definitions',
                'Requirement/Change Summary':'Actor confirmation is needed across '+str(len(entries))+' related source(s). Resolve each duty from its own definitions and context; no common Provider alias is assumed.',
                'Source Section/Link':sources[root]['url'],
                'Proposed Action':'Record source-specific actor definitions/citations in Decision Notes. Do not infer DSA responsibility from generic Provider wording, agency services, or a definition from a different source.',
                'Responsible Party/Duty Scope':'Actor assignments need source-specific confirmation',
                'Evidence / Before and After':'Source-specific confirmation contexts:\n'+'\n'.join(details),'Review Needed':True})
        for key,row in store.items('finding'):
            # Consolidate only never-published implementation-stage questions.
            if key.startswith('question:actor:') and not store.get('row_binding',key) and not store.get('human',key):
                store.put('actor_question_history',key,row)
                store.db.execute('DELETE FROM records WHERE kind="finding" AND key=?',(key,))
                store.db.execute('DELETE FROM outbox WHERE key=?',(key,))
            elif key.startswith('question:actor-family:') and key.removeprefix('question:actor-family:') not in families and row.get('Record Type')=='Question':
                store.publish(key,{**row,'Record Type':'Reference','Requirement/Change Summary':'Current retained source evidence no longer leaves this actor assignment unresolved. Prior human notes remain preserved.','Proposed Action':''})
        store.put('runtime','responsibility_reconciliation',counts)
    return counts


def prior_compatible(support,result):
    if result['status']!='ours':return False
    prior=support.get('responsibility')
    if not prior:return not result['provider_subject'] and result['duty']==result['source_excerpt']
    return prior['status']=='ours' and prior['duty']==result['duty'] and (not result['provider_subject'] or prior['provider_definition']==result['provider_definition'])
