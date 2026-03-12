#!/usr/bin/env python3
"""PreToolUse hook — auto-creates checkpoint before Write/Edit using git tags."""
from __future__ import annotations
import json, os, subprocess, sys
from datetime import datetime, timezone
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
    tool_input = data.get("tool_input", {})
    tool_name = data.get("tool_name", "")
    file_path = tool_input.get("file_path", "")

    try:
        d = _dir(cwd)
        if not d.exists():
            return

        # Skip time-capsule internal files
        if "time-capsule/" in file_path or "time-capsule\\" in file_path:
            return

        # Load config
        config_f = d / "config.json"
        if not config_f.exists():
            return
        config = json.loads(config_f.read_text(encoding="utf-8"))
        if not config.get("auto_checkpoint", True):
            return

        # Check interval since last checkpoint
        min_interval = config.get("min_interval_seconds", 60)
        index_f = d / "index.jsonl"
        if index_f.exists():
            lines = [line for line in index_f.read_text(encoding="utf-8").splitlines() if line.strip()]
            if lines:
                try:
                    last = json.loads(lines[-1])
                    last_ts = datetime.fromisoformat(last["ts"])
                    now = datetime.now(timezone.utc)
                    elapsed = (now - last_ts).total_seconds()
                    if elapsed < min_interval:
                        return
                except Exception:
                    pass

        # Create checkpoint using git stash create (non-destructive)
        basename = Path(file_path).name if file_path else "unknown"
        label = f"auto before {tool_name} on {basename}"
        ts = datetime.now(timezone.utc).isoformat().replace(":", "-").replace("+", "").replace(".", "-")
        tag_name = f"time-capsule/{ts}"

        # git stash create: creates a stash commit without modifying working tree or stash stack
        result = subprocess.run(
            ["git", "stash", "create", "-m", f"time-capsule: {label}"],
            cwd=cwd, capture_output=True, text=True, timeout=30,
        )

        if result.returncode != 0 or not result.stdout.strip():
            # No changes to capture — that's fine
            return

        stash_sha = result.stdout.strip()

        # Create a lightweight tag pointing to this commit
        tag_result = subprocess.run(
            ["git", "tag", tag_name, stash_sha],
            cwd=cwd, capture_output=True, text=True, timeout=10,
        )
        if tag_result.returncode != 0:
            return

        # Record in index
        count = 0
        if index_f.exists():
            count = sum(1 for line in index_f.read_text(encoding="utf-8").splitlines() if line.strip())
        cid = count + 1

        entry = {
            "id": cid,
            "ts": datetime.now(timezone.utc).isoformat(),
            "label": label,
            "tag": tag_name,
        }
        with index_f.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

        # Update status
        status_lines = [
            f"Checkpoints: {cid} | Auto: on",
            f"Last: #{cid} \"{label}\" at {entry['ts'][:19]}",
        ]
        (d / "status.md").write_text("\n".join(status_lines) + "\n", encoding="utf-8")

    except Exception:
        pass

    # Never block — no output


if __name__ == "__main__":
    main()
