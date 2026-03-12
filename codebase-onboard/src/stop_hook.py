#!/usr/bin/env python3
"""
Stop hook — runs after every Claude response.
Checks if onboard.md exists and whether it is stale (>24 hours old).
Uses stdlib only; never blocks Claude on any error.
"""
from __future__ import annotations

import json
import os
import sys
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

    if data.get("stop_hook_active"):
        return

    cwd = data.get("cwd") or os.getcwd()

    try:
        onboard_file = Path(cwd) / "codebase-onboard" / "onboard.md"

        if not onboard_file.exists():
            output = {
                "systemMessage": (
                    "[codebase-onboard] No onboarding doc generated yet. "
                    "Run /codebase-onboard:onboard to create one."
                )
            }
            print(json.dumps(output), flush=True)
            return

        # Check if onboard.md is older than 24 hours
        mtime = onboard_file.stat().st_mtime
        mod_time = datetime.fromtimestamp(mtime, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = (now - mod_time).total_seconds() / 3600

        if age_hours > 24:
            days = int(age_hours // 24)
            output = {
                "systemMessage": (
                    f"[codebase-onboard] Onboarding doc is {days} day(s) old. "
                    "Run /codebase-onboard:refresh to update it."
                )
            }
            print(json.dumps(output), flush=True)

    except Exception:
        pass  # Never block Claude


if __name__ == "__main__":
    main()
