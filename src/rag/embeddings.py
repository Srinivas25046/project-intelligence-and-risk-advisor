from sentence_transformers import SentenceTransformer

_model = None  # lazy-loaded singleton — loads the model into memory only once per run


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()