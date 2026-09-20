#!/usr/bin/env python3
"""Export exactly reviewed bytes into an empty destination; never copy .git or user data."""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT))
from sanitize_check import findings
from kit.common import reject_symlinks

def export(root:Path,dest:Path,private_patterns:list[str]|None=None)->dict:
 reject_symlinks(root);reject_symlinks(dest)
 root=root.resolve();dest=dest.resolve()
 if dest==root or dest.is_relative_to(root) or root.is_relative_to(dest):raise ValueError('Export destination must be outside the source tree')
 if dest.exists():raise ValueError('Destination already exists; no files were overwritten')
 manifest_path=root/'distribution/manifest.json';raw=manifest_path.read_bytes();manifest=json.loads(raw)
 files=manifest['files']
 if not files or manifest.get('copy_git_history') is not False or manifest.get('export_mode')!='exact_file_allowlist':raise ValueError('Invalid release manifest')
 if not manifest.get('version') or manifest.get('version')!=json.loads((root/'kit.json').read_text(encoding='utf-8')).get('version'):raise ValueError('Release version mismatch')
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

def archive(export_dir:Path,zip_path:Path)->dict:
 """ZIP bytes are deterministic: sorted entries, fixed timestamps and permissions."""
 reject_symlinks(export_dir);reject_symlinks(zip_path);reject_symlinks(zip_path.with_suffix(zip_path.suffix+'.sha256'))
 manifest=json.loads((export_dir/'distribution/manifest.json').read_text(encoding='utf-8'))
 names=sorted([*manifest['files'],'distribution/manifest.json'])
 if zip_path.exists() or zip_path.with_suffix(zip_path.suffix+'.sha256').exists():raise ValueError('Archive output already exists')
 if zip_path.resolve().is_relative_to(export_dir.resolve()):raise ValueError('Archive must be outside export directory')
 if findings(export_dir,names):raise ValueError('Archive safety check failed')
 payload={name:(export_dir/name).read_bytes() for name in names}
 if any(hashlib.sha256(payload[name]).hexdigest()!=expected for name,expected in manifest['files'].items()):raise ValueError('Archive contains unreviewed bytes')
 zip_path.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(zip_path,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for name in names:
   info=zipfile.ZipInfo(name,date_time=(2020,1,1,0,0,0));info.create_system=3;info.external_attr=0o100644 << 16;info.compress_type=zipfile.ZIP_DEFLATED
   z.writestr(info,payload[name])
 checksum=hashlib.sha256(zip_path.read_bytes()).hexdigest()
 zip_path.with_suffix(zip_path.suffix+'.sha256').write_text(checksum+'  '+zip_path.name+'\n',encoding='utf-8')
 return {'sha256':checksum,'file_count':len(payload),'published':False}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dest',type=Path,required=True);p.add_argument('--zip',type=Path);p.add_argument('--private-policy',type=Path);a=p.parse_args()
 try:
  patterns=json.loads(a.private_policy.read_text())['deny_patterns'] if a.private_policy else []
  result=export(ROOT,a.dest,patterns)
  if a.zip:result['archive']=archive(a.dest,a.zip)
  print(json.dumps(result,ensure_ascii=False))
 except (OSError,ValueError,KeyError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(2)
