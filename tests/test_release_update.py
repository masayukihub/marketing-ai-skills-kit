import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from build_release import archive,export
from lock_distribution import hashes
from update import read_archive,preview,apply_update,sha,MANIFEST
from install import install
from sanitize_check import findings


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name).resolve()
        self.old=self.make_release(self.base/'old','0.1.0-rc2','old runtime')
        self.new=self.make_release(self.base/'new','0.2.0-rc1','new runtime')
        self.zip=self.base/'release.zip'
        self.checksum=archive(self.new,self.zip)['sha256']
        self.data,self.meta=read_archive(self.zip,self.checksum)

    def tearDown(self):self.tmp.cleanup()

    def make_release(self,root,version,text):
        (root/'kit').mkdir(parents=True);(root/'distribution').mkdir()
        (root/'kit.json').write_text(json.dumps({'version':version,'python':'>=3.10'}),encoding='utf-8')
        (root/'kit/core.py').write_text('# '+text+'\n',encoding='utf-8')
        self.lock(root,version)
        return root

    def lock(self,root,version):
        names=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix()!=MANIFEST)
        manifest={'schema_version':'1.0','version':version,'copy_git_history':False,'export_mode':'exact_file_allowlist',
                  'files':{n:sha((root/n).read_bytes()) for n in names}}
        (root/MANIFEST).write_text(json.dumps(manifest),encoding='utf-8')

    def test_deterministic_zip(self):
        other=self.base/'second.zip';archive(self.new,other)
        self.assertEqual(self.zip.read_bytes(),other.read_bytes())

    def test_checksum_mismatch(self):
        with self.assertRaisesRegex(ValueError,'CHECKSUM_MISMATCH'):read_archive(self.zip,'0'*64)

    def test_dryrun_no_changes(self):
        before={p.relative_to(self.old).as_posix():p.read_bytes() for p in self.old.rglob('*') if p.is_file()}
        plan=preview(self.old,self.data,self.meta,self.checksum)
        self.assertEqual(plan['status'],'UPDATE_REVIEW_REQUIRED')
        self.assertEqual(before,{p.relative_to(self.old).as_posix():p.read_bytes() for p in self.old.rglob('*') if p.is_file()})

    def test_apply_preserves_user_data_and_can_rollback(self):
        old_zip=self.base/'old.zip';old_hash=archive(self.old,old_zip)['sha256']
        protected=['projects/real/brief.md','outputs/real/review.html','config/brand.local.json','.env','.agents/skills/mine/SKILL.md']
        for name in protected:
            p=self.old/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('private user bytes',encoding='utf-8')
        plan=preview(self.old,self.data,self.meta,self.checksum)
        r=apply_update(self.old,self.data,self.meta,self.checksum,plan['plan_sha256'])
        self.assertEqual(r['status'],'APPLIED_LOCALLY')
        self.assertTrue((self.old/r['backup']/MANIFEST).is_file())
        old_data,old_meta=read_archive(old_zip,old_hash)
        with self.assertRaisesRegex(ValueError,'ROLLBACK_FLAG'):preview(self.old,old_data,old_meta,old_hash)
        plan=preview(self.old,old_data,old_meta,old_hash,True)
        apply_update(self.old,old_data,old_meta,old_hash,plan['plan_sha256'],True)
        self.assertEqual(json.loads((self.old/'kit.json').read_text())['version'],'0.1.0-rc2')
        self.assertTrue(all((self.old/n).read_text()=='private user bytes' for n in protected))

    def test_local_modified_file_blocks_all_writes(self):
        (self.old/'kit/core.py').write_text('my edits',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'LOCAL_MODIFICATION_CONFLICT'):
            preview(self.old,self.data,self.meta,self.checksum)
        self.assertFalse((self.old/'.kit-backups').exists())

    def test_stale_plan_blocks(self):
        plan=preview(self.old,self.data,self.meta,self.checksum)
        with self.assertRaisesRegex(ValueError,'PLAN_CHANGED'):
            apply_update(self.old,self.data,self.meta,self.checksum,'0'*64)
        self.assertFalse((self.old/'.kit-backups').exists())

    def test_untracked_collision_blocks(self):
        self.data['kit/new.py']=b'new'
        (self.old/'kit/new.py').write_bytes(b'User file')
        with self.assertRaisesRegex(ValueError,'COLLISION'):
            preview(self.old,self.data,self.meta,self.checksum)

    def test_repeat_update_up_to_date(self):
        plan=preview(self.old,self.data,self.meta,self.checksum)
        apply_update(self.old,self.data,self.meta,self.checksum,plan['plan_sha256'])
        self.assertEqual(preview(self.old,self.data,self.meta,self.checksum)['status'],'UP_TO_DATE')

    def test_partial_failure_restores_managed_files(self):
        before={n:(self.old/n).read_bytes() for n in self.meta['files']}
        plan=preview(self.old,self.data,self.meta,self.checksum)
        original=Path.open;failed=False
        def fail_once(path,mode='r',*args,**kwargs):
            nonlocal failed
            if path==self.old/'kit/core.py' and mode=='wb' and not failed:
                failed=True;raise OSError('synthetic write failure')
            return original(path,mode,*args,**kwargs)
        with patch.object(Path,'open',fail_once),self.assertRaises(OSError):
            apply_update(self.old,self.data,self.meta,self.checksum,plan['plan_sha256'])
        self.assertEqual(before,{n:(self.old/n).read_bytes() for n in before})

    def malicious_zip(self,names):
        path=self.base/'bad.zip'
        with zipfile.ZipFile(path,'w') as z:
            for name,content in names:z.writestr(name,content)
        return path,sha(path.read_bytes())

    def test_zip_traversal_rejected(self):
        p,h=self.malicious_zip([('../escape.py','bad')])
        with self.assertRaisesRegex(ValueError,'Unsafe archive'):read_archive(p,h)

    def test_zip_case_collision_rejected(self):
        p,h=self.malicious_zip([('README.md','one'),('readme.md','two')])
        with self.assertRaisesRegex(ValueError,'Invalid archive entries'):read_archive(p,h)

    def test_windows_device_name_rejected(self):
        p,h=self.malicious_zip([('kit/CON.txt','bad')])
        with self.assertRaisesRegex(ValueError,'Unsafe archive'):read_archive(p,h)

    @unittest.skipIf(os.name=='nt','Symlink privileges vary')
    def test_archive_symlink_destination_rejected(self):
        link=self.base/'linked';link.symlink_to(self.base/'new',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'Symlink'):archive(self.new,link/'unexpected.zip')

    def test_zip_extra_file_rejected(self):
        p,h=self.malicious_zip([*self.data.items(),('extra.txt','not allowlisted')])
        with self.assertRaisesRegex(ValueError,'Unexpected'):read_archive(p,h)

    def test_zip_symlink_rejected(self):
        p=self.base/'bad.zip';info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=0o120777 << 16
        with zipfile.ZipFile(p,'w') as z:z.writestr(info,'target')
        with self.assertRaisesRegex(ValueError,'Unsafe archive'):read_archive(p,sha(p.read_bytes()))

    def test_protected_release_paths_rejected(self):
        for name in ['projects/real.txt','outputs/report.md','local-logs/latest.log','.kit-backups/old.md','config/brand.local.json','Projects/real.txt','.env.local','logs/note.md']:
            p=self.base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('synthetic test')
            self.assertTrue(findings(self.base,[name]),name)

    def test_python_incompatible_release_rejected(self):
        (self.new/'kit.json').write_text(json.dumps({'version':'0.2.0-rc1','python':'>=99.0'}))
        self.lock(self.new,'0.2.0-rc1')
        path=self.base/'future.zip';checksum=archive(self.new,path)['sha256']
        with self.assertRaisesRegex(ValueError,'PYTHON_VERSION'):read_archive(path,checksum)

    def test_lock_uses_explicit_tracked_list_not_disk(self):
        root=self.base/'tracked';(root/'distribution').mkdir(parents=True)
        subprocess.run(['git','init',str(root)],capture_output=True,check=True)
        (root/'distribution/allowlist.txt').write_text('distribution/allowlist.txt\nreadme.md\n',encoding='utf-8')
        (root/'readme.md').write_text('safe fixture')
        subprocess.run(['git','-C',str(root),'add','distribution/allowlist.txt','readme.md'],check=True)
        (root/'logs').mkdir();(root/'logs/local.log').write_text('private log')
        (root/'untracked.md').write_text('untracked')
        self.assertEqual(set(hashes(root)),{'distribution/allowlist.txt','readme.md'})
        with (root/'distribution/allowlist.txt').open('a',encoding='utf-8') as f:f.write('untracked.md\n')
        with self.assertRaisesRegex(ValueError,'UNTRACKED_RELEASE'):hashes(root)

    def test_install_checks_all_conflicts_before_mutating(self):
        root=self.base/'install'
        for name in ('a','z'):
            p=root/'skills'/name/'SKILL.md';p.parent.mkdir(parents=True);p.write_text('v1')
        install(root)
        (root/'skills/a/SKILL.md').write_text('v2')
        (root/'.agents/skills/z/SKILL.md').write_text('user edit')
        with self.assertRaises(ValueError):install(root)
        self.assertEqual((root/'.agents/skills/a/SKILL.md').read_text(),'v1')

    @unittest.skipIf(os.name=='nt','Symlink privileges vary')
    def test_target_symlink_blocks_update(self):
        link=self.base/'linked';link.symlink_to(self.old,target_is_directory=True)
        with self.assertRaises(ValueError):preview(link,self.data,self.meta,self.checksum)


if __name__=='__main__':unittest.main()
