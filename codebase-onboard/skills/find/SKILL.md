---
name: find
description: Search the onboarding guide for a specific pattern, topic, or keyword. Returns the relevant section(s).
allowed-tools: mcp__codebase-onboard__find_pattern
argument-hint: <search query>
---

## Search query

$ARGUMENTS

---

## Instructions

Call `mcp__codebase-onboard__find_pattern` with:
- `cwd` = current working directory
- `query` = "$ARGUMENTS"

Present the matching section(s) to the user. If no matches are found, suggest related terms or offer to search the codebase directly.
