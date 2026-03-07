# carry-forward

> Never lose context between Claude Code sessions again.

Every new Claude Code session starts blank — no memory of what you were building, what decisions you made, or what's next. carry-forward bridges that gap automatically.

## How it works

```
Session 1                          Session 2
─────────────────────────          ──────────────────────────────
You work with Claude          →    Claude opens context.md
Stop hook fires on exit       →    Sees: "Working on JWT refresh"
Appends summary to log.jsonl  →    Sees last 10 log entries
/carry-forward:save writes    →    Ready to continue immediately
  structured context.md
```

1. **One-time setup** — run `/carry-forward:setup` in your project
2. **Auto-save** — Stop hook appends a summary after every Claude response
3. **Auto-load** — `CLAUDE.md` imports `@carry-forward/context.md` at every session start
4. **Manual save** — run `/carry-forward:save` for a rich structured snapshot

## Installation

```
/plugin marketplace add gowtham012/Claude-plugins
/plugin install carry-forward@Claude-plugins
```

Then in your project:

```
/carry-forward:setup
```

Restart Claude Code. Done — context now persists automatically.

## Skills

### `/carry-forward:setup`
One-time setup per project. Creates `carry-forward/` directory, writes initial `context.md`, and adds the `@carry-forward/context.md` import to `CLAUDE.md`.

### `/carry-forward:save`
Writes a structured context snapshot at the end of a session. Uses git history as ground truth for which files were touched. Optionally accepts a focus area:
```
/carry-forward:save auth refactor
```

### `/carry-forward:load`
Presents saved context conversationally — current task, files in play, key decisions, next steps, recent activity log. Accepts an optional section filter:
```
/carry-forward:load next steps
```

### `/carry-forward:clear`
Confirms with you, then resets `context.md` to a blank template and archives `log.jsonl` as a timestamped `.bak` file.

## Storage

Three files created inside your project:

```
your-project/
└── carry-forward/
    ├── context.md          ← auto-loaded every session via CLAUDE.md
    ├── log.jsonl           ← auto-appended after every response
    └── log.*.jsonl.bak     ← archived logs after /clear
```

## Requirements

- Python 3.10+
- `uvx` — install via `curl -LsSf https://astral.sh/uv/install.sh | sh`

## License

MIT
