"""
Infrastructure analyzer.
Detects Docker, CI/CD pipelines, environment variables, Kubernetes, and deployment configs.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAnalyzer


class InfrastructureAnalyzer(BaseAnalyzer):
    """Analyzes infrastructure, CI/CD, Docker, and deployment configurations."""

    @property
    def name(self) -> str:
        return "Infrastructure Analyzer"

    def analyze(self) -> Dict[str, Any]:
        docker: Dict[str, Any] = {}
        cicd: List[Dict[str, Any]] = []
        env_vars: List[Dict[str, str]] = []
        kubernetes: List[Dict[str, Any]] = []
        cloud_services: List[str] = []
        package_managers: List[Dict[str, Any]] = []
        scripts: Dict[str, str] = {}

        all_files = self.walk_files()

        for fpath in all_files:
            rel = self.get_relative_path(fpath)
            fname = fpath.name.lower()

            # Docker
            if fname == "dockerfile" or fname.startswith("dockerfile."):
                content = self.read_file(fpath) or ""
                docker["dockerfile"] = rel
                docker["base_image"] = self._extract_docker_base(content)
                docker["stages"] = self._count_docker_stages(content)
                docker["exposed_ports"] = self._extract_docker_ports(content)

            elif fname in {"docker-compose.yml", "docker-compose.yaml",
                           "compose.yml", "compose.yaml"}:
                content = self.read_file(fpath) or ""
                docker["compose_file"] = rel
                docker["services"] = self._extract_compose_services(content)

            elif fname == ".dockerignore":
                docker["has_dockerignore"] = True

            # CI/CD Pipelines
            elif ".github/workflows" in rel and fpath.suffix in {".yml", ".yaml"}:
                content = self.read_file(fpath) or ""
                cicd.append({
                    "provider": "github_actions",
                    "file": rel,
                    "name": self._extract_yaml_name(content),
                    "triggers": self._extract_gh_triggers(content),
                })

            elif fname in {".gitlab-ci.yml", ".gitlab-ci.yaml"}:
                content = self.read_file(fpath) or ""
                cicd.append({
                    "provider": "gitlab_ci",
                    "file": rel,
                    "stages": self._extract_gitlab_stages(content),
                })

            elif fname in {"Jenkinsfile", "jenkinsfile"}:
                cicd.append({"provider": "jenkins", "file": rel})

            elif fname in {".circleci/config.yml", "circle.yml"} or ".circleci" in rel:
                cicd.append({"provider": "circleci", "file": rel})

            elif fname in {"azure-pipelines.yml", "azure-pipelines.yaml"}:
                cicd.append({"provider": "azure_devops", "file": rel})

            elif fname == "bitbucket-pipelines.yml":
                cicd.append({"provider": "bitbucket", "file": rel})

            elif fname in {"buildspec.yml", "buildspec.yaml"}:
                cicd.append({"provider": "aws_codebuild", "file": rel})
                if "aws" not in cloud_services:
                    cloud_services.append("aws")

            elif fname == "cloudbuild.yaml":
                cicd.append({"provider": "gcp_cloud_build", "file": rel})
                if "gcp" not in cloud_services:
                    cloud_services.append("gcp")

            # Environment variables
            elif fname in {".env", ".env.example", ".env.local", ".env.development",
                           ".env.production", ".env.staging", ".env.test"}:
                content = self.read_file(fpath) or ""
                for var in self._extract_env_vars(content):
                    var["file"] = rel
                    env_vars.append(var)

            # Kubernetes
            elif fpath.suffix in {".yml", ".yaml"} and any(
                k in rel.lower() for k in ["k8s", "kubernetes", "deploy", "helm"]
            ):
                content = self.read_file(fpath) or ""
                if "kind:" in content:
                    kubernetes.append({
                        "file": rel,
                        "kind": self._extract_k8s_kind(content),
                    })

            # Package managers
            elif fname == "package.json":
                content = self.read_file(fpath) or ""
                pkg = self._parse_package_json(content)
                if pkg:
                    pkg["file"] = rel
                    package_managers.append(pkg)
                    scripts.update(pkg.get("scripts", {}))

            elif fname in {"requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "Pipfile"}:
                package_managers.append({"type": "python", "file": rel})

            elif fname in {"Gemfile", "Gemfile.lock"}:
                package_managers.append({"type": "ruby", "file": rel})

            elif fname in {"Cargo.toml"}:
                package_managers.append({"type": "rust", "file": rel})

            elif fname in {"go.mod"}:
                package_managers.append({"type": "go", "file": rel})

            elif fname in {"pom.xml", "build.gradle", "build.gradle.kts"}:
                package_managers.append({"type": "java", "file": rel})

            elif fname in {"composer.json"}:
                package_managers.append({"type": "php", "file": rel})

            # Cloud service detection
            if fname in {"serverless.yml", "serverless.yaml"}:
                if "aws" not in cloud_services:
                    cloud_services.append("aws")
            elif fname in {"app.yaml", "app.yml"} and "gcp" not in cloud_services:
                content = self.read_file(fpath) or ""
                if "runtime:" in content:
                    cloud_services.append("gcp")
            elif fname == "fly.toml":
                if "fly.io" not in cloud_services:
                    cloud_services.append("fly.io")
            elif fname == "vercel.json":
                if "vercel" not in cloud_services:
                    cloud_services.append("vercel")
            elif fname == "netlify.toml":
                if "netlify" not in cloud_services:
                    cloud_services.append("netlify")

        # Detect Terraform
        tf_files = self.walk_files(extensions={".tf"})
        if tf_files:
            cloud_services.append("terraform")

        self.results = {
            "docker": docker,
            "cicd_pipelines": cicd,
            "environment_variables": env_vars[:100],
            "kubernetes": kubernetes,
            "cloud_services": cloud_services,
            "package_managers": package_managers,
            "npm_scripts": scripts,
            "has_docker": bool(docker),
            "has_cicd": bool(cicd),
            "has_kubernetes": bool(kubernetes),
        }
        return self.results

    def _extract_docker_base(self, content: str) -> str:
        match = re.search(r"FROM\s+(\S+)", content)
        return match.group(1) if match else "unknown"

    def _count_docker_stages(self, content: str) -> int:
        return len(re.findall(r"^FROM\s+", content, re.MULTILINE))

    def _extract_docker_ports(self, content: str) -> List[str]:
        return re.findall(r"EXPOSE\s+(\d+)", content)

    def _extract_compose_services(self, content: str) -> List[str]:
        services = []
        in_services = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "services:":
                in_services = True
                continue
            if in_services:
                if line and not line[0].isspace():
                    break
                if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
                    services.append(stripped[:-1])
        return services

    def _extract_yaml_name(self, content: str) -> str:
        match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
        return match.group(1).strip().strip("'\"") if match else "unnamed"

    def _extract_gh_triggers(self, content: str) -> List[str]:
        triggers = []
        for match in re.finditer(r"on:\s*\n((?:\s+.+\n)*)", content):
            block = match.group(1)
            for trigger in re.findall(r"^\s+(\w+):", block, re.MULTILINE):
                triggers.append(trigger)
        # Single-line on:
        match = re.search(r"on:\s*\[([^\]]+)\]", content)
        if match:
            triggers.extend([t.strip() for t in match.group(1).split(",")])
        return triggers

    def _extract_gitlab_stages(self, content: str) -> List[str]:
        match = re.search(r"stages:\s*\n((?:\s+-\s*.+\n)*)", content)
        if match:
            return re.findall(r"-\s*(\S+)", match.group(1))
        return []

    def _extract_env_vars(self, content: str) -> List[Dict[str, str]]:
        """Parse .env file for variable names (not values for security)."""
        vars_list = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                has_value = bool(line.split("=", 1)[1].strip())
                vars_list.append({
                    "name": key,
                    "has_value": str(has_value),
                })
        return vars_list

    def _extract_k8s_kind(self, content: str) -> str:
        match = re.search(r"kind:\s*(\w+)", content)
        return match.group(1) if match else "unknown"

    def _parse_package_json(self, content: str) -> Dict[str, Any]:
        try:
            pkg = json.loads(content)
            deps = list(pkg.get("dependencies", {}).keys())
            dev_deps = list(pkg.get("devDependencies", {}).keys())
            return {
                "type": "node",
                "name": pkg.get("name", "unnamed"),
                "version": pkg.get("version", "0.0.0"),
                "dependencies": deps,
                "dev_dependencies": dev_deps,
                "scripts": pkg.get("scripts", {}),
                "total_deps": len(deps) + len(dev_deps),
            }
        except json.JSONDecodeError:
            return {}
