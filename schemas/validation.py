"""Pydantic schemas for input/output validation.

Defines request and response models that enforce type safety, value
constraints, and security sanitisation across the RAG API boundary.

Schemas:
    - :class:`QueryRequest` — Validated user query input.
    - :class:`SourceInfo` — Citation metadata for a single source.
    - :class:`QueryResponse` — Structured answer with citations.
    - :class:`DocumentIngestRequest` — Document upload parameters.
"""

import re

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Schema for user query requests.

    Validates and sanitises user queries for security and correctness.
    Applies whitespace normalisation and XSS injection protection.

    Attributes:
        query: The user's question text (1–2000 characters).
        top_k: Optional override for the number of results to return.
        num_queries: Optional override for expanded query count.
    """

    query: str = Field(..., min_length=1, max_length=2000, description="User query text")

    top_k: int | None = Field(
        default=None, ge=1, le=50, description="Number of results to return (overrides config)"
    )

    num_queries: int | None = Field(
        default=None, ge=1, le=20, description="Number of expanded queries (overrides config)"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and sanitise the query string.

        Performs three checks in order:

        1. Collapse excessive whitespace.
        2. Reject empty / whitespace-only strings.
        3. Reject strings matching dangerous XSS patterns.

        Args:
            v: The raw query string to validate.

        Returns:
            The cleaned query string with normalised whitespace.

        Raises:
            ValueError: If the query is empty after cleaning or
                contains dangerous content patterns.
        """
        # Remove excessive whitespace
        v = " ".join(v.split())

        # Check for empty after cleaning
        if not v.strip():
            raise ValueError("Query cannot be empty or only whitespace")

        # Basic injection protection
        dangerous_patterns = [
            r"<script",
            r"javascript:",
            r"on\w+\s*=",  # HTML event handlers
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(
                    f"Query contains potentially dangerous content matching pattern: {pattern}"
                )

        return v

    class Config:
        json_schema_extra = {"example": {"query": "Who is Orsted?", "top_k": 10, "num_queries": 5}}


class SourceInfo(BaseModel):
    """Metadata for a single source document citation.

    Represents one citation reference used in a generated answer.

    Attributes:
        citation_number: Sequential reference number (e.g. ``[1]``).
        source: Filesystem path to the source PDF.
        page: Optional page number within the source document.
        content: Relevant text excerpt from the source.
    """

    citation_number: int = Field(..., description="Citation number for reference")

    source: str = Field(..., description="Source file path")

    page: int | None = Field(default=None, description="Page number in source document")

    content: str = Field(..., description="Relevant content excerpt")


class QueryResponse(BaseModel):
    """Schema for structured query responses.

    Wraps the generated answer together with source citations and
    operational metadata (latency, model info, etc.).

    Attributes:
        answer: The generated answer text with inline citations.
        sources: List of :class:`SourceInfo` citation references.
        metadata: Operational metadata dict (latency_ms, model, etc.).
    """

    answer: str = Field(..., description="Generated answer")

    sources: list[SourceInfo] = Field(
        default_factory=list, description="Source documents with citations"
    )

    metadata: dict = Field(
        default_factory=dict, description="Additional metadata (latency, model used, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Orsted is the Dragon God, a powerful figure...",
                "sources": [
                    {
                        "citation_number": 1,
                        "source": "data/raw/volume_15.pdf",
                        "page": 42,
                        "content": "Orsted stood before them...",
                    }
                ],
                "metadata": {
                    "latency_ms": 1250,
                    "model": "claude-opus-4-5",
                    "chunks_retrieved": 10,
                    "thinking_tokens": 2500,
                },
            }
        }


class DocumentIngestRequest(BaseModel):
    """Schema for document ingestion requests.

    Validates parameters for loading new documents into the RAG
    pipeline. Includes security checks on file paths.

    Attributes:
        file_path: Path to the PDF file or directory to ingest.
        chunk_size: Optional override for text chunk size (100–5000).
        chunk_overlap: Optional override for chunk overlap (0–1000).
    """

    file_path: str = Field(..., description="Path to PDF file or directory")

    chunk_size: int | None = Field(
        default=None, ge=100, le=5000, description="Override default chunk size"
    )

    chunk_overlap: int | None = Field(
        default=None, ge=0, le=1000, description="Override default chunk overlap"
    )

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate the file path for directory traversal attacks.

        Args:
            v: The raw file path string to validate.

        Returns:
            The validated file path string.

        Raises:
            ValueError: If the path contains ``..`` sequences.
        """
        # Prevent directory traversal
        if ".." in v:
            raise ValueError("File path cannot contain '..' (directory traversal not allowed)")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "data/raw/new_document.pdf",
                "chunk_size": 1000,
                "chunk_overlap": 300,
            }
        }
