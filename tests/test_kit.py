from __future__ import annotations
from copy import deepcopy
from datetime import date
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from kit.common import number,ratio,safe_path,rows,load_json,write_json,write_csv
from kit.truth import load_project,truth_report,claim_usable
from kit.context import delta,resolve,snapshot
from kit.reviews import summarize
from kit.operations import campaign_report,creator_report
from kit.creative import page_report,edm_html
from run import run
from install import install
from doctor import doctor
from build_release import export
from sanitize_check import findings,release_files
from bootstrap_github import plan

class KitTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
  self.project=self.base/'input';shutil.copytree(ROOT/'examples/demo-project',self.project)
  self.p=load_project(self.project);self.today=date(2026,9,20)
 def tearDown(self):self.tmp.cleanup()
 def mutate(self,p):write_json(self.project/'project.json',p)
 def approved(self):
  c=deepcopy(self.p['claims'][0]);c.update(status='approved',approval_ref='REVIEW-EXAMPLE-ONLY',market='JP');return c
 def test_demo_valid(self):self.assertTrue(self.p['synthetic'])
 def test_unknown_not_zero(self):self.assertIsNone(self.p['facts'][-1]['value'])
 def test_missing_source_rejected(self):
  self.p['facts'][0]['source_id']='missing';self.mutate(self.p)
  with self.assertRaises(ValueError):load_project(self.project)
 def test_approved_without_ref_rejected(self):
  self.p['claims'][0]['status']='approved';self.mutate(self.p)
  with self.assertRaises(ValueError):load_project(self.project)
 def test_conditional_without_conditions_rejected(self):
  self.p['claims'][0]=self.approved();self.p['claims'][0]['status']='conditional';self.mutate(self.p)
  with self.assertRaises(ValueError):load_project(self.project)
 def test_demo_cannot_be_real(self):
  self.p['synthetic']=False;self.mutate(self.p)
  with self.assertRaises(ValueError):load_project(self.project)
 def test_draft_claim_not_usable(self):self.assertFalse(claim_usable(self.p['claims'][-1],self.p,self.today))
 def test_expired_claim_not_usable(self):
  c=self.approved();c['valid_to']='2026-01-01';self.assertFalse(claim_usable(c,self.p,self.today))
 def test_wrong_market_not_usable(self):
  c=self.approved();c['market']='US';self.assertFalse(claim_usable(c,self.p,self.today))
 def test_future_claim_not_usable(self):
  c=self.approved();c['valid_from']='2030-01-01';self.assertFalse(claim_usable(c,self.p,self.today))
 def test_truth_never_publishes(self):self.assertFalse(truth_report(self.p,self.today)['publication_ready'])
 def test_duplicate_ids_rejected(self):
  self.p['page_units'].append(self.p['page_units'][0]);self.mutate(self.p)
  with self.assertRaises(ValueError):load_project(self.project)
 def test_duplicate_json_keys_rejected(self):
  f=self.base/'dup.json';f.write_text('{"a":1,"a":2}')
  with self.assertRaises(ValueError):load_json(f)
 def test_nonfinite_json_rejected(self):
  f=self.base/'bad.json';f.write_text('{"a":NaN}')
  with self.assertRaises(ValueError):load_json(f)
 def test_negative_number_rejected(self):
  with self.assertRaises(ValueError):number(-1)
 def test_missing_ratio_null(self):self.assertIsNone(ratio(10,None));self.assertIsNone(ratio(10,0))
 def test_path_traversal_rejected(self):
  with self.assertRaises(ValueError):safe_path(self.project,'../private.txt')
 def test_absolute_path_rejected(self):
  with self.assertRaises(ValueError):safe_path(self.project,str(self.project/'project.json'))
 @unittest.skipIf(os.name=='nt','Symlink creation requires elevated privileges on some Windows hosts')
 def test_symlink_rejected(self):
  file=self.base/'hidden';file.write_text('private');(self.project/'link').symlink_to(file)
  with self.assertRaises(ValueError):safe_path(self.project,'link')
 def test_reviews_dedupe(self):
  r=summarize(rows(self.project/'reviews.csv'),self.p);self.assertEqual(r['unique_reviews'],8);self.assertEqual(r['exact_duplicates_removed'],1);self.assertEqual(r['rated_reviews'],7)
 def test_reviews_conflicting_version(self):
  r=rows(self.project/'reviews.csv');r[-1]['text']='different'
  with self.assertRaises(ValueError):summarize(r,self.p)
 def test_reviews_unmapped_product(self):
  r=rows(self.project/'reviews.csv');r[0]['product_id']='other'
  with self.assertRaises(ValueError):summarize(r,self.p)
 def test_reviews_invalid_rating(self):
  r=rows(self.project/'reviews.csv');r[0]['rating']='6'
  with self.assertRaises(ValueError):summarize(r,self.p)
 def test_custom_voc_themes(self):
  self.p['review_themes']={'Usability':['操作','設定']}
  r=summarize(rows(self.project/'reviews.csv'),self.p)
  self.assertEqual([t['theme'] for t in r['themes']],['Usability'])
 def test_themes_not_sentiment(self):
  r=summarize(rows(self.project/'reviews.csv'),self.p)
  self.assertTrue(all(t['sentiment']=='NOT_INFERRED' for t in r['themes']))
 def test_campaign_weighted_ratio(self):
  r=campaign_report(rows(self.project/'campaign.csv'),self.p)
  self.assertAlmostEqual(r['total']['CTR'],340/31000);self.assertEqual(r['total']['ROAS'],3.2)
 def test_zero_spend_roas_null(self):
  r=campaign_report(rows(self.project/'campaign.csv'),self.p)
  self.assertIsNone(r['channels'][-1]['ROAS'])
 def test_currency_conflict(self):
  r=rows(self.project/'campaign.csv');r[0]['currency']='USD'
  with self.assertRaises(ValueError):campaign_report(r,self.p)
 def test_missing_metric_not_zero(self):
  r=rows(self.project/'campaign.csv');r[0]['orders']=''
  self.assertIsNone(campaign_report(r,self.p)['total']['orders'])
 def test_kol_range_and_median(self):
  r=creator_report(rows(self.project/'creators.csv'),self.p)
  self.assertEqual([c['creator_id'] for c in r['candidates']],['CR-A','CR-F','CR-B'])
  self.assertEqual(r['candidates'][0]['median_views'],10000)
 def test_no_outreach(self):self.assertFalse(creator_report(rows(self.project/'creators.csv'),self.p)['outreach_sent'])
 def test_content_full_scope(self):
  r,h=page_report(self.project,self.p,'full',self.today)
  self.assertTrue({'gallery','aplus','brand','comparison','faq'}<={x['section'] for x in r['units']});self.assertIn('SYNTHETIC DEMO',h)
 def test_aplus_does_not_rerender_gallery(self):
  r,h=page_report(self.project,self.p,'aplus',self.today)
  self.assertNotIn('gallery',{x['section'] for x in r['units']})
 def test_missing_aplus_flagged(self):
  self.p['page_units']=[u for u in self.p['page_units'] if u['section']!='aplus']
  r,h=page_report(self.project,self.p,'full',self.today)
  self.assertTrue(any(x['code']=='REQUIRED_SCOPE_EMPTY' for x in r['issues']))
 def test_external_brand_blocked(self):
  self.p['series_comparison'][0]['brand']='Unrelated brand'
  with self.assertRaises(ValueError):page_report(self.project,self.p,'full',self.today)
 def test_comparison_missing_source(self):
  self.p['series_comparison'][0]['source_id']='missing'
  with self.assertRaises(ValueError):page_report(self.project,self.p,'full',self.today)
 def test_render_escapes_input(self):
  self.p['page_units'][0]['headline']='<script>alert(1)</script>'
  r,h=page_report(self.project,self.p,'full',self.today)
  self.assertNotIn('<script>',h);self.assertIn('&lt;script&gt;',h)
 def test_semantics_not_fake_pass(self):
  r,h=page_report(self.project,self.p,'full',self.today)
  self.assertTrue(all(x['copy_visual_fidelity']=='NOT_REVIEWED' for x in r['units']));self.assertEqual(r['generated_images'],0)
 def test_draft_binding_flagged(self):
  self.p['page_units'][0]['claim_ids']=['C-04']
  r,h=page_report(self.project,self.p,'full',self.today)
  self.assertTrue(any(x['code']=='CLAIMS_NOT_APPROVED' for x in r['issues']))
 def test_edm_no_send(self):
  r,h=edm_html(self.p,self.today);self.assertFalse(r['send_ready']);self.assertFalse(r['sent'])
 def test_edm_javascript_rejected(self):
  self.p['edm']['cta_url']='javascript:alert(1)';r,h=edm_html(self.p,self.today)
  self.assertNotIn('href=',h);self.assertFalse(r['cta_configured'])
 def test_edm_copy_conditions(self):
  c=self.approved();c.update(status='conditional',conditions='テスト条件下のみ');self.p['claims'][0]=c
  r,h=edm_html(self.p,self.today);self.assertIn('テスト条件下のみ',h)
 def test_freshness_is_dynamic(self):
  self.p['state']['state_as_of']='2026-08-01';self.p['state']['freshness_days']=7
  self.assertEqual(resolve(self.p,'content',date(2026,8,8))['effective_freshness'],'current')
  self.assertEqual(resolve(self.p,'content',date(2026,8,9))['effective_freshness'],'stale')
 def test_unknown_freshness(self):self.assertEqual(resolve(self.p,'content',self.today)['effective_freshness'],'unknown')
 def test_source_delta_nochange(self):
  s=snapshot(self.project,self.p,'content');self.assertEqual(delta(s,s)['changed'],[])
 def test_relevant_source_change(self):
  a=snapshot(self.project,self.p,'content');(self.project/'product-brief.md').write_text('Updated fixture')
  b=snapshot(self.project,self.p,'content');self.assertEqual(delta(a,b)['changed'],['product-brief.md'])
 def test_unrelated_source_not_loaded(self):
  a=snapshot(self.project,self.p,'content');(self.project/'creators.csv').write_text('irrelevant\n')
  self.assertEqual(a,snapshot(self.project,self.p,'content'))
 def test_asset_change_detected(self):
  self.p['page_units'][0]['asset_path']='asset.png';(self.project/'asset.png').write_bytes(b'first')
  a=snapshot(self.project,self.p,'content');(self.project/'asset.png').write_bytes(b'second')
  self.assertEqual(delta(a,snapshot(self.project,self.p,'content'))['changed'],['asset.png'])
 def test_source_deletion_detected(self):self.assertEqual(delta({'a':'hash'}, {})['removed'],['a'])
 def test_run_no_input_writes(self):
  before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.project.iterdir()}
  run('content',self.project,self.base/'out','full',self.today)
  after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.project.iterdir()}
  self.assertEqual(before,after)
 def test_output_isolation(self):
  out=self.base/'out';run('content',self.project,out,'full',self.today)
  self.p['project_id']='other-project';self.mutate(self.p)
  with self.assertRaises(ValueError):run('content',self.project,out,'full',self.today)
 def test_output_cannot_be_input(self):
  with self.assertRaises(ValueError):run('content',self.project,self.project/'out','full',self.today)
 def test_repeat_run_idempotent_after_first_delta(self):
  out=self.base/'out'
  run('content',self.project,out,'full',self.today);second=run('content',self.project,out,'full',self.today)
  before={p.name:p.read_bytes() for p in out.iterdir()}
  third=run('content',self.project,out,'full',self.today)
  self.assertEqual(second,third);self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
 def test_all_five_flows(self):
  for task in ('insights','content','campaign','edm','influencer'):
   r=run(task,self.project,self.base/task,'full',self.today);self.assertFalse(r['publication_ready'])
 def test_csv_formula_escaped(self):
  f=self.base/'safe.csv';write_csv(f,[{'x':'=1+1'}],['x']);self.assertIn("'=1+1",f.read_text(encoding='utf-8-sig'))
 def test_doctor_ready(self):self.assertEqual(doctor(ROOT)['status'],'LOCAL_RUNTIME_READY')
 def test_installer_repo_local(self):
  r=self.base/'mini';(r/'skills/x').mkdir(parents=True);(r/'skills/x/SKILL.md').write_text('hello')
  self.assertEqual(install(r),['x']);self.assertEqual(install(r,True),['x'])
 def test_installer_respects_local_edits(self):
  r=self.base/'mini';(r/'skills/x').mkdir(parents=True);(r/'skills/x/SKILL.md').write_text('hello');install(r)
  (r/'.agents/skills/x/SKILL.md').write_text('my edits');(r/'skills/x/SKILL.md').write_text('upstream edit')
  with self.assertRaises(ValueError):install(r)
 @unittest.skipIf(os.name=='nt','Symlink permissions vary on Windows')
 def test_installer_parent_symlink_rejected(self):
  r=self.base/'mini';(r/'skills/x').mkdir(parents=True);(r/'skills/x/SKILL.md').write_text('hello')
  outside=self.base/'outside';outside.mkdir();(r/'.agents').symlink_to(outside,target_is_directory=True)
  with self.assertRaises(ValueError):install(r)
 def test_secret_scanner(self):
  r=self.base/'scan';r.mkdir();(r/'bad.txt').write_text('gh'+'p_'+'a'*40)
  self.assertTrue(findings(r,['bad.txt']))
 def test_home_path_scanner(self):
  r=self.base/'scan';r.mkdir();(r/'bad.txt').write_text('/Us'+'ers/'+'someone/private/')
  self.assertTrue(findings(r,['bad.txt']))
 def test_custom_private_patterns(self):
  r=self.base/'scan';r.mkdir();(r/'bad.txt').write_text('Launch-Candidate-Secret')
  self.assertTrue(findings(r,['bad.txt'],['Launch-Candidate']))
 def test_export_exact_files_only(self):
  dest=self.base/'export';r=export(ROOT,dest)
  self.assertFalse((dest/'.git').exists());self.assertFalse((dest/'outputs').exists());self.assertEqual(r['file_count'],len(release_files(ROOT)))
 def test_export_refuses_overwrite(self):
  dest=self.base/'exists';dest.mkdir()
  with self.assertRaises(ValueError):export(ROOT,dest)
 def test_export_refuses_changed_bytes(self):
  mini=self.base/'release';shutil.copytree(ROOT,mini,ignore=shutil.ignore_patterns('outputs','.agents','__pycache__'))
  (mini/'kit.json').write_text('{}')
  with self.assertRaises(ValueError):export(mini,self.base/'changed')
 def test_bootstrap_private_no_fork(self):
  cmds=plan('example-owner/marketing-ai-skills-kit',self.base/'new')
  joined=' '.join(' '.join(c) for c in cmds)
  self.assertIn('--private',joined);self.assertNotIn('--public',joined);self.assertNotIn('--mirror',joined);self.assertNotIn('fork',joined)
 def test_bootstrap_bad_name(self):
  with self.assertRaises(ValueError):plan('repo; rm -rf /',self.base/'new')
 def test_skills_have_metadata_and_bundled_commands(self):
  for f in (ROOT/'skills').glob('*/SKILL.md'):
   text=f.read_text(encoding='utf-8');self.assertTrue(text.startswith('---\nname:'));self.assertIn('description:',text);self.assertIn('scripts/run.py',text)

if __name__=='__main__':unittest.main()
