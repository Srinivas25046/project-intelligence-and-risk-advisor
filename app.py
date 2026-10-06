import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
load_dotenv()

from src.ingestion.loaders import load_document
from src.ingestion.manifest import get_new_or_changed_files, mark_ingested, save_last_batch
from src.rag.chunking import chunk_document
from src.rag.vector_store import index_chunks, delete_by_filename
from src.agents.scope_agent import ScopeExtractionAgent
from src.agents.risk_agent import RiskForecastingAgent
from src.agents.blocker_agent import BlockerActionItemAgent
from src.agents.doc_gen_agent import generate_user_stories, generate_risk_register, generate_action_items
from src.health_score import compute_health_score
from src.insights_store import save_insight, load_insight
from src.chat_agent import ChatAssistant
from src.doc_export import build_user_stories_docx, build_risk_register_docx, build_action_items_docx, build_combined_docx

RAW_DATA_DIR = "data/raw"
st.set_page_config(page_title="Project Intelligence & Risk Advisor", page_icon="📊", layout="wide")

# =============================================================================
# THEME
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], p, span, div { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4, .hero h1, .section-title { font-family: 'Space Grotesk', sans-serif; }

.block-container { padding: 2.5rem 3rem 4rem 3rem; max-width: 1280px; }

@keyframes auroraShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.hero {
    background: linear-gradient(120deg, #4338CA, #6366F1, #DB2777, #6366F1, #4338CA);
    background-size: 300% 300%;
    animation: auroraShift 14s ease infinite;
    padding: 3.2rem 3rem;
    border-radius: 24px;
    color: white;
    margin-bottom: 2.4rem;
    box-shadow: 0 20px 50px -20px rgba(99, 102, 241, 0.6);
}
.hero h1 { margin: 0; font-size: 2.3rem; font-weight: 700; color: white !important; }
.hero p { margin: 0.7rem 0 0 0; opacity: 0.92; font-size: 1.05rem; color: #EDE9FE; max-width: 640px; }

.stat-card {
    background: #141B2D;
    border: 1px solid #232B42;
    border-radius: 16px;
    padding: 1.4rem 1.5rem;
}
.stat-label { font-size: 0.82rem; color: #94A3B8; font-weight: 500; margin-bottom: 0.4rem; }
.stat-value { font-size: 1.9rem; font-weight: 700; color: #F1F5F9; }

.section-title {
    font-size: 1.25rem; font-weight: 600; color: #F1F5F9;
    margin: 1.8rem 0 1.1rem 0; display: flex; align-items: center; gap: 10px;
}

.row-high, .row-blocked    { border-left: 4px solid #EF4444; padding: 10px 0 10px 16px; }
.row-medium, .row-progress { border-left: 4px solid #F59E0B; padding: 10px 0 10px 16px; }
.row-low, .row-done        { border-left: 4px solid #22C55E; padding: 10px 0 10px 16px; }
.row-other                 { border-left: 4px solid #475569; padding: 10px 0 10px 16px; }

.tag {
    display: inline-block; padding: 3px 12px; border-radius: 999px;
    font-size: 0.74rem; font-weight: 700; letter-spacing: 0.02em;
}
.tag-high, .tag-blocked { background: rgba(239,68,68,0.15); color: #FCA5A5; }
.tag-medium, .tag-progress { background: rgba(245,158,11,0.15); color: #FCD34D; }
.tag-low, .tag-done { background: rgba(34,197,94,0.15); color: #86EFAC; }
.tag-other { background: rgba(100,116,139,0.2); color: #CBD5E1; }

@keyframes pulseRing {
    0%   { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.55); }
    70%  { box-shadow: 0 0 0 16px rgba(99, 102, 241, 0); }
    100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
}
div[data-testid="stPopover"] { position: fixed !important; bottom: 32px; right: 32px; z-index: 9999; }
div[data-testid="stPopover"] > div > button {
    border-radius: 50% !important; width: 68px !important; height: 68px !important; font-size: 28px !important;
    background: linear-gradient(135deg, #6366F1, #DB2777) !important; color: white !important; border: none !important;
    animation: pulseRing 2.4s infinite;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>📊 Project Intelligence & Risk Advisor</h1>
  <p>Upload your project documents — AI agents automatically extract scope, risks, blockers, and health, no manual steps required.</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "chat_display" not in st.session_state:
    st.session_state.chat_display = []


def try_load(name):
    try:
        return load_insight(name)
    except FileNotFoundError:
        return None


def sev_class(sev):
    return {"high": "high", "medium": "medium", "low": "low"}.get((sev or "").lower().split("|")[0], "other")


def status_class(status):
    s = (status or "").lower()
    if "block" in s: return "blocked"
    if "progress" in s: return "progress"
    if "done" in s: return "done"
    return "other"


def run_agents_pipeline(status):
    """Extraction agents + health score only. Documentation is NOT generated
    automatically — it is only produced when the user explicitly requests
    each document type in the Documentation tab."""
    status.write("🧠 Extracting scope, risks, and blockers...")
    for name, agent in {
        "scope": ScopeExtractionAgent(),
        "risks": RiskForecastingAgent(),
        "blockers": BlockerActionItemAgent(),
    }.items():
        try:
            save_insight(name, agent.run())
            status.write(f"✅ {name.capitalize()} agent complete.")
        except Exception as e:
            status.write(f"⚠️ {name.capitalize()} agent failed: {e}")

    status.write("❤️ Computing health score...")
    try:
        compute_health_score()
        status.write("✅ Health score computed.")
    except Exception as e:
        status.write(f"⚠️ Health score failed: {e}")


# =============================================================================
# STEP 1 — Upload
# =============================================================================
st.markdown('<div class="section-title">📁 Upload Project Documents</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "Upload PDF, DOCX, CSV, or TXT files",
    type=["pdf", "docx", "csv", "txt"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files and not st.session_state.analysis_done:
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    for f in os.listdir(RAW_DATA_DIR):
        fp = os.path.join(RAW_DATA_DIR, f)
        if os.path.isfile(fp):
            os.remove(fp)
    for uf in uploaded_files:
        with open(os.path.join(RAW_DATA_DIR, uf.name), "wb") as out:
            out.write(uf.getbuffer())
    st.success(f"{len(uploaded_files)} file(s) ready: {', '.join(f.name for f in uploaded_files)}")
elif uploaded_files and st.session_state.analysis_done:
    st.info("Initial analysis already run. Use '➕ Add More Documents' below to add further files without resetting your existing data.")

# =============================================================================
# STEP 2 — Run analysis
# =============================================================================
st.markdown('<div class="section-title">🚀 Run Analysis</div>', unsafe_allow_html=True)

if st.button("Run Full Analysis", type="primary", disabled=not uploaded_files, use_container_width=True):
    with st.status("Running full project analysis...", expanded=True) as status:
        status.write("📥 Ingesting documents...")
        all_chunks = []
        for filename in os.listdir(RAW_DATA_DIR):
            filepath = os.path.join(RAW_DATA_DIR, filename)
            if not os.path.isfile(filepath):
                continue
            try:
                document = load_document(filepath)
            except Exception:
                continue
            chunks = chunk_document(document)
            delete_by_filename(filename)
            all_chunks.extend(chunks)
        index_chunks(all_chunks)
        mark_ingested(RAW_DATA_DIR, [f.name for f in uploaded_files])
        save_last_batch([f.name for f in uploaded_files])
        status.write(f"✅ Indexed {len(all_chunks)} chunks.")

        run_agents_pipeline(status)
        status.update(label="Analysis complete!", state="complete", expanded=False)

    st.session_state.analysis_done = True
    if "assistant" in st.session_state:
        del st.session_state["assistant"]
    st.rerun()

if not uploaded_files:
    st.info("Upload at least one document above to enable analysis.")

st.divider()

# =============================================================================
# RESULTS
# =============================================================================
if st.session_state.analysis_done:

    health = try_load("health_score")
    scope = try_load("scope")
    risks = try_load("risks")
    blockers = try_load("blockers")

    overall = health.get("overall_health_score", 0) if health else 0
    status_color = "#22C55E" if overall >= 70 else "#F59E0B" if overall >= 40 else "#EF4444"
    status_label = "Healthy" if overall >= 70 else "At Risk" if overall >= 40 else "Critical"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Overall Health</div>
            <div class="stat-value" style="color:{status_color};">{overall}/100</div>
            <div style="color:{status_color}; font-size:0.85rem; font-weight:600;">{status_label}</div></div>""", unsafe_allow_html=True)
    with c2:
        n_risks = len(risks.get("risks", [])) if risks else 0
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Open Risks</div>
            <div class="stat-value">{n_risks}</div></div>""", unsafe_allow_html=True)
    with c3:
        n_blockers = len(blockers.get("blockers", [])) if blockers else 0
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Active Blockers</div>
            <div class="stat-value">{n_blockers}</div></div>""", unsafe_allow_html=True)
    with c4:
        n_deliverables = len(scope.get("deliverables", [])) if scope else 0
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Deliverables</div>
            <div class="stat-value">{n_deliverables}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    tab_dashboard, tab_health, tab_scope, tab_risks, tab_blockers, tab_docs = st.tabs(
        ["📊 Dashboard", "❤️ Health", "📋 Scope", "⚠️ Risks", "🚧 Blockers", "📄 Documentation"]
    )

    # ---------------- DASHBOARD: unified Project Insights & Risk Summary ----------------
    with tab_dashboard:
        st.markdown("### Project Insights & Risk Summary")
        st.caption("A single-glance view of project health, top risks, outstanding action items, and scope.")

        d_col1, d_col2 = st.columns([1, 1.4])

        with d_col1:
            with st.container(border=True):
                st.markdown("**❤️ Health Score**")
                if health:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=overall,
                        number={"suffix": "/100", "font": {"color": "#F1F5F9"}},
                        gauge={
                            "axis": {"range": [0, 100], "tickcolor": "#64748B"},
                            "bar": {"color": status_color},
                            "bgcolor": "#141B2D",
                            "steps": [
                                {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                                {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                                {"range": [70, 100], "color": "rgba(34,197,94,0.15)"},
                            ],
                        },
                    ))
                    fig.update_layout(height=220, margin=dict(t=10, b=10, l=20, r=20),
                                       paper_bgcolor="rgba(0,0,0,0)", font={"color": "#F1F5F9"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Not available yet.")

            with st.container(border=True):
                st.markdown("**🎯 Scope Summary**")
                if scope:
                    st.markdown("*Goals:*")
                    for g in scope.get("project_goals", [])[:3]:
                        st.write(f"- {g}")
                    st.markdown("*Deliverables:*")
                    for d in scope.get("deliverables", [])[:4]:
                        st.write(f"- {d}")

        with d_col2:
            with st.container(border=True):
                st.markdown("**⚠️ Top Risks**")
                if risks:
                    for r in risks.get("risks", [])[:4]:
                        cls = sev_class(r.get("severity"))
                        st.markdown(f"""
                        <div class="row-{cls}" style="margin:8px 0;">
                            <span class="tag tag-{cls}">{(r.get('severity') or '').upper()}</span>
                            <span style="color:#F1F5F9; margin-left:8px;">{r.get('description')}</span>
                        </div>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("**✅ Action Items**")
                if blockers:
                    for a in blockers.get("action_items", [])[:6]:
                        cls = status_class(a.get("status"))
                        st.markdown(f"""
                        <div class="row-{cls}" style="margin:6px 0; display:flex; justify-content:space-between;">
                            <span style="color:#F1F5F9;">{a.get('task')} <span style="color:#94A3B8;">— {a.get('owner')}</span></span>
                            <span class="tag tag-{cls}">{a.get('status')}</span>
                        </div>""", unsafe_allow_html=True)

    with tab_health:
        if health:
            col_gauge, col_cards = st.columns([1, 1.3])
            with col_gauge:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=overall,
                    title={"text": f"Overall Health — {status_label}", "font": {"color": "#F1F5F9", "size": 16}},
                    number={"suffix": "/100", "font": {"color": "#F1F5F9"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#64748B"},
                        "bar": {"color": status_color},
                        "bgcolor": "#141B2D",
                        "steps": [
                            {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                            {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                            {"range": [70, 100], "color": "rgba(34,197,94,0.15)"},
                        ],
                    },
                ))
                fig.update_layout(height=320, margin=dict(t=60, b=20, l=30, r=30),
                                   paper_bgcolor="rgba(0,0,0,0)", font={"color": "#F1F5F9"})
                st.plotly_chart(fig, use_container_width=True)
            with col_cards:
                breakdown = health.get("breakdown", {})
                for label, key in [("Scope Clarity", "scope_clarity"), ("Timeline Risk", "timeline_risk"), ("Blocker Load", "blocker_load")]:
                    val = breakdown.get(key, 0)
                    color = "#22C55E" if val >= 70 else "#F59E0B" if val >= 40 else "#EF4444"
                    with st.container(border=True):
                        st.markdown(f"**{label}**")
                        st.progress(val / 100)
                        st.markdown(f"<span style='color:{color}; font-weight:700;'>{val}/100</span>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("**Why this score?**")
                st.write(health.get("rationale", ""))
        else:
            st.info("Health score not available.")

    with tab_scope:
        if scope:
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.markdown("**🎯 Project Goals**")
                    for g in scope.get("project_goals", []):
                        st.write(f"- {g}")
                with st.container(border=True):
                    st.markdown("**📦 Deliverables**")
                    for d in scope.get("deliverables", []):
                        st.write(f"- {d}")
            with col2:
                with st.container(border=True):
                    st.markdown("**🗓️ Milestones**")
                    st.table(scope.get("milestones", []))
                with st.container(border=True):
                    st.markdown("**👥 Responsibilities**")
                    st.table(scope.get("responsibilities", []))

    with tab_risks:
        if risks:
            with st.container(border=True):
                st.markdown("**📈 Delivery Forecast**")
                st.write(risks.get("delivery_forecast", ""))
            st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
            for r in risks.get("risks", []):
                cls = sev_class(r.get("severity"))
                st.markdown(f"""
                <div class="row-{cls}" style="margin:12px 0;">
                    <span class="tag tag-{cls}">{(r.get('severity') or '').upper()}</span>
                    <strong style="color:#F1F5F9; margin-left:10px;">{r.get('description')}</strong><br>
                    <span style="color:#94A3B8; font-size:0.85rem;">Impact: {r.get('likely_impact')} · Source: {r.get('evidence_source')}</span>
                </div>""", unsafe_allow_html=True)

    with tab_blockers:
        if blockers:
            st.markdown("**🚧 Active Blockers**")
            for b in blockers.get("blockers", []):
                st.markdown(f"""
                <div class="row-blocked" style="margin:12px 0;">
                    <strong style="color:#F1F5F9;">{b.get('description')}</strong><br>
                    <span style="color:#94A3B8; font-size:0.85rem;">Blocking: {b.get('blocking')} · Source: {b.get('source')}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
            st.markdown("**✅ Action Items**")
            for a in blockers.get("action_items", []):
                cls = status_class(a.get("status"))
                st.markdown(f"""
                <div class="row-{cls}" style="margin:10px 0; display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#F1F5F9;">{a.get('task')} <span style="color:#94A3B8;">— {a.get('owner')}</span></span>
                    <span class="tag tag-{cls}">{a.get('status')}</span>
                </div>""", unsafe_allow_html=True)

    # ---------------- DOCUMENTATION: manual, per-document generation, stacked layout ----------------
    with tab_docs:
        st.caption("Generate each document independently. Nothing is generated automatically — click a button below to create it.")

        with st.container(border=True):
            st.markdown("**📝 User Stories**")
            gen_col, dl_col = st.columns([1, 1])
            with gen_col:
                if st.button("Generate User Stories", use_container_width=True, key="gen_us"):
                    with st.spinner("Generating..."):
                        try:
                            generate_user_stories()
                            st.success("Generated.")
                        except Exception as e:
                            st.error(f"Failed: {e}")
            us_data = try_load("doc_user_stories")
            with dl_col:
                if us_data:
                    st.download_button(
                        "⬇️ Download",
                        data=build_user_stories_docx(us_data),
                        file_name="User_Stories.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="dl_us",
                    )
            if us_data:
                st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
                for us in us_data.get("user_stories", []):
                    st.write(f"As a **{us.get('role')}**, I want to {us.get('goal')} so that {us.get('benefit')}.")

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("**⚠️ Risk Register**")
            gen_col, dl_col = st.columns([1, 1])
            with gen_col:
                if st.button("Generate Risk Register", use_container_width=True, key="gen_rr"):
                    with st.spinner("Generating..."):
                        try:
                            generate_risk_register()
                            st.success("Generated.")
                        except Exception as e:
                            st.error(f"Failed: {e}")
            rr_data = try_load("doc_risk_register")
            with dl_col:
                if rr_data:
                    st.download_button(
                        "⬇️ Download",
                        data=build_risk_register_docx(rr_data),
                        file_name="Risk_Register.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="dl_rr",
                    )
            if rr_data:
                st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
                st.table(rr_data.get("risk_register", []))

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("**✅ Action Item List**")
            gen_col, dl_col = st.columns([1, 1])
            with gen_col:
                if st.button("Generate Action Items", use_container_width=True, key="gen_ai"):
                    with st.spinner("Generating..."):
                        try:
                            generate_action_items()
                            st.success("Generated.")
                        except Exception as e:
                            st.error(f"Failed: {e}")
            ai_data = try_load("doc_action_items")
            with dl_col:
                if ai_data:
                    st.download_button(
                        "⬇️ Download",
                        data=build_action_items_docx(ai_data),
                        file_name="Action_Items.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="dl_ai",
                    )
            if ai_data:
                st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
                st.table(ai_data.get("action_item_list", []))

        us_data = try_load("doc_user_stories")
        rr_data = try_load("doc_risk_register")
        ai_data = try_load("doc_action_items")
        if us_data and rr_data and ai_data:
            st.divider()
            st.download_button(
                "⬇️ Download All as One Combined Document",
                data=build_combined_docx(us_data, rr_data, ai_data),
                file_name="Project_Documentation.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

    # ---------------- Incremental upload ----------------
    st.divider()
    st.markdown('<div class="section-title">➕ Add More Documents</div>', unsafe_allow_html=True)
    st.caption("Add new meeting notes or progress updates — the knowledge base updates incrementally, and insights automatically refresh.")

    new_files = st.file_uploader(
        "Add additional PDF, DOCX, CSV, or TXT files",
        type=["pdf", "docx", "csv", "txt"],
        accept_multiple_files=True,
        key="incremental_uploader",
    )

    if new_files:
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        for uf in new_files:
            with open(os.path.join(RAW_DATA_DIR, uf.name), "wb") as out:
                out.write(uf.getbuffer())

        if st.button("🔄 Update Knowledge Base & Refresh Insights", type="primary", use_container_width=True):
            with st.status("Updating knowledge base...", expanded=True) as status:
                to_process = get_new_or_changed_files(RAW_DATA_DIR)
                status.write(f"📄 {len(to_process)} new/changed file(s) detected: {', '.join(to_process) if to_process else 'none'}")

                new_chunks = []
                for filename in to_process:
                    filepath = os.path.join(RAW_DATA_DIR, filename)
                    try:
                        document = load_document(filepath)
                    except Exception:
                        continue
                    chunks = chunk_document(document)
                    delete_by_filename(filename)
                    new_chunks.extend(chunks)

                if new_chunks:
                    index_chunks(new_chunks)
                    mark_ingested(RAW_DATA_DIR, to_process)
                    save_last_batch(to_process)
                    status.write(f"✅ Indexed {len(new_chunks)} new chunks.")
                else:
                    status.write("ℹ️ No new content to index.")

                run_agents_pipeline(status)
                status.update(label="Knowledge base and insights updated!", state="complete", expanded=False)

            if "assistant" in st.session_state:
                del st.session_state["assistant"]
            st.rerun()
else:
    st.info("Upload documents and click 'Run Full Analysis' to see results here.")

# =============================================================================
# FLOATING CHAT POPUP
# =============================================================================
if st.session_state.analysis_done:
    with st.popover("💬"):
        st.markdown("#### 🤖 Project Assistant")

        if "assistant" not in st.session_state:
            try:
                st.session_state.assistant = ChatAssistant()
            except Exception as e:
                st.session_state.assistant = None
                st.error(f"Could not initialize assistant: {e}")

        chat_box = st.container(height=420)
        with chat_box:
            for role, content in st.session_state.chat_display:
                align = "right" if role == "user" else "left"
                bg = "linear-gradient(135deg, #6366F1, #DB2777)" if role == "user" else "#1E2A42"
                st.markdown(
                    f"<div style='text-align:{align}; margin:8px 0;'>"
                    f"<span style='background:{bg}; color:white; padding:10px 14px; "
                    f"border-radius:14px; display:inline-block; max-width:85%; font-size:0.92rem;'>{content}</span></div>",
                    unsafe_allow_html=True,
                )

        with st.form(key="chat_form", clear_on_submit=True):
            user_q = st.text_input("Ask a question...", label_visibility="collapsed")
            sent = st.form_submit_button("Send", use_container_width=True)

        if sent and user_q and st.session_state.assistant:
            st.session_state.chat_display.append(("user", user_q))
            with st.spinner("Thinking..."):
                answer = st.session_state.assistant.ask(user_q)
            st.session_state.chat_display.append(("assistant", answer))
            st.rerun()