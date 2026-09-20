#!/usr/bin/env python3
"""Run a wholly synthetic local series review, never a send or shared website."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/'scripts/run.py'), '--task', 'edm-series',
                '--project', str(ROOT/'examples/edm-series'), '--as-of', '2026-09-20',
                '--out', str(ROOT/'outputs/edm-series-demo/edm-series')], check=True)
print('SERIES_DEMO_COMPLETE: local drafts; missing images and subject options remain explicit.')
