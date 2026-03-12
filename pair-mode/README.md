# pair-mode

A Claude Code plugin that enforces ping-pong pair programming. Claude writes a block of edits, pauses for human review, then continues. Tracks approval rate across sessions.

## Installation

```
/plugin install pair-mode@pitlane-plugins
```

## Usage

### One-time setup
```
/pair-mode:setup
```

### Start a pair session
```
/pair-mode:pair
/pair-mode:pair 5
```

### During a session

Claude will pause after N edits (default 3) and ask for your review. Respond with:

- **approve** — accept the edits, reset counter, continue
- **reject <reason>** — log the rejection, reset counter, Claude revises

### View stats
```
/pair-mode:stats
```

### End a session
```
/pair-mode:pair end
```

## How It Works

- **PreToolUse hook** physically blocks Write/Edit calls when paused — Claude cannot bypass the pause
- **PostToolUse hook** fires after every Write/Edit, increments an edit counter, and injects a PAUSE message when the threshold is reached
- **Stop hook** reminds Claude of its pair-mode state after every response (paused or active with counter)
- State is stored in `pair-mode/state.json` with full edit history
- `pair-mode/status.md` is auto-imported into CLAUDE.md so Claude always sees the current state

## Skills

| Skill | Description |
|-------|-------------|
| `/pair-mode:setup` | One-time project setup |
| `/pair-mode:pair` | Start/stop pair session, approve/reject edits |
| `/pair-mode:stats` | View approval rate and session stats |

## Requirements

- Python 3.10+
- `uv` (for MCP server)

## License

MIT
