"""Configuration factory and settings management."""

import os

from config.base import BaseConfig
from config.development import DevelopmentConfig

# from config.production import ProductionConfig
# from config.testing import TestingConfig
from exceptions import ConfigurationError

ConfigType = DevelopmentConfig | BaseConfig


def get_config() -> ConfigType:
    """
    Load configuration based on ENVIRONMENT variable.

    Environment variable priority:
    1. ENVIRONMENT (e.g., "production", "development")
    2. Default to "development"

    Returns:
        Configuration instance for current environment

    Raises:
        ConfigurationError: If ENVIRONMENT is invalid

    Example:
        >>> import os
        >>> os.environ["ENVIRONMENT"] = "production"
        >>> config = get_config()
        >>> print(config.environment)
        production
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    config_map = {
        "development": DevelopmentConfig,
        "dev": DevelopmentConfig,
        # "production": ProductionConfig,
        # "prod": ProductionConfig,
        # "staging": ProductionConfig,  # Use production config for staging
        # "stage": ProductionConfig,
        # "testing": TestingConfig,
        # "test": TestingConfig,
    }

    config_class = config_map.get(env)
    if not config_class:
        raise ConfigurationError(
            f"Invalid ENVIRONMENT: '{env}'. " f"Must be one of: {list(set(config_map.keys()))}",
            details={"environment": env, "valid_options": list(set(config_map.keys()))},
        )

    try:
        return config_class()
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load {env} configuration", details={"environment": env, "error": str(e)}
        ) from e


# Singleton instance
_config: ConfigType | None = None


def get_settings() -> ConfigType:
    """
    Get or create settings singleton.

    The configuration is cached after first load for performance.
    Use reload_settings() to force reload.

    Returns:
        Cached configuration instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.chunk_size)
        1000
    """
    global _config
    if _config is None:
        _config = get_config()
    return _config


def reload_settings() -> ConfigType:
    """
    Force reload settings (useful for tests).

    Clears the cached configuration and loads fresh from environment.

    Returns:
        Freshly loaded configuration instance

    Example:
        >>> import os
        >>> os.environ["ENVIRONMENT"] = "testing"
        >>> config = reload_settings()  # Forces reload
        >>> print(config.environment)
        testing
    """
    global _config
    _config = None
    return get_settings()
