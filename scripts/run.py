#!/usr/bin/env python3
"""Run an offline workflow: output is draft analysis, never production approval."""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kit.common import load_json, rows, write_json, write_csv, safe_path
from kit.truth import load_project, truth_report
from kit.context import resolve, snapshot, delta, TASK_FILES
from kit.reviews import summarize
from kit.operations import campaign_report, creator_report
from kit.creative import page_report, edm_html, shell, esc


def run(task: str, project_dir: Path, out: Path, scope: str, as_of: date) -> dict:
    project_dir = project_dir.resolve()
    out = out.resolve()
    # All runtime output lives away from immutable input files.
    if out == project_dir or project_dir.is_relative_to(out) or out.is_relative_to(project_dir):
        raise ValueError('Output directory must be separate from the input project')
    if out == ROOT or ROOT.is_relative_to(out):
        raise ValueError('Output must not overwrite the kit root')
    project = load_project(project_dir)
    out.mkdir(parents=True, exist_ok=True)
    marker = out / 'run.json'
    previous = load_json(marker) if marker.is_file() else None
    if previous and (previous.get('project_id') != project['project_id'] or previous.get('task') != task):
        raise ValueError('Output belongs to another project/task; use another directory')
    current_sources = snapshot(project_dir, project, task)
    changes = delta(previous.get('source_snapshot') if previous else None, current_sources)
    context = resolve(project, task, as_of)
    write_json(out / 'context.json', context)
    write_json(out / 'truth-check.json', truth_report(project, as_of))
    body = ''
    if task == 'content':
        report, page = page_report(project_dir, project, scope, as_of)
        write_json(out / 'page-plan.json', report)
        (out / 'review.html').write_text(page, encoding='utf-8')
        write_csv(out / 'copy-visual-review.csv', report['units'], ['id', 'section', 'headline', 'visual_proof_brief', 'asset_status', 'copy_visual_fidelity', 'mobile_proof'])
    elif task == 'edm':
        report, page = edm_html(project, as_of)
        write_json(out / 'edm-check.json', report)
        (out / 'email.html').write_text(page, encoding='utf-8')
    elif task == 'insights':
        report = summarize(rows(safe_path(project_dir, 'reviews.csv')), project)
        write_json(out / 'voc-summary.json', report)
        competitors = rows(safe_path(project_dir, 'competitors.csv')) if safe_path(project_dir, 'competitors.csv').is_file() else []
        known_sources = {s['id'] for s in project['sources']}
        if any(r.get('source_id') not in known_sources for r in competitors):
            raise ValueError('Competitor rows must reference registered evidence')
        write_json(out / 'internal-competitors.json', {'visibility': 'INTERNAL_RESEARCH_ONLY', 'synthetic': project['synthetic'], 'rows': competitors})
        body = '<div class="panel"><h2>VOC · 上传样本</h2><p>去重后评论数：'+str(report['unique_reviews'])+'</p><p>平均评分：'+esc(report['average_rating'])+'</p><p>主题为关键词匹配，不代表市场占比，也不自动判断正负情绪。</p></div>'
        body += ''.join('<div class="panel"><h3>'+esc(t['theme'])+'</h3><p>提及：'+str(t['sample_mentions'])+'</p><p>证据 ID：'+esc(', '.join(t['evidence_ids']))+'</p><p>行动候选：复核原文，再决定 FAQ、文案或产品改进。</p></div>' for t in report['themes'])
    elif task == 'campaign':
        report = campaign_report(rows(safe_path(project_dir, 'campaign.csv')), project)
        write_json(out / 'campaign-summary.json', report)
        write_csv(out / 'channel-metrics.csv', report['channels'], ['channel', 'spend', 'impressions', 'clicks', 'orders', 'revenue', 'CTR', 'CVR', 'CPA', 'ROAS'])
        body = '<div class="panel"><h2>Campaign · 可复算指标</h2><p>总体比例按合计分子／合计分母计算。ROAS 不是利润 ROI。</p><pre>'+esc(json.dumps(report.get('total'),ensure_ascii=False,indent=2))+'</pre></div>'
    elif task == 'influencer':
        report = creator_report(rows(safe_path(project_dir, 'creators.csv')), project)
        write_json(out / 'creator-shortlist.json', report)
        write_csv(out / 'creator-shortlist.csv', report['candidates'], ['creator_id','platform','followers','median_views','topic_fit','quoted_cost','currency','estimated_historical_CPV','source_id'])
        body = '<div class="panel"><h2>KOL · 条件筛选</h2><p>按人工提供的受众匹配分和近期视频中位播放排序。未发送邀约，无私人联系方式。</p><pre>'+esc(json.dumps(report['candidates'],ensure_ascii=False,indent=2))+'</pre></div>'
    else:
        raise ValueError('Unknown workflow')
    if body:
        (out / 'review.html').write_text(shell(project['product']['name']+' / '+task,body,project['synthetic']),encoding='utf-8')
    result = {'schema_version': '1.0', 'kit_version': '0.1.0-rc1', 'task': task,
              'project_id': project['project_id'], 'synthetic': project['synthetic'],
              'status': 'DEMO_REVIEW_READY' if project['synthetic'] else 'DRAFT_REVIEW_READY',
              'state_as_of': project.get('state',{}).get('state_as_of'), 'evaluated_at': as_of.isoformat(),
              'scope': scope if task == 'content' else None, 'source_snapshot': current_sources,
              'source_delta': changes, 'new_memory_proposals': 0,
              'memory_proposals_implemented': False,
              'source_changes_need_review': bool(changes['new'] or changes['changed'] or changes['removed']),
              'publication_ready': False, 'input_files_modified': False, 'network_calls': 0,
              'browser_qa': 'NOT_RUN_BY_RUNTIME', 'ai_image_generation': 'NOT_IMPLEMENTED'}
    write_json(marker, result)
    (out/'HANDOFF.md').write_text('# Next session\n\nRead AGENTS.md and this output’s context.json, truth-check.json and run.json.\n\nTask: '+task+'\nProject: '+project['project_id']+'\nNext: '+context['next_action']+'\n\nDo not upgrade draft claims, missing images, source changes or test success into approval.\n',encoding='utf-8')
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--task', choices=list(TASK_FILES), required=True)
    p.add_argument('--project', type=Path, default=ROOT/'examples/demo-project')
    p.add_argument('--out', type=Path)
    p.add_argument('--scope', choices=['full','gallery','aplus'], default='full')
    p.add_argument('--as-of', type=date.fromisoformat, default=date.today())
    args = p.parse_args()
    try:
        result = run(args.task,args.project,args.out or ROOT/'outputs'/args.project.name/args.task,args.scope,args.as_of)
        print(json.dumps({k:result[k] for k in ('status','project_id','task','publication_ready','source_delta')},ensure_ascii=False))
        print('OUTPUT:',args.out or ROOT/'outputs'/args.project.name/args.task)
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'status':'INPUT_ERROR','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__ == '__main__': raise SystemExit(main())
