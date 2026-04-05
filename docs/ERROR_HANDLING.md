# Error Handling Guide

## Overview

The RAG system implements a structured exception hierarchy that provides clear, actionable error information with contextual details. All exceptions inherit from `RAGException`, enabling both broad and narrow error handling patterns.

## Table of Contents

- [Exception Hierarchy](#exception-hierarchy)
- [Base Exception](#base-exception)
- [Exception Categories](#exception-categories)
- [Using Exceptions](#using-exceptions)
- [Error Context](#error-context)
- [Best Practices](#best-practices)
- [Error Recovery Patterns](#error-recovery-patterns)

---

## Exception Hierarchy

```text
RAGException (base class)
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
```

---

## Base Exception

### `RAGException`

Base class for all RAG-related errors. Provides structured error reporting with optional context.

**Attributes:**

- `message` (str): Human-readable error description
- `details` (dict): Optional contextual information for debugging

**Example:**

```python
from exceptions import RAGException

raise RAGException(
    "Pipeline failed at embedding stage",
    details={
        "stage": "embedding",
        "doc_count": 42,
        "model": "BAAI/bge-large-en-v1.5"
    }
)
```

**String Representation:**

```python
try:
    raise RAGException("Failed", details={"key": "value"})
except RAGException as e:
    print(str(e))
    # Output: Failed | Details: {'key': 'value'}
```

---

## Exception Categories

### Configuration Errors

#### `ConfigurationError`

Raised when configuration is invalid or missing.

**Common Causes:**

- Invalid `ENVIRONMENT` value
- Missing `.env` file
- Pydantic validation failures on config fields
- Conflicting configuration values

**Examples:**

```python
from exceptions import ConfigurationError

# Invalid environment
raise ConfigurationError(
    "Invalid ENVIRONMENT: 'invalid_env'",
    details={
        "environment": "invalid_env",
        "valid_options": ["development", "production", "testing"]
    }
)

# Missing configuration
raise ConfigurationError(
    "Required configuration missing",
    details={"missing_field": "api_key"}
)

# Validation failure
raise ConfigurationError(
    "chunk_overlap must be less than chunk_size",
    details={
        "chunk_size": 500,
        "chunk_overlap": 600
    }
)
```

**Handling:**

```python
from config.settings import get_settings
from exceptions import ConfigurationError

try:
    config = get_settings()
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    logger.error(f"Details: {e.details}")
    # Show user how to fix
    if "valid_options" in e.details:
        print(f"Valid options: {e.details['valid_options']}")
```

---

#### `SecretsError`

Raised when secrets cannot be loaded or validated.

**Common Causes:**

- Missing `ANTHROPIC_API_KEY` in environment
- Invalid API key format
- Missing `.env` file

**Examples:**

```python
from exceptions import SecretsError

# Missing API key
raise SecretsError(
    "ANTHROPIC_API_KEY not found in environment",
    details={"checked_locations": [".env", "environment variables"]}
)

# Invalid format
raise SecretsError(
    "Invalid API key format",
    details={"expected_prefix": "sk-ant-"}
)
```

**Handling:**

```python
from config.secrets import get_secrets
from exceptions import SecretsError

try:
    secrets = get_secrets()
except SecretsError as e:
    logger.error(f"Secrets error: {e}")
    print("Please set ANTHROPIC_API_KEY in .env file")
    print("Example: ANTHROPIC_API_KEY=sk-ant-api03-xxx")
    sys.exit(1)
```

---

### Ingestion Errors

#### `IngestionError`

Base class for document ingestion pipeline errors.

**Child Exceptions:**

- `DocumentLoadError`
- `DocumentSplitError`
- `EmbeddingError`
- `VectorStoreError`

---

#### `DocumentLoadError`

Raised when document loading fails.

**Common Causes:**

- Missing directory
- Unsupported file format
- Filesystem permission errors
- Corrupted PDF files

**Examples:**

```python
from exceptions import DocumentLoadError

# Directory not found
raise DocumentLoadError(
    "Data directory not found",
    details={"path": "/data/raw", "exists": False}
)

# Unsupported format
raise DocumentLoadError(
    "Unsupported file format",
    details={"file": "document.docx", "supported": [".pdf"]}
)

# Permission error
raise DocumentLoadError(
    "Cannot read file",
    details={"file": "volume1.pdf", "permission": "denied"}
)
```

**Handling:**

```python
from ingestion.loader import DocumentLoader
from exceptions import DocumentLoadError

try:
    loader = DocumentLoader()
    documents = loader.load("data/raw")
except DocumentLoadError as e:
    if "not found" in e.message:
        logger.error(f"Directory does not exist: {e.details['path']}")
        print("Please create the directory and add PDF files")
    elif "permission" in str(e):
        logger.error("Permission denied. Check file permissions.")
```

---

#### `DocumentSplitError`

Raised when document splitting (chunking) fails.

**Common Causes:**

- Invalid chunk size/overlap configuration
- Empty document content
- Text processing errors

**Examples:**

```python
from exceptions import DocumentSplitError

# Invalid configuration
raise DocumentSplitError(
    "chunk_overlap must be less than chunk_size",
    details={"chunk_size": 500, "chunk_overlap": 600}
)

# Empty document
raise DocumentSplitError(
    "Cannot split empty document",
    details={"file": "volume1.pdf", "content_length": 0}
)
```

---

#### `EmbeddingError`

Raised when embedding generation fails.

**Common Causes:**

- Model download failure
- CUDA out-of-memory
- Incompatible model dimensions
- Network errors during model load

**Examples:**

```python
from exceptions import EmbeddingError

# CUDA OOM
raise EmbeddingError(
    "CUDA out of memory",
    details={
        "model": "BAAI/bge-large-en-v1.5",
        "device": "cuda:0",
        "batch_size": 5000
    }
)

# Model load failure
raise EmbeddingError(
    "Failed to load embedding model",
    details={"model": "invalid-model-name", "error": "404 Not Found"}
)

# Dimension mismatch
raise EmbeddingError(
    "Embedding dimension mismatch",
    details={"expected": 1024, "actual": 768}
)
```

**Handling:**

```python
from ingestion.embeddings import EmbeddingModel
from exceptions import EmbeddingError

try:
    model = EmbeddingModel()
    embeddings = model.embed(texts)
except EmbeddingError as e:
    if "CUDA out of memory" in e.message:
        logger.warning("CUDA OOM - falling back to CPU")
        # Retry with CPU
        model = EmbeddingModel(device="cpu")
        embeddings = model.embed(texts)
    else:
        logger.error(f"Embedding failed: {e}")
        raise
```

---

#### `VectorStoreError`

Raised when vector store operations fail.

**Common Causes:**

- ChromaDB initialization failure
- Document insertion errors
- Similarity search failures
- Storage permission issues

**Examples:**

```python
from exceptions import VectorStoreError

# Initialization failure
raise VectorStoreError(
    "Failed to initialize ChromaDB",
    details={"path": "./data/vector_store", "error": "Permission denied"}
)

# Insertion failure
raise VectorStoreError(
    "Failed to add documents to collection",
    details={"collection": "rag_collection", "doc_count": 100}
)

# Search failure
raise VectorStoreError(
    "Similarity search failed",
    details={"query": "sample query", "top_k": 10}
)
```

---

### Retrieval Errors

#### `RetrievalError`

Base class for retrieval pipeline errors.

**Child Exceptions:**

- `QueryExpansionError`
- `SearchError`
- `RerankingError`

---

#### `QueryExpansionError`

Raised when LLM-powered query expansion fails.

**Common Causes:**

- LLM API errors during expansion
- Invalid query format
- Timeout during expansion

**Examples:**

```python
from exceptions import QueryExpansionError

raise QueryExpansionError(
    "Query expansion failed",
    details={
        "original_query": "Who is Rudeus?",
        "llm_error": "Rate limit exceeded"
    }
)
```

---

#### `SearchError`

Raised when vector similarity search fails.

**Examples:**

```python
from exceptions import SearchError

raise SearchError(
    "Vector search failed",
    details={
        "query_embedding_dim": 1024,
        "expected_dim": 768,
        "top_k": 20
    }
)
```

---

#### `RerankingError`

Raised when cross-encoder reranking fails.

**Common Causes:**

- Model loading failure
- Scoring errors
- Out of memory

**Examples:**

```python
from exceptions import RerankingError

raise RerankingError(
    "Reranking model failed",
    details={
        "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "doc_count": 20,
        "error": "CUDA OOM"
    }
)
```

---

### LLM Errors

#### `LLMError`

Base class for LLM-related errors.

**Child Exceptions:**

- `LLMAPIError`
- `LLMTimeoutError`

---

#### `LLMAPIError`

Raised when LLM API calls fail.

**Common Causes:**

- Rate limiting
- Invalid API key
- Network errors
- Malformed requests

**Examples:**

```python
from exceptions import LLMAPIError

# Rate limit
raise LLMAPIError(
    "API rate limit exceeded",
    details={"retry_after": 60, "model": "claude-opus-4-5"}
)

# Invalid API key
raise LLMAPIError(
    "Authentication failed",
    details={"status_code": 401}
)

# Network error
raise LLMAPIError(
    "Network connection failed",
    details={"error": "Connection timeout", "endpoint": "api.anthropic.com"}
)
```

**Handling:**

```python
from llm.model import LLMModel
from exceptions import LLMAPIError
import time

def call_llm_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            model = LLMModel()
            return model.generate(prompt)
        except LLMAPIError as e:
            if "rate limit" in e.message.lower():
                retry_after = e.details.get("retry_after", 60)
                logger.warning(f"Rate limited. Retrying in {retry_after}s")
                time.sleep(retry_after)
            elif "Authentication" in e.message:
                logger.error("Invalid API key. Cannot retry.")
                raise
            else:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
```

---

#### `LLMTimeoutError`

Raised when LLM requests exceed configured timeout.

**Examples:**

```python
from exceptions import LLMTimeoutError

raise LLMTimeoutError(
    "LLM request timed out",
    details={
        "timeout": 120,
        "elapsed": 125,
        "model": "claude-opus-4-5"
    }
)
```

---

### Validation Errors

#### `ValidationError`

Base class for validation errors.

**Child Exceptions:**

- `InputValidationError`

---

#### `InputValidationError`

Raised when user-supplied input is invalid.

**Common Causes:**

- Query too long
- Dangerous content detected
- Out-of-range parameter values

**Examples:**

```python
from exceptions import InputValidationError

# Query too long
raise InputValidationError(
    "Query exceeds maximum length",
    details={"max_length": 2000, "actual_length": 2500}
)

# Dangerous content
raise InputValidationError(
    "Query contains dangerous content",
    details={"pattern": "<script", "sanitized": True}
)

# Invalid parameter
raise InputValidationError(
    "top_k out of range",
    details={"value": 100, "min": 1, "max": 50}
)
```

---

### Device Errors

#### `DeviceError`

Raised when device (CUDA/CPU) configuration fails.

**Common Causes:**

- CUDA requested but unavailable
- No suitable compute device found
- GPU memory allocation failure

**Examples:**

```python
from exceptions import DeviceError

# CUDA unavailable
raise DeviceError(
    "CUDA not available",
    details={"requested": "cuda", "available": ["cpu"]}
)

# No device found
raise DeviceError(
    "No compute device available",
    details={"checked": ["cuda", "cpu"]}
)
```

---

## Using Exceptions

### Raising Exceptions

**Basic:**

```python
from exceptions import DocumentLoadError

raise DocumentLoadError("File not found")
```

**With Context:**

```python
raise DocumentLoadError(
    "Failed to load PDF",
    details={
        "file": "volume1.pdf",
        "path": "/data/raw/volume1.pdf",
        "error": str(original_error)
    }
)
```

**Re-raising with Context:**

```python
try:
    # Some operation
    load_document(path)
except Exception as e:
    raise DocumentLoadError(
        "Document loading failed",
        details={"path": path, "original_error": str(e)}
    ) from e
```

### Catching Exceptions

**Catch Specific:**

```python
try:
    embeddings = create_embeddings(texts)
except EmbeddingError as e:
    logger.error(f"Embedding failed: {e}")
    logger.debug(f"Details: {e.details}")
    # Handle embedding-specific error
```

**Catch Category:**

```python
try:
    process_documents()
except IngestionError as e:
    # Catches all ingestion-related errors
    logger.error(f"Ingestion failed: {e}")
```

**Catch All RAG Errors:**

```python
try:
    run_rag_pipeline(query)
except RAGException as e:
    logger.error(f"RAG error: {e}")
    return {"error": e.message, "details": e.details}
```

---

## Error Context

### Accessing Context

```python
try:
    load_document(path)
except DocumentLoadError as e:
    # Message
    print(e.message)  # "Failed to load PDF"

    # Details dictionary
    print(e.details)  # {"file": "volume1.pdf", ...}

    # Specific detail
    file_path = e.details.get("file")

    # String representation
    print(str(e))  # "Failed to load PDF | Details: {...}"
```

### Logging with Context

```python
import logging

try:
    operation()
except RAGException as e:
    logger.error(
        f"{e.message}",
        extra={
            "error_type": type(e).__name__,
            "details": e.details
        }
    )
```

---

## Best Practices

### 1. Use Specific Exceptions

```python
# Good - specific
raise DocumentLoadError("File not found", details={"path": path})

# Bad - generic
raise Exception("Error loading document")
```

### 2. Include Contextual Details

```python
# Good - actionable context
raise EmbeddingError(
    "CUDA out of memory",
    details={
        "model": config.embedding_model,
        "batch_size": config.batch_size,
        "device": "cuda:0",
        "suggestion": "Try reducing batch_size or use CPU"
    }
)

# Bad - no context
raise EmbeddingError("Failed")
```

### 3. Preserve Original Error

```python
# Good - chain exceptions
try:
    api_call()
except requests.HTTPError as e:
    raise LLMAPIError(
        "API call failed",
        details={"status": e.response.status_code}
    ) from e

# Bad - loses original traceback
except requests.HTTPError as e:
    raise LLMAPIError("API call failed")
```

### 4. Don't Expose Sensitive Data

```python
# Good - sanitized
raise SecretsError(
    "API key validation failed",
    details={"key_length": len(api_key), "prefix": api_key[:7]}
)

# Bad - exposes secret
raise SecretsError(
    f"Invalid API key: {api_key}",
    details={"key": api_key}
)
```

### 5. Handle Gracefully

```python
def process_with_fallback(data):
    try:
        return process_with_gpu(data)
    except DeviceError as e:
        logger.warning(f"GPU failed: {e}. Falling back to CPU.")
        return process_with_cpu(data)
```

---

## Error Recovery Patterns

### Retry with Backoff

```python
import time
from exceptions import LLMAPIError

def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except LLMAPIError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt+1} failed. Retrying in {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.error("Max retries exceeded")
                raise
```

### Fallback Strategy

```python
def embed_with_fallback(texts):
    try:
        return embed_on_gpu(texts)
    except DeviceError:
        logger.info("GPU unavailable, using CPU")
        return embed_on_cpu(texts)
    except EmbeddingError as e:
        logger.error(f"Embedding failed: {e}")
        # Return zero embeddings as fallback
        return [[0.0] * 1024 for _ in texts]
```

### Partial Success

```python
def process_batch(documents):
    results = []
    errors = []

    for doc in documents:
        try:
            result = process_document(doc)
            results.append(result)
        except IngestionError as e:
            errors.append({"doc": doc, "error": str(e)})

    return {
        "success": results,
        "errors": errors,
        "success_rate": len(results) / len(documents)
    }
```

---

## Related Documentation

- [Configuration Guide](./CONFIGURATION.md) - ConfigurationError handling
- [Security Guide](./SECURITY.md) - SecretsError handling
- [Validation Guide](./VALIDATION.md) - InputValidationError handling
