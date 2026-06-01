"""
Generic analyzer — fallback for unsupported languages.
Counts files, LOC, structure, and basic pattern matching.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from .base import BaseAnalyzer


class GenericAnalyzer(BaseAnalyzer):
    """Fallback analyzer for any project. Provides structural overview."""

    LANGUAGE_MAP = {
        ".py": "Python",
        ".js": "JavaScript", ".jsx": "JavaScript (JSX)",
        ".ts": "TypeScript", ".tsx": "TypeScript (TSX)",
        ".java": "Java",
        ".cs": "C#",
        ".go": "Go",
        ".rb": "Ruby",
        ".php": "PHP",
        ".rs": "Rust",
        ".swift": "Swift",
        ".kt": "Kotlin", ".kts": "Kotlin",
        ".scala": "Scala",
        ".dart": "Dart",
        ".lua": "Lua",
        ".r": "R", ".R": "R",
        ".pl": "Perl",
        ".ex": "Elixir", ".exs": "Elixir",
        ".hs": "Haskell",
        ".clj": "Clojure",
        ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++",
        ".c": "C", ".h": "C/C++",
        ".html": "HTML", ".htm": "HTML",
        ".css": "CSS", ".scss": "SCSS", ".sass": "SASS", ".less": "LESS",
        ".sql": "SQL",
        ".sh": "Shell", ".bash": "Shell",
        ".ps1": "PowerShell",
        ".yml": "YAML", ".yaml": "YAML",
        ".json": "JSON",
        ".xml": "XML",
        ".md": "Markdown", ".mdx": "MDX",
        ".toml": "TOML",
        ".ini": "INI",
        ".cfg": "Config",
        ".vue": "Vue",
        ".svelte": "Svelte",
        ".proto": "Protocol Buffers",
        ".graphql": "GraphQL", ".gql": "GraphQL",
    }

    @property
    def name(self) -> str:
        return "Generic Analyzer"

    def analyze(self) -> Dict[str, Any]:
        structure = self.summarize_structure(max_depth=4)
        all_files = self.walk_files()

        # Language breakdown
        lang_stats: Dict[str, Dict[str, int]] = {}
        total_loc = 0
        largest_files: List[Dict[str, Any]] = []

        for fpath in all_files:
            ext = fpath.suffix.lower()
            lang = self.LANGUAGE_MAP.get(ext, f"Other ({ext})" if ext else "No extension")

            if lang not in lang_stats:
                lang_stats[lang] = {"files": 0, "loc": 0}
            lang_stats[lang]["files"] += 1

            content = self.read_file(fpath)
            if content:
                loc = self.count_lines(content)
                lang_stats[lang]["loc"] += loc
                total_loc += loc

                largest_files.append({
                    "file": self.get_relative_path(fpath),
                    "loc": loc,
                    "size_bytes": fpath.stat().st_size,
                })

        # Sort languages by LOC
        sorted_langs = sorted(lang_stats.items(), key=lambda x: -x[1]["loc"])

        # Primary language
        primary_language = sorted_langs[0][0] if sorted_langs else "Unknown"

        # Largest files
        largest_files.sort(key=lambda x: -x["loc"])
        largest_files = largest_files[:20]

        # Detect README
        readme_files = self.find_files_by_name({"README.md", "README.rst", "README.txt", "README"})

        # Detect license
        license_files = self.find_files_by_name({"LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"})

        # Detect documentation
        doc_dirs = [d for d in structure["directories"] if any(
            k in d.lower() for k in ["doc", "docs", "wiki", "guide"]
        )]

        # Detect test directories
        test_dirs = [d for d in structure["directories"] if any(
            k in d.lower() for k in ["test", "tests", "spec", "specs", "__tests__"]
        )]

        self.results = {
            "primary_language": primary_language,
            "languages": dict(sorted_langs[:15]),
            "total_source_files": structure["total_source_files"],
            "total_directories": structure["total_directories"],
            "total_loc": total_loc,
            "file_counts_by_extension": structure["file_counts_by_extension"],
            "directory_tree": structure["directories"][:50],
            "largest_files": largest_files,
            "has_readme": bool(readme_files),
            "has_license": bool(license_files),
            "has_docs": bool(doc_dirs),
            "has_tests": bool(test_dirs),
            "readme_files": [self.get_relative_path(f) for f in readme_files],
            "doc_directories": doc_dirs,
            "test_directories": test_dirs,
        }
        return self.results
