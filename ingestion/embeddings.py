from langchain_huggingface import HuggingFaceEmbeddings


class Embeddings:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={"device": "cuda"},
            encode_kwargs={"normalize_embeddings": True}
        )

    def embed_documents(self, documents: list) -> list:
        texts = [doc.page_content for doc in documents]
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> list:
        return self.embeddings.embed_query(query)

    
