# time-capsule

A Claude Code plugin that auto-creates lightweight git snapshots before risky edits and on demand. Browse and restore any checkpoint.

## Problem

Destructive edits happen. A bad refactor, an overwritten file, a wrong `Write` — and the previous state is gone. Git commits are too heavy for mid-session safety nets.

## Solution

time-capsule uses git stash under the hood to create instant, lightweight checkpoints:

- **Auto-checkpoints** before every Write/Edit (PreToolUse hook), throttled by a configurable interval
- **Manual checkpoints** via `/time-capsule:checkpoint "label"`
- **Browse, diff, restore, delete** any checkpoint

---

## Prerequisites

- Claude Code **1.0.33 or later** (`claude --version`)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — used to run the MCP server with zero global installs
- Git initialized in your project

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
/plugin install time-capsule@Claude-plugins
```

### Dev / local testing

```bash
claude --plugin-dir /path/to/time-capsule
```

---

## One-time project setup

After installing, open Claude Code in any project and run:

```
/time-capsule:setup
```

Then **restart Claude Code**. From that point on, `status.md` loads automatically at every session start via the `@import` in `CLAUDE.md`.

---

## Skills

| Skill | When to use |
|-------|-------------|
| `/time-capsule:setup` | Once per project — creates config and wires up CLAUDE.md |
| `/time-capsule:checkpoint "label"` | Any time — create a named snapshot |

## MCP Tools

| Tool | Description |
|------|-------------|
| `create_checkpoint` | Create a named git checkpoint |
| `list_checkpoints` | Show recent checkpoints as a table |
| `restore_checkpoint` | Restore a checkpoint by ID |
| `diff_checkpoint` | Show diff between checkpoint and current state |
| `delete_checkpoint` | Drop a specific checkpoint |

---

## How it works

```
Before Write/Edit          time-capsule/              On demand
──────────────────         ──────────────────         ──────────────────
PreToolUse hook fires  →   git stash push             /time-capsule:checkpoint
(auto, if interval         (lightweight, instant)     (manual, labeled)
 has elapsed)
                           index.jsonl tracks          list / restore / diff
                           all checkpoints             any checkpoint by ID

Stop hook fires        →   Reminds you if there
                           are unsaved changes
```

---

## Storage

Files are created inside your project:

```
your-project/
├── CLAUDE.md                    ← @time-capsule/status.md added here
└── time-capsule/
    ├── config.json              ← {auto_checkpoint, min_interval_seconds}
    ├── index.jsonl              ← checkpoint entries
    └── status.md                ← auto-loaded every session start
```

Checkpoints themselves live in git's stash — no extra disk space.

---

## Configuration

Edit `time-capsule/config.json`:

```json
{
  "auto_checkpoint": true,
  "min_interval_seconds": 60
}
```

- `auto_checkpoint` — enable/disable automatic checkpoints before edits
- `min_interval_seconds` — minimum seconds between auto-checkpoints (default: 60)

---

## Update

```
/plugin marketplace update time-capsule
```

---

## Uninstall

```
/plugin uninstall time-capsule@Claude-plugins
```

---

## License

MIT
