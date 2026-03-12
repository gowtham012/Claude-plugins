#!/usr/bin/env python3
"""
regression-sentinel MCP server (FastMCP).
7 tools: setup_project, configure, run_tests, get_status, toggle_auto_revert, clear_history, revert_last.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("regression-sentinel")

CLAUDE_MD_IMPORT = "@regression-sentinel/test-status.md"

# Test runner detection: (manifest file, indicator, test command)
TEST_RUNNERS = [
    # JS/TS — vitest
    ("vitest.config.ts", None, "npx vitest run"),
    ("vitest.config.js", None, "npx vitest run"),
    ("vitest.config.mts", None, "npx vitest run"),
    # JS/TS — jest
    ("jest.config.ts", None, "npx jest"),
    ("jest.config.js", None, "npx jest"),
    ("jest.config.mjs", None, "npx jest"),
    # JS/TS — package.json with test script
    ("package.json", "test", "npm test"),
    # Python — pytest
    ("pyproject.toml", "pytest", "pytest"),
    ("pytest.ini", None, "pytest"),
    ("setup.cfg", "pytest", "pytest"),
    ("conftest.py", None, "pytest"),
    # Python — unittest (fallback)
    ("pyproject.toml", None, "python -m pytest"),
    # Rust
    ("Cargo.toml", None, "cargo test"),
    # Go
    ("go.mod", None, "go test ./..."),
    # Ruby
    ("Gemfile", "rspec", "bundle exec rspec"),
    ("Rakefile", None, "bundle exec rake test"),
    # Java — Maven
    ("pom.xml", None, "mvn test"),
    # Java — Gradle
    ("build.gradle", None, "gradle test"),
    ("build.gradle.kts", None, "gradle test"),
    # Elixir
    ("mix.exs", None, "mix test"),
    # PHP
    ("phpunit.xml", None, "vendor/bin/phpunit"),
    ("phpunit.xml.dist", None, "vendor/bin/phpunit"),
]

MAX_RESULTS = 50
MAX_OUTPUT_SNIPPET = 500


def _dir(cwd: str) -> Path:
    return Path(cwd) / "regression-sentinel"


def _config_path(cwd: str) -> Path:
    return _dir(cwd) / "config.json"


def _state_path(cwd: str) -> Path:
    return _dir(cwd) / "state.json"


def _status_path(cwd: str) -> Path:
    return _dir(cwd) / "test-status.md"


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
    # Also write config.json (subset used by the hook)
    config = {
        "test_command": state.get("test_command", ""),
        "auto_revert": state.get("auto_revert", False),
        "max_failures": state.get("max_failures", 3),
        "debounce_seconds": state.get("debounce_seconds", 5),
    }
    _config_path(cwd).write_text(
        json.dumps(config, indent=2), encoding="utf-8"
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


def _detect_test_runner(cwd: str) -> str | None:
    root = Path(cwd)
    for manifest, indicator, command in TEST_RUNNERS:
        manifest_path = root / manifest
        if not manifest_path.exists():
            continue
        if indicator is not None:
            try:
                content = manifest_path.read_text(encoding="utf-8")
                if indicator not in content:
                    continue
            except Exception:
                continue
        return command
    return None


@mcp.tool()
def setup_project(cwd: str) -> str:
    """
    One-time setup for regression-sentinel in a project.
    Creates regression-sentinel/ directory, detects test runner,
    saves config.json, and adds @import to CLAUDE.md.
    """
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)

    # Detect test runner
    detected = _detect_test_runner(cwd)

    state = _load_state(cwd)
    if detected and not state.get("test_command"):
        state["test_command"] = detected

    _save_state(cwd, state)
    _regenerate_status(cwd, state)

    # Append @import to CLAUDE.md if not already present
    claude_md = Path(cwd) / "CLAUDE.md"
    already_imported = False
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")
        already_imported = CLAUDE_MD_IMPORT in content

    if not already_imported:
        with claude_md.open("a", encoding="utf-8") as f:
            f.write(f"\n{CLAUDE_MD_IMPORT}\n")
        claude_md_status = "Added @import to CLAUDE.md."
    else:
        claude_md_status = "CLAUDE.md already has the @import line."

    runner_msg = f"Detected test runner: `{detected}`" if detected else "No test runner detected. Use /regression-sentinel:configure to set one."

    return (
        f"regression-sentinel set up in {d}.\n"
        f"{runner_msg}\n"
        f"{claude_md_status}\n"
        "Restart Claude Code for auto-loading to take effect."
    )


@mcp.tool()
def configure(
    cwd: str,
    test_command: str = "",
    auto_revert: bool = False,
    max_failures: int = 3,
    debounce_seconds: int = 5,
) -> str:
    """
    Configure the test command, auto-revert toggle, max consecutive failures threshold,
    and debounce interval (seconds between test runs).
    """
    state = _load_state(cwd)

    if test_command:
        state["test_command"] = test_command
    state["auto_revert"] = auto_revert
    state["max_failures"] = max_failures
    state["debounce_seconds"] = debounce_seconds

    _save_state(cwd, state)
    _regenerate_status(cwd, state)

    return (
        f"Configuration updated.\n"
        f"  test_command: {state['test_command']}\n"
        f"  auto_revert: {state['auto_revert']}\n"
        f"  max_failures: {state['max_failures']}\n"
        f"  debounce_seconds: {state['debounce_seconds']}"
    )


@mcp.tool()
def run_tests(cwd: str) -> str:
    """
    Runs the configured test command and returns pass/fail with output.
    """
    state = _load_state(cwd)
    test_cmd = state.get("test_command", "")
    if not test_cmd:
        return "ERROR: No test command configured. Use /regression-sentinel:configure to set one."

    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        passed = result.returncode == 0
        output = (result.stdout + "\n" + result.stderr).strip()
    except subprocess.TimeoutExpired:
        passed = False
        output = "ERROR: Test command timed out after 60 seconds."
    except Exception as e:
        passed = False
        output = f"ERROR: Failed to run tests: {e}"

    # Update state
    snippet = output[:MAX_OUTPUT_SNIPPET]
    state["results"].append({
        "ts": _now_iso(),
        "passed": passed,
        "output_snippet": snippet,
    })
    # Keep only last MAX_RESULTS
    if len(state["results"]) > MAX_RESULTS:
        state["results"] = state["results"][-MAX_RESULTS:]

    if passed:
        state["consecutive_failures"] = 0
    else:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1

    _save_state(cwd, state)
    _regenerate_status(cwd, state)

    status = "PASSED" if passed else "FAILED"
    return f"Tests {status}.\n\nOutput:\n{output[:2000]}"


@mcp.tool()
def get_status(cwd: str) -> str:
    """
    Shows test pass/fail history, current streak, and last test output.
    """
    state = _load_state(cwd)
    results = state.get("results", [])
    consecutive = state.get("consecutive_failures", 0)
    auto_revert = state.get("auto_revert", False)
    test_cmd = state.get("test_command", "(not configured)")
    max_fail = state.get("max_failures", 3)

    debounce = state.get("debounce_seconds", 5)

    lines = [
        f"Test command: {test_cmd}",
        f"Auto-revert: {'ON' if auto_revert else 'OFF'}",
        f"Max consecutive failures: {max_fail}",
        f"Debounce interval: {debounce}s",
        f"Consecutive failures: {consecutive}",
        f"Total runs: {len(results)}",
    ]

    if results:
        total_pass = sum(1 for r in results if r["passed"])
        total_fail = len(results) - total_pass
        lines.append(f"Pass/Fail: {total_pass}/{total_fail}")

        lines.append("\nRecent results (last 10):")
        for r in results[-10:]:
            icon = "PASS" if r["passed"] else "FAIL"
            lines.append(f"  [{r['ts']}] {icon}")

        last = results[-1]
        lines.append(f"\nLast output snippet:\n{last.get('output_snippet', '(none)')}")
    else:
        lines.append("\nNo test runs yet.")

    return "\n".join(lines)


@mcp.tool()
def toggle_auto_revert(cwd: str, enabled: bool) -> str:
    """
    Toggle auto-revert on or off. When enabled, the PostToolUse hook will
    automatically restore files from pre-edit snapshots when tests fail.
    """
    state = _load_state(cwd)
    state["auto_revert"] = enabled
    _save_state(cwd, state)
    _regenerate_status(cwd, state)

    status = "ON" if enabled else "OFF"
    return f"Auto-revert is now {status}."


@mcp.tool()
def clear_history(cwd: str) -> str:
    """
    Clear all test run history and reset consecutive failure count.
    """
    state = _load_state(cwd)
    state["results"] = []
    state["consecutive_failures"] = 0
    _save_state(cwd, state)
    _regenerate_status(cwd, state)

    return "Test history cleared. Consecutive failure count reset to 0."


@mcp.tool()
def revert_last(cwd: str) -> str:
    """
    Restore the most recently snapshotted file from regression-sentinel/snapshots/.
    This reverts the last edited file to its pre-edit state.
    """
    snap_dir = _dir(cwd) / "snapshots"
    if not snap_dir.exists():
        return "ERROR: No snapshots directory found. No files have been snapshotted yet."

    # Find the most recently modified .bak file
    bak_files = sorted(snap_dir.glob("*.bak"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not bak_files:
        return "ERROR: No snapshot files found."

    latest = bak_files[0]
    original_name = latest.stem  # e.g., "foo.py" from "foo.py.bak"

    # Try to find the original file in the project
    # Check state for the last edited file path
    state = _load_state(cwd)
    results = state.get("results", [])

    target_path = None
    for r in reversed(results):
        fp = r.get("file", "")
        if fp and Path(fp).name == original_name:
            target_path = fp
            break

    if not target_path:
        return (
            f"ERROR: Found snapshot '{latest.name}' but could not determine "
            f"the original file path. The snapshot is at: {latest}"
        )

    try:
        shutil.copy2(str(latest), target_path)
        return f"Reverted '{target_path}' from snapshot '{latest.name}'."
    except Exception as e:
        return f"ERROR: Failed to restore file: {e}"


if __name__ == "__main__":
    mcp.run()
