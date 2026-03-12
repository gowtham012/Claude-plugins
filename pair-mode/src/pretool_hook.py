#!/usr/bin/env python3
"""PreToolUse hook — physically blocks Write/Edit when pair-mode is paused."""
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

    try:
        cwd = data.get("cwd") or os.getcwd()
        d = Path(cwd) / "pair-mode"
        state_f = d / "state.json"

        if not state_f.exists():
            return

        # Always allow edits to pair-mode's own internal files
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if file_path:
            fp = Path(file_path)
            try:
                fp.relative_to(d)
                return  # internal file — allow
            except ValueError:
                pass

        state = json.loads(state_f.read_text(encoding="utf-8"))

        if not state.get("active"):
            return
        if not state.get("paused"):
            return

        # Paused — DENY the tool call
        edits = state.get("edits_since_review", 0)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"[pair-mode] BLOCKED: Paused for review. "
                    f"{edits} edits made. "
                    f"User must /pair-mode:approve or /pair-mode:reject "
                    f"before you can continue editing."
                ),
            }
        }
        print(json.dumps(output), flush=True)

    except Exception:
        pass


if __name__ == "__main__":
    main()
