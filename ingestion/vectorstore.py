"""ChromaDB vector store module for the ingestion pipeline.

Provides :class:`VectorStore` which manages document storage,
deduplication, and semantic similarity search using ChromaDB as the
persistent vector database backend.
"""

import logging

from langchain_chroma import Chroma

from config import get_settings
from exceptions import VectorStoreError
from ingestion.embeddings import Embeddings

logger = logging.getLogger(__name__)


class VectorStore:
    """Persistent vector store backed by ChromaDB.

    Handles the lifecycle of the vector database: initialization,
    document insertion with deduplication, and similarity search.
    Documents are automatically embedded using the configured
    HuggingFace model before storage.

    Attributes:
        settings: Active application settings.
        persist_directory: Filesystem path where ChromaDB persists data.
        collection_name: Name of the ChromaDB collection.
        batch_size: Number of documents inserted per batch to manage
            memory usage.
        embeddings: :class:`~ingestion.embeddings.Embeddings` instance
            for vector generation.
        vector_store: The underlying :class:`~langchain_chroma.Chroma`
            instance.

    Example:
        >>> store = VectorStore()
        >>> store.add_documents(chunks)
        >>> results = store.search("Who is Orsted?", total_chunks=5)
    """

    def __init__(self, persist_directory: str | None = None, collection_name: str | None = None):
        """Initialize the vector store and its dependencies.

        Creates the persistence directory if it does not exist, loads
        the embedding model, and connects to (or creates) the ChromaDB
        collection.

        Args:
            persist_directory: Filesystem path for ChromaDB storage.
                If ``None``, uses ``vector_store_dir`` from settings.
            collection_name: ChromaDB collection name. If ``None``,
                uses ``vector_store_collection`` from settings.

        Raises:
            VectorStoreError: If directory creation, embedding
                initialization, or ChromaDB connection fails.
        """
        self.settings = get_settings()

        self.persist_directory = (
            persist_directory if persist_directory is not None else self.settings.vector_store_dir
        )

        self.collection_name = (
            collection_name
            if collection_name is not None
            else self.settings.vector_store_collection
        )

        self.batch_size = self.settings.batch_size

        try:
            self.settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Vector store directory: {self.persist_directory}")

        except Exception as e:
            raise VectorStoreError(
                "Failed to create vector store directory",
                details={
                    "vector_store_dir": self.persist_directory,
                    "error": str(e),
                },
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
                },
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
                },
            ) from e

    def get_existing_sources(self) -> set:
        """Retrieve all PDF source paths already stored in ChromaDB.

        Scans the collection metadata to build a set of unique source
        file paths, used for deduplication during ingestion.

        Returns:
            A set of source file path strings already present in the
            vector store.

        Raises:
            VectorStoreError: If the metadata query fails.
        """
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
                },
            ) from e

    def filter_new_documents(self, chunks: list) -> list:
        """Filter out chunks from PDFs already present in the store.

        Compares each chunk's ``source`` metadata against the set of
        existing sources and removes duplicates.

        Args:
            chunks: List of :class:`~langchain_core.documents.Document`
                chunks to filter.

        Returns:
            A list containing only chunks whose source PDF has not
            yet been ingested.
        """
        existing_sources = self.get_existing_sources()
        new_chunks = [
            chunk for chunk in chunks if chunk.metadata.get("source") not in existing_sources
        ]
        skipped = len(chunks) - len(new_chunks)
        if skipped > 0:
            logger.info(f"Skipped {skipped} chunks (already in ChromaDB)")
        return new_chunks

    def add_documents(self, chunks: list):
        """Add new document chunks to the vector store in batches.

        Automatically deduplicates by filtering out chunks from PDFs
        that have already been ingested. Remaining chunks are inserted
        in batches sized by ``batch_size`` to manage memory.

        Args:
            chunks: List of :class:`~langchain_core.documents.Document`
                chunks to add.

        Raises:
            VectorStoreError: If batch insertion fails.
        """
        new_chunks = self.filter_new_documents(chunks)

        if not new_chunks:
            logger.info("No new documents to add — everything is already ingested.")
            print("No new documents to add — everything is already ingested.")
            return

        try:
            logger.info(f"Adding {len(new_chunks)} new chunks in batches of {self.batch_size}")
            for i in range(0, len(new_chunks), self.batch_size):
                batch = new_chunks[i : i + self.batch_size]
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
                    "error": str(e),
                },
            ) from e

    def search(self, query: str, total_chunks: int | None = None) -> list:
        """Perform a semantic similarity search.

        Embeds the query and finds the ``total_chunks`` most similar
        document chunks in the vector store.

        Args:
            query: The search query string.
            total_chunks: Number of results to return. If ``None``,
                uses ``retrieval_total_chunks`` from settings.

        Returns:
            A list of :class:`~langchain_core.documents.Document`
            objects ranked by descending similarity.

        Raises:
            VectorStoreError: If the similarity search fails.
        """
        k = total_chunks if total_chunks is not None else self.settings.retrieval_total_chunks

        try:
            logger.debug(f"Searching for: '{query[:50]}...' (k={k})")
            results = self.vector_store.similarity_search(query, k=k)
            logger.debug(f"Found {len(results)} results")
            return list(results)

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorStoreError(
                "Failed to perform vector search",
                details={"query": query[:100], "k": k, "error": str(e)},
            ) from e

    def search_with_scores(self, query: str, total_chunks: int | None = None) -> list:
        """Perform a semantic similarity search with relevance scores.

        Like :meth:`search`, but returns (document, score) tuples so
        callers can inspect or threshold on similarity.

        Args:
            query: The search query string.
            total_chunks: Number of results to return. If ``None``,
                uses ``retrieval_total_chunks`` from settings.

        Returns:
            A list of ``(Document, float)`` tuples sorted by
            descending similarity score.

        Raises:
            VectorStoreError: If the similarity search fails.
        """
        k = total_chunks if total_chunks is not None else self.settings.retrieval_total_chunks

        try:
            logger.debug(f"Searching for: '{query[:50]}...' (k={k})")
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.debug(f"Found {len(results)} results")
            return list(results)

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorStoreError(
                "Failed to perform vector search",
                details={"query": query[:100], "k": k, "error": str(e)},
            ) from e


if __name__ == "__main__":
    store = VectorStore()
    results = store.search("What is this document about?")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Content: {doc.page_content[:200]}...")
