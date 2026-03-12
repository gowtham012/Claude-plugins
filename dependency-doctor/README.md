# dependency-doctor

A Claude Code plugin that analyzes dependencies before installation — checking bundle size, vulnerabilities, license compatibility, and more. All checks run in a single `analyze` call so nothing gets missed.

## How it works

1. **PreToolUse hook** intercepts install commands across all major package managers:
   - **npm**: `npm install`, `npm add`, `npm i`, `npx`
   - **yarn**: `yarn add`
   - **pnpm**: `pnpm add`, `pnpm install`
   - **bun**: `bun add`, `bun install`, `bunx`
   - **pip**: `pip install`, `pip3 install`, `python -m pip install`, `python3 -m pip install`
   - **uv**: `uv add`, `uv pip install`
   - **poetry**: `poetry add`
   - **pdm**: `pdm add`
2. If the package has not been analyzed and approved, the install is **blocked**
3. Lockfile-only commands (`npm ci`, `--frozen-lockfile`, `pip install -r`, `pip install -e .`) are allowed through
4. Use `/dependency-doctor:analyze <pkg>` to review a package — this fetches registry info, bundle size, vulnerabilities, and license compatibility in one call
5. Once satisfied, `/dependency-doctor:approve <pkg>` to allow installation
6. If a package is dangerous, `/dependency-doctor:reject <pkg> <reason>` to permanently block it

## Skills

| Skill | Description |
|-------|-------------|
| `/dependency-doctor:setup` | One-time project setup — creates config directory |
| `/dependency-doctor:analyze <pkg> [npm\|pip]` | Full analysis: registry info, bundle size, vulnerabilities, license compatibility |
| `/dependency-doctor:audit` | List all dependencies in the current project |
| `/dependency-doctor:approve <pkg>` | Approve a package for installation |
| `/dependency-doctor:reject <pkg> <reason>` | Permanently reject a package with a reason |

## MCP Tools

| Tool | Description |
|------|-------------|
| `setup_project` | Create dependency-doctor/ directory and config |
| `analyze_package` | Full analysis: registry info, bundle size (npm), vulnerabilities (OSV.dev), license compatibility |
| `check_vulnerabilities` | Query OSV.dev for known vulnerabilities (also called automatically by analyze) |
| `audit_project` | Read package.json / requirements.txt and list deps |
| `approve_install` | Add a package to the approved list |
| `reject_install` | Mark a package as rejected with a reason — permanently blocked |
| `toggle_auto_block` | Enable or disable automatic blocking of unapproved installs |
| `get_report` | Show all analyzed, approved, and rejected packages |

## Config

Stored in `dependency-doctor/config.json`:

```json
{
  "auto_block": true,
  "approved": [],
  "rejected": {},
  "analyzed": {}
}
```

- **auto_block** — when `true`, unapproved packages are blocked from installation
- **approved** — list of package names that can be installed freely
- **rejected** — map of package names to `{"reason": "...", "rejected_at": "..."}` — permanently blocked
- **analyzed** — map of analyzed packages with metadata

## What analyze checks

1. **Registry metadata** — version, description, homepage, dependency count
2. **Download counts** — weekly downloads from npm / pypistats link for PyPI
3. **Bundle size** (npm only) — minified and gzip sizes from bundlephobia
4. **Vulnerabilities** — queries OSV.dev for known CVEs
5. **License compatibility** — detects your project's license and warns about:
   - GPL dependencies in MIT/Apache/BSD projects
   - AGPL dependencies in non-AGPL projects
   - Unknown or proprietary licenses

## Data Sources

- **npm**: registry.npmjs.org (package info) + api.npmjs.org (download counts) + bundlephobia.com (bundle size)
- **PyPI**: pypi.org/pypi/{name}/json
- **Vulnerabilities**: api.osv.dev/v1/query
- **License detection**: package.json, pyproject.toml, or LICENSE file in project root

## Installation

Add to your Claude Code plugins or install via the marketplace. No external Python dependencies required beyond `fastmcp`.
