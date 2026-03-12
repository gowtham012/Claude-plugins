---
name: pr-description
description: Generate a PR-ready description from all narrated changes in the current session. Includes Summary, Changes, and Test Plan sections.
disable-model-invocation: true
allowed-tools: mcp__diff-narrator__get_pr_description, mcp__diff-narrator__get_stats
argument-hint: (no arguments needed)
---

## Instructions

1. Call `mcp__diff-narrator__get_pr_description` with `cwd` = current working directory.

2. Present the generated PR description to the user.

3. Tell the user:

> **PR description generated.** You can copy this directly into your pull request. Edit as needed — the auto-generated description captures what changed, but you may want to refine the summary and test plan.
>
> To clear the session and start fresh, use `/diff-narrator:setup` or call `clear_session`.
