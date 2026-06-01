"""
Python source code analyzer using the AST module.
Extracts classes, functions, imports, decorators, routes, and framework patterns.
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseAnalyzer


class PythonAnalyzer(BaseAnalyzer):
    """Analyzes Python source files using AST parsing."""

    @property
    def name(self) -> str:
        return "Python Analyzer"

    def analyze(self) -> Dict[str, Any]:
        py_files = self.walk_files(extensions={".py"})
        if not py_files:
            return {}

        classes: List[Dict[str, Any]] = []
        functions: List[Dict[str, Any]] = []
        imports: Dict[str, int] = {}
        decorators: Dict[str, int] = {}
        routes: List[Dict[str, Any]] = []
        models: List[Dict[str, Any]] = []
        total_loc = 0
        frameworks_detected: List[str] = []
        entry_points: List[str] = []
        test_files: List[str] = []
        config_files: List[str] = []

        framework_indicators = {
            "flask": ["flask", "Flask"],
            "django": ["django", "Django"],
            "fastapi": ["fastapi", "FastAPI"],
            "sqlalchemy": ["sqlalchemy", "SQLAlchemy"],
            "celery": ["celery", "Celery"],
            "pytest": ["pytest"],
            "tornado": ["tornado"],
            "aiohttp": ["aiohttp"],
            "starlette": ["starlette"],
            "pydantic": ["pydantic", "BaseModel"],
        }

        all_imports: set = set()

        for fpath in py_files:
            content = self.read_file(fpath)
            if content is None:
                continue

            rel = self.get_relative_path(fpath)
            total_loc += self.count_lines(content)

            # Detect test files
            if "test" in fpath.name.lower() or "test" in str(fpath.parent).lower():
                test_files.append(rel)

            # Detect config files
            if fpath.name in {"settings.py", "config.py", "conf.py", "wsgi.py", "asgi.py", "manage.py"}:
                config_files.append(rel)

            # Detect entry points
            if fpath.name in {"main.py", "app.py", "run.py", "server.py", "manage.py", "wsgi.py", "asgi.py"}:
                entry_points.append(rel)

            # AST parse
            try:
                tree = ast.parse(content, filename=str(fpath))
            except SyntaxError:
                continue

            self._extract_from_ast(tree, rel, classes, functions, imports,
                                   decorators, routes, models, all_imports)

        # Detect frameworks from imports
        for framework, indicators in framework_indicators.items():
            for imp in all_imports:
                if any(ind in imp for ind in indicators):
                    if framework not in frameworks_detected:
                        frameworks_detected.append(framework)
                    break

        # Top imports
        top_imports = sorted(imports.items(), key=lambda x: -x[1])[:30]

        self.results = {
            "language": "Python",
            "total_files": len(py_files),
            "total_loc": total_loc,
            "classes": classes[:100],  # Cap for large projects
            "functions": functions[:200],
            "top_imports": top_imports,
            "top_decorators": sorted(decorators.items(), key=lambda x: -x[1])[:20],
            "routes": routes,
            "models": models,
            "frameworks": frameworks_detected,
            "entry_points": entry_points,
            "test_files": test_files[:50],
            "config_files": config_files,
            "total_classes": len(classes),
            "total_functions": len(functions),
            "total_test_files": len(test_files),
        }
        return self.results

    def _extract_from_ast(
        self,
        tree: ast.AST,
        rel_path: str,
        classes: list,
        functions: list,
        imports: dict,
        decorators: dict,
        routes: list,
        models: list,
        all_imports: set,
    ):
        """Walk AST nodes and extract structured data."""
        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    imports[name] = imports.get(name, 0) + 1
                    all_imports.add(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    name = node.module.split(".")[0]
                    imports[name] = imports.get(name, 0) + 1
                    all_imports.add(node.module)

            # Classes
            elif isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(ast.dump(base))

                methods = [
                    n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]

                class_info = {
                    "name": node.name,
                    "file": rel_path,
                    "line": node.lineno,
                    "bases": bases,
                    "methods": methods[:20],
                    "method_count": len(methods),
                }

                # Check for model patterns
                model_bases = {"Model", "Base", "BaseModel", "Document", "Table"}
                if any(b in model_bases for b in bases):
                    models.append(class_info)

                # Class decorators
                for dec in node.decorator_list:
                    dec_name = self._get_decorator_name(dec)
                    if dec_name:
                        decorators[dec_name] = decorators.get(dec_name, 0) + 1

                classes.append(class_info)

            # Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip methods (already counted in classes)
                # We still record top-level functions
                args = []
                for arg in node.args.args:
                    if arg.arg != "self" and arg.arg != "cls":
                        args.append(arg.arg)

                func_info = {
                    "name": node.name,
                    "file": rel_path,
                    "line": node.lineno,
                    "args": args[:10],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }

                # Check for route decorators
                for dec in node.decorator_list:
                    dec_name = self._get_decorator_name(dec)
                    if dec_name:
                        decorators[dec_name] = decorators.get(dec_name, 0) + 1

                        # Detect Flask/FastAPI routes
                        route_info = self._extract_route(dec, node, rel_path)
                        if route_info:
                            routes.append(route_info)

                functions.append(func_info)

    def _get_decorator_name(self, node: ast.expr) -> Optional[str]:
        """Extract decorator name string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_decorator_name(node.value)}.{node.attr}" if node.value else node.attr
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return None

    def _extract_route(self, dec: ast.expr, func: ast.FunctionDef, rel_path: str) -> Optional[Dict]:
        """Extract route info from decorator like @app.route('/path')."""
        dec_name = self._get_decorator_name(dec)
        if not dec_name:
            return None

        route_patterns = {
            "app.route", "app.get", "app.post", "app.put", "app.delete", "app.patch",
            "router.get", "router.post", "router.put", "router.delete", "router.patch",
            "bp.route", "blueprint.route",
        }

        if not any(dec_name.endswith(p.split(".")[-1]) for p in route_patterns):
            return None

        # Try to extract path from args
        path = "/"
        method = "GET"
        if isinstance(dec, ast.Call) and dec.args:
            if isinstance(dec.args[0], ast.Constant):
                path = str(dec.args[0].value)

        # Infer method from decorator name
        method_map = {"get": "GET", "post": "POST", "put": "PUT", "delete": "DELETE", "patch": "PATCH"}
        for m, v in method_map.items():
            if dec_name.lower().endswith(m):
                method = v
                break

        return {
            "path": path,
            "method": method,
            "function": func.name,
            "file": rel_path,
            "line": func.lineno,
        }
