---
name: setup
description: One-time setup for dependency-doctor in the current project.
disable-model-invocation: true
allowed-tools: mcp__dependency-doctor__setup_project
argument-hint: (no arguments needed)
---

Call `mcp__dependency-doctor__setup_project` with `cwd` = current working directory.

Report the result. Then tell the user:

> **Setup complete.** Restart Claude Code for the install hook to take effect.
>
> **Commands:**
> - `/dependency-doctor:analyze <package> npm|pip` — analyze a package before installing
> - `/dependency-doctor:audit` — list all current project dependencies
> - `/dependency-doctor:approve <package>` — approve a package for installation
