---
name: setup
description: One-time setup for time-capsule in the current project.
disable-model-invocation: true
allowed-tools: mcp__time-capsule__setup_project
argument-hint: (no arguments needed)
---

Call `mcp__time-capsule__setup_project` with `cwd` = current working directory.

Report the result. Then tell the user:

> **Setup complete.** Restart Claude Code for the `@time-capsule/status.md` import to take effect.
>
> **Commands:**
> - `/time-capsule:checkpoint "label"` — create a named checkpoint
> - Call `list_checkpoints` — browse recent checkpoints
> - Call `restore_checkpoint` — restore any checkpoint
> - Call `diff_checkpoint` — view changes since a checkpoint
