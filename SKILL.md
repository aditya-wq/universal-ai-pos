---
name: aios
description: >-
  Universal AI Project Operating System. Install into any software project to
  create a persistent memory layer (.aios/) that allows any AI model to
  instantly understand the project. Scans codebases, compresses context,
  tracks decisions, manages tasks/bugs, analyzes security, and generates
  health dashboards. Works with ChatGPT, Claude, Gemini, Copilot, Cursor,
  Windsurf, Antigravity IDE, and any future AI system. Zero dependencies.
---

# AIOS — Universal AI Project Operating System

## Overview

AIOS creates a persistent `.aios/` memory layer inside any software project.
This layer acts as the project's single source of truth, enabling any AI model
to understand the entire project within minutes — without re-uploading or
re-analyzing the full codebase.

**Key capabilities:**
- **Project Analysis Engine** — Scans source code, frameworks, APIs, database
  schemas, infrastructure, git history, and security configurations
- **Context Compression** — Generates a <15K token `CONTEXT.md` representing
  projects with hundreds of files and thousands of functions
- **Persistent Memory** — Tracks decisions, changes, tasks, bugs, and history
  across AI sessions and providers
- **Security Scanner** — Detects hardcoded secrets, injection risks, missing
  auth, and generates a security score
- **Health Dashboard** — Multi-dimensional project health scoring
- **Agent Framework** — 8 specialized agent profiles (Architect, Frontend,
  Backend, Database, Security, DevOps, QA, Product)

**Supported languages:** Python, JavaScript/TypeScript, Java, C#, Go, Ruby,
PHP, Rust, SQL — plus generic analysis for any language.

**Supported project types:** SaaS, Web App, Mobile App, Desktop App, API
Platform, AI Product, CRM, ERP, Marketplace, Internal Tool, or any software.

## Quick Start

### 1. Initialize AIOS in a project

```bash
uv run scripts/aios_cli.py init --project-dir /path/to/project
```

### 2. Scan the project

```bash
uv run scripts/aios_cli.py scan --project-dir /path/to/project
```

### 3. Generate compressed AI context

```bash
uv run scripts/aios_cli.py build-context --project-dir /path/to/project
```

### 4. Provide context to any AI

Copy the contents of `.aios/CONTEXT.md` and paste it at the beginning of any
AI conversation. The AI will instantly understand the project.

## CLI Commands

### `init` — Initialize AIOS

Creates the `.aios/` folder with all templates and agent profiles.

```bash
uv run scripts/aios_cli.py init --project-dir ./my-project
uv run scripts/aios_cli.py init --project-dir ./my-project --force  # Reinitialize
```

### `scan` — Analyze Project

Runs all analyzers (Python, JS/TS, Database, API, Infrastructure, Git,
Security, Generic) and populates all `.aios/` documents.

```bash
uv run scripts/aios_cli.py scan --project-dir ./my-project
```

**What gets analyzed:**
- Source code structure, classes, functions, imports
- Framework detection (Flask, Django, FastAPI, React, Next.js, Express, etc.)
- Database schemas (SQL, Django ORM, SQLAlchemy, Prisma, TypeORM)
- API endpoints (REST, GraphQL, OpenAPI)
- Infrastructure (Docker, CI/CD, Kubernetes, cloud services)
- Git history, branches, contributors
- Security (secrets, auth patterns, vulnerabilities)

### `build-context` — Generate AI Context

Creates a compressed `CONTEXT.md` file optimized for AI consumption.

```bash
uv run scripts/aios_cli.py build-context --project-dir ./my-project
uv run scripts/aios_cli.py build-context --project-dir ./my-project --max-tokens 15000
uv run scripts/aios_cli.py build-context --project-dir ./my-project --output ./context.md
```

### `decision` — Record Technical Decisions

Records architectural and technical decisions in `DECISIONS.md`.

```bash
uv run scripts/aios_cli.py decision \
  --project-dir ./my-project \
  --title "Use PostgreSQL over MySQL" \
  --description "Chose PostgreSQL for the primary database" \
  --reason "Better JSON support, JSONB columns, full-text search" \
  --alternatives "MySQL, MongoDB, SQLite" \
  --impact "All database schemas will use PostgreSQL-specific features" \
  --modules "database, api, backend"
```

### `task` — Manage Tasks

```bash
# Add a task
uv run scripts/aios_cli.py task add \
  --project-dir ./my-project \
  --title "Implement user authentication" \
  --priority High \
  --assigned "Backend Team"

# Complete a task
uv run scripts/aios_cli.py task complete --project-dir ./my-project --id T-001

# List all tasks
uv run scripts/aios_cli.py task list --project-dir ./my-project
```

### `bug` — Manage Bugs

```bash
# Report a bug
uv run scripts/aios_cli.py bug add \
  --project-dir ./my-project \
  --title "Login page crashes on mobile" \
  --severity High \
  --component "Frontend/Auth"

# Resolve a bug
uv run scripts/aios_cli.py bug resolve --project-dir ./my-project --id B-001

# List all bugs
uv run scripts/aios_cli.py bug list --project-dir ./my-project
```

### `health` — Project Health Dashboard

```bash
uv run scripts/aios_cli.py health --project-dir ./my-project
uv run scripts/aios_cli.py health --project-dir ./my-project --output health.md
```

### `security-scan` — Security Analysis

```bash
uv run scripts/aios_cli.py security-scan --project-dir ./my-project
uv run scripts/aios_cli.py security-scan --project-dir ./my-project --output security.md
```

### `snapshot` — Save State Snapshot

```bash
uv run scripts/aios_cli.py snapshot --project-dir ./my-project
uv run scripts/aios_cli.py snapshot --project-dir ./my-project --name "pre-refactor"
```

### `diff` — Compare Snapshots

```bash
uv run scripts/aios_cli.py diff --project-dir ./my-project --snapshot pre-refactor
```

### `update` — Record Changes

```bash
uv run scripts/aios_cli.py update \
  --project-dir ./my-project \
  --reason "Added JWT authentication" \
  --files "auth.py, middleware.py, config.py" \
  --added "jwt_utils.py" \
  --impact "All API endpoints now require Bearer token" \
  --author "Claude"
```

### `status` — Quick Status Check

```bash
uv run scripts/aios_cli.py status --project-dir ./my-project
```

### `workflow` — Implementation Workflow Checks

```bash
# Before starting work
uv run scripts/aios_cli.py workflow --project-dir ./my-project --phase pre

# After completing work
uv run scripts/aios_cli.py workflow --project-dir ./my-project --phase post
```

## Development Workflow

### Before Any Implementation

When the user asks you to implement something, follow this workflow:

1. **Run pre-check**: `uv run scripts/aios_cli.py workflow --phase pre --project-dir <dir>`
2. **Read CONTEXT.md**: Get the compressed project understanding
3. **Read DECISIONS.md**: Check for relevant past decisions
4. **Read SECURITY.md**: Note security requirements
5. **Check TASKS.md**: See if there's a related task

### After Any Implementation

1. **Update changelog**: `uv run scripts/aios_cli.py update --reason "..." --files "..." --project-dir <dir>`
2. **Complete tasks**: `uv run scripts/aios_cli.py task complete --id T-XXX --project-dir <dir>`
3. **Re-scan if significant**: `uv run scripts/aios_cli.py scan --project-dir <dir>`
4. **Rebuild context**: `uv run scripts/aios_cli.py build-context --project-dir <dir>`
5. **Run post-check**: `uv run scripts/aios_cli.py workflow --phase post --project-dir <dir>`

## Agent Profiles

The `.aios/AGENTS/` directory contains 8 specialized agent profiles:

| Agent | Focus Area |
|---|---|
| `architect.md` | System architecture, scalability, design patterns |
| `frontend.md` | UI/UX, accessibility, components |
| `backend.md` | APIs, services, business logic |
| `database.md` | Schema design, relationships, performance |
| `security.md` | RBAC, encryption, compliance |
| `devops.md` | CI/CD, infrastructure, monitoring |
| `qa.md` | Testing, validation, regression |
| `product.md` | Features, roadmap, prioritization |

Each agent profile specifies:
- **Responsibilities** — what the agent handles
- **Required reading** — which `.aios/` documents to read first
- **Rules & constraints** — mandatory behavior rules
- **Workflow** — step-by-step implementation process

## Generated .aios/ Structure

```
.aios/
├── PROJECT.md              # Project overview & stats
├── CURRENT_STATE.md         # Current development state
├── ARCHITECTURE.md          # System architecture
├── DATABASE.md              # Database schemas & models
├── FEATURES.md              # Feature tracking
├── MODULES.md               # Module documentation
├── API.md                   # API endpoints & docs
├── SECURITY.md              # Security analysis & score
├── ROLES_PERMISSIONS.md     # RBAC documentation
├── TASKS.md                 # Task tracker
├── BUGS.md                  # Bug tracker
├── TESTS.md                 # Test status
├── CHANGELOG.md             # Change history
├── DECISIONS.md             # Technical decisions log
├── ROADMAP.md               # Future roadmap
├── TIMELINE.md              # Project timeline
├── DEPENDENCIES.md          # Dependency tracking
├── AI_RULES.md              # AI behavior rules
├── AI_HISTORY.md            # AI action history
├── CONTEXT.md               # Compressed AI context (<15K tokens)
├── AGENTS/
│   ├── architect.md
│   ├── frontend.md
│   ├── backend.md
│   ├── database.md
│   ├── security.md
│   ├── devops.md
│   ├── qa.md
│   └── product.md
└── snapshots/
    └── (timestamped snapshots)
```

## Common Mistakes

1. **Running `scan` before `init`** — Always run `init` first to create the
   `.aios/` directory structure. The `scan` command requires it to exist.

2. **Forgetting to rebuild context after changes** — After significant
   project changes, always run `build-context` to update the compressed
   context. Stale context leads to incorrect AI implementations.

3. **Not recording decisions** — When making architectural choices, always
   use the `decision` command. Future AI sessions rely on `DECISIONS.md`
   to avoid contradicting past choices.
