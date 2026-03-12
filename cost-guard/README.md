# cost-guard

A Claude Code plugin that tracks token usage and API costs in real-time. Set spending limits, get warnings when approaching budget, and see cost breakdowns per session and task.

## Installation

```
/plugin install cost-guard@pitlane-plugins
```

## Usage

### One-time setup
```
/cost-guard:setup
```

### Set a budget
```
/cost-guard:budget 10.00
```

### View costs
```
/cost-guard:report
/cost-guard:report all
```

## How It Works

- **Stop hook** estimates token usage after every Claude response
- **PreToolUse hook** enforces hard budget limits (blocks all tool calls when exceeded)
- Costs are estimates based on text length heuristics (~len/4 tokens)
- Supports per-session and all-time tracking with optional task labels

## Skills

| Skill | Description |
|-------|-------------|
| `/cost-guard:setup` | One-time project setup |
| `/cost-guard:budget` | Set or view spending budget |
| `/cost-guard:report` | Detailed cost breakdown |

## Requirements

- Python 3.10+
- `uv` (for MCP server)

## License

MIT
