---
name: lock
description: Lock the scope to specific file paths. Only files matching the given glob patterns will be accessible.
disable-model-invocation: true
allowed-tools: mcp__scope-lock__lock_scope
argument-hint: glob patterns to allow
---

## Current scope state (auto-injected)

**Config exists?**
```
!`cat scope-lock/config.json 2>/dev/null || echo "(no config — run /scope-lock:setup first)"`
```

---

## Instructions

The user wants to lock the scope to specific paths.

**Arguments from user:** $ARGUMENTS

Parse the arguments as a list of glob patterns. Common examples:
- `src/**` — all files under src/
- `tests/**` — all files under tests/
- `*.py` — all Python files in the root
- `src/**/*.ts` — all TypeScript files under src/

Ask the user for a reason if not provided. A short phrase is fine (e.g. "focusing on auth module refactor").

Call `mcp__scope-lock__lock_scope` with:
- `cwd` = current working directory
- `paths` = list of glob patterns parsed from arguments
- `reason` = the reason for locking

Report the result. Remind the user:

> **Scope locked.** All Read, Write, Edit, Bash, Glob, and Grep operations outside these paths will be blocked.
>
> - `/scope-lock:status` — check current scope
> - `/scope-lock:unlock` — remove restrictions
