# 📚 Novel RAG — Retrieval Augmented Generation Pipeline

A modular RAG pipeline built with Python, LangChain, ChromaDB, and Anthropic Claude. Designed for semantic search and question-answering over PDF documents with advanced retrieval techniques including query expansion and cross-encoder reranking.

---

## ✨ Features

- **PDF Ingestion** — Load PDFs from nested directories with smart text extraction
- **Semantic Chunking** — Recursive text splitting with configurable overlap
- **Local Embeddings** — BAAI/bge-large-en-v1.5 (1024-dim, CUDA-accelerated)
- **ChromaDB Vector Store** — Persistent storage with incremental ingestion (no duplicates)
- **Query Expansion** — LLM-powered multi-query generation for broader retrieval
- **Cross-Encoder Reranking** — ms-marco-MiniLM-L-6-v2 for precision re-scoring
- **Streaming Responses** — Token-by-token output with Claude Opus (extended thinking) and Sonnet
- **Source Citations** — Numbered references with PDF source and page tracking
- **Interactive Chat** — Conversational loop for continuous Q&A

---

## 🏗️ Project Structure

```text
rag_book/
├── data/
│   ├── raw/                          # Source PDFs (supports nested subdirectories)
│   └── vector_store/                 # ChromaDB persistence (auto-generated)
│
├── ingestion/                        # 📥 Data ingestion pipeline
│   ├── loader.py                     # PDF loading (UnstructuredPDFLoader)
│   ├── splitter.py                   # Text chunking (RecursiveCharacterTextSplitter)
│   ├── embeddings.py                 # Embedding model (BAAI/bge-large-en-v1.5)
│   ├── vectorstore.py                # ChromaDB store (incremental, batched inserts)
│   ├── reranker.py                   # Cross-encoder reranker (ms-marco-MiniLM-L-6-v2)
│   └── pipeline.py                   # Ingestion orchestrator
│
├── retrieval/                        # 🔍 Retrieval layer
│   ├── __init__.py
│   ├── query_expander.py             # LLM-powered query expansion (Claude Sonnet)
│   └── retriever.py                  # Multi-query search + reranking
│
├── llm/                              # 🤖 Language model layer
│   ├── __init__.py
│   ├── model.py                      # LLM (Opus w/ thinking) + LLM_lite (Sonnet)
│   └── prompt_templates.py           # System prompts
│
├── chain/                            # 🔗 RAG chain
│   ├── __init__.py
│   └── rag_chain.py                  # Retriever + LLM + citations → answer
│
├── main.py                           # Entry point
├── pyproject.toml                    # Dependencies (managed with uv)
├── .env                              # API keys (ANTHROPIC_API_KEY)
└── .gitignore
```

---

## 🔄 How It Works

### Pipeline Architecture

```text
                        ┌──────────────────────────────────┐
                        │         INGESTION (one-time)      │
                        │                                    │
  PDFs in data/raw/ ──► │  Loader ──► Splitter ──► ChromaDB │
                        │  (extract)  (chunk)     (embed +   │
                        │                          store)    │
                        └──────────────────────────────────┘

                        ┌──────────────────────────────────┐
                        │         QUERY (real-time)         │
                        │                                    │
  User Question ──────► │  Query     ──► Multi-Query ──► Rerank │
                        │  Expander      Search           │
                        │  (Sonnet)      (ChromaDB)   (Cross-  │
                        │                              Encoder)│
                        │                    │                │
                        │                    ▼                │
                        │              Top-K Chunks           │
                        │                    │                │
                        │                    ▼                │
                        │         Claude Opus (w/ thinking)   │
                        │                    │                │
                        │                    ▼                │
                        │          Answer + Citations         │
                        └──────────────────────────────────┘
```

### Step-by-Step Flow

#### 1. Ingestion (`uv run python -m ingestion.pipeline`)

| Step | Component | What It Does |
|------|-----------|-------------|
| 1 | **Loader** | Scans `data/raw/` recursively for `*.pdf`, extracts text using UnstructuredPDFLoader |
| 2 | **Splitter** | Splits documents into 1000-char chunks with 300-char overlap using smart separators (`\n\n`, `\n`, `.`) |
| 3 | **Embeddings** | Converts each chunk to a 1024-dim vector using `BAAI/bge-large-en-v1.5` on CUDA |
| 4 | **VectorStore** | Checks for existing sources (incremental), inserts new chunks in batches of 5000 into ChromaDB |

#### 2. Query (`uv run python -m chain.rag_chain`)

| Step | Component | What It Does |
|------|-----------|-------------|
| 1 | **Query Expander** | Uses Claude Sonnet to generate multiple search queries from different angles |
| 2 | **Retriever** | Searches ChromaDB with each expanded query, deduplicates results |
| 3 | **Reranker** | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) re-scores all candidates, keeps top-K |
| 4 | **RAG Chain** | Formats numbered context with source labels, sends to Claude Opus with extended thinking |
| 5 | **Response** | Streams answer token-by-token with `[1]`, `[2]` source citations + full source list |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- CUDA-capable GPU (recommended)
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd rag_basic

# Install dependencies
uv sync

# Set up environment variables
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

### Usage

```bash
# Step 1: Add PDFs to data/raw/ (supports nested subdirectories)
cp your-documents/*.pdf data/raw/

# Step 2: Run ingestion pipeline (one-time, or when new PDFs are added)
uv run python -m ingestion.pipeline

# Step 3: Start chatting
uv run python -m chain.rag_chain
```

### Example Session

```text
Ask me anything about the story!
You: Who is Orsted?

🧠 Thinking...

Orsted is the Dragon God, a powerful figure who has been fighting
against Hitogami across multiple cycles [1]. His face is intimidating,
though it has softened recently [1][2]. He values trusted companions
and works closely with Rudeus [3].

📚 Sources:
  [1] data/raw/With Orsted ENG.pdf (page 1)
  [2] data/raw/With Orsted ENG.pdf (page 3)
  [3] data/raw/MT_Novels/volume_15.pdf (page 42)

You: /exit
```

---

## 🧩 Key Components

### Embedding Model

- **Model**: `BAAI/bge-large-en-v1.5`
- **Dimensions**: 1024
- **Size**: ~1.3GB
- **Device**: CUDA (GPU-accelerated)
- **Normalization**: Enabled

### Reranker

- **Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Type**: Cross-encoder (scores query-document pairs)
- **Usage**: Retrieves top-20 candidates, reranks to top-10

### LLM Models

| Model | Class | Purpose | Features |
|-------|-------|---------|----------|
| Claude Opus 4.5 | `LLM` | Final answer generation | Extended thinking, streaming |
| Claude Sonnet 4.5 | `LLM_lite` | Query expansion | Fast, cost-effective |

### Vector Store

- **Database**: ChromaDB
- **Persistence**: `data/vector_store/`
- **Distance Metric**: L2 (Euclidean)
- **Incremental**: Only ingests new PDFs, skips existing ones
- **Batch Size**: 5000 chunks per batch

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `langchain` | Orchestration framework |
| `langchain-anthropic` | Claude API integration |
| `langchain-huggingface` | Local embedding models |
| `langchain-chroma` | ChromaDB vector store |
| `langchain-community` | Document loaders |
| `chromadb` | Vector database |
| `sentence-transformers` | Embeddings + cross-encoder reranker |
| `pymupdf` | PDF text extraction |
| `unstructured[pdf]` | Advanced PDF parsing |

---

## 🛠️ Configuration

### Chunking Parameters (`ingestion/splitter.py`)

```python
chunk_size = 1000      # Characters per chunk
chunk_overlap = 300    # Overlap between chunks
separators = ["\n\n", "\n", ". "]
```

### Retrieval Parameters (`chain/rag_chain.py`)

```python
total_chunks = 20      # Candidates retrieved per query
rerank_top_k = 10      # Chunks kept after reranking
num_queries = 5        # Expanded queries generated
```

### Model Parameters (`llm/model.py`)

```python
# LLM (Opus) — for final answers
thinking_budget = 10000    # Max thinking tokens

# LLM_lite (Sonnet) — for query expansion
temperature = 0.7
```

---

## 📄 License

MIT
