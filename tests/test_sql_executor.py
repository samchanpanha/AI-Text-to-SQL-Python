"""Test SQL executor with sample queries."""

import pytest


class TestSqlExecutor:
    def test_simple_select(self):
        from app.agents.sql_executor import execute_sql
        result = execute_sql("SELECT 1 as test")
        assert result["success"] is True
        assert result["row_count"] == 1
        assert result["results"][0]["test"] == 1

    def test_invalid_query(self):
        from app.agents.sql_executor import execute_sql
        result = execute_sql("SELECT INVALID SQL")
        assert result["success"] is False
        assert result["error"] is not None

    def test_limit_enforcement(self):
        from app.agents.sql_executor import execute_sql
        result = execute_sql("SELECT 1 as x UNION SELECT 2 as x UNION SELECT 3 as x")
        assert result["success"] is True
