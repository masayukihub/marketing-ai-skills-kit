#!/usr/bin/env python3
"""Hash only explicitly allowlisted, tracked files. Never walk disk to discover a release."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
from sanitize_check import findings
ROOT=Path(__file__).resolve().parents[1]
MANIFEST='distribution/manifest.json'
ALLOWLIST='distribution/allowlist.txt'

def hashes(root:Path)->dict:
 allowlist=root/ALLOWLIST
 if allowlist.is_symlink():raise ValueError('Unsafe allowlist')
 names=[n.strip() for n in allowlist.read_text(encoding='utf-8').splitlines() if n.strip() and not n.startswith('#')]
 if not names or len(names)!=len(set(names)) or MANIFEST in names or ALLOWLIST not in names:raise ValueError('Invalid explicit allowlist')
 try:
  top=subprocess.run(['git','-C',str(root),'rev-parse','--show-toplevel'],capture_output=True,text=True,check=True).stdout.strip()
  tracked=set(subprocess.run(['git','-C',str(root),'ls-files','-z'],capture_output=True,text=True,check=True).stdout.split('\0')) if Path(top).resolve()==root.resolve() else None
 except (FileNotFoundError,subprocess.CalledProcessError):tracked=None
 if tracked is None:tracked=set(json.loads((root/MANIFEST).read_text(encoding='utf-8'))['files'])
 if set(names)-tracked:raise ValueError('UNTRACKED_RELEASE_FILE: stage and review explicit new files first')
 issues=findings(root,names)
 if issues:raise ValueError('Release safety check failed: '+json.dumps(issues))
 return {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in sorted(names)}

def main():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group();g.add_argument('--write',action='store_true');g.add_argument('--check',action='store_true');a=p.parse_args()
 content={'schema_version':'1.0','version':json.loads((ROOT/'kit.json').read_text())['version'],'export_mode':'exact_file_allowlist','copy_git_history':False,'files':hashes(ROOT)}
 if a.check:
  if json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))!=content:raise ValueError('DISTRIBUTION_LOCK_STALE')
  print('DISTRIBUTION_LOCK_VERIFIED')
 elif a.write:
  (ROOT/MANIFEST).write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('LOCK_UPDATED_FOR_REVIEW: no publication performed')
 else:
  old=json.loads((ROOT/MANIFEST).read_text()) if (ROOT/MANIFEST).exists() else {'files':{}}
  print(json.dumps({'added':sorted(set(content['files'])-set(old['files'])),'changed':sorted(k for k,v in content['files'].items() if k in old['files'] and v!=old['files'][k]),'removed':sorted(set(old['files'])-set(content['files']))},indent=2))

if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError) as exc:raise SystemExit(str(exc))
