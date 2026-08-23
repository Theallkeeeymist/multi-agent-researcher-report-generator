import streamlit as st
import requests

# ── Configuration ────────────────────────────────────────────────────────
try:
    API_URL = st.secrets.get("API_URL", "http://localhost:8000/research")
except Exception:
    API_URL = "http://localhost:8000/research"

st.set_page_config(
    page_title="Research Agent",
    page_icon="frontend/research-and-development.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Styling: document/journal aesthetic, matches the project's design language ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root {
        --paper: #141414;
        --paper-raised: #1b1b1b;
        --ink: #EDEAE3;
        --ink-dim: #8f8b82;
        --ink-faint: #56534c;
        --accent: #5B7C99;
        --mark: #C9A66B;
        --rule: #2a2a28;
        --error: #b06a5c;
    }

    .stApp {
        background: var(--paper);
        color: var(--ink);
    }

    /* hide default streamlit chrome for a cleaner document feel */
    #MainMenu, footer, header { visibility: hidden; }

    .block-container {
        max-width: 700px;
        padding-top: 3rem;
        padding-bottom: 6rem;
    }

    /* eyebrow label */
    .eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        text-transform: uppercase;
        color: var(--ink-dim);
        letter-spacing: 0.05em;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .eyebrow .dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent); display: inline-block;
    }

    h1 {
        font-family: 'Source Serif 4', Georgia, serif !important;
        font-weight: 600 !important;
        font-size: 34px !important;
        letter-spacing: -0.01em;
        color: var(--ink) !important;
        margin-bottom: 8px !important;
    }

    .lede {
        font-family: 'Source Serif 4', Georgia, serif;
        color: var(--ink-dim);
        font-size: 17px;
        line-height: 1.5;
        max-width: 54ch;
        margin-bottom: 36px;
    }
    .lede em { color: var(--ink); font-style: italic; }

    /* text input area */
    .stTextArea textarea {
        background: var(--paper-raised) !important;
        color: var(--ink) !important;
        border: 1px solid var(--rule) !important;
        border-radius: 3px !important;
        font-family: 'Source Serif 4', Georgia, serif !important;
        font-size: 17px !important;
        padding: 16px !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: none !important;
    }
    .stTextArea label { display: none; }

    .stTextArea textarea::placeholder {
        color: var(--ink-faint) !important;
        font-style: italic;
    }

    /* run button */
    .stButton button {
        background: var(--ink) !important;
        color: var(--paper) !important;
        border: none !important;
        border-radius: 2px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 13px !important;
        letter-spacing: 0.03em;
        padding: 10px 24px !important;
        transition: opacity 0.15s ease;
    }
    .stButton button:hover {
        opacity: 0.85 !important;
        color: var(--paper) !important;
        border: none !important;
    }

    .hint {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        color: var(--ink-faint);
        margin-top: -8px;
        margin-bottom: 24px;
    }

    /* pipeline trace */
    .trace-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        text-transform: uppercase;
        color: var(--ink-faint);
        letter-spacing: 0.08em;
        margin: 32px 0 14px;
    }
    .stage-row {
        display: flex;
        justify-content: space-between;
        padding: 9px 0;
        border-bottom: 1px solid var(--rule);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
    }
    .stage-row .name { color: var(--ink-dim); }
    .stage-row .status.done { color: var(--mark); }
    .stage-row .status.active { color: var(--accent); }
    .stage-row .status.waiting { color: var(--ink-faint); }

    /* metrics row */
    .meta-row {
        display: flex;
        gap: 32px;
        padding: 20px 0;
        border-top: 1px solid var(--rule);
        border-bottom: 1px solid var(--rule);
        margin: 32px 0;
    }
    .meta-item .label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 10px;
        text-transform: uppercase;
        color: var(--ink-faint);
        letter-spacing: 0.06em;
        margin-bottom: 4px;
    }
    .meta-item .value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 17px;
        color: var(--ink);
    }
    .meta-item .value.mark { color: var(--mark); }

    /* report body */
    .report-heading {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--ink-faint);
        margin: 8px 0 18px;
    }

    .stMarkdown, .stMarkdown p, .stMarkdown li {
        font-family: 'Source Serif 4', Georgia, serif !important;
        color: var(--ink) !important;
        font-size: 16px !important;
        line-height: 1.65 !important;
    }

    .stMarkdown table {
        border-collapse: collapse;
        width: 100%;
    }
    .stMarkdown th, .stMarkdown td {
        border: 1px solid var(--rule) !important;
        padding: 8px 12px !important;
        font-size: 14px !important;
    }
    .stMarkdown th {
        font-family: 'IBM Plex Mono', monospace !important;
        color: var(--ink-dim) !important;
        text-transform: uppercase;
        font-size: 11px !important;
    }

    /* expanders (topics / feedback) */
    .streamlit-expanderHeader {
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--ink-dim) !important;
        background: transparent !important;
    }
    .streamlit-expanderContent {
        background: transparent !important;
        border-top: none !important;
    }

    /* download button */
    .stDownloadButton button {
        background: transparent !important;
        color: var(--ink-dim) !important;
        border: 1px solid var(--rule) !important;
        border-radius: 2px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 12px !important;
    }
    .stDownloadButton button:hover {
        border-color: var(--accent) !important;
        color: var(--ink) !important;
    }

    /* footer */
    .footer-mono {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        color: var(--ink-faint);
        margin-top: 60px;
        padding-top: 20px;
        border-top: 1px solid var(--rule);
    }

    .error-text {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
        color: var(--error);
        border: 1px solid var(--error);
        background: rgba(176, 106, 92, 0.08);
        border-radius: 3px;
        padding: 12px 16px;
        margin-top: 16px;
    }
</style>
""", unsafe_allow_html=True)

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

# ── Run pipeline ──────────────────────────────────────────────────────────
if run_clicked:
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        try:
            with st.spinner(f"Running the pipeline:\n planner → researcher → critic → writer..."):
                response = requests.post(API_URL, json={"question": question}, timeout=180)
                response.raise_for_status()
                data = response.json()

            st.session_state["result"] = data

        except requests.exceptions.ConnectionError:
            st.markdown(
                f'<div class="error-text">Run failed — can\'t reach the backend at {API_URL}. '
                f'Confirm the FastAPI server is running.</div>',
                unsafe_allow_html=True,
            )
        except requests.exceptions.HTTPError as e:
            st.markdown(f'<div class="error-text">Run failed — backend error: {e}</div>', unsafe_allow_html=True)
        except requests.exceptions.Timeout:
            st.markdown(
                '<div class="error-text">Run failed — request timed out. '
                'The graph may be stuck in a retry loop or a tool call is hanging.</div>',
                unsafe_allow_html=True,
            )

# ── Results ───────────────────────────────────────────────────────────────
if "result" in st.session_state:
    data = st.session_state["result"]

    st.markdown(f"""
    <div class="meta-row">
        <div class="meta-item">
            <p class="label">Critic rating</p>
            <p class="value mark">{data['rating']} / 5</p>
        </div>
        <div class="meta-item">
            <p class="label">Loop iterations</p>
            <p class="value">{data['loop_count']}</p>
        </div>
        <div class="meta-item">
            <p class="label">Topics covered</p>
            <p class="value">{len(data['topics'])}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Topics identified"):
        for t in data["topics"]:
            st.markdown(f"- {t}")

    with st.expander("Critic feedback"):
        st.write(data.get("critic_feedback") or "—")

    st.markdown('<p class="report-heading">Report</p>', unsafe_allow_html=True)
    st.markdown(data["report"])

    st.download_button(
        "Download .md",
        data["report"],
        file_name="research_report.md",
        mime="text/markdown",
    )

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="footer-mono">LangGraph · MCP (web / arXiv / Semantic Scholar) · Groq</p>',
    unsafe_allow_html=True,
)