#!/usr/bin/env python3
"""
codebase-onboard MCP server (FastMCP).
6 tools: setup_project, generate_onboard, refresh, find_pattern, add_note, get_stats.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("codebase-onboard")

CLAUDE_MD_IMPORT = "@codebase-onboard/onboard.md"

# Framework detection: (dependency name/pattern, framework label)
FRAMEWORK_SIGNATURES = [
    # JavaScript / TypeScript
    ("next", "Next.js"),
    ("react", "React"),
    ("vue", "Vue.js"),
    ("nuxt", "Nuxt.js"),
    ("svelte", "Svelte"),
    ("angular", "Angular"),
    ("express", "Express"),
    ("fastify", "Fastify"),
    ("hono", "Hono"),
    ("nestjs", "NestJS"),
    ("@nestjs/core", "NestJS"),
    ("electron", "Electron"),
    # Python
    ("fastapi", "FastAPI"),
    ("django", "Django"),
    ("flask", "Flask"),
    ("starlette", "Starlette"),
    ("tornado", "Tornado"),
    ("celery", "Celery"),
    ("sqlalchemy", "SQLAlchemy"),
    ("pydantic", "Pydantic"),
    ("pytest", "pytest"),
    # Ruby
    ("rails", "Ruby on Rails"),
    # Go
    ("gin-gonic/gin", "Gin"),
    ("gorilla/mux", "Gorilla Mux"),
    # Rust
    ("actix-web", "Actix Web"),
    ("axum", "Axum"),
    ("tokio", "Tokio"),
    # General
    ("tailwindcss", "Tailwind CSS"),
    ("prisma", "Prisma"),
    ("drizzle-orm", "Drizzle ORM"),
    ("typeorm", "TypeORM"),
    ("mongoose", "Mongoose"),
    ("graphql", "GraphQL"),
    ("trpc", "tRPC"),
    ("@trpc/server", "tRPC"),
]

# Key directories to scan
KEY_DIRS = [
    "src", "lib", "app", "pages", "components", "api",
    "routes", "models", "services", "utils", "helpers",
    "middleware", "hooks", "config", "scripts",
    "tests", "test", "__tests__", "spec",
    "public", "static", "assets",
]


def _dir(cwd: str) -> Path:
    return Path(cwd) / "codebase-onboard"


def _onboard_file(cwd: str) -> Path:
    return _dir(cwd) / "onboard.md"


def _stats_file(cwd: str) -> Path:
    return _dir(cwd) / "stats.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_package_json(cwd: str) -> dict | None:
    """Read package.json if it exists."""
    p = Path(cwd) / "package.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _read_pyproject(cwd: str) -> dict | None:
    """Read pyproject.toml if it exists (basic parsing)."""
    p = Path(cwd) / "pyproject.toml"
    if not p.exists():
        return None
    try:
        content = p.read_text(encoding="utf-8")
        info: dict = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("name"):
                match = re.search(r'=\s*"([^"]*)"', line)
                if match:
                    info["name"] = match.group(1)
            elif line.startswith("version"):
                match = re.search(r'=\s*"([^"]*)"', line)
                if match:
                    info["version"] = match.group(1)
            elif line.startswith("description"):
                match = re.search(r'=\s*"([^"]*)"', line)
                if match:
                    info["description"] = match.group(1)
        info["_raw"] = content
        return info
    except Exception:
        return None


def _detect_frameworks(cwd: str) -> list[str]:
    """Detect frameworks from dependency files."""
    frameworks: list[str] = []
    seen: set[str] = set()

    # Check package.json
    pkg = _read_package_json(cwd)
    if pkg:
        all_deps = {}
        all_deps.update(pkg.get("dependencies", {}))
        all_deps.update(pkg.get("devDependencies", {}))
        dep_names = " ".join(all_deps.keys()).lower()
        for sig, label in FRAMEWORK_SIGNATURES:
            if label not in seen and sig.lower() in dep_names:
                frameworks.append(label)
                seen.add(label)

    # Check pyproject.toml
    pyproj = _read_pyproject(cwd)
    if pyproj and "_raw" in pyproj:
        raw = pyproj["_raw"].lower()
        for sig, label in FRAMEWORK_SIGNATURES:
            if label not in seen and sig.lower() in raw:
                frameworks.append(label)
                seen.add(label)

    # Check Cargo.toml
    cargo = Path(cwd) / "Cargo.toml"
    if cargo.exists():
        try:
            raw = cargo.read_text(encoding="utf-8").lower()
            for sig, label in FRAMEWORK_SIGNATURES:
                if label not in seen and sig.lower() in raw:
                    frameworks.append(label)
                    seen.add(label)
            if not frameworks:
                frameworks.append("Rust")
        except Exception:
            pass

    # Check go.mod
    gomod = Path(cwd) / "go.mod"
    if gomod.exists():
        try:
            raw = gomod.read_text(encoding="utf-8").lower()
            for sig, label in FRAMEWORK_SIGNATURES:
                if label not in seen and sig.lower() in raw:
                    frameworks.append(label)
                    seen.add(label)
            if not frameworks:
                frameworks.append("Go")
        except Exception:
            pass

    # Check Gemfile
    gemfile = Path(cwd) / "Gemfile"
    if gemfile.exists():
        try:
            raw = gemfile.read_text(encoding="utf-8").lower()
            for sig, label in FRAMEWORK_SIGNATURES:
                if label not in seen and sig.lower() in raw:
                    frameworks.append(label)
                    seen.add(label)
            if not frameworks:
                frameworks.append("Ruby")
        except Exception:
            pass

    return frameworks


def _count_files_by_extension(cwd: str) -> dict[str, int]:
    """Count files by extension using Path.glob."""
    root = Path(cwd)
    counts: dict[str, int] = {}
    try:
        for f in root.glob("**/*"):
            if f.is_file() and not any(
                part.startswith(".") or part == "node_modules" or part == "__pycache__"
                or part == "venv" or part == ".venv" or part == "dist" or part == "build"
                for part in f.parts
            ):
                ext = f.suffix.lower() if f.suffix else "(no ext)"
                counts[ext] = counts.get(ext, 0) + 1
    except Exception:
        pass
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def _find_key_files(cwd: str) -> dict[str, list[str]]:
    """Find key directories and their contents."""
    root = Path(cwd)
    result: dict[str, list[str]] = {}
    for d in KEY_DIRS:
        dir_path = root / d
        if dir_path.is_dir():
            files: list[str] = []
            try:
                for f in sorted(dir_path.iterdir()):
                    if not f.name.startswith("."):
                        if f.is_dir():
                            files.append(f"{f.name}/")
                        else:
                            files.append(f.name)
            except Exception:
                pass
            if files:
                result[d] = files[:30]  # Cap at 30 entries per dir
    return result


CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".rb", ".java",
    ".vue", ".svelte", ".c", ".cpp", ".h", ".hpp", ".cs", ".swift",
    ".kt", ".scala", ".php", ".ex", ".exs", ".erl", ".hs", ".ml",
    ".sh", ".bash", ".zsh", ".lua", ".r", ".sql",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", ".cache", ".tox", ".mypy_cache",
    ".pytest_cache", "codebase-onboard", ".eggs", "egg-info",
    "coverage", ".coverage", "htmlcov", "target",
}


def _get_total_lines(cwd: str) -> int:
    """Count total lines of code by walking the directory tree in Python."""
    total = 0
    root = Path(cwd)
    try:
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if any(part in SKIP_DIRS or part.startswith(".") for part in f.relative_to(root).parts[:-1]):
                continue
            if f.suffix.lower() in CODE_EXTENSIONS:
                try:
                    total += sum(1 for _ in f.open(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
    except Exception:
        pass
    return total


def _analyze_imports(cwd: str) -> dict[str, list[str]]:
    """Analyze import patterns to discover internal module dependencies."""
    root = Path(cwd)
    imports: dict[str, list[str]] = {}
    try:
        for f in root.rglob("*"):
            if not f.is_file() or f.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx"}:
                continue
            if any(part in SKIP_DIRS or part.startswith(".") for part in f.relative_to(root).parts[:-1]):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                rel = str(f.relative_to(root))
                file_imports = []
                for line in content.splitlines()[:100]:  # scan first 100 lines
                    line = line.strip()
                    if f.suffix == ".py":
                        if line.startswith("import ") or line.startswith("from "):
                            file_imports.append(line)
                    elif f.suffix.lower() in {".js", ".ts", ".tsx", ".jsx"}:
                        if "import " in line and "from" in line:
                            file_imports.append(line)
                        elif line.startswith("const ") and "require(" in line:
                            file_imports.append(line)
                if file_imports:
                    imports[rel] = file_imports[:20]  # cap at 20 per file
            except Exception:
                pass
    except Exception:
        pass
    return imports


def _detect_patterns(cwd: str) -> list[str]:
    """Detect code patterns and conventions by scanning the codebase."""
    root = Path(cwd)
    patterns = []

    # Check for common patterns
    has_types = False
    has_tests = False
    has_ci = False
    has_docker = False
    has_env = False
    has_orm = False
    has_api_routes = False
    naming_styles: dict[str, int] = {"camelCase": 0, "snake_case": 0, "PascalCase": 0}

    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(part in SKIP_DIRS for part in f.relative_to(root).parts):
            continue
        name = f.name.lower()

        if name.endswith(".d.ts") or name == "tsconfig.json":
            has_types = True
        if "test" in name or "spec" in name:
            has_tests = True
        if name in {".github", "ci.yml", "ci.yaml", ".travis.yml", "jenkinsfile"}:
            has_ci = True
        if name in {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
            has_docker = True
        if name in {".env", ".env.example", ".env.local"}:
            has_env = True

        # Check for naming conventions in Python/JS files
        if f.suffix in {".py", ".js", ".ts"} and f.stat().st_size < 50000:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")[:5000]
                if re.search(r"\bdef [a-z]+_[a-z]", content):
                    naming_styles["snake_case"] += 1
                if re.search(r"\bfunction [a-z]+[A-Z]", content) or re.search(r"\bconst [a-z]+[A-Z]", content):
                    naming_styles["camelCase"] += 1
                if re.search(r"\bclass [A-Z][a-z]+[A-Z]", content):
                    naming_styles["PascalCase"] += 1
                if "prisma" in content.lower() or "sequelize" in content.lower() or "sqlalchemy" in content.lower() or "typeorm" in content.lower():
                    has_orm = True
                if "router." in content or "app.get(" in content or "app.post(" in content or "@app.route" in content:
                    has_api_routes = True
            except Exception:
                pass

    if has_types:
        patterns.append("TypeScript types/declarations present — project uses static typing")
    if has_tests:
        patterns.append("Test files found — project has test coverage")
    if (root / ".github" / "workflows").is_dir():
        patterns.append("GitHub Actions CI/CD configured")
    if has_docker:
        patterns.append("Docker containerization set up")
    if has_env:
        patterns.append("Environment variables used (.env files) — check .env.example for required vars")
    if has_orm:
        patterns.append("ORM/database layer detected — check models/ or schema files")
    if has_api_routes:
        patterns.append("API route handlers found — check routes/ or app files for endpoints")

    dominant_style = max(naming_styles, key=naming_styles.get) if any(naming_styles.values()) else None
    if dominant_style:
        patterns.append(f"Dominant naming convention: {dominant_style}")

    return patterns


def _find_entry_points(cwd: str) -> list[str]:
    """Find likely entry points of the application."""
    root = Path(cwd)
    entry_points = []
    candidates = [
        "src/index.ts", "src/index.js", "src/main.ts", "src/main.js",
        "src/app.ts", "src/app.js", "src/server.ts", "src/server.js",
        "app/page.tsx", "app/layout.tsx", "pages/index.tsx", "pages/index.js",
        "main.py", "app.py", "manage.py", "src/main.py", "src/app.py",
        "main.go", "cmd/main.go", "src/main.rs", "src/lib.rs",
    ]
    for c in candidates:
        if (root / c).exists():
            entry_points.append(c)

    # Check package.json main/bin fields
    pkg = _read_package_json(cwd)
    if pkg:
        if "main" in pkg:
            entry_points.append(f"{pkg['main']} (package.json main)")
        if "bin" in pkg:
            if isinstance(pkg["bin"], str):
                entry_points.append(f"{pkg['bin']} (package.json bin)")
            elif isinstance(pkg["bin"], dict):
                for name, path in pkg["bin"].items():
                    entry_points.append(f"{path} (bin: {name})")

    return entry_points


def _get_directory_tree(cwd: str) -> str:
    """Build a directory tree string (top-level + one level deep)."""
    root = Path(cwd)
    tree_lines: list[str] = []
    skip = {
        "node_modules", ".git", "__pycache__", "venv", ".venv",
        "dist", "build", ".next", ".cache", ".tox", ".mypy_cache",
        ".pytest_cache", "codebase-onboard",
    }
    try:
        entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for entry in entries:
            if entry.name in skip or entry.name.startswith("."):
                continue
            if entry.is_dir():
                tree_lines.append(f"  {entry.name}/")
                try:
                    children = sorted(entry.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
                    for child in children[:15]:
                        if child.name.startswith(".") or child.name in skip:
                            continue
                        suffix = "/" if child.is_dir() else ""
                        tree_lines.append(f"    {child.name}{suffix}")
                    remaining = len([c for c in children[15:] if not c.name.startswith(".")])
                    if remaining > 0:
                        tree_lines.append(f"    ... and {remaining} more")
                except Exception:
                    pass
            else:
                tree_lines.append(f"  {entry.name}")
    except Exception:
        tree_lines.append("  (unable to read directory)")
    return "\n".join(tree_lines)


def _generate_onboard_doc(cwd: str) -> str:
    """Generate the full onboarding markdown document."""
    root = Path(cwd)
    ts = _now_iso()

    # Project info
    project_name = root.name
    project_desc = ""
    project_version = ""
    scripts: dict = {}

    pkg = _read_package_json(cwd)
    if pkg:
        project_name = pkg.get("name", project_name)
        project_desc = pkg.get("description", "")
        project_version = pkg.get("version", "")
        scripts = pkg.get("scripts", {})

    pyproj = _read_pyproject(cwd)
    if pyproj:
        project_name = pyproj.get("name", project_name)
        project_desc = pyproj.get("description", project_desc)
        project_version = pyproj.get("version", project_version)

    # Detect frameworks
    frameworks = _detect_frameworks(cwd)

    # File counts
    file_counts = _count_files_by_extension(cwd)

    # Key files
    key_files = _find_key_files(cwd)

    # Total lines
    total_lines = _get_total_lines(cwd)

    # Directory tree
    dir_tree = _get_directory_tree(cwd)

    # Build the document
    sections: list[str] = []

    # Header
    sections.append(f"# {project_name} — Onboarding Guide")
    sections.append(f"\n> Auto-generated by codebase-onboard on {ts[:10]}")
    if project_desc:
        sections.append(f">\n> {project_desc}")
    if project_version:
        sections.append(f">\n> Version: {project_version}")

    # Project Overview
    sections.append("\n---\n\n## Project Overview\n")
    sections.append(f"**Name:** {project_name}")
    if project_desc:
        sections.append(f"**Description:** {project_desc}")
    if project_version:
        sections.append(f"**Version:** {project_version}")
    total_files = sum(file_counts.values())
    sections.append(f"**Total files:** {total_files}")
    if total_lines > 0:
        sections.append(f"**Total lines of code:** ~{total_lines:,}")

    # Tech Stack
    sections.append("\n---\n\n## Tech Stack\n")
    if frameworks:
        for fw in frameworks:
            sections.append(f"- {fw}")
    else:
        sections.append("- (no frameworks auto-detected)")

    # Top file types
    if file_counts:
        sections.append("\n**File types:**\n")
        for ext, count in list(file_counts.items())[:15]:
            sections.append(f"- `{ext}`: {count} files")

    # Directory Structure
    sections.append("\n---\n\n## Directory Structure\n")
    sections.append("```")
    sections.append(f"{project_name}/")
    sections.append(dir_tree)
    sections.append("```")

    # Key Files
    sections.append("\n---\n\n## Key Files\n")
    if key_files:
        for dirname, files in key_files.items():
            sections.append(f"### `{dirname}/`\n")
            for f in files:
                sections.append(f"- `{f}`")
            sections.append("")
    else:
        sections.append("(no standard directories found — src/, lib/, app/, tests/)")

    # Scripts / Commands
    if scripts:
        sections.append("\n---\n\n## Available Scripts\n")
        for name, cmd in scripts.items():
            sections.append(f"- `npm run {name}` — `{cmd}`")

    # Entry Points
    entry_points = _find_entry_points(cwd)
    if entry_points:
        sections.append("\n---\n\n## Entry Points\n")
        for ep in entry_points:
            sections.append(f"- `{ep}`")

    # Architecture Notes
    sections.append("\n---\n\n## Architecture Notes\n")
    arch_notes: list[str] = []
    if (root / "src").is_dir():
        arch_notes.append("- Source code lives in `src/`")
    if (root / "app").is_dir():
        arch_notes.append("- App directory pattern (`app/`) — likely Next.js App Router or similar")
    if (root / "pages").is_dir():
        arch_notes.append("- Pages directory — file-based routing (Next.js pages router, Nuxt, etc.)")
    if (root / "api").is_dir() or (root / "src" / "api").is_dir():
        arch_notes.append("- Dedicated API directory for backend routes/endpoints")
    if (root / "models").is_dir() or (root / "src" / "models").is_dir():
        arch_notes.append("- Models directory — data layer / ORM models")
    if (root / "services").is_dir() or (root / "src" / "services").is_dir():
        arch_notes.append("- Services directory — business logic separated from routes")
    if (root / "middleware").is_dir() or (root / "src" / "middleware").is_dir():
        arch_notes.append("- Middleware directory — request/response interceptors")
    if (root / "components").is_dir() or (root / "src" / "components").is_dir():
        arch_notes.append("- Components directory — reusable UI components")
    if (root / "hooks").is_dir() or (root / "src" / "hooks").is_dir():
        arch_notes.append("- Hooks directory — custom React hooks or similar")
    if (root / "utils").is_dir() or (root / "src" / "utils").is_dir():
        arch_notes.append("- Utils/helpers directory — shared utility functions")
    if (root / "tests").is_dir() or (root / "test").is_dir() or (root / "__tests__").is_dir():
        arch_notes.append("- Test directory present — project has test infrastructure")
    if (root / "docker-compose.yml").exists() or (root / "Dockerfile").exists():
        arch_notes.append("- Docker configuration found — containerized deployment")
    if (root / ".github" / "workflows").is_dir():
        arch_notes.append("- GitHub Actions CI/CD workflows configured")
    if (root / "Makefile").exists():
        arch_notes.append("- Makefile present — check `make help` or read it for common commands")

    if arch_notes:
        sections.append("\n".join(arch_notes))
    else:
        sections.append("(add architecture notes here as you explore the codebase)")

    # Detected Patterns
    detected_patterns = _detect_patterns(cwd)
    if detected_patterns:
        sections.append("\n---\n\n## Detected Patterns & Conventions\n")
        for p in detected_patterns:
            sections.append(f"- {p}")

    # Internal Dependencies (top files with most imports)
    imports = _analyze_imports(cwd)
    if imports:
        sections.append("\n---\n\n## Key Module Dependencies\n")
        # Show top 10 files with most imports
        sorted_imports = sorted(imports.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for filepath, imp_list in sorted_imports:
            sections.append(f"\n### `{filepath}` ({len(imp_list)} imports)\n")
            for imp in imp_list[:5]:
                sections.append(f"- `{imp[:100]}`")
            if len(imp_list) > 5:
                sections.append(f"- ... and {len(imp_list) - 5} more")

    # Getting Started
    sections.append("\n---\n\n## Getting Started\n")
    getting_started: list[str] = []

    if pkg:
        getting_started.append("1. Install dependencies: `npm install`")
        if "dev" in scripts:
            getting_started.append(f"2. Start development: `npm run dev`")
        elif "start" in scripts:
            getting_started.append(f"2. Start the app: `npm start`")
        if "test" in scripts:
            getting_started.append(f"3. Run tests: `npm test`")
        if "build" in scripts:
            getting_started.append(f"4. Build: `npm run build`")
    elif pyproj:
        getting_started.append("1. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`")
        getting_started.append("2. Install dependencies: `pip install -e .` or `uv pip install -e .`")
        if (root / "pytest.ini").exists() or (root / "tests").is_dir():
            getting_started.append("3. Run tests: `pytest`")
    elif (root / "Cargo.toml").exists():
        getting_started.append("1. Build: `cargo build`")
        getting_started.append("2. Run: `cargo run`")
        getting_started.append("3. Test: `cargo test`")
    elif (root / "go.mod").exists():
        getting_started.append("1. Build: `go build ./...`")
        getting_started.append("2. Run: `go run .`")
        getting_started.append("3. Test: `go test ./...`")
    else:
        getting_started.append("(add getting started steps as you learn the project)")

    sections.append("\n".join(getting_started))

    # Custom Notes placeholder
    sections.append("\n---\n\n## Custom Notes\n")
    sections.append("(add your own notes here with `/codebase-onboard:find` and `add_note`)")

    # Footer
    sections.append(f"\n---\n\n*Last generated: {ts}*")

    return "\n".join(sections) + "\n"


@mcp.tool()
def setup_project(cwd: str) -> str:
    """
    One-time setup for codebase-onboard in the current project.
    Creates codebase-onboard/ directory and adds @import to CLAUDE.md
    so the onboarding guide auto-loads every session.
    """
    out_dir = _dir(cwd)
    out_dir.mkdir(parents=True, exist_ok=True)

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
        f"codebase-onboard set up in {out_dir}.\n"
        f"{claude_md_status}\n"
        "Run /codebase-onboard:onboard to generate the onboarding guide."
    )


@mcp.tool()
def generate_onboard(cwd: str) -> str:
    """
    Scans the project and generates a comprehensive onboarding guide.
    Reads package.json/pyproject.toml for project info, detects frameworks,
    maps directory structure, identifies key files, and produces a markdown
    onboarding document at codebase-onboard/onboard.md.
    """
    out_dir = _dir(cwd)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate the onboarding doc
    doc = _generate_onboard_doc(cwd)
    _onboard_file(cwd).write_text(doc, encoding="utf-8")

    # Generate stats
    file_counts = _count_files_by_extension(cwd)
    frameworks = _detect_frameworks(cwd)
    total_lines = _get_total_lines(cwd)
    stats = {
        "generated_at": _now_iso(),
        "total_files": sum(file_counts.values()),
        "total_lines": total_lines,
        "files_by_extension": file_counts,
        "frameworks_detected": frameworks,
    }
    _stats_file(cwd).write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    total_files = sum(file_counts.values())
    fw_str = ", ".join(frameworks) if frameworks else "none detected"

    return (
        f"Onboarding guide generated at {_onboard_file(cwd)}.\n"
        f"Stats saved to {_stats_file(cwd)}.\n"
        f"Scanned {total_files} files, ~{total_lines:,} lines of code.\n"
        f"Frameworks detected: {fw_str}."
    )


@mcp.tool()
def refresh(cwd: str) -> str:
    """
    Regenerates the onboarding document by re-scanning the project.
    Use this after significant changes to the codebase.
    """
    if not _dir(cwd).exists():
        return "codebase-onboard not set up yet. Run setup_project first."

    return generate_onboard(cwd)


@mcp.tool()
def find_pattern(cwd: str, query: str) -> str:
    """
    Searches the onboarding document for a specific pattern or topic.
    Returns the relevant section(s) matching the query.
    """
    onboard = _onboard_file(cwd)
    if not onboard.exists():
        return "No onboarding doc found. Run generate_onboard first."

    content = onboard.read_text(encoding="utf-8")
    query_lower = query.lower()

    # Split into sections by ## headings
    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_heading or current_lines:
                sections.append((current_heading, "\n".join(current_lines)))
            current_heading = line
            current_lines = []
        else:
            current_lines.append(line)
    if current_heading or current_lines:
        sections.append((current_heading, "\n".join(current_lines)))

    # Find matching sections
    matches: list[str] = []
    for heading, body in sections:
        if query_lower in heading.lower() or query_lower in body.lower():
            matches.append(f"{heading}\n{body}")

    if not matches:
        # Try individual word matching
        words = query_lower.split()
        for heading, body in sections:
            full = (heading + body).lower()
            if any(w in full for w in words):
                matches.append(f"{heading}\n{body}")

    if matches:
        return f"Found {len(matches)} matching section(s) for '{query}':\n\n" + "\n\n---\n\n".join(matches)
    else:
        return f"No sections matching '{query}' found in the onboarding doc."


@mcp.tool()
def add_note(cwd: str, section: str, note: str) -> str:
    """
    Adds a custom note to a section of the onboarding document.
    The section parameter should match a heading (e.g., 'Architecture Notes',
    'Custom Notes', 'Getting Started'). The note is appended under that section.
    """
    onboard = _onboard_file(cwd)
    if not onboard.exists():
        return "No onboarding doc found. Run generate_onboard first."

    content = onboard.read_text(encoding="utf-8")
    section_lower = section.lower().strip()

    # Find the section heading
    lines = content.splitlines()
    insert_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("## ") and section_lower in line.lower():
            # Find the end of this section (next ## or ---)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## ") or lines[j].strip() == "---":
                    insert_idx = j
                    break
            else:
                insert_idx = len(lines)
            break

    if insert_idx == -1:
        return (
            f"Section '{section}' not found. Available sections: "
            + ", ".join(
                line.replace("## ", "")
                for line in lines
                if line.startswith("## ")
            )
        )

    # Insert the note before the section boundary
    ts = _now_iso()[:10]
    note_line = f"- [{ts}] {note}"
    lines.insert(insert_idx, note_line)
    lines.insert(insert_idx, "")

    onboard.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"Note added to '{section}': {note}"


@mcp.tool()
def get_stats(cwd: str) -> str:
    """
    Returns codebase statistics: file count by type, total lines,
    and frameworks detected. Reads from cached stats or regenerates.
    """
    stats_path = _stats_file(cwd)

    # Regenerate stats fresh
    file_counts = _count_files_by_extension(cwd)
    frameworks = _detect_frameworks(cwd)
    total_lines = _get_total_lines(cwd)
    total_files = sum(file_counts.values())

    stats = {
        "generated_at": _now_iso(),
        "total_files": total_files,
        "total_lines": total_lines,
        "files_by_extension": file_counts,
        "frameworks_detected": frameworks,
    }

    # Save stats
    out_dir = _dir(cwd)
    out_dir.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    # Format output
    parts: list[str] = []
    parts.append(f"## Codebase Stats\n")
    parts.append(f"**Total files:** {total_files}")
    parts.append(f"**Total lines of code:** ~{total_lines:,}")

    if frameworks:
        parts.append(f"**Frameworks:** {', '.join(frameworks)}")
    else:
        parts.append("**Frameworks:** none auto-detected")

    parts.append(f"\n**Files by extension:**\n")
    for ext, count in list(file_counts.items())[:20]:
        parts.append(f"- `{ext}`: {count}")

    parts.append(f"\n*Stats saved to {stats_path}*")

    return "\n".join(parts)


if __name__ == "__main__":
    mcp.run()
