import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from src.ingestion.loaders import load_document
from src.rag.chunking import chunk_document
from src.rag.vector_store import index_chunks, search, delete_by_filename

RAW_DATA_DIR = "data/raw"


def run_ingestion_pipeline():
    all_chunks = []

    for filename in os.listdir(RAW_DATA_DIR):
        filepath = os.path.join(RAW_DATA_DIR, filename)
        if not os.path.isfile(filepath):
            continue

        try:
            print(f"Loading: {filename}")
            document = load_document(filepath)
        except ValueError as e:
            print(f"Skipping {filename}: {e}")
            continue

        print(f"Chunking: {filename}")
        chunks = chunk_document(document)
        print(f" -> {len(chunks)} chunks created")

        delete_by_filename(filename)
        all_chunks.extend(chunks)

    print(f"\nTotal chunks across all documents: {len(all_chunks)}")
    index_chunks(all_chunks)


if __name__ == "__main__":
    run_ingestion_pipeline()

    test_query = "What are the project risks?"
    results = search(test_query, top_k=3)

    print(f"\nTop results for query: '{test_query}'")
    for doc_text, metadata in zip(results["documents"][0], results["metadatas"][0]):
        print(f"- From {metadata['filename']}: {doc_text[:150]}...")