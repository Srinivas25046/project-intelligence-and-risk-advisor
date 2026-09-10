# Project Intelligence & Risk Advisor

An AI-driven platform that ingests enterprise project documents — proposals, reports, task lists, meeting notes — and uses a Retrieval-Augmented Generation (RAG) pipeline with specialized AI agents to automatically surface project risks, scope gaps, and health insights.

## Features

- **Multi-format document ingestion** — parses PDF, DOCX, CSV, and TXT project documents into a unified text representation
- **Semantic search over project knowledge** — documents are chunked, embedded, and indexed in a vector database, enabling retrieval by meaning rather than exact keyword match
- **Local, cost-free embeddings** — runs entirely on CPU with no external API dependency for the retrieval layer

**Planned:**
- [ ] Risk-detection agent (flags schedule, scope, and resourcing risks from ingested content)
- [ ] Scope-gap analysis agent
- [ ] Project health scoring dashboard
- [ ] Conversational Q&A interface over project knowledge base

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Document parsing | pypdf, python-docx, pandas |
| Chunking | LangChain text splitters |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| Vector store | ChromaDB |

## Architecture

```
Raw documents (PDF/DOCX/CSV/TXT)
        │
        ▼
  Ingestion layer  ──▶  normalizes every format into plain text + metadata
        │
        ▼
    Chunking      ──▶  splits text into overlapping, semantically coherent passages
        │
        ▼
   Embedding       ──▶  converts each chunk into a dense vector representation
        │
        ▼
  Vector store     ──▶  indexed for fast semantic similarity search
```

## Project Structure

```
project-intelligence-and-risk-advisor/
├── data/raw/              # source project documents
├── src/
│   ├── schemas.py         # core data models (Document, Chunk)
│   ├── ingestion/         # per-format document loaders
│   ├── rag/               # chunking, embeddings, vector store
│   └── main.py            # pipeline entry point
├── requirements.txt
├── LICENSE
└── README.md
```

## Setup

```bash
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
pip install -r requirements.txt
```

## Usage

Place project documents in `data/raw/`, then run:

```bash
python -m src.main
```

This ingests all documents, builds the vector index, and runs a sample semantic search query against it.

## License

MIT — see [LICENSE](LICENSE).
