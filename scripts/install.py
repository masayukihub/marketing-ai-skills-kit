#!/usr/bin/env python3
"""Install only repo-local skills. Refuse to overwrite a locally modified mirror."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]

def sha(data): return hashlib.sha256(data).hexdigest()

def install(root:Path,check:bool=False)->list[str]:
    results=[]
    for directory in sorted((root/'skills').iterdir()):
        if not directory.is_dir(): continue
        target=root/'.agents/skills'/directory.name
        if any(p.is_symlink() for p in (root/'.agents', root/'.agents/skills', target)) or not target.resolve().is_relative_to(root.resolve()):
            raise ValueError('Refusing escaped or symlinked skill target: '+directory.name)
        incoming=(directory/'SKILL.md').read_bytes()
        marker=target/'.kit-sha256'
        existing=target/'SKILL.md'
        if existing.exists():
            old=existing.read_bytes()
            if old!=incoming and (not marker.is_file() or marker.read_text().strip()!=sha(old)):
                raise ValueError('Locally modified skill, not overwritten: '+directory.name)
        if check:
            if not existing.is_file() or existing.read_bytes()!=incoming: raise ValueError('Skill mirror not installed or stale: '+directory.name)
        else:
            target.mkdir(parents=True,exist_ok=True)
            existing.write_bytes(incoming)
            marker.write_text(sha(incoming)+'\n')
        results.append(directory.name)
    if not results: raise ValueError('No skills found')
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if sys.version_info<(3,10): raise SystemExit('Python 3.10 or newer is required')
    try:
        print('REPO_LOCAL_SKILLS_READY:',', '.join(install(ROOT,a.check)))
        print('Open this entire folder in Codex, then start a new thread. Global skills were not changed.')
    except (OSError,ValueError) as e: print(str(e),file=sys.stderr);raise SystemExit(2)
