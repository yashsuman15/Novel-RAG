from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". "]
        )

    def split_documents(self, documents: list) -> list:
        return self.text_splitter.split_documents(documents)
    
if __name__ == "__main__":
    from ingestion.loader import load_documents
    
    documents = load_documents()
    splitter = DocumentSplitter()
    chunks = splitter.split_documents(documents)
    
    print(f"Split into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:5]):  # Print the first 5 chunks
        print(f"Chunk {i+1}: {chunk.page_content[:200]}...")