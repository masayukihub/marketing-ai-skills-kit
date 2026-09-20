#!/usr/bin/env python3
"""Export exactly reviewed bytes into an empty destination; never copy .git or user data."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from sanitize_check import findings

def export(root:Path,dest:Path,private_patterns:list[str]|None=None)->dict:
 root=root.resolve();dest=dest.resolve()
 if dest==root or dest.is_relative_to(root) or root.is_relative_to(dest):raise ValueError('Export destination must be outside the source tree')
 if dest.exists():raise ValueError('Destination already exists; no files were overwritten')
 manifest_path=root/'distribution/manifest.json';raw=manifest_path.read_bytes();manifest=json.loads(raw)
 files=manifest['files']
 if not files or manifest.get('copy_git_history') is not False:raise ValueError('Invalid release manifest')
 issues=findings(root,list(files)+['distribution/manifest.json'],private_patterns)
 if issues:raise ValueError('Sanitization failed: '+json.dumps(issues,ensure_ascii=False))
 # Cache verified bytes before writing; do not copy a file that changed after validation.
 data={}
 for name,expected in files.items():
  content=(root/name).read_bytes()
  if hashlib.sha256(content).hexdigest()!=expected:raise ValueError('UNREVIEWED_CHANGE: '+name)
  data[name]=content
 data['distribution/manifest.json']=raw
 dest.mkdir(parents=True)
 for name,content in data.items():
  path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
 return {'status':'EXPORT_COMPLETE','file_count':len(data),'manifest_sha256':hashlib.sha256(raw).hexdigest(),'history_copied':False}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dest',type=Path,required=True);p.add_argument('--private-policy',type=Path);a=p.parse_args()
 try:
  patterns=json.loads(a.private_policy.read_text())['deny_patterns'] if a.private_policy else []
  print(json.dumps(export(ROOT,a.dest,patterns),ensure_ascii=False))
 except (OSError,ValueError,KeyError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(2)
