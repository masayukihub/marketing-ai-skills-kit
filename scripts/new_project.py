#!/usr/bin/env python3
"""Create a local blank project; never reuse demo facts or overwrite a project."""
from pathlib import Path
import argparse
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kit.common import load_json,write_json,safe_id
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--id',required=True);p.add_argument('--brand-file',type=Path);a=p.parse_args()
 try:
  pid=safe_id(a.id);dest=ROOT/'projects'/pid
  if dest.exists():raise ValueError('Project already exists; it was not overwritten')
  data=load_json(ROOT/'templates/project.json');data['project_id']=pid;data['product']['id']=pid
  if a.brand_file:
   b=load_json(a.brand_file);data['brand']={'name':b['brand_name'],'company_name':b['company_name']};data['market']=b.get('market','JP')
  dest.mkdir(parents=True)
  write_json(dest/'project.json',data)
  (dest/'product-brief.md').write_text((ROOT/'templates/product-brief.md').read_text(encoding='utf-8'),encoding='utf-8')
  for name in ('reviews.csv','competitors.csv','campaign.csv','creators.csv'):
   header=(ROOT/'examples/demo-project'/name).read_text(encoding='utf-8').splitlines()[0]
   (dest/name).write_text(header+'\n',encoding='utf-8')
  print('LOCAL_PROJECT_CREATED:',dest)
  print('Next: add user-owned evidence, register source IDs in project.json, and keep synthetic=false.')
 except (OSError,ValueError,KeyError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(2)
