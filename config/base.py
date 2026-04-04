"""Base configuration with all default settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """
    Base configuration shared across all environments.

    All settings have sensible defaults and can be overridden via:
    1. Environment variables (highest priority)
    2. .env file
    3. Environment-specific config classes
    4. These defaults (lowest priority)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True,  # Validate on attribute changes
    )

    # =========================================================================
    # Environment
    # =========================================================================

    environment: Literal[
        "development",
        # "staging", "production"
    ] = Field(default="development", description="Runtime environment")

    # =========================================================================
    # Paths
    # =========================================================================

    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent, description="Project root directory"
    )

    data_dir: Path = Field(
        default=Path("data"), description="Data directory for PDFs and vector store"
    )

    @property
    def raw_data_dir(self) -> Path:
        """Directory containing raw PDF files."""
        return self.data_dir / "raw"

    @property
    def vector_store_dir(self) -> Path:
        """Directory for ChromaDB vector store."""
        return self.data_dir / "vector_store"

    # =========================================================================
    # Vector Store Configuration
    # =========================================================================

    vector_store_collection: str = Field(
        default="rag_collection", description="ChromaDB collection name"
    )

    batch_size: int = Field(
        default=5000, ge=100, le=10000, description="Batch size for vector store insertions"
    )

    # =========================================================================
    # Embedding Configuration
    # =========================================================================

    embedding_model: str = Field(
        default="BAAI/bge-large-en-v1.5", description="HuggingFace embedding model identifier"
    )

    embedding_dimension: int = Field(default=1024, description="Embedding vector dimension")

    embedding_device: Literal["cuda", "cpu", "auto"] = Field(
        default="auto",
        description="Device for embedding computation (auto = detect CUDA, fallback to CPU)",
    )

    normalize_embeddings: bool = Field(
        default=True, description="Normalize embeddings to unit length"
    )

    # =========================================================================
    # Reranker Configuration
    # =========================================================================

    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model for reranking",
    )

    # =========================================================================
    # Text Splitting Configuration
    # =========================================================================

    chunk_size: int = Field(default=1000, ge=100, le=5000, description="Characters per chunk")

    chunk_overlap: int = Field(
        default=300, ge=0, le=1000, description="Character overlap between chunks"
    )

    text_separators: list[str] = Field(
        default=["\n\n", "\n", ". ", " ", ""],
        description="Text splitting separators in priority order",
    )

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        """Ensure chunk overlap is strictly less than chunk size.

        Args:
            v: The chunk_overlap value to validate.
            info: Pydantic validation info containing previously
                validated field data.

        Returns:
            The validated chunk_overlap value.

        Raises:
            ValueError: If ``chunk_overlap >= chunk_size``.
        """
        chunk_size = info.data.get("chunk_size", 1000)
        if v >= chunk_size:
            raise ValueError(f"chunk_overlap ({v}) must be less than chunk_size ({chunk_size})")
        return v

    # =========================================================================
    # LLM Configuration
    # =========================================================================

    llm_model: str = Field(
        default="claude-opus-4-5", description="Primary LLM for answer generation"
    )

    llm_lite_model: str = Field(
        default="claude-sonnet-4-5", description="Lightweight LLM for query expansion"
    )

    llm_thinking_budget: int = Field(
        default=10000, ge=1000, le=100000, description="Extended thinking token budget"
    )

    llm_temperature: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="LLM temperature (must be 1.0 for extended thinking)",
    )

    llm_timeout: int = Field(
        default=120, ge=10, le=600, description="LLM request timeout in seconds"
    )

    # =========================================================================
    # Retrieval Configuration
    # =========================================================================

    retrieval_total_chunks: int = Field(
        default=20, ge=1, le=100, description="Total chunks to retrieve before reranking"
    )

    retrieval_rerank_top_k: int = Field(
        default=10, ge=1, le=50, description="Top K chunks after reranking"
    )

    retrieval_num_queries: int = Field(
        default=5, ge=1, le=20, description="Number of expanded queries to generate"
    )

    @field_validator("retrieval_rerank_top_k")
    @classmethod
    def validate_rerank_top_k(cls, v, info):
        """Ensure rerank top-k does not exceed total retrieved chunks.

        Args:
            v: The retrieval_rerank_top_k value to validate.
            info: Pydantic validation info containing previously
                validated field data.

        Returns:
            The validated rerank_top_k value.

        Raises:
            ValueError: If ``rerank_top_k > total_chunks``.
        """
        total = info.data.get("retrieval_total_chunks", 20)
        if v > total:
            raise ValueError(
                f"retrieval_rerank_top_k ({v}) cannot exceed " f"retrieval_total_chunks ({total})"
            )
        return v

    # =========================================================================
    # Logging Configuration
    # =========================================================================

    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    log_format: Literal["json", "text"] = Field(default="text", description="Log output format")

    # =========================================================================
    # Debug & Development
    # =========================================================================

    debug_mode: bool = Field(default=False, description="Enable debug mode with verbose output")
