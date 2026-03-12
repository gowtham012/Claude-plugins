#!/usr/bin/env python3
"""
Stop hook — runs after every Claude response.
If scope is locked, reminds Claude of the active scope boundaries.
Uses stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
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
        config_file = Path(cwd) / "scope-lock" / "config.json"
        if not config_file.exists():
            return

        config = json.loads(config_file.read_text(encoding="utf-8"))
        if not config.get("locked"):
            return

        paths = config.get("paths", [])
        reason = config.get("reason", "")

        paths_display = ", ".join(paths) if paths else "(none)"
        message = f"[scope-lock] Scope locked to: {paths_display}. Reason: {reason}"

        output = {"systemMessage": message}
        print(json.dumps(output), flush=True)

    except Exception:
        pass  # Never block Claude on unexpected errors


if __name__ == "__main__":
    main()
