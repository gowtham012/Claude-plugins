---
name: status
description: Check regression-sentinel test history, pass/fail streak, and current configuration.
disable-model-invocation: true
allowed-tools: mcp__regression-sentinel__get_status
argument-hint: (no arguments needed)
---

## Current status (auto-injected)

**Config exists?**
```
!`test -f regression-sentinel/config.json && echo "YES — configured" || echo "NO — not configured (run /regression-sentinel:setup first)"`
```

**Recent status:**
```
!`cat regression-sentinel/test-status.md 2>/dev/null || echo "(no status yet)"`
```

---

## Instructions

Call `mcp__regression-sentinel__get_status` with `cwd` = current working directory.

If no configuration exists, tell the user:

> **Not set up.** Run `/regression-sentinel:setup` first.

Otherwise, format the response:

> **Regression Sentinel Status**
>
> **Test command:** `<command>`
> **Auto-revert:** ON/OFF
> **Max consecutive failures:** N
>
> **Results:** X passed, Y failed out of Z total runs
> **Current streak:** N consecutive failures
>
> **Recent runs:**
> | Time | Result |
> |------|--------|
> | ... | PASS/FAIL |
>
> **Last output:**
> ```
> <last test output snippet>
> ```
