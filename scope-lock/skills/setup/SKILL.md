---
name: setup
description: One-time setup for scope-lock in the current project. Creates the scope-lock/ directory and adds CLAUDE.md import.
disable-model-invocation: true
allowed-tools: mcp__scope-lock__setup_project
argument-hint: (no arguments needed)
---

## Current project state (auto-injected)

**Existing CLAUDE.md content (if any):**
```
!`cat CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md yet — will be created)"`
```

**Existing scope-lock directory (if any):**
```
!`ls scope-lock/ 2>/dev/null || echo "(not yet set up)"`
```

---

## Instructions

Call `mcp__scope-lock__setup_project` with `cwd` = current working directory.

Report the result verbatim.

Then tell the user:

> **Setup complete.** Restart Claude Code for the `@scope-lock/status.md` import to take effect — after that, the scope status loads automatically at the start of every session.
>
> **Commands:**
> - `/scope-lock:lock src/** tests/**` — lock scope to specific paths
> - `/scope-lock:unlock` — remove all restrictions
> - `/scope-lock:status` — check current scope
>
> **Requires:** Python 3.10+, `uv` installed
