import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function ReportView({ data }) {
  const [copied, setCopied] = useState(false);
  const report = data.report || "";

  const download = () => {
    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "research_report.md";
    a.click();
    URL.revokeObjectURL(url);
  };

  const copy = async () => {
    await navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="report-section">
      <div className="metrics">
        <div className="metric">
          <span className="metric-label">Rating</span>
          <span className="metric-value accent">{data.rating} / 5</span>
        </div>
        <div className="metric">
          <span className="metric-label">Loops</span>
          <span className="metric-value">{data.loop_count}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Topics</span>
          <span className="metric-value">{data.topics?.length ?? 0}</span>
        </div>
      </div>

      {data.topics?.length > 0 && (
        <details className="details">
          <summary>Topics explored</summary>
          <ul>
            {data.topics.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </details>
      )}

      {data.critic_feedback && (
        <details className="details">
          <summary>Critic feedback</summary>
          <p>{data.critic_feedback}</p>
        </details>
      )}

      <div className="report-card">
        <div className="report-header">
          <h2>Report</h2>
          <div className="report-actions">
            <button onClick={download}>Download .md</button>
            <button onClick={copy}>{copied ? "Copied!" : "Copy"}</button>
          </div>
        </div>
        <div className="report-body">
          <ReactMarkdown>{report}</ReactMarkdown>
        </div>
      </div>
    </section>
  );
}
