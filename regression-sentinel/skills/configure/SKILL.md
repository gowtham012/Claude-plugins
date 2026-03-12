---
name: configure
description: Configure test command and auto-revert settings for regression-sentinel.
disable-model-invocation: true
allowed-tools: mcp__regression-sentinel__configure
argument-hint: "<test_command> [--auto-revert] [--max-failures N]"
---

## Current configuration (auto-injected)

**Config file:**
```
!`cat regression-sentinel/config.json 2>/dev/null || echo "(not configured yet — run /regression-sentinel:setup first)"`
```

---

## Instructions

Ask the user for the following (if not already provided as arguments):

1. **test_command** — the shell command to run tests (e.g., `pytest`, `npm test`, `cargo test`)
2. **auto_revert** — whether to suggest reverting files that break tests (default: false)
3. **max_failures** — max consecutive failures before warning to stop (default: 3)

Then call `mcp__regression-sentinel__configure` with:
- `cwd` = current working directory
- `test_command` = the test command
- `auto_revert` = true/false
- `max_failures` = number

Report the result. Confirm the settings are saved.

If the user only provides a test command, use defaults for the other options.
