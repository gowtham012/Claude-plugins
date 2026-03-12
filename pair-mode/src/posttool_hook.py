#!/usr/bin/env python3
"""PostToolUse hook — counts edits and injects pause when threshold reached."""
from __future__ import annotations

import json, os, sys
from datetime import datetime, timezone
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
        if state.get("paused"):
            return

        # Extract file path from hook data
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "(unknown)")

        # Increment edit counter
        state["edits_since_review"] = state.get("edits_since_review", 0) + 1

        # Log the edit
        state.setdefault("history", []).append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "edit",
            "files": [file_path],
            "approved": None,
        })

        max_edits = state.get("max_edits", 3)
        edits = state["edits_since_review"]

        # Check if we should pause
        if edits >= max_edits:
            state["paused"] = True

            # Collect files from recent edits since last review
            recent_files = []
            for h in reversed(state.get("history", [])):
                if h.get("action") == "edit":
                    recent_files.extend(h.get("files", []))
                    if len(recent_files) >= edits:
                        break
                elif h.get("action") in ("approve", "reject", "session_start"):
                    break
            file_list = ", ".join(dict.fromkeys(recent_files))  # deduplicate, preserve order

            # Write state before output
            tmp = state_f.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
            tmp.rename(state_f)

            # Update status.md
            status_f = d / "status.md"
            status_f.write_text(
                f"pair-mode: PAUSED for review\n"
                f"Edits since last review: {edits}\n"
                f"Files edited: {file_list}\n"
                f"Action required: user must /pair-mode:approve or /pair-mode:reject\n",
                encoding="utf-8",
            )

            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"[pair-mode] PAUSE — {edits} edits made. "
                        f"Ask the user to review before continuing. "
                        f"Files: {file_list}"
                    ),
                }
            }
            print(json.dumps(output), flush=True)
            return

        # Not pausing yet — just save state and update status
        tmp = state_f.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.rename(state_f)

        status_f = d / "status.md"
        status_f.write_text(
            f"pair-mode: active\n"
            f"Edits: {edits}/{max_edits} before next pause\n",
            encoding="utf-8",
        )

    except Exception:
        pass


if __name__ == "__main__":
    main()
