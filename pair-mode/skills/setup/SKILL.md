---
name: setup
description: One-time setup for pair-mode in the current project.
disable-model-invocation: true
allowed-tools: mcp__pair-mode__setup_project
argument-hint: (no arguments needed)
---

Call `mcp__pair-mode__setup_project` with `cwd` = current working directory.

Report the result. Then tell the user:

> **Setup complete.** Restart Claude Code for pair-mode to take effect.
>
> **Commands:**
> - `/pair-mode:pair` — start a pair programming session (default: pause every 3 edits)
> - `/pair-mode:pair 5` — start with custom edit threshold
> - `/pair-mode:stats` — view approval rate and session stats
>
> **During a session:**
> - Claude will pause after N edits and ask for your review
> - Type "approve" or use `/pair-mode:approve` to continue
> - Type "reject" with a reason or use `/pair-mode:reject` to request revisions
