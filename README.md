
# Project Intelligence & Risk Advisor

### AI-Powered Enterprise Project Analysis, Risk Detection & Decision Support

An AI-driven project intelligence platform that transforms unstructured enterprise project documents into actionable insights using Retrieval-Augmented Generation (RAG), specialized AI agents, and explainable project health scoring.

The platform identifies project risks, scope gaps, blockers, and action items through an interactive Streamlit dashboard.

---

## Overview

Project teams work with multiple documents, including project proposals, status reports, meeting notes, requirements, and defect trackers. Manually reviewing these documents makes it difficult to identify risks, track blockers, and maintain a consolidated view of project health.

**Project Intelligence & Risk Advisor** automates project document analysis and transforms unstructured information into structured, actionable project intelligence.

## Features

### 1. Multi-Format Document Ingestion
- Supports PDF, DOCX, CSV, and TXT documents.
- Extracts and normalizes document content.
- Prepares documents for semantic retrieval and AI analysis.

### 2. Retrieval-Augmented Generation (RAG)
- Text chunking with overlapping segments.
- Semantic embeddings using Sentence Transformers.
- Vector storage and retrieval using ChromaDB.
- Context-grounded responses based on project documents.

### 3. Multi-Agent Project Analysis
Specialized AI agents analyze:
- **Scope:** Requirements, deliverables, and potential gaps.
- **Risks:** Potential risks, severity, and mitigation strategies.
- **Blockers:** Project impediments and follow-up actions.
- **Documentation:** Structured project-management outputs.

### 4. Multi-Provider LLM Support
- Google Gemini
- Groq
- Cloudflare Workers AI

Supports provider fallback and structured JSON output validation, according to the configured implementation.

### 5. Automated Documentation
Generate project-management artifacts such as:
- Agile user stories
- Project risk registers
- Action-item lists

Export supported reports as Microsoft Word documents.

### 6. Project Health Score
Calculates a project health score using defined indicators such as:
- Scope clarity
- Timeline risk
- Blocker load

The deterministic scoring approach makes the calculation more transparent and explainable.

### 7. Conversational Project Assistant
Ask questions about project documents and receive context-aware answers using document retrieval and project context.

### 8. Incremental Document Updates
- Add new project documents.
- Track new or changed files.
- Reprocess updated documents.
- Refresh project insights when source information changes.

### 9. Interactive Dashboard
- Project health visualization
- Scope analysis
- Risk and blocker views
- Consolidated project summary
- Documentation export
- Conversational assistant

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Visualization | Plotly |
| PDF Processing | pypdf |
| Word Documents | python-docx |
| Data Processing | pandas |
| Text Chunking | LangChain text splitters |
| Embeddings | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| LLM Providers | Gemini, Groq, Cloudflare Workers AI |
| Structured Data | JSON |

---

## System Architecture

```text
Project Documents
 PDF / DOCX / CSV / TXT
          |
          v
  Document Ingestion
          |
          v
    Text Chunking
          |
          v
 Embedding Generation
          |
          v
     ChromaDB
          |
          v
  Context Retrieval
          |
          v
 Specialized AI Agents
    /      |       \
   v       v        v
 Scope    Risk   Blockers and
Analysis Analysis Action Items
    \      |       /
          v
   Structured Outputs
          |
     +----+----+
     |         |
     v         v
 Documentation Health Score
  Generation  Calculation
     |         |
     +----+----+
          |
          v
  Streamlit Dashboard
          |
    +-----+------+
    |     |      |
    v     v      v
 Insights Export  Chat
```

## Project Structure

```text
project-intelligence-and-risk-advisor/
│
├── .streamlit/
│   └── config.toml
│
├── src/
│   ├── schemas.py
│   ├── ingestion/
│   ├── rag/
│   ├── llm/
│   ├── agents/
│   ├── chat_agent.py
│   ├── health_score.py
│   ├── doc_export.py
│   ├── main.py
│   └── run_agents.py
│
├── output/
│   └── insights/
│
├── app.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Installation and Setup

### Prerequisites
- Python
- Git
- Internet connection
- API credentials for at least one supported LLM provider

### 1. Clone the Repository

```bash
git clone https://github.com/Srinivas25046/project-intelligence-and-risk-advisor.git
cd project-intelligence-and-risk-advisor
```

### 2. Create a Virtual Environment

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure API Credentials

Create a `.env` file in the repository root and add the credentials required by your configured providers.

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
```

Replace the placeholders with your actual credentials. Use only the providers enabled by your application.

**Security:** Never commit API keys or other secrets to GitHub. Ensure `.env` is excluded from version control.

### 5. Run the Application

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal.

---

## How to Use

1. Launch the Streamlit application.
2. Upload project documents.
3. Run the project analysis workflow.
4. Review the project health score.
5. Explore scope insights, risks, and blockers.
6. Review generated user stories, risk registers, and action items.
7. Export supported documentation.
8. Ask project-specific questions through the conversational assistant.
9. Upload updated documents and refresh the analysis when necessary.

---

## Command-Line Execution

The repository includes command-line entry points for individual components.

```bash
# Document ingestion
python -m src.main

# Run analysis agents
python -m src.run_agents

# Calculate project health
python -m src.health_score

# Start the conversational assistant
python -m src.chat_agent
```

Run these commands according to the requirements of each module.

---

## Use Cases

- Software development and Agile project management
- Enterprise project planning
- Scope and requirement analysis
- Risk identification and mitigation
- Defect and blocker tracking
- Project status reporting
- Meeting-note and action-item consolidation

---

## Design Principles

- **Context-grounded analysis:** Use retrieved project evidence to support AI-generated insights.
- **Modular architecture:** Separate ingestion, retrieval, LLM integration, agents, scoring, and presentation.
- **Provider resilience:** Support multiple LLM services.
- **Explainable scoring:** Use explicit logic for project health calculations.
- **Incremental processing:** Avoid unnecessary reprocessing of unchanged documents.
- **Actionable outputs:** Convert unstructured information into structured project-management artifacts.

---

## Limitations

- AI-generated findings may contain errors and require human review.
- Analysis quality depends on the completeness and accuracy of source documents.
- LLM services may be affected by API quotas, connectivity, or provider availability.
- Semantic retrieval may miss relevant information.
- The health score depends on the implemented formula and input indicators.
- The application supports project-management decisions but does not replace professional judgment.

## Future Enhancements

- Jira and project-management platform integrations
- Project timeline and dependency visualization
- Historical risk and health-score tracking
- Role-based access control
- Automated report scheduling
- Agent evaluation and accuracy benchmarks
- Additional document formats and enterprise knowledge sources

These are potential enhancements, not claims about existing functionality.

---

## License

See the [`LICENSE`](LICENSE) file for licensing details.

## Author

**Srinivas Gorantla**

- GitHub: [@Srinivas25046](https://github.com/Srinivas25046)
- Repository: [Project Intelligence & Risk Advisor](https://github.com/Srinivas25046/project-intelligence-and-risk-advisor)

---

*An AI-powered project intelligence platform demonstrating RAG, multi-agent workflows, document intelligence, and explainable project analytics.*