"""Development environment configuration."""

from config.base import BaseConfig
from pydantic import Field


class DevelopmentConfig(BaseConfig):
    """
    Development-specific configuration overrides.
    
    Optimized for:
    - Fast iteration
    - Verbose debugging
    - Smaller datasets
    - Less aggressive retrieval
    """
    
    environment: str = "development"
    
    # More verbose logging for development
    log_level: str = "DEBUG"
    log_format: str = "text"  # Human-readable logs
    
    # Smaller batches for faster iteration
    batch_size: int = 1000
    
    # Less aggressive retrieval for testing
    retrieval_total_chunks: int = 10
    retrieval_rerank_top_k: int = 5
    retrieval_num_queries: int = 3
    
    # Lower thinking budget for faster responses
    llm_thinking_budget: int = 5000
    
    # Enable debug features
    debug_mode: bool = True