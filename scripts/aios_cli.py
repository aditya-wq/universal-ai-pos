#!/usr/bin/env python3
"""
AIOS CLI — Universal AI Project Operating System
The permanent project brain for AI development tools.

Usage:
    uv run aios_cli.py <command> [options]

Commands:
    init            Initialize .aios/ folder in a project
    scan            Scan project and populate .aios/ documents
    build-context   Generate compressed CONTEXT.md for AI consumption
    update          Update specific documents after changes
    decision        Record a technical decision
    task            Manage tasks (add, complete, list)
    bug             Manage bugs (add, resolve, list)
    health          Generate project health dashboard
    security-scan   Run security analysis
    snapshot        Create a state snapshot
    diff            Compare snapshots
    status          Quick project status summary
    workflow        Pre/post implementation checks
"""

import argparse
import hashlib
import json
import os
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add scripts directory to path for local imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from analyzers import (
    PythonAnalyzer,
    JavaScriptAnalyzer,
    DatabaseAnalyzer,
    ApiAnalyzer,
    InfrastructureAnalyzer,
    GitAnalyzer,
    SecurityAnalyzer,
    GenericAnalyzer,
)
from generators import (
    ProjectGenerator,
    ArchitectureGenerator,
    DatabaseGenerator,
    ApiGenerator,
    SecurityGenerator,
    ContextGenerator,
    HealthGenerator,
    AgentGenerator,
)


# ──────────────────────────────────────────────
#  Templates for init
# ──────────────────────────────────────────────

TEMPLATE_TASKS = """# Tasks

> Track all project tasks here.

## Backlog

| ID | Title | Priority | Assigned To | Status | Created |
|---|---|---|---|---|---|
| *T-001* | *Example task* | Medium | — | 🔲 Open | {date} |

## Status Legend
- 🔲 Open
- 🔨 In Progress
- ✅ Done
- ⏸️ Blocked
"""

TEMPLATE_BUGS = """# Bug Tracker

> Track all known bugs here.

## Open Bugs

| ID | Title | Severity | Component | Status | Reported |
|---|---|---|---|---|---|
| *B-001* | *Example bug* | Medium | — | 🔲 Open | {date} |

## Severity Legend
- 🔴 Critical
- 🟠 High
- 🟡 Medium
- 🟢 Low

## Resolved Bugs
*None yet.*
"""

TEMPLATE_TESTS = """# Test Status

> Track testing progress here.

## Test Coverage

| Module | Unit Tests | Integration | E2E | Coverage |
|---|---|---|---|---|
| *Module 1* | — | — | — | — |

## Test Results
*Run `aios scan` to auto-detect test files.*
"""

TEMPLATE_CHANGELOG = """# Changelog

> All changes to this project are documented here.
> Format: [Date] [Author/AI] — Description

## Changes

"""

TEMPLATE_DECISIONS = """# Technical Decisions

> All major technical and architectural decisions are recorded here.
> **AI models MUST consult this file before generating code.**

## Decision Log

"""

TEMPLATE_ROADMAP = """# Roadmap

> Future plans and milestones.

## Upcoming

| Milestone | Target Date | Status | Description |
|---|---|---|---|
| *v1.0* | *TBD* | 🔲 Planned | *Initial release* |

## Completed Milestones
*None yet.*
"""

TEMPLATE_TIMELINE = """# Project Timeline

> Key events and milestones chronology.

## Timeline

| Date | Event | Details |
|---|---|---|
| {date} | AIOS Initialized | Project brain created |

"""

TEMPLATE_AI_RULES = """# AI Rules

> **Rules that ALL AI models MUST follow when working on this project.**
> This file is the source of truth for AI behavior.

## Mandatory Pre-Implementation Checklist

Before performing ANY task, the AI MUST:

1. Read `PROJECT.md` — understand the project
2. Read `CURRENT_STATE.md` — understand current status
3. Read `DECISIONS.md` — understand past decisions
4. Read `SECURITY.md` — understand security requirements
5. Read `TASKS.md` — check for related tasks
6. Analyze dependencies and impact

## Mandatory Post-Implementation Checklist

After performing ANY task, the AI MUST:

1. Update `CHANGELOG.md` with all changes
2. Update `TASKS.md` if a task was completed
3. Update `CURRENT_STATE.md` with new status
4. Update `TESTS.md` if tests were added/modified
5. Generate an implementation summary
6. Flag any security concerns

## Context Window Optimization & Scaling (e.g., MiniMax M2.7 / 200K+ Tokens)

The system is designed to be highly token-efficient for smaller context windows while scaling to take full advantage of large context window models. For example, the MiniMax M2.7 model features a context window of 204,800 tokens (with a usable limit around 196,608 to 200K tokens) and supports a maximum output length of 131,072 tokens.

To optimize context usage across different models:
- **For Large Context Windows (200K - 1M+ Tokens)**: Do not limit yourself. You can scale the AIOS context budget (e.g., `aios build-context --max-tokens 50000` or higher) to ingest complete files, detailed dependency trees, and full function implementations. This capacity allows the model to process massive inputs, such as entire software repositories, helping you understand how to change code without breaking existing functions or workflow errors.
- **For Low Context Windows**: Ensure the context remains highly compact and efficient (e.g., keeping `CONTEXT.md` below 10,000 tokens) by relying on summaries, signature mappings, and key endpoint lists.
- **Workflow Integrity**: Use the appropriate context budget to prevent regressions, verify import paths, and trace code dependencies across modules.

## Core Behavioral Guidelines

To reduce common AI coding mistakes, adhere strictly to these principles:

### 1. Think Before Coding
*Don't assume. Don't hide confusion. Surface tradeoffs.*
- State your assumptions explicitly before writing code.
- If multiple interpretations exist, present them rather than picking silently.
- If a simpler approach exists, suggest it. Push back on overcomplication.
- If something is unclear, STOP and ask for clarification.

### 2. Simplicity First
*Minimum code that solves the problem. Nothing speculative.*
- Do not add features beyond what was asked.
- Avoid abstractions for single-use code.
- No speculativeness, extra flexibility, or unrequested config.
- No complex error handling for impossible scenarios.
- If a 200-line implementation could be written in 50 lines, rewrite it.

### 3. Surgical Changes
*Touch only what you must. Clean up only your own mess.*
- Do not "improve" or reformat adjacent code or comments.
- Do not refactor parts of the codebase that are not broken.
- Match existing style exactly, even if you would prefer a different style.
- Remove imports, variables, and functions that *your* changes made unused. Do not touch pre-existing dead code.

### 4. Goal-Driven Execution
*Define success criteria. Loop until verified.*
- Transform tasks into verifiable criteria (e.g., write reproducing tests for bugs, write invalid validation tests).
- For multi-step tasks, define and trace a clear step-by-step verification plan:
  1. [Step] -> verify: [check]
  2. [Step] -> verify: [check]
"""

TEMPLATE_AI_HISTORY = """# AI Action History

> Automatically records all AI-generated changes.
> Format: [Date] [AI Model] — Action description

## History

"""


def now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ──────────────────────────────────────────────
#  Core functions
# ──────────────────────────────────────────────

def get_aios_dir(project_dir: str) -> Path:
    """Get .aios directory path."""
    return Path(project_dir).resolve() / ".aios"


def ensure_aios_exists(project_dir: str) -> Path:
    """Ensure .aios directory exists, error if not."""
    aios_dir = get_aios_dir(project_dir)
    if not aios_dir.exists():
        print(f"Error: .aios/ not found in {project_dir}. Run 'aios init' first.", file=sys.stderr)
        sys.exit(1)
    return aios_dir


def write_doc(aios_dir: Path, filename: str, content: str):
    """Write a document to the .aios directory."""
    fpath = aios_dir / filename
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")
    print(f"  ✅ {filename}")


def append_doc(aios_dir: Path, filename: str, content: str):
    """Append content to a document."""
    fpath = aios_dir / filename
    if fpath.exists():
        existing = fpath.read_text(encoding="utf-8")
        fpath.write_text(existing + content, encoding="utf-8")
    else:
        fpath.write_text(content, encoding="utf-8")


def log_ai_history(aios_dir: Path, action: str, details: str = ""):
    """Append to AI_HISTORY.md."""
    entry = f"- **{now_str()}** — {action}"
    if details:
        entry += f"\n  - {details}"
    entry += "\n"
    append_doc(aios_dir, "AI_HISTORY.md", entry)


# ──────────────────────────────────────────────
#  Command: init
# ──────────────────────────────────────────────

def cmd_init(args):
    """Initialize .aios/ folder structure."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = project_dir / ".aios"

    if aios_dir.exists() and not args.force:
        print(f"Error: .aios/ already exists in {project_dir}. Use --force to reinitialize.", file=sys.stderr)
        sys.exit(1)

    print(f"🚀 Initializing AIOS in: {project_dir}")
    print()

    # Create directories
    aios_dir.mkdir(exist_ok=True)
    (aios_dir / "AGENTS").mkdir(exist_ok=True)
    (aios_dir / "snapshots").mkdir(exist_ok=True)

    date = today_str()

    # Write template files
    templates = {
        "TASKS.md": TEMPLATE_TASKS.format(date=date),
        "BUGS.md": TEMPLATE_BUGS.format(date=date),
        "TESTS.md": TEMPLATE_TESTS,
        "CHANGELOG.md": TEMPLATE_CHANGELOG,
        "DECISIONS.md": TEMPLATE_DECISIONS,
        "ROADMAP.md": TEMPLATE_ROADMAP,
        "TIMELINE.md": TEMPLATE_TIMELINE.format(date=date),
        "AI_RULES.md": TEMPLATE_AI_RULES,
        "AI_HISTORY.md": TEMPLATE_AI_HISTORY,
    }

    print("Creating template files:")
    for filename, content in templates.items():
        write_doc(aios_dir, filename, content)

    # These will be populated by scan
    placeholder_files = [
        "PROJECT.md", "CURRENT_STATE.md", "ARCHITECTURE.md",
        "DATABASE.md", "FEATURES.md", "MODULES.md", "API.md",
        "SECURITY.md", "ROLES_PERMISSIONS.md", "DEPENDENCIES.md",
        "CONTEXT.md",
    ]
    print("\nCreating placeholder files (run 'scan' to populate):")
    for filename in placeholder_files:
        fpath = aios_dir / filename
        if not fpath.exists():
            write_doc(aios_dir, filename, f"# {filename.replace('.md', '')}\n\n*Run `aios scan` to populate this file.*\n")

    # Create agent profiles
    print("\nCreating agent profiles:")
    agent_gen = AgentGenerator({})
    agents = agent_gen.generate_all()
    for agent_file, content in agents.items():
        write_doc(aios_dir, f"AGENTS/{agent_file}", content)

    # Log initialization
    log_ai_history(aios_dir, "AIOS initialized", f"Project: {project_dir.name}")

    print(f"\n✅ AIOS initialized successfully!")
    print(f"   Location: {aios_dir}")
    print(f"   Next step: Run 'aios scan' to analyze the project.")


# ──────────────────────────────────────────────
#  Command: scan
# ──────────────────────────────────────────────

def run_all_analyzers(project_dir: str) -> Dict[str, Any]:
    """Run all analyzers and return combined results."""
    results = {}

    analyzers = [
        ("generic", GenericAnalyzer),
        ("python", PythonAnalyzer),
        ("javascript", JavaScriptAnalyzer),
        ("database", DatabaseAnalyzer),
        ("api", ApiAnalyzer),
        ("infrastructure", InfrastructureAnalyzer),
        ("git", GitAnalyzer),
        ("security", SecurityAnalyzer),
    ]

    for name, AnalyzerClass in analyzers:
        print(f"  🔍 Running {AnalyzerClass(project_dir).name}...")
        try:
            analyzer = AnalyzerClass(project_dir)
            data = analyzer.analyze()
            if data:
                results[name] = data
        except Exception as e:
            print(f"    ⚠️  {name} analyzer error: {e}", file=sys.stderr)

    return results


def cmd_scan(args):
    """Scan project and populate .aios/ documents."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    print(f"🔍 Scanning project: {project_dir}")
    print()

    # Run analyzers
    print("Phase 1: Analysis")
    scan_data = run_all_analyzers(str(project_dir))

    # Save raw scan data
    scan_cache = aios_dir / "snapshots" / ".last_scan.json"
    scan_cache.parent.mkdir(exist_ok=True)
    with open(scan_cache, "w", encoding="utf-8") as f:
        json.dump(scan_data, f, indent=2, default=str)

    # Generate documents
    print("\nPhase 2: Document Generation")
    project_name = project_dir.name

    # Project documents
    proj_gen = ProjectGenerator(scan_data, project_name)
    write_doc(aios_dir, "PROJECT.md", proj_gen.generate_project_md())
    write_doc(aios_dir, "CURRENT_STATE.md", proj_gen.generate_current_state_md())
    write_doc(aios_dir, "FEATURES.md", proj_gen.generate_features_md())
    write_doc(aios_dir, "MODULES.md", proj_gen.generate_modules_md())
    write_doc(aios_dir, "DEPENDENCIES.md", proj_gen.generate_dependencies_md())

    # Architecture
    arch_gen = ArchitectureGenerator(scan_data)
    write_doc(aios_dir, "ARCHITECTURE.md", arch_gen.generate())

    # Database
    db_gen = DatabaseGenerator(scan_data)
    write_doc(aios_dir, "DATABASE.md", db_gen.generate())

    # API
    api_gen = ApiGenerator(scan_data)
    write_doc(aios_dir, "API.md", api_gen.generate())

    # Security
    sec_gen = SecurityGenerator(scan_data)
    write_doc(aios_dir, "SECURITY.md", sec_gen.generate_security_md())
    write_doc(aios_dir, "ROLES_PERMISSIONS.md", sec_gen.generate_roles_permissions_md())

    # Agent profiles
    agent_gen = AgentGenerator(scan_data)
    agents = agent_gen.generate_all()
    for agent_file, content in agents.items():
        write_doc(aios_dir, f"AGENTS/{agent_file}", content)

    # Log
    log_ai_history(aios_dir, "Full project scan completed",
                   f"Files: {scan_data.get('generic', {}).get('total_source_files', '?')}, "
                   f"LOC: {scan_data.get('generic', {}).get('total_loc', '?')}")

    # Summary
    generic = scan_data.get("generic", {})
    security = scan_data.get("security", {})
    print(f"\n✅ Scan complete!")
    print(f"   Files analyzed: {generic.get('total_source_files', 0):,}")
    print(f"   Lines of code: {generic.get('total_loc', 0):,}")
    print(f"   Language: {generic.get('primary_language', 'Unknown')}")
    print(f"   Security score: {security.get('security_score', 'N/A')}/100")
    print(f"\n   Run 'aios build-context' to generate AI context file.")


# ──────────────────────────────────────────────
#  Command: build-context
# ──────────────────────────────────────────────

def cmd_build_context(args):
    """Generate compressed CONTEXT.md."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    # Load last scan data
    scan_cache = aios_dir / "snapshots" / ".last_scan.json"
    if not scan_cache.exists():
        print("No scan data found. Running scan first...")
        # Create a temporary args object for scan
        class ScanArgs:
            project_dir = str(project_dir)
        cmd_scan(ScanArgs())

    with open(scan_cache, "r", encoding="utf-8") as f:
        scan_data = json.load(f)

    max_tokens = args.max_tokens

    print(f"📝 Building context (max {max_tokens:,} tokens)...")

    ctx_gen = ContextGenerator(scan_data, max_tokens=max_tokens)
    context = ctx_gen.generate()

    write_doc(aios_dir, "CONTEXT.md", context)

    # Calculate actual token estimate
    est_tokens = len(context) // 4
    print(f"\n✅ Context generated!")
    print(f"   Estimated tokens: ~{est_tokens:,} / {max_tokens:,} budget")
    print(f"   File: {aios_dir / 'CONTEXT.md'}")

    log_ai_history(aios_dir, "Context rebuilt", f"~{est_tokens:,} tokens")

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(context, encoding="utf-8")
        print(f"   Also written to: {output_path}")


# ──────────────────────────────────────────────
#  Command: decision
# ──────────────────────────────────────────────

def cmd_decision(args):
    """Record a technical decision."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    # Generate decision ID
    decisions_file = aios_dir / "DECISIONS.md"
    content = decisions_file.read_text(encoding="utf-8") if decisions_file.exists() else ""
    
    # Count existing decisions
    import re
    existing = re.findall(r"### DEC-(\d+)", content)
    next_id = max([int(x) for x in existing], default=0) + 1
    dec_id = f"DEC-{next_id:03d}"

    entry = f"""### {dec_id} — {args.title}

- **Date**: {now_str()}
- **Status**: Accepted
- **Description**: {args.description}
- **Reason**: {args.reason}
- **Alternatives Considered**: {args.alternatives or 'None documented'}
- **Expected Impact**: {args.impact or 'Not specified'}
- **Affected Modules**: {args.modules or 'Not specified'}

---

"""
    append_doc(aios_dir, "DECISIONS.md", entry)
    log_ai_history(aios_dir, f"Decision recorded: {dec_id}", args.title)

    print(f"✅ Decision recorded: {dec_id} — {args.title}")


# ──────────────────────────────────────────────
#  Command: task
# ──────────────────────────────────────────────

def cmd_task(args):
    """Manage tasks."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    if args.task_action == "add":
        tasks_file = aios_dir / "TASKS.md"
        content = tasks_file.read_text(encoding="utf-8") if tasks_file.exists() else ""
        
        import re
        existing = re.findall(r"T-(\d+)", content)
        next_id = max([int(x) for x in existing], default=0) + 1
        task_id = f"T-{next_id:03d}"

        entry = f"| {task_id} | {args.title} | {args.priority or 'Medium'} | {args.assigned or '—'} | 🔲 Open | {today_str()} |\n"
        
        # Insert before Status Legend
        if "## Status Legend" in content:
            content = content.replace("## Status Legend", entry + "\n## Status Legend")
        else:
            content += entry
        
        tasks_file.write_text(content, encoding="utf-8")
        log_ai_history(aios_dir, f"Task added: {task_id}", args.title)
        print(f"✅ Task added: {task_id} — {args.title}")

    elif args.task_action == "complete":
        tasks_file = aios_dir / "TASKS.md"
        if not tasks_file.exists():
            print("Error: TASKS.md not found.", file=sys.stderr)
            sys.exit(1)
        
        content = tasks_file.read_text(encoding="utf-8")
        task_id = args.id.upper()
        
        lines = content.splitlines()
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith("|") and (f" {task_id} " in line or f"*{task_id}*" in line):
                if f"~~{task_id}~~" not in line:
                    line = line.replace(f" {task_id} ", f" ~~{task_id}~~ ")
                    line = line.replace(f"*{task_id}*", f"~~{task_id}~~")
                line = line.replace("🔲 Open", "✅ Done")
                line = line.replace("🔨 In Progress", "✅ Done")
                line = line.replace("⏸️ Blocked", "✅ Done")
                lines[i] = line
                updated = True
                break
        
        if updated:
            content = "\n".join(lines) + "\n"
            tasks_file.write_text(content, encoding="utf-8")
            log_ai_history(aios_dir, f"Task completed: {task_id}")
            print(f"✅ Task completed: {task_id}")
        else:
            print(f"Error: Task {task_id} not found.", file=sys.stderr)
            sys.exit(1)

    elif args.task_action == "list":
        tasks_file = aios_dir / "TASKS.md"
        if tasks_file.exists():
            print(tasks_file.read_text(encoding="utf-8"))
        else:
            print("No tasks found.")


# ──────────────────────────────────────────────
#  Command: bug
# ──────────────────────────────────────────────

def cmd_bug(args):
    """Manage bugs."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    if args.bug_action == "add":
        bugs_file = aios_dir / "BUGS.md"
        content = bugs_file.read_text(encoding="utf-8") if bugs_file.exists() else ""
        
        import re
        existing = re.findall(r"B-(\d+)", content)
        next_id = max([int(x) for x in existing], default=0) + 1
        bug_id = f"B-{next_id:03d}"

        entry = f"| {bug_id} | {args.title} | {args.severity or 'Medium'} | {args.component or '—'} | 🔲 Open | {today_str()} |\n"
        
        if "## Severity Legend" in content:
            content = content.replace("## Severity Legend", entry + "\n## Severity Legend")
        else:
            content += entry
        
        bugs_file.write_text(content, encoding="utf-8")
        log_ai_history(aios_dir, f"Bug reported: {bug_id}", args.title)
        print(f"✅ Bug reported: {bug_id} — {args.title}")

    elif args.bug_action == "resolve":
        bugs_file = aios_dir / "BUGS.md"
        if not bugs_file.exists():
            print("Error: BUGS.md not found.", file=sys.stderr)
            sys.exit(1)
        
        content = bugs_file.read_text(encoding="utf-8")
        bug_id = args.id.upper()
        
        lines = content.splitlines()
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith("|") and (f" {bug_id} " in line or f"*{bug_id}*" in line):
                if f"~~{bug_id}~~" not in line:
                    line = line.replace(f" {bug_id} ", f" ~~{bug_id}~~ ")
                    line = line.replace(f"*{bug_id}*", f"~~{bug_id}~~")
                line = line.replace("🔲 Open", "✅ Resolved")
                lines[i] = line
                updated = True
                break
        
        if updated:
            content = "\n".join(lines) + "\n"
            bugs_file.write_text(content, encoding="utf-8")
            log_ai_history(aios_dir, f"Bug resolved: {bug_id}")
            print(f"✅ Bug resolved: {bug_id}")
        else:
            print(f"Error: Bug {bug_id} not found.", file=sys.stderr)
            sys.exit(1)

    elif args.bug_action == "list":
        bugs_file = aios_dir / "BUGS.md"
        if bugs_file.exists():
            print(bugs_file.read_text(encoding="utf-8"))
        else:
            print("No bugs found.")


# ──────────────────────────────────────────────
#  Command: health
# ──────────────────────────────────────────────

def cmd_health(args):
    """Generate project health dashboard."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    scan_cache = aios_dir / "snapshots" / ".last_scan.json"
    if not scan_cache.exists():
        print("No scan data found. Running scan first...")
        class ScanArgs:
            project_dir = str(project_dir)
        cmd_scan(ScanArgs())

    with open(scan_cache, "r", encoding="utf-8") as f:
        scan_data = json.load(f)

    health_gen = HealthGenerator(scan_data, str(aios_dir))
    report = health_gen.generate()

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"✅ Health report written to: {args.output}")
    else:
        print(report)

    log_ai_history(aios_dir, "Health report generated")


# ──────────────────────────────────────────────
#  Command: security-scan
# ──────────────────────────────────────────────

def cmd_security_scan(args):
    """Run security analysis."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    print(f"🔒 Running security scan on: {project_dir}")

    analyzer = SecurityAnalyzer(str(project_dir))
    results = analyzer.analyze()

    # Generate security doc
    scan_data = {"security": results}
    sec_gen = SecurityGenerator(scan_data)
    report = sec_gen.generate_security_md()

    write_doc(aios_dir, "SECURITY.md", report)

    score = results.get("security_score", 0)
    secrets = results.get("total_secrets_found", 0)
    severity = results.get("severity", "UNKNOWN")

    print(f"\n🔒 Security Score: {score}/100 ({severity})")
    if secrets > 0:
        print(f"   ⚠️  {secrets} hardcoded secrets detected!")
    
    missing = results.get("missing_security_features", [])
    if missing:
        print(f"   Missing features: {len(missing)}")

    log_ai_history(aios_dir, f"Security scan completed: {score}/100 ({severity})")

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"\n   Report saved to: {args.output}")


# ──────────────────────────────────────────────
#  Command: snapshot
# ──────────────────────────────────────────────

def cmd_snapshot(args):
    """Create a point-in-time snapshot of .aios/ state."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    snapshot_name = args.name or f"snapshot_{timestamp}"
    snapshot_dir = aios_dir / "snapshots" / snapshot_name

    snapshot_dir.mkdir(parents=True, exist_ok=True)

    # Copy all .md files
    snapshot_data = {}
    for md_file in aios_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        snapshot_data[md_file.name] = content
        (snapshot_dir / md_file.name).write_text(content, encoding="utf-8")

    # Copy agent files
    agents_dir = aios_dir / "AGENTS"
    if agents_dir.exists():
        snapshot_agents = snapshot_dir / "AGENTS"
        snapshot_agents.mkdir(exist_ok=True)
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text(encoding="utf-8")
            snapshot_data[f"AGENTS/{agent_file.name}"] = content
            (snapshot_agents / agent_file.name).write_text(content, encoding="utf-8")

    # Save metadata
    metadata = {
        "timestamp": timestamp,
        "name": snapshot_name,
        "files": list(snapshot_data.keys()),
        "created_at": now_str(),
    }
    (snapshot_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    log_ai_history(aios_dir, f"Snapshot created: {snapshot_name}")
    print(f"✅ Snapshot created: {snapshot_name}")
    print(f"   Location: {snapshot_dir}")
    print(f"   Files: {len(snapshot_data)}")


# ──────────────────────────────────────────────
#  Command: diff
# ──────────────────────────────────────────────

def cmd_diff(args):
    """Compare current state against a snapshot."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    snapshot_name = args.snapshot
    snapshot_dir = aios_dir / "snapshots" / snapshot_name

    if not snapshot_dir.exists():
        # List available snapshots
        snapshots_root = aios_dir / "snapshots"
        available = [d.name for d in snapshots_root.iterdir()
                     if d.is_dir() and d.name != ".last_scan.json" and not d.name.startswith(".")]
        print(f"Error: Snapshot '{snapshot_name}' not found.", file=sys.stderr)
        if available:
            print(f"Available snapshots: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    print(f"📊 Comparing current state with snapshot: {snapshot_name}")
    print()

    changes = []
    # Compare .md files
    for md_file in aios_dir.glob("*.md"):
        snapshot_file = snapshot_dir / md_file.name
        if snapshot_file.exists():
            current = md_file.read_text(encoding="utf-8")
            previous = snapshot_file.read_text(encoding="utf-8")
            if current != previous:
                current_hash = hashlib.md5(current.encode()).hexdigest()[:8]
                previous_hash = hashlib.md5(previous.encode()).hexdigest()[:8]
                changes.append({
                    "file": md_file.name,
                    "status": "modified",
                    "current_lines": len(current.splitlines()),
                    "previous_lines": len(previous.splitlines()),
                })
        else:
            changes.append({"file": md_file.name, "status": "added"})

    # Check for deleted files
    for snapshot_file in snapshot_dir.glob("*.md"):
        current_file = aios_dir / snapshot_file.name
        if not current_file.exists():
            changes.append({"file": snapshot_file.name, "status": "deleted"})

    if changes:
        print("| File | Status | Current Lines | Previous Lines |")
        print("|---|---|---|---|")
        for change in changes:
            status_icon = {"modified": "📝", "added": "➕", "deleted": "❌"}.get(change["status"], "?")
            current_lines = change.get("current_lines", "—")
            previous_lines = change.get("previous_lines", "—")
            print(f"| {change['file']} | {status_icon} {change['status']} | {current_lines} | {previous_lines} |")
    else:
        print("✅ No changes since snapshot.")


# ──────────────────────────────────────────────
#  Command: update
# ──────────────────────────────────────────────

def cmd_update(args):
    """Update changelog and track changes."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    date = now_str()
    files = args.files or "unspecified"
    reason = args.reason or "No reason provided"
    author = args.author or "AI"

    entry = f"### [{date}] — {author}\n\n"
    entry += f"**Reason**: {reason}\n\n"

    if args.files:
        file_list = [f.strip() for f in args.files.split(",")]
        entry += "**Modified Files**:\n"
        for f in file_list:
            entry += f"- `{f}`\n"
        entry += "\n"

    if args.added:
        added_list = [f.strip() for f in args.added.split(",")]
        entry += "**Added Files**:\n"
        for f in added_list:
            entry += f"- `{f}`\n"
        entry += "\n"

    if args.deleted:
        deleted_list = [f.strip() for f in args.deleted.split(",")]
        entry += "**Deleted Files**:\n"
        for f in deleted_list:
            entry += f"- `{f}`\n"
        entry += "\n"

    if args.impact:
        entry += f"**Impact**: {args.impact}\n\n"

    entry += "---\n\n"

    append_doc(aios_dir, "CHANGELOG.md", entry)
    log_ai_history(aios_dir, f"Change recorded: {reason}")

    print(f"✅ Changelog updated: {reason}")


# ──────────────────────────────────────────────
#  Command: status
# ──────────────────────────────────────────────

def cmd_status(args):
    """Quick project status summary."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    print(f"📊 AIOS Status — {project_dir.name}")
    print("=" * 50)

    # Check which files exist and their sizes
    docs = [
        "PROJECT.md", "CURRENT_STATE.md", "ARCHITECTURE.md",
        "DATABASE.md", "API.md", "SECURITY.md", "CONTEXT.md",
        "TASKS.md", "BUGS.md", "TESTS.md", "CHANGELOG.md",
        "DECISIONS.md", "ROADMAP.md", "AI_RULES.md",
    ]

    for doc in docs:
        fpath = aios_dir / doc
        if fpath.exists():
            size = fpath.stat().st_size
            # Check if it's just a placeholder
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            if "Run `aios scan` to populate" in content:
                status = "⬜ Placeholder"
            elif size < 100:
                status = "🟡 Minimal"
            else:
                status = "🟢 Populated"
            print(f"  {status}  {doc} ({size:,} bytes)")
        else:
            print(f"  ❌ Missing  {doc}")

    # Agents
    agents_dir = aios_dir / "AGENTS"
    if agents_dir.exists():
        agent_count = len(list(agents_dir.glob("*.md")))
        print(f"\n  🤖 Agent profiles: {agent_count}")

    # Snapshots
    snapshots_dir = aios_dir / "snapshots"
    if snapshots_dir.exists():
        snapshot_count = len([d for d in snapshots_dir.iterdir() if d.is_dir()])
        print(f"  📸 Snapshots: {snapshot_count}")

    # Last scan
    scan_cache = aios_dir / "snapshots" / ".last_scan.json"
    if scan_cache.exists():
        import time
        mod_time = datetime.fromtimestamp(scan_cache.stat().st_mtime, tz=timezone.utc)
        print(f"\n  🔍 Last scan: {mod_time.strftime('%Y-%m-%d %H:%M UTC')}")
    else:
        print(f"\n  ⚠️  No scan data found. Run 'aios scan'.")


# ──────────────────────────────────────────────
#  Command: workflow
# ──────────────────────────────────────────────

def cmd_workflow(args):
    """Pre/post implementation workflow checks."""
    project_dir = Path(args.project_dir).resolve()
    aios_dir = ensure_aios_exists(str(project_dir))

    if args.phase == "pre":
        print("📋 Pre-Implementation Checklist")
        print("=" * 40)
        checks = [
            ("PROJECT.md", "Project understanding"),
            ("CURRENT_STATE.md", "Current development state"),
            ("DECISIONS.md", "Past technical decisions"),
            ("SECURITY.md", "Security requirements"),
            ("TASKS.md", "Related tasks"),
            ("DEPENDENCIES.md", "Dependency analysis"),
        ]
        for doc, purpose in checks:
            fpath = aios_dir / doc
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if "Run `aios scan` to populate" not in content:
                    print(f"  ✅ {doc} — {purpose}")
                else:
                    print(f"  ⚠️  {doc} — {purpose} (placeholder only!)")
            else:
                print(f"  ❌ {doc} — {purpose} (MISSING!)")

        print("\n✅ Pre-implementation check complete. Proceed with implementation.")

    elif args.phase == "post":
        print("📋 Post-Implementation Checklist")
        print("=" * 40)
        print("  Ensure you have updated:")
        print("  □ CHANGELOG.md — Document all changes")
        print("  □ TASKS.md — Mark completed tasks")
        print("  □ CURRENT_STATE.md — Update project state")
        print("  □ TESTS.md — Document new/modified tests")
        print("  □ BUGS.md — Close resolved bugs")
        print()
        print("  Recommended:")
        print("  □ Run 'aios scan' to refresh analysis")
        print("  □ Run 'aios build-context' to update AI context")
        print("  □ Run 'aios snapshot' to save current state")


# ──────────────────────────────────────────────
#  Argument Parser
# ──────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aios",
        description="AIOS — Universal AI Project Operating System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize .aios/ in a project")
    p_init.add_argument("--project-dir", default=".", help="Project directory (default: current)")
    p_init.add_argument("--force", action="store_true", help="Force reinitialize")
    p_init.set_defaults(func=cmd_init)

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan project and populate documents")
    p_scan.add_argument("--project-dir", default=".", help="Project directory")
    p_scan.set_defaults(func=cmd_scan)

    # build-context
    p_ctx = subparsers.add_parser("build-context", help="Generate compressed CONTEXT.md")
    p_ctx.add_argument("--project-dir", default=".", help="Project directory")
    p_ctx.add_argument("--max-tokens", type=int, default=10000, help="Max token budget (default: 10000)")
    p_ctx.add_argument("--output", help="Additional output file path")
    p_ctx.set_defaults(func=cmd_build_context)

    # decision
    p_dec = subparsers.add_parser("decision", help="Record a technical decision")
    p_dec.add_argument("--project-dir", default=".", help="Project directory")
    p_dec.add_argument("--title", required=True, help="Decision title")
    p_dec.add_argument("--description", required=True, help="Decision description")
    p_dec.add_argument("--reason", required=True, help="Reason for the decision")
    p_dec.add_argument("--alternatives", help="Alternatives considered")
    p_dec.add_argument("--impact", help="Expected impact")
    p_dec.add_argument("--modules", help="Affected modules")
    p_dec.set_defaults(func=cmd_decision)

    # task
    p_task = subparsers.add_parser("task", help="Manage tasks")
    task_sub = p_task.add_subparsers(dest="task_action")

    p_task_add = task_sub.add_parser("add", help="Add a task")
    p_task_add.add_argument("--project-dir", default=".", help="Project directory")
    p_task_add.add_argument("--title", required=True, help="Task title")
    p_task_add.add_argument("--priority", help="Priority (Low/Medium/High/Critical)")
    p_task_add.add_argument("--assigned", help="Assigned to")

    p_task_complete = task_sub.add_parser("complete", help="Complete a task")
    p_task_complete.add_argument("--project-dir", default=".", help="Project directory")
    p_task_complete.add_argument("--id", required=True, help="Task ID (e.g., T-001)")

    p_task_list = task_sub.add_parser("list", help="List tasks")
    p_task_list.add_argument("--project-dir", default=".", help="Project directory")

    p_task.set_defaults(func=cmd_task)

    # bug
    p_bug = subparsers.add_parser("bug", help="Manage bugs")
    bug_sub = p_bug.add_subparsers(dest="bug_action")

    p_bug_add = bug_sub.add_parser("add", help="Report a bug")
    p_bug_add.add_argument("--project-dir", default=".", help="Project directory")
    p_bug_add.add_argument("--title", required=True, help="Bug title")
    p_bug_add.add_argument("--severity", help="Severity (Low/Medium/High/Critical)")
    p_bug_add.add_argument("--component", help="Affected component")

    p_bug_resolve = bug_sub.add_parser("resolve", help="Resolve a bug")
    p_bug_resolve.add_argument("--project-dir", default=".", help="Project directory")
    p_bug_resolve.add_argument("--id", required=True, help="Bug ID (e.g., B-001)")

    p_bug_list = bug_sub.add_parser("list", help="List bugs")
    p_bug_list.add_argument("--project-dir", default=".", help="Project directory")

    p_bug.set_defaults(func=cmd_bug)

    # health
    p_health = subparsers.add_parser("health", help="Generate health dashboard")
    p_health.add_argument("--project-dir", default=".", help="Project directory")
    p_health.add_argument("--output", help="Output file path")
    p_health.set_defaults(func=cmd_health)

    # security-scan
    p_sec = subparsers.add_parser("security-scan", help="Run security analysis")
    p_sec.add_argument("--project-dir", default=".", help="Project directory")
    p_sec.add_argument("--output", help="Output file path")
    p_sec.set_defaults(func=cmd_security_scan)

    # snapshot
    p_snap = subparsers.add_parser("snapshot", help="Create a state snapshot")
    p_snap.add_argument("--project-dir", default=".", help="Project directory")
    p_snap.add_argument("--name", help="Snapshot name (default: auto-timestamped)")
    p_snap.set_defaults(func=cmd_snapshot)

    # diff
    p_diff = subparsers.add_parser("diff", help="Compare with a snapshot")
    p_diff.add_argument("--project-dir", default=".", help="Project directory")
    p_diff.add_argument("--snapshot", required=True, help="Snapshot name to compare against")
    p_diff.set_defaults(func=cmd_diff)

    # update
    p_update = subparsers.add_parser("update", help="Record changes to changelog")
    p_update.add_argument("--project-dir", default=".", help="Project directory")
    p_update.add_argument("--reason", required=True, help="Reason for change")
    p_update.add_argument("--files", help="Modified files (comma-separated)")
    p_update.add_argument("--added", help="Added files (comma-separated)")
    p_update.add_argument("--deleted", help="Deleted files (comma-separated)")
    p_update.add_argument("--impact", help="Impact analysis")
    p_update.add_argument("--author", help="Author (default: AI)")
    p_update.set_defaults(func=cmd_update)

    # status
    p_status = subparsers.add_parser("status", help="Quick project status")
    p_status.add_argument("--project-dir", default=".", help="Project directory")
    p_status.set_defaults(func=cmd_status)

    # workflow
    p_workflow = subparsers.add_parser("workflow", help="Pre/post implementation checks")
    p_workflow.add_argument("--project-dir", default=".", help="Project directory")
    p_workflow.add_argument("--phase", required=True, choices=["pre", "post"], help="Workflow phase")
    p_workflow.set_defaults(func=cmd_workflow)

    return parser


def main():
    # Force UTF-8 stdout/stderr encoding on Windows to support emojis in console
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
