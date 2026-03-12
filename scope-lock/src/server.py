#!/usr/bin/env python3
"""
scope-lock MCP server (FastMCP).
6 tools: setup_project, lock_scope, unlock_scope, add_path, remove_path, get_status.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("scope-lock")

CLAUDE_MD_IMPORT = "@scope-lock/status.md"


def _dir(cwd: str) -> Path:
    return Path(cwd) / "scope-lock"


def _config_file(cwd: str) -> Path:
    return _dir(cwd) / "config.json"


def _status_file(cwd: str) -> Path:
    return _dir(cwd) / "status.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_config(cwd: str) -> dict:
    cfg = _config_file(cwd)
    if not cfg.exists():
        return {"locked": False, "paths": [], "reason": "", "locked_at": ""}
    return json.loads(cfg.read_text(encoding="utf-8"))


def _write_config(cwd: str, config: dict) -> None:
    cfg = _config_file(cwd)
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _update_status(cwd: str, config: dict) -> None:
    status = _status_file(cwd)
    status.parent.mkdir(parents=True, exist_ok=True)

    if config["locked"]:
        paths_list = "\n".join(f"- `{p}`" for p in config["paths"]) or "- (none)"
        content = (
            f"# Scope Lock — ACTIVE\n\n"
            f"**Status:** LOCKED\n"
            f"**Reason:** {config['reason']}\n"
            f"**Locked at:** {config['locked_at']}\n\n"
            f"## Allowed paths\n{paths_list}\n\n"
            f"All file access outside these paths will be BLOCKED.\n"
            f"The `scope-lock/` directory is always allowed.\n"
        )
    else:
        content = (
            "# Scope Lock — INACTIVE\n\n"
            "**Status:** Unlocked\n\n"
            "No file access restrictions are active.\n"
            "Use `/scope-lock:lock` to define allowed paths.\n"
        )

    status.write_text(content, encoding="utf-8")


@mcp.tool()
def setup_project(cwd: str) -> str:
    """
    One-time setup for a project.
    Creates scope-lock/ directory, initializes config, and adds @import to CLAUDE.md.
    """
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)

    # Initialize config if not present
    if not _config_file(cwd).exists():
        config = {"locked": False, "paths": [], "reason": "", "locked_at": ""}
        _write_config(cwd, config)
    else:
        config = _read_config(cwd)

    _update_status(cwd, config)

    # Append @import to CLAUDE.md if not already present
    claude_md = Path(cwd) / "CLAUDE.md"
    already_imported = False
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")
        already_imported = CLAUDE_MD_IMPORT in content

    if not already_imported:
        with claude_md.open("a", encoding="utf-8") as f:
            f.write(f"\n{CLAUDE_MD_IMPORT}\n")
        claude_md_status = "Added @import to CLAUDE.md."
    else:
        claude_md_status = "CLAUDE.md already has the @import line."

    return (
        f"scope-lock set up in {d}.\n"
        f"{claude_md_status}\n"
        "Restart Claude Code for auto-loading to take effect."
    )


@mcp.tool()
def lock_scope(cwd: str, paths: list[str], reason: str) -> str:
    """
    Lock the scope to specific paths. Only files matching these glob patterns
    will be accessible. All other file access will be blocked.

    Args:
        cwd: Current working directory.
        paths: List of allowed glob patterns (e.g. ["src/**", "tests/**"]).
        reason: Why the scope is being locked.
    """
    if not paths:
        return "REJECTED: Must provide at least one path pattern."

    config = {
        "locked": True,
        "paths": paths,
        "reason": reason,
        "locked_at": _now_iso(),
    }
    _write_config(cwd, config)
    _update_status(cwd, config)

    paths_display = ", ".join(f"`{p}`" for p in paths)
    return (
        f"Scope LOCKED.\n"
        f"Allowed paths: {paths_display}\n"
        f"Reason: {reason}\n"
        f"All file access outside these paths will be blocked."
    )


@mcp.tool()
def unlock_scope(cwd: str) -> str:
    """
    Unlock the scope, removing all file access restrictions.
    """
    config = {"locked": False, "paths": [], "reason": "", "locked_at": ""}
    _write_config(cwd, config)
    _update_status(cwd, config)

    return "Scope UNLOCKED. All file access restrictions removed."


@mcp.tool()
def add_path(cwd: str, path: str) -> str:
    """
    Add a single path pattern to the allowed list.

    Args:
        cwd: Current working directory.
        path: Glob pattern to add (e.g. "docs/**").
    """
    config = _read_config(cwd)
    if not config["locked"]:
        return "REJECTED: Scope is not locked. Use lock_scope first."

    if path in config["paths"]:
        return f"Path `{path}` is already in the allowed list."

    config["paths"].append(path)
    _write_config(cwd, config)
    _update_status(cwd, config)

    return f"Added `{path}` to allowed paths. Now allowing: {', '.join(config['paths'])}"


@mcp.tool()
def remove_path(cwd: str, path: str) -> str:
    """
    Remove a single path pattern from the allowed list.

    Args:
        cwd: Current working directory.
        path: Glob pattern to remove.
    """
    config = _read_config(cwd)
    if not config["locked"]:
        return "REJECTED: Scope is not locked."

    if path not in config["paths"]:
        return f"Path `{path}` is not in the allowed list. Current paths: {', '.join(config['paths'])}"

    config["paths"].remove(path)
    _write_config(cwd, config)
    _update_status(cwd, config)

    if not config["paths"]:
        return f"Removed `{path}`. WARNING: No paths remaining — all file access will be blocked."

    return f"Removed `{path}`. Remaining allowed paths: {', '.join(config['paths'])}"


@mcp.tool()
def get_status(cwd: str) -> str:
    """
    Shows current scope lock status: locked/unlocked, allowed paths, reason.
    """
    config = _read_config(cwd)

    if not config["locked"]:
        return "Scope: UNLOCKED. No file access restrictions active."

    paths_display = "\n".join(f"  - {p}" for p in config["paths"]) or "  (none)"
    return (
        f"Scope: LOCKED\n"
        f"Reason: {config['reason']}\n"
        f"Locked at: {config['locked_at']}\n"
        f"Allowed paths:\n{paths_display}"
    )


if __name__ == "__main__":
    mcp.run()
