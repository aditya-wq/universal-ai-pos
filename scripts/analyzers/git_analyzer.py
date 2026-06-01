"""
Git analyzer.
Parses git log, branches, contributors, and recent changes.
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseAnalyzer


class GitAnalyzer(BaseAnalyzer):
    """Analyzes git history, branches, and contributor statistics."""

    @property
    def name(self) -> str:
        return "Git Analyzer"

    def analyze(self) -> Dict[str, Any]:
        if not (self.project_dir / ".git").exists():
            return {"git_initialized": False}

        self.results = {
            "git_initialized": True,
            "recent_commits": self._get_recent_commits(50),
            "branches": self._get_branches(),
            "contributors": self._get_contributors(),
            "file_change_frequency": self._get_file_change_frequency(100),
            "current_branch": self._get_current_branch(),
            "total_commits": self._get_total_commits(),
            "first_commit_date": self._get_first_commit_date(),
            "last_commit_date": self._get_last_commit_date(),
            "uncommitted_changes": self._get_uncommitted_changes(),
            "tags": self._get_tags(),
            "remote_url": self._get_remote_url(),
        }
        return self.results

    def _run_git(self, args: List[str], max_output: int = 50000) -> Optional[str]:
        """Run a git command and return stdout."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0:
                return result.stdout[:max_output]
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def _get_recent_commits(self, count: int) -> List[Dict[str, str]]:
        output = self._run_git([
            "log", f"-{count}", "--pretty=format:%H|%an|%ae|%ad|%s",
            "--date=iso"
        ])
        if not output:
            return []

        commits = []
        for line in output.strip().splitlines():
            parts = line.split("|", 4)
            if len(parts) == 5:
                commits.append({
                    "hash": parts[0][:8],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4][:200],
                })
        return commits

    def _get_branches(self) -> List[Dict[str, str]]:
        output = self._run_git(["branch", "-a", "--format=%(refname:short)|%(objectname:short)|%(committerdate:iso)"])
        if not output:
            return []

        branches = []
        for line in output.strip().splitlines():
            parts = line.split("|", 2)
            if parts:
                branch = {
                    "name": parts[0],
                    "commit": parts[1] if len(parts) > 1 else "",
                    "date": parts[2] if len(parts) > 2 else "",
                }
                branches.append(branch)
        return branches[:50]

    def _get_contributors(self) -> List[Dict[str, Any]]:
        output = self._run_git(["shortlog", "-sne", "--all"])
        if not output:
            return []

        contributors = []
        for line in output.strip().splitlines():
            match = re.match(r"\s*(\d+)\s+(.+?)\s+<(.+?)>", line)
            if match:
                contributors.append({
                    "commits": int(match.group(1)),
                    "name": match.group(2),
                    "email": match.group(3),
                })
        return sorted(contributors, key=lambda x: -x["commits"])[:30]

    def _get_file_change_frequency(self, count: int) -> List[Dict[str, Any]]:
        """Find most frequently changed files."""
        output = self._run_git([
            "log", f"-{count}", "--pretty=format:", "--name-only"
        ])
        if not output:
            return []

        freq: Dict[str, int] = {}
        for line in output.strip().splitlines():
            line = line.strip()
            if line:
                freq[line] = freq.get(line, 0) + 1

        top = sorted(freq.items(), key=lambda x: -x[1])[:30]
        return [{"file": f, "changes": c} for f, c in top]

    def _get_current_branch(self) -> str:
        output = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        return output.strip() if output else "unknown"

    def _get_total_commits(self) -> int:
        output = self._run_git(["rev-list", "--count", "HEAD"])
        try:
            return int(output.strip()) if output else 0
        except ValueError:
            return 0

    def _get_first_commit_date(self) -> str:
        output = self._run_git(["log", "--reverse", "--format=%ad", "--date=iso", "-1"])
        return output.strip() if output else ""

    def _get_last_commit_date(self) -> str:
        output = self._run_git(["log", "--format=%ad", "--date=iso", "-1"])
        return output.strip() if output else ""

    def _get_uncommitted_changes(self) -> Dict[str, List[str]]:
        staged = self._run_git(["diff", "--cached", "--name-only"])
        unstaged = self._run_git(["diff", "--name-only"])
        untracked = self._run_git(["ls-files", "--others", "--exclude-standard"])

        return {
            "staged": staged.strip().splitlines() if staged else [],
            "unstaged": unstaged.strip().splitlines() if unstaged else [],
            "untracked": untracked.strip().splitlines()[:20] if untracked else [],
        }

    def _get_tags(self) -> List[str]:
        output = self._run_git(["tag", "--sort=-version:refname", "-l"])
        return output.strip().splitlines()[:20] if output else []

    def _get_remote_url(self) -> str:
        output = self._run_git(["remote", "get-url", "origin"])
        return output.strip() if output else ""
