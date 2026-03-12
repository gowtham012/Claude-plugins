#!/usr/bin/env python3
"""PreToolUse hook — captures file content BEFORE Write/Edit."""
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
    tool_input = data.get("tool_input", {})
    tool_name = data.get("tool_name", "")
    file_path = tool_input.get("file_path", "")
    if not file_path: return
    try:
        d = Path(cwd) / "rollback"
        if not d.exists(): return
        # Skip rollback internal files
        if "rollback/" in file_path or "rollback\\" in file_path: return
        # Count existing entries for ID
        index_f = d / "index.jsonl"
        count = 0
        if index_f.exists():
            count = sum(1 for line in index_f.read_text().splitlines() if line.strip())
        aid = count + 1
        # Save before snapshot
        fp = Path(file_path)
        existed = fp.exists()
        if existed:
            content = fp.read_text(encoding="utf-8")
            (d / "snapshots" / f"{aid:04d}-before.txt").write_text(content, encoding="utf-8")
        # Write pending
        from datetime import datetime, timezone
        pending = {"id": aid, "ts": datetime.now(timezone.utc).isoformat(), "tool": tool_name, "file_path": file_path, "file_existed_before": existed}
        (d / ".pending").write_text(json.dumps(pending), encoding="utf-8")
    except Exception: pass
    # Never block — no output

if __name__ == "__main__":
    main()
