#!/usr/bin/env python3
"""cost-guard MCP server — token budget & cost tracker."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("cost-guard")

CLAUDE_MD_IMPORT = "@cost-guard/budget-status.md"

PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "default": {"input": 3.00, "output": 15.00},
}


def _dir(cwd: str) -> Path:
    return Path(cwd) / "cost-guard"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default: dict) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default.copy()


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.rename(path)


def _estimate_cost(input_tokens: int, output_tokens: int, model: str = "default") -> float:
    prices = PRICING.get(model, PRICING["default"])
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000


def _regen_status(cwd: str) -> None:
    d = _dir(cwd)
    state = _load_json(d / "state.json", {})
    config = _load_json(d / "config.json", {})
    budget = config.get("budget_usd", 0)
    spent = state.get("all_time_cost_usd", 0)
    session_cost = state.get("session_cost_usd", 0)
    label = state.get("current_label", "")
    if budget > 0:
        pct = (spent / budget) * 100
        line = f"Budget: ${spent:.2f} / ${budget:.2f} ({pct:.1f}%) | Session: ${session_cost:.2f}"
    else:
        line = f"No budget set | Session: ${session_cost:.2f} | All-time: ${spent:.2f}"
    if label:
        line += f" | Label: {label}"
    (d / "budget-status.md").write_text(line + "\n", encoding="utf-8")


@mcp.tool()
def setup_project(cwd: str) -> str:
    """One-time setup. Creates cost-guard/ directory and CLAUDE.md import."""
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)
    (d / "sessions").mkdir(exist_ok=True)
    if not (d / "config.json").exists():
        _save_json(d / "config.json", {"budget_usd": 0, "warn_at_percent": 80.0, "hard_limit": False, "default_model": "claude-sonnet-4-20250514"})
    if not (d / "state.json").exists():
        _save_json(d / "state.json", {"session_id": _now(), "current_label": "", "session_input_tokens": 0, "session_output_tokens": 0, "session_cost_usd": 0.0, "all_time_input_tokens": 0, "all_time_output_tokens": 0, "all_time_cost_usd": 0.0, "last_updated": _now()})
    _regen_status(cwd)
    claude_md = Path(cwd) / "CLAUDE.md"
    if not claude_md.exists() or CLAUDE_MD_IMPORT not in claude_md.read_text(encoding="utf-8"):
        with claude_md.open("a", encoding="utf-8") as f:
            f.write(f"\n{CLAUDE_MD_IMPORT}\n")
    return f"cost-guard set up in {d}.\nAdded @import to CLAUDE.md.\nRestart Claude Code for auto-loading."


@mcp.tool()
def set_budget(cwd: str, budget_usd: float, warn_at_percent: float = 80.0, hard_limit: bool = True) -> str:
    """Set the spending budget in USD. Warns at threshold, optionally blocks when exceeded."""
    config = _load_json(_dir(cwd) / "config.json", {})
    config["budget_usd"] = budget_usd
    config["warn_at_percent"] = warn_at_percent
    config["hard_limit"] = hard_limit
    _save_json(_dir(cwd) / "config.json", config)
    _regen_status(cwd)
    mode = "HARD LIMIT (blocks tool calls)" if hard_limit else "SOFT WARNING only"
    return f"Budget set: ${budget_usd:.2f}, warn at {warn_at_percent}%, mode: {mode}"


@mcp.tool()
def get_report(cwd: str, scope: str = "session") -> str:
    """Returns a cost report. Scope: 'session', 'all', or 'task'."""
    d = _dir(cwd)
    state = _load_json(d / "state.json", {})
    config = _load_json(d / "config.json", {})
    budget = config.get("budget_usd", 0)
    if scope == "session":
        inp = state.get("session_input_tokens", 0)
        out = state.get("session_output_tokens", 0)
        cost = state.get("session_cost_usd", 0)
        title = "Session Report"
    else:
        inp = state.get("all_time_input_tokens", 0)
        out = state.get("all_time_output_tokens", 0)
        cost = state.get("all_time_cost_usd", 0)
        title = "All-Time Report"
    lines = [
        f"## {title}",
        f"- Input tokens: ~{inp:,}",
        f"- Output tokens: ~{out:,}",
        f"- Estimated cost: ${cost:.4f}",
    ]
    if budget > 0:
        remaining = max(0, budget - state.get("all_time_cost_usd", 0))
        pct = (state.get("all_time_cost_usd", 0) / budget) * 100
        lines.append(f"- Budget: ${budget:.2f} | Spent: {pct:.1f}% | Remaining: ${remaining:.4f}")
    label = state.get("current_label", "")
    if label:
        lines.append(f"- Current label: {label}")
    return "\n".join(lines)


@mcp.tool()
def log_usage(cwd: str, input_tokens: int, output_tokens: int, model: str = "claude-sonnet-4-20250514", label: str = "") -> str:
    """Manually log a usage entry."""
    d = _dir(cwd)
    state = _load_json(d / "state.json", {})
    cost = _estimate_cost(input_tokens, output_tokens, model)
    state["session_input_tokens"] = state.get("session_input_tokens", 0) + input_tokens
    state["session_output_tokens"] = state.get("session_output_tokens", 0) + output_tokens
    state["session_cost_usd"] = state.get("session_cost_usd", 0) + cost
    state["all_time_input_tokens"] = state.get("all_time_input_tokens", 0) + input_tokens
    state["all_time_output_tokens"] = state.get("all_time_output_tokens", 0) + output_tokens
    state["all_time_cost_usd"] = state.get("all_time_cost_usd", 0) + cost
    state["last_updated"] = _now()
    if label:
        state["current_label"] = label
    _save_json(d / "state.json", state)
    entry = json.dumps({"ts": _now(), "event": "usage", "input_tokens": input_tokens, "output_tokens": output_tokens, "model": model, "cost_usd": cost, "label": label or state.get("current_label", "")})
    with (d / "sessions" / "current.jsonl").open("a", encoding="utf-8") as f:
        f.write(entry + "\n")
    _regen_status(cwd)
    return f"Logged: ~{input_tokens} in, ~{output_tokens} out, ${cost:.4f}"


@mcp.tool()
def set_label(cwd: str, label: str) -> str:
    """Set the current task label for cost grouping."""
    state = _load_json(_dir(cwd) / "state.json", {})
    state["current_label"] = label
    _save_json(_dir(cwd) / "state.json", state)
    _regen_status(cwd)
    return f"Label set to '{label}'"


@mcp.tool()
def reset_session(cwd: str) -> str:
    """Clear session totals and start fresh. Archives current session log."""
    d = _dir(cwd)
    state = _load_json(d / "state.json", {})
    current_log = d / "sessions" / "current.jsonl"
    if current_log.exists() and current_log.stat().st_size > 0:
        archive_dir = d / "sessions" / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        ts = _now().replace(":", "-").replace(".", "-")
        current_log.rename(archive_dir / f"session-{ts}.jsonl")
    state["session_id"] = _now()
    state["session_input_tokens"] = 0
    state["session_output_tokens"] = 0
    state["session_cost_usd"] = 0.0
    state["last_updated"] = _now()
    _save_json(d / "state.json", state)
    _regen_status(cwd)
    return "Session reset. Previous session archived."


if __name__ == "__main__":
    mcp.run()
