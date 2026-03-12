# codebase-onboard

A Claude Code plugin that analyzes your codebase and generates an onboarding guide: architecture overview, key patterns, directory structure, and getting-started steps.

## Problem

Joining a new project or returning to one after a break means hunting through folders, reading configs, and piecing together how things fit. Claude has no project context until you explain it.

## Solution

codebase-onboard scans your project automatically and produces a structured onboarding guide:
- **Project overview** — name, description, version, total files and lines
- **Tech stack** — auto-detected frameworks (React, Next.js, FastAPI, Django, Express, etc.)
- **Directory structure** — visual tree of the project layout
- **Key files** — contents of src/, lib/, app/, tests/, and other important directories
- **Architecture notes** — inferred patterns (API layer, models, middleware, components, etc.)
- **Getting started** — install, dev, test, and build commands

The guide loads automatically every session via CLAUDE.md `@import`.

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
/plugin install codebase-onboard@Claude-plugins
```

### Dev / local testing

```bash
claude --plugin-dir /path/to/codebase-onboard
```

---

## One-time project setup

After installing, open Claude Code in any project and run:

```
/codebase-onboard:onboard
```

Then **restart Claude Code**. From that point on, `onboard.md` loads automatically at every session start via the `@import` in `CLAUDE.md`.

---

## Skills

| Skill | When to use |
|-------|-------------|
| `/codebase-onboard:onboard` | First time — generate the onboarding guide |
| `/codebase-onboard:find <query>` | Search the guide for a topic (e.g., "auth", "database", "tests") |
| `/codebase-onboard:refresh` | Regenerate the guide after significant codebase changes |

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `setup_project` | Creates codebase-onboard/ dir and adds @import to CLAUDE.md |
| `generate_onboard` | Scans the project and generates onboard.md + stats.json |
| `refresh` | Re-scans and regenerates the onboarding doc |
| `find_pattern` | Searches the onboard doc for a query, returns matching sections |
| `add_note` | Adds a custom note to a section of the onboard doc |
| `get_stats` | Returns codebase stats: file counts, line counts, frameworks |

---

## How it works

```
First run                        Disk                         Every session
─────────────────────            ─────────────────────        ─────────────────────
/codebase-onboard:onboard   →    CLAUDE.md gets               Open Claude Code
                                  @codebase-onboard/           Claude reads onboard.md
Scans project:                    onboard.md                   automatically at startup
  - package.json / pyproject
  - directory structure           codebase-onboard/            Claude already knows:
  - file types                      onboard.md (guide)         - Project structure
  - frameworks                      stats.json (stats)         - Tech stack
                                                               - Key files
Stop hook fires              →   Reminds if doc missing        - How to get started
after every response              or stale (>24h)
```

---

## Storage

Files are created inside your project:

```
your-project/
├── CLAUDE.md                              ← @codebase-onboard/onboard.md added here
└── codebase-onboard/
    ├── onboard.md                         ← auto-loaded every session start
    └── stats.json                         ← file counts, frameworks, line totals
```

---

## Update

```
/plugin marketplace update codebase-onboard
```

---

## Uninstall

```
/plugin uninstall codebase-onboard@Claude-plugins
```

---

## License

MIT
