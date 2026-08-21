const STAGE_COLORS = {
  planner: "#a78bfa",
  researcher: "#34d399",
  critic: "#fb923c",
  writer: "#60a5fa",
};

export default function PipelineTrace({ stages, completed, active }) {
  return (
    <section className="pipeline">
      <p className="pipeline-label">Pipeline</p>
      <div className="pipeline-stages">
        {stages.map((stage) => {
          const isDone = completed.includes(stage);
          const isActive = active === stage;
          const color = STAGE_COLORS[stage];

          return (
            <div
              key={stage}
              className={`stage ${isDone ? "done" : ""} ${isActive ? "active" : ""}`}
              style={{ "--stage-color": color }}
            >
              <span className="stage-dot" />
              <span className="stage-name">{stage}</span>
              <span className="stage-status">
                {isDone ? "done" : isActive ? "running" : "waiting"}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
