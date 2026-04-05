"""Unit tests for the logging system."""

import json
import logging
from io import StringIO
from unittest.mock import patch

from utils.logger import JSONFormatter, TextFormatter, get_logger, setup_logging


class TestJSONFormatter:
    """Test JSON log formatter."""

    def test_basic_log_format(self):
        """Test basic log record formatting as JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"
        record.module = "test_module"

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert "timestamp" in log_data

    def test_log_with_exception(self):
        """Test log formatting with exception information."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.funcName = "test_function"
        record.module = "test_module"

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["level"] == "ERROR"
        assert log_data["message"] == "Error occurred"
        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]
        assert "Test exception" in log_data["exception"]

    def test_log_with_extra_fields(self):
        """Test log formatting with extra custom fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Custom message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"
        record.module = "test_module"
        record.extra_fields = {"user_id": "123", "request_id": "abc-456"}

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["user_id"] == "123"
        assert log_data["request_id"] == "abc-456"


class TestTextFormatter:
    """Test text log formatter."""

    def test_basic_log_format(self):
        """Test basic log record formatting as text."""
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"
        record.module = "test_module"

        result = formatter.format(record)

        assert "INFO" in result
        assert "test.logger" in result
        assert "Test message" in result
        # Check for ANSI color codes
        assert "\033[" in result  # Color code present
        assert "\033[0m" in result  # Reset code present

    def test_log_levels_have_colors(self):
        """Test that different log levels have different colors."""
        formatter = TextFormatter()
        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        results = []
        for level, _level_name in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )
            record.funcName = "test"
            record.module = "test"
            results.append(formatter.format(record))

        # Each log level should produce different output (different colors)
        assert len(set(results)) == len(levels)

    def test_log_with_exception(self):
        """Test text formatting with exception information."""
        formatter = TextFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.funcName = "test_function"
        record.module = "test_module"

        result = formatter.format(record)

        assert "ERROR" in result
        assert "Error occurred" in result
        assert "ValueError" in result
        assert "Test exception" in result


class TestSetupLogging:
    """Test logging setup function."""

    def test_setup_logging_development(self, dev_config):
        """Test logging setup for development environment."""
        with patch("utils.logger.get_config", return_value=dev_config):
            setup_logging()

            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 1
            assert isinstance(root_logger.handlers[0], logging.StreamHandler)
            assert isinstance(root_logger.handlers[0].formatter, TextFormatter)
            assert root_logger.level == logging.DEBUG

    def test_setup_logging_production(self, prod_config):
        """Test logging setup for production environment."""
        with patch("utils.logger.get_config", return_value=prod_config):
            setup_logging()

            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 1
            assert isinstance(root_logger.handlers[0].formatter, JSONFormatter)
            assert root_logger.level == logging.WARNING  # Production uses WARNING level

    def test_setup_logging_custom_level(self, dev_config):
        """Test logging setup with custom log level."""
        with patch("utils.logger.get_config", return_value=dev_config):
            setup_logging(log_level="WARNING")

            root_logger = logging.getLogger()
            assert root_logger.level == logging.WARNING

    def test_setup_logging_clears_existing_handlers(self, dev_config):
        """Test that setup_logging clears existing handlers."""
        # Add a handler
        root_logger = logging.getLogger()
        existing_handler = logging.StreamHandler()
        root_logger.addHandler(existing_handler)

        initial_count = len(root_logger.handlers)
        assert initial_count >= 1

        with patch("utils.logger.get_config", return_value=dev_config):
            setup_logging()

        # Should have exactly 1 handler after setup
        assert len(root_logger.handlers) == 1
        assert existing_handler not in root_logger.handlers

    def test_third_party_logs_silenced(self, dev_config):
        """Test that third-party library logs are set to WARNING."""
        with patch("utils.logger.get_config", return_value=dev_config):
            setup_logging()

        # Check some third-party loggers
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("transformers").level == logging.WARNING


class TestGetLogger:
    """Test logger retrieval function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_same_name_returns_same_instance(self):
        """Test that get_logger returns the same instance for same name."""
        logger1 = get_logger("test.module")
        logger2 = get_logger("test.module")
        assert logger1 is logger2


class TestLoggingIntegration:
    """Integration tests for the logging system."""

    def test_json_logging_output(self, prod_config):
        """Test actual JSON log output."""
        with patch("utils.logger.get_config", return_value=prod_config):
            # Capture stdout
            stream = StringIO()
            handler = logging.StreamHandler(stream)
            handler.setFormatter(JSONFormatter())

            logger = logging.getLogger("test.integration")
            logger.handlers.clear()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("Integration test message")

            output = stream.getvalue()
            log_data = json.loads(output.strip())

            assert log_data["level"] == "INFO"
            assert log_data["message"] == "Integration test message"
            assert log_data["logger"] == "test.integration"

    def test_text_logging_output(self, dev_config):
        """Test actual text log output."""
        with patch("utils.logger.get_config", return_value=dev_config):
            # Capture stdout
            stream = StringIO()
            handler = logging.StreamHandler(stream)
            handler.setFormatter(TextFormatter())

            logger = logging.getLogger("test.integration")
            logger.handlers.clear()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("Integration test message")

            output = stream.getvalue()

            assert "INFO" in output
            assert "Integration test message" in output
            assert "test.integration" in output

    def test_logging_with_parameters(self, dev_config):
        """Test logging with message parameters."""
        with patch("utils.logger.get_config", return_value=dev_config):
            stream = StringIO()
            handler = logging.StreamHandler(stream)
            handler.setFormatter(TextFormatter())

            logger = logging.getLogger("test.params")
            logger.handlers.clear()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("User %s performed action %s", "john_doe", "login")

            output = stream.getvalue()
            assert "User john_doe performed action login" in output
