"""Cross-encoder reranking module for the ingestion pipeline.

Provides :class:`Reranker` which uses a cross-encoder model to
re-score and reorder candidate documents by relevance to a query,
improving precision over embedding-only retrieval.
"""

import logging

from sentence_transformers import CrossEncoder

from config import get_settings
from exceptions import RerankingError

logger = logging.getLogger(__name__)


class Reranker:
    """Rerank retrieved documents using a cross-encoder model.

    Unlike bi-encoder embeddings (which encode query and document
    independently), the cross-encoder processes the (query, document)
    pair jointly, producing more accurate relevance scores at the
    cost of higher latency.

    Attributes:
        model_name: The HuggingFace cross-encoder model identifier
            (e.g. ``"cross-encoder/ms-marco-MiniLM-L-6-v2"``).
        model: The loaded :class:`~sentence_transformers.CrossEncoder`
            instance.

    Example:
        >>> reranker = Reranker()
        >>> top_docs = reranker.rerank("Who is Orsted?", documents, top_k=5)
    """

    def __init__(self, model_name: str | None = None):
        """Initialize the reranker with a cross-encoder model.

        Args:
            model_name: HuggingFace model identifier for the
                cross-encoder. If ``None``, uses ``reranker_model``
                from application settings.

        Raises:
            RerankingError: If the cross-encoder model fails to load.
        """
        settings = get_settings()
        self.model_name = model_name if model_name is not None else settings.reranker_model

        try:
            logger.info(f"Loading reranker model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            logger.info("Reranker model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            raise RerankingError(
                "Failed to load reranker model",
                details={
                    "model_name": self.model_name,
                    "error": str(e),
                },
            ) from e

    def rerank(self, query: str, documents: list, top_k: int = 5) -> list:
        """Rerank documents by relevance to the query.

        Scores every (query, document) pair using the cross-encoder and
        returns the ``top_k`` documents sorted by descending relevance
        score.

        Args:
            query: The user query to rank documents against.
            documents: List of :class:`~langchain_core.documents.Document`
                candidate documents to rerank.
            top_k: Number of top-scoring documents to return.
                If greater than ``len(documents)``, all documents are
                returned. Defaults to ``5``.

        Returns:
            A list of the ``top_k`` most relevant
            :class:`~langchain_core.documents.Document` objects,
            sorted by descending relevance score.

        Raises:
            RerankingError: If scoring or sorting fails.
        """
        if not documents:
            logger.warning("No documents to rerank")
            return []

        if top_k > len(documents):
            logger.warning(
                f"top_k ({top_k}) is greater than the number of documents ({len(documents)})"
            )
            top_k = len(documents)

        try:
            logger.debug(
                f"Reranking {len(documents)} documents for query: {query}, " f"keeping top {top_k}"
            )

            # Score each (query, chunk) pair
            pairs = [(query, doc.page_content) for doc in documents]
            scores = self.model.predict(pairs)

            # Sort by score (highest = most relevant), keep top_k
            scored_docs = sorted(
                zip(scores, documents, strict=False), key=lambda x: x[0], reverse=True
            )
            reranked = [doc for score, doc in scored_docs[:top_k]]

            logger.debug(
                f"Reranking completed: {len(reranked)} documents kept out of {len(documents)} "
                f"[{scored_docs[-1][0]:.3f}, {scored_docs[0][0]:.3f}]"
            )
            return reranked

        except Exception as e:
            logger.error(f"Failed to rerank documents: {e}")
            raise RerankingError(
                "Failed to rerank documents",
                details={
                    "query": query,
                    "documents_count": len(documents),
                    "error": str(e),
                },
            ) from e
