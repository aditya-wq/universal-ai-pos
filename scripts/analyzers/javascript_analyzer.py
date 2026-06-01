"""
JavaScript/TypeScript analyzer using regex-based pattern matching.
Extracts imports, exports, React components, routes, API endpoints.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from .base import BaseAnalyzer


class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyzes JavaScript and TypeScript source files using regex."""

    JS_EXTENSIONS: Set[str] = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

    @property
    def name(self) -> str:
        return "JavaScript/TypeScript Analyzer"

    def analyze(self) -> Dict[str, Any]:
        js_files = self.walk_files(extensions=self.JS_EXTENSIONS)
        if not js_files:
            return {}

        components: List[Dict[str, Any]] = []
        functions: List[Dict[str, Any]] = []
        classes: List[Dict[str, Any]] = []
        imports: Dict[str, int] = {}
        routes: List[Dict[str, Any]] = []
        api_calls: List[Dict[str, Any]] = []
        exports: List[Dict[str, Any]] = []
        total_loc = 0
        frameworks_detected: List[str] = []
        test_files: List[str] = []
        config_files: List[str] = []
        entry_points: List[str] = []
        ts_files = 0
        jsx_files = 0

        framework_indicators = {
            "react": [r"from ['\"]react['\"]", r"import React"],
            "next": [r"from ['\"]next", r"next/"],
            "vue": [r"from ['\"]vue['\"]", r"\.vue$"],
            "angular": [r"@angular/", r"@Component"],
            "express": [r"from ['\"]express['\"]", r"require\(['\"]express['\"]"],
            "nestjs": [r"@nestjs/", r"@Controller", r"@Injectable"],
            "svelte": [r"\.svelte$", r"from ['\"]svelte"],
            "nuxt": [r"from ['\"]nuxt", r"nuxt\.config"],
            "prisma": [r"@prisma/client", r"PrismaClient"],
            "typeorm": [r"from ['\"]typeorm['\"]", r"@Entity"],
            "mongoose": [r"from ['\"]mongoose['\"]", r"require\(['\"]mongoose['\"]"],
            "jest": [r"from ['\"]jest['\"]", r"describe\(", r"it\("],
            "mocha": [r"from ['\"]mocha['\"]"],
            "tailwindcss": [r"tailwindcss", r"tailwind\.config"],
        }

        config_names = {
            "next.config.js", "next.config.ts", "next.config.mjs",
            "vite.config.js", "vite.config.ts",
            "nuxt.config.js", "nuxt.config.ts",
            "webpack.config.js", "rollup.config.js",
            "tsconfig.json", "jest.config.js", "jest.config.ts",
            "tailwind.config.js", "tailwind.config.ts",
            ".eslintrc.js", ".prettierrc.js",
            "babel.config.js",
        }

        all_import_sources: Set[str] = set()

        for fpath in js_files:
            content = self.read_file(fpath)
            if content is None:
                continue

            rel = self.get_relative_path(fpath)
            total_loc += self.count_lines(content)

            if fpath.suffix in {".ts", ".tsx"}:
                ts_files += 1
            if fpath.suffix in {".jsx", ".tsx"}:
                jsx_files += 1

            # Test files
            if any(p in fpath.name.lower() for p in [".test.", ".spec.", "__test__", "__spec__"]):
                test_files.append(rel)

            # Config files
            if fpath.name in config_names:
                config_files.append(rel)

            # Entry points
            if fpath.name in {"index.js", "index.ts", "main.js", "main.ts", "app.js", "app.ts", "server.js", "server.ts"}:
                entry_points.append(rel)

            # Extract imports
            for match in re.finditer(r"""(?:import|from)\s+['"]([@\w/.-]+)['"]""", content):
                src = match.group(1).split("/")[0]
                if src.startswith("@"):
                    src = "/".join(match.group(1).split("/")[:2])
                imports[src] = imports.get(src, 0) + 1
                all_import_sources.add(match.group(1))

            # require() imports
            for match in re.finditer(r"""require\(['"]([@\w/.-]+)['"]\)""", content):
                src = match.group(1).split("/")[0]
                imports[src] = imports.get(src, 0) + 1
                all_import_sources.add(match.group(1))

            # React components (function/const)
            for match in re.finditer(
                r"(?:export\s+(?:default\s+)?)?(?:function|const)\s+([A-Z][a-zA-Z0-9]*)\s*[=(]",
                content
            ):
                components.append({"name": match.group(1), "file": rel})

            # Classes
            for match in re.finditer(
                r"(?:export\s+(?:default\s+)?)?class\s+(\w+)(?:\s+extends\s+(\w+))?",
                content
            ):
                classes.append({
                    "name": match.group(1),
                    "extends": match.group(2),
                    "file": rel,
                })

            # Named function declarations
            for match in re.finditer(
                r"(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)\s*\(",
                content
            ):
                name = match.group(1)
                if name[0].islower():  # Skip components (start with uppercase)
                    functions.append({"name": name, "file": rel})

            # Express/API routes
            for match in re.finditer(
                r"(?:app|router)\.(get|post|put|delete|patch|use)\s*\(\s*['\"]([^'\"]+)['\"]",
                content
            ):
                routes.append({
                    "method": match.group(1).upper(),
                    "path": match.group(2),
                    "file": rel,
                })

            # Fetch/axios API calls
            for match in re.finditer(
                r"""(?:fetch|axios\.(?:get|post|put|delete|patch))\s*\(\s*[`'"](https?://[^`'"]+|/api[^`'"]+)[`'"]""",
                content
            ):
                api_calls.append({"url": match.group(1), "file": rel})

            # Exports
            for match in re.finditer(r"export\s+(?:default\s+)?(?:const|function|class|let|var|type|interface|enum)\s+(\w+)", content):
                exports.append({"name": match.group(1), "file": rel})

        # Detect frameworks from imports
        for framework, patterns in framework_indicators.items():
            for pattern in patterns:
                for imp in all_import_sources:
                    if re.search(pattern, imp):
                        if framework not in frameworks_detected:
                            frameworks_detected.append(framework)
                        break

        top_imports = sorted(imports.items(), key=lambda x: -x[1])[:30]

        self.results = {
            "language": "JavaScript/TypeScript",
            "total_files": len(js_files),
            "typescript_files": ts_files,
            "jsx_tsx_files": jsx_files,
            "total_loc": total_loc,
            "components": components[:100],
            "classes": classes[:50],
            "functions": functions[:200],
            "top_imports": top_imports,
            "routes": routes,
            "api_calls": api_calls[:50],
            "exports": exports[:100],
            "frameworks": frameworks_detected,
            "entry_points": entry_points,
            "test_files": test_files[:50],
            "config_files": config_files,
            "total_components": len(components),
            "total_functions": len(functions),
            "total_test_files": len(test_files),
        }
        return self.results
