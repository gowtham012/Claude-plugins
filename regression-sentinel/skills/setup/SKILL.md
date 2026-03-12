---
name: setup
description: Set up regression-sentinel for this project. Creates the regression-sentinel/ directory, detects test runner, and adds CLAUDE.md import.
disable-model-invocation: true
allowed-tools: mcp__regression-sentinel__setup_project
argument-hint: (no arguments needed)
---

## Current project state (auto-injected)

**Existing CLAUDE.md content (if any):**
```
!`cat CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md yet — will be created)"`
```

**Existing regression-sentinel directory (if any):**
```
!`ls regression-sentinel/ 2>/dev/null || echo "(not yet set up)"`
```

---

## Instructions

Call `mcp__regression-sentinel__setup_project` with `cwd` = current working directory.

Report the result verbatim.

If CLAUDE.md already existed (shown above), confirm that the `@regression-sentinel/test-status.md` line was added without disturbing existing content.

Then tell the user:

> **Setup complete.** Restart Claude Code for the `@regression-sentinel/test-status.md` import to take effect — after that, your test status loads automatically at the start of every session.
>
> **How it works:**
>
> - After every Write/Edit, the PostToolUse hook automatically runs your test suite
> - If tests fail, Claude is immediately notified of the regression
> - With auto-revert enabled, Claude is told to revert breaking changes
> - Test status is visible in CLAUDE.md via the @import
>
> **Commands:**
> - `/regression-sentinel:configure` — set test command, enable auto-revert
> - `/regression-sentinel:status` — check test history and current streak
>
> **Requires:** Python 3.10+, `uv` installed
