from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader
from config import get_settings
from expceptions import DocumentLoadingError
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_documents(directory: str = None) -> list:

    settings = get_settings()

    if directory is None:
        directory = str(settings.raw_data_dir)

    dir_path = Path(directory)
    if not dir_path.exists():
        raise DocumentLoadingError(
            f"Directory not found: {directory}",
            details={
                "directory": directory,
            }
        )
    
    if not dir_path.is_dir():
        raise DocumentLoadingError(
            f"Directory is not a directory: {directory}",
            details={
                "directory": directory,
            }
        )
    
    try:
        logger.info(f"Loading documents from {directory}")
        loader = DirectoryLoader(
            directory, 
            glob="**/*.pdf", 
            show_progress=True, 
            loader_cls=UnstructuredPDFLoader
            )
        documents = loader.load()

        if not documents:
            logger.warning(f"No documents found in {directory}")
            return []
        
        logger.info(f"Loaded {len(documents)} documents")
        return documents

    except Exception as e:
        logger.error(f"Failed to load documents: {e}")
        raise DocumentLoadingError(
            "Failed to load documents",
            details={
                "directory": directory,
                "error": str(e),
            }
        ) from e

if __name__ == "__main__":
    documents = load_documents()
    print(f"Loaded {len(documents)} documents")
    for doc in documents:  # Print the first 10 documents
        print(f"Document: {doc.metadata['source']}, Page: {doc.metadata.get('page', 'N/A')}")