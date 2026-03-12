#!/usr/bin/env python3
"""PreToolUse hook — blocks Write/Edit unless explanation is approved."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

CONFIG_EXTENSIONS = {".json", ".toml", ".yaml", ".yml", ".cfg", ".ini", ".md", ".txt", ".gitignore", ".env"}

def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip(): return
        data = json.loads(raw)
    except Exception: return

    cwd = data.get("cwd") or os.getcwd()
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path: return

    try:
        d = Path(cwd) / "rubber-duck"
        state_f = d / "state.json"
        if not state_f.exists(): return  # Not set up, allow

        state = json.loads(state_f.read_text())
        status = state.get("status", "idle")
        if status == "idle": return  # No active session

        # Always allow rubber-duck internal files
        if "rubber-duck/" in file_path or "rubber-duck\\" in file_path: return
        # Always allow config/meta files
        ext = Path(file_path).suffix.lower()
        if ext in CONFIG_EXTENSIONS: return

        if status in ("awaiting-explanation", "awaiting-approval"):
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"BLOCKED: You must explain your approach and get approval before writing code. Status: {status}. Use /explain or call start_explanation.",
                }
            }
            print(json.dumps(output), flush=True)
            return

        if status == "approved":
            approved = state.get("approved_files", [])
            fp = str(Path(file_path).resolve())
            cwd_resolved = str(Path(cwd).resolve())
            rel = fp.replace(cwd_resolved + "/", "").replace(cwd_resolved + "\\", "")
            if not any(rel == af or rel.endswith("/" + af) or af.endswith("/" + rel) for af in approved):
                if not any(af in rel or rel in af for af in approved):
                    output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": f"BLOCKED: '{rel}' is not in the approved files list. Approved: {', '.join(approved)}. Submit a revised explanation to add this file.",
                        }
                    }
                    print(json.dumps(output), flush=True)
    except Exception: pass

if __name__ == "__main__":
    main()
