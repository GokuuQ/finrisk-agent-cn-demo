from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_TABLES = {
    "customers",
    "applications",
    "loans",
    "monthly_performance",
    "strategy_events",
}


class SQLGuardError(ValueError):
    pass


def validate_readonly_sql(sql: str) -> None:
    normalized = " ".join(sql.strip().lower().split())
    blocked = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "create ",
        "attach ",
        "detach ",
        "pragma ",
        "vacuum ",
        "replace ",
    ]
    if not normalized.startswith("select"):
        raise SQLGuardError("Only SELECT statements are allowed.")
    if ";" in normalized[:-1]:
        raise SQLGuardError("Multiple SQL statements are not allowed.")
    if any(token in normalized for token in blocked):
        raise SQLGuardError("The SQL contains a blocked operation.")


@dataclass
class SQLResult:
    columns: list[str]
    rows: list[dict[str, Any]]


@dataclass
class SQLTools:
    db_path: str
    max_rows: int = 200

    def execute(self, sql: str) -> SQLResult:
        validate_readonly_sql(sql)
        db_file = Path(self.db_path)
        if not db_file.exists():
            raise FileNotFoundError(
                f"Database not found: {db_file}. Run scripts/generate_demo_data.py first."
            )

        limited_sql = sql.strip().rstrip(";")
        if " limit " not in limited_sql.lower():
            limited_sql = f"{limited_sql} LIMIT {self.max_rows}"

        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(limited_sql).fetchall()

        columns = list(rows[0].keys()) if rows else []
        return SQLResult(columns=columns, rows=[dict(row) for row in rows])

    def schema_summary(self) -> str:
        with sqlite3.connect(self.db_path) as conn:
            parts: list[str] = []
            for table in sorted(ALLOWED_TABLES):
                columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
                col_text = ", ".join(f"{col[1]} {col[2]}" for col in columns)
                parts.append(f"{table}({col_text})")
        return "\n".join(parts)
