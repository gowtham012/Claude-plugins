---
name: report
description: Show detailed cost breakdown — per session or all-time.
disable-model-invocation: true
allowed-tools: mcp__cost-guard__get_report
argument-hint: "[session|all] — defaults to 'session'"
---

Call `mcp__cost-guard__get_report` with the specified scope (default "session").
Format and display the result.
