#!/usr/bin/env python3
"""Check bundled runtime, demo inputs and all declared local dependencies."""
from pathlib import Path
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kit.truth import load_project
from kit.common import load_json

def doctor(root:Path)->dict:
    issues=[];config=load_json(root/'kit.json')
    if sys.version_info<(3,10):issues.append('PYTHON_VERSION_TOO_OLD')
    for name in config['skills']:
        if not (root/'skills'/name/'SKILL.md').is_file():issues.append('SKILL_MISSING:'+name)
    for path in config['required_files']:
        if not (root/path).is_file():issues.append('RUNTIME_MISSING:'+path)
    try:load_project(root/'examples/demo-project')
    except (OSError,ValueError,TypeError,KeyError) as exc:issues.append('DEMO_INVALID:'+str(exc))
    return {'status':'LOCAL_RUNTIME_READY' if not issues else 'BLOCKED','issues':issues,
            'skills':len(config['skills']),'required_python_packages':[],
            'local_file_adapter':'READY','codex_cli_detected':bool(shutil.which('codex')),
            'codex_runtime_e2e':'NOT_TESTED_BY_DOCTOR','live_web_collection':'NOT_BUNDLED',
            'ai_image_generation':'NOT_BUNDLED','cloud_connectors':'NOT_BUNDLED'}
if __name__=='__main__':
    r=doctor(ROOT);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(bool(r['issues']))
