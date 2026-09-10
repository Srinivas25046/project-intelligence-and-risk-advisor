import chromadb
from src.schemas import Chunk
from src.rag.embeddings import embed_texts

PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "project_knowledge_base"

def _sanitize_metadata(metadata: dict) -> dict:
    """
    ChromaDB metadata values must be str, int, float, or bool.
    Anything else (lists, dicts, None) is converted to a string so
    indexing never fails on an unexpected metadata shape.
    """
    clean = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean


def get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    # get_or_create avoids errors when re-running during development
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return collection


def index_chunks(chunks: list[Chunk]):
    """
    Embeds and stores a list of Chunks into the vector database.
    """
    collection = get_collection()

    texts = [c.text for c in chunks]
    ids = [c.chunk_id for c in chunks]
    metadatas = [
        _sanitize_metadata({"doc_id": c.doc_id, "chunk_index": c.chunk_index, **c.metadata})
        for c in chunks
    ]

    embeddings = embed_texts(texts)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    print(f"Indexed {len(chunks)} chunks into vector store.")


def search(query: str, top_k: int = 5):
    collection = get_collection()
    query_embedding = embed_texts([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    return results