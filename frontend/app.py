import streamlit as st
from api import fetch_research_report
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────
try:
    API_URL = st.secrets.get("API_URL", "http://localhost:8000/research")
except Exception:
    API_URL = "http://localhost:8000/research"

st.set_page_config(
    page_title="Research Agent",
    page_icon="frontend/research-and-development.png", # Update path if needed
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load CSS cleanly from the external file
with open("frontend/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown('<p class="eyebrow"><span class="dot"></span> planner · researcher · critic · writer</p>', unsafe_allow_html=True)
st.markdown('<h1>Research Agent</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="lede">A four-stage pipeline that plans a research question into topics, '
    'gathers sources across the <em>web, arXiv, and Semantic Scholar</em>, and revises '
    'itself until a critic is satisfied.</p>',
    unsafe_allow_html=True,
)

# ── Input ─────────────────────────────────────────────────────────────────
with st.form("research_form"):
    question = st.text_area(
        "question",
        height=100,
        placeholder="Ask a research question — e.g. how does attention work in transformer models?",
        label_visibility="collapsed",
    )
    run_clicked = st.form_submit_button("Run", type="primary")

# ── Execution ─────────────────────────────────────────────────────────────
if run_clicked:
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        status_text = st.empty()
        with st.spinner("Agents are researching and drafting..."):
            result, error = fetch_research_report(API_URL, question, status_text)
            
            if error:
                st.markdown(f'<div class="error-text">Run failed — {error}</div>', unsafe_allow_html=True)
            elif result:
                st.session_state["result"] = result

# ── Results rendering ─────────────────────────────────────────────────────
if "result" in st.session_state:
    data = st.session_state["result"]

    st.markdown(f"""
    <div class="meta-row">
        <div class="meta-item"><p class="label">Critic rating</p><p class="value mark">{data['rating']} / 5</p></div>
        <div class="meta-item"><p class="label">Loop iterations</p><p class="value">{data['loop_count']}</p></div>
        <div class="meta-item"><p class="label">Topics covered</p><p class="value">{len(data['topics'])}</p></div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Topics identified"):
        for t in data["topics"]:
            st.markdown(f"- {t}")

    with st.expander("Critic feedback"):
        st.write(data.get("critic_feedback") or "—")

    st.markdown('<p class="report-heading">Report</p>', unsafe_allow_html=True)
    st.markdown(data["report"])

    st.download_button("Download .md", data["report"], file_name="research_report.md", mime="text/markdown")

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown('<p class="footer-mono">LangGraph · MCP (web / arXiv / Semantic Scholar) · Groq</p>', unsafe_allow_html=True)