#!/usr/bin/env python3
"""PreToolUse hook — enforces hard budget limits."""
from __future__ import annotations
import json, os, sys
from pathlib import Path


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
        d = Path(cwd) / "cost-guard"
        config_f = d / "config.json"
        state_f = d / "state.json"

        if not config_f.exists() or not state_f.exists():
            return

        config = json.loads(config_f.read_text())
        budget = config.get("budget_usd", 0)
        if budget <= 0 or not config.get("hard_limit", False):
            return

        state = json.loads(state_f.read_text())
        spent = state.get("all_time_cost_usd", 0)

        if spent >= budget:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"BUDGET EXCEEDED: ${spent:.2f} spent of ${budget:.2f} budget. "
                        "Run /cost-guard:budget to increase your limit."
                    ),
                }
            }
            print(json.dumps(output), flush=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
