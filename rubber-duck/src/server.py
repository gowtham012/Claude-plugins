#!/usr/bin/env python3
"""rubber-duck MCP server — explain-before-you-code enforcer."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("rubber-duck")
CLAUDE_MD_IMPORT = "@rubber-duck/active-explanation.md"


def _dir(cwd: str) -> Path:
    return Path(cwd) / "rubber-duck"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _load(path: Path, default: dict) -> dict:
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: pass
    return default.copy()

def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.rename(path)


@mcp.tool()
def setup_project(cwd: str) -> str:
    """One-time setup. Creates rubber-duck/ directory and CLAUDE.md import."""
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)
    (d / "history").mkdir(exist_ok=True)
    if not (d / "state.json").exists():
        _save(d / "state.json", {"status": "idle", "task": "", "explanation": "", "approved_files": [], "feedback_history": []})
    (d / "active-explanation.md").write_text("No active explanation.\n", encoding="utf-8")
    claude_md = Path(cwd) / "CLAUDE.md"
    if not claude_md.exists() or CLAUDE_MD_IMPORT not in claude_md.read_text(encoding="utf-8"):
        with claude_md.open("a", encoding="utf-8") as f:
            f.write(f"\n{CLAUDE_MD_IMPORT}\n")
    return f"rubber-duck set up in {d}.\nAdded @import to CLAUDE.md.\nRestart Claude Code for auto-loading."


@mcp.tool()
def start_explanation(cwd: str, task: str) -> str:
    """Begin a new explain-before-you-code cycle."""
    d = _dir(cwd)
    state = _load(d / "state.json", {})
    state["status"] = "awaiting-explanation"
    state["task"] = task
    state["explanation"] = ""
    state["approved_files"] = []
    state["feedback_history"] = []
    state["created_at"] = _now()
    _save(d / "state.json", state)
    (d / "active-explanation.md").write_text(f"---\nstatus: awaiting-explanation\n---\n\n## Task\n{task}\n\n## Explanation\n(pending)\n", encoding="utf-8")
    _log(cwd, "task_started", {"task": task})
    return "Task registered. Now explain your approach in plain English — no code blocks. Then call submit_explanation."


@mcp.tool()
def submit_explanation(cwd: str, explanation: str, files_to_change: str) -> str:
    """Submit a prose explanation. Rejects code blocks. Requires files_to_change list."""
    if "```" in explanation:
        return "REJECTED: Your explanation contains code blocks. Describe your approach in plain English without code."
    if len(explanation.strip()) < 50:
        return "REJECTED: Explanation too short (min 50 chars). Describe what you'll change and why."
    files = [f.strip() for f in files_to_change.strip().split("\n") if f.strip()]
    if not files:
        return "REJECTED: files_to_change is empty. List the files you plan to create or modify."
    d = _dir(cwd)
    state = _load(d / "state.json", {})
    state["status"] = "awaiting-approval"
    state["explanation"] = explanation
    state["approved_files"] = files
    _save(d / "state.json", state)
    (d / "active-explanation.md").write_text(
        f"---\nstatus: awaiting-approval\n---\n\n## Task\n{state.get('task','')}\n\n## Explanation\n{explanation}\n\n## Files to Change\n" + "\n".join(f"- {f}" for f in files) + "\n",
        encoding="utf-8")
    _log(cwd, "explanation_submitted", {"files_count": len(files)})
    return "Explanation submitted. Ask the user: 'Does this approach sound right? Approve, revise (with feedback), or reject?'"


@mcp.tool()
def record_approval(cwd: str, decision: str, feedback: str = "") -> str:
    """Record user's decision: 'approved', 'revise', or 'rejected'."""
    if decision not in ("approved", "revise", "rejected"):
        return "REJECTED: decision must be 'approved', 'revise', or 'rejected'."
    d = _dir(cwd)
    state = _load(d / "state.json", {})
    if decision == "approved":
        state["status"] = "approved"
        _save(d / "state.json", state)
        _log(cwd, "decision", {"decision": "approved"})
        return f"Approved! You may now write code for: {', '.join(state.get('approved_files', []))}"
    elif decision == "revise":
        state["status"] = "awaiting-explanation"
        state["feedback_history"] = state.get("feedback_history", []) + [feedback]
        _save(d / "state.json", state)
        _log(cwd, "decision", {"decision": "revise", "feedback": feedback})
        return f"Revision requested. Feedback: {feedback}\nSubmit a new explanation addressing this feedback."
    else:
        state["status"] = "idle"
        state["task"] = ""
        _save(d / "state.json", state)
        _log(cwd, "decision", {"decision": "rejected"})
        return "Task rejected. Explanation cleared."


@mcp.tool()
def read_status(cwd: str) -> str:
    """Returns the current rubber-duck state."""
    state = _load(_dir(cwd) / "state.json", {"status": "idle"})
    lines = [f"Status: {state.get('status', 'idle')}"]
    if state.get("task"):
        lines.append(f"Task: {state['task']}")
    if state.get("explanation"):
        lines.append(f"Explanation: {state['explanation'][:200]}...")
    if state.get("approved_files"):
        lines.append(f"Approved files: {', '.join(state['approved_files'])}")
    return "\n".join(lines)


@mcp.tool()
def complete_task(cwd: str) -> str:
    """Mark the current task as done and archive."""
    d = _dir(cwd)
    state = _load(d / "state.json", {})
    ts = _now().replace(":", "-").replace(".", "-")
    src = d / "active-explanation.md"
    if src.exists():
        (d / "history").mkdir(exist_ok=True)
        src.rename(d / "history" / f"explanation-{ts}.md")
    state["status"] = "idle"
    state["task"] = ""
    state["explanation"] = ""
    state["approved_files"] = []
    _save(d / "state.json", state)
    (d / "active-explanation.md").write_text("No active explanation.\n", encoding="utf-8")
    _log(cwd, "task_completed", {})
    return "Task completed and archived."


def _log(cwd: str, event: str, data: dict) -> None:
    try:
        d = _dir(cwd)
        entry = json.dumps({"ts": _now(), "event": event, **data})
        with (d / "log.jsonl").open("a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    mcp.run()
