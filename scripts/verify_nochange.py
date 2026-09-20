#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');args=p.parse_args()
paths=[ROOT/'outputs/demo-project'/task/'run.json' for task in ('insights','content','campaign','edm','influencer')]
if args.launch:
 for case in ('launch-complete','launch-missing','launch-conflict'):
  paths.extend(ROOT/'outputs'/case/'launch'/child/'run.json' for child in ('','content','edm'))
for path in paths:
 r=json.loads(path.read_text(encoding='utf-8'));task=r['task']
 assert all(not r['source_delta'][k] for k in ('new','changed','removed')),task
 assert r['publication_ready'] is False,task
print('NO_CHANGE_SOURCE_DELTA_PASS — no automatic memory writeback is implemented')
