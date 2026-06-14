"""Test logging module components."""

import json
import logging
import io


class TestJsonFormatter:
    def test_json_format(self):
        from app.logging.formatter import JsonFormatter

        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/app/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["module"] == "test.py"
        assert data["line"] == 42

    def test_json_format_with_extras(self):
        from app.logging.formatter import JsonFormatter

        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/app/test.py",
            lineno=10,
            msg="Error: %d",
            args=(500,),
            exc_info=None,
        )
        record.request_id = "abc123"
        record.duration_ms = 150
        record.status_code = 500

        output = formatter.format(record)
        data = json.loads(output)

        assert data["request_id"] == "abc123"
        assert data["duration_ms"] == 150
        assert data["status_code"] == 500
        assert data["message"] == "Error: 500"

    def test_get_logger(self):
        from app.logging.config import get_logger

        logger = get_logger("test")
        assert logger.name == "app.test"


class TestLlmLogger:
    def test_log_llm_call(self):
        from app.logging.llm_logger import log_llm_call

        # Should not raise
        log_llm_call(
            model="gpt-4o",
            system_prompt="You are a helpful assistant",
            user_prompt="What is SQL?",
            response="SQL is a query language.",
            duration_ms=500,
            success=True,
            tokens_prompt=50,
            tokens_completion=20,
            request_id="test-123",
        )

    def test_log_llm_call_failure(self):
        from app.logging.llm_logger import log_llm_call

        log_llm_call(
            model="gpt-4o",
            system_prompt="",
            user_prompt="test",
            response="",
            duration_ms=100,
            success=False,
            error_message="API timeout",
        )


class TestLogCleanup:
    def test_cleanup_signature(self):
        from app.logging.cleanup import cleanup_logs

        result = cleanup_logs(days=365)
        assert isinstance(result, dict)
        assert "audit_deleted" in result
        assert "llm_deleted" in result
        assert "task_deleted" in result
