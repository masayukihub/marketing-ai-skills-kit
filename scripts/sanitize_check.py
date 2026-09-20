#!/usr/bin/env python3
"""Conservative text/path scan, not a guarantee that every confidential fact is detected."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
 'PRIVATE_KEY':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'GITHUB_TOKEN':r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b',
 'API_TOKEN':r'\bsk-[A-Za-z0-9_-]{24,}\b',
 'AWS_KEY':r'\bAKIA[A-Z0-9]{16}\b',
 'BEARER_VALUE':r'(?i)Bearer\s+[A-Za-z0-9._-]{24,}',
 'SECRET_ASSIGNMENT':r'''(?im)^\s*(?:API_KEY|ACCESS_TOKEN|REFRESH_TOKEN|CLIENT_SECRET|PASSWORD|COOKIE)\s*[:=]\s*["']?(?!YOUR_|PLACEHOLDER|<|\$)[A-Za-z0-9_./+=-]{12,}''',
 'PERSONAL_HOME':r'(?:/Users/|/home/)(?!runner/)[a-zA-Z][a-zA-Z0-9_.-]+/',
 'WINDOWS_HOME':r'[A-Za-z]:\\Users\\[^\\\r\n]+',
 'TENANT_DOCUMENT':r'https?://[^/\s]+\.(?:feishu\.cn|larksuite\.com)/(?:docx|wiki|base|drive)/[A-Za-z0-9]+',
 'SIGNED_URL':r'(?i)[?&](?:X-Amz-Signature|access_token|refresh_token|sig)=[A-Za-z0-9%_-]{12,}',
}
BLOCKED_PARTS={'.git','private','private-runtime','raw-private','secrets','local-logs','logs','output','outputs','projects','.kit-backups','.playwright-cli','node_modules','.venv','__pycache__','.agents'}
TEXT_SUFFIXES={'.md','.py','.json','.yaml','.yml','.txt','.sh','.ps1','.csv','.html','.css','.toml','.example'}
ALLOWED_NAMES={'LICENSE','NOTICE','.gitignore','.gitattributes'}

def findings(root:Path,paths:list[str],extra_patterns:list[str]|None=None)->list[dict]:
 errors=[];compiled=[(name,re.compile(pattern)) for name,pattern in PATTERNS.items()]
 compiled += [('PRIVATE_POLICY_'+str(i),re.compile(p,re.I)) for i,p in enumerate(extra_patterns or [])]
 for name in paths:
  rel=Path(name)
  folded_parts={part.casefold() for part in rel.parts}
  if rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name or folded_parts&BLOCKED_PARTS or any(part=='.env' or (part.startswith('.env.') and part!='.env.example') for part in folded_parts) or rel.suffix.casefold()=='.log' or rel.name.casefold()=='brand.local.json':
   errors.append({'path':name,'rule':'DISALLOWED_PATH'});continue
  path=root/rel
  if any(p.is_symlink() for p in [path,*path.parents] if p != root and p.is_relative_to(root)) or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
   errors.append({'path':name,'rule':'UNSAFE_OR_MISSING_FILE'});continue
  if path.stat().st_size>1_500_000:
   errors.append({'path':name,'rule':'FILE_TOO_LARGE'});continue
  if path.suffix not in TEXT_SUFFIXES and path.name not in ALLOWED_NAMES:
   errors.append({'path':name,'rule':'UNREVIEWED_FILE_TYPE'});continue
  try:text=path.read_text(encoding='utf-8-sig')
  except UnicodeError:
   errors.append({'path':name,'rule':'BINARY_OR_NON_UTF8'});continue
  for code,pattern in compiled:
   match=pattern.search(text)
   if match:errors.append({'path':name,'rule':code,'line':text[:match.start()].count('\n')+1})
 return errors

def release_files(root:Path)->list[str]:
 d=json.loads((root/'distribution/manifest.json').read_text(encoding='utf-8'))
 return sorted(d['files'])+['distribution/manifest.json']

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--private-policy',type=Path);a=p.parse_args()
 try:
  patterns=json.loads(a.private_policy.read_text())['deny_patterns'] if a.private_policy else []
  errs=findings(a.root,release_files(a.root),patterns)
  print(json.dumps({'status':'SCAN_PASS' if not errs else 'SCAN_FAILED','findings':errs,'scope':'manifest_allowlist','limitation':'Pattern checks do not replace confidentiality, rights and human review.'},ensure_ascii=False,indent=2))
  raise SystemExit(bool(errs))
 except (OSError,ValueError,KeyError) as exc: print(str(exc),file=sys.stderr);raise SystemExit(2)
