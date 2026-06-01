"""
Context generator — produces CONTEXT.md (compressed <15K tokens).
This is the key file that AI models consume to understand a project instantly.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


class ContextGenerator:
    """Generates a compressed context document optimized for AI consumption."""

    def __init__(self, scan_data: Dict[str, Any], max_tokens: int = 10000):
        self.data = scan_data
        # Rough estimate: 1 token ≈ 4 chars
        self.max_chars = max_tokens * 4

    def generate(self) -> str:
        """Generate CONTEXT.md — compressed project context for AI models."""
        sections = []

        # 1. Project summary (essential - always included)
        sections.append(self._section_project_summary())

        # 2. Architecture summary
        sections.append(self._section_architecture())

        # 3. Database summary
        sections.append(self._section_database())

        # 4. API summary
        sections.append(self._section_api())

        # 5. Module summary
        sections.append(self._section_modules())

        # 6. Security status
        sections.append(self._section_security())

        # 7. Current state
        sections.append(self._section_current_state())

        # 8. Known issues & tasks (from .aios/ if available)
        sections.append(self._section_tasks_and_bugs())

        # 9. Technical decisions
        sections.append(self._section_decisions())

        # 10. Project health
        sections.append(self._section_health())

        # Assemble and trim
        header = [
            "# AI Project Context",
            "",
            f"> **Compressed context for AI consumption** — Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "> Read this file FIRST before making any changes to the project.",
            "",
        ]

        content = "\n".join(header)

        # Add sections, tracking budget
        for section in sections:
            if not section.strip():
                continue
            candidate = content + "\n" + section
            if len(candidate) <= self.max_chars:
                content = candidate
            else:
                # Truncate section to fit
                remaining = self.max_chars - len(content) - 100
                if remaining > 200:
                    truncated = section[:remaining] + "\n\n*[Section truncated for token budget]*\n"
                    content += "\n" + truncated
                break

        content += f"\n---\n*Context budget: ~{len(content) // 4:,} tokens / {self.max_chars // 4:,} max*\n"
        return content

    def _section_project_summary(self) -> str:
        generic = self.data.get("generic", {})
        git = self.data.get("git", {})
        infra = self.data.get("infrastructure", {})

        frameworks = set()
        for key in ["python", "javascript"]:
            if key in self.data:
                frameworks.update(self.data[key].get("frameworks", []))

        pkg_name = ""
        for pm in infra.get("package_managers", []):
            if pm.get("name"):
                pkg_name = pm["name"]
                break

        return "\n".join([
            "## Project Summary",
            "",
            f"- **Name**: {pkg_name or 'Unnamed'}",
            f"- **Language**: {generic.get('primary_language', '?')}",
            f"- **Frameworks**: {', '.join(sorted(frameworks)) or 'None'}",
            f"- **Files**: {generic.get('total_source_files', 0):,} | **LOC**: {generic.get('total_loc', 0):,}",
            f"- **Commits**: {git.get('total_commits', 0):,} | **Contributors**: {len(git.get('contributors', []))}",
            f"- **Branch**: {git.get('current_branch', '?')}",
            "",
        ])

    def _section_architecture(self) -> str:
        generic = self.data.get("generic", {})
        infra = self.data.get("infrastructure", {})

        # Top-level dirs
        dirs = generic.get("directory_tree", [])
        top = [d for d in dirs if d != "/" and d.count("/") == 0]

        lines = [
            "## Architecture",
            "",
            f"**Structure**: {' | '.join(sorted(top)[:15])}",
        ]

        # Entry points
        entry_points = []
        for key in ["python", "javascript"]:
            if key in self.data:
                entry_points.extend(self.data[key].get("entry_points", []))
        if entry_points:
            lines.append(f"**Entry Points**: {', '.join(f'`{e}`' for e in entry_points[:5])}")

        # Docker
        docker = infra.get("docker", {})
        if docker:
            services = docker.get("services", [])
            lines.append(f"**Docker**: base=`{docker.get('base_image', '?')}` services=[{', '.join(services)}]")

        # CI/CD
        cicd = infra.get("cicd_pipelines", [])
        if cicd:
            lines.append(f"**CI/CD**: {', '.join(c.get('provider', '?') for c in cicd)}")

        lines.append("")
        return "\n".join(lines)

    def _section_database(self) -> str:
        db = self.data.get("database", {})
        if not db.get("tables") and not db.get("models"):
            return ""

        lines = [
            "## Database",
            "",
            f"**Tech**: {', '.join(db.get('db_technologies', ['?']))} | "
            f"**Tables**: {db.get('total_tables', 0)} | "
            f"**Models**: {db.get('total_models', 0)} | "
            f"**Migrations**: {db.get('total_migrations', 0)}",
            "",
        ]

        # Compact model list
        models = db.get("models", []) or db.get("tables", [])
        if models:
            lines.append("**Models**: " + ", ".join(f"`{m['name']}`" for m in models[:20]))
            if len(models) > 20:
                lines.append(f"  *...and {len(models) - 20} more*")

        # Key relationships
        rels = db.get("relationships", [])
        if rels:
            lines.append(f"**Relationships**: " + " | ".join(
                f"{r['from_table']}.{r['from_column']}→{r['to_table']}" for r in rels[:10]
            ))

        lines.append("")
        return "\n".join(lines)

    def _section_api(self) -> str:
        api = self.data.get("api", {})
        if not api.get("endpoints"):
            return ""

        lines = [
            "## API Endpoints",
            "",
            f"**Total**: {api.get('total_endpoints', 0)} | "
            f"**Versions**: {', '.join(api.get('api_versions', ['?']))}",
            "",
        ]

        # Compact endpoint list
        endpoints = api.get("endpoints", [])
        for ep in endpoints[:25]:
            lines.append(f"- `{ep.get('method', '?')} {ep.get('path', '?')}` → `{ep.get('function', '?')}` ({ep.get('file', '')})")

        if len(endpoints) > 25:
            lines.append(f"  *...and {len(endpoints) - 25} more endpoints*")

        # Auth endpoints
        auth = api.get("auth_endpoints", [])
        if auth:
            lines.append(f"\n**Auth Endpoints**: " + ", ".join(f"`{e.get('path', '?')}`" for e in auth[:5]))

        lines.append("")
        return "\n".join(lines)

    def _section_modules(self) -> str:
        lines = ["## Key Modules", ""]

        # Python classes
        py = self.data.get("python", {})
        if py.get("classes"):
            classes = py["classes"][:15]
            lines.append("**Python Classes**: " + ", ".join(
                f"`{c['name']}` ({c['file']})" for c in classes
            ))
            if py.get("total_classes", 0) > 15:
                lines.append(f"  *...and {py['total_classes'] - 15} more classes*")

        # JS components
        js = self.data.get("javascript", {})
        if js.get("components"):
            comps = js["components"][:15]
            lines.append("**Components**: " + ", ".join(
                f"`{c['name']}`" for c in comps
            ))
            if js.get("total_components", 0) > 15:
                lines.append(f"  *...and {js['total_components'] - 15} more components*")

        if len(lines) <= 2:
            return ""

        lines.append("")
        return "\n".join(lines)

    def _section_security(self) -> str:
        sec = self.data.get("security", {})
        if not sec:
            return ""

        features = sec.get("security_features", {})
        present = [k for k, v in features.items() if v]
        missing = [k for k, v in features.items() if not v]

        lines = [
            "## Security Status",
            "",
            f"**Score**: {sec.get('security_score', 0)}/100 ({sec.get('severity', '?')})",
            f"**Present**: {', '.join(present) or 'None'}",
            f"**Missing**: {', '.join(missing) or 'None'}",
        ]

        if sec.get("total_secrets_found", 0) > 0:
            lines.append(f"**⚠️ SECRETS FOUND**: {sec['total_secrets_found']} hardcoded secrets detected!")
        if sec.get("total_sql_injection_risks", 0) > 0:
            lines.append(f"**⚠️ SQL INJECTION**: {sec['total_sql_injection_risks']} potential vulnerabilities")

        lines.append("")
        return "\n".join(lines)

    def _section_current_state(self) -> str:
        git = self.data.get("git", {})
        if not git.get("git_initialized"):
            return ""

        lines = [
            "## Current State",
            "",
            f"**Branch**: {git.get('current_branch', '?')} | "
            f"**Last Commit**: {git.get('last_commit_date', '?')[:10]}",
        ]

        # Recent commits (compact)
        recent = git.get("recent_commits", [])[:5]
        if recent:
            lines.append("**Recent Changes**:")
            for c in recent:
                lines.append(f"- `{c['hash']}` {c['message'][:60]} ({c['author']}, {c['date'][:10]})")

        # Uncommitted
        changes = git.get("uncommitted_changes", {})
        total_uncommitted = sum(len(changes.get(k, [])) for k in ["staged", "unstaged", "untracked"])
        if total_uncommitted:
            lines.append(f"**Uncommitted**: {total_uncommitted} files")

        lines.append("")
        return "\n".join(lines)

    def _section_tasks_and_bugs(self) -> str:
        """Placeholder — filled from TASKS.md and BUGS.md if they exist."""
        return "\n".join([
            "## Open Tasks & Known Issues",
            "",
            "*See TASKS.md and BUGS.md for current items.*",
            "",
        ])

    def _section_decisions(self) -> str:
        """Placeholder — filled from DECISIONS.md if it exists."""
        return "\n".join([
            "## Technical Decisions",
            "",
            "*See DECISIONS.md for past architectural and technical decisions.*",
            "",
        ])

    def _section_health(self) -> str:
        """Compact health summary."""
        security = self.data.get("security", {})
        generic = self.data.get("generic", {})
        infra = self.data.get("infrastructure", {})

        return "\n".join([
            "## Project Health",
            "",
            f"- Security: {security.get('security_score', 0)}/100",
            f"- Tests: {'✅' if generic.get('has_tests') else '❌'}",
            f"- Docs: {'✅' if generic.get('has_readme') else '❌'}",
            f"- CI/CD: {'✅' if infra.get('has_cicd') else '❌'}",
            f"- Docker: {'✅' if infra.get('has_docker') else '❌'}",
            "",
        ])
