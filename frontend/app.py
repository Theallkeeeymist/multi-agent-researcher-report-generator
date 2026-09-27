import streamlit as st
from api import fetch_research_report
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────
try:
    API_URL = st.secrets.get("API_URL", "http://localhost:8080/research")
except Exception:
    API_URL = "http://localhost:8080/research"

LOGIN_URL = "http://localhost:8080/auth/login"

st.set_page_config(
    page_title="Research Agent",
    page_icon="frontend/research-and-development.png", 
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load CSS cleanly from the external file
with open("frontend/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Authentication Gate ──────────────────────────────────────────────────
# 1. Catch the token when Google redirects back to Streamlit
if "token" in st.query_params:
    st.session_state["auth_token"] = st.query_params["token"]
    st.query_params.clear()

# 2. Block the UI if the user is not logged in
if "auth_token" not in st.session_state:
    st.markdown('<p class="eyebrow"><span class="dot"></span> planner · researcher · critic · writer</p>', unsafe_allow_html=True)
    st.markdown('<h1>Research Agent</h1>', unsafe_allow_html=True)
    st.write("Please sign in to run research tasks and preserve our API limits.")
    st.markdown(f'<a href="{LOGIN_URL}" target="_self"><button style="padding:10px; border-radius:5px; background-color:#4285F4; color:white; border:none; cursor:pointer;">Sign in with Google</button></a>', unsafe_allow_html=True)
    st.stop() # Stops Streamlit from rendering the rest of the page

# ── Header (Logged In) ───────────────────────────────────────────────────
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
            # We must pass the token headers down to the api call
            headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
            result, error = fetch_research_report(API_URL, question, status_text, headers=headers)
            
            if error:
                st.markdown(f'<div class="error-text">Run failed — {error}</div>', unsafe_allow_html=True)
            elif result:
                st.session_state["result"] = result

# ... (The rest of your results rendering code stays exactly the same)