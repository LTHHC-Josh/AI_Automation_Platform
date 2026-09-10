"""Stable organizational topics; groups never represent assessed obligations."""
import re
from .store import digest

TOPICS = (
    ('Billing, Claims, and EVV', r'\bEVV\b|billing|claim|reimburse|payment'),
    ('Staff Qualifications and Training', r'staff|employee|training|qualification|background check'),
    ('Health, Safety, and Incident Reporting', r'incident|abuse|neglect|exploit|emergency|health and safety'),
    ('Participant Rights and Safeguards', r'rights|confidential|complaint|grievance|consent'),
    ('Transition, Transfer, and Termination', r'transfer|terminat|discharg|suspension|suspend'),
    ('Records and Documentation', r'document|record|retain|retention'),
    ('Service Planning and Authorization', r'service plan|\bIPC\b|\bIP\b|authoriz|planning|assessment'),
    ('Monitoring and Quality Assurance', r'monitor|quality|audit|corrective'),
    ('Service Delivery and Coordination', r'service|case manager|coordinate|CMA'),
)


def choose(payload):
    kind = payload.get('Record Type')
    if kind == 'Question': return 'Agency Questions'
    if kind in ('Source Health','Coverage','Reference'): return 'Source Health and Coverage'
    if kind == 'Control': return 'Monitoring Controls'
    text = (payload.get('Topic') or '') + ' ' + (payload.get('Requirement/Change Summary') or '')
    return next((title for title, pattern in TOPICS if re.search(pattern,text,re.I)), 'Agency Administration and Provider Responsibilities')


def assign(store, key, title):
    value = {'topic':title,'group_key':'group:'+digest(title)[:16]}
    old = store.get('topic_assignment',key)
    if old != value:
        if old: store.event('topic_assignment_history',key,old)
        store.put('topic_assignment',key,value)
    return value


def prepare(store):
    with store.transaction():
        for key,payload in store.items('finding'):
            if payload.get('Record Type') == 'Group' or payload.get('Record Type','').startswith('TEST'): continue
            assignment = store.get('topic_assignment',key) or assign(store,key,choose(payload))
            store.publish(assignment['group_key'],{'Record Type':'Group','Topic':assignment['topic'],
                'Program':payload.get('Program','CLASS'),'Review Needed':False},substantive=False)
    # Never delete old groups: a parent may contain retained or human-created rows.
    return sorted(store.items('finding'), key=lambda kv:(kv[1].get('Record Type')!='Group',kv[0]))
