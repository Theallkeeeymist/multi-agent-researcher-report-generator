import { useCallback, useEffect, useRef, useState } from "react";
import { checkHealth, streamResearch } from "./api";
import PipelineTrace from "./components/PipelineTrace";
import ReportView from "./components/ReportView";

const STAGES = ["planner", "researcher", "critic", "writer"];

export default function App() {
  const [question, setQuestion] = useState("");
  const [running, setRunning] = useState(false);
  const [backendOk, setBackendOk] = useState(null);
  const [completedStages, setCompletedStages] = useState([]);
  const [activeStage, setActiveStage] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  useEffect(() => {
    checkHealth()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false));
  }, []);

  const handleRun = useCallback(async () => {
    const q = question.trim();
    if (!q || running) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setRunning(true);
    setError(null);
    setResult(null);
    setCompletedStages([]);
    setActiveStage(STAGES[0]);

    try {
      await streamResearch(q, {
        signal: controller.signal,
        onStage: ({ node }) => {
          setCompletedStages((prev) => [...prev, node]);
          const idx = STAGES.indexOf(node);
          setActiveStage(idx < STAGES.length - 1 ? STAGES[idx + 1] : null);
        },
        onResult: (data) => {
          setCompletedStages(STAGES);
          setActiveStage(null);
          setResult(data);
        },
      });
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(
          err.message.includes("fetch")
            ? "Cannot reach backend. Start it with: uvicorn app.main:app --reload"
            : err.message
        );
      }
    } finally {
      setRunning(false);
    }
  }, [question, running]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleRun();
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <span className="badge">multi-agent pipeline</span>
          <span className={`status ${backendOk === true ? "online" : backendOk === false ? "offline" : ""}`}>
            {backendOk === true ? "backend connected" : backendOk === false ? "backend offline" : "checking…"}
          </span>
        </div>
        <h1>Research Agent</h1>
        <p className="subtitle">
          Planner → Researcher → Critic → Writer — powered by LangGraph &amp; MCP
        </p>
      </header>

      <section className="input-section">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a research question — e.g. How does attention work in transformer models?"
          rows={3}
          disabled={running}
        />
        <div className="input-footer">
          <span className="hint">Ctrl+Enter to run · typically 30–90s</span>
          <button className="run-btn" onClick={handleRun} disabled={running || !question.trim()}>
            {running ? "Running…" : "Run Research"}
          </button>
        </div>
      </section>

      {(running || completedStages.length > 0) && (
        <PipelineTrace stages={STAGES} completed={completedStages} active={activeStage} />
      )}

      {error && <div className="error">{error}</div>}

      {result && <ReportView data={result} />}
    </div>
  );
}
