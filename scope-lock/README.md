# scope-lock

A Claude Code plugin that prevents scope creep by defining exact files and directories Claude can touch. PreToolUse hooks block Read, Write, Edit, Bash, Glob, and Grep operations outside the boundary.

## The Problem

Claude Code can access any file in your project. When working on a focused task, it sometimes:
- Reads unrelated files, losing context window to noise
- Edits files outside the intended scope of a change
- Accidentally modifies configuration or infrastructure files
- Drifts from the task at hand into unrelated refactors

## The Solution

`scope-lock` lets you define a set of allowed glob patterns. Once locked, Claude literally cannot read, write, or search outside those paths. PreToolUse hooks intercept every file operation and block anything outside the boundary.

## How It Works

| Mechanism | What it does |
|-----------|-------------|
| **PreToolUse hook** | Intercepts Read, Write, Edit, Bash, Glob, Grep. Blocks access to files outside allowed paths. |
| **Stop hook** | Reminds Claude of the active scope after every response. |
| **`lock_scope` tool** | Sets allowed paths with a reason. Saves to `scope-lock/config.json`. |
| **`unlock_scope` tool** | Clears all restrictions. |
| **fnmatch glob matching** | Paths are matched using standard glob patterns (`src/**`, `tests/**`, `*.py`). |
| **`scope-lock/` always allowed** | The plugin's own config files are never blocked. |

## Installation

```bash
claude plugin add gowtham012/Claude-plugins/scope-lock
```

## Usage

### One-time setup
```
/scope-lock:setup
```

### Lock scope to specific paths
```
/scope-lock:lock src/** tests/** docs/api.md
```

### Check current status
```
/scope-lock:status
```

### Unlock (remove all restrictions)
```
/scope-lock:unlock
```

## Skills

| Skill | Description |
|-------|-------------|
| `/scope-lock:setup` | One-time project setup |
| `/scope-lock:lock` | Lock scope to glob patterns |
| `/scope-lock:unlock` | Remove all restrictions |
| `/scope-lock:status` | Check current scope status |

## MCP Tools

| Tool | Description |
|------|-------------|
| `setup_project` | Creates `scope-lock/` dir, adds CLAUDE.md import |
| `lock_scope` | Set allowed paths with a reason |
| `unlock_scope` | Clear scope lock |
| `add_path` | Add a single path to allowed list |
| `remove_path` | Remove a path from allowed list |
| `get_status` | Show current lock status |

## Glob Pattern Examples

| Pattern | Matches |
|---------|---------|
| `src/**` | All files under `src/` |
| `tests/**` | All files under `tests/` |
| `*.py` | Python files in the root directory |
| `src/**/*.ts` | TypeScript files anywhere under `src/` |
| `docs/api.md` | A single specific file |
| `config/*` | All files directly in `config/` |

## Requirements

- Python 3.10+
- `uv` (for MCP server)

## License

MIT
