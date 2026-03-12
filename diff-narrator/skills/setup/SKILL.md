---
name: setup
description: One-time setup for diff-narrator in the current project. Creates the diff-narrator/ directory, initializes changelog, and wires up CLAUDE.md auto-import.
disable-model-invocation: true
allowed-tools: mcp__diff-narrator__setup_project
argument-hint: (no arguments needed)
---

## Current project state (auto-injected)

**Existing CLAUDE.md content (if any):**
```
!`cat CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md yet — will be created)"`
```

**Existing diff-narrator directory (if any):**
```
!`ls diff-narrator/ 2>/dev/null || echo "(not yet set up)"`
```

---

## Instructions

Call `mcp__diff-narrator__setup_project` with `cwd` = current working directory.

Report the result verbatim.

If CLAUDE.md already existed (shown above), confirm that the `@diff-narrator/changelog.md` line was added without disturbing existing content.

Then tell the user:

> **Setup complete.** Restart Claude Code for the `@diff-narrator/changelog.md` import to take effect — after that, your changelog loads automatically at the start of every session.
>
> Every Edit and Write will now be narrated automatically. Use `/diff-narrator:summary` to review changes or `/diff-narrator:pr-description` to generate a PR description.
