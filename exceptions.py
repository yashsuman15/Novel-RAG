"""Custom exceptions for the RAG application.

Defines a hierarchy of domain-specific exceptions that provide
structured error reporting with contextual details. All exceptions
inherit from :class:`RAGException` so callers can catch broad or
narrow error categories as needed.

Exception Hierarchy::

    RAGException
    ├── ConfigurationError
    ├── SecretsError
    ├── IngestionError
    │   ├── DocumentLoadError
    │   ├── DocumentSplitError
    │   ├── EmbeddingError
    │   └── VectorStoreError
    ├── RetrievalError
    │   ├── QueryExpansionError
    │   ├── SearchError
    │   └── RerankingError
    ├── LLMError
    │   ├── LLMAPIError
    │   └── LLMTimeoutError
    ├── ValidationError
    │   └── InputValidationError
    └── DeviceError
"""


class RAGException(Exception):
    """Base exception for all RAG-related errors.

    Provides structured error reporting with an optional ``details``
    dictionary for machine-readable context alongside the human-readable
    message.

    Attributes:
        message: Human-readable error description.
        details: Optional dictionary of contextual key-value pairs
            (e.g. file paths, parameter values, upstream error strings).

    Example:
        >>> raise RAGException(
        ...     "Pipeline failed",
        ...     details={"stage": "embedding", "doc_count": 42}
        ... )
    """

    def __init__(self, message: str, details: dict | None = None):
        """Initialize the RAGException.

        Args:
            message: Human-readable error description.
            details: Optional dictionary of contextual information to
                aid debugging. Defaults to an empty dict.
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        """Return a formatted string representation of the exception.

        Returns:
            The message string, optionally appended with the details
            dictionary if it is non-empty.
        """
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(RAGException):
    """Raised when configuration is invalid or missing.

    Examples include an unrecognised ``ENVIRONMENT`` value, a missing
    ``.env`` file, or Pydantic validation failures on config fields.
    """

    pass


class SecretsError(RAGException):
    """Raised when secrets cannot be loaded or validated.

    Typically triggered when the Anthropic API key is missing from the
    environment or ``.env`` file.
    """

    pass


class IngestionError(RAGException):
    """Base exception for document ingestion pipeline errors.

    Covers loading, splitting, embedding, and vector-store stages.
    """

    pass


class DocumentLoadError(IngestionError):
    """Raised when document loading fails.

    Common causes: missing directory, unsupported file format, or
    filesystem permission errors.
    """

    pass


class DocumentSplitError(IngestionError):
    """Raised when document splitting (chunking) fails.

    Common causes: invalid chunk size / overlap configuration or
    corrupt document content.
    """

    pass


class EmbeddingError(IngestionError):
    """Raised when embedding generation fails.

    Common causes: model download failure, CUDA out-of-memory, or
    incompatible model dimensions.
    """

    pass


class VectorStoreError(IngestionError):
    """Raised when vector store operations fail.

    Covers ChromaDB initialization, document insertion, and
    similarity search failures.
    """

    pass


class RetrievalError(RAGException):
    """Base exception for retrieval pipeline errors.

    Covers query expansion, vector search, and reranking stages.
    """

    pass


class QueryExpansionError(RetrievalError):
    """Raised when LLM-powered query expansion fails.

    Typically caused by an LLM API error during the expansion step.
    """

    pass


class SearchError(RetrievalError):
    """Raised when vector similarity search fails."""

    pass


class RerankingError(RetrievalError):
    """Raised when cross-encoder reranking fails.

    Common causes: model loading failure or scoring errors.
    """

    pass


class LLMError(RAGException):
    """Base exception for LLM-related errors.

    Covers model initialization, API calls, and response parsing.
    """

    pass


class LLMAPIError(LLMError):
    """Raised when an LLM API call fails.

    Common causes: rate limiting, invalid API key, network errors,
    or malformed request payloads.
    """

    pass


class LLMTimeoutError(LLMError):
    """Raised when an LLM request exceeds the configured timeout.

    The timeout value is set via ``llm_timeout`` in the config.
    """

    pass


class ValidationError(RAGException):
    """Raised when input validation fails.

    Covers Pydantic schema validation and custom business-rule checks.
    """

    pass


class InputValidationError(ValidationError):
    """Raised when user-supplied input is invalid.

    Examples: query too long, dangerous content detected, or
    out-of-range parameter values.
    """

    pass


class DeviceError(RAGException):
    """Raised when device (CUDA / CPU) configuration fails.

    Typically occurs when CUDA is requested but unavailable, or when
    torch cannot detect any suitable compute device.
    """

    pass
