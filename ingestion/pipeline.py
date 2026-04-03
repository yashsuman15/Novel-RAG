from ingestion.loader import load_documents
from ingestion.splitter import DocumentSplitter
from ingestion.vectorstore import VectorStore
from exceptions import IngestionError
import logging

logger = logging.getLogger(__name__)


def run_pipeline():
    """
    Run complete ingestion pipeline.
    
    Raises:
        IngestionError: If any step fails
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
            "Ingestion pipeline failed",
            details={"error": str(e), "error_type": type(e).__name__}
        ) from e


if __name__ == "__main__":
    run_pipeline()