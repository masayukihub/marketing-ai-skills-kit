"""Exact, scoped INTERNAL review. Receipts never grant product/claim/publication approval."""
from __future__ import annotations
from datetime import date
import hashlib
import json
from pathlib import Path
from .common import digest, safe_path
from .truth import claim_usable


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def dependencies(root: Path | None, project: dict, claim_ids: list) -> dict:
    claims = {c['id']: c for c in project.get('claims', [])}
    selected = [claims[c] for c in sorted(set(claim_ids)) if c in claims]
    fact_ids = {f for c in selected for f in c.get('fact_ids', [])}
    facts = sorted([f for f in project.get('facts', []) if f['id'] in fact_ids], key=lambda f:f['id'])
    source_ids = {c.get('source_id') for c in selected} | {f.get('source_id') for f in facts}
    sources = []
    for s in project.get('sources', []):
        if s['id'] in source_ids:
            file = safe_path(root, s['path']) if root else None
            sources.append(dict(s, file_sha256=digest(file) if file and file.is_file() else None))
    return {'claims': selected, 'facts': facts, 'sources': sorted(sources,key=lambda s:s['id'])}


def reviewed_state(project: dict, item_id: str, hashed: str, blockers: list, as_of: date, verifiable: bool) -> str:
    records = [r for r in project.get('reviews', []) if r.get('item_id') == item_id]
    if not records:
        return 'CANDIDATE'
    receipt = records[-1]
    if receipt.get('project_id') != project['project_id'] or receipt.get('fingerprint') != hashed:
        return 'STALE_REVIEW'
    try:
        reviewed = date.fromisoformat(receipt.get('reviewed_at', ''))
    except (TypeError, ValueError):
        return 'INVALID_REVIEW'
    if not str(receipt.get('reviewer', '')).strip() or reviewed > as_of:
        return 'INVALID_REVIEW'
    decision = receipt.get('decision')
    if decision == 'APPROVE':
        if blockers or not verifiable or receipt.get('evidence_checked') is not True:
            return 'APPROVAL_BLOCKED'
        return 'APPROVED_INTERNAL_ONLY'
    return {'REJECT': 'REJECTED', 'NEED_MORE_EVIDENCE': 'NEED_MORE_EVIDENCE',
            'KEEP_AS_HYPOTHESIS': 'HYPOTHESIS'}.get(decision, 'INVALID_REVIEW')


def copy_item(root: Path | None, project: dict, owner: dict, prefix: str, field: str, claim_ids: list, as_of: date) -> dict:
    ids = owner.get('field_claim_ids', {}).get(field, claim_ids)
    dep = dependencies(root, project, ids)
    known = {c['id']: c for c in project.get('claims', [])}
    missing = [c for c in ids if c not in known or not claim_usable(known[c], project, as_of)]
    blockers = ['CLAIMS_NOT_USABLE'] if missing else []
    value = owner.get(field)
    if not value:
        blockers.append('COPY_MISSING')
    non_factual = owner.get('copy_kinds', {}).get(field) == 'non_factual'
    if not ids and not non_factual:
        blockers.append('EVIDENCE_BINDING_MISSING')
    item_id = prefix + ':' + field
    hashed = fingerprint({'project_id': project['project_id'], 'synthetic': project['synthetic'],
                          'brand': project['brand'], 'product': project['product'], 'market': project['market'],
                          'item_id': item_id, 'value': value, 'non_factual': non_factual, 'dependencies': dep})
    return {'item_id': item_id, 'category': 'copy', 'scope': prefix, 'field': field, 'value': value,
            'claim_ids': ids, 'source_ids': [s['id'] for s in dep['sources']],
            'fingerprint': hashed, 'blockers': blockers,
            'status': reviewed_state(project, item_id, hashed, blockers, as_of, root is not None),
            'semantic_review': 'HUMAN_REQUIRED', 'external_claim_approval': False}


def unit_items(root: Path, project: dict, unit: dict, as_of: date) -> list:
    prefix = 'content:' + unit['id']
    copies = [copy_item(root, project, unit, prefix, f, unit.get('claim_ids', []), as_of) for f in ('headline', 'support')]
    asset = unit.get('asset_path')
    path = safe_path(root, asset) if asset else None
    exists = bool(path and path.is_file())
    blockers = []
    if not exists:
        blockers.append('ASSET_MISSING')
    if unit.get('asset_rights') != 'user_confirmed':
        blockers.append('ASSET_RIGHTS_UNVERIFIED')
    if any(c['blockers'] for c in copies):
        blockers.append('COPY_EVIDENCE_UNRESOLVED')
    item_id = prefix + ':asset'
    hashed = fingerprint({'project_id': project['project_id'], 'item_id': item_id,
                          'file_sha256': digest(path) if exists else None, 'rights': unit.get('asset_rights'),
                          'proof': unit.get('visual_proof'), 'copy_fingerprints': [c['fingerprint'] for c in copies]})
    return copies + [{'item_id': item_id, 'category': 'asset', 'scope': prefix, 'field': 'asset', 'value': asset,
                      'fingerprint': hashed, 'source_ids': [], 'blockers': blockers,
                      'status': reviewed_state(project, item_id, hashed, blockers, as_of, True),
                      'semantic_review': 'HUMAN_REQUIRED', 'external_claim_approval': False}]


def email_items(root: Path | None, project: dict, as_of: date) -> list:
    edm = project.get('edm', {})
    ids = edm.get('claim_ids', [c['id'] for c in project.get('claims', [])])
    return [copy_item(root, project, edm, 'edm', field, ids, as_of)
            for field in ('subject', 'preheader', 'headline', 'body', 'cta_label', 'cta_url')]
