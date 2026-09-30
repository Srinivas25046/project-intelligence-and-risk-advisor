import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from src.ingestion.loaders import load_document
from src.rag.chunking import chunk_document
from src.rag.vector_store import index_chunks
from src.agents.scope_agent import ScopeExtractionAgent
from src.agents.risk_agent import RiskForecastingAgent
from src.agents.blocker_agent import BlockerActionItemAgent
from src.agents.doc_gen_agent import generate_documentation
from src.health_score import compute_health_score
from src.insights_store import save_insight, load_insight
from src.chat_agent import ChatAssistant

st.set_page_config(page_title="Project Intelligence & Risk Advisor", layout="wide")
st.title("📊 Project Intelligence & Risk Advisor")
st.caption("AI-driven enterprise project intelligence — live demo")

RAW_DATA_DIR = "data/raw"

# Session-only flags: each starts False on every fresh browser session,
# regardless of what's already saved on disk from earlier terminal runs.
# A tab only renders its content once ITS flag is flipped True by the
# matching button being clicked in THIS session.
for flag in ["ingestion_done", "agents_done", "docs_done", "health_done"]:
    if flag not in st.session_state:
        st.session_state[flag] = False


def try_load(name):
    try:
        return load_insight(name)
    except FileNotFoundError:
        return None


# ---------- Sidebar: pipeline controls, run top to bottom ----------
st.sidebar.header("Pipeline Controls")
st.sidebar.caption("Run these in order for a fresh demo.")

if st.sidebar.button("1️⃣ Run Ingestion Pipeline"):
    with st.spinner("Ingesting documents and building the vector index..."):
        all_chunks = []
        skipped = []
        for filename in os.listdir(RAW_DATA_DIR):
            filepath = os.path.join(RAW_DATA_DIR, filename)
            if not os.path.isfile(filepath):
                continue
            try:
                document = load_document(filepath)
            except ValueError:
                skipped.append(filename)
                continue
            all_chunks.extend(chunk_document(document))
        index_chunks(all_chunks)
    st.session_state.ingestion_done = True
    st.sidebar.success(f"Indexed {len(all_chunks)} chunks.")
    if skipped:
        st.sidebar.caption(f"Skipped unsupported files: {', '.join(skipped)}")

if st.sidebar.button("2️⃣ Run Extraction Agents"):
    with st.spinner("Running scope, risk, and blocker agents..."):
        agents = {
            "scope": ScopeExtractionAgent(),
            "risks": RiskForecastingAgent(),
            "blockers": BlockerActionItemAgent(),
        }
        for name, agent in agents.items():
            try:
                result = agent.run()
                save_insight(name, result)
            except Exception as e:
                st.sidebar.error(f"{name} failed: {e}")
    st.session_state.agents_done = True
    st.sidebar.success("Agents completed.")

if st.sidebar.button("3️⃣ Generate Documentation"):
    with st.spinner("Generating user stories and risk register..."):
        try:
            generate_documentation()
            st.session_state.docs_done = True
            st.sidebar.success("Documentation generated.")
        except Exception as e:
            st.sidebar.error(f"Failed: {e}")

if st.sidebar.button("4️⃣ Compute Health Score"):
    with st.spinner("Computing health score..."):
        try:
            compute_health_score()
            st.session_state.health_done = True
            st.sidebar.success("Health score computed.")
        except Exception as e:
            st.sidebar.error(f"Failed: {e}")


# ---------- Main area: tabs for each deliverable ----------
tab_scope, tab_risks, tab_blockers, tab_docs, tab_health, tab_chat = st.tabs(
    ["📋 Scope", "⚠️ Risks", "🚧 Blockers", "📄 Documentation", "❤️ Health Score", "💬 Chat Assistant"]
)

with tab_scope:
    if not st.session_state.agents_done:
        st.info("Click '2️⃣ Run Extraction Agents' in the sidebar to see scope information.")
    else:
        data = try_load("scope")
        if data:
            st.subheader("Project Goals")
            for g in data.get("project_goals", []):
                st.write(f"- {g}")
            st.subheader("Deliverables")
            for d in data.get("deliverables", []):
                st.write(f"- {d}")
            st.subheader("Milestones")
            st.table(data.get("milestones", []))
            st.subheader("Responsibilities")
            st.table(data.get("responsibilities", []))

with tab_risks:
    if not st.session_state.agents_done:
        st.info("Click '2️⃣ Run Extraction Agents' in the sidebar to see risk information.")
    else:
        data = try_load("risks")
        if data:
            st.subheader("Delivery Forecast")
            st.write(data.get("delivery_forecast", ""))
            st.subheader("Identified Risks")
            severity_icon = {"high": "🔴", "medium": "🟠", "low": "🟢"}
            for r in data.get("risks", []):
                icon = severity_icon.get(r.get("severity", "medium"), "⚪")
                st.write(f"{icon} **{r.get('description')}**")
                st.caption(f"Impact: {r.get('likely_impact')} · Severity: {r.get('severity')} · Source: {r.get('evidence_source')}")

with tab_blockers:
    if not st.session_state.agents_done:
        st.info("Click '2️⃣ Run Extraction Agents' in the sidebar to see blocker information.")
    else:
        data = try_load("blockers")
        if data:
            st.subheader("Active Blockers")
            for b in data.get("blockers", []):
                st.write(f"🚧 **{b.get('description')}** — blocking: {b.get('blocking')}")
                st.caption(f"Source: {b.get('source')}")
            st.subheader("Action Items")
            st.table(data.get("action_items", []))

with tab_docs:
    if not st.session_state.docs_done:
        st.info("Click '3️⃣ Generate Documentation' in the sidebar to see this section.")
    else:
        data = try_load("documentation")
        if data:
            st.subheader("User Stories")
            for us in data.get("user_stories", []):
                st.write(f"As a **{us.get('role')}**, I want to {us.get('goal')} so that {us.get('benefit')}.")
            st.subheader("Risk Register")
            st.table(data.get("risk_register", []))
            st.subheader("Consolidated Action Item List")
            st.table(data.get("action_item_list", []))

with tab_health:
    if not st.session_state.health_done:
        st.info("Click '4️⃣ Compute Health Score' in the sidebar to see this section.")
    else:
        data = try_load("health_score")
        if data:
            overall = data.get("overall_health_score", 0)
            st.metric("Overall Health Score", f"{overall}/100")
            breakdown = data.get("breakdown", {})
            col1, col2, col3 = st.columns(3)
            col1.metric("Scope Clarity", f"{breakdown.get('scope_clarity', 0)}/100")
            col2.metric("Timeline Risk", f"{breakdown.get('timeline_risk', 0)}/100")
            col3.metric("Blocker Load", f"{breakdown.get('blocker_load', 0)}/100")
            st.bar_chart(breakdown)
            st.caption(data.get("rationale", ""))

with tab_chat:
    st.subheader("Ask the Project Intelligence Assistant")

    if not st.session_state.agents_done:
        st.info("Run the pipeline steps first so the assistant has project data to answer from.")
    else:
        if "assistant" not in st.session_state:
            try:
                st.session_state.assistant = ChatAssistant()
            except Exception as e:
                st.session_state.assistant = None
                st.error(f"Could not initialize assistant: {e}")

        if "chat_display" not in st.session_state:
            st.session_state.chat_display = []

        for role, content in st.session_state.chat_display:
            with st.chat_message(role):
                st.write(content)

        question = st.chat_input("Ask a question about the project...")
        if question and st.session_state.get("assistant"):
            st.session_state.chat_display.append(("user", question))
            with st.chat_message("user"):
                st.write(question)
            with st.spinner("Thinking..."):
                answer = st.session_state.assistant.ask(question)
            st.session_state.chat_display.append(("assistant", answer))
            with st.chat_message("assistant"):
                st.write(answer)