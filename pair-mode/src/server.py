#!/usr/bin/env python3
"""
pair-mode MCP server (FastMCP).
Enforces ping-pong pair programming: Claude writes a block, pauses for
human review, then continues.  Tracks approval rate.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("pair-mode")

CLAUDE_MD_IMPORT = "@pair-mode/status.md"


def _dir(cwd: str) -> Path:
    return Path(cwd) / "pair-mode"


def _state_file(cwd: str) -> Path:
    return _dir(cwd) / "state.json"


def _status_file(cwd: str) -> Path:
    return _dir(cwd) / "status.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_state(cwd: str) -> dict:
    sf = _state_file(cwd)
    if sf.exists():
        return json.loads(sf.read_text(encoding="utf-8"))
    return {}


def _write_state(cwd: str, state: dict) -> None:
    sf = _state_file(cwd)
    tmp = sf.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.rename(sf)


def _update_status(cwd: str, state: dict) -> None:
    """Regenerate status.md from current state."""
    if not state.get("active"):
        text = "pair-mode: inactive\n"
    elif state.get("paused"):
        files = [
            h["files"] for h in state.get("history", [])
            if h.get("action") == "edit"
        ]
        recent = files[-state.get("edits_since_review", 0):] if files else []
        flat = [f for batch in recent for f in (batch if isinstance(batch, list) else [batch])]
        text = (
            f"pair-mode: PAUSED for review\n"
            f"Edits since last review: {state.get('edits_since_review', 0)}\n"
            f"Files edited: {', '.join(flat) if flat else '(none)'}\n"
            f"Action required: user must /pair-mode:approve or /pair-mode:reject\n"
        )
    else:
        text = (
            f"pair-mode: active\n"
            f"Edits: {state.get('edits_since_review', 0)}/{state.get('max_edits', 3)} before next pause\n"
        )
    _status_file(cwd).write_text(text, encoding="utf-8")


@mcp.tool()
def setup_project(cwd: str) -> str:
    """
    One-time setup for a project.
    Creates pair-mode/ directory, initializes state, and adds @import to CLAUDE.md.
    """
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)

    # Initialize state if not present
    sf = _state_file(cwd)
    if not sf.exists():
        state = {
            "active": False,
            "edits_since_review": 0,
            "max_edits": 3,
            "paused": False,
            "history": [],
        }
        _write_state(cwd, state)
        _update_status(cwd, state)

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
        f"pair-mode set up in {d}.\n"
        f"{claude_md_status}\n"
        "Restart Claude Code for auto-loading to take effect."
    )


@mcp.tool()
def start_pair(cwd: str, max_edits_before_pause: int = 3) -> str:
    """
    Starts a pair programming session.
    Claude will pause after every N edits for human review.
    Default: pause after 3 edits.
    """
    d = _dir(cwd)
    if not d.exists():
        return "REJECTED: Run setup_project first."

    state = _read_state(cwd)
    if state.get("active"):
        return (
            f"Already in a pair session. "
            f"Edits: {state.get('edits_since_review', 0)}/{state.get('max_edits', 3)}. "
            "Use end_pair to stop first."
        )

    state["active"] = True
    state["edits_since_review"] = 0
    state["max_edits"] = max(1, max_edits_before_pause)
    state["paused"] = False
    state["session_start"] = _now_iso()
    state["history"].append({
        "ts": _now_iso(),
        "action": "session_start",
        "files": [],
        "approved": None,
    })

    # Also save config.json for hooks to read
    config = {"max_edits_before_pause": state["max_edits"]}
    (d / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    _write_state(cwd, state)
    _update_status(cwd, state)

    return (
        f"Pair session started. Claude will pause after every "
        f"{state['max_edits']} edit(s) for your review."
    )


@mcp.tool()
def end_pair(cwd: str) -> str:
    """Ends the current pair programming session."""
    state = _read_state(cwd)
    if not state.get("active"):
        return "No active pair session."

    state["active"] = False
    state["paused"] = False
    state["history"].append({
        "ts": _now_iso(),
        "action": "session_end",
        "files": [],
        "approved": None,
    })

    _write_state(cwd, state)
    _update_status(cwd, state)

    return "Pair session ended."


@mcp.tool()
def approve(cwd: str) -> str:
    """
    User approves the last batch of edits. Resets the edit counter
    and unpauses so Claude can continue.
    """
    state = _read_state(cwd)
    if not state.get("active"):
        return "No active pair session."
    if not state.get("paused"):
        return "Not currently paused. Nothing to approve."

    state["paused"] = False
    state["edits_since_review"] = 0
    state["history"].append({
        "ts": _now_iso(),
        "action": "approve",
        "files": [],
        "approved": True,
    })

    _write_state(cwd, state)
    _update_status(cwd, state)

    return "Approved. Edit counter reset. Claude may continue."


@mcp.tool()
def reject(cwd: str, reason: str) -> str:
    """
    User rejects the last batch of edits with a reason.
    Resets the edit counter and unpauses so Claude can revise.
    """
    state = _read_state(cwd)
    if not state.get("active"):
        return "No active pair session."
    if not state.get("paused"):
        return "Not currently paused. Nothing to reject."

    state["paused"] = False
    state["edits_since_review"] = 0
    state["history"].append({
        "ts": _now_iso(),
        "action": "reject",
        "files": [],
        "approved": False,
        "reason": reason,
    })

    _write_state(cwd, state)
    _update_status(cwd, state)

    return f"Rejected: {reason}. Edit counter reset. Claude should revise."


@mcp.tool()
def get_stats(cwd: str) -> str:
    """
    Shows pair programming stats: total edits, approvals, rejections,
    approval rate, and session duration.
    """
    state = _read_state(cwd)
    if not state:
        return "No pair-mode state found. Run setup_project first."

    history = state.get("history", [])

    total_edits = sum(1 for h in history if h.get("action") == "edit")
    approvals = sum(1 for h in history if h.get("action") == "approve")
    rejections = sum(1 for h in history if h.get("action") == "reject")
    reviews = approvals + rejections
    approval_rate = (approvals / reviews * 100) if reviews > 0 else 0.0

    # Session duration
    session_start = state.get("session_start")
    if session_start and state.get("active"):
        start_dt = datetime.fromisoformat(session_start)
        now_dt = datetime.now(timezone.utc)
        duration = now_dt - start_dt
        minutes = int(duration.total_seconds() // 60)
        duration_str = f"{minutes}m"
    else:
        duration_str = "no active session"

    return (
        f"Pair-mode stats:\n"
        f"  Total edits:    {total_edits}\n"
        f"  Approvals:      {approvals}\n"
        f"  Rejections:     {rejections}\n"
        f"  Approval rate:  {approval_rate:.1f}%\n"
        f"  Session duration: {duration_str}\n"
        f"  Active: {state.get('active', False)}\n"
        f"  Paused: {state.get('paused', False)}"
    )


@mcp.tool()
def get_status(cwd: str) -> str:
    """
    Shows the current pair state: active/paused, edits since last review.
    """
    state = _read_state(cwd)
    if not state:
        return "No pair-mode state found. Run setup_project first."

    if not state.get("active"):
        return "pair-mode: inactive. Use start_pair to begin."

    if state.get("paused"):
        return (
            f"pair-mode: PAUSED for review.\n"
            f"Edits since last review: {state.get('edits_since_review', 0)}\n"
            f"Action required: approve or reject before continuing."
        )

    return (
        f"pair-mode: active.\n"
        f"Edits since last review: {state.get('edits_since_review', 0)}/{state.get('max_edits', 3)}"
    )


if __name__ == "__main__":
    mcp.run()
