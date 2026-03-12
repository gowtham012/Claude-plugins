# rollback

One-command undo for any Claude Code action. Automatically snapshots files before and after every Write/Edit, with instant rollback to any point.

## How it works

1. **PreToolUse hook** captures file content BEFORE every Write/Edit
2. **PostToolUse hook** captures file content AFTER every Write/Edit
3. Both snapshots are stored with an action ID in `rollback/snapshots/`
4. An index (`rollback/index.jsonl`) tracks all actions
5. Roll back any number of actions instantly

## Setup

```
/rollback:setup
```

## Commands

| Command | Description |
|---------|-------------|
| `/rollback:setup` | One-time project setup |
| `/rollback:rollback` | Undo last N actions |
| `/rollback:rollback-list` | Show recent actions |

## MCP Tools

- `setup_project` — Initialize rollback tracking
- `rollback_undo` — Undo the last N actions
- `rollback_list` — Show recent actions with IDs
- `rollback_show` — Show unified diff for a specific action
- `rollback_to` — Roll back everything down to a specific action ID
- `rollback_cleanup` — Remove old snapshots, keeping the most recent N

## Hooks

- **PreToolUse** (Write/Edit): Captures before-snapshot
- **PostToolUse** (Write/Edit): Captures after-snapshot, updates index

## Auto-cleanup

Snapshots directory is capped at 50MB. When exceeded, the oldest half of snapshots is automatically removed.

## Requirements

- Python 3.10+
- `uv` installed
