"""Pytest configuration and shared fixtures.

This module provides fixtures that are automatically available to all tests.
Fixtures include configuration instances, sample data, and test utilities.
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from config.base import BaseConfig
from config.development import DevelopmentConfig
from config.production import ProductionConfig
from config.testing import TestingConfig


@pytest.fixture(autouse=True)
def clean_environment() -> Generator[None, None, None]:
    """Clean environment variables before and after each test.

    This fixture runs automatically for every test, ensuring environment
    variable isolation. It saves the original environment, allows the test
    to run, then restores the original state.

    Yields:
        None
    """
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def base_config() -> BaseConfig:
    """Provide a base configuration instance.

    Returns:
        BaseConfig instance with default values
    """
    return BaseConfig(_env_file=None)


@pytest.fixture
def dev_config() -> DevelopmentConfig:
    """Provide a development configuration instance.

    Returns:
        DevelopmentConfig instance with development overrides
    """
    return DevelopmentConfig(_env_file=None)


@pytest.fixture
def prod_config() -> ProductionConfig:
    """Provide a production configuration instance.

    Returns:
        ProductionConfig instance with production overrides
    """
    return ProductionConfig(_env_file=None)


@pytest.fixture
def test_config() -> TestingConfig:
    """Provide a testing configuration instance.

    Returns:
        TestingConfig instance with testing overrides
    """
    return TestingConfig(_env_file=None)


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test data.

    Creates a temporary directory that is automatically cleaned up
    after the test completes.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_query() -> str:
    """Provide a sample valid query.

    Returns:
        A valid query string for testing
    """
    return "Who is Rudeus Greyrat?"


@pytest.fixture
def sample_queries() -> list[str]:
    """Provide multiple sample queries.

    Returns:
        List of valid query strings for testing
    """
    return [
        "Who is Rudeus Greyrat?",
        "What is the Demon Continent?",
        "Explain the magic system in Mushoku Tensei",
        "Who are the Seven Great Powers?",
        "What happened to Paul Greyrat?",
    ]


@pytest.fixture
def sample_xss_queries() -> list[str]:
    """Provide sample XSS injection attempts for security testing.

    Returns:
        List of malicious query strings that should be rejected
    """
    return [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img onerror='alert(1)' src='x'>",
        "<svg onload=alert(1)>",
        "' onmouseover='alert(1)'",
    ]


@pytest.fixture
def sample_documents() -> list[str]:
    """Provide sample document content for testing.

    Returns:
        List of sample document text chunks
    """
    return [
        "Rudeus Greyrat is the protagonist of Mushoku Tensei.",
        "The Demon Continent is one of the major regions in the world.",
        "Magic in this world is divided into three main categories: Attack, Healing, and Summoning.",
        "The Seven Great Powers are the strongest individuals in the world.",
    ]


@pytest.fixture
def config_with_env(monkeypatch) -> Generator[None, None, None]:
    """Set up environment variables for config testing.

    Uses pytest's monkeypatch fixture to safely modify environment
    variables during tests.

    Args:
        monkeypatch: pytest's monkeypatch fixture

    Yields:
        None
    """
    # Example environment variables
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CHUNK_SIZE", "2000")
    yield
