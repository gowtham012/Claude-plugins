#!/usr/bin/env python3
"""PreToolUse hook — blocks unapproved package installs."""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path


# Install command patterns: (regex, ecosystem)
INSTALL_PATTERNS = [
    (r"\bnpm\s+install\b", "npm"),
    (r"\bnpm\s+add\b", "npm"),
    (r"\bnpm\s+i\b", "npm"),  # npm i shorthand
    (r"\byarn\s+add\b", "npm"),
    (r"\bpnpm\s+(add|install)\b", "npm"),
    (r"\bbun\s+(add|install)\b", "npm"),
    (r"\bnpx\s+", "npm"),  # npx can install packages implicitly
    (r"\bbunx\s+", "npm"),  # bunx can install packages implicitly
    (r"\bpip3?\s+install\b", "pip"),
    (r"\bpython3?\s+-m\s+pip\s+install\b", "pip"),
    (r"\buv\s+(add|pip\s+install)\b", "pip"),
    (r"\bpoetry\s+add\b", "pip"),
    (r"\bpdm\s+add\b", "pip"),
]

# Flags/commands that indicate lockfile-only or reproducible installs — skip blocking
LOCKFILE_INDICATORS = [
    "--frozen-lockfile",
    "--ci",
    "npm ci",
    "bun install",  # bare bun install (no packages) restores from lockfile
    "pip install -r",
    "pip install -e .",
    "pip3 install -r",
    "pip3 install -e .",
]


def _extract_packages(command: str) -> list[str]:
    """Extract package names from an install command."""
    # Remove the install command prefix
    cleaned = command
    for pattern, _ in INSTALL_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, count=1)

    # Split remaining args
    parts = cleaned.strip().split()
    packages = []
    skip_next = False
    for part in parts:
        if skip_next:
            skip_next = False
            continue
        # Skip flags
        if part.startswith("-"):
            # Flags that take a value
            if part in ("--registry", "--save-prefix", "--tag", "-w", "--workspace"):
                skip_next = True
            continue
        # Skip if it looks like a path or URL
        if part.startswith(".") or part.startswith("/") or "://" in part:
            continue
        # Strip version specifiers for npm (e.g., express@4.18.0)
        pkg = part.split("@")[0] if "@" in part and not part.startswith("@") else part
        # Handle scoped packages (@scope/name@version)
        if part.startswith("@") and "@" in part[1:]:
            at_idx = part.index("@", 1)
            pkg = part[:at_idx]
        if pkg:
            packages.append(pkg)
    return packages


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except Exception:
        return

    cwd = data.get("cwd") or os.getcwd()
    try:
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")
        if not command:
            return

        # Check if this is an install command
        matched_ecosystem = None
        for pattern, ecosystem in INSTALL_PATTERNS:
            if re.search(pattern, command):
                matched_ecosystem = ecosystem
                break

        if matched_ecosystem is None:
            return

        # Skip lockfile-only installs (no package names, just `npm install` or `npm ci`)
        for indicator in LOCKFILE_INDICATORS:
            if indicator in command:
                return

        # Extract package names
        packages = _extract_packages(command)
        if not packages:
            # Bare `npm install` / `pip install -r requirements.txt` — allow
            return

        # Load config
        d = Path(cwd) / "dependency-doctor"
        config_path = d / "config.json"
        if not config_path.exists():
            return

        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not config.get("auto_block", True):
            return

        approved = config.get("approved", [])
        rejected = config.get("rejected", {})

        # Check for explicitly rejected packages first
        rejected_pkgs = [pkg for pkg in packages if pkg in rejected]
        if rejected_pkgs:
            details = "; ".join(
                f"{p}: {rejected[p].get('reason', 'no reason given')}"
                for p in rejected_pkgs
            )
            reason = f"REJECTED: {details}"
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
            print(json.dumps(output), flush=True)
            return

        # Check each package
        blocked = [pkg for pkg in packages if pkg not in approved]
        if not blocked:
            return

        # Block the install
        names = ", ".join(blocked)
        reason = (
            f"BLOCKED: Package(s) not analyzed yet: {names}. "
            "Run /dependency-doctor:analyze to check before installing."
        )
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
        print(json.dumps(output), flush=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
