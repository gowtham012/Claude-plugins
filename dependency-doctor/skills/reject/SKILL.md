---
name: reject
description: Reject a package — permanently block it from installation with a reason.
disable-model-invocation: true
allowed-tools: mcp__dependency-doctor__reject_install
argument-hint: "package-name reason"
---

## Instructions

Parse `$ARGUMENTS` to extract the package name and reason.

- The first word is the package name. Everything after it is the reason.
- If only a package name is given, use "Rejected by developer" as the default reason.
- If no arguments, ask the user for a package name.

Call `mcp__dependency-doctor__reject_install` with the package name, reason, and `cwd` = current working directory.

Display the result. Note that the install hook will now permanently block this package.
