"""
Configuration management for RAG application.

This module provides centralized configuration management with:
- Environment-based configuration (dev/staging/production)
- Validation using Pydantic
- Type safety
- Secrets management
- Easy testing

Usage:
    Basic usage:
    >>> from config import get_settings, get_secrets
    >>> 
    >>> settings = get_settings()
    >>> secrets = get_secrets()
    >>> 
    >>> # Access configuration
    >>> chunk_size = settings.chunk_size
    >>> api_key = secrets.get_api_key()
    
    Environment switching:
    >>> import os
    >>> os.environ["ENVIRONMENT"] = "production"
    >>> from config import reload_settings
    >>> 
    >>> settings = reload_settings()
    >>> print(settings.environment)  # "production"

Available exports:
    - get_settings(): Get current configuration (singleton)
    - reload_settings(): Force reload configuration
    - get_secrets(): Get secrets manager (singleton)
"""

from config.settings import get_settings, reload_settings
from config.secrets import get_secrets

__all__ = [
    "get_settings",
    "reload_settings", 
    "get_secrets",
]