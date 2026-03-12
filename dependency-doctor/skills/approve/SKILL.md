---
name: approve
description: Approve a package for installation, bypassing the install hook.
disable-model-invocation: true
allowed-tools: mcp__dependency-doctor__approve_install
argument-hint: "package-name"
---

## Instructions

Parse `$ARGUMENTS` to extract the package name.

- If no arguments, ask the user for a package name.

Call `mcp__dependency-doctor__approve_install` with the package name and `cwd` = current working directory.

Display the result. Remind the user they can now install the package normally.
