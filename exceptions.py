"""Custom exceptions for RAG application."""


class RAGException(Exception):
    """Base exception for all RAG-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(RAGException):
    """Raised when configuration is invalid or missing."""
    pass


class SecretsError(RAGException):
    """Raised when secrets cannot be loaded."""
    pass


class IngestionError(RAGException):
    """Base class for ingestion-related errors."""
    pass


class DocumentLoadError(IngestionError):
    """Raised when document loading fails."""
    pass


class DocumentSplitError(IngestionError):
    """Raised when document splitting fails."""
    pass


class EmbeddingError(IngestionError):
    """Raised when embedding generation fails."""
    pass


class VectorStoreError(IngestionError):
    """Raised when vector store operations fail."""
    pass


class RetrievalError(RAGException):
    """Base class for retrieval-related errors."""
    pass


class QueryExpansionError(RetrievalError):
    """Raised when query expansion fails."""
    pass


class SearchError(RetrievalError):
    """Raised when vector search fails."""
    pass


class RerankingError(RetrievalError):
    """Raised when reranking fails."""
    pass


class LLMError(RAGException):
    """Base class for LLM-related errors."""
    pass


class LLMAPIError(LLMError):
    """Raised when LLM API call fails."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


class ValidationError(RAGException):
    """Raised when input validation fails."""
    pass


class InputValidationError(ValidationError):
    """Raised when user input is invalid."""
    pass


class DeviceError(RAGException):
    """Raised when device (CUDA/CPU) configuration fails."""
    pass