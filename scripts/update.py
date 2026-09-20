#!/usr/bin/env python3
"""Preview or apply a checksum-pinned release locally. No download, Git mutation or publication."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kit.common import reject_symlinks, safe_path
from sanitize_check import findings

MANIFEST = 'distribution/manifest.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def version_key(value):
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:-rc(\d+))?', value)
    if not match:
        raise ValueError('Unsupported release version')
    return (*map(int, match.group(1, 2, 3)), int(match[4]) if match[4] else 10**9)


def read_archive(path, expected):
    reject_symlinks(path)
    if not re.fullmatch('[a-f0-9]{64}', expected) or path.stat().st_size > 30_000_000:
        raise ValueError('Invalid release checksum or archive size')
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError('RELEASE_CHECKSUM_MISMATCH')
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        if len(names) != len({n.casefold() for n in names}) or len(names) > 2000 or sum(i.file_size for i in infos) > 30_000_000:
            raise ValueError('Invalid archive entries')
        for info in infos:
            p = PurePosixPath(info.filename)
            if any(part.endswith((' ', '.')) or re.fullmatch(r'(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', part) for part in p.parts):
                raise ValueError('Unsafe archive Windows path')
            if not info.filename or p.is_absolute() or '..' in p.parts or '\\' in info.filename or ':' in info.filename or p.as_posix() != info.filename or info.is_dir() or stat.S_ISLNK(info.external_attr >> 16) or info.file_size > 1_500_000:
                raise ValueError('Unsafe archive path or entry type')
        data = {i.filename: archive.read(i) for i in infos}
    manifest = json.loads(data[MANIFEST])
    if manifest.get('export_mode') != 'exact_file_allowlist' or manifest.get('copy_git_history') is not False or MANIFEST in manifest['files']:
        raise ValueError('Invalid exact release manifest')
    if set(data) != set(manifest['files']) | {MANIFEST}:
        raise ValueError('Unexpected or missing archive files')
    if any(sha(data[n]) != h for n, h in manifest['files'].items()):
        raise ValueError('RELEASE_FILE_HASH_MISMATCH')
    meta = json.loads(data['kit.json'])
    if manifest['version'] != meta['version']:
        raise ValueError('Release version mismatch')
    requirement = re.fullmatch(r'>=(\d+)\.(\d+)', meta['python'])
    if not requirement or sys.version_info[:2] < tuple(map(int, requirement.groups())):
        raise ValueError('PYTHON_VERSION_INCOMPATIBLE')
    version_key(meta['version'])
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name, content in data.items():
            file = directory/name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)
        if findings(directory, list(data)):
            raise ValueError('RELEASE_SAFETY_CHECK_FAILED')
    return data, manifest


def preview(target, data, incoming, checksum, rollback=False):
    reject_symlinks(target)
    old_file = safe_path(target, MANIFEST)
    old_bytes = old_file.read_bytes()
    old = json.loads(old_bytes)
    if old.get('copy_git_history') is not False or old.get('export_mode') != 'exact_file_allowlist' or MANIFEST in old['files']:
        raise ValueError('Unsupported installed manifest')
    if findings(target, list(old['files']) + [MANIFEST]):
        raise ValueError('INSTALLED_RUNTIME_SAFETY_CHECK_FAILED')
    if not rollback and version_key(incoming['version']) < version_key(old['version']):
        raise ValueError('DOWNGRADE_REQUIRES_ROLLBACK_FLAG')
    before = {}
    for name, expected in old['files'].items():
        path = safe_path(target, name)
        if not path.is_file() or sha(path.read_bytes()) != expected:
            raise ValueError('LOCAL_MODIFICATION_CONFLICT: '+name)
        before[name] = expected
    before[MANIFEST] = sha(old_bytes)
    for name in set(data) - set(before):
        if safe_path(target, name).exists():
            raise ValueError('NEW_FILE_COLLISION: '+name)
    changed = sorted(n for n in data if sha(data[n]) != before.get(n))
    removed = sorted(set(before) - set(data))
    plan = {'status':'UPDATE_REVIEW_REQUIRED' if changed or removed else 'UP_TO_DATE',
            'from_version':old['version'], 'to_version':incoming['version'], 'release_sha256':checksum,
            'changed':changed, 'removed':removed, 'installed_hashes':before,
            'user_data_touched':False, 'rollback':rollback, 'published':False}
    plan['plan_sha256'] = sha(json.dumps(plan,sort_keys=True).encode())
    return plan


def apply_update(target, data, incoming, checksum, expected_plan, rollback=False):
    plan = preview(target, data, incoming, checksum, rollback)
    if plan['plan_sha256'] != expected_plan:
        raise ValueError('UPDATE_PLAN_CHANGED')
    if plan['status'] == 'UP_TO_DATE':
        return plan
    backup = safe_path(target, '.kit-backups/'+plan['plan_sha256'])
    if backup.exists():
        raise ValueError('Backup already exists; inspect previous attempt before retrying')
    old_data = {n:safe_path(target,n).read_bytes() for n in plan['installed_hashes']}
    for name, content in old_data.items():
        p = backup/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(content)
    written, deleted = [], []
    try:
        for name in plan['changed']:
            path = safe_path(target,name)
            expected = plan['installed_hashes'].get(name)
            if (sha(path.read_bytes()) if path.exists() else None) != expected:
                raise ValueError('TARGET_CHANGED_DURING_UPDATE')
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('wb' if expected is not None else 'xb') as stream:
                written.append(name)
                stream.write(data[name])
        for name in plan['removed']:
            path=safe_path(target,name)
            if sha(path.read_bytes()) != plan['installed_hashes'][name]:
                raise ValueError('TARGET_CHANGED_DURING_UPDATE')
            path.unlink()
            deleted.append(name)
    except Exception:
        for name in written + deleted:
            path=safe_path(target,name)
            if name in old_data:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(old_data[name])
            else:
                path.unlink(missing_ok=True)
        raise
    return dict(plan,status='APPLIED_LOCALLY',backup=backup.relative_to(target).as_posix(),
                next_action='Run doctor, tests and install.py; no global Skills were changed.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zip',type=Path,required=True)
    p.add_argument('--sha256',required=True,help='Expected checksum obtained from a trusted release channel')
    p.add_argument('--target',type=Path,default=ROOT)
    p.add_argument('--apply',action='store_true')
    p.add_argument('--expected-plan')
    p.add_argument('--rollback',action='store_true')
    args=p.parse_args()
    data,manifest=read_archive(args.zip,args.sha256)
    result=apply_update(args.target,data,manifest,args.sha256,args.expected_plan,args.rollback) if args.apply else preview(args.target,data,manifest,args.sha256,args.rollback)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,zipfile.BadZipFile) as exc:raise SystemExit(str(exc))
