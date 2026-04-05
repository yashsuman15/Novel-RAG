"""Testing environment configuration."""

from typing import Literal

from config.base import BaseConfig


class TestingConfig(BaseConfig):
    """
    Testing-specific configuration overrides.

    Optimized for:
    - Fast test execution
    - Minimal resource usage
    - Deterministic behavior
    - Quick feedback loops
    - Reduced API costs during testing
    """

    environment: Literal["testing"] = "testing"

    # =========================================================================
    # Logging & Debugging
    # =========================================================================

    # Quiet logging during tests - only show errors
    log_level: str = "ERROR"
    log_format: Literal["json", "text"] = "text"  # Human-readable for debugging

    # No debug mode during tests (cleaner output)
    debug_mode: bool = False

    # =========================================================================
    # Performance - Minimal for Speed
    # =========================================================================

    # Small batches for fast test execution
    batch_size: int = 100

    # =========================================================================
    # Retrieval Configuration - Minimal
    # =========================================================================

    # Minimal retrieval for fast tests
    retrieval_total_chunks: int = 5
    retrieval_rerank_top_k: int = 3
    retrieval_num_queries: int = 2

    # =========================================================================
    # LLM Configuration - Minimal
    # =========================================================================

    # Low thinking budget for fast tests
    llm_thinking_budget: int = 1000

    # Short timeout for tests
    llm_timeout: int = 30

    # =========================================================================
    # Text Splitting - Smaller for Speed
    # =========================================================================

    # Smaller chunks for faster test execution
    chunk_size: int = 500
    chunk_overlap: int = 100
