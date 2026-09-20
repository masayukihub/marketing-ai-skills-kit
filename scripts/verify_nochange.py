#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
for task in ('insights','content','campaign','edm','influencer'):
 r=json.loads((ROOT/'outputs/demo-project'/task/'run.json').read_text())
 assert all(not r['source_delta'][k] for k in ('new','changed','removed')),task
 assert r['publication_ready'] is False,task
print('NO_CHANGE_SOURCE_DELTA_PASS — no automatic memory writeback is implemented')
