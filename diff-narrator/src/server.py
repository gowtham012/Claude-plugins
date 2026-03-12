#!/usr/bin/env python3
"""
diff-narrator MCP server (FastMCP).
6 tools: setup_project, get_summary, get_pr_description, add_narration,
         clear_session, get_stats.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("diff-narrator")

CLAUDE_MD_IMPORT = "@diff-narrator/changelog.md"


def _dir(cwd: str) -> Path:
    return Path(cwd) / "diff-narrator"


def _entries_file(cwd: str) -> Path:
    return _dir(cwd) / "entries.jsonl"


def _changelog_file(cwd: str) -> Path:
    return _dir(cwd) / "changelog.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_entries(cwd: str) -> list[dict]:
    """Read all entries from entries.jsonl."""
    ef = _entries_file(cwd)
    if not ef.exists():
        return []
    entries = []
    for line in ef.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries


def _regenerate_changelog(cwd: str, limit: int = 30) -> None:
    """Regenerate changelog.md from the last `limit` entries."""
    entries = _read_entries(cwd)
    recent = entries[-limit:]

    lines = [
        "# Diff Narrator — Changelog",
        "",
        f"_Last updated: {_now_iso()}_",
        "",
    ]

    if not recent:
        lines.append("_No changes recorded yet._")
    else:
        for e in reversed(recent):
            ts = e.get("ts", "")
            # Show just time portion if available
            short_ts = ts[11:19] if len(ts) >= 19 else ts
            fp = e.get("file_path", "unknown")
            ct = e.get("change_type", "modify")
            desc = e.get("description", "")
            lines.append(f"- **[{short_ts}]** `{fp}` ({ct}) — {desc}")

    lines.append("")
    _changelog_file(cwd).write_text("\n".join(lines), encoding="utf-8")


@mcp.tool()
def setup_project(cwd: str) -> str:
    """
    One-time setup for diff-narrator in the current project.
    Creates diff-narrator/ directory, initializes config files,
    and adds @import to CLAUDE.md for diff-narrator/changelog.md.
    """
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)

    # Initialize entries.jsonl
    ef = _entries_file(cwd)
    if not ef.exists():
        ef.touch()

    # Initialize changelog.md
    _regenerate_changelog(cwd)

    # Append @import to CLAUDE.md if not already present
    claude_md = Path(cwd) / "CLAUDE.md"
    already_imported = False
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")
        already_imported = CLAUDE_MD_IMPORT in content

    if not already_imported:
        with claude_md.open("a", encoding="utf-8") as f:
            f.write(f"\n{CLAUDE_MD_IMPORT}\n")
        claude_md_status = "Added @import to CLAUDE.md."
    else:
        claude_md_status = "CLAUDE.md already has the @import line."

    return (
        f"diff-narrator set up in {d}.\n"
        f"{claude_md_status}\n"
        "Restart Claude Code for auto-loading to take effect."
    )


@mcp.tool()
def get_summary(cwd: str, limit: int = 20) -> str:
    """
    Returns recent change narrations as markdown.
    Shows the last `limit` entries (default 20).
    """
    entries = _read_entries(cwd)
    if not entries:
        return "No changes recorded yet. Run setup_project first or make some edits."

    recent = entries[-limit:]
    lines = [f"## Recent Changes (last {len(recent)})", ""]
    for e in reversed(recent):
        ts = e.get("ts", "")
        short_ts = ts[11:19] if len(ts) >= 19 else ts
        fp = e.get("file_path", "unknown")
        ct = e.get("change_type", "modify")
        desc = e.get("description", "")
        lines.append(f"- **[{short_ts}]** `{fp}` ({ct}) — {desc}")

    return "\n".join(lines)


@mcp.tool()
def get_pr_description(cwd: str) -> str:
    """
    Aggregates all changes in the current session into a PR-ready description
    with Summary, Changes, and Test Plan sections.
    """
    entries = _read_entries(cwd)
    if not entries:
        return "No changes recorded. Nothing to generate a PR description from."

    # Collect unique files and their changes
    files_changed: dict[str, list[str]] = {}
    for e in entries:
        fp = e.get("file_path", "unknown")
        desc = e.get("description", "")
        ct = e.get("change_type", "modify")
        if fp not in files_changed:
            files_changed[fp] = []
        files_changed[fp].append(f"{ct}: {desc}")

    # Build summary
    total_edits = len(entries)
    file_count = len(files_changed)

    # Determine change types
    change_types = Counter(e.get("change_type", "modify") for e in entries)
    type_summary = ", ".join(f"{count} {ct}" for ct, count in change_types.most_common())

    lines = [
        "## Summary",
        "",
        f"This PR includes {total_edits} edit(s) across {file_count} file(s) ({type_summary}).",
        "",
        "## Changes",
        "",
    ]

    for fp, changes in files_changed.items():
        lines.append(f"### `{fp}`")
        for change in changes:
            lines.append(f"- {change}")
        lines.append("")

    lines.extend([
        "## Test Plan",
        "",
        "- [ ] Verify all modified files compile/lint without errors",
        "- [ ] Run existing test suite",
        "- [ ] Manual review of changed files:",
    ])
    for fp in files_changed:
        lines.append(f"  - [ ] `{fp}`")

    return "\n".join(lines)


@mcp.tool()
def add_narration(cwd: str, file_path: str, change_type: str, description: str) -> str:
    """
    Manually add a narration entry.
    change_type should be one of: create, modify, append, delete, refactor.
    """
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)

    entry_id = len(_read_entries(cwd)) + 1
    record = {
        "id": entry_id,
        "ts": _now_iso(),
        "file_path": file_path,
        "tool": "manual",
        "change_type": change_type,
        "description": description.strip()[:200],
    }

    with _entries_file(cwd).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    _regenerate_changelog(cwd)
    return f"Narration added: {file_path} ({change_type}) — {description}"


@mcp.tool()
def clear_session(cwd: str) -> str:
    """
    Clear current session narrations.
    Archives entries.jsonl before clearing.
    """
    ef = _entries_file(cwd)
    archive_msg = ""
    if ef.exists() and ef.stat().st_size > 0:
        ts_safe = _now_iso().replace(":", "-").replace(".", "-")
        archive = ef.parent / f"entries.{ts_safe}.jsonl.bak"
        ef.rename(archive)
        ef.touch()
        archive_msg = f" Archived to {archive.name}."

    _regenerate_changelog(cwd)
    return f"Session cleared.{archive_msg}"


@mcp.tool()
def get_stats(cwd: str) -> str:
    """
    Show stats: files changed, total edits, most-edited files.
    """
    entries = _read_entries(cwd)
    if not entries:
        return "No changes recorded yet."

    total = len(entries)
    file_counts = Counter(e.get("file_path", "unknown") for e in entries)
    type_counts = Counter(e.get("change_type", "modify") for e in entries)
    unique_files = len(file_counts)

    lines = [
        "## Diff Narrator Stats",
        "",
        f"- **Total edits:** {total}",
        f"- **Files changed:** {unique_files}",
        "",
        "### By change type",
    ]
    for ct, count in type_counts.most_common():
        lines.append(f"- {ct}: {count}")

    lines.extend(["", "### Most-edited files"])
    for fp, count in file_counts.most_common(10):
        lines.append(f"- `{fp}` — {count} edit(s)")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
