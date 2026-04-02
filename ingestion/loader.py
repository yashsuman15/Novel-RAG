from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader

def load_documents(directory: str = "data/raw") -> list:
    loader = DirectoryLoader(directory, glob="**/*.pdf", show_progress=True, loader_cls=UnstructuredPDFLoader)
    documents = loader.load()
    return documents

if __name__ == "__main__":
    documents = load_documents()
    print(f"Loaded {len(documents)} documents")
    for doc in documents:  # Print the first 10 documents
        print(f"Document: {doc.metadata['source']}, Page: {doc.metadata.get('page', 'N/A')}")