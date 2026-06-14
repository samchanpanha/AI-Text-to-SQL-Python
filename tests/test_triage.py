"""Test triage agent classification."""

import pytest


class TestTriage:
    def test_data_question(self):
        from app.agents.triage import triage_question
        result = triage_question("What were total sales last month?")
        assert result.get("category") == "data"

    def test_general_question(self):
        from app.agents.triage import triage_question
        result = triage_question("Hello, how are you?")
        assert result.get("category") == "general"

    def test_out_of_scope(self):
        from app.agents.triage import triage_question
        result = triage_question("What is the meaning of life?")
        assert result.get("category") in ("general", "out_of_scope")
