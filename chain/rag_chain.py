from retrieval.retriever import Retriever
from llm.model import LLM


class RAGChain:
    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLM()

    def run(self, query: str) -> str:
        # Step 1: Retrieve relevant chunks
        context_docs = self.retriever.get_context(query, total_chunks=20, rerank_top_k=10 ,num_queries=5)

        # Step 2: Build numbered context with source labels
        context_parts = []
        sources = []
        for i, doc in enumerate(context_docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "N/A")
            label = f"{source} (page {page})" if page != "N/A" else source
            sources.append(f"[{i}] {label}")
            context_parts.append(f"[{i}] (Source: {label})\n{doc.page_content}")

        context = "\n\n".join(context_parts)

        # Step 3: Build prompt with citation instructions
        prompt = f"""You are answering questions about a story based ONLY on the provided context.
Read ALL context passages carefully before answering.
If the answer spans multiple passages, synthesize them together.
If the context doesn't contain enough info, say so clearly.
Cite your sources using the bracket numbers like [1], [2], etc.

Context passages:
{context}

Question: {query}

Answer:"""

        # Step 4: Send to LLM
        print("\n--- Answer ---")
        self.llm.generate(prompt)

        # Step 5: Print sources
        print("\n\n📚 Sources:")
        for src in sources:
            print(f"  {src}")
        print()


if __name__ == "__main__":
    rag_chain = RAGChain()
    print("Ask me anything about the story!")
    while True:
        query = input("You: ")
        if query == "/exit":
            break
        rag_chain.run(query)