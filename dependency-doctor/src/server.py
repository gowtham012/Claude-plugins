#!/usr/bin/env python3
"""dependency-doctor MCP server — analyzes dependencies before installation."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("dependency-doctor")


def _dir(cwd: str) -> Path:
    return Path(cwd) / "dependency-doctor"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default: dict) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default.copy()


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.rename(path)


def _default_config() -> dict:
    return {"auto_block": True, "approved": [], "rejected": {}, "analyzed": {}}


# ---------------------------------------------------------------------------
# License compatibility helpers
# ---------------------------------------------------------------------------
# Licenses considered "copyleft" / restrictive
_GPL_FAMILY = {"GPL-2.0", "GPL-2.0-only", "GPL-2.0-or-later",
               "GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later"}
_AGPL_FAMILY = {"AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later"}
_PERMISSIVE = {"MIT", "ISC", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0",
               "0BSD", "Unlicense", "CC0-1.0"}


def _normalize_license(lic: str) -> str:
    """Best-effort SPDX normalization."""
    if not lic:
        return "unknown"
    lic = lic.strip()
    # Common non-SPDX names
    mapping = {
        "MIT License": "MIT",
        "Apache License 2.0": "Apache-2.0",
        "Apache 2.0": "Apache-2.0",
        "BSD": "BSD-3-Clause",
        "ISC License": "ISC",
    }
    return mapping.get(lic, lic)


def _check_license_compatibility(project_license: str, dep_license: str) -> str | None:
    """Return a warning string if dep_license is incompatible with project_license, else None."""
    proj = _normalize_license(project_license)
    dep = _normalize_license(dep_license)

    if dep in ("unknown", "UNKNOWN", "NOASSERTION", "") or dep.upper() == "NONE":
        return f"License is '{dep}' (unknown/proprietary) — review manually before using."

    # AGPL in anything non-AGPL
    if dep in _AGPL_FAMILY and proj not in _AGPL_FAMILY:
        return (f"AGPL dependency ({dep}) in a {proj} project — "
                "AGPL requires sharing source of network-accessible services.")

    # GPL in permissive projects
    if dep in _GPL_FAMILY and proj in _PERMISSIVE:
        return (f"GPL dependency ({dep}) in a {proj} project — "
                "GPL is copyleft and requires derivative works to also be GPL-licensed.")

    # GPL in Apache projects
    if dep in _GPL_FAMILY and proj == "Apache-2.0":
        return (f"GPL dependency ({dep}) in an Apache-2.0 project — "
                "GPL copyleft is incompatible with Apache-2.0.")

    return None


def _fetch_json(url: str, data: bytes | None = None, method: str = "GET") -> dict:
    """Fetch JSON from a URL using urllib.request."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "dependency-doctor/1.0")
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.method = "POST"
        resp = urllib.request.urlopen(req, data, timeout=15)
    else:
        resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode("utf-8"))


def _detect_project_license(cwd: str) -> str:
    """Try to detect the project's license from package.json or LICENSE file."""
    p = Path(cwd)
    # Check package.json first
    pkg_json = p / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            lic = pkg.get("license", "")
            if lic:
                return _normalize_license(str(lic))
        except Exception:
            pass
    # Check pyproject.toml (simple parse)
    pyproject = p / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            for line in content.splitlines():
                if "license" in line.lower() and "=" in line:
                    # e.g. license = { text = "MIT" } or license = "MIT"
                    if '"' in line:
                        parts = line.split('"')
                        if len(parts) >= 2:
                            return _normalize_license(parts[-2])
        except Exception:
            pass
    # Check LICENSE file header
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
        lic_file = p / name
        if lic_file.exists():
            try:
                header = lic_file.read_text(encoding="utf-8")[:500].upper()
                if "MIT" in header:
                    return "MIT"
                if "APACHE" in header:
                    return "Apache-2.0"
                if "BSD" in header:
                    return "BSD-3-Clause"
                if "GPL" in header and "AGPL" not in header:
                    return "GPL-3.0"
                if "AGPL" in header:
                    return "AGPL-3.0"
            except Exception:
                pass
    return "unknown"


def _fetch_bundle_size(package_name: str, version: str) -> dict | None:
    """Fetch bundle size estimation from bundlephobia for npm packages."""
    try:
        url = f"https://bundlephobia.com/api/size?package={package_name}@{version}"
        data = _fetch_json(url)
        return {
            "size_bytes": data.get("size", 0),
            "gzip_bytes": data.get("gzip", 0),
            "size_kb": round(data.get("size", 0) / 1024, 1),
            "gzip_kb": round(data.get("gzip", 0) / 1024, 1),
        }
    except Exception:
        return None


@mcp.tool()
def setup_project(cwd: str) -> str:
    """One-time setup. Creates dependency-doctor/ directory and initializes config."""
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)
    (d / "reports").mkdir(exist_ok=True)
    if not (d / "config.json").exists():
        _save_json(d / "config.json", _default_config())
    return (
        f"dependency-doctor set up in {d}.\n"
        "Config created with auto_block enabled.\n"
        "Use /dependency-doctor:analyze to check packages before installing."
    )


@mcp.tool()
def analyze_package(cwd: str, package_name: str, ecosystem: str = "npm") -> str:
    """Analyze a package: fetches info, version, license, downloads, bundle size,
    vulnerabilities, and license compatibility — all in one call.

    ecosystem: 'npm' or 'pip'.
    """
    d = _dir(cwd)
    d.mkdir(parents=True, exist_ok=True)
    (d / "reports").mkdir(exist_ok=True)

    report: dict = {
        "package": package_name,
        "ecosystem": ecosystem,
        "analyzed_at": _now(),
        "status": "unknown",
    }

    try:
        if ecosystem == "npm":
            url = f"https://registry.npmjs.org/{package_name}"
            data = _fetch_json(url)
            latest_version = data.get("dist-tags", {}).get("latest", "unknown")
            latest_info = data.get("versions", {}).get(latest_version, {})
            report["version"] = latest_version
            report["description"] = data.get("description", "")
            report["license"] = latest_info.get("license", data.get("license", "unknown"))
            report["homepage"] = data.get("homepage", "")
            # Fetch download counts
            try:
                dl_url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
                dl_data = _fetch_json(dl_url)
                report["weekly_downloads"] = dl_data.get("downloads", 0)
            except Exception:
                report["weekly_downloads"] = "unavailable"
            # Dependencies count
            deps = latest_info.get("dependencies", {})
            report["dependency_count"] = len(deps)
            # Bundle size estimation (npm only)
            bundle = _fetch_bundle_size(package_name, latest_version)
            if bundle:
                report["bundle_size"] = bundle
            report["status"] = "analyzed"

        elif ecosystem == "pip":
            url = f"https://pypi.org/pypi/{package_name}/json"
            data = _fetch_json(url)
            info = data.get("info", {})
            report["version"] = info.get("version", "unknown")
            report["description"] = info.get("summary", "")
            report["license"] = info.get("license", "unknown")
            report["homepage"] = info.get("home_page", info.get("project_url", ""))
            report["author"] = info.get("author", "")
            report["weekly_downloads"] = "check pypistats.org"
            requires = info.get("requires_dist") or []
            report["dependency_count"] = len(requires)
            report["status"] = "analyzed"
        else:
            report["status"] = "error"
            report["error"] = f"Unsupported ecosystem: {ecosystem}"

    except urllib.error.HTTPError as e:
        report["status"] = "error"
        report["error"] = f"HTTP {e.code}: package not found or registry error"
    except Exception as e:
        report["status"] = "error"
        report["error"] = str(e)

    # --- Vulnerability check (integrated) ---
    vuln_lines: list[str] = []
    if report["status"] == "analyzed":
        osv_ecosystem = "npm" if ecosystem == "npm" else "PyPI"
        try:
            payload = json.dumps({
                "package": {
                    "name": package_name,
                    "ecosystem": osv_ecosystem,
                }
            }).encode("utf-8")
            result = _fetch_json("https://api.osv.dev/v1/query", data=payload)
            vulns = result.get("vulns", [])
            report["vulnerabilities"] = len(vulns)
            report["vuln_ids"] = [v.get("id", "?") for v in vulns[:10]]
            if vulns:
                vuln_lines.append(f"\n### Vulnerabilities ({len(vulns)} found)")
                for v in vulns[:10]:
                    vid = v.get("id", "?")
                    summary = v.get("summary", "No summary")
                    severity = "unknown"
                    for s in v.get("severity", []):
                        severity = s.get("score", severity)
                    vuln_lines.append(f"- **{vid}**: {summary} (severity: {severity})")
                if len(vulns) > 10:
                    vuln_lines.append(f"- ... and {len(vulns) - 10} more")
            else:
                vuln_lines.append("\n### Vulnerabilities")
                vuln_lines.append("No known vulnerabilities found.")
        except Exception as e:
            vuln_lines.append(f"\n### Vulnerabilities")
            vuln_lines.append(f"Could not check: {e}")

    # --- License compatibility check ---
    license_warning: str | None = None
    if report["status"] == "analyzed" and report.get("license"):
        project_license = _detect_project_license(cwd)
        if project_license != "unknown":
            license_warning = _check_license_compatibility(
                project_license, _normalize_license(str(report["license"]))
            )
            if license_warning:
                report["license_warning"] = license_warning

    # Save report
    _save_json(d / "reports" / f"{package_name}.json", report)

    # Update analyzed list in config
    config = _load_json(d / "config.json", _default_config())
    config.setdefault("analyzed", {})[package_name] = {
        "ecosystem": ecosystem,
        "version": report.get("version", "unknown"),
        "status": report["status"],
        "analyzed_at": report["analyzed_at"],
    }
    _save_json(d / "config.json", config)

    # Format output
    lines = [f"## Package Analysis: {package_name} ({ecosystem})"]
    if report["status"] == "error":
        lines.append(f"ERROR: {report.get('error', 'unknown error')}")
    else:
        lines.append(f"- **Version**: {report.get('version', '?')}")
        lines.append(f"- **Description**: {report.get('description', '?')}")
        lines.append(f"- **License**: {report.get('license', '?')}")
        lines.append(f"- **Weekly downloads**: {report.get('weekly_downloads', '?')}")
        lines.append(f"- **Dependencies**: {report.get('dependency_count', '?')}")
        if report.get("homepage"):
            lines.append(f"- **Homepage**: {report['homepage']}")
        # Bundle size (npm only)
        bundle = report.get("bundle_size")
        if bundle:
            lines.append(f"- **Bundle size**: {bundle['size_kb']} KB (gzip: {bundle['gzip_kb']} KB)")
        # License warning
        if license_warning:
            lines.append(f"\n> **LICENSE WARNING**: {license_warning}")
        # Vulnerabilities
        lines.extend(vuln_lines)
    lines.append("")
    lines.append(f"Report saved to dependency-doctor/reports/{package_name}.json")
    lines.append("Run /dependency-doctor:approve to approve installation.")
    return "\n".join(lines)


@mcp.tool()
def check_vulnerabilities(cwd: str, package_name: str, ecosystem: str = "npm") -> str:
    """Check OSV.dev for known vulnerabilities in a package."""
    d = _dir(cwd)
    osv_ecosystem = "npm" if ecosystem == "npm" else "PyPI"

    # First get the latest version
    report_path = d / "reports" / f"{package_name}.json"
    version = "latest"
    if report_path.exists():
        report = _load_json(report_path, {})
        version = report.get("version", "latest")

    try:
        payload = json.dumps({
            "package": {
                "name": package_name,
                "ecosystem": osv_ecosystem,
            }
        }).encode("utf-8")
        result = _fetch_json("https://api.osv.dev/v1/query", data=payload)
        vulns = result.get("vulns", [])
    except Exception as e:
        return f"Error checking vulnerabilities: {e}"

    # Update report with vuln info
    if report_path.exists():
        report = _load_json(report_path, {})
        report["vulnerabilities"] = len(vulns)
        report["vuln_ids"] = [v.get("id", "?") for v in vulns[:10]]
        _save_json(report_path, report)

    if not vulns:
        return f"No known vulnerabilities found for {package_name} ({osv_ecosystem})."

    lines = [f"## Vulnerabilities for {package_name} ({osv_ecosystem})"]
    lines.append(f"Found **{len(vulns)}** known vulnerability(ies):\n")
    for v in vulns[:10]:
        vid = v.get("id", "?")
        summary = v.get("summary", "No summary")
        severity = "unknown"
        for s in v.get("severity", []):
            severity = s.get("score", severity)
        lines.append(f"- **{vid}**: {summary} (severity: {severity})")
    if len(vulns) > 10:
        lines.append(f"- ... and {len(vulns) - 10} more")
    lines.append("\nConsider alternatives or check if patches are available.")
    return "\n".join(lines)


@mcp.tool()
def audit_project(cwd: str) -> str:
    """Read package.json or requirements.txt and list all dependencies with versions."""
    p = Path(cwd)
    lines = ["## Dependency Audit"]
    found = False

    # Check package.json
    pkg_json = p / "package.json"
    if pkg_json.exists():
        found = True
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = pkg.get("dependencies", {})
            dev_deps = pkg.get("devDependencies", {})
            lines.append(f"\n### package.json ({len(deps)} deps, {len(dev_deps)} devDeps)")
            if deps:
                lines.append("\n**Dependencies:**")
                for name, ver in sorted(deps.items()):
                    lines.append(f"- {name}: {ver}")
            if dev_deps:
                lines.append("\n**Dev Dependencies:**")
                for name, ver in sorted(dev_deps.items()):
                    lines.append(f"- {name}: {ver}")
        except Exception as e:
            lines.append(f"Error reading package.json: {e}")

    # Check requirements.txt
    req_txt = p / "requirements.txt"
    if req_txt.exists():
        found = True
        try:
            reqs = [
                line.strip()
                for line in req_txt.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            lines.append(f"\n### requirements.txt ({len(reqs)} packages)")
            for req in reqs:
                lines.append(f"- {req}")
        except Exception as e:
            lines.append(f"Error reading requirements.txt: {e}")

    if not found:
        lines.append("\nNo package.json or requirements.txt found in the project root.")

    return "\n".join(lines)


@mcp.tool()
def approve_install(cwd: str, package_name: str) -> str:
    """Mark a package as approved for installation."""
    d = _dir(cwd)
    config = _load_json(d / "config.json", _default_config())
    approved = config.get("approved", [])
    if package_name not in approved:
        approved.append(package_name)
        config["approved"] = approved
        _save_json(d / "config.json", config)
        return f"Package '{package_name}' approved for installation."
    return f"Package '{package_name}' is already approved."


@mcp.tool()
def reject_install(cwd: str, package_name: str, reason: str) -> str:
    """Mark a package as rejected with a reason. The install hook will block it permanently."""
    d = _dir(cwd)
    config = _load_json(d / "config.json", _default_config())
    rejected = config.get("rejected", {})
    rejected[package_name] = {"reason": reason, "rejected_at": _now()}
    config["rejected"] = rejected
    # Also remove from approved if present
    approved = config.get("approved", [])
    if package_name in approved:
        approved.remove(package_name)
        config["approved"] = approved
    _save_json(d / "config.json", config)
    return f"Package '{package_name}' rejected: {reason}"


@mcp.tool()
def toggle_auto_block(cwd: str, enabled: bool) -> str:
    """Enable or disable automatic blocking of unapproved package installs."""
    d = _dir(cwd)
    config = _load_json(d / "config.json", _default_config())
    config["auto_block"] = enabled
    _save_json(d / "config.json", config)
    state = "enabled" if enabled else "disabled"
    return f"Auto-block is now {state}. {'Unapproved packages will be blocked.' if enabled else 'All installs are allowed.'}"


@mcp.tool()
def get_report(cwd: str) -> str:
    """Show all analyzed packages and their status."""
    d = _dir(cwd)
    config = _load_json(d / "config.json", _default_config())
    analyzed = config.get("analyzed", {})
    approved = config.get("approved", [])
    auto_block = config.get("auto_block", True)

    rejected = config.get("rejected", {})

    lines = ["## Dependency Doctor Report"]
    lines.append(f"- Auto-block: {'enabled' if auto_block else 'disabled'}")
    lines.append(f"- Approved packages: {len(approved)}")
    lines.append(f"- Rejected packages: {len(rejected)}")
    lines.append(f"- Analyzed packages: {len(analyzed)}")

    if approved:
        lines.append("\n### Approved")
        for pkg in sorted(approved):
            lines.append(f"- {pkg}")

    if rejected:
        lines.append("\n### Rejected")
        for pkg, info in sorted(rejected.items()):
            reason = info.get("reason", "no reason")
            lines.append(f"- **{pkg}**: {reason}")

    if analyzed:
        lines.append("\n### Analyzed")
        for pkg, info in sorted(analyzed.items()):
            status = info.get("status", "?")
            ver = info.get("version", "?")
            eco = info.get("ecosystem", "?")
            marker = " (approved)" if pkg in approved else ""
            if pkg in rejected:
                marker = " (REJECTED)"
            lines.append(f"- **{pkg}** v{ver} [{eco}] — {status}{marker}")

    if not analyzed and not approved:
        lines.append("\nNo packages analyzed yet. Use /dependency-doctor:analyze to get started.")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
