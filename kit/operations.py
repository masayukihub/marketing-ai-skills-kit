"""Deterministic campaign metrics and evidence-based creator shortlist."""
from __future__ import annotations
from statistics import median
from .common import number, ratio

METRICS = ['spend', 'impressions', 'clicks', 'orders', 'revenue']

def campaign_report(data: list[dict], project: dict) -> dict:
    sources = {s['id'] for s in project['sources']}
    if not data: return {'status': 'NO_DATA', 'channels': [], 'total': None}
    dims = ('currency', 'tax_basis', 'attribution_window', 'period')
    for dim in dims:
        values = {r.get(dim, '') for r in data}
        if '' in values or len(values) != 1:
            raise ValueError('Incompatible or missing campaign dimension: ' + dim)
    def metrics(record):
        return {**record, 'CTR': ratio(record['clicks'], record['impressions']),
                'CVR': ratio(record['orders'], record['clicks']),
                'CPA': ratio(record['spend'], record['orders']), 'ROAS': ratio(record['revenue'], record['spend'])}
    channels = []; row_ids = set()
    for r in data:
        if r.get('source_id') not in sources or not r.get('row_id') or r['row_id'] in row_ids:
            raise ValueError('Campaign row lacks evidence or has duplicate ID')
        row_ids.add(r['row_id'])
        values = {f: number(r.get(f)) for f in METRICS}
        channels.append({'channel': r.get('channel', 'unknown'), 'row_id': r['row_id'], **metrics(values)})
    total = {f: sum(c[f] for c in channels) if all(c[f] is not None for c in channels) else None for f in METRICS}
    return {'synthetic': project['synthetic'], **{d: data[0][d] for d in dims}, 'channels': channels,
            'total': metrics(total), 'method': 'ratios_of_sums_not_mean_ratios', 'approval': 'REVIEW_ONLY',
            'note': 'ROAS is revenue/spend, not profit ROI. Missing or zero denominator gives null.'}

def creator_report(data: list[dict], project: dict) -> dict:
    sources = {s['id'] for s in project['sources']}
    criteria = project.get('creator_criteria', {})
    minimum = criteria.get('followers_min', 10000); maximum = criteria.get('followers_max', 100000)
    platform = criteria.get('platform', 'YouTube')
    candidates = []; excluded = []; ids = set()
    for row in data:
        cid = row.get('creator_id')
        if not cid or cid in ids: raise ValueError('Missing or duplicate creator ID')
        ids.add(cid)
        reasons = []
        followers = number(row.get('followers'))
        if row.get('source_id') not in sources: reasons.append('evidence_missing')
        if row.get('platform') != platform: reasons.append('platform_mismatch')
        if followers is None or not minimum <= followers <= maximum: reasons.append('follower_range')
        values = [number(x) for x in row.get('recent_views', '').split('|') if x.strip()]
        med = median(values) if values else None
        if med is None: reasons.append('views_missing')
        fit = number(row.get('topic_fit'))
        if fit is None or not 0 <= fit <= 1: reasons.append('fit_unreviewed')
        elif fit < criteria.get('minimum_topic_fit', 0.5): reasons.append('topic_mismatch')
        cost = number(row.get('quoted_cost'))
        result = {'creator_id': cid, 'platform': row.get('platform'), 'followers': followers,
                  'median_views': med, 'sample_video_count': len(values), 'topic_fit': fit,
                  'topic_fit_type': 'USER_SUPPLIED_ASSESSMENT', 'quoted_cost': cost,
                  'estimated_historical_CPV': ratio(cost, med), 'source_id': row.get('source_id'),
                  'currency': row.get('currency'), 'approval': 'NOT_CONTACTED'}
        if reasons: excluded.append({**result, 'reasons': reasons})
        else: candidates.append(result)
    candidates.sort(key=lambda r: (-r['topic_fit'], -r['median_views'], r['creator_id']))
    return {'synthetic': project['synthetic'], 'criteria': criteria, 'candidates': candidates, 'excluded': excluded,
            'ranking': 'topic_fit_then_median_views', 'outreach_sent': False,
            'note': 'Historical CPV is not a forecast. No personal contact data is stored.'}
