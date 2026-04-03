from langchain_huggingface import HuggingFaceEmbeddings
from config import get_settings
from exceptions import EmbeddingError, DeviceError
import torch
import logging


logger = logging.getLogger(__name__)


class Embeddings:
    def __init__(self):
        setting = get_settings()
        
        device = setting.embedding_device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")

        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA is not available, using CPU instead")
            device = "cpu"

        try:
            logger.info(f"Loading embedding model: {setting.embedding_model} on {device}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=setting.embedding_model,
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": setting.normalize_embeddings}
            )
            self.device = device
            self.model_name = setting.embedding_model
            logger.info(f"Embedding model loaded successfully on {device}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise EmbeddingError(
                f"Failed to load embedding model",
                details={
                    "model_name": setting.embedding_model, 
                    "device": device,
                    "error": str(e),
                }
            ) from e
        


    def embed_documents(self, documents: list) -> list:
        try:
            texts = [doc.page_content for doc in documents]
            logger.debug(f"Embedding {len(texts)} documents")
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"Failed to embed documents: {e}")
            raise EmbeddingError(
                f"Failed to embed documents",
                details={
                    "num_documents": len(documents),
                    "error": str(e),
                }
            ) from e

    def embed_query(self, query: str) -> list:
        try:
            logger.debug(f"Embedding query: {query}")
            return self.embeddings.embed_query(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise EmbeddingError(
                f"Failed to embed query",
                details={
                    "query": query,
                    "error": str(e),
                }
            ) from e

    
