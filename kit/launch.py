"""Assemble one local human-review package; never manufacture approvals or model output."""
from collections import Counter
from .creative import esc, shell


def assemble(project, context, truth, content, edm):
    items = content['review_items'] + edm['review_items']
    summary = dict(Counter(i['status'] for i in items))
    report = {'project_id': project['project_id'], 'synthetic': project['synthetic'],
              'status': 'READY_FOR_HUMAN_REVIEW', 'publication_ready': False, 'send_ready': False,
              'scope': content['scope'], 'review_summary': summary, 'review_items': items,
              'blockers': context['blockers'], 'next_action': context['next_action'],
              'unresolved_fact_ids': truth['unresolved_fact_ids'], 'conflict_fact_ids': truth['conflict_fact_ids'],
              'blocked_claim_ids': truth['blocked_claim_ids'], 'candidate_context': truth['candidate_context'],
              'assets_missing': sum(i['category'] == 'asset' and 'ASSET_MISSING' in i['blockers'] for i in items),
              'unknown_review_ids': sorted({r.get('item_id', '') for r in project.get('reviews', [])} - {i['item_id'] for i in items}),
              'human_user_testing': 'NOT_PERFORMED_BY_RUNTIME', 'ai_generated_images': 0}
    body = '<section class="panel"><h2>新品内容审核包</h2><p>本地内部草稿：事实真实性、产品外观、文案语义、外部发布均需要独立人工判断。</p>'
    body += '<nav><a href="content/review.html">Amazon 页面规划</a><a href="edm/email.html">EDM 草稿</a><a href="human-review.csv">审核表</a><a href="HANDOFF.md">下次继续</a></nav></section>'
    body += '<section class="panel"><h2>当前状态与下一步</h2><p>资料时效：'+esc(context['effective_freshness'])+'</p><p>'+esc(context['next_action'])+'</p>'
    body += '<p>未解决事实：'+esc(', '.join(truth['unresolved_fact_ids']) or '无已登记项')+'</p><p>冲突事实：'+esc(', '.join(truth['conflict_fact_ids']) or '无已登记项')+'</p>'
    body += '<p>不可用 Claim：'+esc(', '.join(truth['blocked_claim_ids']) or '无已登记项')+'</p><p>缺少素材单元：'+str(report['assets_missing'])+'</p>'
    body += '<ul>'+''.join('<li>'+esc(b if isinstance(b, str) else b.get('text', b['id']))+'</li>' for b in context['blockers'])+'</ul></section>'
    body += '<section class="panel"><h2>来源与可追溯事实</h2><div class="scroll"><table><tr><th>ID</th><th>信息</th><th>状态</th><th>来源 / 位置</th></tr>'
    for f in project.get('facts', []):
        body += '<tr>'+''.join('<td>'+esc(v)+'</td>' for v in [f['id'], str(f.get('field'))+' = '+str(f.get('value')), f['status'], str(f.get('source_id'))+' / '+str(f.get('evidence_location'))])+'</tr>'
    body += '</table></div><p>confirmed 是输入声明；本工具只检查结构和关联，不替代证据核实。</p></section>'
    body += '<section class="panel"><h2>假设、建议与资料缺口</h2><ul>'
    for c in project.get('candidate_context', []):
        body += '<li>'+esc(c['information_type'])+' · '+esc(c.get('text'))+' · '+esc(', '.join(c.get('source_ids', [])))+' · '+esc(c.get('status', 'unverified'))+'</li>'
    body += '</ul><p>候选内容不会自动写入 confirmed fact 或 approved claim。</p></section>'
    body += '<section class="panel"><h2>逐项审核：决定保持空白</h2><p>填写 CSV 是审核草稿；只有本人明确作出的决定，才可由 Agent 转写为项目中的 reviews 回执。此操作不批准任何外部 Claim 或发布。</p><div class="scroll"><table><tr><th>项目</th><th>候选值</th><th>Source</th><th>风险 / 状态</th><th>人工决定</th></tr>'
    for item in items:
        body += '<tr>'+''.join('<td>'+esc(v)+'</td>' for v in [item['item_id'], item.get('value'), ', '.join(item['source_ids']), item['status']+' / '+', '.join(item['blockers']), '________________'])+'</tr>'
    body += '</table></div></section><section class="panel"><h2>本包不包含</h2><p>没有 AI 图片生成、真实平台抓取、自动发送、Amazon 上传或真人试用结果。缺图仍是缺图，HTML 不等于最终视觉稿。</p></section>'
    return report, shell(project['product']['name']+' / 新品统一审核', body, project['synthetic']).replace('<html lang="ja">', '<html lang="zh-CN">')
