"""Minimal persistent context and source-delta detection, not automatic memory writeback."""
from __future__ import annotations
from datetime import date
from pathlib import Path
import re
import unicodedata
from .common import digest, safe_path

TASK_FILES = {
    'insights': ['reviews.csv', 'competitors.csv'],
    'content': [], 'campaign': ['campaign.csv'],
    'edm': [], 'edm-series': [], 'influencer': ['creators.csv'], 'launch': [],
}

def snapshot(root: Path, project: dict, task: str) -> dict:
    if task not in TASK_FILES:
        raise ValueError('Unknown task')
    files = {'project.json', *TASK_FILES[task]}
    # Include product evidence and this task's files, not all registered datasets.
    core_ids = {f.get('source_id') for f in project.get('facts', [])}
    core_ids.update(c.get('source_id') for c in project.get('claims', []))
    core_ids.update(s for c in project.get('candidate_context', []) for s in c.get('source_ids', []))
    if task == 'edm-series':
        series = project.get('edm_series', {})
        used = {m for email in series.get('emails', []) for m in email['module_ids']}
        for module in series.get('modules', []):
            if module['id'] not in used:
                continue
            core_ids.add(module.get('inheritance', {}).get('source_id'))
            if module.get('asset_path'):
                files.add(module['asset_path'])
        files.update(v['path'] for v in series.get('visuals', []) if v.get('path'))
    files.update(s['path'] for s in project.get('sources', []) if s['id'] in core_ids)
    if task in {'content', 'launch'}:
        files.update(u['asset_path'] for u in project.get('page_units', []) if u.get('asset_path'))
    return {name: digest(safe_path(root, name)) for name in sorted(files) if safe_path(root, name).is_file()}

def delta(previous: dict | None, current: dict) -> dict:
    old = previous or {}
    return {
        'new': sorted(k for k in current if k not in old),
        'changed': sorted(k for k in current if k in old and current[k] != old[k]),
        'removed': sorted(k for k in old if k not in current),
        'automatic_truth_writeback': False,
    }

def resolve(project: dict, task: str, as_of: date) -> dict:
    state = project.get('state', {})
    raw = state.get('state_as_of')
    freshness = 'unknown'
    if raw:
        elapsed = (as_of - date.fromisoformat(raw)).days
        freshness = 'unknown' if elapsed < 0 else 'current' if elapsed <= state.get('freshness_days', 30) else 'stale'
    blockers = state.get('blockers', [])
    aliases = {'edm'} if task == 'edm-series' else {'content', 'edm'} if task == 'launch' else set()
    scoped = [b for b in blockers if isinstance(b, str) or (b.get('status', 'open') != 'resolved' and
              (not b.get('tasks') or task in b['tasks'] or set(b['tasks']) & aliases))]
    active_ids = {b['id'] for b in blockers if isinstance(b, dict) and b.get('status', 'open') != 'resolved'}
    actions = []
    for action in state.get('next_actions', []):
        if action.get('tasks') and task not in action['tasks'] and not set(action['tasks']) & aliases:
            continue
        safe = action.get('kind') in {'audit', 'source_refresh', 'review_preparation'}
        reasons = []
        if action.get('requires_human_approval'):
            reasons.append('HUMAN_APPROVAL_REQUIRED')
        if active_ids.intersection(action.get('blocked_by', [])):
            reasons.append('DEPENDENCY_BLOCKED')
        if freshness != 'current' and not safe:
            reasons.append('PROJECT_STATE_UNVERIFIED')
        if action.get('kind') == 'execution':
            reasons.append('EXECUTION_NOT_BUNDLED')
        actions.append(dict(action, executable=not reasons, blocking_reasons=reasons))
    actions.sort(key=lambda a: ({'p0': 0, 'p1': 1, 'p2': 2}.get(a.get('priority'), 2), a['id']))
    valid = [a for a in actions if a['executable']]
    fallback = 'Review available evidence and prepare human review; do not execute unverified project state.'
    next_action = valid[0]['text'] if valid else fallback
    if not actions and freshness == 'current':
        next_action = state.get('next_action') or fallback
    return {
        'project_id': project['project_id'], 'task': task, 'synthetic': project['synthetic'],
        'state_as_of': raw, 'evaluated_at': as_of.isoformat(), 'effective_freshness': freshness,
        'blockers': scoped,
        'next_action': next_action, 'next_actions': actions,
        'legacy_next_action': state.get('next_action'),
        'required_reads': ['project.json', *TASK_FILES[task]],
        'allowed_mode': 'LOCAL_REVIEW_ONLY', 'automatic_publish': False,
    }


def identity(value: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value).strip()).casefold()


def find_project(root: Path, name: str) -> Path:
    """Exact alias only: no substring, fuzzy merge, or implicit project creation."""
    from .common import load_json
    hits = []
    if root.is_symlink():
        raise ValueError('Unsafe projects root')
    for file in sorted(root.glob('*/project.json')):
        if file.parent.is_symlink() or file.is_symlink():
            raise ValueError('Unsafe project path')
        data = load_json(file)
        names = [data.get('project_id', ''), *data.get('aliases', [])]
        if identity(name) in {identity(n) for n in names if isinstance(n, str)}:
            hits.append(file.parent)
    if len(hits) > 1:
        raise ValueError('PROJECT_ALIAS_AMBIGUOUS')
    if not hits:
        raise ValueError('PROJECT_BOOTSTRAP_REQUIRED: no project created')
    return hits[0]
