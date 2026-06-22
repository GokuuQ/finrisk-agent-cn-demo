from __future__ import annotations

import pytest

from finrisk_agent.sql_tools import SQLGuardError, validate_readonly_sql


def test_select_is_allowed() -> None:
    validate_readonly_sql("SELECT * FROM applications LIMIT 10")


def test_mutation_is_blocked() -> None:
    with pytest.raises(SQLGuardError):
        validate_readonly_sql("DROP TABLE applications")


def test_multiple_statements_are_blocked() -> None:
    with pytest.raises(SQLGuardError):
        validate_readonly_sql("SELECT * FROM applications; SELECT * FROM loans")
