"""Product/claim validation. Structural validity never grants approval."""
from __future__ import annotations
from datetime import date
from pathlib import Path
from .common import load_json, safe_path, safe_id

STATES = {'confirmed', 'pending', 'conflict', 'unknown'}
CLAIM_STATES = {'approved', 'draft', 'conditional', 'prohibited', 'demo_only'}

def load_project(root: Path) -> dict:
    data = load_json(safe_path(root, 'project.json'))
    if not isinstance(data, dict) or data.get('schema_version') != '1.0':
        raise ValueError('project.json schema_version must be 1.0')
    safe_id(data.get('project_id'))
    if not isinstance(data.get('synthetic'), bool):
        raise ValueError('synthetic must be explicitly true or false')
    if not data.get('brand', {}).get('name') or not data.get('product', {}).get('name'):
        raise ValueError('Brand and product names are required')
    sources = data.get('sources', [])
    if not isinstance(sources, list):
        raise ValueError('sources must be an array')
    source_ids = set()
    for src in sources:
        sid = src.get('id')
        if not isinstance(sid, str) or not sid or sid in source_ids:
            raise ValueError('Missing or duplicate source ID')
        source_ids.add(sid)
        file = safe_path(root, src.get('path', ''))
        if not file.is_file():
            raise ValueError('Registered source file is missing: ' + sid)
        if not data['synthetic'] and src.get('kind') == 'synthetic':
            raise ValueError('Synthetic sources cannot support a real project')
    fact_ids = set()
    for fact in data.get('facts', []):
        if not fact.get('id') or fact['id'] in fact_ids:
            raise ValueError('Missing or duplicate fact ID')
        fact_ids.add(fact['id'])
        if fact.get('status') not in STATES:
            raise ValueError('Invalid fact status')
        if fact.get('status') == 'confirmed' and (fact.get('value') is None or fact.get('source_id') not in source_ids or not fact.get('evidence_location')):
            raise ValueError('Confirmed facts require a value and traceable evidence')
    claim_ids = set()
    facts = {f['id']: f for f in data.get('facts', [])}
    for claim in data.get('claims', []):
        if not claim.get('id') or claim['id'] in claim_ids:
            raise ValueError('Missing or duplicate claim ID')
        claim_ids.add(claim['id'])
        if claim.get('status') not in CLAIM_STATES:
            raise ValueError('Invalid claim status')
        ids = claim.get('fact_ids', [])
        if not isinstance(ids, list) or any(x not in fact_ids for x in ids):
            raise ValueError('Claim references unknown facts')
        if claim['status'] in {'approved', 'conditional'}:
            if not ids or any(facts[x]['status'] != 'confirmed' for x in ids):
                raise ValueError('Approved claims require confirmed facts')
            if claim.get('source_id') not in source_ids or not claim.get('approval_ref'):
                raise ValueError('Approved claims require evidence and approval_ref')
            if claim['status'] == 'conditional' and not claim.get('conditions'):
                raise ValueError('Conditional claims require visible conditions')
        if not data['synthetic'] and claim['status'] == 'demo_only':
            raise ValueError('DEMO claim in a real project')
    ids = set()
    for unit in data.get('page_units', []):
        if not unit.get('id') or unit['id'] in ids:
            raise ValueError('Missing or duplicate page unit ID')
        ids.add(unit['id'])
        if unit.get('section') not in {'gallery', 'aplus', 'brand', 'comparison', 'faq'}:
            raise ValueError('Unknown page section')
        if any(x not in claim_ids for x in unit.get('claim_ids', [])):
            raise ValueError('Page unit references unknown claim')
    for owner in [*data.get('page_units', []), data.get('edm', {})]:
        if any(cid not in claim_ids for cid in owner.get('claim_ids', [])):
            raise ValueError('Content references unknown claim')
        mapping = owner.get('field_claim_ids', {})
        if not isinstance(mapping, dict) or any(not isinstance(v, list) or any(c not in claim_ids for c in v) for v in mapping.values()):
            raise ValueError('Invalid per-field claim binding')
        if any(v not in {'factual', 'non_factual'} for v in owner.get('copy_kinds', {}).values()):
            raise ValueError('Unknown copy classification')
    aliases = data.get('aliases', [])
    if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
        raise ValueError('aliases must contain nonempty routing names')
    if not isinstance(data.get('reviews', []), list):
        raise ValueError('reviews must be an array of explicit human receipts')
    if any(not isinstance(r, dict) for r in data.get('reviews', [])):
        raise ValueError('Invalid human receipt')
    for candidate in data.get('candidate_context', []):
        if candidate.get('information_type') not in {'FACT', 'HYPOTHESIS', 'RECOMMENDATION', 'GAP'}:
            raise ValueError('Invalid candidate information_type')
        if candidate.get('status', 'unverified') not in {'unverified', 'pending', 'conflict'}:
            raise ValueError('Intake cannot approve current truth')
        if any(s not in source_ids for s in candidate.get('source_ids', [])):
            raise ValueError('Candidate references unknown source')
    state = data.get('state', {})
    days = state.get('freshness_days', 30)
    if type(days) is not int or days < 0:
        raise ValueError('freshness_days must be a nonnegative integer')
    if state.get('state_as_of'):
        date.fromisoformat(state['state_as_of'])
    blockers = state.get('blockers', [])
    bids = [b.get('id') for b in blockers if isinstance(b, dict)]
    if len(bids) != len(set(bids)) or any(not b for b in bids):
        raise ValueError('Blocker IDs must be unique')
    actions = state.get('next_actions', [])
    aids = [a.get('id') for a in actions]
    if len(aids) != len(set(aids)) or any(not a for a in aids):
        raise ValueError('Action IDs must be unique')
    for a in actions:
        if a.get('kind') not in {'audit', 'source_refresh', 'review_preparation', 'execution'} or a.get('priority') not in {'p0', 'p1', 'p2'} or not a.get('text'):
            raise ValueError('Action requires text, priority and an explicit safety kind')
        if any(b not in bids for b in a.get('blocked_by', [])):
            raise ValueError('Action references unknown blocker')
    if 'edm_series' in data:
        from .email_series import validate_series
        validate_series(data)
    return data

def claim_usable(claim: dict, project: dict, as_of: date) -> bool:
    demo = project['synthetic'] and claim.get('status') == 'demo_only'
    if not demo and claim.get('status') not in {'approved', 'conditional'}:
        return False
    facts = {f['id']: f for f in project.get('facts', [])}
    ids = claim.get('fact_ids', [])
    if not ids or any(f not in facts or facts[f].get('status') != 'confirmed' for f in ids):
        return False
    sources = {s['id']: s for s in project.get('sources', [])}
    for sid in {claim.get('source_id'), *[facts[f].get('source_id') for f in ids]}:
        src = sources.get(sid)
        if not src or src.get('status') in {'conflict', 'outdated', 'retracted', 'unverified', 'unknown', 'draft'}:
            return False
        if src.get('valid_to') and as_of > date.fromisoformat(src['valid_to']):
            return False
        if src.get('valid_from') and as_of < date.fromisoformat(src['valid_from']):
            return False
    for key, predicate in [('valid_from', lambda d: as_of < d), ('valid_to', lambda d: as_of > d)]:
        if claim.get(key) and predicate(date.fromisoformat(claim[key])):
            return False
    return claim.get('market', project.get('market')) == project.get('market')

def truth_report(project: dict, as_of: date) -> dict:
    return {
        'project_id': project['project_id'], 'synthetic': project['synthetic'],
        'structural_validation': 'PASS',
        'confirmed_fact_ids': [f['id'] for f in project.get('facts', []) if f['status'] == 'confirmed'],
        'unresolved_fact_ids': [f['id'] for f in project.get('facts', []) if f['status'] != 'confirmed'],
        'conflict_fact_ids': [f['id'] for f in project.get('facts', []) if f['status'] == 'conflict'],
        'candidate_context': project.get('candidate_context', []),
        'usable_claim_ids': [c['id'] for c in project.get('claims', []) if claim_usable(c, project, as_of)],
        'blocked_claim_ids': [c['id'] for c in project.get('claims', []) if not claim_usable(c, project, as_of)],
        'publication_ready': False,
        'warning': 'Traceability is checked, not the truth of the source; human review is still required.'
    }
