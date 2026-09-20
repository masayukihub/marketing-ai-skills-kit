"""Shared safe input/output helpers."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

MAX_BYTES = 5_000_000

def safe_path(root: Path, name: str) -> Path:
    root = root.resolve()
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Expected a relative local file path')
    rel = Path(name)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Path traversal is not allowed')
    path = root / rel
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError('Symlink or escaped local path')
    return path

def read_text(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Missing or unsafe input: {path.name}')
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f'Input exceeds {MAX_BYTES} bytes: {path.name}')
    return path.read_text(encoding='utf-8-sig')

def load_json(path: Path) -> Any:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(read_text(path), object_pairs_hook=unique, parse_constant=bad_constant)

def rows(path: Path) -> list[dict[str, str]]:
    import io
    reader = csv.DictReader(io.StringIO(read_text(path)))
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError('CSV header missing or duplicated')
    data = list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in data):
        raise ValueError('Malformed CSV row')
    return data

def number(value: Any, *, nonnegative: bool = True) -> float | None:
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        raise ValueError('Boolean is not a metric')
    try:
        v = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError('Invalid numeric metric') from exc
    if not math.isfinite(v) or (nonnegative and v < 0):
        raise ValueError('Invalid or negative metric')
    return v

def ratio(n: float | None, d: float | None) -> float | None:
    return n / d if n is not None and d not in (None, 0) else None

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')

def write_csv(path: Path, data: list[dict], fields: list[str]) -> None:
    """Prefix spreadsheet-formula triggers in exported text, never input files."""
    def cell(v):
        if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')):
            return "'" + v
        return '' if v is None else v
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows({f: cell(row.get(f)) for f in fields} for row in data)

def safe_id(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', value):
        raise ValueError('ID must use lowercase letters, digits and hyphens')
    return value
