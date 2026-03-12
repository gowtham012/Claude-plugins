---
name: setup
description: Set up rollback undo tracking for this project
---

Call `mcp__rollback__setup_project` with `cwd` = current working directory.

Report the result. Then tell the user:

> **rollback is set up.** Every Write/Edit action is now tracked with before/after snapshots.
>
> **Commands:**
> - `/rollback:rollback` — undo the last N actions
> - `/rollback:rollback-list` — show recent actions
