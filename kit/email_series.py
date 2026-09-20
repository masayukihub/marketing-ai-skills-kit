"""Local multi-email planning and scoped review; no upstream runtime or cloud dependency."""
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from .common import digest, safe_id, safe_path
from .creative import esc, image_element, shell
from .review import copy_item, fingerprint, reviewed_state

COPY_FIELDS = ('headline', 'body', 'cta_label', 'cta_url')
KINDS = {'hero', 'body', 'product', 'proof', 'cta', 'footer'}


def indexed(rows, label):
    if not isinstance(rows, list):
        raise ValueError(label + ' must be a list')
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid ' + label)
        key = safe_id(row.get('id'))
        if key in result:
            raise ValueError('Duplicate ' + label + ' ID')
        result[key] = row
    return result


def validate_series(project):
    series = project.get('edm_series')
    if not isinstance(series, dict):
        raise ValueError('EDM_SERIES_REQUIRED: add local series input, not a new Skill')
    modules = indexed(series.get('modules'), 'module')
    emails = indexed(series.get('emails'), 'email')
    if not emails or not modules:
        raise ValueError('Series requires emails and modules')
    sources = {s['id'] for s in project['sources']}
    claims = {c['id'] for c in project.get('claims', [])}
    owners = list(modules.values())
    for module in modules.values():
        if module.get('kind') not in KINDS or not isinstance(module.get('body'), str) or not module['body'].strip():
            raise ValueError('Module requires a supported kind and body')
        if 'requires_asset' in module and type(module['requires_asset']) is not bool:
            raise ValueError('requires_asset must be boolean')
        inherited = module.get('inheritance')
        if inherited is not None:
            if not isinstance(inherited, dict) or inherited.get('source_id') not in sources:
                raise ValueError('Inheritance requires a registered local source')
            if any(not isinstance(inherited.get(k), str) or not inherited[k].strip()
                   for k in ('locator', 'structure_used', 'excluded_content')):
                raise ValueError('Inheritance requires locator, structure_used and excluded_content')
    for email in emails.values():
        mids = email.get('module_ids')
        if not isinstance(mids, list) or not mids or any(not isinstance(m, str) for m in mids) or len(mids) != len(set(mids)) or any(m not in modules for m in mids):
            raise ValueError('Email requires distinct known module_ids in reading order')
        if modules[mids[-1]]['kind'] != 'footer' or any(modules[m]['kind'] == 'footer' for m in mids[:-1]):
            raise ValueError('Email requires exactly one final footer')
        for field in ('stage', 'audience', 'purpose', 'purchase_reason'):
            if not isinstance(email.get(field), str) or not email[field].strip():
                raise ValueError('Email planning field required: ' + field)
        if email.get('planned_for'):
            date.fromisoformat(email['planned_for'])
        options = indexed(email.get('subject_options'), 'subject option')
        if email.get('selected_subject') not in options:
            raise ValueError('Selected subject must reference a supplied option')
        for option in options.values():
            if any(not isinstance(option.get(f), str) or not option[f].strip() for f in ('subject', 'preheader')):
                raise ValueError('Subject option needs subject and preheader')
        owners.extend(options.values())
    for owner in owners:
        bindings = owner.get('field_claim_ids', {})
        ids = owner.get('claim_ids', [])
        if not isinstance(ids, list) or any(not isinstance(c, str) or c not in claims for c in ids):
            raise ValueError('Series copy references unknown claim')
        if not isinstance(bindings, dict) or any(not isinstance(v, list) or any(c not in claims for c in v) for v in bindings.values()):
            raise ValueError('Invalid series field bindings')
        if not isinstance(owner.get('copy_kinds', {}), dict) or any(v not in {'factual', 'non_factual'} for v in owner.get('copy_kinds', {}).values()):
            raise ValueError('Invalid series copy classification')
        for field in (*COPY_FIELDS, 'subject', 'preheader'):
            if field in owner and not isinstance(owner[field], str):
                raise ValueError('Series copy must be plain text')
        if bool(owner.get('cta_label')) != bool(owner.get('cta_url')):
            raise ValueError('CTA label and URL must be supplied together')
    for key in ('visuals', 'comments'):
        if not isinstance(series.get(key, []), list) or any(not isinstance(r, dict) for r in series.get(key, [])):
            raise ValueError(key + ' must contain objects')
    return modules, emails


def inherited_evidence(root, project, module):
    record = module.get('inheritance')
    if not record:
        return None
    source = next(s for s in project['sources'] if s['id'] == record['source_id'])
    return dict(record, source=source, source_sha256=digest(safe_path(root, source['path'])),
                authority='STRUCTURE_ONLY_NOT_CURRENT_TRUTH')


def aggregate(project, item_id, value, blockers, as_of, category):
    hashed = fingerprint({'project_id': project['project_id'], 'item_id': item_id, 'value': value})
    return {'item_id': item_id, 'category': category, 'field': category, 'value': None,
            'fingerprint': hashed, 'source_ids': [], 'blockers': sorted(set(blockers)),
            'status': reviewed_state(project, item_id, hashed, blockers, as_of, True),
            'external_claim_approval': False}


def asset_item(root, project, module, prefix, copies, as_of):
    if not module.get('requires_asset') and not module.get('asset_path'):
        return None, ''
    graphic, _ = image_element(root, module)
    path = safe_path(root, module['asset_path']) if module.get('asset_path') else None
    blockers = []
    if not path or not path.is_file():
        blockers.append('ASSET_MISSING')
    if module.get('asset_rights') != 'user_confirmed':
        blockers.append('ASSET_RIGHTS_UNVERIFIED')
    if any(c['blockers'] for c in copies):
        blockers.append('COPY_EVIDENCE_UNRESOLVED')
    item = aggregate(project, prefix + ':asset',
                     {'sha256': digest(path) if path and path.is_file() else None,
                      'rights': module.get('asset_rights'), 'visual_brief': module.get('visual_brief'),
                      'copies': [c['fingerprint'] for c in copies]}, blockers, as_of, 'asset')
    return item, graphic


def valid_url(value):
    parsed = urlparse(value)
    return bool(parsed.scheme in {'https', 'http'} and parsed.netloc and not parsed.username and not parsed.password)


def render_email(project, email, selected, parts):
    label = 'SYNTHETIC DEMO / 送信不可' if project['synthetic'] else 'INTERNAL DRAFT / 送信不可'
    rows = ''.join('<tr><td id="' + esc(mid) + '" style="padding:24px;border-bottom:1px solid #dce5e1">' + part + '</td></tr>' for mid, part in parts)
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><title>' + esc(selected['subject']) + '</title>'
            '<style>body{margin:0;background:#eef3f1;color:#173b34;font:16px/1.7 system-ui;overflow-wrap:anywhere}img{max-width:100%;height:auto}h1,h2{line-height:1.35}.placeholder{padding:24px;border:2px dashed #8ca89b;background:#f5f7f4}.warn{font-size:12px;color:#754314;background:#fff5df;padding:8px}</style></head>'
            '<body><div style="display:none;max-height:0;overflow:hidden">' + esc(selected['preheader']) + '</div>'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td align="center">'
            '<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="width:100%;max-width:600px;background:white">'
            '<tr><td style="padding:16px 24px;background:#173b34;color:white">' + esc(label) + ' · ' + esc(email['id']) + '</td></tr>' + rows +
            '<tr><td style="padding:16px 24px;font-size:12px">会社住所・配信停止・同意・リンク・メールクライアント表示は送信前に別途確認。</td></tr>'
            '</table></td></tr></table></body></html>')


def impact(previous, current):
    if previous is not None and previous.get('project_id') != current['project_id']:
        raise ValueError('SERIES_PROJECT_MISMATCH')
    old = {e['id']: e for e in (previous or {}).get('emails', [])}
    new = {e['id']: e for e in current['emails']}
    changes = []
    for key in sorted(set(old) | set(new)):
        a, b = old.get(key), new.get(key)
        if not a or not b:
            changes.append({'email_id': key, 'change': 'added' if b else 'removed', 'visual_review_required': True})
            continue
        mids = sorted(set(a['module_hashes']) | set(b['module_hashes']))
        changed = [m for m in mids if a['module_hashes'].get(m) != b['module_hashes'].get(m)]
        if a['fingerprint'] != b['fingerprint']:
            changes.append({'email_id': key, 'change': 'changed', 'changed_modules': changed,
                            'subject_changed': a['header_hash'] != b['header_hash'],
                            'order_changed': a['module_ids'] != b['module_ids'], 'visual_review_required': True})
    return {'baseline': previous is None, 'changes': changes, 'automatic_approval': False}


def visual_inventory(root, series, emails):
    records = []
    for entry in series.get('visuals', []):
        eid = entry.get('email_id')
        email = emails.get(eid)
        reasons = []
        if not email:
            reasons.append('UNKNOWN_EMAIL')
        elif entry.get('fingerprint') != email['fingerprint']:
            reasons.append('STALE_VISUAL')
        if email and entry.get('module_ids') != email['module_ids']:
            reasons.append('INCOMPLETE_OR_WRONG_ORDER')
        if entry.get('kind') not in {'html_render', 'ai_concept'}:
            reasons.append('UNSUPPORTED_KIND')
        if entry.get('kind') == 'ai_concept' and not entry.get('generation_record'):
            reasons.append('GENERATION_EVIDENCE_MISSING')
        path = safe_path(root, entry.get('path', ''))
        if not path.is_file():
            reasons.append('FILE_MISSING')
        else:
            # Actual PNG/JPEG signature and size check, not a pixel decoder/semantic QA.
            image_element(root, {'asset_path': entry['path'], 'asset_rights': 'user_confirmed'})
            if digest(path) != entry.get('sha256'):
                reasons.append('IMAGE_HASH_MISMATCH')
        if entry.get('asset_rights') != 'user_confirmed':
            reasons.append('ASSET_RIGHTS_UNVERIFIED')
        records.append({'email_id': eid, 'kind': entry.get('kind'), 'path': entry.get('path'),
                        'status': 'BLOCKED' if reasons else 'FILE_CHECKED_REVIEW_REQUIRED', 'reasons': reasons,
                        'pixel_decoding': 'NOT_CHECKED', 'semantic_review': 'NOT_CHECKED',
                        'generation_provenance': 'HUMAN_REVIEW_REQUIRED'})
    return {'entries': records, 'missing_ai_concept_email_ids': [eid for eid in emails if not any(
            r['email_id'] == eid and r['kind'] == 'ai_concept' and not r['reasons'] for r in records)],
            'ai_generation': 'NOT_BUNDLED', 'browser_qa': 'NOT_RUN_BY_RUNTIME', 'complete_visual_approved': False}


def comment_plan(series, email_rows, modules):
    output = []
    seen = set()
    for comment in series.get('comments', []):
        cid = safe_id(comment.get('id'))
        if cid in seen:
            raise ValueError('Duplicate comment ID')
        seen.add(cid)
        eid, mid, field = (comment.get(k) for k in ('email_id', 'module_id', 'field'))
        email = email_rows.get(eid)
        module = modules.get(mid)
        reasons = []
        if not email or mid not in email['module_hashes']:
            reasons.append('TARGET_NOT_FOUND')
        elif comment.get('module_hash') != email['module_hashes'][mid]:
            reasons.append('STALE_COMMENT')
        if comment.get('kind') != 'copy' or field not in COPY_FIELDS:
            reasons.append('UNSUPPORTED_LOCAL_EDIT')
        elif module and module.get(field) != comment.get('before'):
            reasons.append('BEFORE_MISMATCH')
        if not isinstance(comment.get('after'), str) or len(comment.get('after', '')) > 10000:
            reasons.append('INVALID_PROPOSAL')
        output.append({'id': cid, 'email_id': eid, 'module_id': mid, 'field': field,
                       'before': comment.get('before'), 'after': comment.get('after'),
                       'status': 'BLOCKED' if reasons else 'READY_FOR_HUMAN_REVIEW', 'reasons': reasons,
                       'affected_email_ids': [e for e, row in email_rows.items() if mid in row['module_ids']],
                       'applied': False, 'approval_granted': False})
    return output


def build_series(root: Path, project: dict, as_of: date, previous=None):
    modules, emails = validate_series(project)
    series = project['edm_series']
    review_items, rows, pages, warnings = [], [], {}, []
    for eid, email in emails.items():
        prefix = 'series:' + eid
        options = indexed(email['subject_options'], 'subject option')
        selected = options[email['selected_subject']]
        selected_items = []
        if len(options) < 3:
            warnings.append({'email_id': eid, 'code': 'SUBJECT_OPTIONS_BELOW_THREE'})
        for oid, option in options.items():
            items = [copy_item(root, project, option, prefix + ':subject:' + oid, field, option.get('claim_ids', []), as_of)
                     for field in ('subject', 'preheader')]
            review_items.extend(items)
            if oid == email['selected_subject']:
                selected_items = items
        hashes, parts, child_items, inherited = {}, [], list(selected_items), {}
        for mid in email['module_ids']:
            module = modules[mid]
            mprefix = prefix + ':module:' + mid
            copies = [copy_item(root, project, module, mprefix, field, module.get('claim_ids', []), as_of)
                      for field in COPY_FIELDS if field in module]
            review_items.extend(copies)
            asset, graphic = asset_item(root, project, module, mprefix, copies, as_of)
            child_items.extend(copies)
            if asset:
                review_items.append(asset)
                child_items.append(asset)
            inheritance = inherited_evidence(root, project, module)
            inherited[mid] = inheritance
            blockers = [b for c in copies for b in c['blockers']] + (asset['blockers'] if asset else [])
            if any(c['status'] != 'APPROVED_INTERNAL_ONLY' for c in copies) or (asset and asset['status'] != 'APPROVED_INTERNAL_ONLY'):
                blockers.append('COMPONENT_REVIEW_REQUIRED')
            layout = aggregate(project, mprefix + ':layout',
                               {'kind': module['kind'], 'visual_brief': module.get('visual_brief'), 'copies': [c['fingerprint'] for c in copies],
                                'asset': asset['fingerprint'] if asset else None, 'inheritance': inheritance},
                               blockers, as_of, 'module_layout')
            hashes[mid] = layout['fingerprint']
            review_items.append(layout)
            child_items.append(layout)
            text = '<p class="warn">内部候補 / ' + esc(' · '.join(c['status'] for c in copies)) + '</p>'
            if module.get('headline'):
                text += '<h2>' + esc(module['headline']) + '</h2>'
            text += '<p>' + esc(module['body']).replace('\n', '<br>') + '</p>' + graphic
            if module.get('cta_url'):
                if valid_url(module['cta_url']):
                    text += '<a style="display:inline-block;padding:12px 20px;background:#173b34;color:white" href="' + esc(module['cta_url']) + '">' + esc(module['cta_label']) + '</a>'
                else:
                    text += '<p class="warn">CTA URL 要確認</p>'
                    warnings.append({'email_id': eid, 'module_id': mid, 'code': 'CTA_URL_INVALID'})
            parts.append((mid, text))
        header_hash = fingerprint({'selected_subject': email['selected_subject'], 'copy': [i['fingerprint'] for i in selected_items]})
        whole = aggregate(project, prefix + ':whole-email',
                          {'header': header_hash, 'modules': [(mid, hashes[mid]) for mid in email['module_ids']],
                           'plan': {k: email.get(k) for k in ('stage', 'audience', 'purpose', 'purchase_reason', 'planned_for')}},
                          ['COMPONENT_REVIEW_REQUIRED'] if any(i['status'] != 'APPROVED_INTERNAL_ONLY' for i in child_items) else [],
                          as_of, 'whole_email')
        review_items.append(whole)
        rows.append({**{k: email.get(k) for k in ('id', 'stage', 'audience', 'purpose', 'purchase_reason', 'planned_for', 'module_ids')},
                     'subject_options': email['subject_options'], 'selected_subject': email['selected_subject'],
                     'header_hash': header_hash, 'module_hashes': hashes, 'fingerprint': whole['fingerprint'],
                     'inheritance': inherited, 'status': whole['status'], 'date_approval': 'NOT_GRANTED_BY_RUNTIME'})
        pages['emails/' + eid + '.html'] = render_email(project, email, selected, parts)
    for i, row in enumerate(rows):
        if i and row['audience'] == rows[i-1]['audience'] and row['purchase_reason'] == rows[i-1]['purchase_reason']:
            warnings.append({'email_id': row['id'], 'code': 'REPEATED_PURCHASE_REASON'})
    report = {'schema_version': '1.0', 'project_id': project['project_id'], 'emails': rows,
              'review_items': review_items, 'warnings': warnings, 'publication_ready': False, 'send_ready': False,
              'shared_comments': 'NOT_BUNDLED', 'commercial_calculation': 'NOT_BUNDLED'}
    stale = [i for i in review_items if i['status'] == 'STALE_REVIEW']
    pending = [i for i in review_items if i['status'] != 'APPROVED_INTERNAL_ONLY']
    report['review_summary'] = {
        'stale_review_count': len(stale),
        'stale_email_ids': sorted({i['item_id'].split(':')[1] for i in stale}),
        'pending_review_count': len(pending),
        'pending_email_ids': sorted({i['item_id'].split(':')[1] for i in pending}),
    }
    report['impact'] = impact(previous, report)
    report['visual_inventory'] = visual_inventory(root, series, {r['id']: r for r in rows})
    report['comment_plan'] = comment_plan(series, {r['id']: r for r in rows}, modules)
    for change in report['impact']['changes']:
        if change['change'] == 'removed':
            old_id = safe_id(change['email_id'])
            pages['emails/' + old_id + '.html'] = shell('SUPERSEDED / 已从当前系列移除', '<p>请返回最新系列审核首页。此篇不再属于当前交付范围，不可继续作为现稿使用。</p>', project['synthetic'])
    body = '<section class="panel"><h2>系列邮件 · 内部审核</h2><p>日期是计划输入，不是正式排期批准。没有自动出图、共享评论服务或发送。</p>'
    body += '<p>待处理审核：' + str(len(pending)) + ' 项；失效审核：' + str(len(stale)) + ' 项。失效邮件：' + esc(', '.join(report['review_summary']['stale_email_ids']) or '无') + '。无新增变更不代表旧审核已经恢复。</p><nav>'
    body += ''.join('<a href="emails/' + esc(r['id']) + '.html">' + esc(r['id']) + '</a>' for r in rows) + '</nav></section>'
    body += '<iframe title="第一封邮件草稿" src="emails/' + rows[0]['id'] + '.html" sandbox style="width:100%;height:900px;border:1px solid #dbe3df;border-radius:12px;background:white"></iframe>'
    body += '<section class="panel"><h2>系列矩阵</h2><p>小屏可在表格内横向滚动。</p><div class="scroll" tabindex="0" role="region" aria-label="系列矩阵，可横向滚动"><table style="min-width:700px;table-layout:fixed"><tr><th>篇目 / 阶段</th><th>受众 / 任务</th><th>购买理由</th><th>计划日期</th></tr>'
    for r in rows:
        body += '<tr>' + ''.join('<td>' + esc(v) + '</td>' for v in [r['id'] + ' / ' + r['stage'], r['audience'] + ' / ' + r['purpose'], r['purchase_reason'], r['planned_for'] or 'UNKNOWN']) + '</tr>'
    body += '</table></div></section><details class="panel"><summary>变更、来源继承与待核实项</summary><pre>'
    import json
    body += esc(json.dumps({'impact': report['impact'], 'warnings': warnings, 'inheritance': {r['id']: r['inheritance'] for r in rows},
                           'visuals': report['visual_inventory'], 'comments': report['comment_plan']}, ensure_ascii=False, indent=2)) + '</pre></details>'
    body += '<section class="panel"><h2>人工审核</h2><p>文案/模块/整封审核见 human-review.csv 与 scoped-review.json。决定栏保持空白；旧 hash 不能批准新文案。<a href="human-review.csv">打开审核表</a></p></section>'
    pages['review.html'] = shell(project['product']['name'] + ' / EDM 系列审核', body, project['synthetic']).replace('<html lang="ja">', '<html lang="zh-CN">')
    return report, pages
