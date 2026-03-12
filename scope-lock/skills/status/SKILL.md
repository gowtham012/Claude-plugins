---
name: status
description: Check the current scope lock status — locked/unlocked, allowed paths, and reason.
disable-model-invocation: true
allowed-tools: mcp__scope-lock__get_status
argument-hint: (no arguments needed)
---

## Current scope state (auto-injected)

**Config exists?**
```
!`cat scope-lock/config.json 2>/dev/null || echo "(no config — run /scope-lock:setup first)"`
```

---

## Instructions

Call `mcp__scope-lock__get_status` with `cwd` = current working directory.

Format the response:

> **Scope Lock Status**
>
> **State:** LOCKED / UNLOCKED
> **Allowed paths:** (list or "no restrictions")
> **Reason:** (reason or "n/a")
>
> **Commands:**
> - `/scope-lock:lock <patterns>` — lock to specific paths
> - `/scope-lock:unlock` — remove restrictions
