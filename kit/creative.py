"""Page structure, copy/proof review and standalone draft HTML. Not an image model."""
from __future__ import annotations
import base64
import html
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from .common import safe_path
from .truth import claim_usable

CSS = '''*{box-sizing:border-box}body{margin:0;color:#18252b;background:#f1f4f3;font:16px/1.65 system-ui,-apple-system,sans-serif}header{background:#143d36;color:white;padding:36px max(5vw,16px)}main{max-width:1120px;margin:auto;padding:28px 20px}h1{font-size:clamp(27px,5vw,42px);line-height:1.2}h2{font-size:24px}h3{margin:0 0 12px}nav{display:flex;gap:18px;flex-wrap:wrap}a{color:inherit}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.unit,.panel{background:white;border:1px solid #dbe3df;border-radius:16px;padding:24px;margin-bottom:20px}.badge{display:inline-block;font:12px/1.6 system-ui;letter-spacing:.08em;border:1px solid #ccd9d3;border-radius:20px;padding:3px 10px;margin:4px 4px 8px 0}.warn{color:#914a12;background:#fff5df;padding:14px;border-left:4px solid #b68a36}.visual{min-height:180px;background:#f0f3ee;border-radius:12px;padding:20px;display:flex;align-items:center;justify-content:center}.placeholder{text-align:center;max-width:280px;border:2px dashed #a6bcb3;padding:25px;line-height:1.5;color:#445d54}img{max-width:100%;height:auto;max-height:360px}dt{font-size:12px;font-weight:700;color:#617870;margin-top:14px}dd{margin:4px 0}table{width:100%;border-collapse:collapse}td,th{padding:10px;text-align:left;border-bottom:1px solid #dae3df;vertical-align:top}.scroll{overflow:auto}.muted{color:#546762}footer{padding:30px;text-align:center;color:#546762}pre{white-space:pre-wrap;overflow-wrap:anywhere}section{scroll-margin-top:20px}@media(max-width:650px){.grid{grid-template-columns:1fr}main{padding:20px 12px}.unit,.panel{padding:18px}h2{font-size:22px}}'''

def esc(x): return html.escape(str(x if x is not None else ''), quote=True)

def shell(title: str, body: str, synthetic: bool) -> str:
    status = 'SYNTHETIC DEMO — 架空データ・公開不可' if synthetic else 'INTERNAL REVIEW — 未承認・公開不可'
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>{esc(title)}</title><style>{CSS}</style></head><body><header><span class="badge">MARKETING AI SKILLS KIT</span><h1>{esc(title)}</h1><p>{esc(status)}</p></header><main>{body}</main><footer>Local-first / No tracking / Review is not publication approval</footer></body></html>'

def image_element(root: Path, unit: dict) -> tuple[str, str]:
    name = unit.get('asset_path')
    if not name:
        return '<div class="placeholder"><strong>ASSET NOT PROVIDED</strong><br>承認済みの商品画像をここに配置<br>これは生成画像ではありません</div>', 'MISSING'
    if unit.get('asset_rights') != 'user_confirmed':
        return '<div class="placeholder">ASSET RIGHTS NOT CONFIRMED</div>', 'RIGHTS_UNVERIFIED'
    path = safe_path(root, name)
    if not path.is_file() or path.stat().st_size > 3_000_000:
        raise ValueError('Asset missing or exceeds 3 MB')
    data = path.read_bytes(); suffix = path.suffix.lower()
    allowed = {'.png': ('image/png', b'\x89PNG\r\n\x1a\n'), '.jpg': ('image/jpeg', b'\xff\xd8\xff'), '.jpeg': ('image/jpeg', b'\xff\xd8\xff')}
    if suffix not in allowed or not data.startswith(allowed[suffix][1]):
        raise ValueError('Only PNG/JPEG assets with matching signatures are accepted')
    mime = allowed[suffix][0]
    return f'<img alt="{esc(unit.get("alt_text", "User-supplied product asset"))}" src="data:{mime};base64,{base64.b64encode(data).decode()}">', 'USER_SUPPLIED_NOT_VISUALLY_VERIFIED'

def page_report(root: Path, project: dict, scope: str, as_of: date) -> tuple[dict, str]:
    scopes = {'full': {'gallery', 'aplus', 'brand', 'comparison', 'faq'}, 'gallery': {'gallery'}, 'aplus': {'aplus', 'brand', 'comparison', 'faq'}}
    if scope not in scopes: raise ValueError('Invalid page scope')
    claims = {c['id']: c for c in project.get('claims', [])}
    rows = []; sections = {}; problems = []
    for unit in project.get('page_units', []):
        section = unit['section']
        if section not in scopes[scope]: continue
        bound = [claims[c] for c in unit.get('claim_ids', [])]
        blocked = [c['id'] for c in bound if not claim_usable(c, project, as_of)]
        graphic, asset_state = image_element(root, unit)
        if not unit.get('visual_proof'): problems.append({'unit': unit['id'], 'code': 'PROOF_BRIEF_MISSING'})
        if blocked: problems.append({'unit': unit['id'], 'code': 'CLAIMS_NOT_APPROVED', 'claims': blocked})
        if asset_state != 'USER_SUPPLIED_NOT_VISUALLY_VERIFIED': problems.append({'unit': unit['id'], 'code': 'ASSET_NOT_READY'})
        row = {'id': unit['id'], 'section': section, 'consumer_question': unit.get('consumer_question'),
               'headline': unit.get('headline'), 'claim_ids': unit.get('claim_ids', []),
               'blocked_claim_ids': blocked, 'visual_proof_brief': unit.get('visual_proof'),
               'asset_status': asset_state, 'copy_visual_fidelity': 'NOT_REVIEWED',
               'mobile_proof': 'NOT_REVIEWED', 'evidence_mode': 'ILLUSTRATION_NOT_MEASUREMENT'}
        rows.append(row)
        bound_text = '<br>'.join(esc(c['text']) + (f' — {esc(c["conditions"])}' if c.get('conditions') else '') for c in bound if claim_usable(c, project, as_of))
        warning = '<p class="warn">参照された主張に未承認または期限切れのものがあります。確定コピーとして使用しないでください。</p>' if blocked else ''
        card = f'<article class="unit" id="{esc(unit["id"])}"><span class="badge">{esc(unit["id"])} · {esc(section)}</span><h3>{esc(unit.get("headline"))}</h3>{warning}<p>{esc(unit.get("support"))}</p><div class="visual">{graphic}</div><dl><dt>CONSUMER QUESTION</dt><dd>{esc(unit.get("consumer_question"))}</dd><dt>APPROVED / DEMO-ONLY BOUND COPY</dt><dd>{bound_text or "使用可能な主張なし"}</dd><dt>VISUAL PROOF BRIEF — NOT A RENDER</dt><dd>{esc(unit.get("visual_proof"))}</dd><dt>COPY ↔ IMAGE REVIEW</dt><dd>NOT_REVIEWED — 画像の実確認が必要です</dd></dl></article>'
        sections.setdefault(section, []).append(card)
    required = {'gallery', 'aplus'} if scope == 'full' else {scope}
    for family in required:
        if family not in sections: problems.append({'unit': family, 'code': 'REQUIRED_SCOPE_EMPTY'})
    source_ids = {s['id'] for s in project['sources']}
    table_rows = []
    if 'comparison' in scopes[scope]:
        for model in project.get('series_comparison', []):
            if model.get('brand') != project['brand']['name']:
                raise ValueError('External competitor cannot enter same-brand comparison')
            if model.get('source_id') not in source_ids:
                raise ValueError('Comparison value lacks a registered source')
            table_rows.append('<tr>'+''.join(f'<td>{esc(model.get(k))}</td>' for k in ('name','recommended_for','home_fit','key_difference'))+'</tr>')
    titles = {'gallery': 'Gallery · 最初の購入判断', 'aplus': 'A+ · 理解と根拠', 'brand': 'Brand · ブランドの役割', 'comparison': 'Series · 同ブランドの選び方', 'faq': 'FAQ · 購入前の不安'}
    parts = ['<div class="panel"><h2>ページ構成とコピーを先に確認</h2><p>このHTMLは社内レビュー用です。Amazonへのアップロード用ファイル、生成画像、公式テンプレートの再現ではありません。</p><nav>'+''.join(f'<a href="#{k}">{esc(v.split(" · ")[0])}</a>' for k,v in titles.items() if k in scopes[scope])+'</nav></div>']
    for key in titles:
        if key not in scopes[scope]: continue
        cards = ''.join(sections.get(key, [])) or '<div class="panel">この項目の入力はありません。</div>'
        if key == 'comparison' and table_rows:
            cards += '<div class="panel scroll"><table><thead><tr><th>モデル</th><th>おすすめ</th><th>住まい</th><th>主な違い</th></tr></thead><tbody>'+''.join(table_rows)+'</tbody></table></div>'
        parts.append(f'<section id="{key}"><h2>{esc(titles[key])}</h2><div class="grid">{cards}</div></section>')
    return {'scope': scope, 'units': rows, 'issues': problems, 'publication_ready': False,
            'generated_images': 0, 'external_competitors_in_publishable_comparison': 0,
            'browser_qa': 'NOT_RUN_BY_RUNTIME', 'semantic_visual_qa': 'HUMAN_REVIEW_REQUIRED'}, shell(project['product']['name']+' / Content Review', ''.join(parts), project['synthetic'])

def edm_html(project: dict, as_of: date) -> tuple[dict, str]:
    edm = project.get('edm', {})
    url = edm.get('cta_url', '')
    parsed = urlparse(url)
    valid_url = bool(parsed.scheme in {'https', 'http'} and parsed.netloc and not parsed.username and not parsed.password)
    approved = [c for c in project.get('claims', []) if claim_usable(c, project, as_of)]
    copy = ''.join('<p style="margin:12px 0">'+esc(c['text'])+((' '+esc(c['conditions'])) if c.get('conditions') else '')+'</p>' for c in approved)
    cta = f'<a href="{esc(url)}" style="display:inline-block;padding:14px 24px;color:#fff;background:#143d36;text-decoration:none">{esc(edm.get("cta_label", "詳しく見る"))}</a>' if valid_url else '<p style="padding:14px;border:1px dashed #888">CTA URL 未設定</p>'
    # The unsubscribe token is intentionally absent; an ESP-specific validated binding is required.
    label = 'SYNTHETIC DEMO / 送信不可' if project['synthetic'] else 'DRAFT / 送信不可'
    content = f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>{esc(edm.get("subject", "EDM draft"))}</title></head><body style="margin:0;background:#edf1ef;font-family:Arial,sans-serif;color:#18252b"><div style="display:none;max-height:0;overflow:hidden">{esc(edm.get("preheader"))}</div><table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td align="center"><table role="presentation" width="600" cellspacing="0" cellpadding="0" style="width:100%;max-width:600px;background:white"><tr><td style="padding:18px 28px;background:#143d36;color:white;font-size:12px">{esc(label)}</td></tr><tr><td style="padding:32px"><p>{esc(project["brand"]["name"])}</p><h1 style="font-size:28px;line-height:1.3">{esc(edm.get("headline", project["product"]["name"]))}</h1>{copy}{cta}</td></tr><tr><td style="padding:24px;background:#e8eeeb;font-size:12px">{esc(project["brand"].get("company_name", "COMPANY_REQUIRED"))}<br>送信前に会社住所・配信停止リンク・同意・ESP表示を確認してください。</td></tr></table></td></tr></table></body></html>'
    return {'subject': edm.get('subject'), 'preheader': edm.get('preheader'),
            'cta_configured': valid_url, 'send_ready': False, 'sent': False,
            'requires': ['brand/legal review', 'unsubscribe binding', 'ESP client rendering', 'recipient consent', 'human approval'],
            'blocked_claim_ids': [c['id'] for c in project.get('claims', []) if not claim_usable(c, project, as_of)]}, content
