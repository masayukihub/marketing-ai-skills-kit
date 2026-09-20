#!/usr/bin/env python3
"""Run the three explicitly synthetic launch cases; no model, network or user input mutation."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
for case in ('launch-complete','launch-missing','launch-conflict'):
    subprocess.run([sys.executable,str(ROOT/'scripts/run.py'),'--task','launch','--project',str(ROOT/'examples'/case),
                    '--out',str(ROOT/'outputs'/case/'launch'),'--as-of','2026-09-20'],cwd=ROOT,check=True)
print('LAUNCH_DEMOS_COMPLETE: three review packages, not human-user validation or finished product imagery.')
