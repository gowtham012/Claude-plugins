---
name: checkpoint
description: Create a named checkpoint.
disable-model-invocation: true
allowed-tools: mcp__time-capsule__create_checkpoint
argument-hint: label for checkpoint
---

Call `mcp__time-capsule__create_checkpoint` with `cwd` = current working directory and `label` = the user's argument (or a descriptive default like "manual checkpoint").

Report the result verbatim.
