---
name: analyze
description: Analyze a package for safety, license, bundle size, and vulnerabilities before installing.
disable-model-invocation: true
allowed-tools: mcp__dependency-doctor__analyze_package
argument-hint: "package-name npm|pip"
---

## Instructions

Parse `$ARGUMENTS` to extract the package name and ecosystem.

- If two words are provided, the first is the package name and the second is the ecosystem (`npm` or `pip`).
- If only one word is provided, assume `npm` as the ecosystem.
- If no arguments, ask the user for a package name.

Call `mcp__dependency-doctor__analyze_package` with the package name, ecosystem, and `cwd` = current working directory.

This single call returns registry info, bundle size (npm), vulnerabilities, and license compatibility — all in one report.

Display the result clearly. If the package looks safe, suggest running `/dependency-doctor:approve <package>` to allow installation. If there are license or vulnerability warnings, suggest `/dependency-doctor:reject <package>` with a reason.
