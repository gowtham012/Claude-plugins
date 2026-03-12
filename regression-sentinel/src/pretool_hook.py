#!/usr/bin/env python3
"""PreToolUse hook — captures file snapshots before Write/Edit for revert capability.

Reads stdin JSON from Claude Code, extracts file_path from tool_input,
and saves a copy of the current file content to regression-sentinel/snapshots/.
This enables the PostToolUse hook to perform actual auto-revert on test failure.

No deny output — this hook silently captures snapshots and always allows the tool to proceed.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def _dir(cwd: str) -> Path:
    return Path(cwd) / "regression-sentinel"


def _config_path(cwd: str) -> Path:
    return _dir(cwd) / "config.json"


def _snapshots_dir(cwd: str) -> Path:
    return _dir(cwd) / "snapshots"


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
        # Only activate if regression-sentinel is configured
        if not _config_path(cwd).exists():
            return

        # Extract file_path from tool_input
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return

        source = Path(file_path)

        # Skip files inside regression-sentinel/ directory
        sentinel_dir = _dir(cwd)
        try:
            if sentinel_dir.exists() and source.is_relative_to(sentinel_dir):
                return
        except (ValueError, TypeError):
            pass
        if "regression-sentinel/" in file_path or "regression-sentinel\\" in file_path:
            return

        # Skip if the source file doesn't exist yet (new file creation)
        if not source.exists():
            return

        # Save snapshot
        snap_dir = _snapshots_dir(cwd)
        snap_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snap_dir / f"{source.name}.bak"
        shutil.copy2(str(source), str(snapshot_path))

    except Exception:
        # Never fail — silently ignore errors
        pass


if __name__ == "__main__":
    main()
