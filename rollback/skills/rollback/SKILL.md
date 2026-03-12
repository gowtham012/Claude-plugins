---
name: rollback
description: Undo the last N Claude actions
argument-hint: "number of actions to undo (default 1)"
---

Parse the argument as a number (default to 1 if not provided).

Call `mcp__rollback__rollback_undo` with `cwd` = current working directory and `count` = the parsed number.

Report the result showing which files were restored.
