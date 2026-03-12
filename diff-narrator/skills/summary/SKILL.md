---
name: summary
description: Show a plain-English summary of recent changes narrated by diff-narrator. Useful for reviewing what was done during a session.
disable-model-invocation: true
allowed-tools: mcp__diff-narrator__get_summary, mcp__diff-narrator__get_stats
argument-hint: "[optional limit, e.g. 10]"
---

## Instructions

1. Call `mcp__diff-narrator__get_summary` with `cwd` = current working directory. If `$ARGUMENTS` is a number, pass it as `limit`.

2. Call `mcp__diff-narrator__get_stats` with `cwd` = current working directory.

3. Present both results to the user in a clear format:
   - First show the summary of recent changes
   - Then show the stats overview

If no changes are recorded, tell the user:

> **No changes recorded yet.** Make some edits and they will be narrated automatically, or run `/diff-narrator:setup` if you haven't set up the project yet.
