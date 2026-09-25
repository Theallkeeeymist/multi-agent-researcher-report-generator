```markdown
# Multi-Agent Research & Report Generator

A LangGraph multi-agent pipeline that takes a research question, plans it into topics, gathers sources across the web, arXiv, and Semantic Scholar via MCP tools, critiques its own output, and produces a polished written report.

Built to demonstrate practical LangGraph orchestration, asynchronous worker distribution, and Model Context Protocol (MCP) integration — agentic patterns engineered for scalable, real-world execution.

---

## How It Works

```text
Query → Planner → Researcher ⇄ Critic → Writer → Report
                       ↑___________|
                  (loop if rating < 3, capped at 3 retries)

```

1. **Planner** breaks the research question into 3–5 specific sub-topics.
2. **Researcher** gathers information per topic using three MCP-exposed tools — general web search, arXiv, and Semantic Scholar — then synthesizes findings into a preliminary draft.
3. **Critic** scores the draft 0–5 against coverage, accuracy, and depth, returning actionable feedback.
4. **Conditional Routing**: If the score is below 3 (and retry limit of 3 is not reached), the draft loops back to the **Researcher** with critic feedback injected directly into the next prompt.
5. **Writer** converts raw, accepted research notes into a finalized, publication-ready report formatted with executive summaries, technical analyses, and cited conclusions.

---

## Architecture

```text
[ Streamlit UI ]
       │  (HTTP / SSE)
       ▼
 [ FastAPI Gateway ]
       │
       ├─── Enqueues Task ────────► [ Redis Broker ]
       │                                   │
       │                            [ Celery Workers ] (Horizontally Scaled)
       │                                   │
       │                             [ LangGraph Engine ]
       │                              ├── MCP Client (stdio) ──► [ FastMCP Server ]
       │                              └── Async Checkpointer ──► [ PostgreSQL ]
       ▼
[ Task Status Polling ]

```

* **Orchestration**: LangGraph (`StateGraph`) with async execution and PostgreSQL state persistence.
* **LLM Engine**: Groq API — `openai/gpt-oss-20b` for planning, research synthesis, and report generation; `openai/gpt-oss-120b` for evaluation and criticism.
* **Tool Protocol (MCP)**: Custom Model Context Protocol server exposing `web_search` (DuckDuckGo), `arxiv_search` (`arxiv`), and `semantic_scholar_search` (Semantic Scholar REST API).
* **Task Queue & Concurrency**: Celery distributed task queue backed by Redis for decoupled background execution.
* **State Persistence**: PostgreSQL checkpointer (`AsyncPostgresSaver`) for durable agent state snapshots and thread recovery. The `langgraph-checkpoint-postgres` package persists thread states asynchronously inside `checkpoints`, `checkpoint_blobs`, and `checkpoint_writes` tables.
* **Backend API**: FastAPI serving job dispatch, status polling, and health check endpoints.
* **Frontend**: Streamlit interactive UI.
* **Containerization**: Multi-container architecture managed via Docker Compose and rootless Podman.

---

## Project Structure

```text
multi-agent-researcher-and-report-generator/
├── src/
│   ├── api/
│   │   └── routes.py              # FastAPI endpoints (/research, /research/status)
│   ├── graph/
│   │   ├── state.py               # ResearchState (Pydantic) + CriticOutput schemas
│   │   ├── llm.py                 # Groq LLM configurations
│   │   ├── nodes.py               # Planner, Researcher, Critic, Writer implementations
│   │   ├── edges.py               # Conditional routing logic (Critic -> Writer/Researcher)
│   │   ├── utils.py               # Retry wrappers & bounded concurrency helpers
│   │   └── build_graph.py         # Graph compilation with checkpointer binding
│   ├── tools/
│   │   ├── tools.py               # FastMCP tool implementations (Web, arXiv, Semantic Scholar)
│   │   ├── server.py              # FastMCP server entrypoint (stdio transport)
│   │   └── mcp_client.py          # Persistent MCP client and tool adapter session manager
│   ├── worker.py                  # Celery worker initialization & task entrypoints
│   └── celery_app.py              # Celery configuration & Redis broker bindings
├── frontend/
│   └── app.py                     # Streamlit web interface
├── tests/
│   ├── test_api.py                # Unit tests for API routes, docs, and validation schemas
│   ├── test_e2e_pipeline.py       # High-throughput (100-request) simulated traffic load test
│   └── test_persistence.py        # PostgreSQL checkpointer connectivity verification
├── docker-compose.yml             # Orchestration for API, Celery workers, Redis, and PostgreSQL
├── Dockerfile                     # Multi-stage container build definition
└── requirements-backend.txt       # Core backend, queue, agent, and database dependencies

```

---

## Running Locally

### 1. Environment Configuration

Create a `.env` file in the root directory:

```env
# Database & Broker
POSTGRES_DB_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/research_db
REDIS_URL=redis://localhost:6379/0

# LLM & Tracing
GROQ_API_KEY=your_groq_api_key_here
LANGCHAIN_TRACING_V2=false

# API Routing
API_URL=http://localhost:8000/research

```

### 2. Multi-Container Orchestration (Docker / Rootless Podman)

Run the full backend cluster with horizontally scaled workers:

```bash
docker compose up --build -d --scale worker=4

```

Verify service status:

```bash
docker compose ps

```

### 3. Launching the Frontend

With the container backend active, run the Streamlit frontend locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install streamlit requests python-dotenv

streamlit run frontend/app.py

```

Access the UI at `http://localhost:8501`.

---

## API Endpoints

### Enqueue Research Task

`POST /research`

```json
{
  "question": "How do transformer attention mechanisms work?"
}

```

**Response (200 / 202 Accepted):**

```json
{
  "task_id": "a9f8b2c4-1d3e-4b7a-9012-3456789abcde",
  "status": "queued"
}

```

### Check Task Status

`GET /research/status/{task_id}`

```json
{
  "task_id": "a9f8b2c4-1d3e-4b7a-9012-3456789abcde",
  "status": "completed",
  "result": {
    "topics": ["Scaled Dot-Product", "Multi-Head Attention", "Computational Complexity"],
    "critic_rating": 4,
    "retry_count": 0,
    "report": "# Transformer Attention Mechanisms\n\n## Summary\n..."
  }
}

```

---

## Automated Testing & Quality Assurance

The project includes an automated test suite covering unit behavior, distributed execution isolation, and simulated traffic load testing.

```bash
# Run the complete test suite
pytest -v

```

### 1. API Contract & Validation Testing (`tests/test_api.py`)

* Asserts OpenAPI documentation availability (`/docs`).
* Verifies input validation rejects malformed or empty payloads with `422 Unprocessable Entity`.
* Confirms request routing queues background jobs without blocking synchronous threads.

### 2. High-Throughput Traffic Simulation (`tests/test_e2e_pipeline.py`)

* Simulates real-world traffic bursts using a pool of multi-domain topics (deep learning architectures, chemical transport phenomena, distributed systems, and cognitive psychology).
* Executes a **100-request automated loop** testing asynchronous task dispatch and status retrieval resilience under burst traffic.
* Mocks out the broker and results layer in-memory to ensure tests run in under 3 seconds without incurring external API rate limits or requiring local Redis instances.

### 3. State Persistence Verification (`tests/test_persistence.py`)

* Verifies database connection strings and checkpointer initialization.
* Validates that `AsyncPostgresSaver` establishes connection pools and verifies checkpointer schema readiness using `.setup()`.

---

## Key Improvements & Architectural Evolution

Refactoring this platform from an initial proof-of-concept into a production-grade distributed architecture introduced several fundamental system enhancements:

* **Asynchronous Decoupling Over Blocking HTTP**: Previous implementations held synchronous HTTP connections open for 30–90 seconds while agents iterated through research and critique loops. Introducing Celery and Redis decouples ingestion from execution; FastAPI returns a job token immediately (`202 Accepted`), eliminating HTTP request timeouts.
* **Horizontal Worker Scalability**: Agent workflows are no longer restricted to a single API server process. Celery workers can be scaled horizontally across multiple containers (`--scale worker=N`) to process concurrent research tasks in parallel without choking the HTTP gateway.
* **Durable Checkpointing Over Ephemeral State**: Earlier runs stored state in-memory, causing graph context to be permanently lost if a process died mid-loop. Integrating LangGraph's PostgreSQL checkpointer (`AsyncPostgresSaver`) guarantees that thread states, critique ratings, and tool outputs survive service restarts and enable granular run recovery.
* **Protocol-Isolated Tool Execution (MCP)**: Instead of coupling external search SDKs directly into the agent logic, tools run in a modular Model Context Protocol subprocess over `stdio`. This protects core agent orchestration from tool dependency conflicts and unhandled third-party API exceptions.
* **Verified High-Load Reliability**: The inclusion of an in-memory mock-driven test suite allows validating backend stability against bursts of 100+ complex requests in seconds, guaranteeing contract safety without burning external LLM token quotas.
* **Rootless Containerized Deployment**: Full containerization via Docker Compose under rootless Podman ensures standardized networking, dependency management, and reproducible environments across local development and production servers.

```

```
