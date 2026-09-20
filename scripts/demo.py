#!/usr/bin/env python3
"""Run all five local demo workflows without accounts, network or API fees."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
for task in ('insights','content','campaign','edm','influencer'):
    subprocess.run([sys.executable,str(ROOT/'scripts/run.py'),'--task',task],check=True,cwd=ROOT)
print('DEMO_COMPLETE: outputs/demo-project/; these are draft/fixture outputs, not production assets.')
