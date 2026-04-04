"""Ingestion pipeline orchestration module.

Provides :func:`run_pipeline` which executes the complete document
ingestion workflow: load PDFs → split into chunks → embed and store
in ChromaDB → run a test search to verify.
"""

import logging

from exceptions import IngestionError
from ingestion.loader import load_documents
from ingestion.splitter import DocumentSplitter
from ingestion.vectorstore import VectorStore

logger = logging.getLogger(__name__)


def run_pipeline():
    """Run the complete document ingestion pipeline.

    Executes four sequential steps:

    1. **Load** — Read all PDFs from the configured raw data directory.
    2. **Split** — Chunk documents using :class:`DocumentSplitter`.
    3. **Store** — Embed chunks and insert into ChromaDB via
       :class:`VectorStore`.
    4. **Test** — Run a sample similarity search to verify the store.

    Raises:
        IngestionError: If any pipeline step fails. The ``details``
            dict includes the original error type and message.

    Example:
        >>> run_pipeline()
        Split into 2048 chunks
        Batch 1: Added 2048 chunks
        --- Top 2 search results ---
    """
    try:
        # Step 1: Load PDFs
        logger.info("Step 1: Loading documents")
        documents = load_documents()
        logger.info(f"Loaded {len(documents)} documents")

        # Step 2: Split into chunks
        logger.info("Step 2: Splitting documents")
        splitter = DocumentSplitter()
        chunks = splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")

        # Step 3: Embed + Store in ChromaDB
        logger.info("Step 3: Storing in vector database")
        store = VectorStore()
        store.add_documents(chunks)

        # Step 4: Test a search
        logger.info("Step 4: Testing search")
        results = store.search("who is orsted?", total_chunks=2)
        print(f"\n--- Top {len(results)} search results ---")
        for i, doc in enumerate(results):
            print(f"\nResult {i+1} [{doc.metadata.get('source', 'N/A')}]:")
            print(f"  {doc.page_content[:200]}...")
            print("=" * 50)

        logger.info("Ingestion pipeline completed successfully")

    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise IngestionError(
            "Ingestion pipeline failed", details={"error": str(e), "error_type": type(e).__name__}
        ) from e


if __name__ == "__main__":
    run_pipeline()
