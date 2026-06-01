"""
Agent generator — produces agent profile markdown files in AGENTS/.
"""

from datetime import datetime, timezone
from typing import Any, Dict


AGENT_PROFILES = {
    "architect": {
        "title": "Architect Agent",
        "emoji": "🏗️",
        "responsibilities": [
            "System architecture design and review",
            "Scalability planning and assessment",
            "Design pattern selection and enforcement",
            "Technical planning and roadmapping",
            "Technology stack decisions",
            "Component boundary definitions",
            "Performance architecture",
        ],
        "reads": ["ARCHITECTURE.md", "DECISIONS.md", "MODULES.md", "DEPENDENCIES.md"],
        "writes": ["ARCHITECTURE.md", "DECISIONS.md"],
        "rules": [
            "Always consult DECISIONS.md before proposing architectural changes",
            "Document all architectural decisions with rationale and alternatives",
            "Consider scalability implications for every design choice",
            "Prefer composition over inheritance",
            "Follow SOLID principles",
            "Minimize coupling between modules",
        ],
    },
    "frontend": {
        "title": "Frontend Agent",
        "emoji": "🎨",
        "responsibilities": [
            "UI component design and implementation",
            "UX flow optimization",
            "Accessibility (WCAG compliance)",
            "Responsive design",
            "State management",
            "Component library management",
            "Performance optimization (Core Web Vitals)",
        ],
        "reads": ["MODULES.md", "FEATURES.md", "ARCHITECTURE.md"],
        "writes": ["MODULES.md", "FEATURES.md"],
        "rules": [
            "Follow established component patterns in the project",
            "Ensure all interactive elements are accessible",
            "Use semantic HTML elements",
            "Maintain consistent design system tokens",
            "Optimize for Core Web Vitals (LCP, FID, CLS)",
            "Write unit tests for complex component logic",
        ],
    },
    "backend": {
        "title": "Backend Agent",
        "emoji": "⚙️",
        "responsibilities": [
            "API design and implementation",
            "Business logic implementation",
            "Service layer development",
            "Data validation and transformation",
            "Error handling and logging",
            "Integration with external services",
            "Background job processing",
        ],
        "reads": ["API.md", "ARCHITECTURE.md", "DATABASE.md", "SECURITY.md"],
        "writes": ["API.md", "MODULES.md"],
        "rules": [
            "Follow RESTful conventions for API design",
            "Validate all input at the API boundary",
            "Use proper HTTP status codes",
            "Implement proper error handling with meaningful messages",
            "Log all critical operations",
            "Never expose internal errors to clients",
            "Use dependency injection where possible",
        ],
    },
    "database": {
        "title": "Database Agent",
        "emoji": "🗄️",
        "responsibilities": [
            "Schema design and normalization",
            "Relationship modeling",
            "Index optimization",
            "Query performance analysis",
            "Migration management",
            "Data integrity constraints",
            "Backup and recovery strategies",
        ],
        "reads": ["DATABASE.md", "ARCHITECTURE.md"],
        "writes": ["DATABASE.md"],
        "rules": [
            "Always create migrations for schema changes",
            "Add indexes for frequently queried columns",
            "Use foreign key constraints for referential integrity",
            "Normalize to 3NF unless performance requires denormalization",
            "Document the reason for any denormalization",
            "Never store sensitive data in plain text",
            "Consider data volume growth in schema design",
        ],
    },
    "security": {
        "title": "Security Agent",
        "emoji": "🔒",
        "responsibilities": [
            "RBAC implementation and review",
            "MFA enforcement",
            "Encryption standards",
            "Audit logging",
            "Compliance verification",
            "Vulnerability assessment",
            "Secret management",
            "Dependency security review",
        ],
        "reads": ["SECURITY.md", "ROLES_PERMISSIONS.md", "API.md", "DATABASE.md"],
        "writes": ["SECURITY.md", "ROLES_PERMISSIONS.md"],
        "rules": [
            "Never store secrets in source code",
            "Always use parameterized queries",
            "Enforce HTTPS for all production traffic",
            "Implement rate limiting on all public endpoints",
            "Use bcrypt/argon2 for password hashing",
            "Set secure, httpOnly, sameSite flags on cookies",
            "Review OWASP Top 10 for every feature",
            "Log all authentication and authorization events",
        ],
    },
    "devops": {
        "title": "DevOps Agent",
        "emoji": "🚀",
        "responsibilities": [
            "CI/CD pipeline management",
            "Infrastructure as Code",
            "Container orchestration",
            "Monitoring and alerting",
            "Log aggregation",
            "Environment management",
            "Deployment strategies",
            "Resource optimization",
        ],
        "reads": ["ARCHITECTURE.md", "DEPENDENCIES.md", "SECURITY.md"],
        "writes": ["ARCHITECTURE.md"],
        "rules": [
            "Automate everything that can be automated",
            "Use immutable infrastructure patterns",
            "Implement health checks for all services",
            "Set up monitoring before deploying to production",
            "Use environment variables for configuration",
            "Never store secrets in CI/CD configuration files",
            "Implement rollback strategies for every deployment",
        ],
    },
    "qa": {
        "title": "QA Agent",
        "emoji": "🧪",
        "responsibilities": [
            "Test strategy and planning",
            "Unit test implementation",
            "Integration test design",
            "End-to-end test automation",
            "Regression analysis",
            "Performance testing",
            "Code coverage analysis",
        ],
        "reads": ["TESTS.md", "FEATURES.md", "BUGS.md", "API.md"],
        "writes": ["TESTS.md", "BUGS.md"],
        "rules": [
            "Write tests for all new features",
            "Maintain minimum 80% code coverage for critical paths",
            "Test both happy paths and error cases",
            "Use meaningful test descriptions",
            "Keep tests independent and idempotent",
            "Run regression tests before every release",
            "Document test data requirements",
        ],
    },
    "product": {
        "title": "Product Agent",
        "emoji": "📋",
        "responsibilities": [
            "Feature prioritization",
            "User story refinement",
            "Sprint planning support",
            "Roadmap management",
            "Stakeholder communication",
            "Requirements documentation",
            "Feature acceptance criteria",
        ],
        "reads": ["FEATURES.md", "ROADMAP.md", "TASKS.md", "BUGS.md", "TIMELINE.md"],
        "writes": ["FEATURES.md", "ROADMAP.md", "TASKS.md", "TIMELINE.md"],
        "rules": [
            "Prioritize based on user impact and effort",
            "Write clear acceptance criteria for every feature",
            "Keep the roadmap aligned with business goals",
            "Track feature dependencies",
            "Communicate breaking changes early",
            "Validate features against user feedback",
        ],
    },
}


class AgentGenerator:
    """Generates agent profile markdown files."""

    def __init__(self, scan_data: Dict[str, Any]):
        self.data = scan_data

    def generate_all(self) -> Dict[str, str]:
        """Generate all agent profiles. Returns {filename: content}."""
        result = {}
        for agent_id, profile in AGENT_PROFILES.items():
            result[f"{agent_id}.md"] = self._generate_agent(agent_id, profile)
        return result

    def _generate_agent(self, agent_id: str, profile: dict) -> str:
        """Generate a single agent profile markdown."""
        lines = [
            f"# {profile['emoji']} {profile['title']}",
            "",
            f"> Auto-generated by AIOS on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Responsibilities",
            "",
        ]
        for r in profile["responsibilities"]:
            lines.append(f"- {r}")

        lines.extend([
            "",
            "## Required Reading (Before Any Action)",
            "",
        ])
        for doc in profile["reads"]:
            lines.append(f"1. `.aios/{doc}`")

        lines.extend([
            "",
            "## Documents This Agent Updates",
            "",
        ])
        for doc in profile["writes"]:
            lines.append(f"- `.aios/{doc}`")

        lines.extend([
            "",
            "## Rules & Constraints",
            "",
        ])
        for rule in profile["rules"]:
            lines.append(f"- {rule}")

        lines.extend([
            "",
            "## Workflow",
            "",
            "1. Read all required documents listed above",
            "2. Understand current project state from `CURRENT_STATE.md`",
            "3. Check `DECISIONS.md` for relevant past decisions",
            "4. Perform the requested task within your area of responsibility",
            "5. Update relevant documents after implementation",
            "6. Log changes in `CHANGELOG.md`",
            "7. Report any risks or concerns",
            "",
            "---",
            f"*Agent profile for: {profile['title']}*",
            "",
        ])
        return "\n".join(lines)
