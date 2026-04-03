from langchain_chroma import Chroma
from ingestion.embeddings import Embeddings
from config import get_settings
from exceptions import VectorStoreError
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_directory: str = None, collection_name: str = None):

        self.settings = get_settings()

        self.persist_directory = persist_directory if persist_directory is not None else self.settings.vector_store_dir

        self.collection_name = collection_name if collection_name is not None else self.settings.vector_store_collection

        self.batch_size = self.settings.batch_size

        try:
            self.settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Vector store directory: {self.persist_directory}")

        except Exception as e:
            raise VectorStoreError(
                f"Failed to create vector store directory",
                details={
                    "vector_store_dir": self.persist_directory,
                    "error": str(e),
                }
            ) from e

        try:
            logger.info("Initializing embeddings for vector store")
            self.embeddings = Embeddings()
            logger.info("Embeddings initialized successfully")

        except Exception as e:
            raise VectorStoreError(
                "Failed to initialize embeddings",
                details={
                    "error": str(e),
                }
            ) from e

        try:
            logger.info(f"Loading vector store: {self.persist_directory}")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                collection_name=self.collection_name,
                embedding_function=self.embeddings.embeddings,
            )
            logger.info("Vector store loaded successfully")

        except Exception as e:
            raise VectorStoreError(
                "Failed to load vector store",
                details={
                    "vector_store_dir": self.persist_directory,
                    "collection_name": self.collection_name,
                    "error": str(e),
                }
            ) from e

    def get_existing_sources(self) -> set:
        """Get all PDF sources already stored in ChromaDB."""
        try:
            collection = self.vector_store._collection
            result = collection.get(include=["metadatas"])
            sources = set()
            for metadata in result["metadatas"]:
                if metadata and "source" in metadata:
                    sources.add(metadata["source"])
            logger.info(f"Found {len(sources)} existing sources")
            return sources
        except Exception as e:
            logger.error(f"Failed to get existing sources: {e}")
            raise VectorStoreError(
                "Failed to get existing sources",
                details={
                    "error": str(e),
                }
            ) from e

    def filter_new_documents(self, chunks: list) -> list:
        """Filter out chunks from PDFs already in the vector store."""
        existing_sources = self.get_existing_sources()
        new_chunks = [chunk for chunk in chunks if chunk.metadata.get("source") not in existing_sources]
        skipped = len(chunks) - len(new_chunks)
        if skipped > 0:
            logger.info(f"Skipped {skipped} chunks (already in ChromaDB)")
        return new_chunks

    def add_documents(self, chunks: list):
        """Add only new document chunks to the vector store in batches."""
        new_chunks = self.filter_new_documents(chunks)
        
        if not new_chunks:
            logger.info("No new documents to add — everything is already ingested.")
            print("No new documents to add — everything is already ingested.")
            return
        
        try:
            logger.info(f"Adding {len(new_chunks)} new chunks in batches of {self.batch_size}")
            for i in range(0, len(new_chunks), self.batch_size):
                batch = new_chunks[i:i + self.batch_size]
                self.vector_store.add_documents(batch)
                batch_num = i // self.batch_size + 1
                logger.info(f"Batch {batch_num}: Added {len(batch)} chunks")
                print(f"Batch {batch_num}: Added {len(batch)} chunks")
            
            logger.info(
                f"Total: Added {len(new_chunks)} new chunks to ChromaDB "
                f"at '{self.persist_directory}'"
            )
            print(
                f"Total: Added {len(new_chunks)} new chunks to ChromaDB "
                f"at '{self.persist_directory}'"
            )
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise VectorStoreError(
                "Failed to add documents to vector store",
                details={
                    "num_chunks": len(new_chunks),
                    "batch_size": self.batch_size,
                    "error": str(e)
                }
            ) from e

    def search(self, query: str, total_chunks: int = None) -> list:
        """Semantic search - returns top k most relevant chunks."""
        
        k = total_chunks if total_chunks is not None else self.settings.retrieval_total_chunks

        try:
            logger.debug(f"Searching for: '{query[:50]}...' (k={k})")
            results = self.vector_store.similarity_search(query, k=k)
            logger.debug(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorStoreError(
                "Failed to perform vector search",
                details={"query": query[:100], "k": k, "error": str(e)}
            ) from e

    def search_with_scores(self, query: str, total_chunks: int = None) -> list:
        """Semantic search with relevance scores."""
        
        k = total_chunks if total_chunks is not None else self.settings.retrieval_total_chunks

        try:
            logger.debug(f"Searching for: '{query[:50]}...' (k={k})")
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.debug(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorStoreError(
                "Failed to perform vector search",
                details={"query": query[:100], "k": k, "error": str(e)}
            ) from e


if __name__ == "__main__":
    store = VectorStore()
    results = store.search("What is this document about?")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Content: {doc.page_content[:200]}...")
