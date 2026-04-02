from ingestion.vectorstore import VectorStore
from ingestion.reranker import Reranker
from retrieval.query_expander import QueryExpander

class Retriever:
    def __init__(self):
        self.vector_store = VectorStore()
        self.reranker = Reranker()
        self.query_expander = QueryExpander()

    def get_context(self, query: str, total_chunks: int = 20, rerank_top_k: int = 10, num_queries: int = 5) -> list:
        # Step 1: Expand query into multiple search queries
        queries = self.query_expander.expand(query, num_queries=num_queries)
        
        # Step 2: Search with each query, collect all results
        all_docs = []
        seen = set()
        for q in queries:
            docs = self.vector_store.search(q, total_chunks=total_chunks)
            for doc in docs:
                doc_id = doc.page_content[:100]
                if doc_id not in seen:
                    seen.add(doc_id)
                    all_docs.append(doc)
        
        # Step 3: Rerank all collected docs against ORIGINAL query
        return self.reranker.rerank(query, all_docs, top_k=rerank_top_k)

    def get_context_with_scores(self, query: str, k: int = 20) -> list:
        return self.vector_store.search_with_scores(query, k=k)

if __name__ == "__main__":
    retriever = Retriever()
    results = retriever.get_context("Who is Orsted?")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Content: {doc.page_content[:200]}...")