#!/usr/bin/env python3
"""Stop hook — reminds Claude of current rubber-duck phase."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip(): return
        data = json.loads(raw)
    except Exception: return
    cwd = data.get("cwd") or os.getcwd()
    try:
        state_f = Path(cwd) / "rubber-duck" / "state.json"
        if not state_f.exists(): return
        state = json.loads(state_f.read_text())
        status = state.get("status", "idle")
        if status == "idle": return
        msgs = {
            "awaiting-explanation": "[rubber-duck] You have an active task but have not explained your approach yet. Describe your plan in plain English before writing any code.",
            "awaiting-approval": "[rubber-duck] Your explanation is pending user approval. Ask the user to approve, revise, or reject.",
            "approved": "[rubber-duck] Explanation approved. You may write code for the approved files.",
        }
        msg = msgs.get(status)
        if msg:
            print(json.dumps({"systemMessage": msg}), flush=True)
    except Exception: pass

if __name__ == "__main__":
    main()
