---
name: refresh
description: Refresh the onboarding guide by re-scanning the project. Use after significant codebase changes.
allowed-tools: mcp__codebase-onboard__refresh
argument-hint: (no arguments needed)
---

## Current onboard doc status (auto-injected)

```
!`ls -la codebase-onboard/onboard.md 2>/dev/null || echo "(no onboard doc found — run /codebase-onboard:onboard first)"`
```

---

## Instructions

Call `mcp__codebase-onboard__refresh` with `cwd` = current working directory.

Report the updated stats to the user: file count, line count, frameworks detected.

> **Onboarding guide refreshed.** The guide now reflects the current state of the codebase.
