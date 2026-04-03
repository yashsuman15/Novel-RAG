"""Secrets management for RAG application."""

from typing import Optional
from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from exceptions import SecretsError


class Secrets(BaseSettings):
    """
    Centralized secrets management.
    
    Loads secrets from environment variables or .env file.
    Secrets are validated at startup and kept secure using SecretStr.
    
    Example:
        >>> secrets = get_secrets()
        >>> api_key = secrets.get_api_key()
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    anthropic_api_key: SecretStr = Field(
        ..., 
        description="Anthropic API key for Claude models"
    )
    
    def get_api_key(self) -> str:
        """
        Safely retrieve API key as string.
        
        Returns:
            API key as plain string
        """
        return self.anthropic_api_key.get_secret_value()
    
    @classmethod
    def load(cls) -> "Secrets":
        """
        Load secrets with validation.
        
        Returns:
            Validated Secrets instance
            
        Raises:
            SecretsError: If secrets cannot be loaded or validated
        """
        try:
            return cls()
        except Exception as e:
            raise SecretsError(
                "Failed to load secrets. Ensure .env file exists with required variables. "
                f"See .env.example for template. Error: {e}",
                details={"error": str(e), "error_type": type(e).__name__}
            ) from e


# Singleton instance
_secrets: Optional[Secrets] = None


def get_secrets() -> Secrets:
    """
    Get or create secrets singleton.
    
    Returns:
        Secrets instance (cached after first call)
        
    Example:
        >>> secrets = get_secrets()
        >>> api_key = secrets.get_api_key()
    """
    global _secrets
    if _secrets is None:
        _secrets = Secrets.load()
    return _secrets


def reload_secrets() -> Secrets:
    """
    Force reload secrets (useful for tests).
    
    Returns:
        Freshly loaded Secrets instance
    """
    global _secrets
    _secrets = None
    return get_secrets()