from ingestion.loader import load_documents
from ingestion.splitter import DocumentSplitter
from ingestion.vectorstore import VectorStore

def run_pipeline():
    # Step 1: Load PDFs
    documents = load_documents()

    # Step 2: Split into chunks
    splitter = DocumentSplitter()
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    # Step 3: Embed + Store in ChromaDB (done in one step)
    store = VectorStore()
    store.add_documents(chunks)

    # Step 4: Test a search
    results = store.search("who is orsted?", k=2)
    print(f"\n--- Top 3 search results ---")
    for i, doc in enumerate(results):
        print(doc)
        print("--------------------------------")
        print(f"\nResult {i+1} [{doc.metadata.get('source', 'N/A')}]:")
        print(f"  {doc.page_content[:200]}...")
        print("================================")

if __name__ == "__main__":
    run_pipeline()