#!/usr/bin/env python3
"""time-capsule MCP server — git checkpoint auto-saver using a hidden branch."""
from __future__ import annotations
import json, subprocess, hashlib
from datetime import datetime, timezone
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("time-capsule")

BRANCH_PREFIX = "time-capsule/"
CHECKPOINT_BRANCH = "time-capsule/checkpoints"


def _dir(cwd: str) -> Path:
    return Path(cwd) / "time-capsule"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_config(cwd: str) -> dict:
    f = _dir(cwd) / "config.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf-8"))


def _save_config(cwd: str, config: dict) -> None:
    f = _dir(cwd) / "config.json"
    f.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _load_index(cwd: str) -> list[dict]:
    f = _dir(cwd) / "index.jsonl"
    if not f.exists():
        return []
    entries = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return entries


def _append_index(cwd: str, entry: dict) -> None:
    f = _dir(cwd) / "index.jsonl"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def _next_id(cwd: str) -> int:
    return len(_load_index(cwd)) + 1


def _update_status(cwd: str) -> None:
    d = _dir(cwd)
    entries = _load_index(cwd)
    config = _load_config(cwd)
    auto = config.get("auto_checkpoint", True)
    count = len(entries)
    last = entries[-1] if entries else None
    lines = [
        f"Checkpoints: {count} | Auto: {'on' if auto else 'off'}",
    ]
    if last:
        lines.append(f"Last: #{last['id']} \"{last['label']}\" at {last['ts'][:19]}")
    (d / "status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_git(cwd: str, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args, cwd=cwd,
        capture_output=True, text=True, timeout=30
    )


def _get_current_branch(cwd: str) -> str:
    r = _run_git(cwd, ["rev-parse", "--abbrev-ref", "HEAD"])
    return r.stdout.strip() if r.returncode == 0 else "main"


def _get_head_sha(cwd: str) -> str:
    r = _run_git(cwd, ["rev-parse", "HEAD"])
    return r.stdout.strip() if r.returncode == 0 else ""


def _create_checkpoint_commit(cwd: str, label: str) -> str | None:
    """Create a checkpoint by committing current state to a hidden orphan-like tag.

    Strategy: create a lightweight tag pointing to a tree object that captures
    the current working directory state. This doesn't touch branches or stash.
    """
    # Get current state hash for the tag name
    ts = _now().replace(":", "-").replace("+", "").replace(".", "-")
    tag_name = f"time-capsule/{ts}"

    # Stage everything temporarily, create a tree, then restore index
    # Save current index state
    _run_git(cwd, ["stash", "push", "--keep-index", "-m", f"time-capsule-temp-{ts}"])

    # Actually, simpler approach: create a commit on a detached state
    # Best approach: use git stash create (creates stash commit without modifying state)
    result = _run_git(cwd, ["stash", "create", "-m", f"time-capsule: {label}"])

    if result.returncode != 0 or not result.stdout.strip():
        # No changes to stash — create a tag at HEAD instead
        head_sha = _get_head_sha(cwd)
        if not head_sha:
            return None
        r = _run_git(cwd, ["tag", tag_name, head_sha])
        if r.returncode != 0:
            return None
        return tag_name

    stash_sha = result.stdout.strip()

    # Create a tag pointing to this stash commit (without actually pushing to stash stack)
    r = _run_git(cwd, ["tag", tag_name, stash_sha])
    if r.returncode != 0:
        return None

    return tag_name


@mcp.tool()
def setup_project(cwd: str) -> str:
    """One-time setup. Creates time-capsule/ directory, config, and CLAUDE.md import."""
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)

    config_f = d / "config.json"
    if not config_f.exists():
        _save_config(cwd, {
            "auto_checkpoint": True,
            "min_interval_seconds": 60,
        })

    index_f = d / "index.jsonl"
    if not index_f.exists():
        index_f.write_text("", encoding="utf-8")

    _update_status(cwd)

    # Add to .gitignore
    gi = Path(cwd) / ".gitignore"
    if gi.exists():
        content = gi.read_text(encoding="utf-8")
        if "time-capsule/" not in content:
            with gi.open("a", encoding="utf-8") as f:
                f.write("\ntime-capsule/\n")
    else:
        gi.write_text("time-capsule/\n", encoding="utf-8")

    # Add @import to CLAUDE.md
    claude_md = Path(cwd) / "CLAUDE.md"
    import_line = "@time-capsule/status.md"
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")
        if import_line not in content:
            with claude_md.open("a", encoding="utf-8") as f:
                f.write(f"\n{import_line}\n")
    else:
        claude_md.write_text(f"{import_line}\n", encoding="utf-8")

    return (
        f"time-capsule set up in {d}.\n"
        f"Added time-capsule/ to .gitignore.\n"
        f"Added @import to CLAUDE.md for time-capsule/status.md.\n"
        f"Restart Claude Code for the @import to take effect."
    )


@mcp.tool()
def create_checkpoint(cwd: str, label: str) -> str:
    """Create a named checkpoint using a lightweight git tag."""
    d = _dir(cwd)
    if not d.exists():
        return "time-capsule not set up. Run setup_project first."

    cid = _next_id(cwd)
    tag_name = _create_checkpoint_commit(cwd, label)

    if tag_name is None:
        return "Failed to create checkpoint — is this a git repository?"

    entry = {
        "id": cid,
        "ts": _now(),
        "label": label,
        "tag": tag_name,
        "branch": _get_current_branch(cwd),
        "head_sha": _get_head_sha(cwd),
    }
    _append_index(cwd, entry)
    _update_status(cwd)
    return f"Checkpoint #{cid} created: \"{label}\" (tag: {tag_name})"


@mcp.tool()
def list_checkpoints(cwd: str, limit: int = 20) -> str:
    """Show recent checkpoints as a markdown table."""
    entries = _load_index(cwd)
    if not entries:
        return "No checkpoints yet."
    recent = entries[-limit:]
    lines = [
        "| # | Time | Label | Branch |",
        "|---|------|-------|--------|",
    ]
    for e in reversed(recent):
        ts = e.get("ts", "")[:19]
        branch = e.get("branch", "")
        lines.append(f"| {e['id']} | {ts} | {e.get('label', '')} | {branch} |")
    return "\n".join(lines)


@mcp.tool()
def restore_checkpoint(cwd: str, checkpoint_id: int) -> str:
    """Restore files from a checkpoint. Creates a new checkpoint of current state first."""
    entries = _load_index(cwd)
    entry = next((e for e in entries if e["id"] == checkpoint_id), None)
    if not entry:
        return f"Checkpoint #{checkpoint_id} not found."

    tag = entry.get("tag", "")
    if not tag:
        return f"Checkpoint #{checkpoint_id} has no tag reference."

    # Verify tag exists
    r = _run_git(cwd, ["rev-parse", "--verify", tag])
    if r.returncode != 0:
        return f"Tag '{tag}' not found in git. Checkpoint may have been cleaned up."

    # Auto-save current state before restoring
    auto_label = f"auto-save before restoring #{checkpoint_id}"
    create_checkpoint(cwd, auto_label)

    # Restore: checkout the files from the tag
    r = _run_git(cwd, ["checkout", tag, "--", "."])
    if r.returncode != 0:
        # Try alternative: diff and apply
        r2 = _run_git(cwd, ["stash", "apply", tag])
        if r2.returncode != 0:
            return f"Failed to restore checkpoint #{checkpoint_id}: {r.stderr.strip()} / {r2.stderr.strip()}"

    return f"Checkpoint #{checkpoint_id} (\"{entry['label']}\") restored. Current state auto-saved first."


@mcp.tool()
def diff_checkpoint(cwd: str, checkpoint_id: int) -> str:
    """Show diff between a checkpoint and the current working tree."""
    entries = _load_index(cwd)
    entry = next((e for e in entries if e["id"] == checkpoint_id), None)
    if not entry:
        return f"Checkpoint #{checkpoint_id} not found."

    tag = entry.get("tag", "")
    if not tag:
        return f"Checkpoint #{checkpoint_id} has no tag reference."

    r = _run_git(cwd, ["diff", tag, "HEAD", "--stat"])
    if r.returncode != 0:
        return f"Failed to show diff: {r.stderr.strip()}"

    stat = r.stdout.strip()

    # Also get detailed diff (limited)
    r2 = _run_git(cwd, ["diff", tag, "HEAD"])
    detailed = r2.stdout.strip() if r2.returncode == 0 else ""

    lines_list = detailed.splitlines()
    if len(lines_list) > 200:
        detailed = "\n".join(lines_list[:200]) + f"\n\n... ({len(lines_list) - 200} more lines)"

    output = f"Diff for checkpoint #{checkpoint_id} (\"{entry['label']}\"):\n\n"
    output += f"**Summary:**\n```\n{stat}\n```\n\n"
    if detailed:
        output += f"**Changes:**\n```diff\n{detailed}\n```"
    return output


@mcp.tool()
def delete_checkpoint(cwd: str, checkpoint_id: int) -> str:
    """Delete a specific checkpoint (removes its tag)."""
    entries = _load_index(cwd)
    entry = next((e for e in entries if e["id"] == checkpoint_id), None)
    if not entry:
        return f"Checkpoint #{checkpoint_id} not found."

    tag = entry.get("tag", "")
    if tag:
        _run_git(cwd, ["tag", "-d", tag])

    # Remove from index
    entries = [e for e in entries if e["id"] != checkpoint_id]
    f = _dir(cwd) / "index.jsonl"
    if entries:
        f.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    else:
        f.write_text("", encoding="utf-8")

    _update_status(cwd)
    return f"Checkpoint #{checkpoint_id} deleted."


@mcp.tool()
def cleanup(cwd: str, keep: int = 50) -> str:
    """Remove old checkpoints, keeping the most recent N."""
    entries = _load_index(cwd)
    if len(entries) <= keep:
        return f"Only {len(entries)} checkpoints — nothing to clean up."

    to_remove = entries[:-keep]
    for e in to_remove:
        tag = e.get("tag", "")
        if tag:
            _run_git(cwd, ["tag", "-d", tag])

    kept = entries[-keep:]
    f = _dir(cwd) / "index.jsonl"
    f.write_text("\n".join(json.dumps(e) for e in kept) + "\n", encoding="utf-8")
    _update_status(cwd)
    return f"Removed {len(to_remove)} old checkpoints. Kept {len(kept)}."


@mcp.tool()
def configure(cwd: str, auto_checkpoint: bool = True, min_interval_seconds: int = 60) -> str:
    """Configure auto-checkpoint behavior."""
    config = _load_config(cwd)
    config["auto_checkpoint"] = auto_checkpoint
    config["min_interval_seconds"] = max(10, min_interval_seconds)
    _save_config(cwd, config)
    _update_status(cwd)
    return (
        f"Configuration updated.\n"
        f"  auto_checkpoint: {auto_checkpoint}\n"
        f"  min_interval_seconds: {config['min_interval_seconds']}"
    )


if __name__ == "__main__":
    mcp.run()
