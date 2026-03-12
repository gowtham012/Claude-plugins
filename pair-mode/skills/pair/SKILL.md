---
name: pair
description: Start a ping-pong pair programming session. Claude pauses after N edits for human review.
disable-model-invocation: true
allowed-tools: mcp__pair-mode__start_pair, mcp__pair-mode__end_pair, mcp__pair-mode__approve, mcp__pair-mode__reject, mcp__pair-mode__get_status
argument-hint: "max edits before pause (default 3)"
---

## Argument

$ARGUMENTS

---

## Instructions

If the argument is "end" or "stop", call `mcp__pair-mode__end_pair` with `cwd` = current working directory and report the result.

If the argument is "approve", call `mcp__pair-mode__approve` with `cwd` = current working directory and report the result.

If the argument starts with "reject", call `mcp__pair-mode__reject` with `cwd` = current working directory and `reason` = the rest of the argument. Report the result.

If the argument is "status", call `mcp__pair-mode__get_status` with `cwd` = current working directory and report the result.

Otherwise, parse the argument as a number for `max_edits_before_pause` (default 3 if empty or not a number).

Call `mcp__pair-mode__start_pair` with:
- `cwd` = current working directory
- `max_edits_before_pause` = the parsed number

Report the result. Then tell the user:

> **Pair session started.** Claude will pause after every N edits for your review.
>
> When paused, respond with:
> - "approve" — accept the edits and continue
> - "reject <reason>" — request revisions
