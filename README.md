# Project Intelligence & Risk Advisor

An AI-driven platform that ingests enterprise project documents — proposals, reports, task lists, meeting notes — and uses a Retrieval-Augmented Generation (RAG) pipeline with specialized AI agents to automatically surface project risks, scope gaps, and health insights.

Built as part of an Infosys Springboard internship project on AI-driven enterprise project intelligence.

## Features

- **Multi-format document ingestion** — parses PDF, DOCX, CSV, and TXT project documents into a unified text representation
- **Semantic search over project knowledge** — documents are chunked, embedded, and indexed in a vector database, enabling retrieval by meaning rather than exact keyword match
- **Hybrid retrieval** — combines semantic similarity search with exact metadata filtering (e.g. filtering CSV rows by task status) and multi-query merging, so structured facts aren't missed just because they're not the top semantic match
- **Multi-agent extraction pipeline** — specialized agents reason over retrieved content to produce structured insights:
  - **Scope agent** — extracts project goals, deliverables, milestones, and team responsibilities
  - **Risk agent** — identifies risks, rates their severity and likely impact, and writes a delivery forecast
  - **Blocker agent** — extracts active blockers and action items, cross-referencing task status so nothing blocked slips through
- **Resilient, multi-provider LLM backend** — each agent calls out to Google Gemini, Groq, and Cloudflare Workers AI in a rotating fallback chain, so a single provider's rate limit, outage, or deprecated model doesn't take down the pipeline
- **Local, cost-free embeddings** — runs entirely on CPU with no external API dependency for the retrieval layer
- **Documentation generation** — produces Agile user stories, a formal risk register with mitigation suggestions, and a consolidated action item list, chained from earlier agents' structured output
- **Deterministic health scoring** — auditable, formula-based project health score (scope clarity, timeline risk, blocker load) rather than an LLM-generated number
- **Conversational assistant** — hybrid-grounded Q&A combining a persisted project summary with live document retrieval for specific detail questions
- **Streamlit dashboard** — a live UI wrapping the full pipeline: ingestion, extraction agents, documentation generation, health scoring, and the conversational assistant, each triggered step-by-step for demo purposes

**Planned:**
- [ ] Project health scoring dashboard
- [ ] Conversational Q&A interface over the project knowledge base
- [ ] Cross-document timeline and dependency tracking

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Document parsing | pypdf, python-docx, pandas |
| Chunking | LangChain text splitters |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| Vector store | ChromaDB |
| LLM reasoning | Google Gemini, Groq, Cloudflare Workers AI (via OpenAI-compatible client) |
| UI | Streamlit |

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
  Agent retrieval   ──▶  each agent pulls the context relevant to its question
        │
        ▼
  LLM reasoning      ──▶  multi-provider fallback chain (Gemini → Groq → Cloudflare)
        │
        ▼
  Structured JSON output (scope / risks / blockers)
```

## Project Structure

```
project-intelligence-and-risk-advisor/
├── data/raw/               # source project documents
├── src/
│   ├── schemas.py          # core data models (Document, Chunk)
│   ├── ingestion/          # per-format document loaders
│   ├── rag/                # chunking, embeddings, vector store
│   ├── llm/                # multi-provider LLM client with fallback
│   ├── agents/              # scope, risk, and blocker extraction agents
│   ├── main.py              # ingestion pipeline entry point
│   └── run_agents.py        # runs all agents against the indexed data
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

**1. Ingest documents and build the vector index:**

Place project documents in `data/raw/`, then run:

```bash
python -m src.main
```

This parses every document, chunks it, generates embeddings, and stores everything in a local ChromaDB index.

**2. Run the extraction agents:**

```bash
python -m src.run_agents
```

This retrieves relevant context for each agent, sends it to an LLM for reasoning, and prints structured JSON output for scope, risks, and blockers/action items.

**3. Launch the interactive dashboard:**

```bash
streamlit run app.py
```

Opens a browser UI where each pipeline stage (ingestion, agents, documentation, health score) runs on demand via sidebar buttons, with a chat tab for querying the project interactively.

## License

MIT — see [LICENSE](LICENSE).
