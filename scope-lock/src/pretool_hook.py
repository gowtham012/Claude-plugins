#!/usr/bin/env python3
"""
PreToolUse hook — runs before Read, Write, Edit, Bash, Glob, Grep tool calls.
BLOCKS file access outside the allowed scope when locked.
Uses stdlib only.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path


def _read_config(cwd: str) -> dict | None:
    """Read scope-lock config. Returns None if not found or unlocked."""
    config_file = Path(cwd) / "scope-lock" / "config.json"
    if not config_file.exists():
        return None
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
        if not config.get("locked"):
            return None
        return config
    except Exception:
        return None


def _is_scope_lock_internal(file_path: str, cwd: str) -> bool:
    """Check if a path is inside the scope-lock/ directory (always allowed)."""
    try:
        rel = os.path.relpath(file_path, cwd)
    except ValueError:
        return False
    return rel.startswith("scope-lock" + os.sep) or rel == "scope-lock"


def _make_relative(file_path: str, cwd: str) -> str | None:
    """Make a file path relative to cwd. Returns None if outside cwd."""
    try:
        rel = os.path.relpath(file_path, cwd)
    except ValueError:
        return None
    if rel.startswith(".."):
        return None
    return rel


def _path_matches(file_path: str, allowed_paths: list[str], cwd: str) -> bool:
    """Check if a file path matches any allowed glob pattern."""
    # Always allow scope-lock internal files
    if _is_scope_lock_internal(file_path, cwd):
        return True

    rel = _make_relative(file_path, cwd)
    if rel is None:
        return False

    for pattern in allowed_paths:
        # Match against the relative path
        if fnmatch.fnmatch(rel, pattern):
            return True
        # Also try matching just the path components
        # e.g. "src/**" should match "src/foo/bar.py"
        if "**" in pattern:
            # Convert ** glob to fnmatch: src/** -> src/*
            flat_pattern = pattern.replace("**", "*")
            if fnmatch.fnmatch(rel, flat_pattern):
                return True
            # Also check if the path starts with the prefix before **
            prefix = pattern.split("**")[0]
            if prefix and rel.startswith(prefix):
                return True
        # Check if the pattern matches a parent directory
        if fnmatch.fnmatch(rel.split(os.sep)[0], pattern):
            return True

    return False


def _extract_paths_from_bash(command: str) -> list[str]:
    """Extract potential file paths from a bash command string."""
    paths: list[str] = []
    # Split on common shell operators
    tokens = re.split(r'[|;&><\s]+', command)
    for token in tokens:
        token = token.strip("'\"")
        # Skip empty tokens, flags, and common commands
        if not token or token.startswith("-") or token in (
            "cat", "head", "tail", "ls", "cd", "echo", "printf", "mkdir",
            "rm", "cp", "mv", "touch", "chmod", "chown", "grep", "find",
            "sed", "awk", "sort", "uniq", "wc", "diff", "git", "python3",
            "python", "node", "npm", "npx", "uv", "pip", "pytest",
        ):
            continue
        # If it looks like a path (contains / or . or is a relative path)
        if "/" in token or "." in token or os.sep in token:
            paths.append(token)
    return paths


def _deny(reason: str) -> None:
    """Output a deny decision and exit."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"BLOCKED: {reason}",
        }
    }
    print(json.dumps(output), flush=True)


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except Exception:
        return

    cwd = data.get("cwd") or os.getcwd()
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    config = _read_config(cwd)
    if config is None:
        # Not locked or no config — allow everything
        return

    allowed_paths = config.get("paths", [])
    reason = config.get("reason", "")

    # Extract file path(s) based on tool type
    if tool_name in ("Read", "Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return  # No path to check
        if not _path_matches(file_path, allowed_paths, cwd):
            _deny(
                f"File '{file_path}' is outside the allowed scope. "
                f"Allowed paths: {', '.join(allowed_paths)}. "
                f"Reason for lock: {reason}"
            )
            return

    elif tool_name == "Glob":
        path = tool_input.get("path", "")
        if path and not _path_matches(path, allowed_paths, cwd):
            _deny(
                f"Glob path '{path}' is outside the allowed scope. "
                f"Allowed paths: {', '.join(allowed_paths)}. "
                f"Reason for lock: {reason}"
            )
            return

    elif tool_name == "Grep":
        path = tool_input.get("path", "")
        if path and not _path_matches(path, allowed_paths, cwd):
            _deny(
                f"Grep path '{path}' is outside the allowed scope. "
                f"Allowed paths: {', '.join(allowed_paths)}. "
                f"Reason for lock: {reason}"
            )
            return

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if not command:
            return
        paths_in_command = _extract_paths_from_bash(command)
        for p in paths_in_command:
            # Resolve relative paths against cwd
            full_path = p if os.path.isabs(p) else os.path.join(cwd, p)
            if not _path_matches(full_path, allowed_paths, cwd):
                _deny(
                    f"Command references '{p}' which is outside the allowed scope. "
                    f"Allowed paths: {', '.join(allowed_paths)}. "
                    f"Reason for lock: {reason}"
                )
                return

    # If we get here, allow the tool call (no output)


if __name__ == "__main__":
    main()
