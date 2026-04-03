from retrieval.retriever import Retriever
from llm.model import LLM
from config import get_settings
from schemas.validation import QueryRequest
from exceptions import ValidationError, RAGException
from pydantic import ValidationError as PydanticValidationError
import logging

logger = logging.getLogger(__name__)


class RAGChain:
    def __init__(self):
        try:
            logger.info("Initializing RAGChain")
            self.retriever = Retriever()
            self.llm = LLM()
            self.setting = get_settings()
            logger.info("RAGChain initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAGChain: {e}")
            raise RAGException(
                "Failed to initialize RAGChain", details={"error": str(e)}
            ) from e

    def run(
        self,
        query: str,
        total_chunks: int = None,
        rerank_top_k: int = None,
        num_queries: int = None,
    ) -> str:

        try:
            logger.debug(f"Running RAGChain with query: {query[:50]}...")
            request = QueryRequest(
                query=query, top_k=total_chunks, num_queries=num_queries
            )
            clean_query = request.query
            self.rerank_top_k = rerank_top_k if rerank_top_k is not None else self.setting.retrieval_rerank_top_k
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
                    "error": type(e).__name__,
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
