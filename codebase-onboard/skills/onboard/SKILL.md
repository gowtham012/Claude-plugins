---
name: onboard
description: Generate or refresh the codebase onboarding guide. Scans the project for structure, frameworks, key files, and produces a comprehensive markdown guide.
allowed-tools: mcp__codebase-onboard__setup_project, mcp__codebase-onboard__generate_onboard
argument-hint: (no arguments needed)
---

## Current project state (auto-injected)

**Existing CLAUDE.md content (if any):**
```
!`cat CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md yet — will be created)"`
```

**Existing onboard doc (if any):**
```
!`ls -la codebase-onboard/onboard.md 2>/dev/null || echo "(not yet generated)"`
```

---

## Instructions

1. First, call `mcp__codebase-onboard__setup_project` with `cwd` = current working directory to ensure the directory and CLAUDE.md import are set up.

2. Then call `mcp__codebase-onboard__generate_onboard` with `cwd` = current working directory to scan the project and generate the onboarding guide.

3. Report the results to the user. Include:
   - Number of files scanned
   - Frameworks detected
   - Where to find the generated guide

Then tell the user:

> **Onboarding guide generated.** Restart Claude Code for the `@codebase-onboard/onboard.md` import to auto-load the guide every session.
>
> **Commands:**
> - `/codebase-onboard:find <query>` — search the guide for a specific topic
> - `/codebase-onboard:refresh` — regenerate after codebase changes
