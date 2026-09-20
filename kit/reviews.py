"""CSV-only VOC analysis. Theme counts describe the uploaded sample, not the market."""
from __future__ import annotations
from collections import Counter
from .common import number

THEMES = {
    '設置・サイズ': ('サイズ', '小さい', '大きい', '置き', '設置'),
    '操作・設定': ('設定', '操作', '説明書', 'ボタン'),
    '音': ('音', '静か', 'うるさい'),
    'メンテナンス': ('手入れ', 'フィルター', '掃除', '交換'),
}

def summarize(data: list[dict], project: dict) -> dict:
    seen = {}; clean = []; duplicates = 0
    source_ids = {s['id'] for s in project['sources']}
    for row in data:
        if not row.get('review_id') or row.get('source_id') not in source_ids:
            raise ValueError('Review lacks a registered evidence source or ID')
        if row.get('product_id') != project['product']['id']:
            raise ValueError('Unmapped product in review input')
        key = (row['source_id'], row['review_id'])
        if key in seen:
            if row != seen[key]:
                raise ValueError('Conflicting versions of one review ID')
            duplicates += 1; continue
        seen[key] = row
        rating = number(row.get('rating'))
        if rating is not None and (not rating.is_integer() or not 1 <= rating <= 5):
            raise ValueError('Rating must be 1..5 or blank')
        clean.append({'id': row['review_id'], 'source_id': row['source_id'], 'text': row.get('text', ''), 'rating': rating})
    ratings = [r['rating'] for r in clean if r['rating'] is not None]
    themes = []
    configured = project.get('review_themes', THEMES)
    if not isinstance(configured, dict) or any(not isinstance(k, str) or not k or not isinstance(v, (list, tuple)) or not v or any(not isinstance(x, str) or not x for x in v) for k,v in configured.items()):
        raise ValueError('review_themes must map labels to nonempty keyword lists')
    for theme, words in configured.items():
        matches = [r for r in clean if any(w in r['text'] for w in words)]
        themes.append({'theme': theme, 'sample_mentions': len(matches), 'evidence_ids': [r['id'] for r in matches],
                       'sentiment': 'NOT_INFERRED', 'method': 'transparent_keyword_match',
                       'action_candidate': 'Review the matched comments before selecting copy or a product action.'})
    return {'status': 'SAMPLE_ANALYZED' if clean else 'EMPTY_INPUT_NOT_MARKET_ZERO', 'synthetic': project['synthetic'], 'input_rows': len(data), 'unique_reviews': len(clean),
            'exact_duplicates_removed': duplicates, 'rated_reviews': len(ratings),
            'average_rating': sum(ratings) / len(ratings) if ratings else None,
            'rating_distribution': dict(sorted(Counter(str(int(v)) for v in ratings).items())),
            'themes': themes, 'coverage': 'UPLOADED_SAMPLE_ONLY', 'automatic_claim_approval': False,
            'limitations': ['No live collection.', 'Keyword matching is not semantic analysis.',
                            'Counts may overlap; do not sum theme percentages.', 'No market-representative prevalence inference.']}
