"""Production-grade logging system with JSON and text formatters.

This module provides structured logging for the RAG system with:
- JSON formatting for production (machine-parseable)
- Text formatting for development (human-readable)
- Configurable log levels per environment
- Third-party library log silencing
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from config.settings import get_config


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments.

    Outputs structured logs that are easily parsed by log aggregation
    tools like ELK, Splunk, CloudWatch, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development environments.

    Provides colorized, readable logs for local development.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as colored text.

        Args:
            record: Log record to format

        Returns:
            Formatted log string with colors
        """
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        log_msg = (
            f"{color}[{timestamp}] {record.levelname:8s}{self.RESET} "
            f"{record.name} - {record.getMessage()}"
        )

        # Add exception info if present
        if record.exc_info:
            log_msg += f"\n{self.formatException(record.exc_info)}"

        return log_msg


def setup_logging(log_level: str | None = None) -> None:
    """Configure logging for the application.

    Sets up appropriate formatter based on environment:
    - Production: JSON formatter
    - Development/Testing: Text formatter

    Also silences noisy third-party libraries.

    Args:
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, uses environment-specific default.
    """
    config = get_config()

    # Determine log level
    if log_level is None:
        log_level = config.log_level

    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Choose formatter based on environment
    formatter: JSONFormatter | TextFormatter
    if config.environment == "production":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(numeric_level)

    # Silence noisy third-party libraries
    _silence_third_party_logs()

    # Log startup message
    logger = get_logger(__name__)
    logger.info(f"Logging initialized for {config.environment} environment at {log_level} level")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def _silence_third_party_logs() -> None:
    """Reduce noise from third-party library logs.

    Sets third-party loggers to WARNING level to avoid cluttering
    application logs with library debug information.
    """
    noisy_loggers = [
        "httpx",
        "httpcore",
        "urllib3",
        "sentence_transformers",
        "transformers",
        "torch",
        "openai",
        "chromadb",
        "qdrant_client",
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
