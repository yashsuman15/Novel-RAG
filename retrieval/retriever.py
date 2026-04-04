"""Multi-query retrieval module with reranking.

Provides :class:`Retriever` which combines query expansion, vector
similarity search, and cross-encoder reranking to produce
high-quality context for answer generation.
"""

import os

# Must be set BEFORE importing libraries that read these
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["SENTENCE_TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import logging

from config import get_settings
from exceptions import RetrievalError
from ingestion.reranker import Reranker
from ingestion.vectorstore import VectorStore
from retrieval.query_expander import QueryExpander

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s")

# Silence all third-party loggers
for name in ("httpx", "httpcore", "anthropic", "sentence_transformers", "chromadb", "urllib3"):
    logging.getLogger(name).setLevel(logging.WARNING)


class Retriever:
    def __init__(self):
        """
        Initialize retriever with all components.

        Raises:
            RetrievalError: If initialization fails
        """
        try:
            logger.info("Initializing retriever components")
            self.vector_store = VectorStore()
            self.reranker = Reranker()
            self.query_expander = QueryExpander()
            logger.info("Retriever initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            raise RetrievalError("Failed to initialize retriever", details={"error": str(e)}) from e

    def get_context(
        self,
        query: str,
        total_chunks: int | None = None,
        rerank_top_k: int | None = None,
        num_queries: int | None = None,
    ) -> list:
        """
        Retrieve and rerank relevant context for query.

        Uses multi-query expansion + reranking for better results.

        Args:
            query: User query
            total_chunks: Override config total chunks (optional)
            rerank_top_k: Override config rerank top_k (optional)
            num_queries: Override config num_queries (optional)

        Returns:
            List of top-K reranked documents

        Raises:
            RetrievalError: If retrieval fails
        """
        settings = get_settings()

        # Use provided values or fall back to config
        total_chunks = total_chunks if total_chunks is not None else settings.retrieval_total_chunks
        rerank_top_k = rerank_top_k if rerank_top_k is not None else settings.retrieval_rerank_top_k
        num_queries = num_queries if num_queries is not None else settings.retrieval_num_queries

        logger.info(
            f"Retrieving context: total_chunks={total_chunks}, "
            f"rerank_top_k={rerank_top_k}, num_queries={num_queries}"
        )

        try:
            # Step 1: Expand query
            logger.debug("Expanding query")
            queries = self.query_expander.expand(query, num_queries=num_queries)
            logger.debug(f"Generated {len(queries)} queries")

            # Step 2: Search with each query
            logger.debug("Searching vector store with expanded queries")
            all_docs = []
            seen = set()
            for q in queries:
                docs = self.vector_store.search(q, total_chunks=total_chunks)
                for doc in docs:
                    doc_id = doc.page_content[:100]
                    if doc_id not in seen:
                        seen.add(doc_id)
                        all_docs.append(doc)

            logger.debug(f"Retrieved {len(all_docs)} unique documents")

            # Step 3: Rerank against ORIGINAL query
            logger.debug("Reranking documents")
            reranked = self.reranker.rerank(query, all_docs, top_k=rerank_top_k)
            logger.info(f"Context retrieval complete: {len(reranked)} documents")

            return reranked

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            raise RetrievalError(
                "Failed to retrieve context",
                details={
                    "query": query[:100],
                    "total_chunks": total_chunks,
                    "rerank_top_k": rerank_top_k,
                    "num_queries": num_queries,
                    "error": str(e),
                },
            ) from e

    def get_context_with_scores(self, query: str, k: int | None = None) -> list:
        """
        Retrieve context with similarity scores.

        Args:
            query: User query
            k: Number of results (defaults to config)

        Returns:
            List of (document, score) tuples
        """
        settings = get_settings()
        k = k if k is not None else settings.retrieval_total_chunks

        try:
            return self.vector_store.search_with_scores(query, total_chunks=k)
        except Exception as e:
            raise RetrievalError(
                "Failed to retrieve context with scores",
                details={"query": query[:100], "k": k, "error": str(e)},
            ) from e


if __name__ == "__main__":
    retriever = Retriever()
    results = retriever.get_context("Who is Orsted?")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Content: {doc.page_content[:50]}...")
