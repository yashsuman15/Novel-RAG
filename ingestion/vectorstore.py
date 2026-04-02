from langchain_chroma import Chroma
from ingestion.embeddings import Embeddings


class VectorStore:
    def __init__(self, persist_directory: str = "data/vector_store", collection_name: str = "rag_collection"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embeddings = Embeddings()
        
        # ChromaDB auto-persists to disk at this path
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings.embeddings,
            persist_directory=persist_directory,
        )

    def get_existing_sources(self) -> set:
        """Get all PDF sources already stored in ChromaDB."""
        collection = self.vector_store._collection
        result = collection.get(include=["metadatas"])
        sources = set()
        for metadata in result["metadatas"]:
            if metadata and "source" in metadata:
                sources.add(metadata["source"])
        return sources

    def filter_new_documents(self, chunks: list) -> list:
        """Filter out chunks from PDFs already in the vector store."""
        existing_sources = self.get_existing_sources()
        new_chunks = [chunk for chunk in chunks if chunk.metadata.get("source") not in existing_sources]
        skipped = len(chunks) - len(new_chunks)
        if skipped > 0:
            print(f"Skipped {skipped} chunks (already in ChromaDB)")
        return new_chunks

    def add_documents(self, chunks: list, batch_size: int = 5000):
        """Add only new document chunks to the vector store in batches."""
        new_chunks = self.filter_new_documents(chunks)
        if new_chunks:
            for i in range(0, len(new_chunks), batch_size):
                batch = new_chunks[i:i + batch_size]
                self.vector_store.add_documents(batch)
                print(f"Batch {i // batch_size + 1}: Added {len(batch)} chunks")
            print(f"Total: Added {len(new_chunks)} new chunks to ChromaDB at '{self.persist_directory}'")
        else:
            print("No new documents to add — everything is already ingested.")

    def search(self, query: str, total_chunks: int = 5) -> list:
        """Semantic search - returns top k most relevant chunks."""
        results = self.vector_store.similarity_search(query, k=total_chunks)
        return results

    def search_with_scores(self, query: str, total_chunks: int = 5) -> list:
        """Semantic search with relevance scores."""
        results = self.vector_store.similarity_search_with_score(query, k=total_chunks)
        return results


if __name__ == "__main__":
    store = VectorStore()
    results = store.search("What is this document about?")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Content: {doc.page_content[:200]}...")
