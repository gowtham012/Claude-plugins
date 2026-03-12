#!/usr/bin/env python3
"""PostToolUse hook — captures file content AFTER Write/Edit, writes to index."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip(): return
        data = json.loads(raw)
    except Exception: return
    cwd = data.get("cwd") or os.getcwd()
    try:
        d = Path(cwd) / "rollback"
        pending_f = d / ".pending"
        if not pending_f.exists(): return
        pending = json.loads(pending_f.read_text())
        pending_f.unlink()
        aid = pending["id"]
        file_path = pending["file_path"]
        # Save after snapshot
        fp = Path(file_path)
        if fp.exists():
            content = fp.read_text(encoding="utf-8")
            (d / "snapshots" / f"{aid:04d}-after.txt").write_text(content, encoding="utf-8")
        # Append to index
        pending["rolled_back"] = False
        with (d / "index.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(pending) + "\n")
        # Auto-cleanup if snapshots dir too large
        snap_dir = d / "snapshots"
        total = sum(f.stat().st_size for f in snap_dir.iterdir() if f.is_file())
        if total > 50 * 1024 * 1024:  # 50MB
            files = sorted(snap_dir.iterdir(), key=lambda f: f.name)
            half = len(files) // 2
            for f in files[:half]:
                f.unlink()
    except Exception: pass

if __name__ == "__main__":
    main()
