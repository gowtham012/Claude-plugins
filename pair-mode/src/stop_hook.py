#!/usr/bin/env python3
"""Stop hook — reminds Claude of pair-mode state after every response."""
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
        d = Path(cwd) / "pair-mode"
        state_f = d / "state.json"
        if not state_f.exists():
            return

        state = json.loads(state_f.read_text(encoding="utf-8"))
        if not state.get("active"):
            return

        edits = state.get("edits_since_review", 0)
        max_edits = state.get("max_edits", 3)

        if state.get("paused"):
            msg = (
                f"[pair-mode] PAUSED for review. "
                f"{edits} edits since last review. "
                f"Ask user to approve or reject before continuing."
            )
            print(json.dumps({"systemMessage": msg}), flush=True)
        else:
            msg = (
                f"[pair-mode] Active. "
                f"{edits}/{max_edits} edits before next pause."
            )
            print(json.dumps({"systemMessage": msg}), flush=True)

    except Exception:
        pass


if __name__ == "__main__":
    main()
