"""Version-bound agency reports; never independent compliance certification."""
from .store import digest, now

STATUSES = ('Not Assessed', 'Met', 'Partially Met', 'Not Met', 'Not Applicable')


def observe(store, key, fields):
    finding = store.get('finding', key, {})
    revision = fields.get('Reviewed Revision')
    status = fields.get('Implementation Status')
    if not revision or status not in STATUSES:
        return
    support = store.get('requirement_revision', key + ':' + revision)
    if support is None and revision == finding.get('Current Revision'):
        support = store.get('requirement_evidence', key)
    if not support:
        return
    store.put('requirement_revision', key + ':' + revision, support)
    value = {'reviewed_revision': revision, 'implementation_status': status,
             'completion_evidence': fields.get('Completion Evidence'),
             'notes': fields.get('Decision Notes'), 'support': support,
             'authority': 'Agency-reported; not independently certified'}
    previous = store.get('determination', key)
    if previous != value:
        if previous: store.event('determination_history', key, previous)
        store.put('determination', key, value)
        store.put('determination_version', key + ':' + digest(value), value)


def presentation(store, key, payload):
    value = dict(payload)
    if not store.get('requirement_evidence', key):
        value['Implementation Assessment'] = ''
        return value
    human = store.get('human', key, {})
    status = human.get('Implementation Status')
    current = human.get('Reviewed Revision') == payload.get('Current Revision')
    if status not in STATUSES or status == 'Not Assessed':
        value['Implementation Assessment'] = 'Not Assessed. Review completion does not establish implementation.'
    elif not current:
        value['Implementation Assessment'] = 'Reassessment required. Prior agency report: ' + status + '; it is not current for this revision.'
        value['Proposed Action'] = 'Reassess the changed requirement against prior agency-reported implementation and evidence. ' + (payload.get('Proposed Action') or '')
    else:
        value['Implementation Assessment'] = 'Agency-reported ' + status + ' for this reviewed revision; not independently certified.'
        if status == 'Met':
            value['Proposed Action'] = 'Agency reports this revision met. Retain the supporting evidence; no repeat implementation work is proposed without a relevant change.'
        elif status == 'Partially Met':
            value['Proposed Action'] = 'Agency reports this revision partially met. Review remaining gaps against the recorded completion evidence and notes; preserve work already reported complete.'
        elif status == 'Not Applicable':
            value['Proposed Action'] = 'Agency reports this revision not applicable. Retain the rationale and reassess if relevant source or agency facts change.'
    return value


def prior_context(store, key, meaning_version):
    previous = store.get('determination', key)
    if not previous: return None
    return {**previous, 'compatible_with_current_evidence': previous['support'].get('meaning_version') == meaning_version,
            'use': 'Prior agency report only. Changed evidence requires human reassessment; do not carry a prior Met status forward as current.'}
