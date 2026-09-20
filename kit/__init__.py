"""Local-first marketing workflows. No network clients or model credentials."""
import json
from pathlib import Path

# One release version; no separate CLI/runtime literals.
__version__ = json.loads((Path(__file__).resolve().parents[1] / 'kit.json').read_text(encoding='utf-8'))['version']
