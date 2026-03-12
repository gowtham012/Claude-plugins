#!/usr/bin/env python3
"""rollback MCP server — one-command undo for any Claude action."""
from __future__ import annotations
import json, difflib
from datetime import datetime, timezone
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("rollback")

def _dir(cwd: str) -> Path: return Path(cwd) / "rollback"
def _now() -> str: return datetime.now(timezone.utc).isoformat()

def _load_index(cwd: str) -> list[dict]:
    f = _dir(cwd) / "index.jsonl"
    if not f.exists(): return []
    entries = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try: entries.append(json.loads(line))
            except Exception: pass
    return entries

def _save_index(cwd: str, entries: list[dict]) -> None:
    f = _dir(cwd) / "index.jsonl"
    f.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")

def _next_id(cwd: str) -> int:
    return len(_load_index(cwd)) + 1


@mcp.tool()
def setup_project(cwd: str) -> str:
    """One-time setup. Creates rollback/ directory and adds to .gitignore."""
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)
    (d / "snapshots").mkdir(exist_ok=True)
    gi = Path(cwd) / ".gitignore"
    if gi.exists():
        content = gi.read_text(encoding="utf-8")
        if "rollback/" not in content:
            with gi.open("a", encoding="utf-8") as f:
                f.write("\nrollback/\n")
    else:
        gi.write_text("rollback/\n", encoding="utf-8")
    return f"rollback set up in {d}. Added rollback/ to .gitignore."


@mcp.tool()
def rollback_undo(cwd: str, count: int = 1) -> str:
    """Undo the last N actions."""
    entries = _load_index(cwd)
    active = [e for e in entries if not e.get("rolled_back")]
    if not active:
        return "Nothing to roll back."
    to_undo = active[-count:]
    results = []
    for entry in reversed(to_undo):
        aid = entry["id"]
        fp = entry["file_path"]
        before_f = _dir(cwd) / "snapshots" / f"{aid:04d}-before.txt"
        existed = entry.get("file_existed_before", True)
        try:
            if existed and before_f.exists():
                Path(fp).write_text(before_f.read_text(encoding="utf-8"), encoding="utf-8")
                results.append(f"  #{aid}: restored {fp}")
            elif not existed:
                p = Path(fp)
                if p.exists():
                    p.unlink()
                results.append(f"  #{aid}: deleted {fp} (was created by Claude)")
            else:
                results.append(f"  #{aid}: skipped — no snapshot for {fp}")
            entry["rolled_back"] = True
        except Exception as e:
            results.append(f"  #{aid}: FAILED — {e}")
    _save_index(cwd, entries)
    return f"Rolled back {len(to_undo)} action(s):\n" + "\n".join(results)


@mcp.tool()
def rollback_list(cwd: str, limit: int = 20) -> str:
    """Show recent actions with IDs."""
    entries = _load_index(cwd)
    if not entries:
        return "No actions recorded yet."
    recent = entries[-limit:]
    lines = ["| # | Time | Tool | File | Rolled Back |", "|---|------|------|------|-------------|"]
    for e in reversed(recent):
        rb = "Yes" if e.get("rolled_back") else ""
        ts = e.get("ts", "")[:19]
        lines.append(f"| {e['id']} | {ts} | {e.get('tool','')} | {e.get('file_path','')[-40:]} | {rb} |")
    return "\n".join(lines)


@mcp.tool()
def rollback_show(cwd: str, action_id: int) -> str:
    """Show diff for a specific action."""
    d = _dir(cwd)
    before_f = d / "snapshots" / f"{action_id:04d}-before.txt"
    after_f = d / "snapshots" / f"{action_id:04d}-after.txt"
    entries = _load_index(cwd)
    entry = next((e for e in entries if e["id"] == action_id), None)
    if not entry:
        return f"Action #{action_id} not found."
    before = before_f.read_text(encoding="utf-8").splitlines() if before_f.exists() else []
    after = after_f.read_text(encoding="utf-8").splitlines() if after_f.exists() else []
    diff = list(difflib.unified_diff(before, after, fromfile="before", tofile="after", lineterm=""))
    if not diff:
        return f"Action #{action_id}: no diff available."
    return f"Action #{action_id} ({entry.get('tool','')} on {entry.get('file_path','')}):\n" + "\n".join(diff[:100])


@mcp.tool()
def rollback_to(cwd: str, action_id: int) -> str:
    """Roll back everything from most recent down to action_id."""
    entries = _load_index(cwd)
    active = [e for e in entries if not e.get("rolled_back")]
    to_undo = [e for e in active if e["id"] >= action_id]
    if not to_undo:
        return f"No active actions at or after #{action_id}."
    count = len(to_undo)
    return rollback_undo(cwd, count)


@mcp.tool()
def rollback_cleanup(cwd: str, keep: int = 100) -> str:
    """Remove old snapshots, keeping the most recent N actions."""
    entries = _load_index(cwd)
    if len(entries) <= keep:
        return f"Only {len(entries)} actions — nothing to clean up."
    to_remove = entries[:-keep]
    d = _dir(cwd)
    freed = 0
    for e in to_remove:
        for suffix in ("before", "after"):
            f = d / "snapshots" / f"{e['id']:04d}-{suffix}.txt"
            if f.exists():
                freed += f.stat().st_size
                f.unlink()
    _save_index(cwd, entries[-keep:])
    return f"Cleaned {len(to_remove)} actions, freed ~{freed // 1024}KB."


if __name__ == "__main__":
    mcp.run()
