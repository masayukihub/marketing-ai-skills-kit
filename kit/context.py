"""Minimal persistent context and source-delta detection, not automatic memory writeback."""
from __future__ import annotations
from datetime import date
from pathlib import Path
from .common import digest, safe_path

TASK_FILES = {
    'insights': ['reviews.csv', 'competitors.csv'],
    'content': [], 'campaign': ['campaign.csv'],
    'edm': [], 'influencer': ['creators.csv'],
}

def snapshot(root: Path, project: dict, task: str) -> dict:
    if task not in TASK_FILES:
        raise ValueError('Unknown task')
    files = {'project.json', *TASK_FILES[task]}
    # Include product evidence and this task's files, not all registered datasets.
    core_ids = {f.get('source_id') for f in project.get('facts', [])}
    core_ids.update(c.get('source_id') for c in project.get('claims', []))
    files.update(s['path'] for s in project.get('sources', []) if s['id'] in core_ids)
    if task == 'content':
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
    return {
        'project_id': project['project_id'], 'task': task, 'synthetic': project['synthetic'],
        'state_as_of': raw, 'evaluated_at': as_of.isoformat(), 'effective_freshness': freshness,
        'blockers': state.get('blockers', []),
        'next_action': state.get('next_action') or 'Review available evidence; do not fabricate missing data.',
        'required_reads': ['project.json', *TASK_FILES[task]],
        'allowed_mode': 'LOCAL_REVIEW_ONLY', 'automatic_publish': False,
    }
