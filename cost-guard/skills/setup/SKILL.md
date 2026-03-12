---
name: setup
description: One-time setup for cost-guard in the current project.
disable-model-invocation: true
allowed-tools: mcp__cost-guard__setup_project
argument-hint: (no arguments needed)
---

Call `mcp__cost-guard__setup_project` with `cwd` = current working directory.

Report the result. Then tell the user:

> **Setup complete.** Restart Claude Code for budget tracking to take effect.
>
> **Commands:**
> - `/cost-guard:budget <amount>` — set a spending budget in USD
> - `/cost-guard:report` — view cost breakdown
