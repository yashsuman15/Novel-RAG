# Validation Guide

## Overview

The RAG system uses Pydantic schemas for type-safe input/output validation. This provides automatic validation, sanitization, and security protection against malicious input.

## Table of Contents

- [Request Schemas](#request-schemas)
- [Response Schemas](#response-schemas)
- [Validation Rules](#validation-rules)
- [Security Features](#security-features)
- [Usage Examples](#usage-examples)
- [Custom Validation](#custom-validation)
- [Error Handling](#error-handling)

---

## Request Schemas

### `QueryRequest`

Validates and sanitizes user query requests.

**Fields:**

- `query` (str): User query text (1-2000 characters, required)
- `top_k` (int | None): Number of results to return (1-50, optional)
- `num_queries` (int | None): Number of expanded queries (1-20, optional)

**Automatic Processing:**

1. Whitespace normalization
2. XSS injection detection
3. Empty query rejection
4. Length validation

**Example:**

```python
from schemas.validation import QueryRequest

# Valid query
request = QueryRequest(
    query="Who is Rudeus Greyrat?",
    top_k=10,
    num_queries=5
)

print(request.query)        # "Who is Rudeus Greyrat?"
print(request.top_k)        # 10
print(request.num_queries)  # 5
```

**Constraints:**

| Field | Constraint | Error if Violated |
|-------|-----------|-------------------|
| `query` | min_length=1 | ValidationError |
| `query` | max_length=2000 | ValidationError |
| `query` | not empty after whitespace removal | ValueError |
| `query` | no dangerous patterns | ValueError |
| `top_k` | 1 ≤ value ≤ 50 | ValidationError |
| `num_queries` | 1 ≤ value ≤ 20 | ValidationError |

---

### `DocumentIngestRequest`

Validates document ingestion requests.

**Fields:**

- `file_path` (str): Path to PDF document (required)
- `chunk_size` (int | None): Override chunk size (100-5000, optional)
- `chunk_overlap` (int | None): Override chunk overlap (0-1000, optional)

**Example:**

```python
from schemas.validation import DocumentIngestRequest

# Basic request
request = DocumentIngestRequest(
    file_path="data/raw/volume1.pdf"
)

# With overrides
request = DocumentIngestRequest(
    file_path="data/raw/volume1.pdf",
    chunk_size=800,
    chunk_overlap=200
)
```

**Constraints:**

| Field | Constraint | Error if Violated |
|-------|-----------|-------------------|
| `chunk_size` | 100 ≤ value ≤ 5000 | ValidationError |
| `chunk_overlap` | 0 ≤ value ≤ 1000 | ValidationError |

---

## Response Schemas

### `SourceInfo`

Metadata for a single source citation.

**Fields:**

- `citation_number` (int): Sequential reference number (required)
- `source` (str): Filesystem path to source PDF (required)
- `page` (int | None): Page number within document (optional)
- `content` (str): Relevant text excerpt (required)

**Example:**

```python
from schemas.validation import SourceInfo

source = SourceInfo(
    citation_number=1,
    source="data/raw/volume1.pdf",
    page=42,
    content="Rudeus Greyrat is the protagonist of the story."
)
```

---

### `QueryResponse`

Structured answer with citations.

**Fields:**

- `query` (str): Original user query (required)
- `answer` (str): Generated answer text (required)
- `sources` (list[SourceInfo]): Citation sources (required)
- `thinking` (str | None): Extended thinking process (optional)

**Example:**

```python
from schemas.validation import QueryResponse, SourceInfo

response = QueryResponse(
    query="Who is Rudeus Greyrat?",
    answer="Rudeus Greyrat is the protagonist [1].",
    sources=[
        SourceInfo(
            citation_number=1,
            source="data/raw/volume1.pdf",
            page=10,
            content="Rudeus Greyrat is the protagonist..."
        )
    ],
    thinking="The query asks about the main character..."
)
```

---

## Validation Rules

### Whitespace Normalization

Excessive whitespace is automatically normalized:

**Input → Output:**

```python
"Who  is    Rudeus?"  →  "Who is Rudeus?"
"  Who is Rudeus?  "  →  "Who is Rudeus?"
"Who\tis\nRudeus?"    →  "Who is Rudeus?"
```

**Implementation:**

```python
@field_validator("query")
@classmethod
def validate_query(cls, v: str) -> str:
    # Collapse whitespace
    v = " ".join(v.split())
    return v
```

### Empty Query Rejection

Queries that are empty or whitespace-only are rejected:

**Rejected:**

```python
QueryRequest(query="")          # ValidationError
QueryRequest(query="   ")       # ValueError
QueryRequest(query="\t\n")      # ValueError
```

**Accepted:**

```python
QueryRequest(query="a")         # ✓ OK (min length = 1)
QueryRequest(query="?")         # ✓ OK (any character)
```

### Length Constraints

**Query Length:**

- Minimum: 1 character
- Maximum: 2000 characters

```python
# Valid
QueryRequest(query="a")                  # ✓ 1 char
QueryRequest(query="a" * 2000)           # ✓ 2000 chars

# Invalid
QueryRequest(query="")                   # ✗ 0 chars
QueryRequest(query="a" * 2001)           # ✗ 2001 chars
```

### Range Constraints

**top_k:**

- Minimum: 1
- Maximum: 50

```python
QueryRequest(query="test", top_k=1)      # ✓ OK
QueryRequest(query="test", top_k=50)     # ✓ OK
QueryRequest(query="test", top_k=0)      # ✗ ValidationError
QueryRequest(query="test", top_k=51)     # ✗ ValidationError
```

**num_queries:**

- Minimum: 1
- Maximum: 20

```python
QueryRequest(query="test", num_queries=1)   # ✓ OK
QueryRequest(query="test", num_queries=20)  # ✓ OK
QueryRequest(query="test", num_queries=0)   # ✗ ValidationError
QueryRequest(query="test", num_queries=21)  # ✗ ValidationError
```

---

## Security Features

### XSS Injection Prevention

The validator detects and rejects dangerous content patterns.

#### Pattern 1: Script Tags

**Rejected:**

```python
QueryRequest(query="<script>alert('xss')</script>")
# ValueError: Query contains potentially dangerous content matching pattern: <script
```

**Case-insensitive:**

```python
QueryRequest(query="<SCRIPT>alert('xss')</SCRIPT>")  # Also rejected
QueryRequest(query="<ScRiPt>alert(1)</ScRiPt>")      # Also rejected
```

#### Pattern 2: JavaScript Protocol

**Rejected:**

```python
QueryRequest(query="javascript:alert('xss')")
# ValueError: Query contains potentially dangerous content matching pattern: javascript:
```

**Case-insensitive:**

```python
QueryRequest(query="JAVASCRIPT:alert(1)")            # Rejected
QueryRequest(query="JaVaScRiPt:alert(1)")            # Rejected
```

#### Pattern 3: HTML Event Handlers

**Rejected:**

```python
QueryRequest(query="<img onerror='alert(1)'>")
# ValueError: Query contains potentially dangerous content matching pattern: on\w+=

QueryRequest(query="<div onclick='alert(1)'>")       # Rejected
QueryRequest(query="<body onload='alert(1)'>")       # Rejected
QueryRequest(query="' onmouseover='alert(1)'")       # Rejected
```

**Implementation:**

```python
dangerous_patterns = [
    r"<script",           # Script tags
    r"javascript:",       # JS protocol
    r"on\w+\s*=",        # Event handlers (onclick, onerror, etc.)
]

for pattern in dangerous_patterns:
    if re.search(pattern, v, re.IGNORECASE):
        raise ValueError(f"Query contains potentially dangerous content matching pattern: {pattern}")
```

### Safe Content

These are considered **SAFE** and allowed:

```python
# Mathematical operators
QueryRequest(query="What is x < y?")                 # ✓ OK
QueryRequest(query="Explain the > operator")         # ✓ OK

# Generic brackets (not HTML)
QueryRequest(query="What is a <vector> in math?")    # ✓ OK

# Special characters
QueryRequest(query="What is $100?")                  # ✓ OK
QueryRequest(query="Explain @mention syntax")        # ✓ OK
QueryRequest(query="What does #hashtag mean?")       # ✓ OK

# Unicode
QueryRequest(query="What is 日本語?")                # ✓ OK
QueryRequest(query="Explain café")                   # ✓ OK
```

---

## Usage Examples

### Basic Query Validation

```python
from schemas.validation import QueryRequest
from pydantic import ValidationError

# Valid query
try:
    request = QueryRequest(query="Who is Rudeus Greyrat?")
    print(f"Query: {request.query}")
    print(f"Valid: True")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Query with Optional Fields

```python
request = QueryRequest(
    query="Explain the magic system",
    top_k=15,
    num_queries=7
)

print(request.query)        # "Explain the magic system"
print(request.top_k)        # 15
print(request.num_queries)  # 7
```

### Handling Validation Errors

```python
from pydantic import ValidationError

def process_user_query(user_input: str, top_k: int = None):
    try:
        request = QueryRequest(
            query=user_input,
            top_k=top_k
        )
        return {"valid": True, "request": request}
    except ValidationError as e:
        # Pydantic validation error (field constraints)
        return {
            "valid": False,
            "error": "Invalid input format",
            "details": e.errors()
        }
    except ValueError as e:
        # Custom validation error (dangerous content)
        return {
            "valid": False,
            "error": str(e),
            "details": {"dangerous_content": True}
        }
```

### API Integration

```python
from fastapi import FastAPI, HTTPException
from schemas.validation import QueryRequest, QueryResponse
from pydantic import ValidationError

app = FastAPI()

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Query the RAG system.

    Automatic validation:
    - Query length checked
    - XSS injection prevented
    - Optional fields validated
    """
    try:
        # Process query (validation already done by FastAPI)
        answer = process_rag_query(request.query)

        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=get_sources(request.query)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Document Ingestion Validation

```python
from schemas.validation import DocumentIngestRequest

def ingest_document(file_path: str, chunk_size: int = None):
    try:
        request = DocumentIngestRequest(
            file_path=file_path,
            chunk_size=chunk_size
        )

        # Use validated values
        loader = DocumentLoader(
            chunk_size=request.chunk_size or config.chunk_size
        )
        return loader.load(request.file_path)

    except ValidationError as e:
        logger.error(f"Invalid ingestion request: {e}")
        raise
```

---

## Custom Validation

### Adding Custom Validators

You can add custom validators to schemas:

```python
from pydantic import BaseModel, field_validator

class CustomQueryRequest(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def validate_no_profanity(cls, v: str) -> str:
        """Reject queries with profanity."""
        profanity_list = ["badword1", "badword2"]

        if any(word in v.lower() for word in profanity_list):
            raise ValueError("Query contains inappropriate content")

        return v
```

### Multi-Field Validation

Validate relationships between fields:

```python
from pydantic import BaseModel, model_validator

class ChunkingRequest(BaseModel):
    chunk_size: int
    chunk_overlap: int

    @model_validator(mode='after')
    def validate_overlap_size(self):
        """Ensure overlap is less than chunk size."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        return self
```

---

## Error Handling

### Pydantic ValidationError

Raised when field constraints are violated:

```python
from pydantic import ValidationError

try:
    request = QueryRequest(query="a" * 2001)  # Too long
except ValidationError as e:
    print(e.errors())
    # [{'loc': ('query',), 'msg': 'ensure this value has at most 2000 characters', ...}]
```

**Error Structure:**

```python
{
    'loc': ('field_name',),           # Location of error
    'msg': 'error message',            # Human-readable message
    'type': 'value_error.max_length', # Error type
    'ctx': {'limit_value': 2000}      # Additional context
}
```

### Custom ValueError

Raised for custom validation logic (e.g., dangerous content):

```python
try:
    request = QueryRequest(query="<script>alert(1)</script>")
except ValueError as e:
    print(str(e))
    # "Query contains potentially dangerous content matching pattern: <script"
```

### Combined Error Handling

```python
from pydantic import ValidationError

def safe_validate_query(user_input: str):
    try:
        request = QueryRequest(query=user_input)
        return {"success": True, "request": request}

    except ValidationError as e:
        # Field constraint violations
        errors = []
        for error in e.errors():
            errors.append({
                "field": error['loc'][0],
                "message": error['msg'],
                "type": error['type']
            })
        return {"success": False, "errors": errors}

    except ValueError as e:
        # Custom validation failures
        return {
            "success": False,
            "errors": [{
                "field": "query",
                "message": str(e),
                "type": "dangerous_content"
            }]
        }
```

---

## Testing Validation

### Unit Tests

```python
import pytest
from pydantic import ValidationError
from schemas.validation import QueryRequest

def test_valid_query():
    """Test that valid query is accepted."""
    request = QueryRequest(query="Who is Rudeus?")
    assert request.query == "Who is Rudeus?"

def test_empty_query_rejected():
    """Test that empty query is rejected."""
    with pytest.raises(ValidationError):
        QueryRequest(query="")

def test_xss_injection_rejected():
    """Test that XSS attempts are rejected."""
    with pytest.raises(ValueError) as exc_info:
        QueryRequest(query="<script>alert('xss')</script>")
    assert "dangerous" in str(exc_info.value).lower()

def test_whitespace_normalization():
    """Test that whitespace is normalized."""
    request = QueryRequest(query="Who  is   Rudeus?")
    assert request.query == "Who is Rudeus?"
```

### Integration Tests

```python
from fastapi.testclient import TestClient

def test_query_endpoint_validation(client: TestClient):
    """Test that API endpoint validates input."""

    # Valid request
    response = client.post("/api/v1/query", json={
        "query": "Who is Rudeus?",
        "top_k": 10
    })
    assert response.status_code == 200

    # Invalid request - empty query
    response = client.post("/api/v1/query", json={
        "query": ""
    })
    assert response.status_code == 422  # Unprocessable Entity

    # Invalid request - XSS attempt
    response = client.post("/api/v1/query", json={
        "query": "<script>alert(1)</script>"
    })
    assert response.status_code == 422
```

---

## Best Practices

### 1. Always Use Schemas for User Input

```python
# Good - validated
def process_query(user_input: str):
    request = QueryRequest(query=user_input)
    return rag_pipeline.query(request.query)

# Bad - no validation
def process_query(user_input: str):
    return rag_pipeline.query(user_input)  # Dangerous!
```

### 2. Handle Validation Errors Gracefully

```python
# Good - user-friendly error
try:
    request = QueryRequest(query=user_input)
except ValidationError as e:
    return {"error": "Invalid input. Please check your query length and format."}

# Bad - exposes internal details
except ValidationError as e:
    return {"error": str(e)}  # Too technical
```

### 3. Use Type Hints

```python
# Good - type safe
def query(request: QueryRequest) -> QueryResponse:
    ...

# Bad - no type safety
def query(request) -> dict:
    ...
```

### 4. Test Edge Cases

```python
# Test boundary conditions
test_cases = [
    "a",                  # Min length
    "a" * 2000,          # Max length
    "a" * 2001,          # Over max
    "",                  # Empty
    "   ",               # Whitespace only
    "<script>x</script>", # XSS
]
```

---

## Related Documentation

- [Security Guide](./SECURITY.md) - XSS prevention details
- [Error Handling Guide](./ERROR_HANDLING.md) - ValidationError handling
- [Configuration Guide](./CONFIGURATION.md) - Configuration validation

---

## Additional Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [FastAPI Validation](https://fastapi.tiangolo.com/tutorial/body/)
