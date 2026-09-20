#!/usr/bin/env python3
"""Create a NEW PRIVATE repository from an audited snapshot. Dry-run is the default."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_release import export
from verify_github import inspect as verify_remote

def plan(repo:str,dest:Path)->list[list[str]]:
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9._-]*',repo):raise ValueError('Use OWNER/REPOSITORY')
 return [['git','init','-b','main'],['git','add','--','<exact manifest file list>'],
         ['git','commit','-m','Initial sanitized marketing skills distribution'],
         ['gh','repo','create',repo,'--private','--source',str(dest),'--remote','origin','--push','--description','Local-first AI marketing skills, synthetic demos and explicit review gates'],
         ['gh','repo','edit',repo,'--template']]

def command(args,**kw):return subprocess.run(args,check=True,text=True,capture_output=True,timeout=300,env={**os.environ,"GH_HOST":"github.com"},**kw)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True);p.add_argument('--dest',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
 try:
  dest=a.dest.resolve();commands=plan(a.repo,dest)
  if not a.apply:
   print(json.dumps({'mode':'DRY_RUN','visibility':'private','history_copied':False,'commands':commands,'requirements':['Git','authenticated GitHub CLI','new empty destination'],'source':str(ROOT)},ensure_ascii=False,indent=2));raise SystemExit(0)
  if not shutil.which('gh') or not shutil.which('git'):raise ValueError('Install Git and GitHub CLI, then run gh auth login locally. Never paste tokens in chat.')
  command(['gh','auth','status'])
  user=json.loads(command(['gh','api','user']).stdout)
  if a.repo.split('/')[0]!=user['login']:raise ValueError('Requested owner differs from authenticated user; organization creation is not automatic')
  command([sys.executable,str(ROOT/'scripts/doctor.py')],cwd=ROOT)
  command([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT)
  result=export(ROOT,dest)
  command(['git','init','-b','main'],cwd=dest)
  command(['git','config','user.name',user['login']],cwd=dest)
  command(['git','config','user.email',str(user['id'])+'+'+user['login']+'@users.noreply.github.com'],cwd=dest)
  manifest=json.loads((dest/'distribution/manifest.json').read_text())
  command(['git','add','--',*sorted(manifest['files']),'distribution/manifest.json'],cwd=dest)
  command(['git','commit','-m','Initial sanitized marketing skills distribution'],cwd=dest)
  command(commands[3],cwd=dest)
  template_status='NOT_SET'
  try:command(commands[4],cwd=dest);template_status='ENABLED'
  except subprocess.CalledProcessError:template_status='NEEDS_MANUAL_SETUP'
  remote=json.loads(command(['gh','repo','view',a.repo,'--json','url,visibility,isTemplate']).stdout)
  head=command(['git','rev-parse','HEAD'],cwd=dest).stdout.strip()
  verified=verify_remote(a.repo,head)
  print(json.dumps({'status':verified['status'],'remote':remote,'head_commit':head,'template_status':template_status,'verification':verified,'export':result,'public_publication':'NOT_PERFORMED'},ensure_ascii=False,indent=2))
  if not verified['all_remote_checks_passed']:
   print('Repository is private and commit matches. Remote CI is not yet PASS; use scripts/verify_github.py --repo '+a.repo+' --checkout '+str(dest)+' for a read-only recheck.',file=sys.stderr)
   raise SystemExit(3)
 except subprocess.TimeoutExpired:
  print('COMMAND_TIMEOUT: staging files are preserved; remote completion is not assumed.',file=sys.stderr);raise SystemExit(2)
 except subprocess.CalledProcessError as exc:
  # Do not print complete CLI payloads, credentials or environment.
  print('COMMAND_FAILED: '+str(exc.cmd[0])+' (exit '+str(exc.returncode)+'). Existing staging files are preserved.',file=sys.stderr);raise SystemExit(2)
 except (OSError,ValueError,KeyError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(2)
