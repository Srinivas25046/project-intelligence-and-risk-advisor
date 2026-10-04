# Project Intelligence & Risk Advisor

An AI-driven platform that ingests enterprise project documents — proposals, reports, task lists, meeting notes — and uses a Retrieval-Augmented Generation (RAG) pipeline with specialized AI agents to automatically surface project risks, scope gaps, and health insights, presented through an interactive dashboard.

Built as part of an Infosys Springboard internship project on AI-driven enterprise project intelligence.

## Features

- **Multi-format document ingestion** — parses PDF, DOCX, CSV, and TXT project documents into a unified text representation, restricted to these supported types at upload
- **Semantic + hybrid search** — documents are chunked, embedded, and indexed in a vector database; retrieval combines semantic similarity with exact metadata filtering and multi-query merging
- **Fully automatic end-to-end analysis** — one click runs ingestion, all extraction agents, documentation generation, and health scoring with no further manual steps
- **Multi-agent extraction pipeline** — specialized agents extract scope, risks, and blockers/action items, each reasoning over retrieved content via LLMs
- **Resilient, multi-provider LLM backend** — Google Gemini, Groq, and Cloudflare Workers AI in a rotating fallback chain per agent, with in-loop JSON validation so a malformed response triggers fallback instead of being accepted
- **Automatic documentation generation** — Agile user stories, a risk register with mitigation suggestions, and a consolidated action item list, generated automatically and downloadable as a Word document
- **Deterministic, explainable health scoring** — an auditable formula across scope clarity, timeline risk, and blocker load, not an opaque AI-generated number
- **Conversational assistant** — hybrid-grounded Q&A combining a persisted project summary with live document retrieval, presented as a floating chat popup
- **Incremental document updates** — add new documents at any time; only new or changed files are re-embedded, while extraction agents fully re-run so conclusions always reflect the complete, current picture
- **Polished interactive dashboard** — built with Streamlit, featuring a health gauge, severity-coded risk/blocker views, and an "at a glance" summary strip

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Document parsing | pypdf, python-docx, pandas |
| Chunking | LangChain text splitters |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| Vector store | ChromaDB |
| LLM reasoning | Google Gemini, Groq, Cloudflare Workers AI (via OpenAI-compatible client) |
| Document export | python-docx |
| UI | Streamlit, Plotly |

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
  Vector store     ──▶  indexed for fast semantic + hybrid similarity search
        │
        ▼
  Agent retrieval   ──▶  each agent pulls the context relevant to its question,
                          always including the latest document batch
        │
        ▼
  LLM reasoning      ──▶  multi-provider fallback chain (Gemini → Groq → Cloudflare)
        │
        ▼
  Structured JSON ──▶  Documentation generation ──▶ Health scoring
        │
        ▼
  Interactive dashboard + conversational assistant
```

## Project Structure

```
project-intelligence-and-risk-advisor/
├── .streamlit/
│   └── config.toml         # native Streamlit theming
├── data/raw/                # source project documents
├── output/
│   ├── insights/            # saved agent outputs (scope, risks, blockers, health, docs)
│   ├── ingestion_manifest.json  # tracks which files are already indexed
│   └── last_batch.json      # tracks the most recent ingestion batch
├── src/
│   ├── schemas.py            # core data models (Document, Chunk)
│   ├── ingestion/            # per-format document loaders + incremental manifest
│   ├── rag/                  # chunking, embeddings, vector store
│   ├── llm/                  # multi-provider LLM client with fallback
│   ├── agents/                # scope, risk, blocker, and documentation agents
│   ├── chat_agent.py          # conversational assistant
│   ├── health_score.py        # deterministic health scoring
│   ├── doc_export.py          # Word document generation
│   ├── main.py                 # ingestion pipeline entry point (CLI)
│   └── run_agents.py           # runs all agents against indexed data (CLI)
├── app.py                     # Streamlit dashboard entry point
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

Create a `.env` file in the project root with your free-tier API keys:

```
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

## Usage

**Interactive dashboard (recommended):**

```bash
streamlit run app.py
```

Upload PDF/DOCX/CSV/TXT files, click **Run Full Analysis**, and explore the Health, Scope, Risks, Blockers, and Documentation tabs. Add further documents at any time via **Add More Documents** to incrementally update the knowledge base and refresh all insights. Use the floating chat icon to ask questions about the project.

**Command-line pipeline (for development/testing):**

```bash
python -m src.main          # ingest documents and build the vector index
python -m src.run_agents    # run all extraction agents and save insights
python -m src.health_score  # compute the deterministic health score
python -m src.chat_agent    # interactive terminal chat session
```

## License

MIT — see [LICENSE](LICENSE).