from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import get_settings
from exceptions import DocumentSplitError
import logging

logger = logging.getLogger(__name__)



class DocumentSplitter:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        
        settings = get_settings()

        self.chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise DocumentSplitError(
                f"Chunk overlap ({self.chunk_overlap}) must be less than chunk size ({self.chunk_size})",
                details={
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                }
            )
        
        
        try:
            logger.info(
                f"Initializing DocumentSplitter with chunk size {self.chunk_size} and chunk overlap {self.chunk_overlap}"
            )

            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". "]
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
                }
            ) from e

    def split_documents(self, documents: list) -> list:
        if not documents:
            logger.warning("No documents to split")
            return []

        try:
            logger.info(f"Splitting {len(documents)} documents into chunks")
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Split into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Failed to split documents: {e}")
            raise DocumentSplitError(
                "Failed to split documents",
                details={
                    "num_documents": len(documents),
                    "error": str(e),
                }
            ) from e
    
if __name__ == "__main__":
    from ingestion.loader import load_documents
    
    documents = load_documents()
    splitter = DocumentSplitter()
    chunks = splitter.split_documents(documents)
    
    print(f"Split into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:5]):  # Print the first 5 chunks
        print(f"Chunk {i+1}: {chunk.page_content[:200]}...")