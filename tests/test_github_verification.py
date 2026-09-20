from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_github import assess, inspect, validate_identity

class GitHubVerificationTests(unittest.TestCase):
    def setUp(self):
        self.repo='demo-owner/marketing-ai-skills-kit'
        self.sha='a'*40
        self.remote={'nameWithOwner':self.repo,'visibility':'PRIVATE',
                     'url':'https://github.com/'+self.repo,'isTemplate':True}
        self.run={'databaseId':1,'headSha':self.sha,'event':'push','status':'completed',
                  'conclusion':'success','url':'https://github.com/'+self.repo+'/actions/runs/1'}
    def result(self,runs):return assess(self.repo,self.sha,self.remote,self.sha,runs)
    def test_pass_requires_success(self):self.assertTrue(self.result([self.run])['all_remote_checks_passed'])
    def test_no_runs_not_pass(self):self.assertEqual(self.result([])['ci_status'],'NOT_STARTED')
    def test_query_unavailable_not_pass(self):self.assertEqual(self.result(None)['ci_status'],'UNAVAILABLE')
    def test_pending_not_pass(self):
        self.run.update(status='in_progress',conclusion=None)
        self.assertEqual(self.result([self.run])['ci_status'],'PENDING')
    def test_skipped_not_pass(self):
        self.run['conclusion']='skipped'
        self.assertFalse(self.result([self.run])['all_remote_checks_passed'])
    def test_failure_not_pass(self):
        self.run['conclusion']='failure'
        self.assertEqual(self.result([self.run])['ci_status'],'NOT_PASSED')
    def test_cancelled_not_pass(self):
        self.run['conclusion']='cancelled'
        self.assertEqual(self.result([self.run])['ci_status'],'NOT_PASSED')
    def test_wrong_commit_not_pass(self):
        self.run['headSha']='b'*40
        self.assertEqual(self.result([self.run])['ci_status'],'NOT_STARTED')
    def test_pr_run_not_pass(self):
        self.run['event']='pull_request'
        self.assertEqual(self.result([self.run])['ci_status'],'NOT_STARTED')
    def test_latest_run_wins(self):
        newer=deepcopy(self.run);newer.update(databaseId=2,conclusion='failure')
        self.assertEqual(self.result([newer,self.run])['ci_status'],'NOT_PASSED')
    def test_public_rejected(self):
        self.remote['visibility']='PUBLIC'
        with self.assertRaisesRegex(ValueError,'REMOTE_NOT_PRIVATE'):self.result([])
    def test_unknown_visibility_rejected(self):
        self.remote.pop('visibility')
        with self.assertRaises(ValueError):self.result([])
    def test_wrong_owner_rejected(self):
        self.remote['nameWithOwner']='different/repo'
        with self.assertRaisesRegex(ValueError,'IDENTITY'):self.result([])
    def test_wrong_head_rejected(self):
        with self.assertRaisesRegex(ValueError,'HEAD_MISMATCH'):
            assess(self.repo,self.sha,self.remote,'b'*40,[])
    def test_wrong_url_rejected(self):
        self.remote['url']='https://example.com/repo'
        with self.assertRaisesRegex(ValueError,'URL_MISMATCH'):self.result([])
    def test_invalid_identity_rejected(self):
        with self.assertRaises(ValueError):validate_identity('owner/repo;bad',self.sha)
    def test_short_commit_rejected(self):
        with self.assertRaises(ValueError):validate_identity(self.repo,'abc123')
    def test_missing_gh_reports_blocked(self):
        with patch('verify_github.shutil.which',return_value=None):
            with self.assertRaisesRegex(ValueError,'CLI_MISSING'):inspect(self.repo,self.sha)
    def test_ci_api_failure_is_not_pass(self):
        responses=[self.remote,{'object':{'sha':self.sha}},subprocess.CalledProcessError(1,['gh'])]
        with patch('verify_github.shutil.which',return_value='/bin/gh'),patch('verify_github.gh_json',side_effect=responses):
            self.assertEqual(inspect(self.repo,self.sha)['ci_status'],'UNAVAILABLE')
    def test_remote_mock_pass(self):
        with patch('verify_github.shutil.which',return_value='/bin/gh'),patch('verify_github.gh_json',side_effect=[self.remote,{'object':{'sha':self.sha}},[self.run]]) as mocked:
            self.assertTrue(inspect(self.repo,self.sha)['all_remote_checks_passed'])
            self.assertIn('--commit',mocked.call_args_list[-1].args[0])
            self.assertIn('--workflow',mocked.call_args_list[-1].args[0])

if __name__=='__main__':unittest.main()
