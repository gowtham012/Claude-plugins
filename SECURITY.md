# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| Latest  | Yes                |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please email **gowtham** with:

1. A description of the vulnerability
2. Steps to reproduce
3. The potential impact
4. Any suggested fixes (optional)

You can expect an initial response within 48 hours. We will work with you to understand and address the issue before any public disclosure.

## Scope

This policy applies to:

- The `carry-forward` plugin (MCP server, hooks, skills)
- The `video-insight` plugin (MCP server, video analyzer, skills)
- Any configuration files that could affect security (`.mcp.json`, `hooks.json`)

## Best Practices for Users

- Keep `uv` and Python updated to the latest stable versions
- Do not expose MCP servers to untrusted networks
- Review plugin permissions before installation
- Do not commit sensitive data (API keys, credentials) to `carry-forward/context.md`
