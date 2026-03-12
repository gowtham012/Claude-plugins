# rubber-duck

Explain-before-code enforcement for Claude Code. Forces Claude to describe its approach in plain English and get user approval before writing any code.

## How it works

1. When a task starts, Claude must explain what it plans to do and which files it will touch
2. Write/Edit tools are **physically blocked** by a PreToolUse hook until the explanation is approved
3. Once approved, only the listed files can be modified
4. A Stop hook reminds Claude of the current phase after every response

## State machine

`idle` → `awaiting-explanation` → `awaiting-approval` → `approved` → `idle`

## Setup

```
/rubber-duck:setup
```

## Commands

| Command | Description |
|---------|-------------|
| `/rubber-duck:setup` | One-time project setup |
| `/rubber-duck:explain` | Start or submit an explanation |

## MCP Tools

- `setup_project` — Initialize rubber-duck in the project
- `start_explanation` — Begin a new explanation session
- `submit_explanation` — Submit the explanation text (must be 50+ chars, no code blocks)
- `record_approval` — Approve, revise, or reject the explanation
- `read_status` — Check current state
- `complete_task` — Mark task complete and reset to idle

## Hooks

- **PreToolUse** (Write/Edit): Blocks code changes unless status is "approved" and file is in the approved list
- **Stop**: Reminds Claude of the current rubber-duck phase

## Requirements

- Python 3.10+
- `uv` installed
