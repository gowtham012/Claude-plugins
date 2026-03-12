#!/usr/bin/env python3
"""Stop hook — reports checkpoint count and unsaved changes."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path


def _dir(cwd: str) -> Path:
    return Path(cwd) / "time-capsule"


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except Exception:
        return

    cwd = data.get("cwd") or os.getcwd()

    try:
        d = _dir(cwd)
        if not d.exists():
            return

        # Count checkpoints
        index_f = d / "index.jsonl"
        count = 0
        if index_f.exists():
            count = sum(1 for l in index_f.read_text(encoding="utf-8").splitlines() if l.strip())

        # Check for unsaved changes
        result = subprocess.run(
            "git status --porcelain",
            shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=30,
        )
        has_changes = bool(result.stdout.strip()) if result.returncode == 0 else False

        if has_changes and count > 0:
            msg = f"[time-capsule] {count} checkpoint(s) saved. You have unsaved changes — consider /time-capsule:checkpoint before ending."
            print(json.dumps({"systemMessage": msg}), flush=True)
        elif has_changes:
            msg = "[time-capsule] You have unsaved changes with no checkpoints. Consider /time-capsule:checkpoint to save a snapshot."
            print(json.dumps({"systemMessage": msg}), flush=True)

    except Exception:
        pass


if __name__ == "__main__":
    main()
