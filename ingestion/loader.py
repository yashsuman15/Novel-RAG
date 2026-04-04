"""Document loading module for the ingestion pipeline.

Provides functionality to load PDF documents from the filesystem
using LangChain's :class:`DirectoryLoader` with the
:class:`UnstructuredPDFLoader` backend.
"""

import logging
from pathlib import Path

from expceptions import DocumentLoadingError
from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader

from config import get_settings

logger = logging.getLogger(__name__)


def load_documents(directory: str | None = None) -> list:
    """Load all PDF documents from a directory.

    Recursively scans the target directory for ``*.pdf`` files and
    returns them as LangChain :class:`Document` objects with metadata
    (source path, page number, etc.).

    Args:
        directory: Absolute or relative path to the directory containing
            PDF files. If ``None``, defaults to the ``raw_data_dir``
            path from application settings.

    Returns:
        A list of :class:`~langchain_core.documents.Document` objects.
        Returns an empty list if no PDFs are found.

    Raises:
        DocumentLoadingError: If the directory does not exist, is not a
            directory, or if loading fails for any other reason.

    Example:
        >>> docs = load_documents("data/raw")
        >>> print(len(docs))
        42
    """
    settings = get_settings()

    if directory is None:
        directory = str(settings.raw_data_dir)

    dir_path = Path(directory)
    if not dir_path.exists():
        raise DocumentLoadingError(
            f"Directory not found: {directory}",
            details={
                "directory": directory,
            },
        )

    if not dir_path.is_dir():
        raise DocumentLoadingError(
            f"Directory is not a directory: {directory}",
            details={
                "directory": directory,
            },
        )

    try:
        logger.info(f"Loading documents from {directory}")
        loader = DirectoryLoader(
            directory, glob="**/*.pdf", show_progress=True, loader_cls=UnstructuredPDFLoader
        )
        documents = loader.load()

        if not documents:
            logger.warning(f"No documents found in {directory}")
            return []

        logger.info(f"Loaded {len(documents)} documents")
        return list(documents)

    except Exception as e:
        logger.error(f"Failed to load documents: {e}")
        raise DocumentLoadingError(
            "Failed to load documents",
            details={
                "directory": directory,
                "error": str(e),
            },
        ) from e


if __name__ == "__main__":
    documents = load_documents()
    print(f"Loaded {len(documents)} documents")
    for doc in documents:  # Print the first 10 documents
        print(f"Document: {doc.metadata['source']}, Page: {doc.metadata.get('page', 'N/A')}")
