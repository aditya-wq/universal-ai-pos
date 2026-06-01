"""
Database analyzer.
Detects SQL schemas, ORM models, migrations, and database patterns.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from .base import BaseAnalyzer


class DatabaseAnalyzer(BaseAnalyzer):
    """Analyzes database schemas, ORM models, and migration files."""

    @property
    def name(self) -> str:
        return "Database Analyzer"

    def analyze(self) -> Dict[str, Any]:
        tables: List[Dict[str, Any]] = []
        models: List[Dict[str, Any]] = []
        migrations: List[Dict[str, Any]] = []
        relationships: List[Dict[str, str]] = []
        indexes: List[Dict[str, str]] = []
        db_type: List[str] = []

        # 1. Scan SQL files
        sql_files = self.walk_files(extensions={".sql"})
        for fpath in sql_files:
            content = self.read_file(fpath)
            if not content:
                continue
            rel = self.get_relative_path(fpath)

            # Detect migration files
            if any(k in rel.lower() for k in ["migration", "migrate", "alembic", "flyway", "liquibase"]):
                migrations.append({"file": rel, "type": "sql"})

            # Extract CREATE TABLE
            for match in re.finditer(
                r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(\w+)[`\"\]]?\s*\((.*?)\);",
                content, re.IGNORECASE | re.DOTALL
            ):
                table_name = match.group(1)
                body = match.group(2)
                columns = self._parse_sql_columns(body)
                tables.append({
                    "name": table_name,
                    "columns": columns,
                    "file": rel,
                    "source": "sql",
                })

                # Extract foreign keys
                for fk_match in re.finditer(
                    r"FOREIGN\s+KEY\s*\([`\"\[]?(\w+)[`\"\]]?\)\s*REFERENCES\s+[`\"\[]?(\w+)[`\"\]]?",
                    body, re.IGNORECASE
                ):
                    relationships.append({
                        "from_table": table_name,
                        "from_column": fk_match.group(1),
                        "to_table": fk_match.group(2),
                    })

            # Extract CREATE INDEX
            for match in re.finditer(
                r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(\w+)[`\"\]]?\s+ON\s+[`\"\[]?(\w+)[`\"\]]?\s*\(([^)]+)\)",
                content, re.IGNORECASE
            ):
                indexes.append({
                    "name": match.group(1),
                    "table": match.group(2),
                    "columns": match.group(3).strip(),
                })

        # 2. Scan ORM models - Python (SQLAlchemy, Django)
        py_files = self.walk_files(extensions={".py"}, include_patterns=[r"model"])
        for fpath in py_files:
            content = self.read_file(fpath)
            if not content:
                continue
            rel = self.get_relative_path(fpath)

            # Django models
            for match in re.finditer(
                r"class\s+(\w+)\s*\(.*?models\.Model.*?\):\s*\n((?:\s+.+\n)*)",
                content
            ):
                model_name = match.group(1)
                body = match.group(2)
                fields = self._parse_django_fields(body)
                models.append({
                    "name": model_name,
                    "fields": fields,
                    "file": rel,
                    "orm": "django",
                })
                if "django" not in db_type:
                    db_type.append("django")

            # SQLAlchemy models
            for match in re.finditer(
                r"class\s+(\w+)\s*\(.*?(?:Base|Model|db\.Model).*?\):\s*\n((?:\s+.+\n)*)",
                content
            ):
                model_name = match.group(1)
                body = match.group(2)
                fields = self._parse_sqlalchemy_fields(body)
                if fields:  # Only add if we found Column definitions
                    models.append({
                        "name": model_name,
                        "fields": fields,
                        "file": rel,
                        "orm": "sqlalchemy",
                    })
                    if "sqlalchemy" not in db_type:
                        db_type.append("sqlalchemy")

        # 3. Scan Prisma schema
        prisma_files = self.walk_files(include_patterns=[r"schema\.prisma$"])
        for fpath in prisma_files:
            content = self.read_file(fpath)
            if not content:
                continue
            rel = self.get_relative_path(fpath)

            for match in re.finditer(
                r"model\s+(\w+)\s*\{([^}]+)\}",
                content
            ):
                model_name = match.group(1)
                body = match.group(2)
                fields = self._parse_prisma_fields(body)
                models.append({
                    "name": model_name,
                    "fields": fields,
                    "file": rel,
                    "orm": "prisma",
                })
                if "prisma" not in db_type:
                    db_type.append("prisma")

        # 4. Scan TypeORM entities
        ts_files = self.walk_files(extensions={".ts"}, include_patterns=[r"entity|model"])
        for fpath in ts_files:
            content = self.read_file(fpath)
            if not content:
                continue
            rel = self.get_relative_path(fpath)

            if "@Entity" in content:
                for match in re.finditer(r"class\s+(\w+)", content):
                    columns = re.findall(r"@Column[^)]*\)\s*(\w+)", content)
                    models.append({
                        "name": match.group(1),
                        "fields": [{"name": c, "type": "unknown"} for c in columns],
                        "file": rel,
                        "orm": "typeorm",
                    })
                    if "typeorm" not in db_type:
                        db_type.append("typeorm")

        # 5. Scan migration directories
        migration_patterns = [
            r"migrations?/", r"alembic/versions/", r"db/migrate/",
            r"flyway/", r"liquibase/", r"knex.*migrations/",
        ]
        all_files = self.walk_files()
        for fpath in all_files:
            rel = self.get_relative_path(fpath)
            if any(re.search(p, rel) for p in migration_patterns):
                if rel not in [m["file"] for m in migrations]:
                    migrations.append({"file": rel, "type": fpath.suffix})

        self.results = {
            "tables": tables,
            "models": models,
            "migrations": migrations[:50],
            "relationships": relationships,
            "indexes": indexes,
            "db_technologies": db_type,
            "total_tables": len(tables),
            "total_models": len(models),
            "total_migrations": len(migrations),
            "total_relationships": len(relationships),
        }
        return self.results

    def _parse_sql_columns(self, body: str) -> List[Dict[str, str]]:
        """Parse column definitions from CREATE TABLE body."""
        columns = []
        for line in body.split(","):
            line = line.strip()
            if not line or line.upper().startswith(("PRIMARY", "FOREIGN", "UNIQUE", "INDEX", "CONSTRAINT", "CHECK")):
                continue
            match = re.match(r"[`\"\[]?(\w+)[`\"\]]?\s+(\w+(?:\([^)]+\))?)", line)
            if match:
                columns.append({
                    "name": match.group(1),
                    "type": match.group(2),
                    "nullable": "NOT NULL" not in line.upper(),
                    "primary_key": "PRIMARY KEY" in line.upper(),
                })
        return columns

    def _parse_django_fields(self, body: str) -> List[Dict[str, str]]:
        """Parse Django model field definitions."""
        fields = []
        for match in re.finditer(r"(\w+)\s*=\s*models\.(\w+)\s*\(", body):
            fields.append({"name": match.group(1), "type": match.group(2)})
        return fields

    def _parse_sqlalchemy_fields(self, body: str) -> List[Dict[str, str]]:
        """Parse SQLAlchemy column definitions."""
        fields = []
        for match in re.finditer(r"(\w+)\s*=\s*(?:db\.)?Column\s*\(\s*(?:db\.)?(\w+)", body):
            fields.append({"name": match.group(1), "type": match.group(2)})
        return fields

    def _parse_prisma_fields(self, body: str) -> List[Dict[str, str]]:
        """Parse Prisma schema field definitions."""
        fields = []
        for line in body.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("@@"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                fields.append({"name": parts[0], "type": parts[1]})
        return fields
