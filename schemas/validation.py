"""Pydantic schemas for input/output validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re


class QueryRequest(BaseModel):
    """
    Schema for user query requests.
    
    Validates and sanitizes user queries for security and correctness.
    """
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User query text"
    )
    
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Number of results to return (overrides config)"
    )
    
    num_queries: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of expanded queries (overrides config)"
    )
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and sanitize query."""
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
        json_schema_extra = {
            "example": {
                "query": "Who is Orsted?",
                "top_k": 10,
                "num_queries": 5
            }
        }


class SourceInfo(BaseModel):
    """Information about a source document."""
    
    citation_number: int = Field(
        ...,
        description="Citation number for reference"
    )
    
    source: str = Field(
        ...,
        description="Source file path"
    )
    
    page: Optional[int] = Field(
        default=None,
        description="Page number in source document"
    )
    
    content: str = Field(
        ...,
        description="Relevant content excerpt"
    )


class QueryResponse(BaseModel):
    """Schema for query responses."""
    
    answer: str = Field(
        ...,
        description="Generated answer"
    )
    
    sources: List[SourceInfo] = Field(
        default_factory=list,
        description="Source documents with citations"
    )
    
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (latency, model used, etc.)"
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
                        "content": "Orsted stood before them..."
                    }
                ],
                "metadata": {
                    "latency_ms": 1250,
                    "model": "claude-opus-4-5",
                    "chunks_retrieved": 10,
                    "thinking_tokens": 2500
                }
            }
        }


class DocumentIngestRequest(BaseModel):
    """Schema for document ingestion requests."""
    
    file_path: str = Field(
        ...,
        description="Path to PDF file or directory"
    )
    
    chunk_size: Optional[int] = Field(
        default=None,
        ge=100,
        le=5000,
        description="Override default chunk size"
    )
    
    chunk_overlap: Optional[int] = Field(
        default=None,
        ge=0,
        le=1000,
        description="Override default chunk overlap"
    )
    
    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path for security."""
        # Prevent directory traversal
        if ".." in v:
            raise ValueError(
                "File path cannot contain '..' (directory traversal not allowed)"
            )
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "data/raw/new_document.pdf",
                "chunk_size": 1000,
                "chunk_overlap": 300
            }
        }