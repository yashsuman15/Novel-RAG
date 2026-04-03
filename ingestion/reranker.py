from sentence_transformers import CrossEncoder
from config import get_settings
from exceptions import RerankingError
import logging

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, model_name: str = None):
        
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
                }
            ) from e

    def rerank(self, query: str, documents: list, top_k: int = 5) -> list:

        if not documents:
            logger.warning("No documents to rerank")
            return []
        
        if top_k > len(documents):
            logger.warning(
                f"top_k ({top_k}) is greater than the number of documents ({len(documents)})")
            top_k = len(documents)


        try:
            logger.debug(
                f"Reranking {len(documents)} documents for query: {query}, "
                f"keeping top {top_k}"
            )

            # Score each (query, chunk) pair
            pairs = [(query, doc.page_content) for doc in documents]
            scores = self.model.predict(pairs)

            # Sort by score (highest = most relevant), keep top_k
            scored_docs = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)
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
                }
            ) from e