#!/usr/bin/env python3
"""Explicitly propose a new distribution lock after reviewing changes; never publish."""
from pathlib import Path
import argparse
import hashlib
import json
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'outputs','projects','private-runtime','.agents','.git','.venv','__pycache__','dist','build','.pytest_cache'}
MANIFEST='distribution/manifest.json'

def hashes(root:Path)->dict:
 result={}
 for p in sorted(root.rglob('*')):
  rel=p.relative_to(root)
  if set(rel.parts)&EXCLUDE or not p.is_file() or rel.as_posix()==MANIFEST or p.name=='brand.local.json' or (p.name.startswith('.env') and p.name!='.env.example'):continue
  if p.is_symlink():raise ValueError('Symlinks cannot enter the public distribution')
  result[rel.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');a=p.parse_args()
 content={'schema_version':'1.0','version':json.loads((ROOT/'kit.json').read_text())['version'],'export_mode':'exact_file_allowlist','copy_git_history':False,'files':hashes(ROOT)}
 if a.write:
  (ROOT/MANIFEST).write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('LOCK_UPDATED_FOR_REVIEW: no publication performed')
 else:
  old=json.loads((ROOT/MANIFEST).read_text()) if (ROOT/MANIFEST).exists() else {'files':{}}
  print(json.dumps({'added':sorted(set(content['files'])-set(old['files'])),'changed':sorted(k for k,v in content['files'].items() if k in old['files'] and v!=old['files'][k]),'removed':sorted(set(old['files'])-set(content['files']))},indent=2))
