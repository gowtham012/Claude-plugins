# regression-sentinel

A Claude Code plugin that runs tests automatically after every file edit, detects regressions instantly, and auto-reverts breaking changes.

## The Problem

When Claude edits code, it can silently break existing functionality. Without continuous testing, regressions go unnoticed until much later, making them harder to fix.

## The Solution

regression-sentinel hooks into every Write and Edit tool call. Before each edit, a PreToolUse hook snapshots the file. After each change, a PostToolUse hook runs your test suite. If tests fail with auto-revert enabled, the file is automatically restored to its pre-edit state.

### Features

- **Automatic test runs** -- PostToolUse hook runs tests after every Write/Edit
- **Debouncing** -- skips test runs if less than N seconds since the last run (default 5s, configurable)
- **Smart skip patterns** -- ignores edits to .md, .json, .txt, .gitignore, and other non-code files
- **Pre-edit snapshots** -- PreToolUse hook saves file content before every edit
- **Real auto-revert** -- when tests fail and auto-revert is ON, the file is actually restored from snapshot
- **Consecutive failure enforcement** -- after N failures (default 3), Claude is told to STOP and reassess
- **Manual revert tool** -- `revert_last` MCP tool to restore the most recently snapshotted file
- **Status in CLAUDE.md** -- test status is always visible via @import
- **Test runner auto-detection** -- detects pytest, vitest, jest, cargo test, go test, and more

## Setup

```bash
# Install the plugin, then in your project:
/regression-sentinel:setup
```

This creates a `regression-sentinel/` directory, detects your test runner, and adds a status @import to CLAUDE.md.

## Commands

| Command | Description |
|---------|-------------|
| `/regression-sentinel:setup` | One-time project setup |
| `/regression-sentinel:configure` | Set test command, auto-revert, max failures, debounce |
| `/regression-sentinel:status` | View test history and current streak |

## MCP Tools

| Tool | Description |
|------|-------------|
| `setup_project` | Create regression-sentinel directory and detect test runner |
| `configure` | Set test command, auto-revert, max failures, debounce interval |
| `run_tests` | Manually run the configured test command |
| `get_status` | View pass/fail history, streak, last output |
| `toggle_auto_revert` | Toggle auto-revert on/off |
| `clear_history` | Clear test run history |
| `revert_last` | Restore the most recently snapshotted file to its pre-edit state |

## How It Works

1. You edit a file with Write or Edit
2. **PreToolUse hook** fires first and saves the current file to `regression-sentinel/snapshots/{name}.bak`
3. The edit happens
4. **PostToolUse hook** fires and checks debounce timing
5. If within the debounce window, the test run is skipped (no slowdown)
6. If the file is a non-code file (.md, .json, etc.), the test run is skipped
7. Otherwise, tests are run:
   - If tests pass: consecutive failure count resets, status updated
   - If tests fail: Claude receives a regression warning with test output
   - With auto-revert ON: the file is **actually restored** from the snapshot
   - After N consecutive failures (default 3): Claude is told to **STOP** and reassess

## Configuration

Use `/regression-sentinel:configure` or the `configure` MCP tool:

| Setting | Default | Description |
|---------|---------|-------------|
| `test_command` | (auto-detected) | Shell command to run tests |
| `auto_revert` | `false` | Restore files from snapshot on test failure |
| `max_failures` | `3` | Consecutive failures before STOP enforcement |
| `debounce_seconds` | `5` | Minimum seconds between test runs |

## Files

```
regression-sentinel/
  config.json       # Test command and settings (used by hooks)
  state.json        # Full state with test history
  test-status.md    # One-liner status imported by CLAUDE.md
  snapshots/        # Pre-edit file snapshots for auto-revert
    *.bak           # Snapshot files (basename.bak)
```

## Requirements

- Python 3.10+
- `uv` installed
- A project with a test suite
