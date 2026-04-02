from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list, top_k: int = 5) -> list:
        # Score each (query, chunk) pair
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)

        # Sort by score (highest = most relevant), keep top_k
        scored_docs = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]