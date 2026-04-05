"""Production environment configuration."""

from typing import Literal

from config.base import BaseConfig


class ProductionConfig(BaseConfig):
    """
    Production-specific configuration overrides.

    Optimized for:
    - High performance and throughput
    - Structured logging for observability
    - Security and stability
    - Longer timeouts for reliability
    - Aggressive retrieval for quality
    """

    environment: Literal["production"] = "production"

    # =========================================================================
    # Logging & Debugging
    # =========================================================================

    # Production logging - structured JSON for log aggregation
    log_level: str = "WARNING"
    log_format: Literal["json", "text"] = "json"  # Structured logs for parsing

    # Disable debug features in production
    debug_mode: bool = False

    # =========================================================================
    # Performance Optimization
    # =========================================================================

    # Larger batches for better throughput
    batch_size: int = 5000

    # =========================================================================
    # Retrieval Configuration
    # =========================================================================

    # Aggressive retrieval for maximum quality
    retrieval_total_chunks: int = 20
    retrieval_rerank_top_k: int = 10
    retrieval_num_queries: int = 5

    # =========================================================================
    # LLM Configuration
    # =========================================================================

    # Full thinking budget for best answers
    llm_thinking_budget: int = 10000

    # Longer timeout for production reliability
    llm_timeout: int = 120

    # =========================================================================
    # Text Splitting
    # =========================================================================

    # Standard chunk size for production
    chunk_size: int = 1000
    chunk_overlap: int = 300
