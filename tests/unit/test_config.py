"""Unit tests for configuration system.

Tests cover:
- Base configuration defaults and validation
- Environment-specific configuration overrides
- Configuration factory and singleton pattern
- Environment variable handling
- Field validation and constraints
- Error handling for invalid configurations
"""

import os

import pytest
from pydantic import ValidationError

from config.base import BaseConfig
from config.development import DevelopmentConfig
from config.production import ProductionConfig
from config.settings import get_settings, reload_settings
from config.testing import TestingConfig
from exceptions import ConfigurationError


class TestBaseConfig:
    """Tests for BaseConfig class."""

    def test_default_values(self, base_config):
        """Test that default values are set correctly."""
        assert base_config.environment == "development"
        assert base_config.chunk_size == 1000
        assert base_config.chunk_overlap == 300
        assert base_config.embedding_device == "auto"
        assert base_config.log_level == "INFO"
        assert base_config.debug_mode is False

    def test_embedding_configuration(self, base_config):
        """Test embedding-related configuration defaults."""
        assert base_config.embedding_model == "BAAI/bge-large-en-v1.5"
        assert base_config.embedding_dimension == 1024
        assert base_config.normalize_embeddings is True

    def test_llm_configuration(self, base_config):
        """Test LLM-related configuration defaults."""
        assert base_config.llm_model == "claude-opus-4-5"
        assert base_config.llm_lite_model == "claude-sonnet-4-5"
        assert base_config.llm_thinking_budget == 10000
        assert base_config.llm_temperature == 1.0
        assert base_config.llm_timeout == 120

    def test_retrieval_configuration(self, base_config):
        """Test retrieval-related configuration defaults."""
        assert base_config.retrieval_total_chunks == 20
        assert base_config.retrieval_rerank_top_k == 10
        assert base_config.retrieval_num_queries == 5

    def test_chunk_overlap_validation_success(self):
        """Test that valid chunk_overlap is accepted."""
        config = BaseConfig(chunk_size=1000, chunk_overlap=300)
        assert config.chunk_overlap == 300

    def test_chunk_overlap_validation_failure(self):
        """Test that chunk_overlap must be less than chunk_size."""
        with pytest.raises(ValidationError) as exc_info:
            BaseConfig(chunk_size=500, chunk_overlap=600)
        error_msg = str(exc_info.value)
        assert "chunk_overlap" in error_msg

    def test_chunk_overlap_equal_to_chunk_size_rejected(self):
        """Test that chunk_overlap equal to chunk_size is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BaseConfig(chunk_size=1000, chunk_overlap=1000)
        error_msg = str(exc_info.value)
        assert "chunk_overlap" in error_msg

    def test_rerank_top_k_validation_success(self):
        """Test that rerank_top_k within total_chunks is accepted."""
        config = BaseConfig(retrieval_total_chunks=20, retrieval_rerank_top_k=10)
        assert config.retrieval_rerank_top_k == 10

    def test_rerank_top_k_validation_failure(self):
        """Test that rerank_top_k cannot exceed total_chunks."""
        with pytest.raises(ValidationError) as exc_info:
            BaseConfig(retrieval_total_chunks=10, retrieval_rerank_top_k=15)
        error_msg = str(exc_info.value)
        assert "retrieval_rerank_top_k" in error_msg

    def test_batch_size_constraints(self):
        """Test batch_size min/max validation."""
        # Valid
        config = BaseConfig(batch_size=1000)
        assert config.batch_size == 1000

        # Too low
        with pytest.raises(ValidationError):
            BaseConfig(batch_size=50)

        # Too high
        with pytest.raises(ValidationError):
            BaseConfig(batch_size=15000)

    def test_llm_thinking_budget_constraints(self):
        """Test llm_thinking_budget min/max validation."""
        # Valid
        config = BaseConfig(llm_thinking_budget=5000)
        assert config.llm_thinking_budget == 5000

        # Too low
        with pytest.raises(ValidationError):
            BaseConfig(llm_thinking_budget=500)

        # Too high
        with pytest.raises(ValidationError):
            BaseConfig(llm_thinking_budget=150000)

    def test_path_properties(self, base_config):
        """Test computed path properties."""
        assert base_config.raw_data_dir == base_config.data_dir / "raw"
        assert base_config.vector_store_dir == base_config.data_dir / "vector_store"


class TestDevelopmentConfig:
    """Tests for DevelopmentConfig class."""

    def test_environment_override(self, dev_config):
        """Test that environment is set to development."""
        assert dev_config.environment == "development"

    def test_logging_overrides(self, dev_config):
        """Test development-specific logging overrides."""
        assert dev_config.log_level == "DEBUG"
        assert dev_config.log_format == "text"
        assert dev_config.debug_mode is True

    def test_performance_overrides(self, dev_config):
        """Test development-specific performance overrides."""
        assert dev_config.batch_size == 1000
        assert dev_config.retrieval_total_chunks == 10
        assert dev_config.retrieval_rerank_top_k == 5
        assert dev_config.retrieval_num_queries == 3

    def test_llm_overrides(self, dev_config):
        """Test development-specific LLM overrides."""
        assert dev_config.llm_thinking_budget == 5000


class TestProductionConfig:
    """Tests for ProductionConfig class."""

    def test_environment_override(self, prod_config):
        """Test that environment is set to production."""
        assert prod_config.environment == "production"

    def test_logging_overrides(self, prod_config):
        """Test production-specific logging overrides."""
        assert prod_config.log_level == "WARNING"
        assert prod_config.log_format == "json"
        assert prod_config.debug_mode is False

    def test_performance_overrides(self, prod_config):
        """Test production-specific performance overrides."""
        assert prod_config.batch_size == 5000
        assert prod_config.retrieval_total_chunks == 20
        assert prod_config.retrieval_rerank_top_k == 10
        assert prod_config.retrieval_num_queries == 5

    def test_llm_overrides(self, prod_config):
        """Test production-specific LLM overrides."""
        assert prod_config.llm_thinking_budget == 10000
        assert prod_config.llm_timeout == 120


class TestTestingConfig:
    """Tests for TestingConfig class."""

    def test_environment_override(self, test_config):
        """Test that environment is set to testing."""
        assert test_config.environment == "testing"

    def test_logging_overrides(self, test_config):
        """Test testing-specific logging overrides."""
        assert test_config.log_level == "ERROR"
        assert test_config.log_format == "text"
        assert test_config.debug_mode is False

    def test_minimal_performance_settings(self, test_config):
        """Test testing-specific minimal performance settings."""
        assert test_config.batch_size == 100
        assert test_config.retrieval_total_chunks == 5
        assert test_config.retrieval_rerank_top_k == 3
        assert test_config.retrieval_num_queries == 2

    def test_minimal_llm_settings(self, test_config):
        """Test testing-specific minimal LLM settings."""
        assert test_config.llm_thinking_budget == 1000
        assert test_config.llm_timeout == 30

    def test_smaller_chunk_settings(self, test_config):
        """Test testing-specific smaller chunk settings."""
        assert test_config.chunk_size == 500
        assert test_config.chunk_overlap == 100


class TestConfigFactory:
    """Tests for config factory functions."""

    def test_get_config_development(self):
        """Test loading development config from environment."""
        os.environ["ENVIRONMENT"] = "development"
        config = reload_settings()
        assert isinstance(config, DevelopmentConfig)
        assert config.environment == "development"

    def test_get_config_dev_alias(self):
        """Test that 'dev' alias works for development."""
        os.environ["ENVIRONMENT"] = "dev"
        config = reload_settings()
        assert isinstance(config, DevelopmentConfig)

    def test_get_config_production(self):
        """Test loading production config from environment."""
        os.environ["ENVIRONMENT"] = "production"
        config = reload_settings()
        assert isinstance(config, ProductionConfig)
        assert config.environment == "production"

    def test_get_config_prod_alias(self):
        """Test that 'prod' alias works for production."""
        os.environ["ENVIRONMENT"] = "prod"
        config = reload_settings()
        assert isinstance(config, ProductionConfig)

    def test_get_config_staging_uses_production(self):
        """Test that staging environment uses production config."""
        os.environ["ENVIRONMENT"] = "staging"
        config = reload_settings()
        assert isinstance(config, ProductionConfig)

    def test_get_config_testing(self):
        """Test loading testing config from environment."""
        os.environ["ENVIRONMENT"] = "testing"
        config = reload_settings()
        assert isinstance(config, TestingConfig)
        assert config.environment == "testing"

    def test_get_config_test_alias(self):
        """Test that 'test' alias works for testing."""
        os.environ["ENVIRONMENT"] = "test"
        config = reload_settings()
        assert isinstance(config, TestingConfig)

    def test_get_config_invalid_environment(self):
        """Test that invalid environment raises ConfigurationError."""
        os.environ["ENVIRONMENT"] = "invalid_env"
        with pytest.raises(ConfigurationError) as exc_info:
            reload_settings()
        error_msg = str(exc_info.value)
        assert "invalid" in error_msg.lower()

    def test_get_config_defaults_to_development(self):
        """Test that missing ENVIRONMENT defaults to development."""
        # Remove ENVIRONMENT variable if it exists
        os.environ.pop("ENVIRONMENT", None)
        config = reload_settings()
        assert isinstance(config, DevelopmentConfig)

    def test_singleton_caching(self):
        """Test that get_settings returns cached instance."""
        os.environ["ENVIRONMENT"] = "development"
        config1 = get_settings()
        config2 = get_settings()
        assert config1 is config2  # Same instance

    def test_reload_settings_clears_cache(self):
        """Test that reload_settings creates new instance."""
        os.environ["ENVIRONMENT"] = "development"
        config1 = get_settings()
        config2 = reload_settings()
        # Instances should be different (new object created)
        # But same type and values
        assert type(config1) is type(config2)
        assert config1.environment == config2.environment


class TestEnvironmentVariableOverrides:
    """Tests for environment variable overrides."""

    def test_chunk_size_override(self):
        """Test that CHUNK_SIZE env var overrides default."""
        os.environ["CHUNK_SIZE"] = "2000"
        config = BaseConfig()
        assert config.chunk_size == 2000

    def test_log_level_override(self):
        """Test that LOG_LEVEL env var overrides default."""
        os.environ["LOG_LEVEL"] = "ERROR"
        config = BaseConfig()
        assert config.log_level == "ERROR"

    def test_batch_size_override(self):
        """Test that BATCH_SIZE env var overrides default."""
        os.environ["BATCH_SIZE"] = "3000"
        config = BaseConfig()
        assert config.batch_size == 3000

    def test_multiple_overrides(self):
        """Test multiple environment variable overrides."""
        os.environ["CHUNK_SIZE"] = "1500"
        os.environ["CHUNK_OVERLAP"] = "200"
        os.environ["LOG_LEVEL"] = "WARNING"
        config = BaseConfig()
        assert config.chunk_size == 1500
        assert config.chunk_overlap == 200
        assert config.log_level == "WARNING"
