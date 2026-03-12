---
name: explain
description: Start or submit an explanation of your approach before writing code
argument-hint: "description of your approach"
---

If arguments were provided, call `mcp__rubber-duck__submit_explanation` with `cwd` = current working directory and `explanation` = the provided arguments.

If no arguments, call `mcp__rubber-duck__read_status` first to check current state, then prompt the user to describe their approach.

After submitting, tell the user their explanation is pending approval and they should approve, revise, or reject it.
