#!/usr/bin/env python3
"""Read-only verification of the exact private GitHub release and its push CI.

An empty/pending/skipped run is never a successful CI result. This does not create
repositories, change visibility, push commits, approve content or poll forever.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any


def validate_identity(repo: str, commit: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9._-]*", repo):
        raise ValueError("Use OWNER/REPOSITORY")
    if not re.fullmatch(r"[a-fA-F0-9]{40}", commit):
        raise ValueError("Expected a full 40-character commit SHA")


def assess(repo: str, commit: str, remote: dict[str, Any], head: str,
           runs: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Pure classification function; live evidence must be supplied by inspect()."""
    validate_identity(repo, commit)
    commit = commit.lower()
    if remote.get("nameWithOwner", "").lower() != repo.lower():
        raise ValueError("REMOTE_IDENTITY_MISMATCH")
    if remote.get("visibility", "").upper() != "PRIVATE":
        raise ValueError("REMOTE_NOT_PRIVATE: no visibility changes were attempted")
    if remote.get("url", "").lower() != ("https://github.com/" + repo).lower():
        raise ValueError("REMOTE_URL_MISMATCH")
    if head.lower() != commit:
        raise ValueError("REMOTE_HEAD_MISMATCH: no push or force-push was attempted")

    matching = [r for r in (runs or [])
                if r.get("headSha", "").lower() == commit and r.get("event") == "push"]
    latest = max(matching, key=lambda r: int(r.get("databaseId", 0)), default=None)
    if runs is None:
        ci = "UNAVAILABLE"
    elif latest is None:
        ci = "NOT_STARTED"
    elif latest.get("status") != "completed":
        ci = "PENDING"
    elif latest.get("conclusion") == "success":
        ci = "PASS"
    else:
        ci = "NOT_PASSED"
    return {
        "status": "PRIVATE_REPOSITORY_VERIFIED_CI_" + ci,
        "repository": repo,
        "url": remote["url"],
        "visibility": "private",
        "expected_commit": commit,
        "remote_main_commit": head.lower(),
        "head_matches": True,
        "is_template": bool(remote.get("isTemplate", False)),
        "ci_workflow": ".github/workflows/ci.yml",
        "ci_status": ci,
        "ci_run_url": latest.get("url") if latest else None,
        "ci_conclusion": latest.get("conclusion") if latest else None,
        "all_remote_checks_passed": ci == "PASS",
        "public_publication": "NOT_PERFORMED",
    }


def gh_json(args: list[str]) -> Any:
    result = subprocess.run(["gh", *args], check=True, capture_output=True,
                            text=True, timeout=60, env={**os.environ, "GH_HOST": "github.com"})
    return json.loads(result.stdout)


def inspect(repo: str, commit: str) -> dict[str, Any]:
    validate_identity(repo, commit)
    if not shutil.which("gh"):
        raise ValueError("GITHUB_CLI_MISSING: run this on a host with authenticated GitHub CLI")
    remote = gh_json(["repo", "view", repo, "--json", "nameWithOwner,url,visibility,isTemplate"])
    head = gh_json(["api", f"repos/{repo}/git/ref/heads/main"])["object"]["sha"]
    # Fail on identity/privacy/head mismatch before reporting anything as verified.
    assess(repo, commit, remote, head, None)
    try:
        runs = gh_json(["run", "list", "--repo", repo, "--workflow", "ci.yml",
                        "--commit", commit, "--event", "push", "--limit", "20",
                        "--json", "databaseId,headSha,event,status,conclusion,url"])
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError):
        runs = None
    return assess(repo, commit, remote, head, runs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--commit")
    target.add_argument("--checkout", type=Path)
    args = parser.parse_args()
    try:
        commit = args.commit
        if args.checkout:
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=args.checkout,
                                    check=True, capture_output=True, text=True, timeout=30).stdout.strip()
        result = inspect(args.repo, commit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["all_remote_checks_passed"] else 3
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        # Never echo credential-bearing CLI payloads or environment variables.
        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(json.dumps({"status": "REMOTE_VERIFICATION_BLOCKED", "reason": detail}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
