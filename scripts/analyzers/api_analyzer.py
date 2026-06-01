"""
API analyzer.
Detects REST endpoints, GraphQL schemas, OpenAPI/Swagger specs, and API patterns.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAnalyzer


class ApiAnalyzer(BaseAnalyzer):
    """Analyzes API definitions, endpoints, and documentation."""

    @property
    def name(self) -> str:
        return "API Analyzer"

    def analyze(self) -> Dict[str, Any]:
        endpoints: List[Dict[str, Any]] = []
        graphql_types: List[Dict[str, Any]] = []
        openapi_specs: List[str] = []
        middleware: List[Dict[str, str]] = []
        auth_endpoints: List[Dict[str, Any]] = []
        api_versions: List[str] = []
        websocket_endpoints: List[Dict[str, str]] = []

        all_files = self.walk_files()

        for fpath in all_files:
            rel = self.get_relative_path(fpath)
            content = self.read_file(fpath)
            if not content:
                continue

            # OpenAPI / Swagger spec detection
            if fpath.name in {"openapi.json", "openapi.yaml", "openapi.yml",
                              "swagger.json", "swagger.yaml", "swagger.yml"}:
                openapi_specs.append(rel)
                self._parse_openapi(content, fpath, endpoints)
                continue

            # GraphQL schema detection
            if fpath.suffix in {".graphql", ".gql"}:
                self._parse_graphql(content, rel, graphql_types)
                continue

            # Python API routes (Flask, FastAPI, Django REST)
            if fpath.suffix == ".py":
                self._extract_python_apis(content, rel, endpoints, middleware, auth_endpoints)

            # JavaScript API routes (Express, Koa, Hapi, Next.js API routes)
            elif fpath.suffix in {".js", ".ts", ".mjs"}:
                self._extract_js_apis(content, rel, endpoints, middleware, auth_endpoints, websocket_endpoints)

            # Java API (Spring Boot)
            elif fpath.suffix == ".java":
                self._extract_java_apis(content, rel, endpoints)

            # C# API (ASP.NET)
            elif fpath.suffix == ".cs":
                self._extract_csharp_apis(content, rel, endpoints)

            # Go API (Gin, Echo, Mux)
            elif fpath.suffix == ".go":
                self._extract_go_apis(content, rel, endpoints)

        # Detect API versions
        for ep in endpoints:
            path = ep.get("path", "")
            match = re.search(r"/v(\d+)/", path)
            if match:
                ver = f"v{match.group(1)}"
                if ver not in api_versions:
                    api_versions.append(ver)

        # Categorize auth endpoints
        auth_keywords = {"login", "logout", "register", "signup", "signin", "auth",
                         "token", "refresh", "password", "reset", "verify", "oauth"}
        for ep in endpoints:
            func = ep.get("function", "").lower()
            path = ep.get("path", "").lower()
            if any(k in func or k in path for k in auth_keywords):
                if ep not in auth_endpoints:
                    auth_endpoints.append(ep)

        self.results = {
            "endpoints": endpoints[:200],
            "graphql_types": graphql_types[:100],
            "openapi_specs": openapi_specs,
            "middleware": middleware[:50],
            "auth_endpoints": auth_endpoints[:30],
            "api_versions": api_versions,
            "websocket_endpoints": websocket_endpoints,
            "total_endpoints": len(endpoints),
            "total_graphql_types": len(graphql_types),
        }
        return self.results

    def _parse_openapi(self, content: str, fpath: Path, endpoints: list):
        """Parse OpenAPI/Swagger JSON spec."""
        if fpath.suffix == ".json":
            try:
                spec = json.loads(content)
                paths = spec.get("paths", {})
                for path, methods in paths.items():
                    for method, details in methods.items():
                        if method in {"get", "post", "put", "delete", "patch", "options", "head"}:
                            endpoints.append({
                                "path": path,
                                "method": method.upper(),
                                "summary": details.get("summary", ""),
                                "file": self.get_relative_path(fpath),
                                "source": "openapi",
                            })
            except json.JSONDecodeError:
                pass

    def _parse_graphql(self, content: str, rel: str, graphql_types: list):
        """Parse GraphQL schema definitions."""
        for match in re.finditer(r"type\s+(\w+)\s*(?:implements\s+[\w\s&]+)?\{([^}]+)\}", content):
            type_name = match.group(1)
            body = match.group(2)
            fields = []
            for field_match in re.finditer(r"(\w+)\s*(?:\([^)]*\))?\s*:\s*([^\n!]+!?)", body):
                fields.append({"name": field_match.group(1), "type": field_match.group(2).strip()})
            graphql_types.append({
                "name": type_name,
                "fields": fields[:20],
                "file": rel,
            })

        # Queries and Mutations
        for match in re.finditer(r"(type\s+(?:Query|Mutation))\s*\{([^}]+)\}", content):
            type_name = match.group(1)
            body = match.group(2)
            for field_match in re.finditer(r"(\w+)\s*(?:\([^)]*\))?\s*:\s*([^\n!]+!?)", body):
                graphql_types.append({
                    "name": f"{type_name.split()[-1]}.{field_match.group(1)}",
                    "return_type": field_match.group(2).strip(),
                    "file": rel,
                })

    def _extract_python_apis(self, content: str, rel: str, endpoints: list,
                              middleware: list, auth_endpoints: list):
        """Extract Python framework API routes."""
        # Flask / FastAPI route decorators
        for match in re.finditer(
            r"@(?:app|router|bp|blueprint|api)\.(?:route|get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
            content
        ):
            path = match.group(1)
            # Find function name after decorator
            func_match = re.search(r"def\s+(\w+)", content[match.end():match.end() + 200])
            endpoints.append({
                "path": path,
                "method": self._infer_method(content[match.start():match.end()]),
                "function": func_match.group(1) if func_match else "unknown",
                "file": rel,
                "source": "python",
            })

        # Django URL patterns
        for match in re.finditer(
            r"path\s*\(\s*['\"]([^'\"]*)['\"].*?(?:views?\.)?(\w+)",
            content
        ):
            endpoints.append({
                "path": f"/{match.group(1)}",
                "method": "ANY",
                "function": match.group(2),
                "file": rel,
                "source": "django",
            })

    def _extract_js_apis(self, content: str, rel: str, endpoints: list,
                          middleware: list, auth_endpoints: list,
                          websocket_endpoints: list):
        """Extract JavaScript framework API routes."""
        # Express-style routes
        for match in re.finditer(
            r"(?:app|router)\.(get|post|put|delete|patch|all|use)\s*\(\s*['\"]([^'\"]+)['\"]",
            content
        ):
            method = match.group(1).upper()
            path = match.group(2)
            if method == "USE":
                middleware.append({"path": path, "file": rel})
            else:
                endpoints.append({
                    "path": path,
                    "method": method if method != "ALL" else "ANY",
                    "file": rel,
                    "source": "express",
                })

        # Next.js API route (file-based)
        if "/api/" in rel or "\\api\\" in rel:
            for match in re.finditer(
                r"export\s+(?:default\s+)?(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|handler)",
                content
            ):
                endpoints.append({
                    "path": "/" + rel.replace("\\", "/"),
                    "method": match.group(1) if match.group(1) != "handler" else "ANY",
                    "file": rel,
                    "source": "nextjs",
                })

        # WebSocket
        for match in re.finditer(r"(?:ws|wss|WebSocket|socket\.io)\s*\(\s*['\"]([^'\"]+)['\"]", content):
            websocket_endpoints.append({"path": match.group(1), "file": rel})

    def _extract_java_apis(self, content: str, rel: str, endpoints: list):
        """Extract Spring Boot API endpoints."""
        for match in re.finditer(
            r"@(?:Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*(?:value\s*=\s*)?['\"]([^'\"]+)['\"]",
            content
        ):
            method = "GET"
            anno = content[match.start():match.start() + 30]
            for m in ["Post", "Put", "Delete", "Patch"]:
                if m in anno:
                    method = m.upper()
                    break
            endpoints.append({
                "path": match.group(1),
                "method": method,
                "file": rel,
                "source": "spring",
            })

    def _extract_csharp_apis(self, content: str, rel: str, endpoints: list):
        """Extract ASP.NET API endpoints."""
        for match in re.finditer(
            r"\[Http(Get|Post|Put|Delete|Patch)\s*(?:\(\s*\"([^\"]*)\"\s*\))?\]",
            content
        ):
            endpoints.append({
                "path": match.group(2) or "/",
                "method": match.group(1).upper(),
                "file": rel,
                "source": "aspnet",
            })

    def _extract_go_apis(self, content: str, rel: str, endpoints: list):
        """Extract Go API endpoints (Gin, Echo, Mux)."""
        for match in re.finditer(
            r"(?:r|router|e|g|group)\.(GET|POST|PUT|DELETE|PATCH|Handle|HandleFunc)\s*\(\s*\"([^\"]+)\"",
            content, re.IGNORECASE
        ):
            endpoints.append({
                "path": match.group(2),
                "method": match.group(1).upper() if match.group(1).upper() in {"GET", "POST", "PUT", "DELETE", "PATCH"} else "ANY",
                "file": rel,
                "source": "go",
            })

    def _infer_method(self, decorator_text: str) -> str:
        """Infer HTTP method from decorator text."""
        text = decorator_text.lower()
        for m in ["post", "put", "delete", "patch"]:
            if m in text:
                return m.upper()
        if "route" in text:
            return "ANY"
        return "GET"
