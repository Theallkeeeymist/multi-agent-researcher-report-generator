# Multi-Agent Research & Report Generator

A LangGraph multi-agent pipeline that takes a research question, plans it into
topics, gathers sources across the web, arXiv, and Semantic Scholar via MCP
tools, critiques its own output, and produces a polished written report.

Built to demonstrate practical LangGraph orchestration and Model Context
Protocol (MCP) integration — agentic patterns beyond a single LLM call or a
linear RAG chain.

---

## How it works

```
Query → Planner → Researcher ⇄ Critic → Writer → Report
                       ↑___________|
                  (loop if rating < 3, capped at 3 retries)
```

1. **Planner** breaks the research question into 3-5 specific sub-topics.
2. **Researcher** gathers information per topic using three MCP-exposed tools
   — general web search, arXiv, and Semantic Scholar — then synthesizes the
   findings into a draft.
3. **Critic** scores the draft 0-5 against coverage, accuracy, and depth, and
   returns specific feedback.
4. If the score is below 3 (and the retry cap hasn't been hit), the draft goes
   back to the **Researcher**, which incorporates the critic's feedback
   directly into its next attempt.
5. Once accepted, **Writer** turns the raw research notes into a final,
   structured report with headings, a summary, and a conclusion.

This loop — not just the tool use — is the core justification for LangGraph
here: the graph makes a real routing decision based on LLM output, rather than
executing a fixed sequence of steps.

---

## Architecture

- **Orchestration**: LangGraph (`StateGraph`), async graph execution
- **LLMs**: Groq API — `openai/gpt-oss-20b` for planning/research/writing,
  `openai/gpt-oss-120b` for the critic (judgment-heavy task, given a larger
  model)
- **Tools (via MCP)**: a custom MCP server exposing three tools —
  `web_search` (DuckDuckGo, no key required), `arxiv_search` (official
  `arxiv` package), `semantic_scholar_search` (Semantic Scholar public API)
- **Backend**: FastAPI, exposing both a standard request/response endpoint
  and a Server-Sent Events streaming endpoint for real-time pipeline progress
- **Frontend**: Streamlit
- **State**: Pydantic (`ResearchState`) tracking question, topics, the
  researcher's draft, critic rating/feedback, retry count, and final report

### Why MCP specifically

Tools are exposed through a standalone MCP server (`app/mcp_server/`) rather
than bound directly as LangChain tools in-process. The Researcher node
connects to it as an MCP client (`langchain_mcp_adapters`), meaning the tool
layer is protocol-based and swappable — the graph doesn't need to know how
`web_search` or `arxiv_search` are implemented, only that an MCP server
exposes them.

### Why no Google Scholar

Considered and deliberately excluded — Google Scholar has no official API,
and unofficial scrapers are unreliable and prone to being rate-limited or
blocked, especially from cloud IPs. Semantic Scholar's public API was used
instead as a reliable, free substitute for academic search.

---

## Project structure

```
app/
  graph/
    state.py          # ResearchState (Pydantic) + CriticOutput schema
    llm.py             # Groq LLM instances
    nodes.py            # planner, researcher, critic, writer
    edges.py            # critic → writer/researcher routing logic
    utils.py            # retry wrapper, per-topic research helper
    build_graph.py      # graph wiring and compilation
  mcp_server/
    tools.py             # MCP tool definitions
    server.py             # MCP server entrypoint (stdio transport)
  mcp_client.py           # MCP client, connects to the server as a subprocess
  main.py                  # FastAPI app — /research, /research/stream, /health
frontend/
  app.py                   # Streamlit UI
```

---

## Running locally

**Backend**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env
GROQ_API_KEY=your_key_here

uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
streamlit run frontend/app.py
```

Open the Streamlit URL it prints, ask a research question, and the pipeline
runs end to end — typically 30-90 seconds depending on topic count and
whether a critic retry is triggered.

---

## API

`POST /research`
```json
{ "question": "How does attention work in transformer models?" }
```
Returns the final report along with topics, critic rating, retry count, and
critic feedback.

`POST /research/stream`
Same input, but streams a Server-Sent Event after each node completes,
followed by a final event with the full result — built to support real-time
progress UIs (not currently wired into the Streamlit frontend, which uses the
simpler blocking endpoint above).

`GET /health`
Liveness check.

---
## Docker

Images are published to Docker Hub(you can give it a try:) ):

```bash
docker pull theallkeeeymist/multi-agent-research-backend:latest
docker pull theallkeeeymist/multi-agent-research-frontend:latest
```

Run locally with Docker Compose:
```bash
docker compose up --build
```

## Known limitations

- Groq's free-tier `gpt-oss` models don't reliably support forced tool-choice
  structured output — the critic node uses `json_mode` with explicit
  formatting instructions in the prompt instead of LangChain's default
  structured-output method, to work around this.
- MCP tool calls over stdio transport re-establish a session per invocation
  rather than holding one persistent connection; topic-level research calls
  are run with bounded concurrency (not fully parallel) to avoid overloading
  the MCP subprocess.
- No persistent storage — each request is stateless; no history of past
  reports is kept.

---

## Evaluation

*(In progress — offline evaluation harness scoring faithfulness,
completeness, and coherence against a fixed set of test questions, separate
from the in-pipeline critic. Results to be added)*
