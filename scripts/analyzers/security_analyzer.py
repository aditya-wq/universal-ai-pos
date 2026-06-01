"""
Security analyzer.
Detects hardcoded secrets, auth patterns, dependency risks, and security misconfigurations.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from .base import BaseAnalyzer


# Patterns for detecting hardcoded secrets
SECRET_PATTERNS: List[Tuple[str, str]] = [
    (r"""(?:password|passwd|pwd)\s*[:=]\s*['"][^'"]{4,}['"]""", "Hardcoded password"),
    (r"""(?:api[_-]?key|apikey)\s*[:=]\s*['"][^'"]{8,}['"]""", "Hardcoded API key"),
    (r"""(?:secret[_-]?key|secretkey)\s*[:=]\s*['"][^'"]{8,}['"]""", "Hardcoded secret key"),
    (r"""(?:access[_-]?token|auth[_-]?token)\s*[:=]\s*['"][^'"]{8,}['"]""", "Hardcoded access token"),
    (r"""AKIA[0-9A-Z]{16}""", "AWS Access Key ID"),
    (r"""(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}""", "GitHub token"),
    (r"""sk-[A-Za-z0-9]{20,}""", "OpenAI/Stripe secret key"),
    (r"""-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----""", "Private key in source"),
    (r"""(?:jdbc|mongodb|mysql|postgres|redis)://[^\s'"]+""", "Database connection string"),
    (r"""Bearer\s+[A-Za-z0-9\-_.~+/]+=*""", "Hardcoded Bearer token"),
    (r"""(?:slack|xoxb|xoxp|xoxa|xoxr)-[A-Za-z0-9-]+""", "Slack token"),
    (r"""(?:SG\.)[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}""", "SendGrid API key"),
    (r"""(?:sk_live|pk_live|sk_test|pk_test)_[A-Za-z0-9]+""", "Stripe key"),
]

# Files that should NOT contain secrets
SENSITIVE_FILE_PATTERNS = [
    r"\.env(?:\.(?:local|development|production|staging|test))?$",
    r"config.*\.(py|js|ts|json|yaml|yml)$",
    r"settings.*\.(py|js|ts|json|yaml|yml)$",
]


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzes security configurations, vulnerabilities, and best practices."""

    @property
    def name(self) -> str:
        return "Security Analyzer"

    def analyze(self) -> Dict[str, Any]:
        secrets_found: List[Dict[str, Any]] = []
        auth_patterns: List[Dict[str, str]] = []
        security_headers: List[Dict[str, str]] = []
        cors_configs: List[Dict[str, str]] = []
        encryption_usage: List[Dict[str, str]] = []
        rbac_patterns: List[Dict[str, str]] = []
        audit_logging: List[Dict[str, str]] = []
        input_validation: List[Dict[str, str]] = []
        sql_injection_risks: List[Dict[str, str]] = []
        xss_risks: List[Dict[str, str]] = []
        dependency_risks: List[Dict[str, str]] = []
        missing_security: List[str] = []
        security_score = 100  # Start at 100, deduct for issues

        all_files = self.walk_files(
            exclude_patterns=[r"\.min\.", r"test", r"spec", r"mock", r"fixture"]
        )

        # Track what security features exist
        has_auth = False
        has_rbac = False
        has_encryption = False
        has_audit = False
        has_rate_limiting = False
        has_input_validation = False
        has_csrf_protection = False
        has_security_headers = False
        has_https_enforcement = False

        for fpath in all_files:
            content = self.read_file(fpath)
            if not content:
                continue
            rel = self.get_relative_path(fpath)

            # 1. Secret detection
            for pattern, description in SECRET_PATTERNS:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    # Skip if in a comment or test
                    line_start = content.rfind("\n", 0, match.start()) + 1
                    line = content[line_start:content.find("\n", match.start())].strip()
                    if line.startswith("#") or line.startswith("//") or line.startswith("*"):
                        continue
                    # Skip example/placeholder values
                    value = match.group(0)
                    if any(p in value.lower() for p in ["example", "placeholder", "your_", "xxx", "changeme", "<", "{{", "${}"]):
                        continue

                    secrets_found.append({
                        "type": description,
                        "file": rel,
                        "line_preview": line[:80] + "..." if len(line) > 80 else line,
                    })
                    security_score -= 5

            # 2. Authentication patterns
            auth_keywords = [
                (r"(?:jwt|jsonwebtoken|jose)", "JWT"),
                (r"(?:passport|auth0|okta|firebase\.auth|cognito)", "Auth Provider"),
                (r"(?:bcrypt|argon2|scrypt|pbkdf2)", "Password Hashing"),
                (r"(?:oauth|openid|oidc|saml)", "OAuth/OIDC"),
                (r"(?:mfa|two.?factor|totp|2fa)", "MFA/2FA"),
                (r"(?:session|cookie.*secure|httponly)", "Session Security"),
            ]
            for pattern, auth_type in auth_keywords:
                if re.search(pattern, content, re.IGNORECASE):
                    has_auth = True
                    auth_patterns.append({"type": auth_type, "file": rel})

            # 3. RBAC patterns
            rbac_keywords = [
                r"(?:role|permission|authorize|can|ability|policy)",
                r"(?:admin|moderator|editor|viewer|owner)",
                r"(?:@Roles|@Permissions|@Authorize|hasRole|hasPermission)",
            ]
            for pattern in rbac_keywords:
                if re.search(pattern, content, re.IGNORECASE):
                    has_rbac = True
                    rbac_patterns.append({"pattern": pattern, "file": rel})
                    break

            # 4. Encryption
            enc_keywords = [
                r"(?:AES|RSA|crypto|encrypt|decrypt|cipher)",
                r"(?:hashlib|hmac|sha256|sha512|md5)",
                r"(?:ssl|tls|https)",
            ]
            for pattern in enc_keywords:
                if re.search(pattern, content, re.IGNORECASE):
                    has_encryption = True
                    encryption_usage.append({"pattern": pattern, "file": rel})
                    break

            # 5. Audit logging
            if re.search(r"(?:audit|log\.(?:info|warn|error)|logger|winston|bunyan|pino|logging\.getLogger)", content, re.IGNORECASE):
                has_audit = True
                audit_logging.append({"file": rel})

            # 6. Rate limiting
            if re.search(r"(?:rate.?limit|throttle|express.?rate|slowapi|django.?ratelimit)", content, re.IGNORECASE):
                has_rate_limiting = True

            # 7. Input validation
            if re.search(r"(?:validate|sanitize|escape|joi|yup|zod|cerberus|marshmallow|pydantic)", content, re.IGNORECASE):
                has_input_validation = True
                input_validation.append({"file": rel})

            # 8. CSRF protection
            if re.search(r"(?:csrf|xsrf|csurf|csrftoken)", content, re.IGNORECASE):
                has_csrf_protection = True

            # 9. Security headers
            if re.search(r"(?:helmet|Content-Security-Policy|X-Frame-Options|X-XSS-Protection|Strict-Transport-Security)", content, re.IGNORECASE):
                has_security_headers = True
                security_headers.append({"file": rel})

            # 10. CORS configuration
            if re.search(r"(?:cors|Access-Control-Allow|crossorigin)", content, re.IGNORECASE):
                cors_match = re.search(r"(?:origin|Access-Control-Allow-Origin)\s*[:=]\s*['\"]?\*['\"]?", content)
                if cors_match:
                    cors_configs.append({"file": rel, "issue": "Wildcard CORS origin (*)"})
                    security_score -= 3

            # 11. SQL injection risks
            if re.search(r"""(?:execute|query|raw)\s*\(\s*(?:f['\"]|['"].*%s|['"].*\+\s*\w+|['"].*\{)""", content):
                sql_injection_risks.append({"file": rel})
                security_score -= 5

            # 12. XSS risks (innerHTML, dangerouslySetInnerHTML)
            if re.search(r"(?:innerHTML|dangerouslySetInnerHTML|v-html|__html)", content):
                xss_risks.append({"file": rel})
                security_score -= 3

            # 13. HTTPS enforcement
            if re.search(r"(?:https|ssl|tls|SECURE_SSL_REDIRECT|force_ssl|requireSSL)", content, re.IGNORECASE):
                has_https_enforcement = True

        # Check for missing security features
        if not has_auth:
            missing_security.append("No authentication system detected")
            security_score -= 10
        if not has_rbac:
            missing_security.append("No RBAC/authorization system detected")
            security_score -= 8
        if not has_encryption:
            missing_security.append("No encryption usage detected")
            security_score -= 5
        if not has_audit:
            missing_security.append("No audit logging detected")
            security_score -= 5
        if not has_rate_limiting:
            missing_security.append("No rate limiting detected")
            security_score -= 5
        if not has_input_validation:
            missing_security.append("No input validation library detected")
            security_score -= 5
        if not has_csrf_protection:
            missing_security.append("No CSRF protection detected")
            security_score -= 5
        if not has_security_headers:
            missing_security.append("No security headers configured")
            security_score -= 5
        if not has_https_enforcement:
            missing_security.append("No HTTPS enforcement detected")
            security_score -= 3

        # Check .gitignore for sensitive files
        gitignore_path = self.project_dir / ".gitignore"
        if gitignore_path.exists():
            gitignore_content = self.read_file(gitignore_path) or ""
            if ".env" not in gitignore_content:
                missing_security.append(".env not in .gitignore")
                security_score -= 5
        else:
            missing_security.append("No .gitignore file found")
            security_score -= 3

        # Clamp score
        security_score = max(0, min(100, security_score))

        # Determine severity
        if security_score >= 80:
            severity = "LOW"
        elif security_score >= 60:
            severity = "MEDIUM"
        elif security_score >= 40:
            severity = "HIGH"
        else:
            severity = "CRITICAL"

        self.results = {
            "security_score": security_score,
            "severity": severity,
            "secrets_found": secrets_found[:50],
            "auth_patterns": auth_patterns[:20],
            "security_headers": security_headers[:10],
            "cors_issues": cors_configs,
            "encryption_usage": encryption_usage[:20],
            "rbac_patterns": rbac_patterns[:20],
            "audit_logging": audit_logging[:20],
            "input_validation": input_validation[:20],
            "sql_injection_risks": sql_injection_risks[:20],
            "xss_risks": xss_risks[:20],
            "dependency_risks": dependency_risks,
            "missing_security_features": missing_security,
            "security_features": {
                "authentication": has_auth,
                "authorization_rbac": has_rbac,
                "encryption": has_encryption,
                "audit_logging": has_audit,
                "rate_limiting": has_rate_limiting,
                "input_validation": has_input_validation,
                "csrf_protection": has_csrf_protection,
                "security_headers": has_security_headers,
                "https_enforcement": has_https_enforcement,
            },
            "total_secrets_found": len(secrets_found),
            "total_sql_injection_risks": len(sql_injection_risks),
            "total_xss_risks": len(xss_risks),
        }
        return self.results
