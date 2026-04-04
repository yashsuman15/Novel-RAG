"""Embedding generation module for the ingestion pipeline.

Provides :class:`Embeddings` which wraps HuggingFace sentence-transformer
models for generating dense vector representations of text, used for
semantic similarity search in the vector store.
"""

import logging

import torch
from langchain_huggingface import HuggingFaceEmbeddings

from config import get_settings
from exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class Embeddings:
    """Generate dense vector embeddings for documents and queries.

    Wraps :class:`~langchain_huggingface.HuggingFaceEmbeddings` with
    automatic device detection (CUDA / CPU) and application-level
    configuration.

    Attributes:
        embeddings: The underlying
            :class:`~langchain_huggingface.HuggingFaceEmbeddings` instance.
        device: The compute device in use (``"cuda"`` or ``"cpu"``).
        model_name: The HuggingFace model identifier
            (e.g. ``"BAAI/bge-large-en-v1.5"``).

    Example:
        >>> emb = Embeddings()
        >>> vector = emb.embed_query("Who is Orsted?")
        >>> print(len(vector))  # embedding dimension
        1024
    """

    def __init__(self):
        """Initialize the embedding model.

        Detects the best available compute device (CUDA if available,
        otherwise CPU) and loads the configured HuggingFace embedding
        model.

        Raises:
            EmbeddingError: If the embedding model fails to load
                (e.g. download failure, incompatible model).
        """
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
                encode_kwargs={"normalize_embeddings": setting.normalize_embeddings},
            )
            self.device = device
            self.model_name = setting.embedding_model
            logger.info(f"Embedding model loaded successfully on {device}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise EmbeddingError(
                "Failed to load embedding model",
                details={
                    "model_name": setting.embedding_model,
                    "device": device,
                    "error": str(e),
                },
            ) from e

    def embed_documents(self, documents: list) -> list:
        """Generate embeddings for a list of documents.

        Extracts the ``page_content`` from each document and encodes
        them in a single batch.

        Args:
            documents: List of :class:`~langchain_core.documents.Document`
                objects whose ``page_content`` will be embedded.

        Returns:
            A list of embedding vectors (each a list of floats),
            one per input document.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            texts = [doc.page_content for doc in documents]
            logger.debug(f"Embedding {len(texts)} documents")
            return list(self.embeddings.embed_documents(texts))
        except Exception as e:
            logger.error(f"Failed to embed documents: {e}")
            raise EmbeddingError(
                "Failed to embed documents",
                details={
                    "num_documents": len(documents),
                    "error": str(e),
                },
            ) from e

    def embed_query(self, query: str) -> list:
        """Generate an embedding for a single query string.

        Args:
            query: The text query to embed.

        Returns:
            A single embedding vector (list of floats).

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            logger.debug(f"Embedding query: {query}")
            return list(self.embeddings.embed_query(query))
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise EmbeddingError(
                "Failed to embed query",
                details={
                    "query": query,
                    "error": str(e),
                },
            ) from e
