import chromadb
from src.schemas import Chunk
from src.rag.embeddings import embed_texts

PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "project_knowledge_base"


def get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return collection


def _sanitize_metadata(metadata: dict) -> dict:
    clean = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean


def delete_by_filename(filename: str):
    collection = get_collection()
    try:
        collection.delete(where={"filename": filename})
    except Exception:
        pass


def index_chunks(chunks: list[Chunk]):
    if not chunks:
        print("No chunks to index.")
        return

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


def search(query: str, top_k: int = 5, where: dict | None = None):
    collection = get_collection()
    query_embedding = embed_texts([query])[0]

    query_kwargs = {"query_embeddings": [query_embedding], "n_results": top_k}
    if where:
        query_kwargs["where"] = where

    return collection.query(**query_kwargs)