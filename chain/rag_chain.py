"""RAG chain orchestration module.

Provides the top-level :class:`RAGChain` class that ties together
retrieval, reranking, context assembly, and LLM generation into a
single ``run()`` call.
"""

import logging

from pydantic import ValidationError as PydanticValidationError

from config import get_settings
from exceptions import RAGException, ValidationError
from llm.model import LLM
from retrieval.retriever import Retriever
from schemas.validation import QueryRequest

logger = logging.getLogger(__name__)


class RAGChain:
    """End-to-end Retrieval-Augmented Generation pipeline.

    Orchestrates the full question-answering workflow:

    1. Validate and sanitise the user query via :class:`QueryRequest`.
    2. Retrieve relevant document chunks with multi-query expansion.
    3. Assemble numbered context passages with source citations.
    4. Stream the answer from the LLM with inline citations.
    5. Print source references.

    Attributes:
        retriever: :class:`~retrieval.retriever.Retriever` instance for
            context retrieval.
        llm: :class:`~llm.model.LLM` instance for answer generation.
        setting: Active application settings from
            :func:`~config.get_settings`.

    Example:
        >>> chain = RAGChain()
        >>> chain.run("Who is Orsted?")
    """

    def __init__(self):
        """Initialize the RAG chain with retriever and LLM components.

        Raises:
            RAGException: If any component fails to initialize (e.g.
                embedding model download failure, API key missing).
        """
        try:
            logger.info("Initializing RAGChain")
            self.retriever = Retriever()
            self.llm = LLM()
            self.setting = get_settings()
            logger.info("RAGChain initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAGChain: {e}")
            raise RAGException("Failed to initialize RAGChain", details={"error": str(e)}) from e

    def run(
        self,
        query: str,
        total_chunks: int | None = None,
        rerank_top_k: int | None = None,
        num_queries: int | None = None,
    ) -> None:
        """Execute the full RAG pipeline for a given user query.

        The pipeline proceeds through five sequential steps:

        1. **Validate** — sanitise the query and optional overrides.
        2. **Retrieve** — fetch relevant chunks via multi-query expansion.
        3. **Assemble context** — build numbered passages with source labels.
        4. **Generate** — stream the LLM response with citation instructions.
        5. **Print sources** — display the source references used.

        Args:
            query: The user's natural-language question.
            total_chunks: Override the configured number of chunks to
                retrieve from the vector store. Defaults to ``None``
                (uses ``retrieval_total_chunks`` from settings).
            rerank_top_k: Override the configured number of top chunks
                to keep after reranking. Defaults to ``None``
                (uses ``retrieval_rerank_top_k`` from settings).
            num_queries: Override the configured number of expanded
                queries to generate. Defaults to ``None``
                (uses ``retrieval_num_queries`` from settings).

        Returns:
            The generated answer string (also printed to stdout via
            streaming).

        Raises:
            ValidationError: If the query or parameters fail validation.
            RAGException: If retrieval, context assembly, or LLM
                generation fails.
        """

        try:
            logger.debug(f"Running RAGChain with query: {query[:50]}...")
            request = QueryRequest(query=query, top_k=total_chunks, num_queries=num_queries)
            clean_query = request.query
            self.rerank_top_k = (
                rerank_top_k if rerank_top_k is not None else self.setting.retrieval_rerank_top_k
            )
            logger.debug(f"Cleaned query: {clean_query[:50]}...")

        except PydanticValidationError as e:
            logger.warning(f"Validation error: {e}")
            raise ValidationError(
                "Invalid query parameters",
                details={"errors": e.errors(), "validation_error": str(e)},
            ) from e

        try:
            logger.info(f"Retrieving context for query: {clean_query[:50]}...")

            # Step 1: Retrieve relevant chunks
            logger.debug("Retrieving Context")
            context_docs = self.retriever.get_context(
                query=clean_query,
                total_chunks=self.setting.retrieval_total_chunks,
                rerank_top_k=self.rerank_top_k,
                num_queries=request.num_queries or self.setting.retrieval_num_queries,
            )
            logger.debug("Context retrieved successfully")

            # Step 2: Build numbered context with source labels
            logger.debug("Building Context")
            context_parts = []
            sources = []
            for i, doc in enumerate(context_docs, 1):
                source = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", "N/A")
                label = f"{source} (page {page})" if page != "N/A" else source
                sources.append(f"[{i}] {label}")
                context_parts.append(f"[{i}] (Source: {label})\n{doc.page_content}")

            context = "\n\n".join(context_parts)
            logger.debug("Context built successfully")

            # Step 3: Build prompt with citation instructions
            prompt = f"""You are answering questions about a story based ONLY on the provided context.
Read ALL context passages carefully before answering.
If the answer spans multiple passages, synthesize them together.
If the context doesn't contain enough info, say so clearly.
Cite your sources using the bracket numbers like [1], [2], etc.

Context passages:
{context}

Question: {clean_query}

Answer:"""
            logger.debug("Prompt built successfully")

            # Step 4: Send to LLM
            logger.debug("Sending prompt to LLM")
            print("\n--- Answer ---")
            self.llm.generate(prompt)

            # Step 5: Print sources
            print("\n\n📚 Sources:")
            for src in sources:
                print(f"  {src}")
            print()
            logger.debug("RAG Pipeline Completed")

        except Exception as e:
            logger.error(f"Failed to run RAGChain: {e}")
            raise RAGException(
                "Failed to run RAGChain",
                details={
                    "query": clean_query[:100],
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e


if __name__ == "__main__":
    rag_chain = RAGChain()
    print("Ask me anything about the story!")
    while True:
        query = input("You: ")
        if query == "/exit":
            break
        rag_chain.run(query)
