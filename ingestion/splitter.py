"""Document splitting (chunking) module for the ingestion pipeline.

Provides :class:`DocumentSplitter` which wraps LangChain's
:class:`RecursiveCharacterTextSplitter` with application-level
configuration and error handling.
"""

import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings
from exceptions import DocumentSplitError

logger = logging.getLogger(__name__)


class DocumentSplitter:
    """Split loaded documents into overlapping text chunks.

    Chunks are created using a recursive character-based strategy that
    tries paragraph breaks first, then sentence boundaries, then
    individual words.

    Attributes:
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of overlapping characters between
            consecutive chunks to preserve context across boundaries.
        text_splitter: The underlying
            :class:`RecursiveCharacterTextSplitter` instance.

    Example:
        >>> splitter = DocumentSplitter(chunk_size=500, chunk_overlap=100)
        >>> chunks = splitter.split_documents(documents)
        >>> print(len(chunks))
        1024
    """

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        """Initialize the document splitter.

        Args:
            chunk_size: Maximum characters per chunk. If ``None``,
                uses ``chunk_size`` from application settings.
            chunk_overlap: Overlap characters between chunks. If ``None``,
                uses ``chunk_overlap`` from application settings.

        Raises:
            DocumentSplitError: If ``chunk_overlap >= chunk_size``, or
                if the underlying splitter fails to initialize.
        """
        settings = get_settings()

        self.chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise DocumentSplitError(
                f"Chunk overlap ({self.chunk_overlap}) must be less than chunk size ({self.chunk_size})",
                details={
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                },
            )

        try:
            logger.info(
                f"Initializing DocumentSplitter with chunk size {self.chunk_size} and chunk overlap {self.chunk_overlap}"
            )

            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". "],
            )

            logger.info("DocumentSplitter initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize DocumentSplitter: {e}")
            raise DocumentSplitError(
                "Failed to initialize DocumentSplitter",
                details={
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "error": str(e),
                },
            ) from e

    def split_documents(self, documents: list) -> list:
        """Split a list of documents into text chunks.

        Args:
            documents: List of :class:`~langchain_core.documents.Document`
                objects to split. May be empty.

        Returns:
            A list of :class:`~langchain_core.documents.Document` chunks.
            Returns an empty list if the input is empty.

        Raises:
            DocumentSplitError: If splitting fails for any reason.
        """
        if not documents:
            logger.warning("No documents to split")
            return []

        try:
            logger.info(f"Splitting {len(documents)} documents into chunks")
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Split into {len(chunks)} chunks")
            return list(chunks)
        except Exception as e:
            logger.error(f"Failed to split documents: {e}")
            raise DocumentSplitError(
                "Failed to split documents",
                details={
                    "num_documents": len(documents),
                    "error": str(e),
                },
            ) from e


if __name__ == "__main__":
    from ingestion.loader import load_documents

    documents = load_documents()
    splitter = DocumentSplitter()
    chunks = splitter.split_documents(documents)

    print(f"Split into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:5]):  # Print the first 5 chunks
        print(f"Chunk {i+1}: {chunk.page_content[:200]}...")
