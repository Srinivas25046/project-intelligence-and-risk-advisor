from src.rag.vector_store import search

TEST_QUERIES = [
    "What is causing the release to be delayed?",
    "Which tasks are blocked?",
    "What was discussed about accessibility?",
    "What is out of scope for this project?",
    "What are the project risks?",
]


def run_query(query: str, top_k: int = 3):
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    results = search(query, top_k=top_k)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]  # lower distance = more similar

    for rank, (text, meta, dist) in enumerate(zip(documents, metadatas, distances), start=1):
        print(f"\n[{rank}] from {meta.get('filename', 'unknown')}  (distance: {dist:.4f})")
        print(f"    {text[:200].strip()}...")

    print()


if __name__ == "__main__":
    for q in TEST_QUERIES:
        run_query(q)

    # Demonstrate hybrid search: exact metadata filter + semantic ranking
    print("=" * 80)
    print("FILTERED QUERY: status = Blocked (exact match, not just semantic)")
    print("=" * 80)
    from src.rag.vector_store import search
    results = search("task", top_k=10, where={"status": "Blocked"})
    for text, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"- {text}")