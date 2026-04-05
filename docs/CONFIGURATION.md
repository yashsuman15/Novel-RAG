# Configuration Guide

## Overview

The RAG system uses a Pydantic-based configuration system with environment-specific overrides. This provides type-safe, validated configuration with sensible defaults and flexible customization.

## Table of Contents

- [Configuration Architecture](#configuration-architecture)
- [Configuration Files](#configuration-files)
- [Environment Selection](#environment-selection)
- [Configuration Hierarchy](#configuration-hierarchy)
- [Environment Variables](#environment-variables)
- [Usage Examples](#usage-examples)
- [Advanced Patterns](#advanced-patterns)
- [Troubleshooting](#troubleshooting)

---

## Configuration Architecture

The configuration system is built on Pydantic `BaseSettings` with a layered approach:

```text
BaseConfig (base.py)
    ├── DevelopmentConfig (development.py)
    ├── ProductionConfig (production.py)
    └── TestingConfig (testing.py)
```

**Key Features:**

- ✅ Type-safe configuration with Pydantic validation
- ✅ Environment-specific overrides
- ✅ Automatic validation on load
- ✅ Environment variable support
- ✅ Singleton pattern for performance
- ✅ Easy testing with `reload_settings()`

---

## Configuration Files

### Directory Structure

```text
├── __init__.py          # Public API exports
├── base.py              # Base configuration with defaults
├── development.py       # Development overrides
├── production.py        # Production overrides
├── testing.py           # Testing overrides
├── settings.py          # Configuration factory
└── secrets.py           # Secrets management
```

### `config/base.py` - Base Configuration

Contains all configuration fields with sensible defaults.

**Major configuration sections:**

1. **Environment**

   ```python
   environment: Literal["development", "production", "testing"]
   ```

2. **Paths**

   ```python
   project_root: Path
   data_dir: Path
   raw_data_dir: Path  # Computed property
   vector_store_dir: Path  # Computed property
   ```

3. **Vector Store**

   ```python
   vector_store_collection: str = "rag_collection"
   batch_size: int = 5000
   ```

4. **Embeddings**

   ```python
   embedding_model: str = "BAAI/bge-large-en-v1.5"
   embedding_dimension: int = 1024
   embedding_device: Literal["cuda", "cpu", "auto"] = "auto"
   normalize_embeddings: bool = True
   ```

5. **Text Splitting**

   ```python
   chunk_size: int = 1000
   chunk_overlap: int = 300
   text_separators: list[str] = ["\n\n", "\n", ". ", " ", ""]
   ```

6. **LLM Configuration**

   ```python
   llm_model: str = "claude-opus-4-5"
   llm_lite_model: str = "claude-sonnet-4-5"
   llm_thinking_budget: int = 10000
   llm_temperature: float = 1.0
   llm_timeout: int = 120
   ```

7. **Retrieval**

   ```python
   retrieval_total_chunks: int = 20
   retrieval_rerank_top_k: int = 10
   retrieval_num_queries: int = 5
   ```

8. **Logging**

   ```python
   log_level: str = "INFO"
   log_format: Literal["json", "text"] = "text"
   ```

**Validation Rules:**

- `chunk_overlap` must be less than `chunk_size`
- `retrieval_rerank_top_k` must not exceed `retrieval_total_chunks`
- Field constraints enforced via Pydantic validators

### `config/development.py` - Development Config

Optimized for fast iteration and debugging.

**Key Overrides:**

```python
log_level: str = "DEBUG"
log_format: str = "text"  # Human-readable
debug_mode: bool = True

batch_size: int = 1000  # Smaller batches
retrieval_total_chunks: int = 10  # Fewer chunks
llm_thinking_budget: int = 5000  # Lower budget
```

**Use Case:**

- Local development
- Debugging
- Quick iteration
- Verbose logging

### `config/production.py` - Production Config

Optimized for performance, stability, and observability.

**Key Overrides:**

```python
log_level: str = "WARNING"
log_format: str = "json"  # Structured logging
debug_mode: bool = False

batch_size: int = 5000  # Maximum performance
retrieval_total_chunks: int = 20  # Best quality
llm_thinking_budget: int = 10000  # Full budget
llm_timeout: int = 120  # Longer timeout
```

**Use Case:**

- Production deployment
- Staging environment
- Performance-critical scenarios
- Log aggregation systems (JSON format)

### `config/testing.py` - Testing Config

Optimized for fast, deterministic test execution.

**Key Overrides:**

```python
log_level: str = "ERROR"  # Quiet during tests
log_format: str = "text"
debug_mode: bool = False

batch_size: int = 100  # Minimal batches
retrieval_total_chunks: int = 5  # Minimal retrieval
llm_thinking_budget: int = 1000  # Fast responses
llm_timeout: int = 30  # Short timeout

chunk_size: int = 500  # Smaller chunks
chunk_overlap: int = 100
```

**Use Case:**

- Automated testing
- CI/CD pipelines
- Fast feedback loops
- Reduced API costs

### `config/settings.py` - Configuration Factory

Provides factory functions and singleton management.

**Key Functions:**

```python
def get_config() -> ConfigType:
    """Load config based on ENVIRONMENT variable."""

def get_settings() -> ConfigType:
    """Get or create settings singleton."""

def reload_settings() -> ConfigType:
    """Force reload settings (for tests)."""
```

### `config/secrets.py` - Secrets Management

Centralized secrets loading and validation.

```python
from config.secrets import get_secrets

secrets = get_secrets()
api_key = secrets.anthropic_api_key
```

---

## Environment Selection

### Setting the Environment

The environment is selected via the `ENVIRONMENT` variable:

```bash
# Development (default)
export ENVIRONMENT=development
# or
export ENVIRONMENT=dev

# Production
export ENVIRONMENT=production
# or
export ENVIRONMENT=prod
# or
export ENVIRONMENT=staging

# Testing
export ENVIRONMENT=testing
# or
export ENVIRONMENT=test
```

### Environment Mapping

| Environment Value | Configuration Class | Use Case |
|-------------------|---------------------|----------|
| `development`, `dev` | `DevelopmentConfig` | Local development |
| `production`, `prod` | `ProductionConfig` | Production deployment |
| `staging`, `stage` | `ProductionConfig` | Staging environment |
| `testing`, `test` | `TestingConfig` | Automated tests |

### Default Behavior

If `ENVIRONMENT` is not set, defaults to `development`:

```python
# No ENVIRONMENT variable
config = get_settings()
# Returns DevelopmentConfig
```

---

## Configuration Hierarchy

Configuration values are loaded in priority order (highest to lowest):

1. **Environment Variables** (highest priority)

   ```bash
   export CHUNK_SIZE=2000
   ```

2. **`.env` File**

   ```bash
   # .env
   CHUNK_SIZE=1500
   ```

3. **Environment-Specific Config Class**

   ```python
   # config/development.py
   chunk_size: int = 1000
   ```

4. **Base Defaults** (lowest priority)

   ```python
   # config/base.py
   chunk_size: int = 1000
   ```

### Example

```bash
# .env
CHUNK_SIZE=1500
LOG_LEVEL=WARNING

# Shell
export CHUNK_SIZE=2000
```

```python
config = DevelopmentConfig()
print(config.chunk_size)  # 2000 (env var wins)
print(config.log_level)   # "WARNING" (from .env)
print(config.batch_size)  # 1000 (from DevelopmentConfig)
```

---

## Environment Variables

All configuration fields can be overridden via environment variables.

### Naming Convention

Environment variable names are **UPPERCASE** versions of field names:

| Config Field | Environment Variable |
|--------------|----------------------|
| `chunk_size` | `CHUNK_SIZE` |
| `log_level` | `LOG_LEVEL` |
| `llm_model` | `LLM_MODEL` |
| `embedding_device` | `EMBEDDING_DEVICE` |

### Type Conversion

Pydantic automatically converts environment variable strings:

```bash
# Integers
export CHUNK_SIZE=2000

# Booleans
export DEBUG_MODE=true
export NORMALIZE_EMBEDDINGS=false

# Lists (JSON)
export TEXT_SEPARATORS='["\n\n", "\n", ". "]'

# Paths
export DATA_DIR=/path/to/data
```

### Common Overrides

```bash
# Adjust chunk size
export CHUNK_SIZE=1500

# Change log level
export LOG_LEVEL=DEBUG

# Use CPU instead of GPU
export EMBEDDING_DEVICE=cpu

# Increase LLM timeout
export LLM_TIMEOUT=180

# Change batch size
export BATCH_SIZE=3000
```

---

## Usage Examples

### Basic Usage

```python
from config.settings import get_settings

# Get configuration
config = get_settings()

# Access fields
print(config.chunk_size)           # 1000
print(config.embedding_model)      # "BAAI/bge-large-en-v1.5"
print(config.llm_thinking_budget)  # 10000
```

### Environment-Specific Loading

```python
import os
from config.settings import get_config

# Development
os.environ["ENVIRONMENT"] = "development"
config = get_config()
print(config.log_level)  # "DEBUG"

# Production
os.environ["ENVIRONMENT"] = "production"
config = get_config()
print(config.log_level)  # "WARNING"
```

### Direct Class Instantiation

```python
from config.development import DevelopmentConfig
from config.production import ProductionConfig

# Development
dev_config = DevelopmentConfig()

# Production with overrides
prod_config = ProductionConfig(
    chunk_size=1500,
    log_level="ERROR"
)
```

### Using in Modules

```python
# ingestion/embeddings.py
from config.settings import get_settings

def create_embeddings():
    config = get_settings()

    model = SentenceTransformer(
        config.embedding_model,
        device=config.embedding_device
    )

    embeddings = model.encode(
        texts,
        normalize_embeddings=config.normalize_embeddings
    )

    return embeddings
```

### Testing Configuration

```python
# tests/test_my_module.py
import os
from config.settings import reload_settings

def test_with_custom_config():
    # Set test environment
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["CHUNK_SIZE"] = "500"

    # Reload to apply changes
    config = reload_settings()

    assert config.chunk_size == 500
    assert config.environment == "testing"
```

---

## Advanced Patterns

### Computed Properties

```python
config = get_settings()

# Computed from data_dir
print(config.raw_data_dir)      # data_dir / "raw"
print(config.vector_store_dir)  # data_dir / "vector_store"
```

### Validation on Assignment

```python
config = BaseConfig()

# This will raise ValidationError
try:
    config.chunk_overlap = 2000  # Greater than chunk_size
except ValidationError as e:
    print(e)
```

### Custom Validation

In `config/base.py`:

```python
@field_validator("chunk_overlap")
@classmethod
def validate_chunk_overlap(cls, v, info):
    chunk_size = info.data.get("chunk_size", 1000)
    if v >= chunk_size:
        raise ValueError(f"chunk_overlap ({v}) must be < chunk_size ({chunk_size})")
    return v
```

### Dependency Injection

```python
# Instead of importing get_settings everywhere
class DocumentLoader:
    def __init__(self, config: BaseConfig):
        self.config = config

    def load(self):
        # Use self.config
        pass

# Usage
config = get_settings()
loader = DocumentLoader(config)
```

---

## Troubleshooting

### Issue: Configuration Not Loading

**Symptom:** Changes to `.env` not reflected

**Solution:**

```python
# Reload settings to pick up changes
from config.settings import reload_settings
config = reload_settings()
```

### Issue: ValidationError on Startup

**Symptom:**

```text
pydantic.ValidationError: chunk_overlap must be less than chunk_size
```

**Solution:**

```bash
# Check your environment variables
env | grep CHUNK

# Fix the values
export CHUNK_SIZE=1000
export CHUNK_OVERLAP=300
```

### Issue: Wrong Environment Loaded

**Symptom:** Production settings in development

**Solution:**

```bash
# Check ENVIRONMENT variable
echo $ENVIRONMENT

# Set explicitly
export ENVIRONMENT=development

# Verify
python -c "from config.settings import get_settings; print(get_settings().environment)"
```

### Issue: Cannot Import Config

**Symptom:**

```text
ImportError: cannot import name 'ProductionConfig'
```

**Solution:**

```bash
# Ensure all config files exist
ls config/

# Check for syntax errors
python -m py_compile config/production.py
```

### Issue: Secrets Not Loading

**Symptom:**

```text
SecretsError: ANTHROPIC_API_KEY not found
```

**Solution:**

```bash
# Check .env file exists
ls .env

# Verify content
cat .env | grep ANTHROPIC_API_KEY

# Set explicitly
export ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

---

## Configuration Reference

### Complete Field List

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `environment` | Literal | "development" | Runtime environment |
| `chunk_size` | int | 1000 | Characters per chunk |
| `chunk_overlap` | int | 300 | Overlap between chunks |
| `batch_size` | int | 5000 | Batch size for operations |
| `embedding_model` | str | "BAAI/bge-large-en-v1.5" | Embedding model |
| `embedding_device` | Literal | "auto" | cuda/cpu/auto |
| `llm_model` | str | "claude-opus-4-5" | Primary LLM |
| `llm_thinking_budget` | int | 10000 | Thinking tokens |
| `llm_timeout` | int | 120 | Request timeout (seconds) |
| `retrieval_total_chunks` | int | 20 | Chunks to retrieve |
| `retrieval_rerank_top_k` | int | 10 | Top K after reranking |
| `log_level` | str | "INFO" | Logging level |
| `log_format` | Literal | "text" | json/text |

For complete list, see `config/base.py`.

---

## Best Practices

1. **Use get_settings() in Application Code**

   ```python
   # Good
   config = get_settings()

   # Avoid (unless testing)
   config = DevelopmentConfig()
   ```

2. **Use reload_settings() in Tests**

   ```python
   def test_something():
       os.environ["ENVIRONMENT"] = "testing"
       config = reload_settings()
   ```

3. **Don't Modify Config After Load**

   ```python
   # Bad - mutations won't propagate
   config = get_settings()
   config.chunk_size = 2000

   # Good - use environment variables
   os.environ["CHUNK_SIZE"] = "2000"
   config = reload_settings()
   ```

4. **Use Type Hints**

   ```python
   from config.base import BaseConfig

   def process(config: BaseConfig):
       # Editor autocomplete works
       size = config.chunk_size
   ```

---

## Related Documentation

- [Security Guide](./SECURITY.md) - Secrets management
- [Error Handling Guide](./ERROR_HANDLING.md) - ConfigurationError
- [Validation Guide](./VALIDATION.md) - Input validation
