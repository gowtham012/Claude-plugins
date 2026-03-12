---
name: unlock
description: Remove all scope restrictions, allowing access to all files.
disable-model-invocation: true
allowed-tools: mcp__scope-lock__unlock_scope
argument-hint: (no arguments needed)
---

## Current scope state (auto-injected)

**Config exists?**
```
!`cat scope-lock/config.json 2>/dev/null || echo "(no config — not locked)"`
```

---

## Instructions

Call `mcp__scope-lock__unlock_scope` with `cwd` = current working directory.

Report the result. Tell the user:

> **Scope unlocked.** All file access restrictions have been removed. Claude can now access any file.
