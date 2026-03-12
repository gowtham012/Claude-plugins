# diff-narrator

A Claude Code plugin that generates plain-English summaries of every edit, maintains a running changelog, and produces PR-ready descriptions.

## Problem

During a coding session, it is hard to remember exactly what changed and why. When it is time to write a PR description or review what was done, you have to manually dig through diffs.

## Solution

diff-narrator automatically narrates every Edit and Write operation:
- **Auto-narrates** every edit with a plain-English description
- **Maintains a changelog** that auto-loads via CLAUDE.md `@import`
- **Generates PR descriptions** with Summary, Changes, and Test Plan sections

---

## Prerequisites

- Claude Code **1.0.33 or later** (`claude --version`)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — used to run the MCP server with zero global installs

Install `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Install

### From GitHub (recommended)

Inside Claude Code:

```
/plugin marketplace add gowtham012/Claude-plugins
/plugin install diff-narrator@Claude-plugins
```

### Dev / local testing

```bash
claude --plugin-dir /path/to/diff-narrator
```

This loads the plugin for the current session only — use this while developing, not for day-to-day use.

---

## One-time project setup

After installing, open Claude Code in any project and run:

```
/diff-narrator:setup
```

Then **restart Claude Code**. From that point on, `changelog.md` loads automatically at every session start via the `@import` in `CLAUDE.md` — no command needed.

---

## Skills

| Skill | When to use |
|-------|-------------|
| `/diff-narrator:setup` | Once per project — creates diff-narrator/ dir, wires up CLAUDE.md |
| `/diff-narrator:summary` | Mid-session — review recent changes as plain-English narrations |
| `/diff-narrator:pr-description` | End of session — generate a PR-ready description from all changes |

---

## How it works

```
You make an edit              PostToolUse hook fires          changelog.md updated
─────────────────────         ─────────────────────           ─────────────────────
Edit or Write tool    →       posttool_hook.py detects        entries.jsonl grows
                              the change type and             changelog.md regenerated
                              generates a narration           (last 30 entries)

                              Output: "Logged: ..."          CLAUDE.md @import loads
                                                              changelog automatically
```

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `setup_project` | One-time setup: creates dir, initializes files, adds @import |
| `get_summary` | Returns recent narrations as markdown (default: last 20) |
| `get_pr_description` | Aggregates all changes into PR description |
| `add_narration` | Manually add a narration entry |
| `clear_session` | Clear narrations, archive old entries |
| `get_stats` | Show stats: files changed, total edits, most-edited files |

---

## Storage

Files are created inside your project:

```
your-project/
├── CLAUDE.md                              ← @diff-narrator/changelog.md added here
└── diff-narrator/
    ├── changelog.md                       ← auto-loaded every session start
    ├── entries.jsonl                       ← machine-readable narration entries
    └── entries.2026-03-11T10-30.jsonl.bak ← created by clear_session
```

Each entry in `entries.jsonl`:
```json
{"id": 1, "ts": "2026-03-11T10:30:00+00:00", "file_path": "src/app.py", "tool": "Edit", "change_type": "modify", "description": "Replaced `old code` with `new code`"}
```

---

## Update

```
/plugin marketplace update diff-narrator
```

---

## Uninstall

```
/plugin uninstall diff-narrator@Claude-plugins
```

---

## License

MIT
