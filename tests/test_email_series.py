from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from kit.common import digest, load_json, write_json
from kit.truth import load_project
from kit.context import snapshot, delta, resolve
from kit.email_series import build_series, validate_series, impact
from run import run


class SeriesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base/'input'
        shutil.copytree(ROOT/'examples/edm-series', self.root)
        self.project = load_project(self.root)
        self.today = date(2026, 9, 20)

    def tearDown(self):
        self.temp.cleanup()

    def build(self, previous=None):
        return build_series(self.root, self.project, self.today, previous)

    def save(self):
        write_json(self.root/'project.json', self.project)

    def item(self, report, item_id):
        return next(i for i in report['review_items'] if i['item_id'] == item_id)

    def approve(self, item):
        self.project['reviews'].append({'project_id': self.project['project_id'], 'item_id': item['item_id'],
            'fingerprint': item['fingerprint'], 'decision': 'APPROVE', 'reviewer': 'Synthetic reviewer',
            'reviewed_at': self.today.isoformat(), 'evidence_checked': True})

    def test_run_writes_real_pages_without_input_changes(self):
        before = {p.name:p.read_bytes() for p in self.root.iterdir()}
        out = self.base/'out'
        run('edm-series', self.root, out, 'full', self.today)
        self.assertTrue((out/'review.html').is_file())
        self.assertEqual(len(list((out/'emails').glob('*.html'))), 3)
        self.assertTrue((out/'human-review.csv').is_file())
        self.assertEqual(before, {p.name:p.read_bytes() for p in self.root.iterdir()})
        report = load_json(out/'series-review.json')
        self.assertFalse(report['send_ready'])
        self.assertEqual(report['shared_comments'], 'NOT_BUNDLED')

    def test_repeated_run_no_fake_changes(self):
        out = self.base/'out'
        run('edm-series', self.root, out, 'full', self.today)
        second = run('edm-series', self.root, out, 'full', self.today)
        self.assertFalse(any(second['source_delta'][key] for key in ('new','changed','removed')))
        self.assertEqual(load_json(out/'series-review.json')['impact']['changes'], [])

    def test_only_private_module_changes_one_email(self):
        old, _ = self.build()
        self.project['edm_series']['modules'][1]['body'] += ' 新しい候補。'
        new, _ = self.build(old)
        self.assertEqual([c['email_id'] for c in new['impact']['changes']], ['imagine'])
        self.assertEqual(new['impact']['changes'][0]['changed_modules'], ['idea'])

    def test_handoff_keeps_stale_reviews_on_unchanged_resume(self):
        old, _ = self.build()
        self.approve(self.item(old, 'series:imagine:module:idea:body'))
        self.project['edm_series']['modules'][1]['body'] += ' Revised candidate.'
        self.save()
        out = self.base/'out'
        run('edm-series', self.root, out, 'full', self.today)
        run('edm-series', self.root, out, 'full', self.today)
        report = load_json(out/'series-review.json')
        self.assertEqual(report['impact']['changes'], [])
        self.assertEqual(report['review_summary']['stale_review_count'], 1)
        self.assertEqual(report['review_summary']['stale_email_ids'], ['imagine'])
        handoff = (out/'HANDOFF.md').read_text(encoding='utf-8')
        self.assertIn('series-review.json and scoped-review.json', handoff)
        self.assertIn('Stale reviews: 1\nAffected emails: imagine', handoff)
        self.assertIn('失效审核：1 项', (out/'review.html').read_text(encoding='utf-8'))

    def test_shared_footer_change_affects_all_users(self):
        old, _ = self.build()
        self.project['edm_series']['modules'][-1]['body'] += ' Updated candidate.'
        new, _ = self.build(old)
        self.assertEqual(len(new['impact']['changes']), 3)
        self.assertTrue(all(c['changed_modules'] == ['shared-footer'] for c in new['impact']['changes']))

    def test_reorder_changes_email_not_module_hash(self):
        old, _ = self.build()
        self.project['edm_series']['emails'][1]['module_ids'] = ['details', 'idea', 'shared-footer']
        new, _ = self.build(old)
        change = new['impact']['changes'][0]
        self.assertTrue(change['order_changed'])
        self.assertEqual(change['changed_modules'], [])

    def test_removed_email_gets_superseded_page(self):
        old, _ = self.build()
        self.project['edm_series']['emails'].pop()
        new, pages = self.build(old)
        self.assertEqual(new['impact']['changes'][0]['change'], 'removed')
        self.assertIn('SUPERSEDED', pages['emails/compare.html'])

    def test_other_project_snapshot_refused(self):
        old, _ = self.build()
        old['project_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'MISMATCH'):
            self.build(old)

    def test_subject_option_switch_invalidates_header_only(self):
        old, _ = self.build()
        self.project['edm_series']['emails'][0]['selected_subject'] = 'scene'
        new, _ = self.build(old)
        change = new['impact']['changes'][0]
        self.assertTrue(change['subject_changed'])
        self.assertEqual(change['changed_modules'], [])

    def test_review_only_changed_copy_goes_stale(self):
        old, _ = self.build()
        changed = 'series:imagine:module:idea:body'
        stable = 'series:imagine:module:details:body'
        for iid in (changed, stable):
            self.approve(self.item(old, iid))
        self.project['edm_series']['modules'][1]['body'] += ' More.'
        new, _ = self.build()
        self.assertEqual(self.item(new, changed)['status'], 'STALE_REVIEW')
        self.assertEqual(self.item(new, stable)['status'], 'APPROVED_INTERNAL_ONLY')

    def test_whole_email_cannot_skip_child_review(self):
        old, _ = self.build()
        item = self.item(old, 'series:imagine:whole-email')
        self.approve(item)
        new, _ = self.build()
        self.assertEqual(self.item(new, item['item_id'])['status'], 'APPROVAL_BLOCKED')

    def test_history_not_truth_and_change_scoped(self):
        old, _ = self.build()
        before = deepcopy(self.project['facts'])
        (self.root/'history.md').write_text('Changed structure fixture', encoding='utf-8')
        new, _ = self.build(old)
        self.assertEqual([c['email_id'] for c in new['impact']['changes']], ['discover'])
        self.assertEqual(self.project['facts'], before)
        self.assertEqual(new['emails'][0]['inheritance']['intro']['authority'], 'STRUCTURE_ONLY_NOT_CURRENT_TRUTH')

    def test_source_byte_changes_reopen_bound_copy(self):
        old, _ = self.build()
        iid = 'series:discover:module:intro:body'
        self.approve(self.item(old, iid))
        (self.root/'source.md').write_text('Changed evidence', encoding='utf-8')
        new, _ = self.build()
        self.assertEqual(self.item(new, iid)['status'], 'STALE_REVIEW')

    def test_registered_history_in_source_delta(self):
        before = snapshot(self.root, self.project, 'edm-series')
        (self.root/'history.md').write_text('Changed', encoding='utf-8')
        self.assertEqual(delta(before, snapshot(self.root, self.project, 'edm-series'))['changed'], ['history.md'])

    def test_edm_task_blocker_is_visible_to_series(self):
        self.assertEqual(resolve(self.project, 'edm-series', self.today)['blockers'][0]['id'], 'REAL-ASSETS')

    def test_missing_images_stay_missing(self):
        report, pages = self.build()
        self.assertIn('ASSET NOT PROVIDED', pages['emails/discover.html'])
        self.assertIn('ASSET_MISSING', self.item(report, 'series:discover:module:intro:asset')['blockers'])
        self.assertEqual(len(report['visual_inventory']['missing_ai_concept_email_ids']), 3)
        self.assertFalse(report['visual_inventory']['complete_visual_approved'])

    def test_invalid_url_not_linked_or_approved(self):
        self.project['edm_series']['modules'][3]['cta_url'] = 'javascript:alert(1)'
        old, pages = self.build()
        iid = 'series:imagine:module:details:cta_url'
        self.approve(self.item(old, iid))
        new, _ = self.build()
        self.assertNotIn('href="javascript:', pages['emails/imagine.html'])
        self.assertEqual(self.item(new, iid)['status'], 'APPROVAL_BLOCKED')

    def test_draft_claim_cannot_be_approved(self):
        self.project['claims'][0]['status'] = 'draft'
        old, _ = self.build()
        iid = 'series:discover:module:intro:body'
        self.approve(self.item(old, iid))
        new, _ = self.build()
        self.assertEqual(self.item(new, iid)['status'], 'APPROVAL_BLOCKED')

    def test_html_and_comment_values_are_escaped(self):
        self.project['edm_series']['modules'][1]['body'] = '<script>alert(1)</script>'
        _, pages = self.build()
        self.assertIn('&lt;script&gt;', pages['emails/imagine.html'])
        self.assertNotIn('<script>', pages['emails/imagine.html'])

    def test_missing_subject_options_are_not_invented(self):
        report, _ = self.build()
        self.assertEqual(len(report['emails'][1]['subject_options']), 1)
        self.assertIn({'email_id':'imagine','code':'SUBJECT_OPTIONS_BELOW_THREE'}, report['warnings'])

    def test_repeated_purchase_reason_warns(self):
        series = self.project['edm_series']
        series['emails'][1]['purchase_reason'] = series['emails'][0]['purchase_reason']
        report, _ = self.build()
        self.assertIn({'email_id':'imagine','code':'REPEATED_PURCHASE_REASON'}, report['warnings'])

    def test_unsafe_ids_missing_footer_or_unknown_module_refused(self):
        for mutation in ('unsafe', 'missing-footer', 'unknown', 'duplicate'):
            project = deepcopy(self.project)
            email = project['edm_series']['emails'][0]
            if mutation == 'unsafe': email['id'] = '../escape'
            elif mutation == 'missing-footer': email['module_ids'].pop()
            elif mutation == 'unknown': email['module_ids'][0] = 'missing'
            else: email['module_ids'].insert(0, 'intro')
            with self.assertRaises(ValueError, msg=mutation): validate_series(project)

    def test_failed_series_preflight_does_not_modify_outputs(self):
        out = self.base/'out'
        run('edm-series', self.root, out, 'full', self.today)
        before = (out/'review.html').read_bytes()
        self.project['edm_series']['emails'][0]['module_ids'].pop()
        self.save()
        with self.assertRaises(ValueError):run('edm-series', self.root, out, 'full', self.today)
        self.assertEqual((out/'review.html').read_bytes(), before)

    def add_comment(self):
        report, _ = self.build()
        module = self.project['edm_series']['modules'][-1]
        comment = {'id':'comment-1','email_id':'discover','module_id':module['id'],'kind':'copy','field':'body',
                   'module_hash':report['emails'][0]['module_hashes'][module['id']],
                   'before':module['body'],'after':'Proposed footer text','approved':True,'role':'owner'}
        self.project['edm_series']['comments'].append(comment)

    def test_comment_plan_never_applies_or_approves(self):
        self.add_comment()
        before = deepcopy(self.project)
        report, _ = self.build()
        plan = report['comment_plan'][0]
        self.assertEqual(plan['status'], 'READY_FOR_HUMAN_REVIEW')
        self.assertEqual(len(plan['affected_email_ids']), 3)
        self.assertFalse(plan['applied']);self.assertFalse(plan['approval_granted'])
        self.assertEqual(self.project, before)

    def test_stale_comment_blocked(self):
        self.add_comment()
        self.project['edm_series']['modules'][-1]['body'] += ' New version.'
        report, _ = self.build()
        self.assertIn('STALE_COMMENT', report['comment_plan'][0]['reasons'])
        self.assertIn('BEFORE_MISMATCH', report['comment_plan'][0]['reasons'])

    def test_unknown_comment_target_blocked(self):
        self.add_comment()
        self.project['edm_series']['comments'][0]['email_id'] = 'unknown'
        report, _ = self.build()
        self.assertIn('TARGET_NOT_FOUND', report['comment_plan'][0]['reasons'])

    def add_visual(self):
        # Header fixture, not a semantically validated image; runtime never claims pixel QA.
        (self.root/'fixture.png').write_bytes(b'\x89PNG\r\n\x1a\n' + b'fixture')
        report, _ = self.build()
        email = report['emails'][0]
        entry = {'email_id':email['id'],'kind':'ai_concept','path':'fixture.png','sha256':digest(self.root/'fixture.png'),
                 'fingerprint':email['fingerprint'],'module_ids':email['module_ids'],
                 'asset_rights':'user_confirmed','generation_record':'synthetic-record-not-real-generation'}
        self.project['edm_series']['visuals'].append(entry)

    def test_visual_file_check_not_pixel_or_generation_approval(self):
        self.add_visual()
        report, _ = self.build()
        record = report['visual_inventory']['entries'][0]
        self.assertEqual(record['status'], 'FILE_CHECKED_REVIEW_REQUIRED')
        self.assertEqual(record['pixel_decoding'], 'NOT_CHECKED')
        self.assertFalse(report['visual_inventory']['complete_visual_approved'])

    def test_visual_stale_hash_coverage_rights_and_kind_are_distinct(self):
        self.add_visual()
        visual = self.project['edm_series']['visuals'][0]
        visual.update(fingerprint='old',sha256='wrong',module_ids=['intro'],asset_rights='unknown')
        report, _ = self.build()
        self.assertEqual(set(report['visual_inventory']['entries'][0]['reasons']),
                         {'STALE_VISUAL','IMAGE_HASH_MISMATCH','INCOMPLETE_OR_WRONG_ORDER','ASSET_RIGHTS_UNVERIFIED'})

    def test_html_screenshot_is_not_ai_concept(self):
        self.add_visual()
        self.project['edm_series']['visuals'][0]['kind'] = 'html_render'
        report, _ = self.build()
        self.assertIn('discover', report['visual_inventory']['missing_ai_concept_email_ids'])

    def test_visual_escape_refused(self):
        self.add_visual()
        self.project['edm_series']['visuals'][0]['path'] = '../outside.png'
        with self.assertRaises(ValueError):self.build()


if __name__ == '__main__': unittest.main()
