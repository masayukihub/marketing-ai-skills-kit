#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if command -v python3 >/dev/null 2>&1; then PY=python3; elif command -v python >/dev/null 2>&1; then PY=python; else echo 'Install Python 3.10+ first.' >&2; exit 2; fi
"$PY" "$ROOT/scripts/install.py"
"$PY" "$ROOT/scripts/doctor.py"
"$PY" "$ROOT/scripts/demo.py"
"$PY" "$ROOT/scripts/demo_launch.py"
