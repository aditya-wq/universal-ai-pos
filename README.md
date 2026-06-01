# AIOS — Universal AI Project Operating System

AIOS (AI Project Operating System) is a reusable, project-agnostic persistent memory layer that can be installed into any software codebase.

The goal of AIOS is to create a lightweight, standardized brain (`.aios/` directory) that allows any AI model (ChatGPT, Claude, Gemini, Cursor, Windsurf, GitHub Copilot, Antigravity IDE, etc.) to instantly understand a project's architecture, APIs, databases, decisions, tasks, and state without requiring the entire codebase to be uploaded or repeatedly parsed.

It dramatically reduces token consumption while ensuring consistent, high-accuracy AI pair programming and updates.

---

## 🚀 Key Features

*   **Zero Dependencies**: Written purely in Python standard library. Portable and immediately runnable in any environment.
*   **Universal Analysis Engine**: AST-based parsing (Python) and advanced regex-based scanning (JavaScript/TypeScript, database schemas, API routers, Docker, Git history, and security contexts).
*   **Context Compression**: Translates vast projects into a single, high-fidelity `<15K` token `CONTEXT.md` file optimized for AI ingestion.
*   **Security Guardrails**: Automated scanning for hardcoded API keys/secrets, encryption usage, and missing security modules, providing a 0–100 security score.
*   **Ready-to-Use Agent Framework**: 8 preconfigured markdown role profiles (`AGENTS/`) mapping database engineers, architects, backend/frontend devs, DevOps, product managers, and QA.
*   **Change Tracking & State Snapshots**: Take point-in-time state snapshots, calculate project diffs, and manage an structured changelog automatically.

---

## 📦 Installation & Quick Start

Clone this repository and run the CLI directly. It supports Python 3.8+.

### 1. Initialize AIOS in your project:
```bash
python path/to/aios/scripts/aios_cli.py init --project-dir ./my-project
```

### 2. Scan and populate project artifacts:
```bash
python path/to/aios/scripts/aios_cli.py scan --project-dir ./my-project
```

### 3. Build the compressed context file:
```bash
python path/to/aios/scripts/aios_cli.py build-context --project-dir ./my-project
```

### 4. Paste Context to your AI session:
Copy the generated `.aios/CONTEXT.md` and paste it at the beginning of any AI chat session. Your model will instantly understand your codebase!

---

## 🛠️ CLI Subcommands

| Subcommand | Description |
| :--- | :--- |
| `init` | Create `.aios/` folder structure, templates, and agent profiles. |
| `scan` | Analyze codebase components, schemas, routes, git log, and update docs. |
| `build-context` | Generate the compressed context file `CONTEXT.md`. |
| `status` | Display population state of all AIOS tracking documents. |
| `health` | Build a project readiness health scorecard (0-100 score). |
| `security-scan` | Verify project secrets exposure and check security standards. |
| `task` | Manage project TODOs (`add`, `list`, `complete`) directly in markdown. |
| `bug` | Manage defects (`add`, `list`, `resolve`). |
| `decision` | Log architectural/technical decisions in `DECISIONS.md`. |
| `snapshot` | Create a timestamped, structured state snapshot of `.aios/`. |
| `diff` | Compare current project status with a previous snapshot. |
| `update` | Manually record changes, modified files, and impact. |
| `workflow` | Run pre/post implementation checklists for AI execution. |

---

## 📐 AI Behavior Rules

Inside `.aios/AI_RULES.md`, developer rules are specified. A summary of the workflows:

### Before Implementation:
1. Run `workflow --phase pre` to check setup status.
2. Read `.aios/CONTEXT.md` to get project-wide context.
3. Consult `.aios/DECISIONS.md` to ensure your plan aligns with past tech choices.

### After Implementation:
1. Document modifications in `.aios/CHANGELOG.md` using `update`.
2. Close completed items using `task complete --id T-XXX`.
3. Refresh the context using `scan` followed by `build-context`.
4. Validate changes against checklists using `workflow --phase post`.

---

## 📁 Repository Structure

```
aios/
├── SKILL.md                 # Main instructions for Antigravity IDE Integration
├── README.md                 # Repository setup and quick start
├── .gitignore               # Ignored files (pycache, local .aios/ snapshots)
└── scripts/
    ├── aios_cli.py          # Central CLI entrypoint and subcommand parsing
    ├── analyzers/           # Static analyzer modules
    │   ├── __init__.py
    │   ├── base.py          # Base abstract class with walker logic
    │   ├── python_analyzer.py
    │   ├── javascript_analyzer.py
    │   ├── database_analyzer.py
    │   ├── api_analyzer.py
    │   ├── infrastructure_analyzer.py
    │   ├── git_analyzer.py
    │   ├── security_analyzer.py
    │   └── generic_analyzer.py
    └── generators/          # Markdown document layout generators
        ├── __init__.py
        ├── project_generator.py
        ├── architecture_generator.py
        ├── database_generator.py
        ├── api_generator.py
        ├── security_generator.py
        ├── health_generator.py
        ├── agent_generator.py
        └── context_generator.py
```
