#!/usr/bin/env python3
"""PostToolUse hook — runs tests after every Write/Edit and detects regressions.

Improvements over v1:
- Debouncing: skips test run if less than debounce_seconds since last run
- Skip patterns: ignores .md, .json, .txt, .gitignore edits
- Skip internal: ignores edits inside regression-sentinel/ directory
- Real auto-revert: restores file from snapshot when tests fail and auto_revert is ON
- Stronger stop message when consecutive failures hit threshold
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

MAX_OUTPUT_SNIPPET = 500
MAX_RESULTS = 50
TIMEOUT = 30

SKIP_EXTENSIONS = {".md", ".json", ".txt", ".gitignore", ".yml", ".yaml", ".toml", ".lock", ".cfg", ".ini"}


def _dir(cwd: str) -> Path:
    return Path(cwd) / "regression-sentinel"


def _config_path(cwd: str) -> Path:
    return _dir(cwd) / "config.json"


def _state_path(cwd: str) -> Path:
    return _dir(cwd) / "state.json"


def _status_path(cwd: str) -> Path:
    return _dir(cwd) / "test-status.md"


def _snapshots_dir(cwd: str) -> Path:
    return _dir(cwd) / "snapshots"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state(cwd: str) -> dict:
    sp = _state_path(cwd)
    if sp.exists():
        try:
            return json.loads(sp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "test_command": "",
        "auto_revert": False,
        "max_failures": 3,
        "debounce_seconds": 5,
        "results": [],
        "consecutive_failures": 0,
        "last_test_time": 0,
    }


def _save_state(cwd: str, state: dict) -> None:
    _dir(cwd).mkdir(parents=True, exist_ok=True)
    _state_path(cwd).write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )


def _regenerate_status(cwd: str, state: dict) -> None:
    results = state.get("results", [])
    consecutive = state.get("consecutive_failures", 0)
    auto_revert = state.get("auto_revert", False)
    test_cmd = state.get("test_command", "(not configured)")

    if not results:
        status_line = "No tests run yet."
    else:
        last = results[-1]
        icon = "PASS" if last["passed"] else "FAIL"
        total_pass = sum(1 for r in results if r["passed"])
        total_fail = len(results) - total_pass
        status_line = (
            f"Last: {icon} | "
            f"History: {total_pass} passed, {total_fail} failed | "
            f"Streak: {consecutive} consecutive failures | "
            f"Auto-revert: {'ON' if auto_revert else 'OFF'}"
        )

    content = (
        f"# Regression Sentinel Status\n\n"
        f"**Test command:** `{test_cmd}`\n\n"
        f"{status_line}\n"
    )
    _status_path(cwd).write_text(content, encoding="utf-8")


def _should_skip_file(file_path: str, cwd: str) -> bool:
    """Return True if we should skip running tests for this file."""
    if not file_path:
        return False

    p = Path(file_path)

    # Skip files inside regression-sentinel/ directory
    try:
        sentinel_dir = _dir(cwd)
        if sentinel_dir.exists() and p.is_relative_to(sentinel_dir):
            return True
        # Also check string-based (handles cases where path isn't resolved)
        if "regression-sentinel/" in file_path or "regression-sentinel\\" in file_path:
            return True
    except (ValueError, TypeError):
        pass

    # Skip files matching skip extensions
    suffix = p.suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return True
    # Also handle dotfiles like .gitignore (no suffix, name starts with .)
    if p.name.lower() in {".gitignore", ".dockerignore", ".editorconfig", ".prettierrc"}:
        return True

    return False


def _get_snapshot_path(cwd: str, file_path: str) -> Path:
    """Get the snapshot path for a given file."""
    basename = Path(file_path).name
    return _snapshots_dir(cwd) / f"{basename}.bak"


def _restore_from_snapshot(cwd: str, file_path: str) -> bool:
    """Restore a file from its snapshot. Returns True if successful."""
    snapshot = _get_snapshot_path(cwd, file_path)
    if not snapshot.exists():
        return False
    try:
        target = Path(file_path)
        shutil.copy2(str(snapshot), str(target))
        return True
    except Exception:
        return False


def _output_hook(message: str) -> None:
    """Output the PostToolUse hook JSON to stdout."""
    hook_output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": message,
        }
    }
    print(json.dumps(hook_output))


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
        # Check if regression-sentinel is configured for this project
        if not _config_path(cwd).exists():
            return

        config = json.loads(_config_path(cwd).read_text(encoding="utf-8"))
        test_cmd = config.get("test_command", "")
        if not test_cmd:
            return

        auto_revert = config.get("auto_revert", False)
        max_failures = config.get("max_failures", 3)
        debounce_seconds = config.get("debounce_seconds", 5)

        # Extract file_path from tool_input if available
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        # Skip files that shouldn't trigger tests
        if _should_skip_file(file_path, cwd):
            return

        # Debounce: skip if less than debounce_seconds since last test run
        state = _load_state(cwd)
        last_test_time = state.get("last_test_time", 0)
        now = time.time()
        if last_test_time and (now - last_test_time) < debounce_seconds:
            return

        # Run tests
        try:
            result = subprocess.run(
                test_cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
            passed = result.returncode == 0
            output = (result.stdout + "\n" + result.stderr).strip()
        except subprocess.TimeoutExpired:
            passed = False
            output = f"Test command timed out after {TIMEOUT} seconds."
        except Exception as e:
            passed = False
            output = f"Failed to run tests: {e}"

        # Update state
        state["last_test_time"] = now
        snippet = output[:MAX_OUTPUT_SNIPPET]
        state["results"].append({
            "ts": _now_iso(),
            "passed": passed,
            "output_snippet": snippet,
            "file": file_path,
        })
        if len(state["results"]) > MAX_RESULTS:
            state["results"] = state["results"][-MAX_RESULTS:]

        if passed:
            state["consecutive_failures"] = 0
        else:
            state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1

        _save_state(cwd, state)
        _regenerate_status(cwd, state)

        # Produce hook output
        if not passed:
            consecutive = state["consecutive_failures"]

            msg_parts = [
                f"REGRESSION DETECTED: Tests failed after editing '{file_path}'.",
                f"Consecutive failures: {consecutive}/{max_failures}.",
                f"Output: {snippet[:300]}",
            ]

            # Auto-revert: actually restore the file from snapshot
            if auto_revert and file_path:
                restored = _restore_from_snapshot(cwd, file_path)
                if restored:
                    msg_parts.append(
                        f"AUTO-REVERTED: The file '{file_path}' has been restored to its pre-edit state. "
                        "Your change broke tests and was rolled back. Try a different approach."
                    )
                else:
                    msg_parts.append(
                        f"Auto-revert is ON but no snapshot found for '{file_path}'. "
                        "You should manually revert this change and try a different approach."
                    )

            # Strong stop message at threshold
            if consecutive >= max_failures:
                msg_parts.append(
                    f"STOP: You have hit {consecutive} consecutive test failures (threshold: {max_failures}). "
                    "Do NOT make another edit. Step back and reassess your approach entirely. "
                    "Read the test output carefully, consider what you are doing wrong, "
                    "and explain your new plan before making any changes."
                )

            _output_hook(" ".join(msg_parts))
        else:
            _output_hook("Tests passed after file edit.")

    except Exception:
        pass


if __name__ == "__main__":
    main()
