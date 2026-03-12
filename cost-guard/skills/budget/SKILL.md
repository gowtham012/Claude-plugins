---
name: budget
description: Set or view the token spending budget.
disable-model-invocation: true
allowed-tools: mcp__cost-guard__set_budget, mcp__cost-guard__get_report
argument-hint: "[amount in USD, e.g. 5.00] or 'status'"
---

## Instructions

If `$ARGUMENTS` is a number, call `mcp__cost-guard__set_budget` with that amount.
If `$ARGUMENTS` is empty or "status", call `mcp__cost-guard__get_report` with scope "session".

Display the result clearly.
