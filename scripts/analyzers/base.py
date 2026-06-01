"""
Base analyzer abstract class.
All analyzers inherit from BaseAnalyzer and implement the `analyze` method.
"""

import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Directories to always skip during scanning
DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git", ".svn", ".hg",
    "node_modules", "bower_components",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".nox", ".eggs", "*.egg-info",
    "venv", ".venv", "env", ".env",
    "dist", "build", "out", "target",
    ".next", ".nuxt", ".output",
    ".aios", ".idea", ".vscode",
    "vendor", "Pods",
    "coverage", ".coverage", "htmlcov",
    ".terraform", ".serverless",
    "bin", "obj",  # .NET
}

# File patterns to always skip
DEFAULT_IGNORE_FILES: Set[str] = {
    ".DS_Store", "Thumbs.db",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "composer.lock",
    "Gemfile.lock", "Cargo.lock",
}

# Binary file extensions to skip
BINARY_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
    ".zip", ".tar", ".gz", ".bz2", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".dll", ".so", ".dylib", ".o", ".a",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pyc", ".pyo", ".class", ".jar",
    ".db", ".sqlite", ".sqlite3",
    ".min.js", ".min.css",
}


class BaseAnalyzer(ABC):
    """Abstract base class for all project analyzers."""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir).resolve()
        self.results: Dict[str, Any] = {}
        self._file_cache: Dict[str, str] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this analyzer."""
        ...

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """Run analysis and return structured results."""
        ...

    def walk_files(
        self,
        extensions: Optional[Set[str]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_files: int = 5000,
    ) -> List[Path]:
        """
        Walk project directory and yield matching files.
        
        Args:
            extensions: Set of file extensions to include (e.g., {'.py', '.js'}).
            include_patterns: Regex patterns files must match.
            exclude_patterns: Regex patterns to exclude files.
            max_files: Safety cap on number of files to process.
        
        Returns:
            List of Path objects for matching files.
        """
        matched: List[Path] = []
        count = 0

        for root, dirs, files in os.walk(self.project_dir):
            # Filter out ignored directories in-place to prevent descent
            dirs[:] = [
                d for d in dirs
                if d not in DEFAULT_IGNORE_DIRS
                and not d.startswith(".")
                or d in {".github", ".gitlab", ".circleci"}
            ]

            for fname in files:
                if count >= max_files:
                    return matched

                if fname in DEFAULT_IGNORE_FILES:
                    continue

                fpath = Path(root) / fname
                rel = fpath.relative_to(self.project_dir)

                # Skip binary files
                if fpath.suffix.lower() in BINARY_EXTENSIONS:
                    continue

                # Extension filter
                if extensions and fpath.suffix.lower() not in extensions:
                    continue

                # Include patterns
                if include_patterns:
                    if not any(re.search(p, str(rel)) for p in include_patterns):
                        continue

                # Exclude patterns
                if exclude_patterns:
                    if any(re.search(p, str(rel)) for p in exclude_patterns):
                        continue

                matched.append(fpath)
                count += 1

        return matched

    def read_file(self, fpath: Path, max_size: int = 1_000_000) -> Optional[str]:
        """
        Read a file's content with caching and size limits.
        
        Args:
            fpath: Path to the file.
            max_size: Maximum file size in bytes (default 1MB).
        
        Returns:
            File contents as string, or None if unreadable.
        """
        key = str(fpath)
        if key in self._file_cache:
            return self._file_cache[key]

        try:
            if fpath.stat().st_size > max_size:
                return None
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            self._file_cache[key] = content
            return content
        except (OSError, UnicodeDecodeError):
            return None

    def count_lines(self, content: str) -> int:
        """Count non-empty, non-comment lines in content."""
        lines = 0
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
                lines += 1
        return lines

    def find_files_by_name(self, names: Set[str]) -> List[Path]:
        """Find files matching exact names anywhere in the project."""
        found: List[Path] = []
        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS]
            for fname in files:
                if fname in names:
                    found.append(Path(root) / fname)
        return found

    def get_relative_path(self, fpath: Path) -> str:
        """Get path relative to project root."""
        try:
            return str(fpath.relative_to(self.project_dir)).replace("\\", "/")
        except ValueError:
            return str(fpath).replace("\\", "/")

    def summarize_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """
        Generate a tree-like summary of the project structure.
        
        Returns:
            Dict with 'directories' and 'file_counts' by extension.
        """
        directories: List[str] = []
        ext_counts: Dict[str, int] = {}
        total_files = 0

        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS and not d.startswith(".")]
            
            rel_root = Path(root).relative_to(self.project_dir)
            depth = len(rel_root.parts)
            
            if depth <= max_depth:
                directories.append(str(rel_root).replace("\\", "/") if str(rel_root) != "." else "/")

            for fname in files:
                if fname in DEFAULT_IGNORE_FILES:
                    continue
                ext = Path(fname).suffix.lower()
                if ext not in BINARY_EXTENSIONS:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
                    total_files += 1

        return {
            "directories": directories,
            "file_counts_by_extension": dict(sorted(ext_counts.items(), key=lambda x: -x[1])),
            "total_source_files": total_files,
            "total_directories": len(directories),
        }
