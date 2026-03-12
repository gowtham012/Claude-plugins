---
name: setup
description: Set up rubber-duck explain-before-code enforcement for this project
---

Call `mcp__rubber-duck__setup_project` with `cwd` = current working directory.

Report the result. Then tell the user:

> **rubber-duck is set up.** Restart Claude Code for the state import to take effect.
>
> From now on, Claude must explain its approach in plain English before writing any code. Write/Edit tools are blocked until the explanation is approved.
>
> **Commands:**
> - `/rubber-duck:explain` — start explaining your approach
